"""
Ray-based verification for obstruction angles

When horizon + zenith >= 90 degrees, the current plane-intersection algorithm
reports full obstruction. This module verifies whether there is actually a
continuous wall of obstruction by casting rays at different elevation angles
in the suspect gap region.

Two-phase adaptive approach:
  Phase 1: Coarse sweep (5 degree steps) to find hit/miss transitions
  Phase 2: Fine sweep (1 degree steps) at transitions to find exact boundaries

Uses vectorized numpy operations for batch ray-triangle testing.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import logging
import numpy as np

from src.components.geometry import Mesh, Point3D, Triangle
from src.components.geometry.coordinate_system import CoordinateSystem
from src.components.calculators.ray_triangle_intersector import RayTriangleIntersector, TriangleArrays
from src.components.models import Window, ObstructionResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RayVerificationConfig:
    """Configuration constants for ray verification"""
    TRIGGER_THRESHOLD_DEG: float = 90.0
    COARSE_STEP_DEG: float = 5.0
    FINE_STEP_DEG: float = 1.0


@dataclass(frozen=True)
class ElevationSample:
    """Result of a single ray cast at a given elevation"""
    elevation_deg: float
    hit: bool


class RayVerificationCalculator:
    """
    Two-phase adaptive ray sweep to verify full obstruction.

    Only triggers when horizon_deg + zenith_deg >= 90 (threshold).
    Casts rays in the elevation range between the zenith boundary
    (90 - zenith_deg) and the horizon boundary (horizon_deg) to find
    gaps of visible sky.

    Uses vectorized numpy batch operations for performance:
    all coarse rays are tested against all triangles in a single pass.
    """

    @classmethod
    def verify(
        cls,
        horizon_result: ObstructionResult,
        zenith_result: ObstructionResult,
        window: Window,
        direction_angle: float,
        horizon_mesh: Mesh,
        zenith_mesh: Mesh,
        config: RayVerificationConfig = RayVerificationConfig()
    ) -> Tuple[ObstructionResult, ObstructionResult]:
        """
        Verify and correct obstruction angles when h+z >= 90 degrees.

        Args:
            horizon_result: Calculated horizon obstruction
            zenith_result: Calculated zenith obstruction
            window: Window being analyzed (center + normal per direction)
            direction_angle: Current horizontal direction angle in radians
            horizon_mesh: Pre-filtered horizon mesh for this direction
            zenith_mesh: Pre-filtered zenith mesh for this direction
            config: Verification configuration constants

        Returns:
            Corrected (horizon_result, zenith_result) pair.
            Returns originals unchanged if no gap found.
        """
        h_deg = horizon_result.obstruction_angle_degrees
        z_deg = zenith_result.obstruction_angle_degrees

        if h_deg + z_deg < config.TRIGGER_THRESHOLD_DEG:
            return horizon_result, zenith_result

        all_triangles = cls._combine_triangles(horizon_mesh, zenith_mesh)
        if not all_triangles:
            return horizon_result, zenith_result

        # Pre-pack triangle vertices into numpy arrays (done once, reused for all rays)
        tri_arrays = RayTriangleIntersector.prepare_arrays(all_triangles)
        origin_arr = window.center.to_array()

        # Sweep the full elevation range (0° to 90°) to find any sky gap.
        elev_low_deg = 0.0
        elev_high_deg = 90.0

        logger.debug(
            f"[RAY-VERIFY] Triggered: h={h_deg:.1f} + z={z_deg:.1f} = {h_deg + z_deg:.1f} >= 90. "
            f"Sweep range: {elev_low_deg:.1f} to {elev_high_deg:.1f} deg, "
            f"triangles: {tri_arrays.count} (h={len(horizon_mesh.triangles) if horizon_mesh and horizon_mesh.triangles else 0}, "
            f"z={len(zenith_mesh.triangles) if zenith_mesh and zenith_mesh.triangles else 0})"
        )

        # Phase 1: vectorized coarse sweep
        coarse_samples = cls._coarse_sweep_batch(
            origin_arr, direction_angle, tri_arrays,
            elev_low_deg, elev_high_deg, config.COARSE_STEP_DEG
        )

        # Log every sample for debugging
        sample_str = ", ".join(
            f"{s.elevation_deg:.1f}°:{'HIT' if s.hit else 'MISS'}"
            for s in coarse_samples
        )
        logger.debug(f"[RAY-VERIFY] Coarse samples ({len(coarse_samples)}): [{sample_str}]")

        # Find transitions (hit->miss or miss->hit)
        transitions = cls._find_transitions(coarse_samples)

        if not transitions:
            # No transitions found — check if ALL samples are hits
            if coarse_samples and all(s.hit for s in coarse_samples):
                logger.debug("[RAY-VERIFY] All coarse rays hit — truly fully obstructed")
                return horizon_result, zenith_result
            # All misses — the entire range is a gap
            if coarse_samples and not any(s.hit for s in coarse_samples):
                logger.debug("[RAY-VERIFY] All coarse rays miss — entire range is gap")
                return cls._build_corrected_results(
                    horizon_result, zenith_result,
                    elev_low_deg, elev_high_deg
                )
            return horizon_result, zenith_result

        # Phase 2: vectorized fine sweep at each transition
        gap_low_deg, gap_high_deg = cls._refine_gap_batch(
            origin_arr, direction_angle, tri_arrays,
            coarse_samples, transitions, config.FINE_STEP_DEG
        )

        if gap_low_deg is None or gap_high_deg is None:
            return horizon_result, zenith_result

        logger.debug(
            f"[RAY-VERIFY] Gap found: {gap_low_deg:.1f} to {gap_high_deg:.1f} deg elevation"
        )

        return cls._build_corrected_results(
            horizon_result, zenith_result,
            gap_low_deg, gap_high_deg
        )

    @classmethod
    def _combine_triangles(
        cls,
        horizon_mesh: Mesh,
        zenith_mesh: Mesh
    ) -> Tuple[Triangle, ...]:
        """Combine triangles from both meshes for ray testing."""
        h_tris = horizon_mesh.triangles if horizon_mesh and horizon_mesh.triangles else ()
        z_tris = zenith_mesh.triangles if zenith_mesh and zenith_mesh.triangles else ()
        return h_tris + z_tris

    @classmethod
    def _build_directions(
        cls,
        direction_angle: float,
        elevation_degs: np.ndarray
    ) -> np.ndarray:
        """
        Build unit direction vectors for multiple elevation angles at a fixed azimuth.

        Args:
            direction_angle: Horizontal direction in radians
            elevation_degs: Array of elevation angles in degrees, shape (M,)

        Returns:
            Direction vectors of shape (M, 3)
        """
        horizontal = np.array([np.cos(direction_angle), np.sin(direction_angle), 0.0])
        elev_rads = np.radians(elevation_degs)
        cos_e = np.cos(elev_rads)[:, np.newaxis]  # (M, 1)
        sin_e = np.sin(elev_rads)[:, np.newaxis]  # (M, 1)
        directions = cos_e * horizontal + sin_e * CoordinateSystem.UP  # (M, 3)
        norms = np.linalg.norm(directions, axis=1, keepdims=True)
        return directions / norms

    @classmethod
    def _coarse_sweep_batch(
        cls,
        origin: np.ndarray,
        direction_angle: float,
        tri_arrays: TriangleArrays,
        elev_low_deg: float,
        elev_high_deg: float,
        step_deg: float
    ) -> List[ElevationSample]:
        """
        Phase 1: Cast all coarse rays in a single vectorized batch.

        Args:
            origin: Ray origin as numpy array, shape (3,)
            direction_angle: Horizontal direction in radians
            tri_arrays: Pre-packed triangle vertex arrays
            elev_low_deg: Lower elevation bound (degrees)
            elev_high_deg: Upper elevation bound (degrees)
            step_deg: Angular step between rays (degrees)

        Returns:
            List of ElevationSample results ordered by elevation
        """
        # Build elevation array
        elev_degs = np.arange(elev_low_deg, elev_high_deg + step_deg * 0.5, step_deg)
        # Ensure upper bound is included
        if elev_degs[-1] < elev_high_deg:
            elev_degs = np.append(elev_degs, elev_high_deg)

        # Build all directions at once and batch test
        directions = cls._build_directions(direction_angle, elev_degs)
        hits = RayTriangleIntersector.batch_hits_any(origin, directions, tri_arrays)

        return [
            ElevationSample(elevation_deg=float(elev_degs[i]), hit=bool(hits[i]))
            for i in range(len(elev_degs))
        ]

    @classmethod
    def _find_transitions(cls, samples: List[ElevationSample]) -> List[int]:
        """
        Find indices where hit status changes between consecutive samples.

        Args:
            samples: Ordered elevation samples

        Returns:
            List of indices i where samples[i].hit != samples[i+1].hit
        """
        transitions: List[int] = []
        for i in range(len(samples) - 1):
            if samples[i].hit != samples[i + 1].hit:
                transitions.append(i)
        return transitions

    @classmethod
    def _refine_gap_batch(
        cls,
        origin: np.ndarray,
        direction_angle: float,
        tri_arrays: TriangleArrays,
        coarse_samples: List[ElevationSample],
        transitions: List[int],
        fine_step_deg: float
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Phase 2: Refine all transition boundaries in a single vectorized batch.

        Collects all fine elevation angles across all transitions, tests them
        in one batch call, then finds the lowest and highest miss elevations.

        Args:
            origin: Ray origin as numpy array, shape (3,)
            direction_angle: Horizontal direction in radians
            tri_arrays: Pre-packed triangle vertex arrays
            coarse_samples: Results from phase 1
            transitions: Indices of coarse transitions
            fine_step_deg: Fine angular step (degrees)

        Returns:
            (gap_low_deg, gap_high_deg) — the elevation bounds of the sky gap.
            Returns (None, None) if refinement finds no gap.
        """
        # Collect all fine elevation angles across all transitions
        fine_elevations: List[float] = []
        for idx in transitions:
            low_elev = coarse_samples[idx].elevation_deg
            high_elev = coarse_samples[idx + 1].elevation_deg
            elev = low_elev + fine_step_deg
            while elev < high_elev:
                fine_elevations.append(elev)
                elev += fine_step_deg

        # Batch test all fine rays at once
        all_miss_elevations: List[float] = []
        if fine_elevations:
            fine_elev_arr = np.array(fine_elevations)
            directions = cls._build_directions(direction_angle, fine_elev_arr)
            hits = RayTriangleIntersector.batch_hits_any(origin, directions, tri_arrays)
            for i, elev in enumerate(fine_elevations):
                if not hits[i]:
                    all_miss_elevations.append(elev)

        # Also include any coarse misses
        for sample in coarse_samples:
            if not sample.hit:
                all_miss_elevations.append(sample.elevation_deg)

        if not all_miss_elevations:
            return None, None

        gap_low_deg = min(all_miss_elevations)
        gap_high_deg = max(all_miss_elevations)
        return gap_low_deg, gap_high_deg

    @classmethod
    def _build_corrected_results(
        cls,
        horizon_result: ObstructionResult,
        zenith_result: ObstructionResult,
        gap_low_deg: float,
        gap_high_deg: float
    ) -> Tuple[ObstructionResult, ObstructionResult]:
        """
        Build corrected ObstructionResult pair clamped to the sky gap.

        Horizon is clamped to gap_low_deg (can't see higher than where gap starts).
        Zenith is clamped to 90 - gap_high_deg (can't see lower than where gap ends).

        Args:
            horizon_result: Original horizon result
            zenith_result: Original zenith result
            gap_low_deg: Lower elevation of sky gap (degrees)
            gap_high_deg: Upper elevation of sky gap (degrees)

        Returns:
            Corrected (horizon, zenith) result pair
        """
        corrected_h_deg = min(horizon_result.obstruction_angle_degrees, gap_low_deg)
        corrected_z_deg = min(zenith_result.obstruction_angle_degrees, 90.0 - gap_high_deg)

        corrected_horizon = ObstructionResult(
            obstruction_angle_degrees=corrected_h_deg,
            obstruction_angle_radians=float(np.radians(corrected_h_deg)),
            highest_point=horizon_result.highest_point
        )
        corrected_zenith = ObstructionResult(
            obstruction_angle_degrees=corrected_z_deg,
            obstruction_angle_radians=float(np.radians(corrected_z_deg)),
            highest_point=zenith_result.highest_point
        )

        logger.info(
            f"[RAY-VERIFY] Corrected: horizon {horizon_result.obstruction_angle_degrees:.1f} -> {corrected_h_deg:.1f}, "
            f"zenith {zenith_result.obstruction_angle_degrees:.1f} -> {corrected_z_deg:.1f}"
        )

        return corrected_horizon, corrected_zenith

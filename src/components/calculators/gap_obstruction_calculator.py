"""
Gap-based unified obstruction calculator

Replaces the separate horizon/zenith calculation with a single pass:
1. Intersect ALL geometry with the vertical sweep plane
2. Collect elevation angles of all intersection points
3. Find the largest gap between consecutive angles
4. Verify gap with a single ray, then binary search boundaries to 1 degree

Output: gap_midpoint (center of sky opening) and gap_amplitude (width).
Derived horizon/zenith angles for backward compatibility.
"""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from src.components.calculators.intersection_calculator import IntersectionCalculator
from src.components.calculators.ray_triangle_intersector import RayTriangleIntersector, TriangleArrays
from src.components.geometry import Mesh, Point3D
from src.components.geometry.coordinate_system import CoordinateSystem
from src.components.models import Window

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GapObstructionConfig:
    """Configuration for gap-based obstruction calculation"""
    MIN_GAP_DEG: float = 4.0
    BINARY_SEARCH_PRECISION_DEG: float = 1.0


@dataclass(frozen=True)
class GapObstructionResult:
    """Result of gap-based obstruction calculation"""
    gap_midpoint_deg: float
    gap_amplitude_deg: float
    horizon_deg: float
    zenith_deg: float
    rays_cast: int
    elapsed_ms: float


class GapObstructionCalculator:
    """
    Unified obstruction calculator using gap detection.

    For each direction, finds all plane-mesh intersection points,
    sorts by elevation angle, identifies the largest angular gap
    between consecutive points, and verifies it with ray casting.

    The gap boundaries directly yield horizon and zenith angles
    without needing separate mesh splits or calculation passes.
    """

    @classmethod
    def calculate(
        cls,
        mesh: Mesh,
        window: Window,
        direction_angle: float,
        config: GapObstructionConfig = GapObstructionConfig()
    ) -> GapObstructionResult:
        """
        Calculate obstruction using gap detection for a single direction.

        Args:
            mesh: Combined mesh (all triangles, no horizon/zenith split)
            window: Window with center and normal set to this direction
            direction_angle: Horizontal direction angle in radians
            config: Gap detection configuration

        Returns:
            GapObstructionResult with gap info and derived horizon/zenith
        """
        start = time.time()
        rays_cast = 0

        # Step 1: Collect all elevation angles from plane intersections
        elevation_angles = IntersectionCalculator.collect_all_elevation_angles(
            mesh.triangles, window
        )

        # Step 2: Find gaps between consecutive intersection points
        gaps = cls._find_gaps(elevation_angles, config.MIN_GAP_DEG)

        if not gaps:
            # No gaps larger than threshold — fully obstructed
            elapsed = (time.time() - start) * 1000
            logger.debug(
                f"[GAP-CALC] No gaps > {config.MIN_GAP_DEG} deg found "
                f"({len(elevation_angles)} intersection angles). "
                f"Elapsed: {elapsed:.1f}ms"
            )
            return GapObstructionResult(
                gap_midpoint_deg=0.0,
                gap_amplitude_deg=0.0,
                horizon_deg=45.0,
                zenith_deg=45.0,
                rays_cast=0,
                elapsed_ms=elapsed
            )

        # Step 3: Prepare triangles for ray casting
        if not mesh.triangles:
            elapsed = (time.time() - start) * 1000
            return cls._no_obstruction_result(elapsed)

        tri_arrays = RayTriangleIntersector.prepare_arrays(mesh.triangles)
        origin = window.center.to_array()

        # Step 4: Test gaps largest-first, verify with a single ray
        for gap_low, gap_high, gap_size in gaps:
            test_elevation = gap_low + 1.0
            if test_elevation >= gap_high:
                test_elevation = (gap_low + gap_high) / 2.0

            direction = cls._build_direction(direction_angle, test_elevation)
            hits = RayTriangleIntersector.batch_hits_any(
                origin, direction[np.newaxis, :], tri_arrays
            )
            rays_cast += 1

            if not hits[0]:
                # Sky found! Binary search for exact boundaries
                exact_low = cls._binary_search_lower(
                    origin, direction_angle, tri_arrays,
                    gap_low, test_elevation, config.BINARY_SEARCH_PRECISION_DEG
                )
                exact_high = cls._binary_search_upper(
                    origin, direction_angle, tri_arrays,
                    test_elevation, gap_high, config.BINARY_SEARCH_PRECISION_DEG
                )
                rays_cast += exact_low[1] + exact_high[1]
                low_boundary = exact_low[0]
                high_boundary = exact_high[0]

                gap_midpoint = (low_boundary + high_boundary) / 2.0
                gap_amplitude = high_boundary - low_boundary
                horizon_deg = low_boundary
                zenith_deg = 90.0 - high_boundary

                elapsed = (time.time() - start) * 1000
                logger.debug(
                    f"[GAP-CALC] Gap found: {low_boundary:.1f} to {high_boundary:.1f} deg "
                    f"(mid={gap_midpoint:.1f}, amp={gap_amplitude:.1f}). "
                    f"h={horizon_deg:.1f}, z={zenith_deg:.1f}. "
                    f"Rays: {rays_cast}. Elapsed: {elapsed:.1f}ms"
                )
                return GapObstructionResult(
                    gap_midpoint_deg=gap_midpoint,
                    gap_amplitude_deg=gap_amplitude,
                    horizon_deg=horizon_deg,
                    zenith_deg=zenith_deg,
                    rays_cast=rays_cast,
                    elapsed_ms=elapsed
                )

        # All gaps tested but all had hits — fully obstructed
        elapsed = (time.time() - start) * 1000
        logger.debug(
            f"[GAP-CALC] All {len(gaps)} gaps had hits — fully obstructed. "
            f"Rays: {rays_cast}. Elapsed: {elapsed:.1f}ms"
        )
        return GapObstructionResult(
            gap_midpoint_deg=0.0,
            gap_amplitude_deg=0.0,
            horizon_deg=45.0,
            zenith_deg=45.0,
            rays_cast=rays_cast,
            elapsed_ms=elapsed
        )

    @classmethod
    def _find_gaps(
        cls,
        elevation_angles: List[float],
        min_gap_deg: float
    ) -> List[Tuple[float, float, float]]:
        """
        Find angular gaps between consecutive intersection points.

        Adds 0 and 90 degree boundaries, sorts, and returns gaps
        larger than min_gap_deg, ranked by size (largest first).

        Args:
            elevation_angles: Sorted list of elevation angles in degrees
            min_gap_deg: Minimum gap size to include

        Returns:
            List of (low, high, size) tuples sorted by size descending
        """
        boundaries = [0.0] + list(elevation_angles) + [90.0]
        # Remove duplicates and sort
        boundaries = sorted(set(boundaries))

        gaps: List[Tuple[float, float, float]] = []
        for i in range(len(boundaries) - 1):
            size = boundaries[i + 1] - boundaries[i]
            if size > min_gap_deg:
                gaps.append((boundaries[i], boundaries[i + 1], size))

        # Largest gaps first
        gaps.sort(key=lambda g: g[2], reverse=True)
        return gaps

    @classmethod
    def _build_direction(cls, direction_angle: float, elevation_deg: float) -> np.ndarray:
        """
        Build a unit direction vector for a given azimuth and elevation.

        Args:
            direction_angle: Horizontal direction in radians
            elevation_deg: Elevation angle in degrees (0=horizontal, 90=up)

        Returns:
            Unit direction vector, shape (3,)
        """
        horizontal = np.array([np.cos(direction_angle), np.sin(direction_angle), 0.0])
        elev_rad = np.radians(elevation_deg)
        direction = np.cos(elev_rad) * horizontal + np.sin(elev_rad) * CoordinateSystem.UP
        norm = np.linalg.norm(direction)
        return direction / norm

    @classmethod
    def _binary_search_lower(
        cls,
        origin: np.ndarray,
        direction_angle: float,
        tri_arrays: TriangleArrays,
        low: float,
        high: float,
        precision: float
    ) -> Tuple[float, int]:
        """
        Binary search for the exact lower boundary of a sky gap.

        Searches between low (intersection point) and high (known clear sky)
        to find where obstruction ends and sky begins.

        Args:
            origin: Ray origin, shape (3,)
            direction_angle: Horizontal direction in radians
            tri_arrays: Pre-packed triangle arrays
            low: Lower bound (likely obstructed), degrees
            high: Upper bound (known clear), degrees
            precision: Stop when range < this, degrees

        Returns:
            (boundary_elevation_deg, rays_cast)
        """
        rays_cast = 0
        while (high - low) > precision:
            mid = (low + high) / 2.0
            direction = cls._build_direction(direction_angle, mid)
            hits = RayTriangleIntersector.batch_hits_any(
                origin, direction[np.newaxis, :], tri_arrays
            )
            rays_cast += 1
            if hits[0]:
                # Still obstructed — boundary is higher
                low = mid
            else:
                # Clear sky — boundary is lower
                high = mid

        return high, rays_cast

    @classmethod
    def _binary_search_upper(
        cls,
        origin: np.ndarray,
        direction_angle: float,
        tri_arrays: TriangleArrays,
        low: float,
        high: float,
        precision: float
    ) -> Tuple[float, int]:
        """
        Binary search for the exact upper boundary of a sky gap.

        Searches between low (known clear sky) and high (intersection point)
        to find where sky ends and obstruction begins.

        Args:
            origin: Ray origin, shape (3,)
            direction_angle: Horizontal direction in radians
            tri_arrays: Pre-packed triangle arrays
            low: Lower bound (known clear), degrees
            high: Upper bound (likely obstructed), degrees
            precision: Stop when range < this, degrees

        Returns:
            (boundary_elevation_deg, rays_cast)
        """
        rays_cast = 0
        while (high - low) > precision:
            mid = (low + high) / 2.0
            direction = cls._build_direction(direction_angle, mid)
            hits = RayTriangleIntersector.batch_hits_any(
                origin, direction[np.newaxis, :], tri_arrays
            )
            rays_cast += 1
            if hits[0]:
                # Obstructed — boundary is lower
                high = mid
            else:
                # Clear sky — boundary is higher
                low = mid

        return low, rays_cast

    @classmethod
    def _no_obstruction_result(cls, elapsed_ms: float) -> GapObstructionResult:
        """Result when no geometry exists — full sky visible."""
        return GapObstructionResult(
            gap_midpoint_deg=45.0,
            gap_amplitude_deg=90.0,
            horizon_deg=0.0,
            zenith_deg=0.0,
            rays_cast=0,
            elapsed_ms=elapsed_ms
        )

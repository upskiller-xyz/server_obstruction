"""
Batched multi-direction obstruction calculator

Computes obstruction for all requested directions in one vectorized pass instead
of one async task per direction. All directions share the same ray/plane origin
(the window center), which lets ``RayTriangleIntersector.batch_hits_any`` test one
ray per direction against every triangle in a single NumPy sweep.

Semantics are identical to ``GapObstructionOrchestrator.calculate`` run per
direction:
  1. Collect plane-mesh intersection elevation angles (batched)
  2. Detect angular gaps per direction (largest first)
  3. Probe each direction's largest unresolved gap; on sky, binary-search the
     horizon/zenith boundaries — all batched across directions in lockstep
  4. Fall back to the fully-obstructed default (45/45) when no gap admits sky

Directions are processed in chunks to bound the (chunk, N, 3) memory of the
elevation broadcast; each chunk is fully batched internally.
"""

import logging
import os
import time
from typing import Any, Dict, List, Tuple

import numpy as np

from src.components.calculators.batched_elevation_angle_collector import (
    BatchedElevationAngleCollector,
)
from src.components.calculators.gap_detection_strategy import GapDetectionStrategy
from src.components.calculators.gap_obstruction_calculator import GapObstructionConfig
from src.components.calculators.ray_triangle_intersector import (
    RayTriangleIntersector,
    TriangleArrays,
)
from src.components.geometry import Vector3D
from src.components.models import ObstructionResult, Window
from src.server.base.constants import BoundaryDirection, ResponseField

logger = logging.getLogger(__name__)

# Default fallback angles when a direction admits no sky gap (matches
# ObstructionResultFactory.create_empty).
_FULLY_OBSTRUCTED_DEG: float = 45.0


class BatchedDirectionSettings:
    """
    Runtime settings for the batched all-directions path.

    Enumerator Pattern: env keys grouped here instead of scattered magic strings.
    - OBSTRUCTION_BATCHED: "1" (default) enables the batched path
    - OBSTRUCTION_BATCH_CHUNK: directions per batched chunk (memory bound)
    - OBSTRUCTION_BATCH_MAX_CELLS: N*D safety ceiling; above it the caller falls
      back to the async per-direction path
    """

    _ENABLED_KEY = "OBSTRUCTION_BATCHED"
    _CHUNK_KEY = "OBSTRUCTION_BATCH_CHUNK"
    _MAX_CELLS_KEY = "OBSTRUCTION_BATCH_MAX_CELLS"

    @classmethod
    def enabled(cls) -> bool:
        """Whether the batched path is enabled (default: yes)."""
        return os.getenv(cls._ENABLED_KEY, "1").lower() in ("1", "true", "yes")

    @classmethod
    def chunk_size(cls) -> int:
        """Directions processed per batched chunk.

        Default 8: measured fastest on large meshes (~12k triangles) — bigger
        chunks (32/64) lose to cache/memory pressure in the (chunk, N, 3) ray
        broadcast, smaller chunks add Python-loop overhead.
        """
        return max(1, int(os.getenv(cls._CHUNK_KEY, "8")))

    @classmethod
    def max_cells(cls) -> int:
        """N*D ceiling before falling back to the async path (default 40M)."""
        return int(os.getenv(cls._MAX_CELLS_KEY, str(40_000_000)))

    @classmethod
    def within_budget(cls, triangle_count: int, num_directions: int) -> bool:
        """True if this workload fits the batched path's memory budget."""
        return triangle_count * num_directions <= cls.max_cells()


class BatchedDirectionCalculator:
    """
    Vectorized all-directions obstruction calculator.

    Single Responsibility:
    - Orchestrates the batched gap-detection + verification pipeline for a whole
      set of directions and formats the per-direction response entries
    """

    @classmethod
    def calculate(
        cls,
        tri_arrays: TriangleArrays,
        window: Window,
        azimuths: np.ndarray,
        config: GapObstructionConfig = GapObstructionConfig(),
        chunk_size: int | None = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate obstruction for every direction, batched over directions.

        Args:
            tri_arrays: Pre-packed triangle arrays (shared across directions)
            window: Window (center is the shared origin for all directions)
            azimuths: (D,) absolute direction angles in radians
            config: Gap detection / binary-search configuration
            chunk_size: Directions per batched chunk (defaults to settings)

        Returns:
            List of D response dicts, order matching ``azimuths``, each with
            direction_angle, horizon and zenith (same shape as the async path)
        """
        start = time.time()
        azimuths = np.asarray(azimuths, dtype=float)
        origin = window.center.to_array()
        if chunk_size is None:
            chunk_size = BatchedDirectionSettings.chunk_size()

        results: List[Dict[str, Any]] = []
        for chunk_start in range(0, azimuths.shape[0], chunk_size):
            chunk = azimuths[chunk_start:chunk_start + chunk_size]
            horizon, zenith = cls._solve_chunk(tri_arrays, origin, chunk, config)
            for i in range(chunk.shape[0]):
                results.append(
                    cls._build_entry(float(chunk[i]), float(horizon[i]), float(zenith[i]))
                )

        logger.debug(
            "[BATCHED] %d directions, %d triangles in %.0fms",
            azimuths.shape[0], tri_arrays.count, (time.time() - start) * 1000
        )
        return results

    @classmethod
    def _solve_chunk(
        cls,
        tri_arrays: TriangleArrays,
        origin: np.ndarray,
        azimuths: np.ndarray,
        config: GapObstructionConfig
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Resolve horizon/zenith for one chunk of directions.

        Returns:
            (horizon_deg, zenith_deg) arrays, shape (len(azimuths),)
        """
        num = azimuths.shape[0]
        horizon = np.full(num, _FULLY_OBSTRUCTED_DEG)
        zenith = np.full(num, _FULLY_OBSTRUCTED_DEG)
        resolved = np.zeros(num, dtype=bool)

        if tri_arrays.count == 0:
            return horizon, zenith

        angle_lists = BatchedElevationAngleCollector.collect(tri_arrays, origin, azimuths)
        gaps_per_dir = [
            GapDetectionStrategy.find_gaps(angles.tolist(), config.MIN_GAP_DEG)
            for angles in angle_lists
        ]

        # Iterate gap ranks (largest gap first). Most directions resolve at rank 0
        # ("Gaps tested: 1" in the logs); a direction whose largest gap is obstructed
        # advances to its next gap on the following rank.
        rank = 0
        while not resolved.all():
            active = [
                d for d in range(num)
                if not resolved[d] and rank < len(gaps_per_dir[d])
            ]
            # Directions with no gap left are fully obstructed (keep 45/45 default).
            for d in range(num):
                if not resolved[d] and rank >= len(gaps_per_dir[d]):
                    resolved[d] = True
            if not active:
                break

            gap_low = np.array([gaps_per_dir[d][rank][0] for d in active])
            gap_high = np.array([gaps_per_dir[d][rank][1] for d in active])
            az = azimuths[active]

            test_elev = gap_low + 1.0
            fallback = (gap_low + gap_high) * 0.5
            test_elev = np.where(test_elev >= gap_high, fallback, test_elev)

            probe_dirs = Vector3D.directions_from_azimuth_elevation(az, test_elev)
            hits = RayTriangleIntersector.batch_hits_any(origin, probe_dirs, tri_arrays)
            sky = ~hits

            if np.any(sky):
                sky_idx = [active[k] for k in range(len(active)) if sky[k]]
                s_az = az[sky]
                s_low = gap_low[sky]
                s_high = gap_high[sky]
                s_test = test_elev[sky]

                horizon_deg = cls._search_boundary(
                    origin, s_az, tri_arrays, s_low, s_test,
                    config.BINARY_SEARCH_PRECISION_DEG, BoundaryDirection.LOWER
                )
                upper = cls._search_boundary(
                    origin, s_az, tri_arrays, s_test, s_high,
                    config.BINARY_SEARCH_PRECISION_DEG, BoundaryDirection.UPPER
                )
                for j, d in enumerate(sky_idx):
                    horizon[d] = horizon_deg[j]
                    zenith[d] = 90.0 - upper[j]
                    resolved[d] = True

            # Obstructed (non-sky) directions stay unresolved for the next rank.
            rank += 1

        return horizon, zenith

    @classmethod
    def _search_boundary(
        cls,
        origin: np.ndarray,
        azimuths: np.ndarray,
        tri_arrays: TriangleArrays,
        low: np.ndarray,
        high: np.ndarray,
        precision: float,
        boundary: BoundaryDirection
    ) -> np.ndarray:
        """
        Batched binary search for a gap boundary across directions.

        Each direction converges its own [low, high] to ``precision`` in lockstep;
        already-converged directions are cast but not updated, so the result equals
        the per-direction ``BoundarySearchStrategy.search_boundary``.

        Args:
            low: (K,) lower elevation bounds, degrees
            high: (K,) upper elevation bounds, degrees
            boundary: LOWER (returns low) or UPPER (returns high)

        Returns:
            (K,) boundary elevations, degrees
        """
        low = low.astype(float).copy()
        high = high.astype(float).copy()
        is_lower = boundary == BoundaryDirection.LOWER

        while True:
            active = (high - low) > precision
            if not np.any(active):
                break

            mid = (low + high) / 2.0
            directions = Vector3D.directions_from_azimuth_elevation(azimuths, mid)
            hits = RayTriangleIntersector.batch_hits_any(origin, directions, tri_arrays)

            if is_lower:
                # Hit -> obstruction, search higher (low = mid); miss -> high = mid.
                low = np.where(active & hits, mid, low)
                high = np.where(active & ~hits, mid, high)
            else:
                # Hit -> search lower (high = mid); miss -> obstruction above (low = mid).
                high = np.where(active & hits, mid, high)
                low = np.where(active & ~hits, mid, low)

        return low if is_lower else high

    @staticmethod
    def _build_entry(
        direction_angle: float,
        horizon_deg: float,
        zenith_deg: float
    ) -> Dict[str, Any]:
        """Format one direction's response entry (same shape as the async path)."""
        horizon_result, zenith_result = ObstructionResult.from_gap(
            horizon_deg=horizon_deg,
            zenith_deg=zenith_deg,
        )
        return {
            ResponseField.DIRECTION_ANGLE.value: direction_angle,
            ResponseField.HORIZON.value: horizon_result.to_dict(),
            ResponseField.ZENITH.value: zenith_result.to_dict(),
        }

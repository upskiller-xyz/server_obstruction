"""
Gap verification service

Service for verifying sky gaps with ray casting.
"""

import numpy as np

from src.components.calculators.boundary_search_strategy import BoundarySearchStrategy
from src.components.calculators.ray_triangle_intersector import (
    RayTriangleIntersector,
    TriangleArrays,
)
from src.components.geometry.vector import Vector3D
from src.components.models.gap_verification_result import GapVerificationResult
from src.server.base.constants import BoundaryDirection, GapVerificationStatus


class GapVerificationService:
    """Service for verifying sky gaps with ray casting."""

    def __init__(self, boundary_search: BoundarySearchStrategy):
        self._boundary_search = boundary_search

    def verify_gap(
        self,
        gap_low: float,
        gap_high: float,
        origin: np.ndarray,
        direction_angle: float,
        tri_arrays: TriangleArrays,
        precision: float
    ) -> GapVerificationResult:
        """
        Test gap with a single ray, then binary search boundaries if clear.

        Args:
            gap_low: Lower bound of gap, degrees
            gap_high: Upper bound of gap, degrees
            origin: Ray origin, shape (3,)
            direction_angle: Horizontal direction in radians
            tri_arrays: Pre-packed triangle arrays
            precision: Binary search precision, degrees

        Returns:
            GapVerificationResult with status and boundaries if sky found
        """
        # Probe just inside the gap from its lower edge (gap_low + 1°). The gap was
        # detected between two obstructions, so testing near the bottom checks whether
        # sky opens up right above the horizon obstruction; the boundary search below
        # then refines the exact horizon/zenith. Narrow gaps (<1°) fall back to the
        # midpoint.
        test_elevation = gap_low + 1.0
        if test_elevation >= gap_high:
            test_elevation = (gap_low + gap_high) * 0.5

        direction = Vector3D.from_azimuth_elevation(
            direction_angle, test_elevation
        ).to_array()
        hits = RayTriangleIntersector.batch_hits_any(
            origin, direction[np.newaxis, :], tri_arrays
        )

        if hits[0]:
            # Gap is obstructed
            return GapVerificationResult(
                status=GapVerificationStatus.OBSTRUCTED,
                rays_cast=1
            )

        # Sky found! Binary search exact boundaries
        horizon_deg, rays_lower = self._boundary_search.search_boundary(
            origin, direction_angle, tri_arrays,
            gap_low, test_elevation, precision,
            BoundaryDirection.LOWER
        )

        zenith_boundary, rays_upper = self._boundary_search.search_boundary(
            origin, direction_angle, tri_arrays,
            test_elevation, gap_high, precision,
            BoundaryDirection.UPPER
        )

        zenith_deg = 90.0 - zenith_boundary

        return GapVerificationResult(
            status=GapVerificationStatus.SKY_FOUND,
            horizon_deg=horizon_deg,
            zenith_deg=zenith_deg,
            rays_cast=1 + rays_lower + rays_upper
        )

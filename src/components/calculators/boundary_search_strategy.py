"""
Boundary search strategy

Unified binary search strategy for finding gap boundaries (horizon/zenith).
"""

from typing import Tuple

import numpy as np

from src.components.calculators.ray_triangle_intersector import RayTriangleIntersector, TriangleArrays
from src.components.geometry.vector import Vector3D
from src.server.base.constants import BoundaryDirection


class BoundarySearchStrategy:
    """Unified strategy for binary searching gap boundaries."""

    @staticmethod
    def search_boundary(
        origin: np.ndarray,
        direction_angle: float,
        tri_arrays: TriangleArrays,
        low: float,
        high: float,
        precision: float,
        boundary_direction: BoundaryDirection
    ) -> Tuple[float, int]:
        """
        Binary search for gap boundary.

        Args:
            origin: Ray origin, shape (3,)
            direction_angle: Horizontal direction in radians
            tri_arrays: Pre-packed triangle arrays
            low: Lower elevation bound, degrees
            high: Upper elevation bound, degrees
            precision: Stop when range < this, degrees
            boundary_direction: LOWER (horizon) or UPPER (zenith)

        Returns:
            (boundary_elevation_deg, rays_cast)
        """
        rays_cast = 0
        while (high - low) > precision:
            mid = (low + high) / 2.0
            direction = Vector3D.from_azimuth_elevation(
                direction_angle, mid
            ).to_array()
            hits = RayTriangleIntersector.batch_hits_any(
                origin, direction[np.newaxis, :], tri_arrays
            )
            rays_cast += 1

            # Strategy pattern: different update logic based on direction
            if boundary_direction == BoundaryDirection.LOWER:
                # Finding LOWER boundary (highest obstruction before sky gap)
                # If HIT: obstruction exists, search higher for more
                # If MISS: we found the boundary, obstruction is below
                if hits[0]:
                    low = mid  # Hit obstruction, search higher
                else:
                    high = mid  # Missed sky, boundary is below
            else:  # BoundaryDirection.UPPER
                # Finding UPPER boundary (lowest obstruction above sky gap)
                # If HIT: obstruction exists, search lower for where it starts
                # If MISS: obstruction is above, search higher for it
                if hits[0]:
                    high = mid  # Hit obstruction, search lower for boundary
                else:
                    low = mid  # Sky here, obstruction is above, search higher

        # Return appropriate boundary based on direction
        # LOWER: Returns 'low' (highest obstruction angle before sky gap)
        # UPPER: Returns 'high' (lowest obstruction angle above sky gap)
        return (
            low if boundary_direction == BoundaryDirection.LOWER else high,
            rays_cast
        )

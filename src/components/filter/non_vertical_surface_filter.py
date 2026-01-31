"""
Vertical surface filtering for horizon calculations

Filters out horizontal surfaces like roofs, keeping only walls and vertical obstructions.
"""

from typing import List, Tuple
import numpy as np
import logging

from src.components.geometry import Triangle
from src.server.base.constants import ANGLES, MathConstants
from src.components.models import Window
from src.components.filter.base_filter import TriangleFilter
from src.components.filter.distance_filter import DistanceTriangleFilter
from src.utils.settings import Settings

logger = logging.getLogger(__name__)


class NonVerticalSurfaceFilter(TriangleFilter):
    """
    Filter for vertical/near-vertical surfaces (walls) - for horizon calculations

    Filters out horizontal surfaces like roofs, keeping only walls and vertical obstructions.
    """

    @classmethod
    def call(
        cls,
        triangles: Tuple[Triangle, ...],
        window: Window,
        angle_type: ANGLES = ANGLES.ZENITH,
        **kwargs
    ) -> Tuple[Triangle, ...]:
        """
        Filter triangles to only include vertical/near-vertical surfaces

        Args:
            triangles: Input triangles
            window: Window object
            angle_type: Type of angle calculation (default: HORIZON)
            **kwargs: Additional parameters

        Returns:
            List of filtered triangles that are vertical surfaces
        """
        if not triangles:
            return tuple()

        # First apply horizon filter (above, in front, minimum distance)
        filtered = DistanceTriangleFilter.call(triangles, window, angle_type=angle_type)

        if not filtered:
            return tuple()

        # Filter by surface orientation - keep only vertical surfaces
        vertical_triangles = [x for x in filter(cls._is_vertical, filtered)]
        logger.debug(
            f"        [NON-VERTICAL-FILTER] Kept {len(vertical_triangles)}/{len(filtered)} - "
            f"Filtered: {len(filtered) - len(vertical_triangles)} horizontal surfaces"
        )

        return tuple(vertical_triangles)

    @classmethod
    def _is_vertical(cls, triangle: Triangle) -> bool:
        """
        Check if a triangle represents a vertical surface

        Args:
            triangle: Triangle to check

        Returns:
            True if the triangle is vertical (normal has small Z component)
        """
        v1 = triangle.v1.to_array()
        v2 = triangle.v2.to_array()
        v3 = triangle.v3.to_array()

        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = np.cross(edge1, edge2)
        normal_mag = np.linalg.norm(normal)
        if normal_mag < MathConstants.EPSILON.value:
            return True
        normal = normal / normal_mag
        # Check if surface is vertical (normal has small Z component)
        if abs(normal[2]) > Settings().max_vertical_normal_z:
            return True
        return False

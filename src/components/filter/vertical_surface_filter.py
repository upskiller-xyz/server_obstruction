"""
Vertical surface filtering for horizon calculations

Filters out horizontal surfaces like roofs, keeping only walls and vertical obstructions.
"""

import logging
from typing import Tuple

import numpy as np

from src.components.filter.base_filter import TriangleFilter
from src.components.geometry import Triangle
from src.components.models import Window
from src.server.base.constants import ANGLES, MathConstants
from src.utils.settings import Settings


class VerticalSurfaceFilter(TriangleFilter):
    """
    Filter for vertical/near-vertical surfaces (walls) - for horizon calculations

    Filters out horizontal surfaces like roofs, keeping only walls and vertical obstructions.
    """

    @classmethod
    def call(
        cls,
        triangles: Tuple[Triangle, ...],
        window: Window,
        angle_type: ANGLES = ANGLES.HORIZON,
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

        # Filter by surface orientation - keep only vertical surfaces
        relevant_triangles = [x for x in filter(cls._should_keep, triangles)]
        logging.debug(
            f"        [VERTICAL-FILTER] Kept {len(relevant_triangles)}/{len(triangles)} - "
            f"Filtered: {len(triangles) - len(relevant_triangles)} horizontal surfaces"
        )

        return tuple(relevant_triangles)

    @classmethod
    def _should_keep(cls, triangle: Triangle) -> bool:
        """Return True if triangle should be kept (is vertical surface)"""
        return cls._is_vertical(triangle)

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
            return False
        normal = normal / normal_mag
        # Check if surface is vertical (normal has small Z component)
        if abs(normal[2]) > Settings().max_vertical_normal_z:
            return False
        return True

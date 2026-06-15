"""
Height-only triangle filtering for obstruction calculations.

Filters triangles based on their height (Z-axis extent).
Removes triangles that are too short to be relevant for obstruction analysis.
"""

import logging
from typing import Tuple

from src.components.filter.base_filter import TriangleFilter
from src.components.geometry import Triangle
from src.components.models import Window
from src.server.base.constants import ANGLES


class HeightTriangleFilter(TriangleFilter):
    """
    Filter triangles by height only (above window center).

    Used in the split-mesh path where geometry is already classified
    by the caller, so min/max horizontal distance heuristics are not needed.
    """

    @classmethod
    def call(
        cls,
        triangles: Tuple[Triangle, ...],
        window: Window,
        angle_type: ANGLES,
        **kwargs
    ) -> Tuple[Triangle, ...]:
        """
        Filter triangles keeping only those with at least one vertex above window center Z.

        Args:
            triangles: All mesh triangles
            window: Window
            angle_type: Type of angle calculation (unused, kept for interface compatibility)

        Returns:
            Filtered tuple of triangles above window
        """
        if not triangles:
            return tuple()

        vertices_array = cls._vectorize_triangles(triangles)
        above_mask = cls.mask(vertices_array, window)
        return cls._build_filtered_list(triangles, above_mask)

    @classmethod
    def mask(cls, vertices_array: "np.ndarray", window: Window) -> "np.ndarray":
        """
        Height keep-mask directly on an (N, 3, 3) vertex array (array-native).

        Returns:
            Boolean keep-mask (N,) — triangles with at least one vertex above window Z
        """
        return cls._filter_by_height(vertices_array, window.center.z)

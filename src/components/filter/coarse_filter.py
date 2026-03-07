"""
Coarse triangle filtering for initial pre-filtering

Removes triangles below and behind window for all-direction calculations.
"""

from typing import Tuple
import numpy as np

from src.components.geometry import Triangle
from src.server.base.constants import ANGLES
from src.components.models import Window
from src.components.filter.base_filter import TriangleFilter


class CoarseTriangleFilter(TriangleFilter):
    """
    Coarse filter for removing obviously irrelevant triangles

    Filters out triangles that are:
    1. Below the window (Z axis)
    2. Behind the window (opposite to viewing direction)

    Used as a pre-filter for all-direction calculations to reduce
    the number of triangles that need to be processed for each direction.
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
        Coarse filter for triangles (above and not behind window)

        Args:
            triangles: All mesh triangles
            window: Window
            angle_type: Type of angle calculation (ignored)
            **kwargs: Additional parameters

        Returns:
            Filtered list of triangles above and not behind window
        """
        if not triangles:
            return tuple()

        # Vectorize triangles
        vertices_array = cls._vectorize_triangles(triangles)

        # Filter 1: Height (above window)
        above_mask = cls._filter_by_height(vertices_array, window.center.z)

        # Filter 2: Not behind window (simplified - just check if any vertex is not behind)
        vecs = vertices_array - window.center.to_array()
        normal_horizontal, magnitude = cls._compute_horizontal_normal(window.normal)

        if magnitude > 1e-6:
            # Normalize and compute dot product
            normal_horizontal = normal_horizontal / magnitude
            dists = np.dot(vecs, normal_horizontal)
            # Keep if any vertex is ahead of window
            ahead_mask = (dists > 0).any(axis=1)
        else:
            # If window is pointing up/down, just keep all triangles
            ahead_mask = np.ones(len(triangles), dtype=bool)

        # Combine filters
        keep_mask = above_mask & ahead_mask

        return cls._build_filtered_list(triangles, keep_mask)

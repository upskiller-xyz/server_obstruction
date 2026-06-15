"""
Coarse triangle filtering for initial pre-filtering

Removes triangles below and behind window for all-direction calculations.
"""

from typing import Tuple

import numpy as np

from src.components.filter.base_filter import TriangleFilter
from src.components.geometry import Triangle
from src.components.models import Window
from src.server.base.constants import ANGLES


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

        vertices_array = cls._vectorize_triangles(triangles)
        keep_mask = cls.mask(vertices_array, window)
        return cls._build_filtered_list(triangles, keep_mask)

    @classmethod
    def mask(cls, vertices_array: np.ndarray, window: Window) -> np.ndarray:
        """
        Compute the coarse keep-mask directly on an (N, 3, 3) vertex array.

        Array-native — no Triangle objects. Used by the all-directions path so the
        mesh stays numpy end-to-end.

        Returns:
            Boolean keep-mask (N,) — triangles above and not behind the window
        """
        # Filter 1: Height (above window)
        above_mask = cls._filter_by_height(vertices_array, window.center.z)

        # Filter 2: Not behind window (keep if any vertex is ahead of the window)
        vecs = vertices_array - window.center.to_array()
        normal_horizontal, magnitude = cls._compute_horizontal_normal(window.normal)

        if magnitude > 1e-6:
            normal_horizontal = normal_horizontal / magnitude
            dists = np.dot(vecs, normal_horizontal)
            ahead_mask = (dists > 0).any(axis=1)
        else:
            # Window pointing up/down → keep all triangles
            ahead_mask = np.ones(len(vertices_array), dtype=bool)

        return above_mask & ahead_mask

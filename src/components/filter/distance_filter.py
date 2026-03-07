"""
Distance-based triangle filtering for obstruction calculations

Filters triangles based on height and horizontal distance criteria.
"""

from typing import Tuple
import numpy as np
import logging

from src.components.geometry import Triangle
from src.server.base.constants import ANGLES
from src.components.models import Window
from src.components.filter.base_filter import TriangleFilter
from src.components.filter.within_distance_filter import WithinDistanceFilter
from src.utils.settings import Settings


class DistanceTriangleFilter(TriangleFilter):
    """
    Filter triangles for horizon obstruction calculation

    Criteria:
    1. Triangle must be above window (Z axis)
    2. Triangle must be in front of window (following view direction)
    3. Triangle must be at least Settings.min_horizontal_distance away
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
        Filter triangles for horizon obstruction (VECTORIZED)

        Args:
            triangles: All mesh triangles
            window: Window
            angle_type: Type of angle calculation

        Returns:
            Filtered list of relevant triangles
        """
        vecs, above_mask = cls._precompute(triangles, window)
        param = Settings().max_horizontal_distance
        if angle_type == ANGLES.HORIZON:
            param = Settings().min_horizontal_distance
        mask = WithinDistanceFilter.run(window, vecs, angle_type, param)

        cls._removed_stats(triangles, above_mask, mask, angle_type)
        # Combine filters
        keep_mask = above_mask & mask
        # Build result and log stats
        return cls._build_filtered_list(triangles, keep_mask)

    @classmethod
    def _removed_stats(
        cls,
        triangles: Tuple[Triangle, ...],
        above_mask: np.ndarray,
        mask: np.ndarray,
        angle_type: ANGLES
    ) -> None:
        """
        Log filtering statistics

        Args:
            triangles: Original triangles
            above_mask: Mask for triangles above window
            mask: Distance filter mask
            angle_type: Type of angle calculation
        """
        n_triangles = len(triangles)
        keep_mask = above_mask & mask
        stats = {
            'kept': int(keep_mask.sum()),
            'below': int((~above_mask).sum()),
            'too_close_or_behind': int((above_mask & ~mask).sum())
        }

        settings = Settings()
        distance = settings.min_horizontal_distance if angle_type == ANGLES.HORIZON else settings.max_horizontal_distance

        logging.debug(
            f"        [DISTANCE-FILTER] Kept {stats['kept']}/{n_triangles} - "
            f"Filtered: {stats['below']} below window, "
            f"{stats['too_close_or_behind']} outside distance criteria ({distance}m)"
        )

    @classmethod
    def _precompute(
        cls,
        triangles: Tuple[Triangle, ...],
        window: Window
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Precompute vectorized data and height filter

        Args:
            triangles: All mesh triangles
            window: Window

        Returns:
            Tuple of (vertex_vectors, above_mask)
        """
        n_triangles = len(triangles)
        if n_triangles == 0:
            return np.array([]), np.array([])

        # Vectorize triangles
        vertices_array = cls._vectorize_triangles(triangles)

        # Filter 1: Height (above window)
        above_mask = cls._filter_by_height(vertices_array, window.center.z)

        vecs = vertices_array - window.center.to_array()
        return vecs, above_mask

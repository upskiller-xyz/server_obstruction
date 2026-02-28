"""
Height-only triangle filtering for pre-separated mesh obstruction calculations.

When meshes are already separated by type (horizon_mesh / zenith_mesh),
the distance-based filtering is unnecessary — only height matters.
"""

from typing import Tuple
import logging

from src.components.geometry import Triangle
from src.server.base.constants import ANGLES
from src.components.models import Window
from src.components.filter.base_filter import TriangleFilter


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
        above_mask = cls._filter_by_height(vertices_array, window.center.z)

        kept = int(above_mask.sum())
        removed = len(triangles) - kept
        logging.debug(
            f"        [HEIGHT-FILTER] Kept {kept}/{len(triangles)} — "
            f"Filtered: {removed} below window"
        )

        return cls._build_filtered_list(triangles, above_mask)

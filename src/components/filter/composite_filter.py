"""
Composite filter for both horizon and zenith calculations

Optimized to filter for both angle types in a single pass.
"""

from typing import List, Tuple
import logging

from src.components.geometry import Triangle
from src.server.base.constants import ANGLES
from src.components.models import Window
from src.components.filter.distance_filter import DistanceTriangleFilter
from src.components.filter.within_distance_filter import WithinDistanceFilter
from src.utils.settings import Settings

logger = logging.getLogger(__name__)


class CompositeTriangleFilter(DistanceTriangleFilter):
    """
    Filter triangles for BOTH horizon and zenith in a single pass

    Optimized to avoid duplicate vectorization and height filtering.
    """

    @classmethod
    def call(
        cls,
        triangles: Tuple[Triangle, ...],
        window: Window,
        angle_type: ANGLES = ANGLES.HORIZON,
        **kwargs
    ) -> Tuple[Tuple[Triangle, ...], Tuple[Triangle, ...]]:
        """
        Filter triangles for both horizon and zenith simultaneously

        Args:
            triangles: All mesh triangles
            window: Window
            angle_type: Type of angle calculation (ignored for composite filter)
            **kwargs: Additional parameters

        Returns:
            Tuple of (horizon_filtered, zenith_filtered)
        """
        vecs, above_mask = cls._precompute(triangles, window)

        settings = Settings()
        z_mask = WithinDistanceFilter.run(window, vecs, ANGLES.ZENITH, settings.max_horizontal_distance)
        h_mask = WithinDistanceFilter.run(window, vecs, ANGLES.HORIZON, settings.min_horizontal_distance)

        # Build results
        h_filtered = cls._build_filtered_list(triangles, above_mask & h_mask)
        z_filtered = cls._build_filtered_list(triangles, above_mask & z_mask)

        # logger.info(
        #     f"        [COMPOSITE-FILTER] Kept {len(h_filtered)} horizon, "
        #     f"{len(z_filtered)} zenith from {len(triangles)} triangles"
        # )

        return (h_filtered, z_filtered)

"""
Within distance filtering logic

Handles distance-based filtering for both horizontal and vertical scenarios.
"""

import numpy as np

from src.server.base.constants import ANGLES, MathConstants
from src.components.models import Window
from src.components.filter.base_filter import TriangleFilter
from src.utils.settings import Settings


class WithinDistanceFilter:
    """
    Filters triangles based on distance criteria

    Uses Strategy Pattern to handle different distance conditions
    based on angle type and window normal magnitude.
    """

    @classmethod
    def run(
        cls,
        window: Window,
        vecs: np.ndarray,
        angle_type: ANGLES,
        param: float | None
    ) -> np.ndarray:
        """
        Run distance filtering based on window orientation

        Args:
            window: Window object
            vecs: Vertex vectors relative to window center (N, 3, 3)
            angle_type: Type of angle calculation
            param: Distance parameter (min or max)

        Returns:
            Boolean mask of triangles within distance criteria
        """
        _, magnitude = TriangleFilter._compute_horizontal_normal(window.normal)
        _func = cls._large_magnitude
        if magnitude < MathConstants.EPSILON.value:
            _func = cls._small_magnitude
        return _func(vecs, angle_type, param, window).any(axis=1)

    @classmethod
    def _horizontal_s_condition(cls, dists: np.ndarray, param: float) -> np.ndarray:
        """Small magnitude horizontal condition: distance <= param"""
        return dists <= param

    @classmethod
    def _vertical_s_condition(cls, dists: np.ndarray, param: float) -> np.ndarray:
        """Small magnitude vertical condition: distance >= param"""
        return dists >= param

    @classmethod
    def _small_magnitude(
        cls,
        vecs: np.ndarray,
        angle_type: ANGLES,
        param: float | None,
        window: Window
    ) -> np.ndarray:
        """
        Handle filtering when window normal has small horizontal component

        Args:
            vecs: Vertex vectors relative to window center
            angle_type: Type of angle calculation
            param: Distance parameter
            window: Window object (unused in this case)

        Returns:
            Boolean mask for distance filtering
        """
        _sm_map = {
            ANGLES.HORIZON: cls._horizontal_s_condition,
            ANGLES.ZENITH: cls._vertical_s_condition
        }
        if not param:
            param = Settings().max_horizontal_distance

        horiz_vecs = vecs[:, :, :2]  # Only X, Y
        horiz_dists = np.linalg.norm(horiz_vecs, axis=2)
        condition_method = _sm_map.get(angle_type, cls._horizontal_s_condition)
        return condition_method(horiz_dists, param)

    @classmethod
    def _horizontal_l_condition(cls, dists: np.ndarray, param: float) -> np.ndarray:
        """Large magnitude horizontal condition: distance > 0 and >= param"""
        return (dists > 0) & (dists >= param)

    @classmethod
    def _vertical_l_condition(cls, dists: np.ndarray, param: float) -> np.ndarray:
        """Large magnitude vertical condition: distance > 0 and <= param"""
        return (dists > 0) & (dists <= param)

    @classmethod
    def _large_magnitude(
        cls,
        vecs: np.ndarray,
        angle_type: ANGLES,
        param: float | None,
        window: Window
    ) -> np.ndarray:
        """
        Handle filtering when window normal has large horizontal component

        Args:
            vecs: Vertex vectors relative to window center
            angle_type: Type of angle calculation
            param: Distance parameter
            window: Window object

        Returns:
            Boolean mask for distance filtering
        """
        _sm_map = {
            ANGLES.HORIZON: cls._horizontal_l_condition,
            ANGLES.ZENITH: cls._vertical_l_condition
        }
        if not param:
            param = Settings().max_horizontal_distance

        normal_horizontal, magnitude = TriangleFilter._compute_horizontal_normal(window.normal)
        # Normalize horizontal component
        normal_horizontal = normal_horizontal / magnitude
        dists = np.dot(vecs, normal_horizontal)
        return _sm_map.get(angle_type, cls._horizontal_l_condition)(dists, param)

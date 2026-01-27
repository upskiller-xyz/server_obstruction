"""
Horizontal distance calculator

Calculates horizontal distance from a point to the window along viewing direction.
"""

import numpy as np

from src.components.geometry import Point3D, CoordinateSystem
from src.components.models import Window
from src.server.base.constants import MathConstants


class HorizontalDistanceCalculator:
    """
    Calculator for horizontal distances along viewing direction

    Encapsulates the logic for calculating horizontal distance from a point
    to the window center, projected onto the horizontal plane.
    """

    @staticmethod
    def calculate(
        point: Point3D,
        window: Window
    ) -> float:
        """
        Calculate horizontal distance from point to window along viewing direction

        Args:
            point: 3D point
            window: Window with center position and viewing direction

        Returns:
            Horizontal distance in meters
        """
        # Get horizontal component of viewing direction
        normal_horizontal = window.normal.get_horizontal().to_array()
        normal_horizontal_mag = np.linalg.norm(normal_horizontal)

        # Vector from window to point
        point_vec = point.to_array() - window.center.to_array()

        if normal_horizontal_mag < MathConstants.EPSILON.value:
            # Viewing straight up or down, use direct horizontal distance
            point_horizontal = CoordinateSystem.remove_vertical_component(point_vec)
            return float(np.linalg.norm(point_horizontal))

        # Normalize horizontal viewing direction and project
        normal_horizontal = normal_horizontal / normal_horizontal_mag
        return abs(float(np.dot(point_vec, normal_horizontal)))

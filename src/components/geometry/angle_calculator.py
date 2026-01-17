"""
Angle calculation utilities

Calculator for obstruction angles from vertical and horizontal distances.
"""

from typing import Callable, Dict
import numpy as np

from src.server.base.constants import ANGLES, MathConstants


class AngleCalculator:
    """
    Calculator for obstruction angles

    Encapsulates the logic for calculating angles from vertical and horizontal distances
    """

    @staticmethod
    def radians_to_degrees(radians: float) -> float:
        """
        Convert radians to degrees

        Args:
            radians: Angle in radians

        Returns:
            Angle in degrees
        """
        return float(np.degrees(radians))

    @staticmethod
    def horizon_angle(
        vertical_distance: float,
        horizontal_distance: float
    ) -> float:
        """
        Calculate obstruction angle from vertical and horizontal distances

        Args:
            vertical_distance: Vertical distance (height difference)
            horizontal_distance: Horizontal distance along viewing direction

        Returns:
            Angle in radians (0 to π/2)
        """
        # Handle case where point is directly above (infinite angle)
        if horizontal_distance < MathConstants.EPSILON.value:
            return float(np.pi * 0.5)  # 90 degrees

        # Calculate angle using arctan
        return float(np.arctan(vertical_distance / horizontal_distance))

    @staticmethod
    def zenith_angle(
        vertical_distance: float,
        horizontal_distance: float
    ) -> float:
        """
        Calculate zenith angle from vertical and horizontal distances

        Zenith angle is measured from vertical: 90° - elevation_angle

        Args:
            vertical_distance: Vertical distance (positive = above)
            horizontal_distance: Horizontal distance along viewing direction

        Returns:
            Angle in radians (0 to π/2)
        """
        # Point directly overhead
        if horizontal_distance < MathConstants.EPSILON.value:
            return 0.0

        elevation_angle = float(np.arctan(vertical_distance / horizontal_distance))
        return (np.pi / 2) - elevation_angle

    _content: Dict[ANGLES, Callable] = {
        ANGLES.HORIZON: horizon_angle,
        ANGLES.ZENITH: zenith_angle
    }

    @classmethod
    def call(
        cls,
        vertical_distance: float,
        horizontal_distance: float,
        angle: ANGLES = ANGLES.HORIZON
    ) -> float:
        """
        Calculate angle using the specified angle type

        Args:
            vertical_distance: Vertical distance (height difference)
            horizontal_distance: Horizontal distance along viewing direction
            angle: Type of angle calculation (HORIZON or ZENITH)

        Returns:
            Angle in radians
        """
        method = cls._content.get(angle, cls.horizon_angle)
        return method(vertical_distance, horizontal_distance)

"""Obstruction angle calculator with filtering"""

from typing import Optional

import numpy as np

from src.components.calculators import AngleCalculator
from src.components.calculators.geometric_distance_calculator import GeometricDistanceCalculator
from src.components.geometry import Point3D
from src.components.models import Window
from src.server.base.constants import ANGLES
from src.utils.settings import Settings


class ObstructionAngleCalculator:
    """
    Calculates obstruction angles with built-in filtering

    Single Responsibility:
    - Only calculates obstruction angles from points
    - Applies angle filtering rules
    - Does NOT perform geometric intersections
    """

    @classmethod
    def calculate(
        cls,
        point: Point3D,
        window: Window,
        angle_type: ANGLES = ANGLES.HORIZON
    ) -> Optional[float]:
        """
        Calculate obstruction angle from window to point with filtering

        Args:
            point: Intersection point
            window: Window with center and normal
            angle_type: Type of angle (HORIZON or ZENITH)

        Returns:
            Obstruction angle in radians, or None if point is invalid
        """
        # Calculate vertical distance
        vertical_distance = point.z - window.center.z

        # FILTER 1: Skip points below window (both horizon and zenith look upwards)
        if vertical_distance <= 0:
            return None

        # Calculate horizontal distance along viewing direction
        horizontal_distance = GeometricDistanceCalculator.horizontal_distance(
            point, window
        )

        # FILTER 2: Skip points behind window
        if horizontal_distance < 0:
            return None

        # Calculate angle using appropriate method
        angle = AngleCalculator.call(
            vertical_distance, horizontal_distance, angle_type
        )

        if angle is None:
            return None

        # FILTER 3: Skip angles too steep (likely roof, not horizon obstruction)
        max_angle_rad = np.radians(Settings.max_angle_degrees)
        if angle > max_angle_rad:
            return None

        return angle

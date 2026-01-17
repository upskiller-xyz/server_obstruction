import math
import numpy as np
from typing import List
from src.server.base.constants import AllDirectionDefaults


class DirectionCalculator:
    """
    Calculator for multi-direction obstruction angles

    Implements the half-circle coordinate system:
    - 0° = 90° counter-clockwise from window normal (left edge)
    - 90° = window normal direction (straight ahead)
    - 180° = 90° clockwise from window normal (right edge)

    Follows Single Responsibility Principle:
    - Only handles direction angle calculations
    - Separate from obstruction calculations
    """

    @staticmethod
    def calculate_direction_angles(
        base_direction_radians: float,
        num_directions: int | None = None,
        start_angle_degrees: float | None = None,
        end_angle_degrees: float | None = None
    ) -> np.ndarray:
        """
        Calculate absolute direction angles for multi-direction obstruction

        Args:
            base_direction_radians: Window's base direction in radians
            num_directions: Number of directions to sample (default 64)
            start_angle_degrees: Start angle relative to window normal (default 17.5°)
            end_angle_degrees: End angle relative to window normal (default 162.5°)

        Returns:
            Array of absolute direction angles in radians
        """
        # Apply defaults using Enumerator Pattern
        if num_directions is None:
            num_directions = AllDirectionDefaults.NUM_DIRECTIONS.value
        if start_angle_degrees is None:
            start_angle_degrees = AllDirectionDefaults.START_ANGLE_DEGREES.value
        if end_angle_degrees is None:
            end_angle_degrees = AllDirectionDefaults.END_ANGLE_DEGREES.value

        # Convert to radians
        start_angle_rad = math.radians(start_angle_degrees)
        end_angle_rad = math.radians(end_angle_degrees)

        # Generate evenly spaced angles in half-circle
        half_circle_angles = np.linspace(start_angle_rad, end_angle_rad, num_directions)

        # Transform to absolute world directions
        # half_circle angle is measured from left edge (-90° from normal)
        absolute_angles = base_direction_radians - (math.pi / 2) + half_circle_angles

        return absolute_angles

    @staticmethod
    def get_direction_angles_degrees(
        base_direction_radians: float,
        num_directions: int | None = None,
        start_angle_degrees: float | None = None,
        end_angle_degrees: float | None = None
    ) -> List[float]:
        """
        Get direction angles in degrees (for response formatting)

        Args:
            base_direction_radians: Window's base direction in radians
            num_directions: Number of directions to sample
            start_angle_degrees: Start angle relative to window normal
            end_angle_degrees: End angle relative to window normal

        Returns:
            List of absolute direction angles in degrees
        """
        angles_rad = DirectionCalculator.calculate_direction_angles(
            base_direction_radians, num_directions, start_angle_degrees, end_angle_degrees
        )
        return [math.degrees(angle) for angle in angles_rad]

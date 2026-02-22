import pytest
import numpy as np
from src.components.calculators.angle_calculator import AngleCalculator
from src.server.base.constants import ANGLES


class TestAngleCalculator:
    """Test cases for AngleCalculator class (from src.components.calculators)"""

    def test_horizon_angle_horizontal(self):
        """Test horizon angle for horizontal distance"""
        vertical_distance = 0.0
        horizontal_distance = 10.0

        angle_rad = AngleCalculator.horizon_angle(vertical_distance, horizontal_distance)
        angle_deg = AngleCalculator.radians_to_degrees(angle_rad)

        assert abs(angle_deg) < 0.01

    def test_horizon_angle_45_degrees(self):
        """Test horizon angle for 45 degree obstruction"""
        vertical_distance = 10.0
        horizontal_distance = 10.0

        angle_rad = AngleCalculator.horizon_angle(vertical_distance, horizontal_distance)
        angle_deg = AngleCalculator.radians_to_degrees(angle_rad)

        assert abs(angle_deg - 45.0) < 0.01

    def test_horizon_angle_negative(self):
        """Test horizon angle for point below reference"""
        vertical_distance = -10.0
        horizontal_distance = 10.0

        angle_rad = AngleCalculator.horizon_angle(vertical_distance, horizontal_distance)
        angle_deg = AngleCalculator.radians_to_degrees(angle_rad)

        assert abs(angle_deg + 45.0) < 0.01

    def test_zenith_angle_horizontal(self):
        """Test zenith angle for horizontal point (90 degrees from vertical)"""
        vertical_distance = 0.0
        horizontal_distance = 10.0

        angle_rad = AngleCalculator.zenith_angle(vertical_distance, horizontal_distance)
        angle_deg = AngleCalculator.radians_to_degrees(angle_rad)

        assert abs(angle_deg - 90.0) < 0.01

    def test_zenith_angle_vertical(self):
        """Test zenith angle for vertical point (0 degrees from vertical)"""
        vertical_distance = 10.0
        horizontal_distance = 0.001

        angle_rad = AngleCalculator.zenith_angle(vertical_distance, horizontal_distance)
        angle_deg = AngleCalculator.radians_to_degrees(angle_rad)

        assert abs(angle_deg) < 0.5

    def test_call_with_horizon_type(self):
        """Test call method with HORIZON angle type"""
        vertical_distance = 10.0
        horizontal_distance = 10.0

        angle_rad = AngleCalculator.call(vertical_distance, horizontal_distance, ANGLES.HORIZON)
        angle_deg = AngleCalculator.radians_to_degrees(angle_rad)

        assert abs(angle_deg - 45.0) < 0.01

    def test_call_with_zenith_type(self):
        """Test call method with ZENITH angle type"""
        vertical_distance = 0.0
        horizontal_distance = 10.0

        angle_rad = AngleCalculator.call(vertical_distance, horizontal_distance, ANGLES.ZENITH)
        angle_deg = AngleCalculator.radians_to_degrees(angle_rad)

        assert abs(angle_deg - 90.0) < 0.01

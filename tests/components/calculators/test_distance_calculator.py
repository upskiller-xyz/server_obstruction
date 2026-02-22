import pytest
import numpy as np
from src.components.calculators.distance_calculator import DistanceCalculator
from src.components.geometry import Point3D, Vector3D
from src.components.models import Window
from src.server.base.constants import ANGLES


class TestDistanceCalculator:
    """Test cases for DistanceCalculator class"""

    def test_get_vertical_distances(self):
        """Test extraction of vertical distances (z-coordinates)"""
        intersections = [
            Point3D(x=1.0, y=2.0, z=5.0),
            Point3D(x=2.0, y=3.0, z=10.0),
            Point3D(x=3.0, y=4.0, z=3.0)
        ]

        vertical_distances = DistanceCalculator._get_vertical(intersections)

        assert len(vertical_distances) == 3
        assert vertical_distances == [5.0, 10.0, 3.0]

    def test_get_horizontal_distances(self):
        """Test extraction of horizontal distances"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        intersections = [
            Point3D(x=5.0, y=0.0, z=1.0),
            Point3D(x=10.0, y=0.0, z=2.0),
        ]

        horizontal_distances = DistanceCalculator._get_horizontal(intersections, window)

        assert len(horizontal_distances) == 2
        assert all(d > 0 for d in horizontal_distances)

    def test_call_with_horizon_angle(self):
        """Test call method with HORIZON angle type returns vertical distances"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        intersections = [
            Point3D(x=1.0, y=2.0, z=5.0),
            Point3D(x=2.0, y=3.0, z=10.0)
        ]

        result = DistanceCalculator.call(intersections, ANGLES.HORIZON, window)

        assert len(result) == 2
        assert result == [5.0, 10.0]

    def test_call_with_zenith_angle(self):
        """Test call method with ZENITH angle type returns horizontal distances"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        intersections = [
            Point3D(x=5.0, y=0.0, z=1.0),
            Point3D(x=10.0, y=0.0, z=2.0),
        ]

        result = DistanceCalculator.call(intersections, ANGLES.ZENITH, window)

        assert len(result) <= 2
        assert all(d > 0 for d in result)

    def test_adjust_horizontal_filters_points_below_window(self):
        """Test that points below window are filtered out"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=5.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        point_below = Point3D(x=10.0, y=0.0, z=2.0)

        result = DistanceCalculator._adjust_horizontal(point_below, window)

        assert result is None

    def test_adjust_horizontal_accepts_points_above_window(self):
        """Test that points above window are accepted"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        point_above = Point3D(x=10.0, y=0.0, z=5.0)

        result = DistanceCalculator._adjust_horizontal(point_above, window)

        assert result is not None
        assert result > 0

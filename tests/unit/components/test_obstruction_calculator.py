import pytest
import numpy as np
from src.components.geometry import Point3D
from src.components.raytracing_models import ProjectedPoint
from src.components.obstruction_calculator import (
    MaxHeightObstructionCalculator,
    WorstCaseObstructionCalculator
)


class TestMaxHeightObstructionCalculator:
    """Test cases for MaxHeightObstructionCalculator class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.calculator = MaxHeightObstructionCalculator()

    def test_empty_points_returns_zero(self):
        """Test that empty point list returns zero obstruction"""
        result = self.calculator.calculate_obstruction_angle([], reference_height=0.0)

        assert result.obstruction_angle_degrees == 0.0
        assert result.obstruction_angle_radians == 0.0
        assert result.highest_point is None
        assert result.projected_point_count == 0

    def test_single_point_above_reference(self):
        """Test with single point above reference height"""
        original = Point3D(x=10.0, y=10.0, z=0.0)
        points = [ProjectedPoint(u=10.0, v=10.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # Should be 45 degrees (arctangent of 10/10 = 1)
        assert abs(result.obstruction_angle_degrees - 45.0) < 0.01
        assert abs(result.obstruction_angle_radians - np.pi/4) < 0.01
        assert result.highest_point == original
        assert result.projected_point_count == 1

    def test_single_point_below_reference(self):
        """Test with single point below reference height"""
        original = Point3D(x=10.0, y=-5.0, z=0.0)
        points = [ProjectedPoint(u=10.0, v=-5.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert result.obstruction_angle_degrees == 0.0
        assert result.obstruction_angle_radians == 0.0
        assert result.highest_point == original
        assert result.projected_point_count == 1

    def test_point_at_reference_height(self):
        """Test with point at reference height"""
        original = Point3D(x=10.0, y=0.0, z=0.0)
        points = [ProjectedPoint(u=10.0, v=0.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert result.obstruction_angle_degrees == 0.0
        assert result.obstruction_angle_radians == 0.0

    def test_point_directly_above(self):
        """Test with point directly above (u=0, v>0)"""
        original = Point3D(x=0.0, y=10.0, z=0.0)
        points = [ProjectedPoint(u=0.0, v=10.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # Should be 90 degrees (vertical)
        assert abs(result.obstruction_angle_degrees - 90.0) < 0.01
        assert abs(result.obstruction_angle_radians - np.pi/2) < 0.01

    def test_multiple_points_selects_highest(self):
        """Test that calculator selects the highest point"""
        points = [
            ProjectedPoint(u=10.0, v=5.0, original=Point3D(x=1.0, y=5.0, z=0.0)),
            ProjectedPoint(u=10.0, v=15.0, original=Point3D(x=1.0, y=15.0, z=0.0)),
            ProjectedPoint(u=10.0, v=10.0, original=Point3D(x=1.0, y=10.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # Should use the point at v=15
        assert result.highest_point.y == 15.0
        assert result.projected_point_count == 3

    def test_steep_angle(self):
        """Test with steep obstruction angle"""
        original = Point3D(x=1.0, y=100.0, z=0.0)
        points = [ProjectedPoint(u=1.0, v=100.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # arctan(100/1) ≈ 89 degrees
        assert result.obstruction_angle_degrees > 89.0
        assert result.obstruction_angle_degrees < 90.0

    def test_shallow_angle(self):
        """Test with shallow obstruction angle"""
        original = Point3D(x=100.0, y=1.0, z=0.0)
        points = [ProjectedPoint(u=100.0, v=1.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # arctan(1/100) ≈ 0.57 degrees
        assert result.obstruction_angle_degrees > 0.5
        assert result.obstruction_angle_degrees < 1.0

    def test_negative_u_coordinate(self):
        """Test with negative u coordinate (point behind)"""
        original = Point3D(x=-10.0, y=10.0, z=0.0)
        points = [ProjectedPoint(u=-10.0, v=10.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # Should use absolute value of u
        assert abs(result.obstruction_angle_degrees - 45.0) < 0.01

    def test_non_zero_reference_height(self):
        """Test with non-zero reference height"""
        original = Point3D(x=10.0, y=15.0, z=0.0)
        points = [ProjectedPoint(u=10.0, v=15.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=5.0)

        # Vertical distance is 15 - 5 = 10
        # arctan(10/10) = 45 degrees
        assert abs(result.obstruction_angle_degrees - 45.0) < 0.01


class TestWorstCaseObstructionCalculator:
    """Test cases for WorstCaseObstructionCalculator class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.calculator = WorstCaseObstructionCalculator()

    def test_empty_points_returns_zero(self):
        """Test that empty point list returns zero obstruction"""
        result = self.calculator.calculate_obstruction_angle([], reference_height=0.0)

        assert result.obstruction_angle_degrees == 0.0
        assert result.obstruction_angle_radians == 0.0
        assert result.highest_point is None
        assert result.projected_point_count == 0

    def test_single_point_above_reference(self):
        """Test with single point above reference height"""
        original = Point3D(x=10.0, y=10.0, z=0.0)
        points = [ProjectedPoint(u=10.0, v=10.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert abs(result.obstruction_angle_degrees - 45.0) < 0.01
        assert result.highest_point == original

    def test_all_points_below_reference(self):
        """Test with all points below reference height"""
        points = [
            ProjectedPoint(u=10.0, v=-5.0, original=Point3D(x=1.0, y=-5.0, z=0.0)),
            ProjectedPoint(u=10.0, v=-10.0, original=Point3D(x=2.0, y=-10.0, z=0.0)),
            ProjectedPoint(u=10.0, v=-2.0, original=Point3D(x=3.0, y=-2.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert result.obstruction_angle_degrees == 0.0

    def test_worst_case_not_highest_point(self):
        """Test that worst case may not be the highest point"""
        # Point closer with medium height may have steeper angle than
        # point farther away with greater height
        points = [
            # Close point, medium height: arctan(10/5) ≈ 63.4 degrees
            ProjectedPoint(u=5.0, v=10.0, original=Point3D(x=1.0, y=10.0, z=0.0)),
            # Far point, higher: arctan(15/20) ≈ 36.9 degrees
            ProjectedPoint(u=20.0, v=15.0, original=Point3D(x=2.0, y=15.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # Should select the closer point (steeper angle)
        assert result.highest_point.x == 1.0
        assert result.obstruction_angle_degrees > 60.0

    def test_multiple_points_same_angle(self):
        """Test with multiple points having same angle"""
        points = [
            ProjectedPoint(u=10.0, v=10.0, original=Point3D(x=1.0, y=10.0, z=0.0)),
            ProjectedPoint(u=20.0, v=20.0, original=Point3D(x=2.0, y=20.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # Both have 45 degree angle
        assert abs(result.obstruction_angle_degrees - 45.0) < 0.01

    def test_point_directly_above(self):
        """Test with point directly above"""
        original = Point3D(x=0.0, y=10.0, z=0.0)
        points = [ProjectedPoint(u=0.0, v=10.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert abs(result.obstruction_angle_degrees - 90.0) < 0.01

    def test_mixed_heights_selects_worst(self):
        """Test that worst case angle is selected"""
        points = [
            # 45 degrees
            ProjectedPoint(u=10.0, v=10.0, original=Point3D(x=1.0, y=10.0, z=0.0)),
            # ~26.6 degrees
            ProjectedPoint(u=20.0, v=10.0, original=Point3D(x=2.0, y=10.0, z=0.0)),
            # ~71.6 degrees (worst case)
            ProjectedPoint(u=5.0, v=15.0, original=Point3D(x=3.0, y=15.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # Should select the steepest angle (last point)
        assert result.highest_point.x == 3.0
        assert result.obstruction_angle_degrees > 70.0

    def test_negative_u_coordinates(self):
        """Test with negative u coordinates"""
        points = [
            ProjectedPoint(u=-10.0, v=10.0, original=Point3D(x=-1.0, y=10.0, z=0.0)),
            ProjectedPoint(u=-5.0, v=5.0, original=Point3D(x=-2.0, y=5.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # Should use absolute values
        assert result.obstruction_angle_degrees > 0.0
        assert result.projected_point_count == 2

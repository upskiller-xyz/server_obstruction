import pytest
import numpy as np
from src.components.geometry import Point3D, Vector3D
from src.components.raytracing_models import ProjectedPoint
from src.components.obstruction_calculator import (
    MaxHeightObstructionCalculator,
    WorstCaseObstructionCalculator,
    ZenithAngleCalculator
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
        """Test with vertical wall triangle above reference height"""
        # Vertical triangle at X=10, top at Y=10
        points = [
            ProjectedPoint(u=10.0, v=0.0, original=Point3D(x=10.0, y=0.0, z=-1.0)),
            ProjectedPoint(u=10.0, v=0.0, original=Point3D(x=10.0, y=0.0, z=1.0)),
            ProjectedPoint(u=10.0, v=10.0, original=Point3D(x=10.0, y=10.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # Should be 45 degrees (arctangent of 10/10 = 1)
        assert abs(result.obstruction_angle_degrees - 45.0) < 0.01
        assert abs(result.obstruction_angle_radians - np.pi/4) < 0.01
        assert result.highest_point.y == 10.0
        assert result.projected_point_count == 3

    def test_single_point_below_reference(self):
        """Test with vertical wall below reference height"""
        # Vertical triangle entirely below Y=0
        points = [
            ProjectedPoint(u=10.0, v=-5.0, original=Point3D(x=10.0, y=-5.0, z=-1.0)),
            ProjectedPoint(u=10.0, v=-5.0, original=Point3D(x=10.0, y=-5.0, z=1.0)),
            ProjectedPoint(u=10.0, v=-2.0, original=Point3D(x=10.0, y=-2.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert result.obstruction_angle_degrees == 0.0
        assert result.obstruction_angle_radians == 0.0
        assert result.highest_point.y == -2.0  # Highest point of the triangle
        assert result.projected_point_count == 3

    def test_point_at_reference_height(self):
        """Test with point at reference height"""
        original = Point3D(x=10.0, y=0.0, z=0.0)
        points = [ProjectedPoint(u=10.0, v=0.0, original=original)]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert result.obstruction_angle_degrees == 0.0
        assert result.obstruction_angle_radians == 0.0

    def test_point_directly_above(self):
        """Test with vertical wall directly above (very close to window)"""
        points = [
            ProjectedPoint(u=0.1, v=0.0, original=Point3D(x=0.1, y=0.0, z=-0.5)),
            ProjectedPoint(u=0.1, v=0.0, original=Point3D(x=0.1, y=0.0, z=0.5)),
            ProjectedPoint(u=0.1, v=10.0, original=Point3D(x=0.1, y=10.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        # Should be close to 90 degrees
        assert abs(result.obstruction_angle_degrees - 90.0) < 1.0

    def test_multiple_points_selects_highest(self):
        """Test that calculator selects the highest point from vertical surface"""
        points = [
            ProjectedPoint(u=1.0, v=5.0, original=Point3D(x=1.0, y=5.0, z=-0.5)),
            ProjectedPoint(u=1.0, v=5.0, original=Point3D(x=1.0, y=5.0, z=0.5)),
            ProjectedPoint(u=1.0, v=15.0, original=Point3D(x=1.0, y=15.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert result.highest_point.y == 15.0
        assert result.projected_point_count == 3

    def test_steep_angle(self):
        """Test with steep vertical wall obstruction angle"""
        points = [
            ProjectedPoint(u=1.0, v=0.0, original=Point3D(x=1.0, y=0.0, z=-0.5)),
            ProjectedPoint(u=1.0, v=0.0, original=Point3D(x=1.0, y=0.0, z=0.5)),
            ProjectedPoint(u=1.0, v=100.0, original=Point3D(x=1.0, y=100.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert result.obstruction_angle_degrees > 89.0
        assert result.obstruction_angle_degrees < 90.0

    def test_shallow_angle(self):
        """Test with shallow vertical wall obstruction angle"""
        points = [
            ProjectedPoint(u=100.0, v=0.0, original=Point3D(x=100.0, y=0.0, z=-0.5)),
            ProjectedPoint(u=100.0, v=0.0, original=Point3D(x=100.0, y=0.0, z=0.5)),
            ProjectedPoint(u=100.0, v=1.0, original=Point3D(x=100.0, y=1.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert result.obstruction_angle_degrees > 0.5
        assert result.obstruction_angle_degrees < 1.0

    def test_negative_u_coordinate(self):
        """Test with vertical wall at negative X (behind window)"""
        points = [
            ProjectedPoint(u=-10.0, v=0.0, original=Point3D(x=-10.0, y=0.0, z=-0.5)),
            ProjectedPoint(u=-10.0, v=0.0, original=Point3D(x=-10.0, y=0.0, z=0.5)),
            ProjectedPoint(u=-10.0, v=10.0, original=Point3D(x=-10.0, y=10.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=0.0)

        assert abs(result.obstruction_angle_degrees - 45.0) < 0.01

    def test_non_zero_reference_height(self):
        """Test with non-zero reference height on vertical wall"""
        points = [
            ProjectedPoint(u=10.0, v=5.0, original=Point3D(x=10.0, y=5.0, z=-0.5)),
            ProjectedPoint(u=10.0, v=5.0, original=Point3D(x=10.0, y=5.0, z=0.5)),
            ProjectedPoint(u=10.0, v=15.0, original=Point3D(x=10.0, y=15.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(points, reference_height=5.0)

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


class TestZenithAngleCalculator:
    """Test cases for ZenithAngleCalculator class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.calculator = ZenithAngleCalculator()
        # Default window center and normal for tests
        self.window_center = Point3D(x=0.0, y=3.0, z=0.0)
        self.window_normal = Vector3D(x=1.0, y=0.0, z=0.0)

    def test_empty_points_returns_zero(self):
        """Test that empty point list returns zero zenith angle"""
        result = self.calculator.calculate_obstruction_angle(
            [],
            reference_height=0.0,
            window_center=self.window_center,
            window_normal=self.window_normal
        )

        assert result.obstruction_angle_degrees == 0.0
        assert result.obstruction_angle_radians == 0.0
        assert result.highest_point is None
        assert result.projected_point_count == 0

    def test_no_overhead_points_returns_zero(self):
        """Test that points below window center return zero zenith angle"""
        points = [
            ProjectedPoint(u=10.0, v=2.0, original=Point3D(x=10.0, y=2.0, z=0.0)),
            ProjectedPoint(u=10.0, v=1.0, original=Point3D(x=10.0, y=1.0, z=0.0)),
            ProjectedPoint(u=10.0, v=0.5, original=Point3D(x=10.0, y=0.5, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(
            points,
            reference_height=0.0,
            window_center=self.window_center,
            window_normal=self.window_normal
        )

        assert result.obstruction_angle_degrees == 0.0
        assert result.obstruction_angle_radians == 0.0

    def test_overhead_point_calculates_zenith_angle(self):
        """Test zenith angle calculation with horizontal overhead surface"""
        # Horizontal triangle at Y=5 (2m above window at Y=3)
        # Horizontal surface at X=10m away
        # Elevation angle = arctan(2/10) ≈ 11.31°
        # Zenith angle = 90° - 11.31° ≈ 78.69°
        points = [
            ProjectedPoint(u=10.0, v=5.0, original=Point3D(x=10.0, y=5.0, z=-1.0)),
            ProjectedPoint(u=10.0, v=5.0, original=Point3D(x=10.0, y=5.0, z=1.0)),
            ProjectedPoint(u=11.0, v=5.0, original=Point3D(x=11.0, y=5.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(
            points,
            reference_height=0.0,
            window_center=self.window_center,
            window_normal=self.window_normal
        )

        assert abs(result.obstruction_angle_degrees - 78.69) < 1.5
        assert result.highest_point.y == 5.0
        assert result.projected_point_count == 3

    def test_point_directly_overhead(self):
        """Test with horizontal surface directly above window"""
        # Horizontal triangle at (0.1, 13, Z) - 10m above window at (0, 3, 0)
        # Should be close to 0° zenith angle (straight up)
        points = [
            ProjectedPoint(u=0.1, v=13.0, original=Point3D(x=0.1, y=13.0, z=-0.5)),
            ProjectedPoint(u=0.1, v=13.0, original=Point3D(x=0.1, y=13.0, z=0.5)),
            ProjectedPoint(u=0.5, v=13.0, original=Point3D(x=0.5, y=13.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(
            points,
            reference_height=0.0,
            window_center=self.window_center,
            window_normal=self.window_normal
        )

        # Should be very small angle (close to vertical)
        assert result.obstruction_angle_degrees < 3.0

    def test_horizontal_overhead_obstruction(self):
        """Test with horizontal overhead surface at horizon level"""
        # Horizontal triangle far away but only slightly above window
        # Should have large zenith angle (close to 90°)
        points = [
            ProjectedPoint(u=100.0, v=4.0, original=Point3D(x=100.0, y=4.0, z=-1.0)),
            ProjectedPoint(u=100.0, v=4.0, original=Point3D(x=100.0, y=4.0, z=1.0)),
            ProjectedPoint(u=101.0, v=4.0, original=Point3D(x=101.0, y=4.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(
            points,
            reference_height=0.0,
            window_center=self.window_center,
            window_normal=self.window_normal
        )

        # arctan(1/100) ≈ 0.57°, zenith angle ≈ 89.43°
        assert result.obstruction_angle_degrees > 89.0
        assert result.obstruction_angle_degrees < 90.0

    def test_multiple_overhead_points_selects_furthest(self):
        """Test that calculator selects the furthest overhead point along viewing direction"""
        # Create horizontal triangle at Y=5 (above window)
        points = [
            ProjectedPoint(u=5.0, v=5.0, original=Point3D(x=5.0, y=5.0, z=-0.5)),
            ProjectedPoint(u=5.0, v=5.0, original=Point3D(x=5.0, y=5.0, z=0.5)),
            ProjectedPoint(u=8.0, v=5.0, original=Point3D(x=8.0, y=5.0, z=0.0))  # Furthest along X
        ]

        result = self.calculator.calculate_obstruction_angle(
            points,
            reference_height=0.0,
            window_center=self.window_center,
            window_normal=self.window_normal
        )

        # Should use the point at x=8 (furthest along viewing direction)
        assert result.highest_point.x == 8.0
        assert result.projected_point_count == 3

    def test_mixed_points_filters_below_window(self):
        """Test that triangles below window center are ignored"""
        # Triangle 1: Below window (should be ignored)
        # Triangle 2: Above window (horizontal surface)
        points = [
            ProjectedPoint(u=10.0, v=1.0, original=Point3D(x=10.0, y=1.0, z=-0.5)),  # Below
            ProjectedPoint(u=10.0, v=1.0, original=Point3D(x=10.0, y=1.0, z=0.5)),   # Below
            ProjectedPoint(u=11.0, v=1.0, original=Point3D(x=11.0, y=1.0, z=0.0)),   # Below
            ProjectedPoint(u=10.0, v=5.0, original=Point3D(x=10.0, y=5.0, z=-0.5)),  # Above - horizontal
            ProjectedPoint(u=10.0, v=5.0, original=Point3D(x=10.0, y=5.0, z=0.5)),   # Above - horizontal
            ProjectedPoint(u=11.0, v=5.0, original=Point3D(x=11.0, y=5.0, z=0.0))    # Above - horizontal
        ]

        result = self.calculator.calculate_obstruction_angle(
            points,
            reference_height=0.0,
            window_center=self.window_center,
            window_normal=self.window_normal
        )

        # Should only consider the overhead horizontal surface at y=5
        assert result.highest_point.y == 5.0

    def test_steep_zenith_angle(self):
        """Test with close horizontal overhead obstruction (steep zenith angle)"""
        # Horizontal surface very close horizontally but high above
        # Should have small zenith angle
        points = [
            ProjectedPoint(u=1.0, v=103.0, original=Point3D(x=1.0, y=103.0, z=-0.5)),
            ProjectedPoint(u=1.0, v=103.0, original=Point3D(x=1.0, y=103.0, z=0.5)),
            ProjectedPoint(u=1.5, v=103.0, original=Point3D(x=1.5, y=103.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(
            points,
            reference_height=0.0,
            window_center=self.window_center,
            window_normal=self.window_normal
        )

        # arctan(100/1) ≈ 89°, zenith angle ≈ 1°
        assert result.obstruction_angle_degrees < 2.0

    def test_shallow_zenith_angle(self):
        """Test with far horizontal overhead obstruction (shallow zenith angle)"""
        # Horizontal triangle far away but only slightly above
        # Should have large zenith angle (close to 90°)
        points = [
            ProjectedPoint(u=100.0, v=4.0, original=Point3D(x=100.0, y=4.0, z=-1.0)),
            ProjectedPoint(u=100.0, v=4.0, original=Point3D(x=100.0, y=4.0, z=1.0)),
            ProjectedPoint(u=101.0, v=4.0, original=Point3D(x=101.0, y=4.0, z=0.0))
        ]

        result = self.calculator.calculate_obstruction_angle(
            points,
            reference_height=0.0,
            window_center=self.window_center,
            window_normal=self.window_normal
        )

        # arctan(1/100) ≈ 0.57°, zenith angle ≈ 89.43°
        assert result.obstruction_angle_degrees > 89.0

    def test_vertical_surface_has_zero_zenith(self):
        """Test that vertical surfaces do not create zenith angle obstruction"""
        # Vertical triangle (all points at same X,Y, different Z) - NOT a horizontal surface
        # Zenith angle should be 0 because no horizontal overhead surface
        points = [
            ProjectedPoint(u=10.0, v=5.0, original=Point3D(x=10.0, y=5.0, z=-1.0)),
            ProjectedPoint(u=10.0, v=5.0, original=Point3D(x=10.0, y=5.0, z=0.0)),
            ProjectedPoint(u=10.0, v=5.0, original=Point3D(x=10.0, y=5.0, z=1.0))
        ]

        # Calculate zenith angle - should be 0 for vertical surface
        zenith_result = self.calculator.calculate_obstruction_angle(
            points,
            reference_height=0.0,
            window_center=self.window_center,
            window_normal=self.window_normal
        )

        # Vertical surface should have zero zenith angle
        assert zenith_result.obstruction_angle_degrees == 0.0
        assert zenith_result.highest_point is None

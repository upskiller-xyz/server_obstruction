import pytest
import numpy as np
from src.components.geometry.reference_point import ReferencePointCalculator
from src.components.geometry import Point3D


class TestReferencePointCalculator:
    """Test cases for ReferencePointCalculator class"""

    def test_calculate_with_simple_square_room(self):
        """Test reference point calculation with square room"""
        # Window at (5, 0) to (5, 2), height 1.5 to 3.5
        # Square room from (0,0) to (10, 10)
        room_polygon = [
            [0.0, 0.0],
            [10.0, 0.0],
            [10.0, 10.0],
            [0.0, 10.0]
        ]

        result = ReferencePointCalculator.calculate(
            x1=5.0, y1=0.0, z1=1.5,
            x2=5.0, y2=2.0, z2=3.5,
            room_polygon=room_polygon
        )

        assert isinstance(result, Point3D)
        # X should be window center
        assert abs(result.x - 5.0) < 0.01
        # Y should be projected onto polygon edge (0.0)
        assert abs(result.y - 0.0) < 0.01
        # Z should be vertical center
        assert abs(result.z - 2.5) < 0.01

    def test_calculate_with_closed_polygon(self):
        """Test with already closed polygon"""
        room_polygon = [
            [0.0, 0.0],
            [10.0, 0.0],
            [10.0, 10.0],
            [0.0, 10.0],
            [0.0, 0.0]  # Already closed
        ]

        result = ReferencePointCalculator.calculate(
            x1=5.0, y1=5.0, z1=0.0,
            x2=7.0, y2=5.0, z2=2.0,
            room_polygon=room_polygon
        )

        assert isinstance(result, Point3D)
        assert result.z == 1.0  # Vertical center

    def test_calculate_projects_to_nearest_edge(self):
        """Test that point projects to nearest polygon edge"""
        # Simple rectangle
        room_polygon = [
            [0.0, 0.0],
            [10.0, 0.0],
            [10.0, 5.0],
            [0.0, 5.0]
        ]

        # Window center at (5, 2.5) should project to nearest edge
        result = ReferencePointCalculator.calculate(
            x1=5.0, y1=2.0, z1=0.0,
            x2=5.0, y2=3.0, z2=2.0,
            room_polygon=room_polygon
        )

        # Should project to one of the edges
        assert isinstance(result, Point3D)
        # Y should be at one of the edges (0 or 5)
        assert abs(result.y - 0.0) < 0.5 or abs(result.y - 5.0) < 0.5

    def test_calculate_with_triangle_room(self):
        """Test with triangular room polygon"""
        room_polygon = [
            [0.0, 0.0],
            [10.0, 0.0],
            [5.0, 10.0]
        ]

        result = ReferencePointCalculator.calculate(
            x1=5.0, y1=3.0, z1=0.0,
            x2=5.0, y2=4.0, z2=2.0,
            room_polygon=room_polygon
        )

        assert isinstance(result, Point3D)
        assert result.z == 1.0

    def test_calculate_raises_error_for_invalid_polygon(self):
        """Test that invalid polygon raises ValueError"""
        # Too few vertices
        room_polygon = [
            [0.0, 0.0],
            [10.0, 0.0]
        ]

        with pytest.raises(ValueError, match="at least 3 vertices"):
            ReferencePointCalculator.calculate(
                x1=5.0, y1=0.0, z1=0.0,
                x2=5.0, y2=2.0, z2=2.0,
                room_polygon=room_polygon
            )

    def test_calculate_vertical_center(self):
        """Test that vertical center is calculated correctly"""
        room_polygon = [
            [0.0, 0.0],
            [10.0, 0.0],
            [10.0, 10.0],
            [0.0, 10.0]
        ]

        result = ReferencePointCalculator.calculate(
            x1=5.0, y1=0.0, z1=5.0,
            x2=5.0, y2=2.0, z2=15.0,
            room_polygon=room_polygon
        )

        # Vertical center should be (5 + 15) / 2 = 10.0
        assert abs(result.z - 10.0) < 0.01

    def test_calculate_with_window_inside_polygon(self):
        """Test with window center inside polygon"""
        room_polygon = [
            [0.0, 0.0],
            [20.0, 0.0],
            [20.0, 20.0],
            [0.0, 20.0]
        ]

        # Window center at (10, 10) - inside polygon
        result = ReferencePointCalculator.calculate(
            x1=9.0, y1=9.0, z1=0.0,
            x2=11.0, y2=11.0, z2=2.0,
            room_polygon=room_polygon
        )

        assert isinstance(result, Point3D)
        # Should project to nearest boundary
        assert result.x >= 0.0 and result.x <= 20.0
        assert result.y >= 0.0 and result.y <= 20.0

    def test_calculate_with_corner_window(self):
        """Test with window at room corner"""
        room_polygon = [
            [0.0, 0.0],
            [10.0, 0.0],
            [10.0, 10.0],
            [0.0, 10.0]
        ]

        # Window near corner (0, 0)
        result = ReferencePointCalculator.calculate(
            x1=0.0, y1=0.0, z1=1.0,
            x2=1.0, y2=1.0, z2=3.0,
            room_polygon=room_polygon
        )

        assert isinstance(result, Point3D)
        assert result.z == 2.0  # Vertical center

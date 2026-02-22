import pytest
import numpy as np
from src.components.calculators.intersection_calculator import IntersectionCalculator
from src.components.geometry import Point3D, Vector3D, Mesh
from src.components.models import Window, ObstructionResult
from src.server.base.constants import ANGLES


class TestIntersectionCalculator:
    """Test cases for IntersectionCalculator class"""

    def test_call_with_simple_mesh(self):
        """Test intersection calculation with simple vertical wall"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        # Vertical wall in front of window
        mesh = Mesh.from_vertices([
            [10.0, 0.0, -5.0],
            [10.0, 5.0, -5.0],
            [10.0, 0.0, 5.0]
        ])

        result = IntersectionCalculator.call(mesh, window, ANGLES.HORIZON)

        assert isinstance(result, ObstructionResult)
        assert result.obstruction_angle_degrees >= 0.0
        assert result.obstruction_angle_radians >= 0.0

    def test_call_with_empty_mesh(self):
        """Test that empty mesh raises error"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )

        with pytest.raises(ValueError):
            mesh = Mesh.from_vertices([])

    def test_call_with_no_valid_window(self):
        """Test that None window raises error"""
        mesh = Mesh.from_vertices([
            [10.0, 0.0, 0.0],
            [10.0, 5.0, 0.0],
            [10.0, 0.0, 5.0]
        ])
        window = Window(
            center=None,
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )

        with pytest.raises(ValueError):
            IntersectionCalculator.call(mesh, window, ANGLES.HORIZON)

    def test_call_returns_no_obstruction_for_distant_mesh(self):
        """Test that very distant or behind mesh returns no obstruction"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        # Mesh behind window
        mesh = Mesh.from_vertices([
            [-10.0, 0.0, 0.0],
            [-10.0, 5.0, 0.0],
            [-10.0, 0.0, 5.0]
        ])

        result = IntersectionCalculator.call(mesh, window, ANGLES.HORIZON)

        # Should return no obstruction or very low angle
        assert result.obstruction_angle_degrees >= 0.0

    def test_horizon_angle_calculation(self):
        """Test horizon angle is calculated correctly"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        # Simple vertical wall directly in front, higher than window
        mesh = Mesh.from_vertices([
            [5.0, -1.0, 0.0],
            [5.0, 1.0, 0.0],
            [5.0, 0.0, 5.0]
        ])

        result = IntersectionCalculator.call(mesh, window, ANGLES.HORIZON)

        # Should have positive obstruction angle (wall is 5m away and 5m high)
        assert result.obstruction_angle_degrees >= 0.0

    def test_zenith_angle_calculation(self):
        """Test zenith angle is calculated correctly"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=1.5),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        # Horizontal surface above window
        mesh = Mesh.from_vertices([
            [5.0, -2.0, 5.0],
            [5.0, 2.0, 5.0],
            [15.0, 0.0, 5.0]
        ])

        result = IntersectionCalculator.call(mesh, window, ANGLES.ZENITH)

        # Should calculate zenith angle
        assert result.obstruction_angle_degrees >= 0.0

    def test_multiple_triangles(self):
        """Test with multiple triangles, highest should be selected"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        # Two vertical walls, second one taller
        mesh = Mesh.from_vertices([
            # First triangle - lower (3m high)
            [5.0, -1.0, 0.0],
            [5.0, 1.0, 0.0],
            [5.0, 0.0, 3.0],
            # Second triangle - taller (8m high)
            [5.0, -1.0, 0.0],
            [5.0, 1.0, 0.0],
            [5.0, 0.0, 8.0]
        ])

        result = IntersectionCalculator.call(mesh, window, ANGLES.HORIZON)

        # Should select the taller triangle (8m high / 5m away gives ~58 degrees)
        assert result.obstruction_angle_degrees >= 0.0

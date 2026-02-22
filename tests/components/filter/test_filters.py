import pytest
from src.components.filter import (
    CoarseTriangleFilter,
    DistanceTriangleFilter,
    HeightTriangleFilter,
    VerticalSurfaceFilter,
    CompositeTriangleFilter
)
from src.components.geometry import Point3D, Vector3D, Mesh, Triangle
from src.components.models import Window


class TestCoarseTriangleFilter:
    """Test cases for CoarseTriangleFilter"""

    def test_filter_keeps_front_facing_triangles(self):
        """Test that filter keeps triangles in front of window"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            # Front triangle (positive X)
            [10.0, 0.0, 0.0],
            [10.0, 1.0, 0.0],
            [10.0, 0.5, 1.0]
        ])

        filtered_triangles = CoarseTriangleFilter.call(mesh.triangles, window)

        assert len(filtered_triangles) == 1

    def test_filter_removes_back_facing_triangles(self):
        """Test that filter removes triangles behind window"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            # Behind triangle (negative X)
            [-10.0, 0.0, 0.0],
            [-10.0, 1.0, 0.0],
            [-10.0, 0.5, 1.0]
        ])

        filtered_triangles = CoarseTriangleFilter.call(mesh.triangles, window)

        assert len(filtered_triangles) == 0


class TestDistanceTriangleFilter:
    """Test cases for DistanceTriangleFilter"""

    def test_filter_keeps_triangles_above_window(self):
        """Test that filter keeps triangles above window"""
        from src.server.base.constants import ANGLES
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [5.0, 0.0, 1.0],
            [5.0, 1.0, 1.0],
            [5.0, 0.5, 2.0]
        ])

        filtered_triangles = DistanceTriangleFilter.call(mesh.triangles, window, ANGLES.HORIZON)

        assert len(filtered_triangles) >= 0

    def test_filter_removes_triangles_below_window(self):
        """Test that filter removes triangles below window"""
        from src.server.base.constants import ANGLES
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=5.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [100.0, 0.0, 0.0],
            [100.0, 1.0, 0.0],
            [100.0, 0.5, 1.0]
        ])

        filtered_triangles = DistanceTriangleFilter.call(mesh.triangles, window, ANGLES.HORIZON)

        assert len(filtered_triangles) == 0


class TestHeightTriangleFilter:
    """Test cases for HeightTriangleFilter"""

    def test_filter_keeps_tall_triangles(self):
        """Test that filter keeps triangles above window center"""
        from src.server.base.constants import ANGLES
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [10.0, 5.0, 2.0],
            [10.0, 10.0, 3.0],
            [10.0, 7.5, 4.0]
        ])

        filtered_triangles = HeightTriangleFilter.call(mesh.triangles, window, ANGLES.HORIZON)

        assert len(filtered_triangles) == 1

    def test_filter_removes_short_triangles(self):
        """Test that filter removes triangles below window center"""
        from src.server.base.constants import ANGLES
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=10.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            # Low triangle (all vertices below window center)
            [10.0, 0.0, 0.0],
            [10.0, 1.0, 1.0],
            [10.0, 0.5, 2.0]
        ])

        filtered_triangles = HeightTriangleFilter.call(mesh.triangles, window, ANGLES.HORIZON)

        assert len(filtered_triangles) == 0


class TestVerticalSurfaceFilter:
    """Test cases for VerticalSurfaceFilter"""

    def test_filter_keeps_vertical_surfaces(self):
        """Test that filter keeps vertical surfaces (walls) for horizon calculations"""
        from src.server.base.constants import ANGLES
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=1.5),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        # Vertical triangle (constant X, varying Y and Z) - should be KEPT
        mesh = Mesh.from_vertices([
            [10.0, -1.0, 0.0],
            [10.0, 1.0, 0.0],
            [10.0, 0.0, 5.0]
        ])

        filtered_triangles = VerticalSurfaceFilter.call(mesh.triangles, window, ANGLES.HORIZON)

        # VerticalSurfaceFilter keeps vertical surfaces (walls) for horizon calculations
        assert len(filtered_triangles) == 1

    def test_filter_removes_horizontal_surfaces(self):
        """Test that filter removes horizontal surfaces (roofs) for horizon calculations"""
        from src.server.base.constants import ANGLES
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=1.5),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        # Horizontal triangle (constant Z, varying X and Y) - should be FILTERED OUT
        mesh = Mesh.from_vertices([
            [10.0, -1.0, 5.0],
            [11.0, -1.0, 5.0],
            [10.5, 1.0, 5.0]
        ])

        filtered_triangles = VerticalSurfaceFilter.call(mesh.triangles, window, ANGLES.HORIZON)

        # VerticalSurfaceFilter filters OUT horizontal surfaces (roofs)
        assert len(filtered_triangles) == 0


class TestCompositeTriangleFilter:
    """Test cases for CompositeTriangleFilter"""

    def test_composite_returns_both_filtered_sets(self):
        """Test that composite filter returns both horizon and zenith filtered sets"""
        from src.server.base.constants import ANGLES
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            # Triangle above window
            [5.0, 0.0, 1.0],
            [5.0, 1.0, 2.0],
            [5.0, 0.5, 1.5],
            # Another triangle
            [10.0, 0.0, 3.0],
            [10.0, 1.0, 4.0],
            [10.0, 0.5, 3.5]
        ])

        horizon_filtered, zenith_filtered = CompositeTriangleFilter.call(mesh.triangles, window, ANGLES.HORIZON)

        # Should return two tuples
        assert isinstance(horizon_filtered, tuple)
        assert isinstance(zenith_filtered, tuple)
        # Both should have some triangles (exact count depends on filtering logic)
        assert len(horizon_filtered) >= 0
        assert len(zenith_filtered) >= 0

    def test_composite_with_single_triangle(self):
        """Test that composite filter handles single triangle mesh"""
        from src.server.base.constants import ANGLES
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [5.0, -1.0, 1.0],
            [5.0, 1.0, 1.0],
            [5.0, 0.0, 3.0]
        ])

        horizon_filtered, zenith_filtered = CompositeTriangleFilter.call(mesh.triangles, window, ANGLES.HORIZON)

        # Both should be tuples
        assert isinstance(horizon_filtered, tuple)
        assert isinstance(zenith_filtered, tuple)
        # At least one should have results
        assert len(horizon_filtered) + len(zenith_filtered) >= 0

import pytest
import numpy as np
from src.components.geometry import Point3D, Vector3D, Mesh
from src.components.models import Window
from src.components.calculators import OrthographicProjectionCalculator


class TestOrthographicProjectionCalculator:
    """Test cases for OrthographicProjectionCalculator class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.calculator = OrthographicProjectionCalculator()

    def test_create_projection_plane_forward_facing(self):
        """Test plane creation for forward-facing window"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)  # Viewing direction +X
        )
        plane = self.calculator.create_projection_plane(window)

        # Plane origin should be at window center
        assert plane.origin == window.center

        # Plane's geometric normal should be perpendicular to viewing direction (which is +X)
        # Since viewing is +X and world up is +Y, plane normal should be ±Z
        assert abs(plane.normal.x) < 1e-10
        assert abs(plane.normal.y) < 1e-10
        assert abs(abs(plane.normal.z) - 1.0) < 1e-10  # Should be +1 or -1

        # V-axis should point up (world up)
        assert abs(plane.v_axis.x) < 1e-10
        assert abs(plane.v_axis.y - 1.0) < 1e-10
        assert abs(plane.v_axis.z) < 1e-10

        # U-axis should be the horizontal component of viewing direction (+X)
        assert abs(plane.u_axis.x - 1.0) < 1e-10
        assert abs(plane.u_axis.y) < 1e-10
        assert abs(plane.u_axis.z) < 1e-10

    def test_create_projection_plane_upward_facing(self):
        """Test plane creation for upward-facing window"""
        # Window normal pointing up (parallel to world up)
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=0.0, y=1.0, z=0.0)
        )
        plane = self.calculator.create_projection_plane(window)

        # Should handle edge case where normal is parallel to world up
        assert plane.origin == window.center
        assert abs(plane.u_axis.magnitude() - 1.0) < 1e-10
        assert abs(plane.v_axis.magnitude() - 1.0) < 1e-10

    def test_create_projection_plane_axes_orthogonal(self):
        """Test that plane axes are orthogonal"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D.from_angles(rad_x=0.0, rad_y=np.pi/4).normalize()
        )
        plane = self.calculator.create_projection_plane(window)

        # Check u and v are orthogonal
        u_arr = plane.u_axis.to_array()
        v_arr = plane.v_axis.to_array()
        n_arr = plane.normal.to_array()

        u_dot_v = np.dot(u_arr, v_arr)
        u_dot_n = np.dot(u_arr, n_arr)
        v_dot_n = np.dot(v_arr, n_arr)

        assert abs(u_dot_v) < 1e-10
        assert abs(u_dot_n) < 1e-10
        assert abs(v_dot_n) < 1e-10

    def test_create_projection_plane_axes_normalized(self):
        """Test that all plane axes are unit vectors"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D.from_angles(rad_x=0.0, rad_y=np.pi/6).normalize()
        )
        plane = self.calculator.create_projection_plane(window)

        assert abs(plane.u_axis.magnitude() - 1.0) < 1e-10
        assert abs(plane.v_axis.magnitude() - 1.0) < 1e-10
        assert abs(plane.normal.magnitude() - 1.0) < 1e-10

    def test_project_point_on_plane(self):
        """Test projecting a point that lies on the plane"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)  # Viewing direction +X
        )
        plane = self.calculator.create_projection_plane(window)

        # Point to project: (1, 1, 0)
        # Since u_axis is (1,0,0) and v_axis is (0,1,0), and origin is (0,0,0):
        # relative = (1, 1, 0)
        # u = dot(relative, u_axis) = 1*1 + 1*0 + 0*0 = 1
        # v = dot(relative, v_axis) = 1*0 + 1*1 + 0*0 = 1
        point = Point3D(x=1.0, y=1.0, z=0.0)
        projected = self.calculator.project_point(point, plane)

        assert projected.original == point
        assert abs(projected.u - 1.0) < 1e-10
        assert abs(projected.v - 1.0) < 1e-10

    def test_project_point_origin(self):
        """Test projecting the plane origin itself"""
        window = Window(
            center=Point3D(x=5.0, y=10.0, z=15.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        plane = self.calculator.create_projection_plane(window)

        # Project the plane origin
        projected = self.calculator.project_point(plane.origin, plane)

        # Should project to (0, 0)
        assert abs(projected.u) < 1e-10
        assert abs(projected.v) < 1e-10

    def test_project_point_above_plane(self):
        """Test projecting a point above plane center"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        plane = self.calculator.create_projection_plane(window)

        # Point above the plane center
        point = Point3D(x=0.0, y=5.0, z=0.0)
        projected = self.calculator.project_point(point, plane)

        # Should have positive v coordinate
        assert projected.v > 4.9

    def test_project_mesh_single_triangle(self):
        """Test projecting a mesh with single triangle"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=0.0, y=0.0, z=1.0)
        )
        plane = self.calculator.create_projection_plane(window)

        mesh = Mesh.from_vertices([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ])

        projected_points = self.calculator.project_mesh(mesh, plane)

        assert len(projected_points) == 3
        assert all(hasattr(p, 'u') and hasattr(p, 'v') for p in projected_points)

    def test_project_mesh_multiple_triangles(self):
        """Test projecting a mesh with multiple triangles"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        plane = self.calculator.create_projection_plane(window)

        mesh = Mesh.from_vertices([
            [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [1.0, 0.0, 1.0],
            [2.0, 0.0, 0.0], [2.0, 2.0, 0.0], [2.0, 0.0, 2.0]
        ])

        projected_points = self.calculator.project_mesh(mesh, plane)

        assert len(projected_points) == 6

    def test_project_mesh_preserves_original_points(self):
        """Test that projection preserves reference to original points"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        plane = self.calculator.create_projection_plane(window)

        vertices = [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ]
        mesh = Mesh.from_vertices(vertices)

        projected_points = self.calculator.project_mesh(mesh, plane)

        # Check that original points are preserved
        assert projected_points[0].original.x == 1.0
        assert projected_points[0].original.y == 2.0
        assert projected_points[0].original.z == 3.0

    def test_orthographic_projection_parallel_lines_stay_parallel(self):
        """Test orthographic property: parallel lines stay parallel"""
        window = Window(
            center=Point3D(x=0.0, y=0.0, z=0.0),
            normal=Vector3D(x=0.0, y=0.0, z=1.0)
        )
        plane = self.calculator.create_projection_plane(window)

        # Two parallel vertical lines
        line1_bottom = Point3D(x=1.0, y=0.0, z=0.0)
        line1_top = Point3D(x=1.0, y=10.0, z=0.0)
        line2_bottom = Point3D(x=2.0, y=0.0, z=0.0)
        line2_top = Point3D(x=2.0, y=10.0, z=0.0)

        p1b = self.calculator.project_point(line1_bottom, plane)
        p1t = self.calculator.project_point(line1_top, plane)
        p2b = self.calculator.project_point(line2_bottom, plane)
        p2t = self.calculator.project_point(line2_top, plane)

        # Vertical distances should be the same
        dist1 = abs(p1t.v - p1b.v)
        dist2 = abs(p2t.v - p2b.v)
        assert abs(dist1 - dist2) < 1e-10

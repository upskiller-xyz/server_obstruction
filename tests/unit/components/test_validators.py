"""Unit tests for geometric validators"""
import unittest
import numpy as np
from src.components.validators import GeometricValidator, PointOnTriangleError
from src.components.geometry import Point3D, Triangle


class TestGeometricValidator(unittest.TestCase):
    """Test cases for GeometricValidator"""

    def setUp(self):
        """Set up test fixtures"""
        # Simple triangle in XY plane at z=0
        self.triangle_horizontal = Triangle(
            v1=Point3D(0.0, 0.0, 0.0),
            v2=Point3D(1.0, 0.0, 0.0),
            v3=Point3D(0.5, 1.0, 0.0)
        )

        # Vertical triangle
        self.triangle_vertical = Triangle(
            v1=Point3D(0.0, 0.0, 0.0),
            v2=Point3D(1.0, 0.0, 0.0),
            v3=Point3D(0.5, 0.0, 1.0)
        )

    def test_point_on_triangle_center(self):
        """Test point at triangle center"""
        # Center of horizontal triangle
        center = Point3D(0.5, 0.33333, 0.0)
        result = GeometricValidator.is_point_on_triangle(center, self.triangle_horizontal)
        self.assertTrue(result)

    def test_point_on_triangle_vertex(self):
        """Test point at triangle vertex"""
        result = GeometricValidator.is_point_on_triangle(
            self.triangle_horizontal.v1,
            self.triangle_horizontal
        )
        self.assertTrue(result)

    def test_point_on_triangle_edge(self):
        """Test point on triangle edge"""
        # Midpoint of edge between v1 and v2
        edge_point = Point3D(0.5, 0.0, 0.0)
        result = GeometricValidator.is_point_on_triangle(edge_point, self.triangle_horizontal)
        self.assertTrue(result)

    def test_point_outside_triangle(self):
        """Test point outside triangle boundaries"""
        outside = Point3D(2.0, 2.0, 0.0)
        result = GeometricValidator.is_point_on_triangle(outside, self.triangle_horizontal)
        self.assertFalse(result)

    def test_point_above_triangle_plane(self):
        """Test point above triangle plane (not on plane)"""
        above = Point3D(0.5, 0.33333, 1.0)
        result = GeometricValidator.is_point_on_triangle(above, self.triangle_horizontal)
        self.assertFalse(result)

    def test_point_on_vertical_triangle(self):
        """Test point on vertical triangle"""
        # Center of vertical triangle
        center = Point3D(0.5, 0.0, 0.33333)
        result = GeometricValidator.is_point_on_triangle(center, self.triangle_vertical)
        self.assertTrue(result)

    def test_find_triangle_containing_point(self):
        """Test finding triangle containing point"""
        triangles = (self.triangle_horizontal, self.triangle_vertical)
        point = Point3D(0.5, 0.33333, 0.0)

        triangle = GeometricValidator.find_triangle_containing_point(point, triangles)
        self.assertIsNotNone(triangle)
        self.assertEqual(triangle, self.triangle_horizontal)

    def test_find_triangle_no_match(self):
        """Test finding triangle when point is not on any triangle"""
        triangles = (self.triangle_horizontal, self.triangle_vertical)
        point = Point3D(10.0, 10.0, 10.0)

        triangle = GeometricValidator.find_triangle_containing_point(point, triangles)
        self.assertIsNone(triangle)

    def test_validate_point_not_on_mesh_success(self):
        """Test validation passes when point is not on mesh"""
        triangles = (self.triangle_horizontal, self.triangle_vertical)
        point = Point3D(10.0, 10.0, 10.0)

        # Should not raise exception
        GeometricValidator.validate_point_not_on_mesh(point, triangles)

    def test_validate_point_not_on_mesh_failure(self):
        """Test validation fails when point is on mesh"""
        triangles = (self.triangle_horizontal, self.triangle_vertical)
        point = Point3D(0.5, 0.33333, 0.0)

        with self.assertRaises(PointOnTriangleError) as context:
            GeometricValidator.validate_point_not_on_mesh(point, triangles)

        error = context.exception
        self.assertEqual(error.point, point)
        self.assertEqual(error.triangle, self.triangle_horizontal)

    def test_barycentric_coordinates(self):
        """Test barycentric coordinate calculation"""
        # Point at center of triangle
        center = np.array([0.5, 0.33333, 0.0])
        v1 = self.triangle_horizontal.v1.to_array()
        v2 = self.triangle_horizontal.v2.to_array()
        v3 = self.triangle_horizontal.v3.to_array()

        u, v, w = GeometricValidator._calculate_barycentric_coordinates(
            center, v1, v2, v3
        )

        # All coordinates should be positive
        self.assertGreater(u, 0.0)
        self.assertGreater(v, 0.0)
        self.assertGreater(w, 0.0)

        # Sum should be approximately 1
        self.assertAlmostEqual(u + v + w, 1.0, places=5)

    def test_point_distance_to_plane(self):
        """Test distance calculation from point to plane"""
        # Point 1 unit above horizontal triangle
        point = np.array([0.5, 0.33333, 1.0])
        v1 = self.triangle_horizontal.v1.to_array()
        v2 = self.triangle_horizontal.v2.to_array()
        v3 = self.triangle_horizontal.v3.to_array()

        distance = GeometricValidator._point_distance_to_plane(point, v1, v2, v3)
        self.assertAlmostEqual(distance, 1.0, places=5)


if __name__ == '__main__':
    unittest.main()

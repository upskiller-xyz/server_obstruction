import pytest
import numpy as np
from src.components.geometry import Point3D, Vector3D, Triangle, Mesh


class TestPoint3D:
    """Test cases for Point3D class"""

    def test_point_creation(self):
        """Test basic point creation"""
        point = Point3D(x=1.0, y=2.0, z=3.0)
        assert point.x == 1.0
        assert point.y == 2.0
        assert point.z == 3.0

    def test_point_immutability(self):
        """Test that Point3D is immutable"""
        point = Point3D(x=1.0, y=2.0, z=3.0)
        with pytest.raises(AttributeError):
            point.x = 5.0

    def test_to_array(self):
        """Test conversion to numpy array"""
        point = Point3D(x=1.0, y=2.0, z=3.0)
        arr = point.to_array()
        assert isinstance(arr, np.ndarray)
        assert np.allclose(arr, [1.0, 2.0, 3.0])

    def test_from_array(self):
        """Test creation from numpy array"""
        arr = np.array([4.0, 5.0, 6.0])
        point = Point3D.from_array(arr)
        assert point.x == 4.0
        assert point.y == 5.0
        assert point.z == 6.0


class TestVector3D:
    """Test cases for Vector3D class"""

    def test_vector_creation(self):
        """Test basic vector creation"""
        vector = Vector3D(x=1.0, y=0.0, z=0.0)
        assert vector.x == 1.0
        assert vector.y == 0.0
        assert vector.z == 0.0

    def test_vector_immutability(self):
        """Test that Vector3D is immutable"""
        vector = Vector3D(x=1.0, y=0.0, z=0.0)
        with pytest.raises(AttributeError):
            vector.x = 2.0

    def test_magnitude(self):
        """Test vector magnitude calculation"""
        vector = Vector3D(x=3.0, y=4.0, z=0.0)
        assert vector.magnitude() == 5.0

    def test_magnitude_unit_vector(self):
        """Test magnitude of unit vector"""
        vector = Vector3D(x=1.0, y=0.0, z=0.0)
        assert vector.magnitude() == 1.0

    def test_normalize(self):
        """Test vector normalization"""
        vector = Vector3D(x=3.0, y=4.0, z=0.0)
        normalized = vector.normalize()
        assert abs(normalized.magnitude() - 1.0) < 1e-10
        assert abs(normalized.x - 0.6) < 1e-10
        assert abs(normalized.y - 0.8) < 1e-10

    def test_normalize_zero_vector_raises_error(self):
        """Test that normalizing zero vector raises error"""
        vector = Vector3D(x=0.0, y=0.0, z=0.0)
        with pytest.raises(ValueError, match="Cannot normalize zero vector"):
            vector.normalize()

    def test_from_array(self):
        """Test creation from numpy array"""
        arr = np.array([1.0, 2.0, 3.0])
        vector = Vector3D.from_array(arr)
        assert vector.x == 1.0
        assert vector.y == 2.0
        assert vector.z == 3.0

    def test_from_angles_zero(self):
        """Test vector creation from zero angles"""
        vector = Vector3D.from_angles(rad_x=0.0, rad_y=0.0)
        # Should point in positive X direction
        assert abs(vector.x - 1.0) < 1e-10
        assert abs(vector.y) < 1e-10
        assert abs(vector.z) < 1e-10

    def test_from_angles_vertical(self):
        """Test vector creation with vertical rotation"""
        vector = Vector3D.from_angles(rad_x=np.pi/2, rad_y=0.0)
        # Should point up (positive Y)
        assert abs(vector.x) < 1e-10
        assert abs(vector.y - 1.0) < 1e-10
        assert abs(vector.z) < 1e-10

    def test_to_array(self):
        """Test conversion to numpy array"""
        vector = Vector3D(x=1.0, y=2.0, z=3.0)
        arr = vector.to_array()
        assert isinstance(arr, np.ndarray)
        assert np.allclose(arr, [1.0, 2.0, 3.0])


class TestTriangle:
    """Test cases for Triangle class"""

    def test_triangle_creation(self):
        """Test basic triangle creation"""
        v1 = Point3D(x=0.0, y=0.0, z=0.0)
        v2 = Point3D(x=1.0, y=0.0, z=0.0)
        v3 = Point3D(x=0.0, y=1.0, z=0.0)
        triangle = Triangle(v1=v1, v2=v2, v3=v3)
        assert triangle.v1 == v1
        assert triangle.v2 == v2
        assert triangle.v3 == v3

    def test_triangle_immutability(self):
        """Test that Triangle is immutable"""
        v1 = Point3D(x=0.0, y=0.0, z=0.0)
        v2 = Point3D(x=1.0, y=0.0, z=0.0)
        v3 = Point3D(x=0.0, y=1.0, z=0.0)
        triangle = Triangle(v1=v1, v2=v2, v3=v3)
        with pytest.raises(AttributeError):
            triangle.v1 = Point3D(x=5.0, y=5.0, z=5.0)

    def test_vertices_method(self):
        """Test vertices() returns list of all vertices"""
        v1 = Point3D(x=0.0, y=0.0, z=0.0)
        v2 = Point3D(x=1.0, y=0.0, z=0.0)
        v3 = Point3D(x=0.0, y=1.0, z=0.0)
        triangle = Triangle(v1=v1, v2=v2, v3=v3)
        vertices = triangle.vertices()
        assert len(vertices) == 3
        assert vertices[0] == v1
        assert vertices[1] == v2
        assert vertices[2] == v3


class TestMesh:
    """Test cases for Mesh class"""

    def test_mesh_creation_from_vertices(self):
        """Test mesh creation from vertex list"""
        vertices = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ]
        mesh = Mesh.from_vertices(vertices)
        assert len(mesh.triangles) == 1

    def test_mesh_multiple_triangles(self):
        """Test mesh with multiple triangles"""
        vertices = [
            [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0], [2.0, 1.0, 0.0], [1.0, 2.0, 0.0]
        ]
        mesh = Mesh.from_vertices(vertices)
        assert len(mesh.triangles) == 2

    def test_mesh_invalid_vertex_count(self):
        """Test that invalid vertex count raises error"""
        vertices = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0]
        ]
        with pytest.raises(ValueError, match="Number of vertices must be divisible by 3"):
            Mesh.from_vertices(vertices)

    def test_mesh_immutability(self):
        """Test that Mesh is immutable"""
        vertices = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ]
        mesh = Mesh.from_vertices(vertices)
        with pytest.raises((AttributeError, TypeError)):
            mesh.triangles = ()

    def test_get_all_points(self):
        """Test getting all points from mesh"""
        vertices = [
            [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0], [2.0, 1.0, 0.0], [1.0, 2.0, 0.0]
        ]
        mesh = Mesh.from_vertices(vertices)
        points = mesh.get_all_points()
        assert len(points) == 6

    def test_mesh_empty_vertices_raises_error(self):
        """Test that empty vertex list raises error"""
        with pytest.raises(ValueError):
            Mesh.from_vertices([])

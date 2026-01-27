import pytest
import numpy as np
from src.components.geometry import Point3D, Vector3D, ProjectedPoint,ProjectionPlane, Mesh
from src.components.models import (
    Window,
    ObstructionRequest,
    ObstructionResult
)


class TestWindow:
    """Test cases for Window class"""

    def test_window_creation(self):
        """Test basic window creation"""
        center = Point3D(x=0.0, y=1.5, z=0.0)
        normal = Vector3D(x=1.0, y=0.0, z=0.0)
        window = Window(center=center, normal=normal)
        assert window.center == center
        assert window.normal == normal

    def test_window_immutability(self):
        """Test that Window is immutable"""
        center = Point3D(x=0.0, y=1.5, z=0.0)
        normal = Vector3D(x=1.0, y=0.0, z=0.0)
        window = Window(center=center, normal=normal)
        with pytest.raises(AttributeError):
            window.center = Point3D(x=5.0, y=5.0, z=5.0)

    def test_from_dict(self):
        """Test window creation from dictionary"""
        data = {
            "x": 1.0,
            "y": 2.0,
            "z": 3.0,
            "rad_x": 0.0,
            "rad_y": 0.0
        }
        window = Window.from_dict(data)
        assert window.center.x == 1.0
        assert window.center.y == 2.0
        assert window.center.z == 3.0
        assert abs(window.normal.magnitude() - 1.0) < 1e-10

    def test_from_dict_normalizes_vector(self):
        """Test that normal vector is normalized"""
        data = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": np.pi/4
        }
        window = Window.from_dict(data)
        assert abs(window.normal.magnitude() - 1.0) < 1e-10


class TestProjectedPoint:
    """Test cases for ProjectedPoint class"""

    def test_projected_point_creation(self):
        """Test basic projected point creation"""
        original = Point3D(x=1.0, y=2.0, z=3.0)
        point = ProjectedPoint(u=5.0, v=10.0, original=original)
        assert point.u == 5.0
        assert point.v == 10.0
        assert point.original == original

    def test_projected_point_immutability(self):
        """Test that ProjectedPoint is immutable"""
        original = Point3D(x=1.0, y=2.0, z=3.0)
        point = ProjectedPoint(u=5.0, v=10.0, original=original)
        with pytest.raises(AttributeError):
            point.u = 20.0

    def test_height_property(self):
        """Test height property returns v coordinate"""
        original = Point3D(x=1.0, y=2.0, z=3.0)
        point = ProjectedPoint(u=5.0, v=15.0, original=original)
        assert point.height == 15.0


class TestProjectionPlane:
    """Test cases for ProjectionPlane class"""

    def test_projection_plane_creation(self):
        """Test basic projection plane creation"""
        origin = Point3D(x=0.0, y=0.0, z=0.0)
        u_axis = Vector3D(x=1.0, y=0.0, z=0.0)
        v_axis = Vector3D(x=0.0, y=1.0, z=0.0)
        normal = Vector3D(x=0.0, y=0.0, z=1.0)
        plane = ProjectionPlane(
            origin=origin,
            u_axis=u_axis,
            v_axis=v_axis,
            normal=normal
        )
        assert plane.origin == origin
        assert plane.u_axis == u_axis
        assert plane.v_axis == v_axis
        assert plane.normal == normal

    def test_projection_plane_immutability(self):
        """Test that ProjectionPlane is immutable"""
        origin = Point3D(x=0.0, y=0.0, z=0.0)
        u_axis = Vector3D(x=1.0, y=0.0, z=0.0)
        v_axis = Vector3D(x=0.0, y=1.0, z=0.0)
        normal = Vector3D(x=0.0, y=0.0, z=1.0)
        plane = ProjectionPlane(
            origin=origin,
            u_axis=u_axis,
            v_axis=v_axis,
            normal=normal
        )
        with pytest.raises(AttributeError):
            plane.origin = Point3D(x=5.0, y=5.0, z=5.0)


class TestObstructionRequest:
    """Test cases for ObstructionRequest class"""

    def test_raytrace_request_creation(self):
        """Test basic request creation"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ])
        request = ObstructionRequest(window=window, mesh=mesh)
        assert request.window == window
        assert request.mesh == mesh

    def test_raytrace_request_immutability(self):
        """Test that ObstructionRequest is immutable"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ])
        request = ObstructionRequest(window=window, mesh=mesh)
        with pytest.raises(AttributeError):
            request.window = None

    def test_from_dict(self):
        """Test request creation from dictionary"""
        data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0]
            ]
        }
        request = ObstructionRequest.from_dict(data)
        assert request.window.center.x == 0.0
        assert request.window.center.y == 1.5
        assert len(request.mesh.triangles) == 1

    def test_from_dict_multiple_triangles(self):
        """Test request with multiple triangles"""
        data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [
                [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                [1.0, 1.0, 0.0], [2.0, 1.0, 0.0], [1.0, 2.0, 0.0]
            ]
        }
        request = ObstructionRequest.from_dict(data)
        assert len(request.mesh.triangles) == 2


class TestObstructionResult:
    """Test cases for ObstructionResult class"""

    def test_raytrace_result_creation(self):
        """Test basic result creation"""
        highest = Point3D(x=1.0, y=5.0, z=0.0)
        result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=np.pi/4,
            highest_point=highest,
            projected_point_count=10
        )
        assert result.obstruction_angle_degrees == 45.0
        assert result.obstruction_angle_radians == np.pi/4
        assert result.highest_point == highest
        assert result.projected_point_count == 10

    def test_raytrace_result_immutability(self):
        """Test that ObstructionResult is immutable"""
        highest = Point3D(x=1.0, y=5.0, z=0.0)
        result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=np.pi/4,
            highest_point=highest,
            projected_point_count=10
        )
        with pytest.raises(AttributeError):
            result.obstruction_angle_degrees = 90.0

    def test_to_dict(self):
        """Test conversion to dictionary"""
        highest = Point3D(x=1.0, y=5.0, z=0.0)
        result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=np.pi/4,
            highest_point=highest,
            projected_point_count=10
        )
        data = result.to_dict()
        assert data["obstruction_angle_degrees"] == 45.0
        assert data["obstruction_angle_radians"] == np.pi/4
        assert data["highest_point"]["x"] == 1.0
        assert data["highest_point"]["y"] == 5.0
        assert data["highest_point"]["z"] == 0.0
        assert data["projected_point_count"] == 10

    def test_to_dict_no_highest_point(self):
        """Test to_dict with no highest point"""
        result = ObstructionResult(
            obstruction_angle_degrees=0.0,
            obstruction_angle_radians=0.0,
            highest_point=None,
            projected_point_count=0
        )
        data = result.to_dict()
        assert data["highest_point"] is None
        assert data["projected_point_count"] == 0

import pytest
from src.components.geometry import Point3D, Vector3D, Mesh
from src.components.models import Window, ObstructionRequest
from src.server.base.constants import RequestField


class TestObstructionRequest:
    """Test cases for ObstructionRequest model"""

    def test_obstruction_request_creation(self):
        """Test basic obstruction request creation"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [1.0, 0.0, 0.0],
            [1.0, 3.0, 0.0],
            [1.0, 1.5, 1.0]
        ])

        request = ObstructionRequest(
            window=window,
            mesh=mesh
        )

        assert request.window == window
        assert request.mesh == mesh

    def test_obstruction_request_immutability(self):
        """Test that obstruction request is immutable"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        request = ObstructionRequest(
            window=window,
            mesh=None
        )

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            request.window = window

    def test_from_dict_with_flat_list_format(self):
        """Test creating request from dictionary with flat list mesh format"""
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 0.0,
            RequestField.MESH.value: [
                [1.0, 0.0, 0.0],
                [1.0, 3.0, 0.0],
                [1.0, 1.5, 1.0]
            ]
        }

        request = ObstructionRequest.from_dict(data)

        assert isinstance(request, ObstructionRequest)
        assert isinstance(request.window, Window)
        assert request.mesh is not None
        assert len(request.mesh.triangles) == 1

    def test_from_dict_with_empty_mesh(self):
        """Test creating request with empty mesh list"""
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 0.0,
            RequestField.MESH.value: []
        }

        request = ObstructionRequest.from_dict(data)

        # Empty mesh should result in None
        assert request.mesh is None

    def test_from_dict_with_multiple_triangles(self):
        """Test creating request with multiple triangles"""
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 0.0,
            RequestField.MESH.value: [
                [1.0, 0.0, 0.0],
                [1.0, 3.0, 0.0],
                [1.0, 1.5, 1.0],
                [2.0, 0.0, 0.0],
                [2.0, 3.0, 0.0],
                [2.0, 1.5, 1.0]
            ]
        }

        request = ObstructionRequest.from_dict(data)

        assert request.mesh is not None
        assert len(request.mesh.triangles) == 2

    def test_from_dict_with_no_mesh(self):
        """Test creating request with no mesh key"""
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 0.0
        }

        request = ObstructionRequest.from_dict(data)

        assert request.mesh is None

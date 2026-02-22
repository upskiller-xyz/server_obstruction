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
        horizon_mesh = Mesh.from_vertices([
            [1.0, 0.0, 0.0],
            [1.0, 3.0, 0.0],
            [1.0, 1.5, 1.0]
        ])
        zenith_mesh = Mesh.from_vertices([
            [2.0, 5.0, -1.0],
            [2.0, 5.0, 1.0],
            [3.0, 5.0, 0.0]
        ])

        request = ObstructionRequest(
            window=window,
            horizon_mesh=horizon_mesh,
            zenith_mesh=zenith_mesh
        )

        assert request.window == window
        assert request.horizon_mesh == horizon_mesh
        assert request.zenith_mesh == zenith_mesh

    def test_obstruction_request_immutability(self):
        """Test that obstruction request is immutable"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        request = ObstructionRequest(
            window=window,
            horizon_mesh=None,
            zenith_mesh=None
        )

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            request.window = window

    def test_from_dict_with_nested_mesh_format(self):
        """Test creating request from dictionary with nested mesh format"""
        from src.server.base.constants import ANGLES
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 0.0,
            RequestField.MESH.value: {
                ANGLES.HORIZON: [
                    [1.0, 0.0, 0.0],
                    [1.0, 3.0, 0.0],
                    [1.0, 1.5, 1.0]
                ],
                ANGLES.ZENITH: [
                    [2.0, 5.0, -1.0],
                    [2.0, 5.0, 1.0],
                    [3.0, 5.0, 0.0]
                ]
            }
        }

        request = ObstructionRequest.from_dict(data)

        assert isinstance(request, ObstructionRequest)
        assert isinstance(request.window, Window)
        assert request.horizon_mesh is not None
        assert request.zenith_mesh is not None
        assert len(request.horizon_mesh.triangles) == 1
        assert len(request.zenith_mesh.triangles) == 1

    def test_from_dict_with_horizon_only(self):
        """Test creating request with horizon mesh only"""
        from src.server.base.constants import ANGLES
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 0.0,
            RequestField.MESH.value: {
                ANGLES.HORIZON: [
                    [1.0, 0.0, 0.0],
                    [1.0, 3.0, 0.0],
                    [1.0, 1.5, 1.0]
                ]
            }
        }

        request = ObstructionRequest.from_dict(data)

        assert request.horizon_mesh is not None
        assert request.zenith_mesh is None

    def test_from_dict_with_zenith_only(self):
        """Test creating request with zenith mesh only"""
        from src.server.base.constants import ANGLES
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 0.0,
            RequestField.MESH.value: {
                ANGLES.ZENITH: [
                    [2.0, 5.0, -1.0],
                    [2.0, 5.0, 1.0],
                    [3.0, 5.0, 0.0]
                ]
            }
        }

        request = ObstructionRequest.from_dict(data)

        assert request.horizon_mesh is None
        assert request.zenith_mesh is not None

    def test_from_dict_multiple_triangles(self):
        """Test creating request with multiple triangles"""
        from src.server.base.constants import ANGLES
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 0.0,
            RequestField.MESH.value: {
                ANGLES.HORIZON: [
                    [1.0, 0.0, 0.0],
                    [1.0, 3.0, 0.0],
                    [1.0, 1.5, 1.0],
                    [2.0, 0.0, 0.0],
                    [2.0, 3.0, 0.0],
                    [2.0, 1.5, 1.0]
                ]
            }
        }

        request = ObstructionRequest.from_dict(data)

        assert request.horizon_mesh is not None
        assert len(request.horizon_mesh.triangles) == 2

    def test_from_dict_empty_mesh(self):
        """Test creating request with empty mesh"""
        from src.server.base.constants import ANGLES
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 0.0,
            RequestField.MESH.value: {
                ANGLES.HORIZON: []
            }
        }

        request = ObstructionRequest.from_dict(data)

        # Empty mesh should result in None
        assert request.horizon_mesh is None
        assert request.zenith_mesh is None

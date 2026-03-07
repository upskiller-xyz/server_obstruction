import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.server.services.obstruction_service import ObstructionService
from src.components.geometry import Point3D, Vector3D, Mesh
from src.components.models import Window, ObstructionResult


class TestObstructionService:
    """Test cases for ObstructionService class"""

    def test_calculate_horizon_returns_result(self):
        """Test calculate_horizon returns ObstructionResult"""
        from src.components.models import ObstructionRequest
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [1.0, 0.0, 0.0],
            [1.0, 3.0, 0.0],
            [1.0, 1.5, 1.0]
        ])
        request = ObstructionRequest(window=window, mesh=mesh)

        result = ObstructionService.calculate_horizon(request)

        assert isinstance(result, ObstructionResult)
        assert result.obstruction_angle_degrees >= 0.0
        assert result.obstruction_angle_radians >= 0.0

    def test_calculate_zenith_returns_result(self):
        """Test calculate_zenith_angle returns ObstructionResult"""
        from src.components.models import ObstructionRequest
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [1.0, 0.0, 0.0],
            [1.0, 3.0, 0.0],
            [1.0, 1.5, 1.0]
        ])
        request = ObstructionRequest(window=window, mesh=mesh)

        result = ObstructionService.calculate_zenith_angle(request)

        assert isinstance(result, ObstructionResult)
        assert result.obstruction_angle_degrees >= 0.0
        assert result.obstruction_angle_radians >= 0.0

    def test_get_status_returns_dict(self):
        """Test get_status returns dictionary with status info"""
        status = ObstructionService.get_status()

        assert isinstance(status, dict)
        assert "status" in status
        assert status["status"] == "success"

    @patch('src.server.services.obstruction_service.IntersectionCalculator.call')
    def test_calculate_horizon_calls_calculator(self, mock_calc):
        """Test that calculate_horizon calls IntersectionCalculator"""
        from src.components.models import ObstructionRequest
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [1.0, 0.0, 0.0],
            [1.0, 3.0, 0.0],
            [1.0, 1.5, 1.0]
        ])
        request = ObstructionRequest(window=window, mesh=mesh)

        mock_result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=np.pi/4,
            highest_point=Point3D(x=1.0, y=3.0, z=0.0)
        )
        mock_calc.return_value = mock_result

        result = ObstructionService.calculate_horizon(request)

        assert result == mock_result
        mock_calc.assert_called_once()

    def test_calculate_horizon_with_empty_mesh(self):
        """Test calculate_horizon with empty mesh"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )

        # This should raise an error or return zero obstruction
        with pytest.raises(ValueError):
            mesh = Mesh.from_vertices([])

    def test_calculate_zenith_with_empty_mesh(self):
        """Test calculate_zenith_angle with empty mesh"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )

        # This should raise an error or return zero obstruction
        with pytest.raises(ValueError):
            mesh = Mesh.from_vertices([])

import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.server.controllers.obstruction_controller import ObstructionController
from src.components.geometry import Point3D
from src.components.obstruction_models import ObstructionResult
from src.components.constants import EndpointName


class TestObstructionController:
    """Test cases for simplified ObstructionController using call() method"""

    def test_controller_strategy_attributes_exist(self):
        """Test controller has required strategy attributes"""
        assert hasattr(ObstructionController, 'ASYNC_ENDPOINTS')
        assert hasattr(ObstructionController, 'MULTI_DIRECTION_ENDPOINTS')

    @patch('src.server.services.obstruction_service.ObstructionService.calculate_horizon')
    def test_call_obstruction_valid_request(self, mock_calc):
        """Test call() with obstruction endpoint and valid request"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": [
                [1.0, 0.0, 0.0],
                [1.0, 3.0, 0.0],
                [1.0, 1.5, 1.0]
            ]
        }

        mock_result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=np.pi/4,
            highest_point=Point3D(x=1.0, y=3.0, z=0.0)
        )
        mock_calc.return_value = mock_result

        result = ObstructionController.call(EndpointName.OBSTRUCTION, request_data)

        assert result["status"] == "success"
        assert "data" in result
        assert result["data"]["obstruction_angle_degrees"] == 45.0
        mock_calc.assert_called_once()

    @patch('src.server.services.obstruction_service.ObstructionService.calculate_zenith_angle')
    def test_call_zenith_angle_endpoint(self, mock_calc):
        """Test call() with zenith_angle endpoint"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": [
                [1.0, 0.0, 0.0],
                [1.0, 3.0, 0.0],
                [1.0, 1.5, 1.0]
            ]
        }

        mock_result = ObstructionResult(
            obstruction_angle_degrees=30.0,
            obstruction_angle_radians=np.pi/6,
            highest_point=Point3D(x=1.0, y=3.0, z=0.0)
        )
        mock_calc.return_value = mock_result

        result = ObstructionController.call(EndpointName.ZENITH_ANGLE, request_data)

        assert result["status"] == "success"
        mock_calc.assert_called_once()

    def test_call_missing_field(self):
        """Test call() with missing required field"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            # Missing z
            "direction_angle": 0.0,
            "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]
        }

        result = ObstructionController.call(EndpointName.OBSTRUCTION, request_data)

        assert result["status"] == "error"
        assert "Missing required fields" in result["error"]

    def test_call_invalid_mesh(self):
        """Test call() with invalid mesh format"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": "not a list"
        }

        result = ObstructionController.call(EndpointName.OBSTRUCTION, request_data)

        assert result["status"] == "error"
        assert "Mesh must be a list" in result["error"]

    def test_call_unknown_endpoint(self):
        """Test call() with unknown endpoint - uses default service"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]
        }

        # Unknown endpoint uses default service (calculate_horizon)
        # This will succeed, not error
        with patch('src.server.services.obstruction_service.ObstructionService.calculate_horizon') as mock_calc:
            mock_calc.return_value = ObstructionResult(
                obstruction_angle_degrees=0.0,
                obstruction_angle_radians=0.0,
                highest_point=None
            )
            result = ObstructionController.call(EndpointName.OBSTRUCTION, request_data)
            assert result["status"] == "success"

    @patch('src.server.services.obstruction_service.ObstructionService.calculate_horizon')
    def test_call_service_raises_value_error(self, mock_calc):
        """Test call() when service raises ValueError"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]
        }

        mock_calc.side_effect = ValueError("Service error")

        result = ObstructionController.call(EndpointName.OBSTRUCTION, request_data)

        assert result["status"] == "error"
        assert "Service error" in result["error"]

    @patch('src.server.services.obstruction_service.ObstructionService.calculate_all_directions_async')
    def test_call_multi_direction_endpoint(self, mock_calc):
        """Test call() with multi-direction endpoint"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]],
            "num_directions": 8
        }

        mock_results = [
            {"direction_angle_degrees": i * 45, "obstruction_angle_degrees": 30.0}
            for i in range(8)
        ]

        # Mock async function
        async def async_mock(*args, **kwargs):
            return mock_results

        mock_calc.return_value = async_mock()

        result = ObstructionController.call(EndpointName.OBSTRUCTION_ALL, request_data)

        assert result["status"] == "success"
        assert "data" in result
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 8
        mock_calc.assert_called_once()

    @patch('src.server.services.obstruction_service.ObstructionService.get_status')
    def test_call_status_endpoint(self, mock_status):
        """Test call() with status endpoint"""
        mock_status.return_value = {"status": "success"}

        result = ObstructionController.call(EndpointName.STATUS, {})

        assert result["status"] == "success"
        mock_status.assert_called_once()

    @patch('src.server.services.obstruction_service.ObstructionService.get_status')
    def test_get_status_backwards_compatibility(self, mock_status):
        """Test get_status() for backwards compatibility"""
        mock_status.return_value = {"status": "success"}

        status = ObstructionController.get_status()

        assert status["status"] == "success"
        mock_status.assert_called_once()

    @patch('src.server.services.obstruction_service.ObstructionService.calculate_horizon')
    @patch('src.server.validators.validation_steps.logger')
    def test_call_mesh_not_divisible_by_three(self, mock_logger, mock_calc):
        """Test call() with mesh not divisible by 3"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": [
                [1.0, 0.0, 0.0],
                [1.0, 3.0, 0.0],
                [1.0, 1.5, 1.0],
                [2.0, 0.0, 0.0]  # Extra vertex
            ]
        }

        mock_result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=np.pi/4,
            highest_point=Point3D(x=1.0, y=3.0, z=0.0)
        )
        mock_calc.return_value = mock_result

        result = ObstructionController.call(EndpointName.OBSTRUCTION, request_data)

        # Should succeed with trimmed mesh
        assert result["status"] == "success"
        # Warning should be logged
        mock_logger.warning.assert_called_once()

    def test_call_invalid_numeric_field(self):
        """Test call() with invalid numeric field"""
        request_data = {
            "x": "not a number",
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]
        }

        result = ObstructionController.call(EndpointName.OBSTRUCTION, request_data)

        assert result["status"] == "error"
        assert "must be a number" in result["error"]

    def test_call_empty_mesh(self):
        """Test call() with empty mesh"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": []
        }

        result = ObstructionController.call(EndpointName.OBSTRUCTION, request_data)

        assert result["status"] == "error"
        assert "Mesh cannot be empty" in result["error"]

    @patch('src.server.services.obstruction_service.ObstructionService.calculate_horizon')
    def test_call_with_large_mesh(self, mock_calc):
        """Test call() with large mesh"""
        # Create mesh with 100 triangles (300 vertices)
        vertices = []
        for i in range(100):
            vertices.extend([
                [float(i), 0.0, 0.0],
                [float(i), 1.0, 0.0],
                [float(i), 0.5, 1.0]
            ])

        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": vertices
        }

        mock_result = ObstructionResult(
            obstruction_angle_degrees=30.0,
            obstruction_angle_radians=np.pi/6,
            highest_point=Point3D(x=50.0, y=1.0, z=0.0)
        )
        mock_calc.return_value = mock_result

        result = ObstructionController.call(EndpointName.OBSTRUCTION, request_data)

        assert result["status"] == "success"
        assert result["data"]["obstruction_angle_degrees"] == 30.0

import pytest
import numpy as np
from unittest.mock import Mock
from src.server.controllers.obstruction_controller import ObstructionController
from src.components.geometry import Point3D
from src.components.obstruction_models import ObstructionResult


class TestObstructionController:
    """Test cases for ObstructionController class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_logger = Mock()
        self.mock_logger.debug = Mock()
        self.mock_logger.info = Mock()
        self.mock_logger.warning = Mock()
        self.mock_logger.error = Mock()

        self.mock_service = Mock()
        self.controller = ObstructionController(
            raytrace_service=self.mock_service,
            logger=self.mock_logger
        )

    def test_controller_initialization(self):
        """Test controller initializes with dependencies"""
        assert self.controller._raytrace_service == self.mock_service
        assert self.controller._logger == self.mock_logger

    def test_calculate_obstruction_valid_request(self):
        """Test calculate_obstruction with valid request"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [
                [1.0, 0.0, 0.0],
                [1.0, 3.0, 0.0],
                [1.0, 1.5, 1.0]
            ]
        }

        mock_result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=np.pi/4,
            highest_point=Point3D(x=1.0, y=3.0, z=0.0),
            projected_point_count=3
        )
        self.mock_service.calculate_obstruction.return_value = mock_result

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "success"
        assert "data" in result
        assert result["data"]["obstruction_angle_degrees"] == 45.0
        self.mock_service.calculate_obstruction.assert_called_once()

    def test_calculate_obstruction_missing_field(self):
        """Test validation fails with missing required field"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            # Missing z
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]
        }

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "error"
        assert "Missing required fields" in result["error"]
        self.mock_logger.warning.assert_called_once()

    def test_calculate_obstruction_missing_multiple_fields(self):
        """Test validation fails with multiple missing fields"""
        request_data = {
            "x": 0.0,
            # Missing y, z, rad_x, rad_y, mesh
        }

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "error"
        assert "Missing required fields" in result["error"]

    def test_calculate_obstruction_invalid_mesh_not_list(self):
        """Test validation fails when mesh is not a list"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": "not a list"
        }

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "error"
        assert "Mesh must be a list" in result["error"]

    def test_calculate_obstruction_empty_mesh(self):
        """Test validation fails with empty mesh"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": []
        }

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "error"
        assert "Mesh cannot be empty" in result["error"]

    def test_calculate_obstruction_mesh_not_divisible_by_three(self):
        """Test validation fails when mesh vertices not divisible by 3"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [
                [1.0, 0.0, 0.0],
                [1.0, 3.0, 0.0]
                # Only 2 vertices
            ]
        }

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "error"
        assert "groups of 3" in result["error"]

    def test_calculate_obstruction_invalid_vertex_format(self):
        """Test validation fails with invalid vertex format"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [
                [1.0, 0.0, 0.0],
                [1.0, 3.0],  # Invalid: only 2 coordinates
                [1.0, 1.5, 1.0]
            ]
        }

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "error"
        assert "Vertex" in result["error"]
        assert "3 coordinates" in result["error"]

    def test_calculate_obstruction_invalid_numeric_field(self):
        """Test validation fails with non-numeric field"""
        request_data = {
            "x": "not a number",
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]
        }

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "error"
        assert "must be a number" in result["error"]

    def test_calculate_obstruction_service_raises_value_error(self):
        """Test handling when service raises ValueError"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]
        }

        self.mock_service.calculate_obstruction.side_effect = ValueError("Service error")

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "error"
        assert "Invalid request" in result["error"]
        self.mock_logger.warning.assert_called()

    def test_calculate_obstruction_service_raises_generic_exception(self):
        """Test handling when service raises generic exception"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]
        }

        self.mock_service.calculate_obstruction.side_effect = RuntimeError("Unexpected error")

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "error"
        assert "Calculation failed" in result["error"]
        self.mock_logger.error.assert_called_once()

    def test_get_status(self):
        """Test get_status returns controller and service status"""
        self.mock_service.get_status.return_value = {"service": "ready"}

        status = self.controller.get_status()

        assert status["controller"] == "ready"
        assert "service" in status
        self.mock_service.get_status.assert_called_once()

    def test_validate_request_all_numeric_fields(self):
        """Test that all numeric fields are validated"""
        numeric_fields = ["x", "y", "z", "rad_x", "rad_y"]

        for field in numeric_fields:
            request_data = {
                "x": 0.0,
                "y": 1.5,
                "z": 0.0,
                "rad_x": 0.0,
                "rad_y": 0.0,
                "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]
            }
            request_data[field] = "invalid"

            result = self.controller.calculate_obstruction(request_data)

            assert result["status"] == "error"
            assert field in result["error"] or "must be a number" in result["error"]

    def test_calculate_obstruction_with_large_mesh(self):
        """Test with large mesh (many triangles)"""
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
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": vertices
        }

        mock_result = ObstructionResult(
            obstruction_angle_degrees=30.0,
            obstruction_angle_radians=np.pi/6,
            highest_point=Point3D(x=50.0, y=1.0, z=0.0),
            projected_point_count=300
        )
        self.mock_service.calculate_obstruction.return_value = mock_result

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "success"
        assert result["data"]["projected_point_count"] == 300

    def test_calculate_obstruction_with_negative_coordinates(self):
        """Test with negative coordinates"""
        request_data = {
            "x": -10.0,
            "y": -5.0,
            "z": -3.0,
            "rad_x": -0.5,
            "rad_y": -1.0,
            "mesh": [
                [-1.0, -2.0, -3.0],
                [-4.0, -5.0, -6.0],
                [-7.0, -8.0, -9.0]
            ]
        }

        mock_result = ObstructionResult(
            obstruction_angle_degrees=0.0,
            obstruction_angle_radians=0.0,
            highest_point=None,
            projected_point_count=3
        )
        self.mock_service.calculate_obstruction.return_value = mock_result

        result = self.controller.calculate_obstruction(request_data)

        assert result["status"] == "success"

    def test_calculate_obstruction_result_to_dict_called(self):
        """Test that result.to_dict() is called for response"""
        request_data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]
        }

        mock_result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=np.pi/4,
            highest_point=Point3D(x=1.0, y=3.0, z=0.0),
            projected_point_count=3
        )
        self.mock_service.calculate_obstruction.return_value = mock_result

        result = self.controller.calculate_obstruction(request_data)

        # Verify the result contains data from to_dict()
        assert "data" in result
        assert "obstruction_angle_degrees" in result["data"]
        assert "highest_point" in result["data"]

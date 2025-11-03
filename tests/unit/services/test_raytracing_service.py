import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from src.server.services.raytracing_service import RaytraceService, RaytraceServiceFactory
from src.components.geometry import Point3D, Vector3D, Mesh
from src.components.raytracing_models import (
    Window,
    RaytraceRequest,
    RaytraceResult,
    ProjectionPlane,
    ProjectedPoint
)
from src.components.projection import OrthographicProjectionCalculator
from src.components.obstruction_calculator import MaxHeightObstructionCalculator


class TestRaytraceService:
    """Test cases for RaytraceService class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_logger = Mock()
        self.mock_logger.debug = Mock()
        self.mock_logger.info = Mock()
        self.mock_logger.warning = Mock()
        self.mock_logger.error = Mock()

        self.mock_projection_calculator = Mock()
        self.mock_obstruction_calculator = Mock()

        self.service = RaytraceService(
            projection_calculator=self.mock_projection_calculator,
            obstruction_calculator=self.mock_obstruction_calculator,
            logger=self.mock_logger
        )

    def test_service_initialization(self):
        """Test service initializes with dependencies"""
        assert self.service._projection_calculator == self.mock_projection_calculator
        assert self.service._obstruction_calculator == self.mock_obstruction_calculator
        assert self.service._logger == self.mock_logger

    def test_calculate_obstruction_calls_projection_calculator(self):
        """Test that calculate_obstruction calls projection calculator"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [1.0, 0.0, 0.0],
            [1.0, 3.0, 0.0],
            [1.0, 1.5, 1.0]
        ])
        request = RaytraceRequest(window=window, mesh=mesh)

        # Setup mocks
        mock_plane = Mock()
        self.mock_projection_calculator.create_projection_plane.return_value = mock_plane

        projected_points = [
            ProjectedPoint(u=0.0, v=1.5, original=Point3D(x=1.0, y=3.0, z=0.0))
        ]
        self.mock_projection_calculator.project_mesh.return_value = projected_points

        mock_result = RaytraceResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=np.pi/4,
            highest_point=Point3D(x=1.0, y=3.0, z=0.0),
            projected_point_count=1
        )
        self.mock_obstruction_calculator.calculate_obstruction_angle.return_value = mock_result

        # Execute
        result = self.service.calculate_obstruction(request)

        # Verify calls
        self.mock_projection_calculator.create_projection_plane.assert_called_once_with(window)
        self.mock_projection_calculator.project_mesh.assert_called_once_with(mesh, mock_plane)
        self.mock_obstruction_calculator.calculate_obstruction_angle.assert_called_once()

        # Verify result
        assert result == mock_result

    def test_calculate_obstruction_logs_debug_messages(self):
        """Test that service logs debug messages"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [1.0, 0.0, 0.0],
            [1.0, 3.0, 0.0],
            [1.0, 1.5, 1.0]
        ])
        request = RaytraceRequest(window=window, mesh=mesh)

        # Setup mocks
        mock_plane = Mock()
        self.mock_projection_calculator.create_projection_plane.return_value = mock_plane
        self.mock_projection_calculator.project_mesh.return_value = []
        self.mock_obstruction_calculator.calculate_obstruction_angle.return_value = RaytraceResult(
            obstruction_angle_degrees=0.0,
            obstruction_angle_radians=0.0,
            highest_point=None,
            projected_point_count=0
        )

        # Execute
        self.service.calculate_obstruction(request)

        # Verify logging
        assert self.mock_logger.debug.call_count >= 2
        assert self.mock_logger.info.call_count >= 1

    def test_calculate_obstruction_with_exception_logs_error(self):
        """Test that exceptions are logged"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [1.0, 0.0, 0.0],
            [1.0, 3.0, 0.0],
            [1.0, 1.5, 1.0]
        ])
        request = RaytraceRequest(window=window, mesh=mesh)

        # Setup mock to raise exception
        self.mock_projection_calculator.create_projection_plane.side_effect = ValueError("Test error")

        # Execute and verify exception is raised
        with pytest.raises(ValueError):
            self.service.calculate_obstruction(request)

        # Verify error was logged
        self.mock_logger.error.assert_called_once()

    def test_get_status(self):
        """Test get_status returns service information"""
        status = self.service.get_status()

        assert "status" in status
        assert status["status"] == "ready"
        assert "projection_calculator" in status
        assert "obstruction_calculator" in status

    def test_calculate_obstruction_passes_correct_reference_height(self):
        """Test that reference height 0.0 is passed to obstruction calculator"""
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )
        mesh = Mesh.from_vertices([
            [1.0, 0.0, 0.0],
            [1.0, 3.0, 0.0],
            [1.0, 1.5, 1.0]
        ])
        request = RaytraceRequest(window=window, mesh=mesh)

        # Setup mocks
        mock_plane = Mock()
        self.mock_projection_calculator.create_projection_plane.return_value = mock_plane
        projected_points = [Mock()]
        self.mock_projection_calculator.project_mesh.return_value = projected_points

        # Return a proper RaytraceResult instead of Mock
        mock_result = RaytraceResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=np.pi/4,
            highest_point=Point3D(x=1.0, y=3.0, z=0.0),
            projected_point_count=1
        )
        self.mock_obstruction_calculator.calculate_obstruction_angle.return_value = mock_result

        # Execute
        self.service.calculate_obstruction(request)

        # Verify reference_height is 0.0
        call_args = self.mock_obstruction_calculator.calculate_obstruction_angle.call_args
        # Check kwargs instead of positional args
        assert call_args.kwargs['reference_height'] == 0.0


class TestRaytraceServiceFactory:
    """Test cases for RaytraceServiceFactory class"""

    def test_create_default_service(self):
        """Test factory creates service with default implementations"""
        mock_logger = Mock()

        service = RaytraceServiceFactory.create_default_service(mock_logger)

        assert isinstance(service, RaytraceService)
        assert isinstance(service._projection_calculator, OrthographicProjectionCalculator)
        assert isinstance(service._obstruction_calculator, MaxHeightObstructionCalculator)
        assert service._logger == mock_logger

    def test_create_custom_service(self):
        """Test factory creates service with custom implementations"""
        mock_logger = Mock()
        mock_projection = Mock()
        mock_obstruction = Mock()

        service = RaytraceServiceFactory.create_custom_service(
            projection_calculator=mock_projection,
            obstruction_calculator=mock_obstruction,
            logger=mock_logger
        )

        assert isinstance(service, RaytraceService)
        assert service._projection_calculator == mock_projection
        assert service._obstruction_calculator == mock_obstruction
        assert service._logger == mock_logger


class TestRaytraceServiceIntegration:
    """Integration tests with real implementations"""

    def setup_method(self):
        """Setup test fixtures with real implementations"""
        self.mock_logger = Mock()
        self.mock_logger.debug = Mock()
        self.mock_logger.info = Mock()
        self.mock_logger.warning = Mock()
        self.mock_logger.error = Mock()

        self.service = RaytraceServiceFactory.create_default_service(self.mock_logger)

    def test_calculate_obstruction_integration(self):
        """Integration test with real calculation"""
        # Create a simple scenario: building in front of window
        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )

        # Building 10m away, 5m tall
        mesh = Mesh.from_vertices([
            [10.0, 0.0, -5.0],
            [10.0, 5.0, -5.0],
            [10.0, 0.0, 5.0]
        ])

        request = RaytraceRequest(window=window, mesh=mesh)

        result = self.service.calculate_obstruction(request)

        # Verify result structure
        assert result.obstruction_angle_degrees >= 0.0
        assert result.obstruction_angle_radians >= 0.0
        assert result.projected_point_count == 3
        assert result.highest_point is not None

    def test_calculate_obstruction_no_obstruction(self):
        """Test scenario with no obstruction (geometry below window)"""
        window = Window(
            center=Point3D(x=0.0, y=10.0, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )

        # Ground level geometry
        mesh = Mesh.from_vertices([
            [10.0, 0.0, -5.0],
            [10.0, 0.0, 0.0],
            [10.0, 0.0, 5.0]
        ])

        request = RaytraceRequest(window=window, mesh=mesh)

        result = self.service.calculate_obstruction(request)

        # Should have zero or near-zero obstruction
        assert result.obstruction_angle_degrees >= 0.0
        assert result.projected_point_count == 3

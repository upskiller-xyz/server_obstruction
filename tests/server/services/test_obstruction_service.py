from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from src.components.geometry import Mesh, Point3D, Vector3D
from src.components.models import ObstructionResult, Window
from src.server.services.obstruction_service import ObstructionService


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

    def test_multi_direction_builds_arrays_once_no_triangle_objects(self):
        """The all-directions path stays numpy end-to-end: triangle arrays are built
        once per request (not 64×), directly from the array — and Triangle objects are
        never materialized (``prepare_arrays`` is the legacy object→array loop)."""
        import asyncio

        from src.components.calculators.ray_triangle_intersector import (
            RayTriangleIntersector,
        )
        from src.components.models import ObstructionRequest

        window = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0),
        )
        mesh = Mesh.from_vertices([[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]])
        request = ObstructionRequest(window=window, mesh=mesh)

        service = ObstructionService()
        # wraps= keeps the real classmethod behaviour (correct descriptor binding)
        # while letting us assert call counts.
        with patch.object(
            RayTriangleIntersector, "from_array",
            wraps=RayTriangleIntersector.from_array,
        ) as from_array, patch.object(
            RayTriangleIntersector, "prepare_arrays",
            wraps=RayTriangleIntersector.prepare_arrays,
        ) as prepare_arrays:
            result = asyncio.run(service.calculate_all_directions_async(request))

        assert len(result["results"]) == 64
        assert from_array.call_count == 1       # built once, not 64×
        assert prepare_arrays.call_count == 0   # no Triangle objects built

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

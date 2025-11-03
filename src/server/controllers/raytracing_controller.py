from typing import Dict, Any
from src.server.interfaces import ILogger
from src.server.services.raytracing_service import RaytraceService
from src.components.raytracing_models import RaytraceRequest, RaytraceResult


class RaytraceController:
    """
    Controller for raytracing endpoints

    Responsibilities (Single Responsibility Principle):
    - Parse and validate request data
    - Delegate calculations to service layer
    - Format responses
    """

    def __init__(self, raytrace_service: RaytraceService, logger: ILogger):
        """
        Initialize controller with dependencies

        Args:
            raytrace_service: Service for raytracing operations
            logger: Structured logger
        """
        self._raytrace_service = raytrace_service
        self._logger = logger

    def calculate_obstruction(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle raytrace calculation request

        Args:
            request_data: Dictionary containing:
                - x, y, z: window center coordinates
                - rad_x, rad_y: window normal angles
                - mesh: list of vertex coordinates

        Returns:
            Dictionary with calculation results or error

        Example request:
        {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "rad_x": 0.0,
            "rad_y": 0.0,
            "mesh": [
                [1.0, 0.0, 0.0],
                [1.0, 3.0, 0.0],
                [1.0, 1.5, 1.0],
                ...
            ]
        }
        """
        try:
            # Validate required fields
            self._validate_request(request_data)

            # Parse request into domain model
            request = RaytraceRequest.from_dict(request_data)

            # Delegate to service layer
            result = self._raytrace_service.calculate_obstruction(request)

            # Format response
            return {
                "status": "success",
                "data": result.to_dict()
            }

        except ValueError as e:
            self._logger.warning(f"Invalid request data: {str(e)}")
            return {
                "status": "error",
                "error": f"Invalid request: {str(e)}"
            }
        except Exception as e:
            self._logger.error(f"Raytrace calculation failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Calculation failed: {str(e)}"
            }

    def _validate_request(self, data: Dict[str, Any]) -> None:
        """
        Validate request data

        Args:
            data: Request data dictionary

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Check required fields
        required_fields = ['x', 'y', 'z', 'rad_x', 'rad_y', 'mesh']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate mesh format
        mesh = data['mesh']
        if not isinstance(mesh, list):
            raise ValueError("Mesh must be a list of vertices")

        if len(mesh) == 0:
            raise ValueError("Mesh cannot be empty")

        if len(mesh) % 3 != 0:
            raise ValueError(
                f"Mesh must contain vertices in groups of 3 (triangles). "
                f"Got {len(mesh)} vertices."
            )

        # Validate each vertex
        for i, vertex in enumerate(mesh):
            if not isinstance(vertex, (list, tuple)) or len(vertex) != 3:
                raise ValueError(
                    f"Vertex {i} must be a list/tuple of 3 coordinates [x, y, z]"
                )

        # Validate numeric fields
        numeric_fields = ['x', 'y', 'z', 'rad_x', 'rad_y']
        for field in numeric_fields:
            try:
                float(data[field])
            except (TypeError, ValueError):
                raise ValueError(f"Field '{field}' must be a number")

    def get_status(self) -> Dict[str, Any]:
        """Get controller status"""
        return {
            "controller": "ready",
            "service": self._raytrace_service.get_status()
        }

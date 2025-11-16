from typing import Dict, Any
from src.server.interfaces import ILogger
from src.server.services.obstruction_service import ObstructionService
from src.components.obstruction_models import ObstructionRequest, ObstructionResult
from src.components.constants import ResponseStatus, ResponseField, RequestField, ControllerStatus
from src.components.validators import GeometricValidator, PointOnTriangleError
from src.components.geometry import Point3D, Mesh


class ObstructionController:
    """
    Controller for obstruction calculation endpoints

    Responsibilities (Single Responsibility Principle):
    - Parse and validate request data
    - Delegate calculations to service layer
    - Format responses
    """

    def __init__(self, raytrace_service: ObstructionService, logger: ILogger):
        """
        Initialize controller with dependencies

        Args:
            raytrace_service: Service for obstruction calculation operations
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
                - direction_angle: horizontal rotation angle in radians
                - mesh: list of vertex coordinates

        Returns:
            Dictionary with calculation results or error

        Example request:
        {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
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
            request = ObstructionRequest.from_dict(request_data)

            # Delegate to service layer
            result = self._raytrace_service.calculate_obstruction(request)

            # Format response
            return {
                ResponseField.STATUS.value: ResponseStatus.SUCCESS.value,
                ResponseField.DATA.value: result.to_dict()
            }

        except PointOnTriangleError as e:
            self._logger.warning(f"Window center lies on mesh: {str(e)}")
            return {
                ResponseField.STATUS.value: ResponseStatus.ERROR.value,
                ResponseField.ERROR.value: str(e),
                ResponseField.WINDOW_CENTER.value: {
                    RequestField.X.value: e.point.x,
                    RequestField.Y.value: e.point.y,
                    RequestField.Z.value: e.point.z
                },
                ResponseField.TRIANGLE.value: {
                    ResponseField.VERTICES.value: [
                        {RequestField.X.value: e.triangle.v1.x, RequestField.Y.value: e.triangle.v1.y, RequestField.Z.value: e.triangle.v1.z},
                        {RequestField.X.value: e.triangle.v2.x, RequestField.Y.value: e.triangle.v2.y, RequestField.Z.value: e.triangle.v2.z},
                        {RequestField.X.value: e.triangle.v3.x, RequestField.Y.value: e.triangle.v3.y, RequestField.Z.value: e.triangle.v3.z}
                    ]
                }
            }
        except ValueError as e:
            self._logger.warning(f"Invalid request data: {str(e)}")
            return {
                ResponseField.STATUS.value: ResponseStatus.ERROR.value,
                ResponseField.ERROR.value: f"Invalid request: {str(e)}"
            }
        except Exception as e:
            self._logger.error(f"Obstruction calculation failed: {str(e)}")
            return {
                ResponseField.STATUS.value: ResponseStatus.ERROR.value,
                ResponseField.ERROR.value: f"Calculation failed: {str(e)}"
            }

    def _validate_request(self, data: Dict[str, Any]) -> None:
        """
        Validate request data

        Args:
            data: Request data dictionary

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Check required position fields
        required_fields = [
            RequestField.X.value,
            RequestField.Y.value,
            RequestField.Z.value,
            RequestField.DIRECTION_ANGLE.value,
            RequestField.MESH.value
        ]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate mesh format
        mesh = data[RequestField.MESH.value]
        if not isinstance(mesh, list):
            raise ValueError("Mesh must be a list of vertices")

        if len(mesh) == 0:
            raise ValueError("Mesh cannot be empty")

        # Handle mesh vertices not divisible by 3
        if len(mesh) % 3 != 0:
            extra_vertices = len(mesh) % 3
            original_count = len(mesh)
            # Trim extra vertices (1-2 vertices)
            data[RequestField.MESH.value] = mesh[:-extra_vertices]
            self._logger.warning(
                f"Mesh had {original_count} vertices (not divisible by 3). "
                f"Trimmed {extra_vertices} extra vertex/vertices. "
                f"Proceeding with {len(data[RequestField.MESH.value])} vertices."
            )

        # Validate each vertex
        for i, vertex in enumerate(mesh):
            if not isinstance(vertex, (list, tuple)) or len(vertex) != 3:
                raise ValueError(
                    f"Vertex {i} must be a list/tuple of 3 coordinates [x, y, z]"
                )

        # Validate numeric fields
        numeric_fields = [
            RequestField.X.value,
            RequestField.Y.value,
            RequestField.Z.value,
            RequestField.DIRECTION_ANGLE.value
        ]

        for field in numeric_fields:
            if field in data:  # Only validate if present
                try:
                    float(data[field])
                except (TypeError, ValueError):
                    raise ValueError(f"Field '{field}' must be a number")

        # Validate window center doesn't lie on mesh
        self._validate_window_not_on_mesh(data)

    def _validate_window_not_on_mesh(self, data: Dict[str, Any]) -> None:
        """
        Validate that window center point doesn't lie on any mesh triangle

        Args:
            data: Request data dictionary

        Raises:
            PointOnTriangleError: If window center lies on a mesh triangle
        """
        # Extract window center
        window_center = Point3D(
            x=float(data[RequestField.X.value]),
            y=float(data[RequestField.Y.value]),
            z=float(data[RequestField.Z.value])
        )

        # Create mesh from vertices
        mesh = Mesh.from_vertices(data[RequestField.MESH.value])

        # Validate window center doesn't lie on any triangle
        GeometricValidator.validate_point_not_on_mesh(
            window_center,
            mesh.triangles
        )

    def calculate_zenith_angle(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle zenith angle calculation request

        Args:
            request_data: Dictionary containing:
                - x, y, z: window center coordinates
                - direction_angle: horizontal rotation angle in radians
                - mesh: list of vertex coordinates

        Returns:
            Dictionary with zenith angle results or error
        """
        try:
            # Validate required fields
            self._validate_request(request_data)

            # Parse request into domain model
            request = ObstructionRequest.from_dict(request_data)

            # Delegate to service layer
            result = self._raytrace_service.calculate_zenith_angle(request)

            # Format response
            return {
                ResponseField.STATUS.value: ResponseStatus.SUCCESS.value,
                ResponseField.DATA.value: result.to_dict()
            }

        except PointOnTriangleError as e:
            self._logger.warning(f"Window center lies on mesh: {str(e)}")
            return {
                ResponseField.STATUS.value: ResponseStatus.ERROR.value,
                ResponseField.ERROR.value: str(e),
                ResponseField.WINDOW_CENTER.value: {
                    RequestField.X.value: e.point.x,
                    RequestField.Y.value: e.point.y,
                    RequestField.Z.value: e.point.z
                },
                ResponseField.TRIANGLE.value: {
                    ResponseField.VERTICES.value: [
                        {RequestField.X.value: e.triangle.v1.x, RequestField.Y.value: e.triangle.v1.y, RequestField.Z.value: e.triangle.v1.z},
                        {RequestField.X.value: e.triangle.v2.x, RequestField.Y.value: e.triangle.v2.y, RequestField.Z.value: e.triangle.v2.z},
                        {RequestField.X.value: e.triangle.v3.x, RequestField.Y.value: e.triangle.v3.y, RequestField.Z.value: e.triangle.v3.z}
                    ]
                }
            }
        except ValueError as e:
            self._logger.warning(f"Invalid request data: {str(e)}")
            return {
                ResponseField.STATUS.value: ResponseStatus.ERROR.value,
                ResponseField.ERROR.value: f"Invalid request: {str(e)}"
            }
        except Exception as e:
            self._logger.error(f"Zenith angle calculation failed: {str(e)}")
            return {
                ResponseField.STATUS.value: ResponseStatus.ERROR.value,
                ResponseField.ERROR.value: f"Calculation failed: {str(e)}"
            }

    def calculate_both_angles(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle obstruction calculation request (both horizon and zenith angles)

        Args:
            request_data: Dictionary containing:
                - x, y, z: window center coordinates
                - direction_angle: horizontal rotation angle in radians
                - mesh: list of vertex coordinates

        Returns:
            Dictionary with both horizon and zenith angle results or error
        """
        try:
            # Validate required fields
            self._validate_request(request_data)

            # Parse request into domain model
            request = ObstructionRequest.from_dict(request_data)

            # Delegate to service layer
            results = self._raytrace_service.calculate_both_angles(request)

            # Format response
            return {
                ResponseField.STATUS.value: ResponseStatus.SUCCESS.value,
                ResponseField.DATA.value: {
                    ResponseField.HORIZON.value: results[ResponseField.HORIZON.value].to_dict(),
                    ResponseField.ZENITH.value: results[ResponseField.ZENITH.value].to_dict()
                }
            }

        except PointOnTriangleError as e:
            self._logger.warning(f"Window center lies on mesh: {str(e)}")
            return {
                ResponseField.STATUS.value: ResponseStatus.ERROR.value,
                ResponseField.ERROR.value: str(e),
                ResponseField.WINDOW_CENTER.value: {
                    RequestField.X.value: e.point.x,
                    RequestField.Y.value: e.point.y,
                    RequestField.Z.value: e.point.z
                },
                ResponseField.TRIANGLE.value: {
                    ResponseField.VERTICES.value: [
                        {RequestField.X.value: e.triangle.v1.x, RequestField.Y.value: e.triangle.v1.y, RequestField.Z.value: e.triangle.v1.z},
                        {RequestField.X.value: e.triangle.v2.x, RequestField.Y.value: e.triangle.v2.y, RequestField.Z.value: e.triangle.v2.z},
                        {RequestField.X.value: e.triangle.v3.x, RequestField.Y.value: e.triangle.v3.y, RequestField.Z.value: e.triangle.v3.z}
                    ]
                }
            }
        except ValueError as e:
            self._logger.warning(f"Invalid request data: {str(e)}")
            return {
                ResponseField.STATUS.value: ResponseStatus.ERROR.value,
                ResponseField.ERROR.value: f"Invalid request: {str(e)}"
            }
        except Exception as e:
            self._logger.error(f"Both angles calculation failed: {str(e)}")
            return {
                ResponseField.STATUS.value: ResponseStatus.ERROR.value,
                ResponseField.ERROR.value: f"Calculation failed: {str(e)}"
            }

    def get_status(self) -> Dict[str, Any]:
        """Get controller status"""
        return {
            ResponseField.CONTROLLER.value: ControllerStatus.READY.value,
            ResponseField.SERVICE.value: self._raytrace_service.get_status()
        }

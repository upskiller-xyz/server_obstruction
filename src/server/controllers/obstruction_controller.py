from typing import Dict, Any, Optional
import time
import asyncio
from src.server.interfaces import ILogger
from src.server.services.obstruction_service import ObstructionService
from src.server.services.parallel_obstruction_service import ParallelObstructionService
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

    def __init__(
        self,
        raytrace_service: ObstructionService,
        logger: ILogger,
        parallel_service: Optional[ParallelObstructionService] = None
    ):
        """
        Initialize controller with dependencies

        Args:
            raytrace_service: Service for obstruction calculation operations
            logger: Structured logger
            parallel_service: Optional service for parallel multi-direction calculations
        """
        self._raytrace_service = raytrace_service
        self._logger = logger
        self._parallel_service = parallel_service

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
        controller_start = time.time()

        try:
            # Validate required fields
            validation_start = time.time()
            self._validate_request(request_data)
            self._logger.info(f"[CONTROLLER] Validation: {(time.time()-validation_start)*1000:.2f}ms")

            # Parse request into domain model
            parse_start = time.time()
            request = ObstructionRequest.from_dict(request_data)
            self._logger.info(f"[CONTROLLER] Parsing {len(request_data.get('mesh', []))} vertices: {(time.time()-parse_start)*1000:.2f}ms")

            # Delegate to service layer (use EFFICIENT method with filters)
            service_start = time.time()
            result = self._raytrace_service.calculate_obstruction_efficient(request)
            self._logger.info(f"[CONTROLLER] Service calculation: {(time.time()-service_start)*1000:.2f}ms")
            self._logger.info(f"[CONTROLLER] Total controller time: {(time.time()-controller_start)*1000:.2f}ms")

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

    def calculate_all_directions(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle all-direction obstruction calculation request

        Calculates obstruction angles in a semicircle from the window.
        By default samples 64 directions from 17.5° to 162.5° relative to window normal.

        Args:
            request_data: Dictionary containing:
                - x, y, z: window center coordinates
                - mesh: list of vertex coordinates
                - num_directions (optional): number of directions to sample (default 64)
                - start_angle_degrees (optional): start angle relative to window normal (default 17.5°)
                - end_angle_degrees (optional): end angle relative to window normal (default 162.5°)

        Returns:
            Dictionary with obstruction results for all directions or error
        """
        try:
            # Validate required fields (direction_angle not required for this endpoint)
            required_fields = [
                RequestField.X.value,
                RequestField.Y.value,
                RequestField.Z.value,
                RequestField.MESH.value
            ]
            missing_fields = [field for field in required_fields if field not in request_data]

            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            # Validate mesh format
            mesh = request_data[RequestField.MESH.value]
            if not isinstance(mesh, list):
                raise ValueError("Mesh must be a list of vertices")

            if len(mesh) == 0:
                raise ValueError("Mesh cannot be empty")

            # Handle mesh vertices not divisible by 3
            if len(mesh) % 3 != 0:
                extra_vertices = len(mesh) % 3
                original_count = len(mesh)
                request_data[RequestField.MESH.value] = mesh[:-extra_vertices]
                self._logger.warning(
                    f"Mesh had {original_count} vertices (not divisible by 3). "
                    f"Trimmed {extra_vertices} extra vertex/vertices. "
                    f"Proceeding with {len(request_data[RequestField.MESH.value])} vertices."
                )

            # Validate window center doesn't lie on mesh
            self._validate_window_not_on_mesh(request_data)

            # Set default direction_angle to 0 for parsing
            if RequestField.DIRECTION_ANGLE.value not in request_data:
                request_data[RequestField.DIRECTION_ANGLE.value] = 0.0

            # Parse request into domain model
            request = ObstructionRequest.from_dict(request_data)

            # Get optional parameters
            num_directions = request_data.get("num_directions", None)
            start_angle_degrees = request_data.get("start_angle_degrees", None)
            end_angle_degrees = request_data.get("end_angle_degrees", None)

            # Validate num_directions if provided
            if num_directions is not None:
                if not isinstance(num_directions, int) or num_directions < 1:
                    raise ValueError("num_directions must be a positive integer")

            # Validate angle ranges if provided
            if start_angle_degrees is not None:
                if not isinstance(start_angle_degrees, (int, float)):
                    raise ValueError("start_angle_degrees must be a number")

            if end_angle_degrees is not None:
                if not isinstance(end_angle_degrees, (int, float)):
                    raise ValueError("end_angle_degrees must be a number")

            # Delegate to service layer
            results = self._raytrace_service.calculate_all_directions(
                request, num_directions, start_angle_degrees, end_angle_degrees
            )

            # Format response
            return {
                ResponseField.STATUS.value: ResponseStatus.SUCCESS.value,
                ResponseField.DATA.value: results
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
            self._logger.error(f"All-direction obstruction calculation failed: {str(e)}")
            return {
                ResponseField.STATUS.value: ResponseStatus.ERROR.value,
                ResponseField.ERROR.value: f"Calculation failed: {str(e)}"
            }

    def calculate_parallel_multi_direction(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle parallel multi-direction obstruction calculation request

        Calculates 64 obstruction angles in parallel by making HTTP requests
        to a microservice endpoint. Uses asyncio and aiohttp for parallel execution.

        Args:
            request_data: Dictionary containing:
                - x, y, z: window center coordinates
                - mesh: list of vertex coordinates
                - num_directions (optional): number of directions (default 64)
                - start_angle_degrees (optional): start angle (default 17.5°)
                - end_angle_degrees (optional): end angle (default 162.5°)
                - microservice_url: URL of the obstruction calculation endpoint
                - auth_token (optional): Bearer token for GCP authentication

        Returns:
            Dictionary with obstruction results for all 64 directions
        """
        try:
            # Check if parallel service is available
            if self._parallel_service is None:
                raise ValueError(
                    "Parallel obstruction service not configured. "
                    "Please provide microservice_url in request."
                )

            # Validate required fields (direction_angle not required)
            required_fields = [
                RequestField.X.value,
                RequestField.Y.value,
                RequestField.Z.value,
                RequestField.MESH.value
            ]
            missing_fields = [field for field in required_fields if field not in request_data]

            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            self._logger.info("checked fields")
            # Validate mesh format
            mesh = request_data[RequestField.MESH.value]
            if not isinstance(mesh, list):
                raise ValueError("Mesh must be a list of vertices")

            if len(mesh) == 0:
                raise ValueError("Mesh cannot be empty")

            # Handle mesh vertices not divisible by 3
            if len(mesh) % 3 != 0:
                extra_vertices = len(mesh) % 3
                original_count = len(mesh)
                request_data[RequestField.MESH.value] = mesh[:-extra_vertices]
                self._logger.warning(
                    f"Mesh had {original_count} vertices (not divisible by 3). "
                    f"Trimmed {extra_vertices} extra vertex/vertices. "
                    f"Proceeding with {len(request_data[RequestField.MESH.value])} vertices."
                )

            # Validate window center doesn't lie on mesh
            self._validate_window_not_on_mesh(request_data)
            self._logger.info("validate window on  mesh done")
            # Set default direction_angle to 0 for parsing
            if RequestField.DIRECTION_ANGLE.value not in request_data:
                request_data[RequestField.DIRECTION_ANGLE.value] = 0.0

            # Parse request into domain model
            request = ObstructionRequest.from_dict(request_data)

            # Get optional parameters
            num_directions = request_data.get("num_directions", None)
            start_angle_degrees = request_data.get("start_angle_degrees", None)
            end_angle_degrees = request_data.get("end_angle_degrees", None)

            # Validate num_directions if provided
            if num_directions is not None:
                if not isinstance(num_directions, int) or num_directions < 1:
                    raise ValueError("num_directions must be a positive integer")

            # Validate angle ranges if provided
            if start_angle_degrees is not None:
                if not isinstance(start_angle_degrees, (int, float)):
                    raise ValueError("start_angle_degrees must be a number")

            if end_angle_degrees is not None:
                if not isinstance(end_angle_degrees, (int, float)):
                    raise ValueError("end_angle_degrees must be a number")

            # Use direct async calculation instead of HTTP requests
            self._logger.info("set loop")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(
                    self._raytrace_service.calculate_all_directions_async(
                        request, num_directions, start_angle_degrees, end_angle_degrees
                    )
                )
            finally:
                loop.close()

            # Format response
            return {
                ResponseField.STATUS.value: ResponseStatus.SUCCESS.value,
                ResponseField.DATA.value: results
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
            self._logger.error(f"Parallel multi-direction calculation failed: {str(e)}")
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

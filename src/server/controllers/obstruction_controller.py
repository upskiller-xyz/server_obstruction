from typing import Dict, Any
from src.server.interfaces import ILogger
from src.server.services.obstruction_service import ObstructionService
from src.components.obstruction_models import ObstructionRequest, ObstructionResult
from src.components.constants import ResponseStatus, ResponseField, RequestField, ControllerStatus


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
                - direction_angle: horizontal rotation angle in radians (new format)
                  OR rad_x, rad_y: window normal angles (old format)
                - mesh: list of vertex coordinates

        Returns:
            Dictionary with calculation results or error

        Example request (new format):
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

        Supports both new (direction_angle) and old (rad_x, rad_y) formats

        Args:
            data: Request data dictionary

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Check required position fields
        required_fields = [RequestField.X.value, RequestField.Y.value, RequestField.Z.value, RequestField.MESH.value]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Check for direction angle (new format) OR rad_x/rad_y (old format)
        has_new_format = RequestField.DIRECTION_ANGLE.value in data
        has_old_format = RequestField.RAD_X.value in data and RequestField.RAD_Y.value in data

        if not has_new_format and not has_old_format:
            raise ValueError(
                f"Must provide either '{RequestField.DIRECTION_ANGLE.value}' (new format) "
                f"or both '{RequestField.RAD_X.value}' and '{RequestField.RAD_Y.value}' (old format)"
            )

        # Validate mesh format
        mesh = data[RequestField.MESH.value]
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
        numeric_fields = [RequestField.X.value, RequestField.Y.value, RequestField.Z.value]
        if has_new_format:
            numeric_fields.append(RequestField.DIRECTION_ANGLE.value)
        if has_old_format:
            numeric_fields.extend([RequestField.RAD_X.value, RequestField.RAD_Y.value])

        for field in numeric_fields:
            if field in data:  # Only validate if present
                try:
                    float(data[field])
                except (TypeError, ValueError):
                    raise ValueError(f"Field '{field}' must be a number")

    def calculate_zenith_angle(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle zenith angle calculation request

        Args:
            request_data: Dictionary containing:
                - x, y, z: window center coordinates
                - rad_x, rad_y: window normal angles
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
                - rad_x, rad_y: window normal angles
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

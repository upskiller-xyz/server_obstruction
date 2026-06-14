"""
Builder classes for constructing API responses following Builder Pattern

These classes use classmethods to build responses, following the principle:
"Use classmethods for functionality that operates on the class"
"""
from typing import Any, Dict, Optional

from src.components.models import ObstructionResult
from src.server.base.constants import (
    ControllerStatus,
    RequestField,
    ResponseField,
    ResponseStatus,
)
from src.server.base.errors import PointOnTriangleError


class ResponseBuilder:
    """
    Builder class for constructing success responses

    Uses Builder Pattern with fluent interface for response construction
    """

    @classmethod
    def status(cls, data:Any)->Dict[str, Any]:
        return {
                ResponseField.CONTROLLER.value: ControllerStatus.READY.value,
                ResponseField.SERVICE.value: data
            }

    @classmethod
    def success(cls, data: Any) -> Dict[str, Any]:
        """
        Build a success response

        Args:
            data: Response data payload

        Returns:
            Dictionary with status and data fields
        """
        return {
            ResponseField.STATUS.value: ResponseStatus.SUCCESS.value,
            ResponseField.DATA.value: data
        }

    @classmethod
    def success_with_result(cls, result: ObstructionResult) -> Dict[str, Any]:
        """
        Build a success response with ObstructionResult

        Args:
            result: ObstructionResult object

        Returns:
            Dictionary with status and result data
        """
        return cls.success(result.to_dict())

    @classmethod
    def success_with_both_angles(
        cls,
        result: Dict[str, ObstructionResult] | tuple[ObstructionResult, ObstructionResult]
    ) -> Dict[str, Any]:
        """
        Build a success response with both horizon and zenith results

        Args:
            result: Either a dict with 'horizon' and 'zenith' keys or
                   a tuple of (horizon_result, zenith_result)

        Returns:
            Dictionary with status and both results
        """
        # Handle dict format
        if isinstance(result, dict):
            horizon_result = result['horizon']
            zenith_result = result['zenith']
        else:
            # Handle tuple format
            horizon_result, zenith_result = result

        return cls.success({
            ResponseField.HORIZON.value: horizon_result.to_dict(),
            ResponseField.ZENITH.value: zenith_result.to_dict()
        })

    @classmethod
    def success_with_multi_direction(cls, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a success response with multi-direction results

        Args:
            results: Dictionary containing results for multiple directions

        Returns:
            Dictionary with status and results
        """
        return cls.success(results)


class ErrorResponseBuilder:
    """
    Builder class for constructing error responses using Strategy Pattern

    Uses Strategy Pattern: Different error types map to different builders
    """

    @classmethod
    def generic_error(cls, error_message: str) -> Dict[str, Any]:
        """
        Build a generic error response

        Args:
            error_message: Error message string

        Returns:
            Dictionary with status and error message
        """
        return {
            ResponseField.STATUS.value: ResponseStatus.ERROR.value,
            ResponseField.ERROR.value: error_message
        }

    @classmethod
    def validation_error(cls, error_message: str) -> Dict[str, Any]:
        """
        Build a validation error response

        Args:
            error_message: Validation error message

        Returns:
            Dictionary with status and formatted error message
        """
        return cls.generic_error(f"Invalid request: {error_message}")

    @classmethod
    def calculation_error(cls, error_message: str, operation: str) -> Dict[str, Any]:
        """
        Build a calculation error response

        Args:
            error_message: Error message
            operation: Name of the operation that failed

        Returns:
            Dictionary with status and formatted error message
        """
        return cls.generic_error(f"Calculation failed: {error_message}")

    @classmethod
    def point_on_triangle_error(cls, error: PointOnTriangleError) -> Dict[str, Any]:
        """
        Build a point-on-triangle validation error response

        Args:
            error: PointOnTriangleError exception

        Returns:
            Dictionary with status, error message, and triangle details
        """
        return {
            ResponseField.STATUS.value: ResponseStatus.ERROR.value,
            ResponseField.ERROR.value: str(error),
            ResponseField.WINDOW_CENTER.value: {
                RequestField.X.value: error.point.x,
                RequestField.Y.value: error.point.y,
                RequestField.Z.value: error.point.z
            },
            ResponseField.TRIANGLE.value: {
                ResponseField.VERTICES.value: [
                    {
                        RequestField.X.value: error.triangle.v1.x,
                        RequestField.Y.value: error.triangle.v1.y,
                        RequestField.Z.value: error.triangle.v1.z
                    },
                    {
                        RequestField.X.value: error.triangle.v2.x,
                        RequestField.Y.value: error.triangle.v2.y,
                        RequestField.Z.value: error.triangle.v2.z
                    },
                    {
                        RequestField.X.value: error.triangle.v3.x,
                        RequestField.Y.value: error.triangle.v3.y,
                        RequestField.Z.value: error.triangle.v3.z
                    }
                ]
            }
        }

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        operation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build error response from exception using Strategy Pattern

        Args:
            exception: The exception that occurred
            operation: Optional operation name for context

        Returns:
            Dictionary with appropriate error response
        """
        # Strategy Pattern: Map error types to handler methods
        if isinstance(exception, PointOnTriangleError):
            return cls.point_on_triangle_error(exception)
        elif isinstance(exception, ValueError):
            return cls.validation_error(str(exception))
        elif isinstance(exception, Exception):
            return cls.calculation_error(str(exception), operation or "Operation")

        # Fallback to generic error
        return cls.generic_error(str(exception))

"""Simplified obstruction controller using Strategy Pattern"""

import asyncio
import logging
from typing import Any, Dict

from src.components.models import ObstructionRequest
from src.server.base.constants import EndpointName, OptionalRequestField, RequestField
from src.server.base.errors import PointOnTriangleError
from src.server.builders import ErrorResponseBuilder
from src.server.controllers.endpoint_config import ServiceMethod
from src.server.maps import EndpointResponseMap
from src.server.services.obstruction_service import ObstructionService
from src.server.validators.request_validator import RequestValidator

logger = logging.getLogger(__name__)


class ObstructionController:
    """
    Simplified controller using Strategy Pattern

    Responsibilities (Single Responsibility Principle):
    - Route endpoints to appropriate service methods
    - Validate requests based on endpoint type
    - Format responses based on result type

    Strategy Pattern:
    - Validation strategies: Different validation steps per endpoint
    - Service strategies: Different service methods per endpoint
    - Response strategies: Different response builders per result type
    """


    # Strategy Pattern: Map endpoints to response formatting methods
    

    # Endpoints that require async processing
    ASYNC_ENDPOINTS = {EndpointName.OBSTRUCTION_PARALLEL}

    # Endpoints that require multi-direction parameter processing
    MULTI_DIRECTION_ENDPOINTS = {
        EndpointName.OBSTRUCTION_ALL,
        EndpointName.OBSTRUCTION_PARALLEL
    }

    @classmethod
    def call(cls, endpoint: EndpointName, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for all controller operations

        Strategy Pattern implementation:
        1. Validate request using endpoint-specific validation pipeline
        2. Call endpoint-specific service method
        3. Format response using endpoint-specific formatter

        Args:
            endpoint: Endpoint name enum
            request_data: Request data dictionary

        Returns:
            Formatted response dictionary

        Raises:
            ValueError: If endpoint is not recognized
        """
        try:

            # Step 1: Validate request using Strategy Pattern
            RequestValidator.call(endpoint, request_data)

            # Step 2: Call service method (creates request internally if needed)
            result = cls._call_service(endpoint, request_data)

            # Step 3: Format response using Strategy Pattern
            return cls._format_response(endpoint, result)

        except PointOnTriangleError as e:
            logger.warning(f"Window center lies on mesh: {str(e)}")
            return ErrorResponseBuilder.point_on_triangle_error(e)
        except ValueError as e:
            logger.warning(f"Invalid request data: {str(e)}")
            return ErrorResponseBuilder.validation_error(str(e))
        except Exception as e:
            logger.error(f"{endpoint.value} failed: {str(e)}")
            return ErrorResponseBuilder.calculation_error(str(e), endpoint.value)

    @classmethod
    def _call_service(cls, endpoint: EndpointName, request_data: Dict[str, Any]) -> Any:
        """
        Call appropriate service method based on endpoint

        Args:
            endpoint: Endpoint name
            request_data: Request data dictionary

        Returns:
            Service method result
        """
        # Special case: status endpoint doesn't need request parsing
        if endpoint == EndpointName.STATUS:
            return ObstructionService.get_status()

        # Prepare request for multi-direction endpoints
        if endpoint in cls.MULTI_DIRECTION_ENDPOINTS:
            return cls._parallel(endpoint, request_data)

        # Parse request for single-direction endpoints
        request = ObstructionRequest.from_dict(request_data)
        return ServiceMethod.get(endpoint)(request)


    @classmethod
    def _parallel(cls, endpoint: EndpointName, request_data: Dict[str, Any]) -> Any:
        """
        Call service method for multi-direction endpoints

        Args:
            endpoint: Endpoint name
            request_data: Request data dictionary

        Returns:
            Service method result
        """
        # Set default direction_angle for parsing
        if RequestField.DIRECTION_ANGLE.value not in request_data:
            request_data[RequestField.DIRECTION_ANGLE.value] = 0.0

        # Parse request and optional parameters
        request = ObstructionRequest.from_dict(request_data)
        num_directions = request_data.get(OptionalRequestField.NUM_DIRECTIONS.value, None)
        start_angle_degrees = request_data.get(OptionalRequestField.START_ANGLE_DEGREES.value, None)
        end_angle_degrees = request_data.get(OptionalRequestField.END_ANGLE_DEGREES.value, None)

        # Create service instance for instance methods
        service = ObstructionService()
        service_method = service.calculate_all_directions_async

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                service_method(request, num_directions, start_angle_degrees, end_angle_degrees)
            )
        finally:
            loop.close()
        return result
    

    @classmethod
    def _format_response(cls, endpoint: EndpointName, result: Any) -> Dict[str, Any]:
        """
        Format response based on endpoint type

        Args:
            endpoint: Endpoint name
            result: Result from service method

        Returns:
            Formatted response dictionary
        """
        return EndpointResponseMap.get(endpoint)(result)
    

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get controller status (for backwards compatibility)"""
        return cls.call(EndpointName.STATUS, {})

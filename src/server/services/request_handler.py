"""HTTP request handler for JSON endpoints"""

import logging
from typing import Any, Tuple

import orjson
from flask import Response, jsonify, request
from werkzeug.exceptions import BadRequest

from src.server.base.constants import ContentType, EndpointName, HTTPStatus, ResponseStatus
from src.server.controllers.obstruction_controller import ObstructionController


class RequestHandler:
    """
    Handles HTTP requests with consistent error handling

    Single Responsibility:
    - Only handles HTTP request/response cycle
    - Does NOT register routes or manage application state
    """

    @staticmethod
    def handle_json_post(endpoint_str: str) -> Tuple[Response, int]:
        """
        Generic handler for JSON POST requests with consistent error handling

        Args:
            endpoint_str: Endpoint name as string

        Returns:
            Tuple of (JSON response, HTTP status code)
        """
        try:
            # Validate content type
            if not request.is_json:
                raise BadRequest(f"Content-Type must be {ContentType.JSON.value}")

            # Parse request body with orjson (~faster than get_json; obstruction
            # receives the full mesh, so body parsing dominates here too).
            request_data = orjson.loads(request.get_data())
            if not request_data:
                raise BadRequest("Request body cannot be empty")

            # Route to controller
            endpoint = EndpointName.by_value(endpoint_str)
            result = ObstructionController.call(endpoint, request_data)  # type: ignore

            # Check result status
            if result.get("status") == ResponseStatus.ERROR.value:
                return jsonify(result), HTTPStatus.BAD_REQUEST.value

            return jsonify(result), HTTPStatus.OK.value

        except BadRequest as e:
            return jsonify({
                "status": ResponseStatus.ERROR.value,
                "error": str(e)
            }), HTTPStatus.BAD_REQUEST.value

        except Exception as e:
            logging.error(f"{endpoint_str} endpoint failed: {str(e)}")
            return jsonify({
                "status": ResponseStatus.ERROR.value,
                "error": f"Internal server error: {str(e)}"
            }), HTTPStatus.INTERNAL_SERVER_ERROR.value

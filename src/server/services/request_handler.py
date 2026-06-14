"""HTTP request handler for JSON endpoints"""

import logging
from typing import Any, Tuple

import orjson
from flask import Response, jsonify, request
from werkzeug.exceptions import BadRequest

from src.server.base.constants import (
    BinaryEndpointName,
    ContentType,
    EndpointName,
    HTTPStatus,
    RequestField,
    ResponseStatus,
)
from src.server.controllers.endpoint_config import BinaryEndpointLogicalMap
from src.server.controllers.obstruction_controller import ObstructionController
from src.server.services.mesh_decoder import NpyMeshDecoder


class RequestHandler:
    """
    Handles HTTP requests with consistent error handling

    Single Responsibility:
    - Only handles HTTP request/response cycle
    - Does NOT register routes or manage application state
    """

    _mesh_decoder = NpyMeshDecoder()

    @staticmethod
    def handle_multipart_post(endpoint_str: str) -> Tuple[Response, int]:
        """Handle a binary (multipart) POST for a binary transport endpoint.

        Body: a small ``params`` JSON form field (window fields) plus a ``mesh``
        file (.npy, optionally gzipped). The mesh is decoded to the same list
        structure the JSON path produces, then dispatched to the controller via
        the logical endpoint — so validation/service/response logic is reused
        unchanged. Only the transport differs (no multi-second JSON mesh parse).
        """
        try:
            raw_params = request.form.get("params")
            if not raw_params:
                raise BadRequest("Missing 'params' form field")
            try:
                request_data = orjson.loads(raw_params)
            except orjson.JSONDecodeError as e:
                raise BadRequest(f"Invalid params JSON: {e}")

            mesh_file = request.files.get(RequestField.MESH.value)
            if mesh_file is not None:
                request_data[RequestField.MESH.value] = (
                    RequestHandler._mesh_decoder.decode(mesh_file.read())
                )

            binary_endpoint = BinaryEndpointName.by_value(endpoint_str)
            endpoint = BinaryEndpointLogicalMap.get(binary_endpoint)
            result = ObstructionController.call(endpoint, request_data)  # type: ignore

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
            # receives the full mesh, so body parsing dominates here too). Mirror
            # get_json's error contract: empty/invalid body → 400, not 500.
            raw = request.get_data()
            if not raw:
                raise BadRequest("Request body cannot be empty")
            try:
                request_data = orjson.loads(raw)
            except orjson.JSONDecodeError as e:
                raise BadRequest(f"Invalid JSON: {e}")
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

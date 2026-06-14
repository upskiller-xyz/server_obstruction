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
from src.server.services.timing import StageTimer

logger = logging.getLogger(__name__)


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
            if not isinstance(request_data, dict):
                raise BadRequest("'params' must be a JSON object")

            # The binary transport contract requires a mesh file (see OpenAPI);
            # fail fast with a clear 400 instead of a generic validation error later.
            mesh_file = request.files.get(RequestField.MESH.value)
            if mesh_file is None:
                raise BadRequest("Missing 'mesh' file")
            # Binary decode is ~ms (np.load) vs multi-second JSON parse; timed to
            # confirm the win. One timer for the whole mesh, not per vertex.
            with StageTimer("decode_mesh", logger):
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

        except Exception:
            # Log full traceback server-side; return a generic message so internal
            # details are not leaked to the client.
            logger.error(f"{endpoint_str} endpoint failed", exc_info=True)
            return jsonify({
                "status": ResponseStatus.ERROR.value,
                "error": "Internal server error"
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
            with StageTimer("parse_body", logger):
                try:
                    request_data = orjson.loads(raw)
                except orjson.JSONDecodeError as e:
                    raise BadRequest(f"Invalid JSON: {e}")
            # Non-object JSON (list/null/number) would fail confusingly downstream;
            # reject it as a client error. An empty object ({}) is allowed through so
            # the validator can report the specific missing fields.
            if not isinstance(request_data, dict):
                raise BadRequest("Request body must be a JSON object")

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

        except Exception:
            # Log full traceback server-side; return a generic message so internal
            # details are not leaked to the client.
            logger.error(f"{endpoint_str} endpoint failed", exc_info=True)
            return jsonify({
                "status": ResponseStatus.ERROR.value,
                "error": "Internal server error"
            }), HTTPStatus.INTERNAL_SERVER_ERROR.value

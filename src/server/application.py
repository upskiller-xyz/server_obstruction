"""Server application implementation"""
import os
import sys
import logging
import multiprocessing
from typing import Dict, Any
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

from src.server.base.constants import (
    ResponseStatus, HTTPStatus, HTTPMethod, ContentType,
    EndpointName
)
from src.server.controllers.obstruction_controller import ObstructionController
from src.server.controllers.endpoint_config import EndpointMethodMap
from src.server.openapi import OpenAPISpecGenerator


logger = logging.getLogger(__name__)


class ServerApplication:
    """Main application class implementing dependency injection and OOP principles"""

    def __init__(self, app_name: str = "Server Application") -> None:
        """
        Initialize the Flask application with dependencies.

        Args:
            app_name: Name of the Flask application
        """
        self._app: Flask = Flask(app_name)
        CORS(self._app)
        self._route_handlers: Dict[str, Any] = {}
        self._setup_dependencies()
        self._setup_routes()

    def _setup_dependencies(self) -> None:
        """Setup all dependencies using dependency injection"""

        # Log worker/thread configuration
        workers = int(os.getenv("WORKERS", "1"))
        threads = int(os.getenv("THREADS", "8"))
        cpu_count = multiprocessing.cpu_count()
        max_concurrent = workers * threads

        logger.info("=" * 60)
        logger.info("GUNICORN WORKER CONFIGURATION")
        logger.info("=" * 60)
        logger.info(f"  CPU Cores Available:  {cpu_count}")
        logger.info(f"  Workers (processes):  {workers}")
        logger.info(f"  Threads per worker:   {threads}")
        logger.info(f"  Max concurrent reqs:  {max_concurrent} ({workers}×{threads})")
        logger.info(f"  Workers per core:     {workers/cpu_count:.1f}x")
        logger.info("=" * 60)

    def _call(
        self,
        endpoint_str: str
    ) -> tuple[Response, Any]:
        """
        Generic handler for JSON POST requests with consistent error handling

        Uses Strategy Pattern - different controller methods can be passed in
        """
        try:
            if not request.is_json:
                raise BadRequest(f"Content-Type must be {ContentType.JSON.value}")

            request_data = request.get_json()

            if not request_data:
                raise BadRequest("Request body cannot be empty")
            endpoint = EndpointName.by_value(endpoint_str)
            result = ObstructionController.call(endpoint, request_data) # type: ignore

            # Check result status (controllers return dict with "status" key)
            if result.get("status") == ResponseStatus.ERROR.value:
                return jsonify(result), HTTPStatus.BAD_REQUEST.value

            return jsonify(result), HTTPStatus.OK.value

        except BadRequest as e:
            return jsonify({
                "status": ResponseStatus.ERROR.value,
                "error": str(e)
            }), HTTPStatus.BAD_REQUEST.value
        except Exception as e:
            logger.error(f"{endpoint} endpoint failed: {str(e)}")
            return jsonify({
                "status": ResponseStatus.ERROR.value,
                "error": f"Internal server error: {str(e)}"
            }), HTTPStatus.INTERNAL_SERVER_ERROR.value

    def _setup_routes(self) -> None:
        """Setup Flask routes using Enumerator Pattern"""
        # Strategy Pattern: Map endpoints to their configurations

        def create_handler(endpoint_value: str):
            """Create a route handler for the given endpoint"""
            def handler():
                return self._call(endpoint_value)
            handler.__name__ = f'handler_{endpoint_value}'
            return handler

        for endpoint in EndpointName.get_members():
            path = "/" + endpoint.value
            handler = create_handler(endpoint.value)

            # Special handling for GET endpoints
            if endpoint == EndpointName.STATUS:
                path = "/"
                handler = self._get_status
            elif endpoint == EndpointName.ROUTES:
                handler = self._list_routes

            self._app.add_url_rule(
                path,
                endpoint.value,
                handler,
                methods=[EndpointMethodMap.get(endpoint).value]
            )

        # Add documentation endpoints
        self._app.add_url_rule("/openapi.json", "openapi_spec", self._openapi_spec, methods=["GET"])
        self._app.add_url_rule("/docs", "swagger_ui", self._swagger_ui, methods=["GET"])
        self._app.add_url_rule("/redoc", "redoc", self._redoc, methods=["GET"])

        # Log registered routes
        logger.info("Registered routes:")
        for rule in self._app.url_map.iter_rules():
            if rule.methods is not None:
                methods = ', '.join(sorted(rule.methods - {HTTPMethod.HEAD.value, HTTPMethod.OPTIONS.value}))
            logger.info(f"  {rule.rule:30} [{methods}]")

    def _get_status(self) -> Response:
        """
        Get server status endpoint.

        Returns:
            JSON response with server status information
        """
        return jsonify(ObstructionController.get_status())

    def _list_routes(self) -> Response:
        """
        List all registered routes (debug endpoint).

        Returns:
            JSON response with all registered routes
        """
        routes = []
        for rule in self._app.url_map.iter_rules():
            if rule.methods is not None:
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': sorted(list(rule.methods - {HTTPMethod.HEAD.value, HTTPMethod.OPTIONS.value})),
                    'path': rule.rule
                })
        routes.sort(key=lambda x: x['path'])
        return jsonify({
            'status': ResponseStatus.SUCCESS.value,
            'total_routes': len(routes),
            'routes': routes
        })

    def _openapi_spec(self) -> Dict[str, Any]:
        """
        Return OpenAPI 3.0 specification.

        Returns:
            JSON with complete API specification
        """
        spec = OpenAPISpecGenerator.generate_spec(
            title="Obstruction Calculation API",
            description="Service for calculating horizon and zenith obstruction angles from 3D mesh data",
            version="1.0.0",
            base_url="/"
        )
        return jsonify(spec)

    def _swagger_ui(self) -> str:
        """
        Return Swagger UI HTML.

        Interactive API documentation at /docs
        """
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Obstruction Calculation API - Swagger UI</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css">
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
            <script>
            window.onload = function() {
                window.ui = SwaggerUIBundle({
                    url: "/openapi.json",
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",
                    requestInterceptor: (request) => {
                        request.headers['X-API-Version'] = '1.0.0';
                        return request;
                    }
                })
            }
            </script>
        </body>
        </html>
        """

    def _redoc(self) -> str:
        """
        Return ReDoc HTML.

        Alternative interactive API documentation at /redoc
        """
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Obstruction Calculation API - ReDoc</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
            <style>
              body {
                margin: 0;
                padding: 0;
              }
            </style>
        </head>
        <body>
            <redoc spec-url='/openapi.json'></redoc>
            <script src="https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js"></script>
        </body>
        </html>
        """

    @property
    def app(self) -> Flask:
        """
        Get Flask application instance.

        Returns:
            Flask: The Flask application object
        """
        return self._app

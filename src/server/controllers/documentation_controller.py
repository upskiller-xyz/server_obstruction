"""Documentation controller for OpenAPI spec and UI"""

from typing import Any, Dict

from flask import Response, jsonify

from src.server.base.constants import HTTPMethod, ResponseStatus
from src.server.controllers.obstruction_controller import ObstructionController
from src.server.openapi import OpenAPISpecGenerator
from src.server.services.template_loader import TemplateLoader


class DocumentationController:
    """
    Controller for API documentation endpoints

    Single Responsibility:
    - Only handles documentation-related endpoints
    - Does NOT handle obstruction calculations or route registration
    """

    @staticmethod
    def get_status() -> Response:
        """
        Get server status endpoint

        Returns:
            JSON response with server status information
        """
        return jsonify(ObstructionController.get_status())

    @staticmethod
    def list_routes(app) -> Response:
        """
        List all registered routes (debug endpoint)

        Args:
            app: Flask application instance

        Returns:
            JSON response with all registered routes
        """
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.methods is not None:
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': sorted(list(
                        rule.methods - {HTTPMethod.HEAD.value, HTTPMethod.OPTIONS.value}
                    )),
                    'path': rule.rule
                })
        routes.sort(key=lambda x: x['path'])
        return jsonify({
            'status': ResponseStatus.SUCCESS.value,
            'total_routes': len(routes),
            'routes': routes
        })

    @staticmethod
    def get_openapi_spec() -> Response:
        """
        Return OpenAPI 3.0 specification

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

    @staticmethod
    def get_swagger_ui() -> str:
        """
        Return Swagger UI HTML

        Interactive API documentation at /docs

        Returns:
            HTML string for Swagger UI
        """
        return TemplateLoader.load("swagger_ui.html")

    @staticmethod
    def get_redoc() -> str:
        """
        Return ReDoc HTML

        Alternative interactive API documentation at /redoc

        Returns:
            HTML string for ReDoc
        """
        return TemplateLoader.load("redoc.html")

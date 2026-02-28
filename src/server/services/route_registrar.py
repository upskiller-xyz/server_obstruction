"""Route registration service for Flask application"""

import logging
from typing import Callable

from flask import Flask

from src.server.base.constants import EndpointName, HTTPMethod
from src.server.controllers.endpoint_config import EndpointMethodMap


class RouteRegistrar:
    """
    Registers routes with Flask application

    Single Responsibility:
    - Only handles route registration
    - Does NOT handle requests or create handlers
    """

    @staticmethod
    def register_routes(
        app: Flask,
        handler_factory: Callable[[str], Callable],
        status_handler: Callable,
        routes_handler: Callable
    ) -> None:
        """
        Register all application routes

        Args:
            app: Flask application instance
            handler_factory: Factory function to create endpoint handlers
            status_handler: Handler for status endpoint
            routes_handler: Handler for routes listing endpoint
        """
        # Register main endpoints
        for endpoint in EndpointName.get_members():
            path = "/" + endpoint.value
            handler = handler_factory(endpoint.value)

            # Special handling for GET endpoints
            if endpoint == EndpointName.STATUS:
                path = "/"
                handler = status_handler
            elif endpoint == EndpointName.ROUTES:
                handler = routes_handler

            app.add_url_rule(
                path,
                endpoint.value,
                handler,
                methods=[EndpointMethodMap.get(endpoint).value]
            )

    @staticmethod
    def register_documentation_routes(
        app: Flask,
        openapi_handler: Callable,
        swagger_handler: Callable,
        redoc_handler: Callable
    ) -> None:
        """
        Register documentation routes

        Args:
            app: Flask application instance
            openapi_handler: OpenAPI spec handler
            swagger_handler: Swagger UI handler
            redoc_handler: ReDoc handler
        """
        app.add_url_rule("/openapi.json", "openapi_spec", openapi_handler, methods=["GET"])
        app.add_url_rule("/docs", "swagger_ui", swagger_handler, methods=["GET"])
        app.add_url_rule("/redoc", "redoc", redoc_handler, methods=["GET"])

    @staticmethod
    def log_registered_routes(app: Flask) -> None:
        """
        Log all registered routes

        Args:
            app: Flask application instance
        """
        logging.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            if rule.methods is not None:
                methods = ', '.join(sorted(
                    rule.methods - {HTTPMethod.HEAD.value, HTTPMethod.OPTIONS.value}
                ))
                logging.info(f"  {rule.rule:30} [{methods}]")

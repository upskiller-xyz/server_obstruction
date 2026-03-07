"""Server application implementation"""

import logging
import multiprocessing
import os

from flask import Flask
from flask_cors import CORS

from src.server.controllers.documentation_controller import DocumentationController
from src.server.services.request_handler import RequestHandler
from src.server.services.route_registrar import RouteRegistrar


class ServerApplication:
    """
    Main application class implementing dependency injection and OOP principles

    Single Responsibility:
    - Orchestrates application setup and configuration
    - Delegates route registration to RouteRegistrar
    - Delegates request handling to RequestHandler
    - Delegates documentation to DocumentationController

    Follows OOP principles:
    - Uses dependency injection
    - Delegates to focused classes
    - No business logic in this class
    """

    def __init__(self, app_name: str = "Server Application") -> None:
        """
        Initialize the Flask application with dependencies

        Args:
            app_name: Name of the Flask application
        """
        self._app: Flask = Flask(app_name)
        CORS(self._app)
        self._setup_dependencies()
        self._setup_routes()

    def _setup_dependencies(self) -> None:
        """
        Setup all dependencies using dependency injection

        Logs worker/thread configuration for monitoring
        """
        # Log worker/thread configuration
        workers = int(os.getenv("WORKERS", "1"))
        threads = int(os.getenv("THREADS", "8"))
        cpu_count = multiprocessing.cpu_count()
        max_concurrent = workers * threads

        logging.info("=" * 60)
        logging.info("GUNICORN WORKER CONFIGURATION")
        logging.info("=" * 60)
        logging.info(f"  CPU Cores Available:  {cpu_count}")
        logging.info(f"  Workers (processes):  {workers}")
        logging.info(f"  Threads per worker:   {threads}")
        logging.info(f"  Max concurrent reqs:  {max_concurrent} ({workers}×{threads})")
        logging.info(f"  Workers per core:     {workers/cpu_count:.1f}x")
        logging.info("=" * 60)

    def _setup_routes(self) -> None:
        """
        Setup Flask routes using RouteRegistrar

        Delegates route registration to dedicated service
        """
        # Create handler factory
        def create_handler(endpoint_value: str):
            """Create a route handler for the given endpoint"""
            def handler():
                return RequestHandler.handle_json_post(endpoint_value)
            handler.__name__ = f'handler_{endpoint_value}'
            return handler

        # Delegate main route registration to RouteRegistrar
        RouteRegistrar.register_routes(
            self._app,
            handler_factory=create_handler,
            status_handler=self._get_status,
            routes_handler=self._list_routes
        )

        # Delegate documentation route registration
        RouteRegistrar.register_documentation_routes(
            self._app,
            openapi_handler=DocumentationController.get_openapi_spec,
            swagger_handler=DocumentationController.get_swagger_ui,
            redoc_handler=DocumentationController.get_redoc
        )

        # Log all registered routes
        RouteRegistrar.log_registered_routes(self._app)

    def _get_status(self):
        """
        Get server status endpoint

        Delegates to DocumentationController
        """
        return DocumentationController.get_status()

    def _list_routes(self):
        """
        List all registered routes

        Delegates to DocumentationController
        """
        return DocumentationController.list_routes(self._app)

    @property
    def app(self) -> Flask:
        """
        Get Flask application instance.

        Returns:
            Flask: The Flask application object
        """
        return self._app

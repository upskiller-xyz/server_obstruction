import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Callable

# Add project root to path FIRST
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Disable GPU/CUDA to prevent bus errors on WSL2
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '0'
os.environ['OMP_NUM_THREADS'] = '1'

# Configure root logger to show all logs from all modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Import after path is set
from src.server.controllers.obstruction_controller import ObstructionController
from src.server.controllers.endpoint_config import EndpointMethodMap

import multiprocessing
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

from src.server.base.constants import (
    ResponseStatus, HTTPStatus, HTTPMethod, ContentType,
    EndpointName
)


class ServerApplication:
    """Main application class implementing dependency injection and OOP principles"""

    def __init__(self, app_name: str = "Server Application"):
        self._app = Flask(app_name)
        CORS(self._app)
        self._route_handlers = {}
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

        # Raytracing service (using Factory Pattern)


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
            result = ObstructionController.call(endpoint, request_data)

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

        # Log registered routes
        logger.info("Registered routes:")
        for rule in self._app.url_map.iter_rules():
            if rule.methods is not None:
                methods = ', '.join(sorted(rule.methods - {HTTPMethod.HEAD.value, HTTPMethod.OPTIONS.value}))
            logger.info(f"  {rule.rule:30} [{methods}]")

    def _get_status(self) -> Response:
        """Get server status endpoint"""
        return jsonify(ObstructionController.get_status())

    def _list_routes(self) -> Response:
        """List all registered routes (debug endpoint)"""
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
    
    
    
    @property
    def app(self) -> Flask:
        """Get Flask application instance"""
        return self._app


class ServerLauncher:
    """Launcher class for the server application"""

    @staticmethod
    def create_application() -> ServerApplication:
        """Create and configure the application"""
        return ServerApplication()

    @staticmethod
    def run_server(
        app: ServerApplication,
        host: str = "0.0.0.0",
        port: int = 8081,
        debug: bool = True
    ) -> None:
        """Run the server"""
        """Run the server"""
        log_msg = (
            f"Flask app '{app.app.name}' starting on "
            f"host {host}, port {port}. Debug mode: {debug}"
        )
        app.app.logger.info(log_msg)
        # Disable reloader to prevent bus errors/hangs on WSL2
        app.app.run(host=host, port=port, debug=debug, use_reloader=False)


def main() -> None:
    """Main entry point"""
    launcher = ServerLauncher()
    application = launcher.create_application()
    port = int(os.getenv("PORT", 8081))
    launcher.run_server(application, port=port, debug=True)


# Create app instance for gunicorn only when needed
# Don't create at module import time to avoid bus errors
def create_app():
    """Factory function for creating the Flask app (for gunicorn)"""
    _application = ServerApplication()
    return _application.app


# Only create app instance if not running as main (i.e., when imported by gunicorn)
if __name__ != "__main__":
    app = create_app()
else:
    # Running as main script
    main()
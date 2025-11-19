import os
from typing import Dict, Any

# Disable GPU/CUDA to prevent bus errors on WSL2
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '0'
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import logging
from pathlib import Path

# Configure root logger to show all logs from all modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import multiprocessing
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from http import HTTPStatus
from src.server.services.logging import StructuredLogger
from src.server.enums import LogLevel, ContentType
from src.server.controllers.base_controller import ServerController
from src.server.services.obstruction_service import ObstructionServiceFactory
from src.server.services.parallel_obstruction_service import ParallelObstructionServiceFactory
from src.server.controllers.obstruction_controller import ObstructionController




class ServerApplication:
    """Main application class implementing dependency injection and OOP principles"""

    def __init__(self, app_name: str = "Server Application"):
        self._app = Flask(app_name)
        CORS(self._app)
        self._controller = None
        self._logger = None
        self._setup_dependencies()
        self._setup_routes()

    def _setup_dependencies(self) -> None:
        """Setup all dependencies using dependency injection"""
        # Logger
        self._logger = StructuredLogger("Server", LogLevel.INFO)

        # Log worker/thread configuration
        workers = int(os.getenv("WORKERS", "1"))
        threads = int(os.getenv("THREADS", "8"))
        cpu_count = multiprocessing.cpu_count()
        max_concurrent = workers * threads

        self._logger.info("=" * 60)
        self._logger.info("GUNICORN WORKER CONFIGURATION")
        self._logger.info("=" * 60)
        self._logger.info(f"  CPU Cores Available:  {cpu_count}")
        self._logger.info(f"  Workers (processes):  {workers}")
        self._logger.info(f"  Threads per worker:   {threads}")
        self._logger.info(f"  Max concurrent reqs:  {max_concurrent} ({workers}×{threads})")
        self._logger.info(f"  Workers per core:     {workers/cpu_count:.1f}x")
        self._logger.info("=" * 60)

        # Raytracing service (using Factory Pattern)
        self._raytrace_service = ObstructionServiceFactory.create_default_service(self._logger)

        # Parallel obstruction service (optional - configured per request)
        # Microservice URL will be provided in request data
        self._parallel_service = None

        # Raytracing controller
        self._raytrace_controller = ObstructionController(
            raytrace_service=self._raytrace_service,
            logger=self._logger,
            parallel_service=self._parallel_service
        )

        # Services for base controller
        services = {
            "raytrace_service": self._raytrace_service
        }

        # Controller
        self._controller = ServerController(
            logger=self._logger,
            services=services
        )

        # Initialize controller
        self._controller.initialize()

    def _setup_routes(self) -> None:
        """Setup Flask routes"""
        self._app.add_url_rule("/", "get_status", self._get_status, methods=["GET"])
        self._app.add_url_rule("/routes", "list_routes", self._list_routes, methods=["GET"])
        self._app.add_url_rule("/horizon_angle", "horizon_angle", self._horizon_angle, methods=["POST"])
        self._app.add_url_rule("/obstruction", "obstruction", self._obstruction, methods=["POST"])
        self._app.add_url_rule("/zenith_angle", "zenith_angle", self._zenith_angle, methods=["POST"])
        self._app.add_url_rule("/obstruction_all", "obstruction_all", self._obstruction_all, methods=["POST"])
        self._app.add_url_rule("/obstruction_parallel", "obstruction_parallel", self._obstruction_parallel, methods=["POST"])
        self._app.add_url_rule("/route_example", "route_example", self._route_example, methods=["POST"])

        # Log registered routes
        self._logger.info("Registered routes:")
        for rule in self._app.url_map.iter_rules():
            methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            self._logger.info(f"  {rule.rule:30} [{methods}]")

    def _get_status(self) -> Dict[str, Any]:
        """Get server status endpoint"""
        return jsonify(self._controller.get_status())

    def _list_routes(self) -> Dict[str, Any]:
        """List all registered routes (debug endpoint)"""
        routes = []
        for rule in self._app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': sorted(list(rule.methods - {'HEAD', 'OPTIONS'})),
                'path': rule.rule
            })
        routes.sort(key=lambda x: x['path'])
        return jsonify({
            'status': 'success',
            'total_routes': len(routes),
            'routes': routes
        })

    def _horizon_angle(self) -> Dict[str, Any]:
        """
        Horizon angle calculation endpoint

        Calculates the angle from the horizontal plane at the window center
        upward to the highest point of obstruction in the viewing direction.
        """
        try:
            # Get JSON data from request
            if not request.is_json:
                raise BadRequest("Content-Type must be application/json")

            request_data = request.get_json()

            if not request_data:
                raise BadRequest("Request body cannot be empty")

            # Delegate to obstruction controller
            result = self._raytrace_controller.calculate_obstruction(request_data)

            # Check for errors
            if result.get("status") == "error":
                return jsonify(result), HTTPStatus.BAD_REQUEST.value

            return jsonify(result)

        except BadRequest as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), HTTPStatus.BAD_REQUEST.value
        except Exception as e:
            self._logger.error(f"Horizon angle endpoint failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Internal server error: {str(e)}"
            }), HTTPStatus.INTERNAL_SERVER_ERROR.value

    def _obstruction(self) -> Dict[str, Any]:
        """
        Obstruction calculation endpoint

        Calculates both horizon and zenith angles for a given window and mesh.
        """
        try:
            # Get JSON data from request
            if not request.is_json:
                raise BadRequest("Content-Type must be application/json")

            request_data = request.get_json()

            if not request_data:
                raise BadRequest("Request body cannot be empty")

            # Delegate to obstruction controller
            result = self._raytrace_controller.calculate_both_angles(request_data)

            # Check for errors
            if result.get("status") == "error":
                return jsonify(result), HTTPStatus.BAD_REQUEST.value

            return jsonify(result)

        except BadRequest as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), HTTPStatus.BAD_REQUEST.value
        except Exception as e:
            self._logger.error(f"Obstruction endpoint failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Internal server error: {str(e)}"
            }), HTTPStatus.INTERNAL_SERVER_ERROR.value

    def _zenith_angle(self) -> Dict[str, Any]:
        """
        Zenith angle calculation endpoint

        Calculates the angle from vertical (90°) downward to the lowest
        overhead obstruction (like balconies or roofs).
        """
        try:
            # Get JSON data from request
            if not request.is_json:
                raise BadRequest("Content-Type must be application/json")

            request_data = request.get_json()

            if not request_data:
                raise BadRequest("Request body cannot be empty")

            # Delegate to obstruction controller
            result = self._raytrace_controller.calculate_zenith_angle(request_data)

            # Check for errors
            if result.get("status") == "error":
                return jsonify(result), HTTPStatus.BAD_REQUEST.value

            return jsonify(result)

        except BadRequest as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), HTTPStatus.BAD_REQUEST.value
        except Exception as e:
            self._logger.error(f"Zenith angle endpoint failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Internal server error: {str(e)}"
            }), HTTPStatus.INTERNAL_SERVER_ERROR.value

    def _obstruction_all(self) -> Dict[str, Any]:
        """
        All-direction obstruction calculation endpoint

        Calculates both horizon and zenith angles for all directions around the window.
        The number of directions can be specified with the 'num_directions' parameter.
        """
        try:
            # Get JSON data from request
            if not request.is_json:
                raise BadRequest("Content-Type must be application/json")

            request_data = request.get_json()

            if not request_data:
                raise BadRequest("Request body cannot be empty")

            # Delegate to obstruction controller
            result = self._raytrace_controller.calculate_all_directions(request_data)

            # Check for errors
            if result.get("status") == "error":
                return jsonify(result), HTTPStatus.BAD_REQUEST.value

            return jsonify(result)

        except BadRequest as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), HTTPStatus.BAD_REQUEST.value
        except Exception as e:
            self._logger.error(f"All-direction obstruction endpoint failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Internal server error: {str(e)}"
            }), HTTPStatus.INTERNAL_SERVER_ERROR.value

    def _obstruction_parallel(self) -> Dict[str, Any]:
        """
        Parallel multi-direction obstruction calculation endpoint

        Calculates obstruction angles for 64 directions in parallel by making
        HTTP requests to a microservice endpoint. The microservice URL must be
        provided in the request body.

        Request body must include:
        - x, y, z: window center coordinates
        - mesh: list of vertex coordinates
        - microservice_url: URL of the /obstruction endpoint to call in parallel
        - num_directions (optional): number of directions (default 64)
        - start_angle_degrees (optional): start angle (default 17.5°)
        - end_angle_degrees (optional): end angle (default 162.5°)
        - auth_token (optional): Bearer token for GCP authentication
        """
        try:
            # Get JSON data from request
            if not request.is_json:
                raise BadRequest("Content-Type must be application/json")

            request_data = request.get_json()

            if not request_data:
                raise BadRequest("Request body cannot be empty")

            # Extract microservice URL from request (default to internal /obstruction endpoint)
            microservice_url = request_data.get("microservice_url")
            if not microservice_url:
                # Use internal endpoint - construct from request context
                microservice_url = f"{request.scheme}://{request.host}/obstruction"
                self._logger.info(f"Using internal obstruction endpoint: {microservice_url}")

            # Extract optional auth token (only for external calls)
            auth_token = request_data.get("auth_token")
            
            # Create parallel service dynamically for this request
            from src.server.services.parallel_obstruction_service import ParallelObstructionServiceFactory

            parallel_service = ParallelObstructionServiceFactory.create_service(
                microservice_url=microservice_url,
                logger=self._logger,
                auth_token=auth_token
            )
            self._logger.info("start parakkek service")
            # Temporarily assign parallel service to controller
            self._raytrace_controller._parallel_service = parallel_service
            self._logger.info("start calculation")
            # Delegate to obstruction controller
            result = self._raytrace_controller.calculate_parallel_multi_direction(request_data)

            # Clear parallel service after use
            self._raytrace_controller._parallel_service = None

            # Check for errors
            if result.get("status") == "error":
                return jsonify(result), HTTPStatus.BAD_REQUEST.value

            return jsonify(result)

        except BadRequest as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), HTTPStatus.BAD_REQUEST.value
        except Exception as e:
            self._logger.error(f"Parallel obstruction endpoint failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Internal server error: {str(e)}"
            }), HTTPStatus.INTERNAL_SERVER_ERROR.value

    def _route_example(self) -> Dict[str, Any]:
        """Run prediction endpoint"""
        # Check if file was uploaded
        if 'file' not in request.files:
            raise BadRequest("No file uploaded")

        file = request.files['file']

        # Validate content type
        # remove if using other input types
        if not ContentType.is_image(file.content_type):
            raise BadRequest("File must be an image")

        try:
            # endpoint logic

            result = {}

            # Check for errors
            if result.get("status") == "error":
                return jsonify(result), HTTPStatus.INTERNAL_SERVER_ERROR.value

            return jsonify(result)

        except Exception as e:
            return jsonify({"error": f"Prediction failed: {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR.value

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
        port: int = 8080,
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
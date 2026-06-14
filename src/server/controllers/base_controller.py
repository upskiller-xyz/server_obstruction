import logging
from typing import Any, Dict, Optional

from src.server.enums import ServerStatus


class ServerController:
    """Generic server controller"""

    def __init__(
        self,
        services: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the controller with dependencies

        Args:
            services: Optional dictionary of service name -> service instance
        """
        self._services = services or {}
        self._status = ServerStatus.STARTING

    def initialize(self) -> None:
        """Initialize the server and its components"""
        logging.info("Initializing server controller")
        try:
            # Initialize all registered services
            for service_name, service in self._services.items():
                if hasattr(service, 'initialize'):
                    logging.debug(f"Initializing service: {service_name}")
                    service.initialize()

            self._status = ServerStatus.RUNNING
            logging.info("Server controller initialized successfully")
        except Exception as e:
            self._status = ServerStatus.ERROR
            logging.error(f"Failed to initialize server controller: {str(e)}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """
        Get current server status

        Returns:
            Dictionary containing status information
        """
        components = {}
        for service_name, service in self._services.items():
            if hasattr(service, 'get_status'):
                components[service_name] = service.get_status()
            else:
                components[service_name] = "ready"

        return {
            "status": self._status.value,
            "services": components
        }

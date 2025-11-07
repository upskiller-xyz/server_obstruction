from typing import Dict, Any
from src.server.interfaces import ILogger
from src.components.raytracing_models import RaytraceRequest, RaytraceResult
from src.components.projection import IProjectionCalculator, OrthographicProjectionCalculator
from src.components.obstruction_calculator import IObstructionCalculator, MaxHeightObstructionCalculator, ZenithAngleCalculator


class RaytraceService:
    """
    Service orchestrating raytracing operations

    Follows Single Responsibility Principle:
    - Coordinates projection and obstruction calculations
    - Does not handle HTTP/request parsing
    - Does not perform low-level calculations
    """

    def __init__(
        self,
        projection_calculator: IProjectionCalculator,
        obstruction_calculator: IObstructionCalculator,
        zenith_calculator: IObstructionCalculator,
        logger: ILogger
    ):
        """
        Initialize with dependencies (Dependency Injection pattern)

        Args:
            projection_calculator: Calculator for 3D to 2D projections
            obstruction_calculator: Calculator for horizon angles
            zenith_calculator: Calculator for zenith angles
            logger: Structured logger instance
        """
        self._projection_calculator = projection_calculator
        self._obstruction_calculator = obstruction_calculator
        self._zenith_calculator = zenith_calculator
        self._logger = logger

    def calculate_obstruction(self, request: RaytraceRequest) -> RaytraceResult:
        """
        Calculate obstruction angle for given window and geometry

        Args:
            request: Raytracing request with window and mesh data

        Returns:
            RaytraceResult with obstruction angle and metadata

        Raises:
            ValueError: If request data is invalid
        """
        self._logger.debug(
            f"Starting raytrace calculation for window at "
            f"({request.window.center.x}, {request.window.center.y}, {request.window.center.z})"
        )

        try:
            # Step 1: Create projection plane
            plane = self._projection_calculator.create_projection_plane(request.window)
            self._logger.debug("Projection plane created")

            # Step 2: Project mesh onto plane
            projected_points = self._projection_calculator.project_mesh(
                request.mesh,
                plane
            )
            self._logger.debug(f"Projected {len(projected_points)} points onto plane")

            # Step 3: Calculate obstruction angle
            # Reference height is 0 since we're measuring from the window center
            # (which is at the origin of the projection plane)
            # Pass window center and normal for accurate angle calculation in viewing plane
            result = self._obstruction_calculator.calculate_obstruction_angle(
                projected_points,
                reference_height=0.0,
                window_center=request.window.center,
                window_normal=request.window.normal
            )

            self._logger.info(
                f"Obstruction angle calculated: {result.obstruction_angle_degrees:.2f}°"
            )

            return result

        except Exception as e:
            self._logger.error(f"Raytrace calculation failed: {str(e)}")
            raise

    def calculate_zenith_angle(self, request: RaytraceRequest) -> RaytraceResult:
        """
        Calculate zenith angle for given window and geometry

        The zenith angle measures the angle from vertical (90°) downward to
        the lowest overhead obstruction (like balconies or roofs).

        Args:
            request: Raytracing request with window and mesh data

        Returns:
            RaytraceResult with zenith angle and metadata

        Raises:
            ValueError: If request data is invalid
        """
        self._logger.debug(
            f"Starting zenith angle calculation for window at "
            f"({request.window.center.x}, {request.window.center.y}, {request.window.center.z})"
        )

        try:
            # Step 1: Create projection plane
            plane = self._projection_calculator.create_projection_plane(request.window)
            self._logger.debug("Projection plane created")

            # Step 2: Project mesh onto plane
            projected_points = self._projection_calculator.project_mesh(
                request.mesh,
                plane
            )
            self._logger.debug(f"Projected {len(projected_points)} points onto plane")

            # Step 3: Calculate zenith angle
            result = self._zenith_calculator.calculate_obstruction_angle(
                projected_points,
                reference_height=0.0,
                window_center=request.window.center,
                window_normal=request.window.normal
            )

            self._logger.info(
                f"Zenith angle calculated: {result.obstruction_angle_degrees:.2f}°"
            )

            return result

        except Exception as e:
            self._logger.error(f"Zenith angle calculation failed: {str(e)}")
            raise

    def calculate_both_angles(self, request: RaytraceRequest) -> Dict[str, RaytraceResult]:
        """
        Calculate both horizon and zenith angles

        Args:
            request: Raytracing request with window and mesh data

        Returns:
            Dictionary with 'horizon' and 'zenith' RaytraceResults
        """
        horizon_result = self.calculate_obstruction(request)
        zenith_result = self.calculate_zenith_angle(request)

        return {
            "horizon": horizon_result,
            "zenith": zenith_result
        }

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "status": "ready",
            "projection_calculator": type(self._projection_calculator).__name__,
            "horizon_calculator": type(self._obstruction_calculator).__name__,
            "zenith_calculator": type(self._zenith_calculator).__name__
        }


class RaytraceServiceFactory:
    """
    Factory for creating RaytraceService instances (Factory Pattern)

    Centralizes service configuration and dependency wiring
    """

    @staticmethod
    def create_default_service(logger: ILogger) -> RaytraceService:
        """
        Create service with default implementations

        Args:
            logger: Logger instance

        Returns:
            Configured RaytraceService
        """
        projection_calculator = OrthographicProjectionCalculator()
        obstruction_calculator = MaxHeightObstructionCalculator()
        zenith_calculator = ZenithAngleCalculator()

        return RaytraceService(
            projection_calculator=projection_calculator,
            obstruction_calculator=obstruction_calculator,
            zenith_calculator=zenith_calculator,
            logger=logger
        )

    @staticmethod
    def create_custom_service(
        projection_calculator: IProjectionCalculator,
        obstruction_calculator: IObstructionCalculator,
        zenith_calculator: IObstructionCalculator,
        logger: ILogger
    ) -> RaytraceService:
        """
        Create service with custom implementations

        Args:
            projection_calculator: Custom projection calculator
            obstruction_calculator: Custom horizon angle calculator
            zenith_calculator: Custom zenith angle calculator
            logger: Logger instance

        Returns:
            Configured RaytraceService
        """
        return RaytraceService(
            projection_calculator=projection_calculator,
            obstruction_calculator=obstruction_calculator,
            zenith_calculator=zenith_calculator,
            logger=logger
        )

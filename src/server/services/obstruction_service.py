from typing import Dict, Any
import time
from src.server.interfaces import ILogger
from src.components.obstruction_models import ObstructionRequest, ObstructionResult
from src.components.projection import IProjectionCalculator, OrthographicProjectionCalculator
from src.components.obstruction_calculator import IObstructionCalculator, HorizonObstructionCalculator, ZenithAngleCalculator
from src.components.constants import ResponseField, ResponseStatus


class ObstructionService:
    """
    Service orchestrating obstruction calculation operations

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

    def calculate_obstruction(self, request: ObstructionRequest) -> ObstructionResult:
        """
        Calculate obstruction angle for given window and geometry

        Args:
            request: Raytracing request with window and mesh data

        Returns:
            ObstructionResult with obstruction angle and metadata

        Raises:
            ValueError: If request data is invalid
        """
        start_time = time.time()
        self._logger.info(
            f"[TIMING] Starting horizon obstruction calculation for window at "
            f"({request.window.center.x}, {request.window.center.y}, {request.window.center.z})"
        )

        try:
            # Step 1: Create projection plane
            step_start = time.time()
            plane = self._projection_calculator.create_projection_plane(request.window)
            plane_time = time.time() - step_start
            self._logger.info(f"[TIMING] Projection plane created in {plane_time*1000:.2f}ms")

            # Step 2: Project mesh onto plane
            step_start = time.time()
            projected_points = self._projection_calculator.project_mesh(
                request.mesh,
                plane
            )
            projection_time = time.time() - step_start
            self._logger.info(f"[TIMING] Projected {len(projected_points)} points in {projection_time*1000:.2f}ms")

            # Step 3: Calculate obstruction angle
            step_start = time.time()
            result = self._obstruction_calculator.calculate_obstruction_angle(
                projected_points,
                request.window.center,
                request.window.normal
            )
            calc_time = time.time() - step_start
            self._logger.info(f"[TIMING] Obstruction angle calculated in {calc_time*1000:.2f}ms")

            total_time = time.time() - start_time
            self._logger.info(
                f"[TIMING] Horizon obstruction complete: {result.obstruction_angle_degrees:.2f}° "
                f"(total: {total_time*1000:.2f}ms)"
            )

            return result

        except Exception as e:
            self._logger.error(f"Obstruction calculation failed: {str(e)}")
            raise

    def calculate_zenith_angle(self, request: ObstructionRequest) -> ObstructionResult:
        """
        Calculate zenith angle for given window and geometry

        The zenith angle measures the angle from vertical (90°) downward to
        the lowest overhead obstruction (like balconies or roofs).

        Args:
            request: Raytracing request with window and mesh data

        Returns:
            ObstructionResult with zenith angle and metadata

        Raises:
            ValueError: If request data is invalid
        """
        start_time = time.time()
        self._logger.info(
            f"[TIMING] Starting zenith angle calculation for window at "
            f"({request.window.center.x}, {request.window.center.y}, {request.window.center.z})"
        )

        try:
            # Step 1: Create projection plane
            step_start = time.time()
            plane = self._projection_calculator.create_projection_plane(request.window)
            plane_time = time.time() - step_start
            self._logger.info(f"[TIMING] Projection plane created in {plane_time*1000:.2f}ms")

            # Step 2: Project mesh onto plane
            step_start = time.time()
            projected_points = self._projection_calculator.project_mesh(
                request.mesh,
                plane
            )
            projection_time = time.time() - step_start
            self._logger.info(f"[TIMING] Projected {len(projected_points)} points in {projection_time*1000:.2f}ms")

            # Step 3: Calculate zenith angle
            step_start = time.time()
            result = self._zenith_calculator.calculate_obstruction_angle(
                projected_points,
                request.window.center,
                request.window.normal
            )
            calc_time = time.time() - step_start
            self._logger.info(f"[TIMING] Zenith angle calculated in {calc_time*1000:.2f}ms")

            total_time = time.time() - start_time
            self._logger.info(
                f"[TIMING] Zenith angle complete: {result.obstruction_angle_degrees:.2f}° "
                f"(total: {total_time*1000:.2f}ms)"
            )

            return result

        except Exception as e:
            self._logger.error(f"Zenith angle calculation failed: {str(e)}")
            raise

    def calculate_both_angles(self, request: ObstructionRequest) -> Dict[str, ObstructionResult]:
        """
        Calculate both horizon and zenith angles

        Args:
            request: Raytracing request with window and mesh data

        Returns:
            Dictionary with 'horizon' and 'zenith' ObstructionResults
        """
        horizon_result = self.calculate_obstruction(request)
        zenith_result = self.calculate_zenith_angle(request)

        return {
            ResponseField.HORIZON.value: horizon_result,
            ResponseField.ZENITH.value: zenith_result
        }

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            ResponseField.STATUS.value: ResponseStatus.SUCCESS.value,
            "projection_calculator": type(self._projection_calculator).__name__,
            "horizon_calculator": type(self._obstruction_calculator).__name__,
            "zenith_calculator": type(self._zenith_calculator).__name__
        }


class ObstructionServiceFactory:
    """
    Factory for creating ObstructionService instances (Factory Pattern)

    Centralizes service configuration and dependency wiring
    """

    @staticmethod
    def create_default_service(logger: ILogger) -> ObstructionService:
        """
        Create service with default implementations

        Args:
            logger: Logger instance

        Returns:
            Configured ObstructionService
        """
        projection_calculator = OrthographicProjectionCalculator()
        obstruction_calculator = HorizonObstructionCalculator()
        zenith_calculator = ZenithAngleCalculator()

        return ObstructionService(
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
    ) -> ObstructionService:
        """
        Create service with custom implementations

        Args:
            projection_calculator: Custom projection calculator
            obstruction_calculator: Custom horizon angle calculator
            zenith_calculator: Custom zenith angle calculator
            logger: Logger instance

        Returns:
            Configured ObstructionService
        """
        return ObstructionService(
            projection_calculator=projection_calculator,
            obstruction_calculator=obstruction_calculator,
            zenith_calculator=zenith_calculator,
            logger=logger
        )

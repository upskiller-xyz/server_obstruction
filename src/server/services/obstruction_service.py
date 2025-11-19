from typing import Dict, Any, List
import time
import math
import asyncio
import numpy as np
from src.server.interfaces import ILogger
from src.components.obstruction_models import ObstructionRequest, ObstructionResult, Window
from src.components.projection import IProjectionCalculator, OrthographicProjectionCalculator
from src.components.obstruction_calculator import (
    IObstructionCalculator, HorizonObstructionCalculator, ZenithAngleCalculator,
    IntersectionObstructionCalculator, IntersectionZenithCalculator
)
from src.components.constants import ResponseField, ResponseStatus, AllDirectionDefaults
from src.components.geometry import Vector3D, Mesh
from src.components.plane_intersection import TriangleFilter


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

    def calculate_obstruction_efficient(self, request: ObstructionRequest) -> ObstructionResult:
        """
        Calculate obstruction angle using EFFICIENT plane-intersection method

        This method uses plane-triangle intersections instead of projecting all points.
        It's significantly faster because:
        - Pre-filters triangles behind/below window
        - Only processes triangles that intersect the viewing plane
        - No 2D projection step needed
        - Direct angle calculation from 3D intersection points

        Args:
            request: Raytracing request with window and mesh data

        Returns:
            ObstructionResult with obstruction angle and metadata

        Raises:
            ValueError: If request data is invalid
        """
        start_time = time.time()
        self._logger.info(
            f"[CALC-START] Starting calculation with {len(request.mesh.triangles)} triangles"
        )

        try:
            # PRE-FILTER: Remove triangles behind/below window (vectorized)
            coarse_start = time.time()
            coarse_filtered = TriangleFilter.filter_by_height_and_direction(
                request.mesh.triangles,
                request.window.center,
                request.window.normal
            )
            filtered_mesh = Mesh(tuple(coarse_filtered))
            coarse_time = time.time() - coarse_start
            self._logger.info(f"[PRE-FILTER] Completed in {coarse_time*1000:.2f}ms")

            # Use intersection-based calculator with pre-filtered mesh (skips Step 0)
            calculator = IntersectionObstructionCalculator()
            result = calculator._calculate_with_filtered_mesh(
                filtered_mesh,
                request.window.center,
                request.window.normal
            )

            total_time = time.time() - start_time
            self._logger.info(
                f"[TIMING] EFFICIENT horizon obstruction complete: {result.obstruction_angle_degrees:.2f}° "
                f"(total: {total_time*1000:.2f}ms, {result.projected_point_count} intersections)"
            )

            return result

        except Exception as e:
            self._logger.error(f"Efficient obstruction calculation failed: {str(e)}")
            raise

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
        Calculate both horizon and zenith angles using EFFICIENT methods with COMBINED filtering

        This optimized version filters triangles ONCE for both calculations,
        avoiding duplicate array construction and filtering operations.

        Args:
            request: Raytracing request with window and mesh data

        Returns:
            Dictionary with 'horizon' and 'zenith' ObstructionResults
        """
        overall_start = time.time()
        self._logger.info(f"[CALC-START] Starting calculation with {len(request.mesh.triangles)} triangles")

        # PRE-STEP: Quick coarse filter using vectorized method
        coarse_start = time.time()
        coarse_filtered = TriangleFilter.filter_by_height_and_direction(
            request.mesh.triangles,
            request.window.center,
            request.window.normal
        )
        filtered_mesh = Mesh(tuple(coarse_filtered))
        coarse_time = time.time() - coarse_start
        self._logger.info(f"[PRE-FILTER] Completed in {coarse_time*1000:.2f}ms")

        # OPTIMIZATION: Filter triangles ONCE for both calculations
        filter_start = time.time()
        horizon_triangles, zenith_triangles = TriangleFilter.filter_for_both(
            filtered_mesh.triangles,
            request.window.center,
            request.window.normal,
            min_horizontal_distance=1.0
        )
        filter_time = time.time() - filter_start
        self._logger.info(
            f"[COMBINED-FILTER] {len(horizon_triangles)} horizon, "
            f"{len(zenith_triangles)} zenith in {filter_time*1000:.2f}ms"
        )

        # Create filtered mesh objects for each calculator
        horizon_mesh = Mesh(triangles=tuple(horizon_triangles))
        zenith_mesh = Mesh(triangles=tuple(zenith_triangles))

        # Calculate horizon angle with pre-filtered mesh
        horizon_calculator = IntersectionObstructionCalculator()
        horizon_result = horizon_calculator._calculate_with_filtered_mesh(
            horizon_mesh, request.window.center, request.window.normal
        )

        # Calculate zenith angle with pre-filtered mesh
        zenith_calculator = IntersectionZenithCalculator()
        zenith_result = zenith_calculator._calculate_with_filtered_mesh(
            zenith_mesh, request.window.center, request.window.normal
        )

        return {
            ResponseField.HORIZON.value: horizon_result,
            ResponseField.ZENITH.value: zenith_result
        }

    async def calculate_all_directions_async(
        self,
        request: ObstructionRequest,
        num_directions: int = None,
        start_angle_degrees: float = None,
        end_angle_degrees: float = None
    ) -> Dict[str, Any]:
        """
        Calculate obstruction angles for multiple directions in parallel using asyncio

        Uses asyncio to run calculations in parallel without HTTP overhead.
        Much faster than making HTTP requests to itself.
        """
        # Apply defaults
        if num_directions is None:
            num_directions = AllDirectionDefaults.NUM_DIRECTIONS
        if start_angle_degrees is None:
            start_angle_degrees = AllDirectionDefaults.START_ANGLE_DEGREES
        if end_angle_degrees is None:
            end_angle_degrees = AllDirectionDefaults.END_ANGLE_DEGREES

        start_time = time.time()
        self._logger.info(f"[PARALLEL] Starting with {len(request.mesh.triangles)} triangles") 

        # PRE-FILTER ONCE: Remove triangles below AND behind window (using base direction)
        coarse_start = time.time()

        coarse_filtered = TriangleFilter.filter_by_height_and_direction(
            request.mesh.triangles,
            request.window.center,
            request.window.normal
        )

        removed_count = len(request.mesh.triangles) - len(coarse_filtered)
        filtered_mesh = Mesh(tuple(coarse_filtered))

        coarse_time = time.time() - coarse_start
        self._logger.info(
            f"[PARALLEL-PRE-FILTER] Removed {removed_count} triangles below/behind window "
            f"({len(coarse_filtered)} remaining, {coarse_time*1000:.2f}ms)"
        )

        # Get base direction
        normal_arr = request.window.normal.to_array()
        base_direction_angle = math.atan2(normal_arr[1], normal_arr[0])

        # Generate direction angles
        start_angle_rad = math.radians(start_angle_degrees)
        end_angle_rad = math.radians(end_angle_degrees)
        angle_step = (end_angle_rad - start_angle_rad) / (num_directions - 1) if num_directions > 1 else 0

        direction_angles = []
        for i in range(num_directions):
            relative_angle = start_angle_rad + (i * angle_step)
            absolute_angle = base_direction_angle - (math.pi / 2) + relative_angle
            direction_angles.append(absolute_angle)
        self._logger.info("setup dirs")
        # Calculate each direction in parallel (each with parallel horizon/zenith)
        tasks = []
        self._logger.info("start real loops")
        for direction_angle in direction_angles:
            # Create window normal for this direction
            normal = Vector3D.from_horizontal_angle(direction_angle)

            # Create async task for calculation (horizon and zenith run in parallel within)
            task = self._calculate_direction_async(
                filtered_mesh,
                request.window.center,
                normal,
                direction_angle
            )
            self._logger.info("create task for {}".format(direction_angle))
            tasks.append(task)
        self._logger.info("created tasks")
        # Execute all in parallel
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        self._logger.info(f"[PARALLEL] Calculated {num_directions} directions in {total_time:.2f}s")

        return {
            ResponseField.RESULTS.value: results
        }

    async def _calculate_direction_async(self, mesh, center, normal, direction_angle):
        """Asynchronous calculation for a single direction with parallel horizon/zenith"""
        # Filter triangles behind window for THIS specific direction
        # This reduces triangles from ~1200 to ~700
        filtered_triangles = TriangleFilter.filter_by_direction(
            mesh.triangles,
            center,
            normal
        )
        filtered_mesh = Mesh(tuple(filtered_triangles))

        loop = asyncio.get_event_loop()

        # Calculate horizon and zenith in parallel with direction-filtered mesh
        horizon_task = loop.run_in_executor(
            None,
            self._calculate_horizon_sync,
            filtered_mesh, center, normal
        )
        zenith_task = loop.run_in_executor(
            None,
            self._calculate_zenith_sync,
            filtered_mesh, center, normal
        )

        horizon_result, zenith_result = await asyncio.gather(horizon_task, zenith_task)

        return {
            ResponseField.DIRECTION_ANGLE.value: direction_angle,
            ResponseField.HORIZON.value: horizon_result.to_dict(),
            ResponseField.ZENITH.value: zenith_result.to_dict()
        }

    def _calculate_horizon_sync(self, mesh, center, normal):
        """Synchronous horizon calculation (for thread pool)"""
        calculator = IntersectionObstructionCalculator()
        return calculator._calculate_with_filtered_mesh(mesh, center, normal)

    def _calculate_zenith_sync(self, mesh, center, normal):
        """Synchronous zenith calculation (for thread pool)"""
        calculator = IntersectionZenithCalculator()
        return calculator._calculate_with_filtered_mesh(mesh, center, normal)

    def calculate_all_directions(
        self,
        request: ObstructionRequest,
        num_directions: int = None,
        start_angle_degrees: float = None,
        end_angle_degrees: float = None
    ) -> Dict[str, Any]:
        """
        Calculate obstruction angles for multiple directions in a semicircle from window

        The calculation spans a semicircle centered on the window's normal direction.
        By default, samples 64 directions from 17.5° to 162.5° relative to window normal.

        Args:
            request: Raytracing request with window and mesh data
            num_directions: Number of directions to sample (default 64)
            start_angle_degrees: Start angle in degrees relative to window normal (default 17.5°)
            end_angle_degrees: End angle in degrees relative to window normal (default 162.5°)

        Returns:
            Dictionary with list of results for each direction
        """
        from src.components.obstruction_models import Window
        from src.components.geometry import Vector3D

        # Apply defaults
        if num_directions is None:
            num_directions = AllDirectionDefaults.NUM_DIRECTIONS
        if start_angle_degrees is None:
            start_angle_degrees = AllDirectionDefaults.START_ANGLE_DEGREES
        if end_angle_degrees is None:
            end_angle_degrees = AllDirectionDefaults.END_ANGLE_DEGREES

        start_time = time.time()
        self._logger.info(
            f"[TIMING] Starting all-direction obstruction calculation for window at "
            f"({request.window.center.x}, {request.window.center.y}, {request.window.center.z}) "
            f"with {num_directions} directions from {start_angle_degrees}° to {end_angle_degrees}°"
        )

        # Get base direction from request window (convert to horizontal angle)
        # Extract horizontal components and compute angle with atan2
        normal_arr = request.window.normal.to_array()
        base_direction_angle = math.atan2(normal_arr[1], normal_arr[0])

        # Convert start/end angles to radians
        start_angle_rad = math.radians(start_angle_degrees)
        end_angle_rad = math.radians(end_angle_degrees)

        # Calculate angle step
        angle_range = end_angle_rad - start_angle_rad
        angle_step = angle_range / (num_directions - 1) if num_directions > 1 else 0

        # Generate all direction angles (relative to base direction)
        direction_angles = []
        for i in range(num_directions):
            relative_angle = start_angle_rad + (i * angle_step)
            # Convert relative angle to absolute angle
            # Relative angle is measured from the left (-90° from normal)
            # So we need to add it to (base_direction - 90°)
            absolute_angle = base_direction_angle - (math.pi / 2) + relative_angle
            direction_angles.append(absolute_angle)

        self._logger.info(f"[TIMING] Step 1: Setup complete, generated {num_directions} direction angles")

        # Calculate each direction sequentially (client will parallelize by making multiple requests)
        results = []
        for i, direction_angle in enumerate(direction_angles):
            dir_start = time.time()

            # Create window normal for this direction
            normal = Vector3D.from_horizontal_angle(direction_angle)

            # Use prefiltered calculator (skips Step 0 filtering)
            horizon_calculator = IntersectionObstructionCalculator()
            horizon_result = horizon_calculator._calculate_with_filtered_mesh(
                request.mesh, request.window.center, normal
            )

            # Use prefiltered calculator (skips Step 0 filtering)
            zenith_calculator = IntersectionZenithCalculator()
            zenith_result = zenith_calculator._calculate_with_filtered_mesh(
                request.mesh, request.window.center, normal
            )

            result = {
                ResponseField.DIRECTION_ANGLE.value: direction_angle,
                ResponseField.HORIZON.value: horizon_result.to_dict(),
                ResponseField.ZENITH.value: zenith_result.to_dict()
            }
            results.append(result)

            dir_time = time.time() - dir_start
            self._logger.info(
                f"[TIMING] Step 2: Completed direction {i+1}/{num_directions} "
                f"({math.degrees(direction_angle):.1f}°) in {dir_time*1000:.2f}ms"
            )

        total_time = time.time() - start_time
        self._logger.info(
            f"[TIMING] All-direction obstruction COMPLETE: {num_directions} directions in {total_time*1000:.2f}ms"
        )

        return {
            ResponseField.RESULTS.value: results
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

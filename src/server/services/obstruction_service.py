from typing import Dict, Any, List
import time
import math
import asyncio
import logging

logger = logging.getLogger(__name__)

from src.components.calculators.intersection_calculator import IntersectionCalculator
from src.components.models import ObstructionRequest, ObstructionResult, Window

from src.server.base.constants import ANGLES, ResponseField, ResponseStatus, AllDirectionDefaults
from src.components.geometry import Mesh
from src.components.filter import CompositeTriangleFilter, DistanceTriangleFilter, CoarseTriangleFilter


class ObstructionService:
    """
    Service orchestrating obstruction calculation operations

    Follows Single Responsibility Principle:
    - Coordinates projection and obstruction calculations
    - Does not handle HTTP/request parsing
    - Does not perform low-level calculations
    """

    @classmethod
    def calculate_horizon(cls, request: ObstructionRequest) -> ObstructionResult:
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
        
        logger.info(
            f"[CALC-START] Starting calculation with {len(request.mesh.triangles)} triangles"
        )

        try:
            result = IntersectionCalculator.call(
                request.mesh,
                request.window,
                ANGLES.HORIZON)
            
            return result

        except Exception as e:
            logger.error(f"Efficient obstruction calculation failed: {str(e)}")
            raise

    @classmethod
    def calculate_both_angles(cls, request: ObstructionRequest) -> Dict[str, ObstructionResult]:
        """
        Calculate both horizon and zenith angles in a single request

        Args:
            request: Raytracing request with window and mesh data

        Returns:
            Dictionary with 'horizon' and 'zenith' ObstructionResults
        """
        logger.info(
            f"[CALC-BOTH] Starting calculation for both horizon and zenith angles "
            f"with {len(request.mesh.triangles)} triangles"
        )

        # Calculate horizon angle
        horizon_result = cls.calculate_horizon(request)

        # Calculate zenith angle
        zenith_result = cls.calculate_zenith_angle(request)

        return {
            "horizon": horizon_result,
            "zenith": zenith_result
        }

    @classmethod
    def calculate_zenith_angle(cls, request: ObstructionRequest) -> ObstructionResult:
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
        logger.info(
            f"[TIMING] Starting zenith angle calculation for window at "
            f"({request.window.center.x}, {request.window.center.y}, {request.window.center.z})"
        )

        try:
            zenith_triangles = DistanceTriangleFilter.call(
                request.mesh.triangles,
                request.window, angle_type=ANGLES.ZENITH
            )
            zenith_mesh = Mesh(triangles=zenith_triangles)
            result = IntersectionCalculator.call(
            zenith_mesh, request.window, angle_type=ANGLES.ZENITH)
            
            total_time = time.time() - start_time
            logger.info(
                f"[TIMING] Zenith angle complete: {result.obstruction_angle_degrees:.2f}° "
                f"(total: {total_time*1000:.2f}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"Zenith angle calculation failed: {str(e)}")
            raise

    
    @classmethod
    def _absolute_direction(cls, start_angle_rad,base_direction_angle,
                             i, angle_step)->float:
        relative_angle = start_angle_rad + (i * angle_step)
        return base_direction_angle - (math.pi * 0.5) + relative_angle

    @classmethod
    def _get_directions(cls,window:Window,start_angle_degrees,
                             end_angle_degrees, num_directions)->List[float]:
        normal_arr = window.normal.to_array()
        base_direction_angle = math.atan2(normal_arr[1], normal_arr[0])

        # Generate direction angles
        start_angle_rad = math.radians(start_angle_degrees)
        end_angle_rad = math.radians(end_angle_degrees)
        angle_step = (end_angle_rad - start_angle_rad) / (num_directions - 1) if num_directions > 1 else 0

        return [cls._absolute_direction(start_angle_rad, base_direction_angle, i, angle_step) for i in range(num_directions)]
    

    @classmethod
    async def calculate_all_directions_async(
        cls,
        request: ObstructionRequest,
        num_directions: int|None = None,
        start_angle_degrees: float|None = None,
        end_angle_degrees: float|None = None
    ) -> Dict[str, Any]:
        """
        Calculate obstruction angles for multiple directions in parallel using asyncio

        Uses asyncio to run calculations in parallel without HTTP overhead.
        Much faster than making HTTP requests to itcls.
        """
        # Apply defaults
        if num_directions is None:
            num_directions = AllDirectionDefaults.NUM_DIRECTIONS.value
        if start_angle_degrees is None:
            start_angle_degrees = AllDirectionDefaults.START_ANGLE_DEGREES.value
        if end_angle_degrees is None:
            end_angle_degrees = AllDirectionDefaults.END_ANGLE_DEGREES.value

        start_time = time.time()
        logger.info(f"[PARALLEL] Starting with {len(request.mesh.triangles)} triangles") 

        # PRE-FILTER ONCE: Remove triangles below AND behind window (using base direction)
        coarse_start = time.time()

        coarse_filtered = CoarseTriangleFilter.call(
            request.mesh.triangles,
            request.window
        )

        removed_count = len(request.mesh.triangles) - len(coarse_filtered)
        filtered_mesh = Mesh(coarse_filtered)

        coarse_time = time.time() - coarse_start
        logger.info(
            f"[PARALLEL-PRE-FILTER] Removed {removed_count} triangles below/behind window "
            f"({len(coarse_filtered)} remaining, {coarse_time*1000:.2f}ms)"
        )

        
        direction_angles = cls._get_directions(request.window, start_angle_degrees, end_angle_degrees, num_directions)
        # Calculate each direction in parallel (each with parallel horizon/zenith)
        # window_normal = Vector3D.from_horizontal_angle(direction_angle),
        tasks = [cls.calculate_direction_async(
                filtered_mesh,
                request.window,
                direction_angle
            ) for direction_angle in direction_angles]
        
        # Execute all in parallel
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        logger.info(f"[PARALLEL] Calculated {num_directions} directions in {total_time:.2f}s")

        return {
            ResponseField.RESULTS.value: results
        }
    @classmethod
    async def calculate_direction_async(cls, mesh:Mesh, window_orig:Window, direction_angle:float):
        """Asynchronous calculation for a single direction with parallel horizon/zenith"""
        # Filter triangles behind window for THIS specific direction
        # This reduces triangles from ~1200 to ~700
        window = Window.set_angle(window_orig, direction_angle)

        h_filtered, v_filtered = CompositeTriangleFilter.call(
            mesh.triangles,
            window
        )
        
        h_filtered = Mesh(h_filtered)
        v_filtered = Mesh(v_filtered)

        loop = asyncio.get_event_loop()

        # Calculate horizon and zenith in parallel with direction-filtered mesh
        # Note: Wrap classmethod calls in lambdas for executor compatibility
        horizon_task = loop.run_in_executor(
            None,
            lambda: IntersectionCalculator.call(h_filtered, window, ANGLES.HORIZON)
        )
        zenith_task = loop.run_in_executor(
            None,
            lambda: IntersectionCalculator.call(v_filtered, window, ANGLES.ZENITH)
        )

        horizon_result, zenith_result = await asyncio.gather(horizon_task, zenith_task)

        return {
            ResponseField.DIRECTION_ANGLE.value: direction_angle,
            ResponseField.HORIZON.value: horizon_result.to_dict(),
            ResponseField.ZENITH.value: zenith_result.to_dict()
        }
    
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get service status"""
        return {
            ResponseField.STATUS.value: ResponseStatus.SUCCESS.value,
            "projection_calculator": ResponseStatus.SUCCESS.value,
            "horizon_calculator": ResponseStatus.SUCCESS.value,
            "zenith_calculator": ResponseStatus.SUCCESS.value
        }


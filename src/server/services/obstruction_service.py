from typing import Dict, Any, List, Optional
import time
import math
import asyncio
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger(__name__)

from src.components.calculators.intersection_calculator import IntersectionCalculator
from src.components.models import ObstructionRequest, ObstructionResult, Window

from src.server.base.constants import ANGLES, ResponseField, ResponseStatus, AllDirectionDefaults
from src.components.geometry import Mesh
from src.components.filter import CompositeTriangleFilter, CoarseTriangleFilter, DistanceTriangleFilter, HeightTriangleFilter


# Top-level functions for ProcessPoolExecutor (must be picklable)
def _calculate_horizon_worker(mesh: Mesh, window: Window) -> ObstructionResult:
    """Worker function for horizon calculation (picklable)"""
    return IntersectionCalculator.call(mesh, window, ANGLES.HORIZON)


def _calculate_zenith_worker(mesh: Mesh, window: Window) -> ObstructionResult:
    """Worker function for zenith calculation (picklable)"""
    return IntersectionCalculator.call(mesh, window, ANGLES.ZENITH)


class ObstructionService:
    """
    Service orchestrating obstruction calculation operations

    Follows Single Responsibility Principle:
    - Coordinates projection and obstruction calculations
    - Does not handle HTTP/request parsing
    - Does not perform low-level calculations
    """

    # Shared ProcessPoolExecutor for all parallel calculations (Singleton Pattern)
    _process_pool: Optional[ProcessPoolExecutor] = None
    _max_workers: Optional[int] = None

    @classmethod
    def _get_process_pool(cls) -> ProcessPoolExecutor:
        """Get or create shared ProcessPoolExecutor instance (Singleton Pattern)"""
        if cls._process_pool is None:
            cpu_count = multiprocessing.cpu_count()
            cls._max_workers = max(2, cpu_count - 1)
            cls._process_pool = ProcessPoolExecutor(max_workers=cls._max_workers)
            logger.debug(f"[PARALLEL-INIT] Created ProcessPoolExecutor with {cls._max_workers} workers (CPU count: {cpu_count})")
        return cls._process_pool

    @classmethod
    def calculate_horizon(cls, request: ObstructionRequest) -> ObstructionResult:
        """Calculate horizon obstruction angle using horizon_mesh."""
        if request.horizon_mesh is None:
            return ObstructionResult.no_obstruction()

        logger.debug(
            f"[CALC-START] Horizon calculation with {len(request.horizon_mesh.triangles)} triangles"
        )
        return IntersectionCalculator.call(
            request.horizon_mesh, request.window, ANGLES.HORIZON
        )

    @classmethod
    def calculate_both_angles(cls, request: ObstructionRequest) -> Dict[str, ObstructionResult]:
        """Calculate both horizon and zenith angles in a single request."""
        return {
            "horizon": cls.calculate_horizon(request),
            "zenith": cls.calculate_zenith_angle(request),
        }

    @classmethod
    def calculate_zenith_angle(cls, request: ObstructionRequest) -> ObstructionResult:
        """Calculate zenith obstruction angle using zenith_mesh."""
        if request.zenith_mesh is None:
            return ObstructionResult.no_obstruction()

        logger.debug(
            f"[CALC-START] Zenith calculation with {len(request.zenith_mesh.triangles)} triangles"
        )
        return IntersectionCalculator.call(
            request.zenith_mesh, request.window, angle_type=ANGLES.ZENITH
        )

    @classmethod
    def _absolute_direction(cls, start_angle_rad, base_direction_angle,
                            i, angle_step) -> float:
        relative_angle = start_angle_rad + (i * angle_step)
        return base_direction_angle - (math.pi * 0.5) + relative_angle

    @classmethod
    def _get_directions(cls, window: Window, start_angle_degrees,
                        end_angle_degrees, num_directions) -> List[float]:
        normal_arr = window.normal.to_array()
        base_direction_angle = math.atan2(normal_arr[1], normal_arr[0])

        start_angle_rad = math.radians(start_angle_degrees)
        end_angle_rad = math.radians(end_angle_degrees)
        angle_step = (end_angle_rad - start_angle_rad) / (num_directions - 1) if num_directions > 1 else 0

        return [cls._absolute_direction(start_angle_rad, base_direction_angle, i, angle_step) for i in range(num_directions)]

    @classmethod
    async def calculate_all_directions_async(
        cls,
        request: ObstructionRequest,
        num_directions: int | None = None,
        start_angle_degrees: float | None = None,
        end_angle_degrees: float | None = None
    ) -> Dict[str, Any]:
        """Calculate obstruction angles for multiple directions in parallel."""
        if num_directions is None:
            num_directions = AllDirectionDefaults.NUM_DIRECTIONS.value
        if start_angle_degrees is None:
            start_angle_degrees = AllDirectionDefaults.START_ANGLE_DEGREES.value
        if end_angle_degrees is None:
            end_angle_degrees = AllDirectionDefaults.END_ANGLE_DEGREES.value

        start_time = time.time()

        # Determine if we have split meshes (new format) or single mesh (legacy)
        is_split = request.horizon_mesh is not request.zenith_mesh

        # Pre-filter each mesh once (coarse filter: remove triangles below/behind window)
        h_filtered_mesh = cls._coarse_filter_mesh(request.horizon_mesh, request.window, "horizon")
        z_filtered_mesh = cls._coarse_filter_mesh(request.zenith_mesh, request.window, "zenith")

        direction_angles = cls._get_directions(
            request.window, start_angle_degrees, end_angle_degrees, num_directions
        )

        tasks = [
            cls._calculate_direction_async(
                h_filtered_mesh, z_filtered_mesh, request.window,
                direction_angle, is_split
            )
            for direction_angle in direction_angles
        ]

        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        logger.info(f"[PARALLEL] Calculated {num_directions} directions in {total_time:.2f}s")

        return {
            ResponseField.RESULTS.value: results,
        }

    @classmethod
    def _height_filter_mesh(cls, mesh: Optional[Mesh], window: Window, label: str) -> Optional[Mesh]:
        """Apply height-only pre-filter (remove triangles below window, keep all directions)."""
        if mesh is None:
            return None
        filtered = HeightTriangleFilter.call(mesh.triangles, window, ANGLES.HORIZON)
        removed = len(mesh.triangles) - len(filtered)
        logger.debug(
            f"[PRE-FILTER-HEIGHT] {label}: removed {removed} triangles "
            f"({len(filtered)} remaining)"
        )
        return Mesh(filtered)

    @classmethod
    def _coarse_filter_mesh(cls, mesh: Optional[Mesh], window: Window, label: str) -> Optional[Mesh]:
        """Apply coarse triangle filter to a mesh (remove triangles below/behind window)."""
        if mesh is None:
            return None
        coarse_filtered = CoarseTriangleFilter.call(mesh.triangles, window)
        removed = len(mesh.triangles) - len(coarse_filtered)
        logger.debug(
            f"[PRE-FILTER] {label}: removed {removed} triangles "
            f"({len(coarse_filtered)} remaining)"
        )
        return Mesh(coarse_filtered)

    @classmethod
    async def _calculate_direction_async(
        cls,
        horizon_mesh: Optional[Mesh],
        zenith_mesh: Optional[Mesh],
        window_orig: Window,
        direction_angle: float,
        is_split: bool,
    ):
        """Calculate horizon and zenith for a single direction in parallel."""
        window = Window.set_angle(window_orig, direction_angle)

        if is_split:
            # Split format: meshes are already separated by type.
            # Apply per-direction distance filter but skip surface orientation filter.
            h_mesh = cls._direction_filter(horizon_mesh, window, ANGLES.HORIZON)
            z_mesh = cls._direction_filter(zenith_mesh, window, ANGLES.ZENITH)
        else:
            # Legacy format: single mesh, use CompositeTriangleFilter to classify surfaces.
            if horizon_mesh is not None:
                h_filtered, v_filtered = CompositeTriangleFilter.call(
                    horizon_mesh.triangles, window
                )
                h_mesh = Mesh(h_filtered)
                z_mesh = Mesh(v_filtered)
            else:
                h_mesh = Mesh(())
                z_mesh = Mesh(())

        loop = asyncio.get_event_loop()
        executor = cls._get_process_pool()

        horizon_task = loop.run_in_executor(
            executor, _calculate_horizon_worker, h_mesh, window
        )
        zenith_task = loop.run_in_executor(
            executor, _calculate_zenith_worker, z_mesh, window
        )

        horizon_result, zenith_result = await asyncio.gather(horizon_task, zenith_task)

        return {
            ResponseField.DIRECTION_ANGLE.value: direction_angle,
            ResponseField.HORIZON.value: horizon_result.to_dict(),
            ResponseField.ZENITH.value: zenith_result.to_dict(),
        }

    @staticmethod
    def _direction_filter(mesh: Optional[Mesh], window: Window, angle_type: ANGLES) -> Mesh:
        """Apply height-only filtering for split meshes (no distance heuristics needed)."""
        if mesh is None or not mesh.triangles:
            return Mesh(())
        filtered = HeightTriangleFilter.call(mesh.triangles, window, angle_type)
        return Mesh(filtered)

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get service status"""
        return {
            ResponseField.STATUS.value: ResponseStatus.SUCCESS.value,
            "projection_calculator": ResponseStatus.SUCCESS.value,
            "horizon_calculator": ResponseStatus.SUCCESS.value,
            "zenith_calculator": ResponseStatus.SUCCESS.value,
        }

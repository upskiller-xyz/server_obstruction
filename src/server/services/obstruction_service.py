from typing import Dict, Any, List, Optional
import time
import math
import asyncio
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger(__name__)

from src.components.calculators.intersection_calculator import IntersectionCalculator
from src.components.calculators.gap_obstruction_calculator import GapObstructionCalculator, GapObstructionResult
from src.components.models import ObstructionRequest, ObstructionResult, Window

from src.server.base.constants import ANGLES, ResponseField, ResponseStatus, AllDirectionDefaults
from src.components.geometry import Mesh
from src.components.filter import CompositeTriangleFilter, CoarseTriangleFilter, DistanceTriangleFilter, HeightTriangleFilter


# Top-level worker function for ProcessPoolExecutor (must be picklable)
def _calculate_gap_worker(mesh: Mesh, window: Window, direction_angle: float) -> GapObstructionResult:
    """Worker function for gap-based obstruction calculation (picklable)"""
    return GapObstructionCalculator.calculate(mesh, window, direction_angle)


# Legacy workers kept for backward compatibility with single-direction endpoints
def _calculate_horizon_worker(mesh: Mesh, window: Window) -> ObstructionResult:
    """Worker function for horizon calculation (picklable)"""
    return IntersectionCalculator.call(mesh, window, ANGLES.HORIZON)


def _calculate_zenith_worker(mesh: Mesh, window: Window) -> ObstructionResult:
    """Worker function for zenith calculation (picklable)"""
    return IntersectionCalculator.call(mesh, window, ANGLES.ZENITH)


class ObstructionService:
    """
    Service orchestrating obstruction calculation operations

    Uses gap-based unified calculation for multi-direction requests.
    Keeps legacy horizon/zenith split for single-direction endpoints.
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
        """Calculate obstruction angles for multiple directions using gap-based approach."""
        if num_directions is None:
            num_directions = AllDirectionDefaults.NUM_DIRECTIONS.value
        if start_angle_degrees is None:
            start_angle_degrees = AllDirectionDefaults.START_ANGLE_DEGREES.value
        if end_angle_degrees is None:
            end_angle_degrees = AllDirectionDefaults.END_ANGLE_DEGREES.value

        start_time = time.time()

        # Combine all meshes into one (no horizon/zenith split needed)
        combined_mesh = cls._combine_and_filter_meshes(
            request.horizon_mesh, request.zenith_mesh, request.window
        )

        direction_angles = cls._get_directions(
            request.window, start_angle_degrees, end_angle_degrees, num_directions
        )

        tasks = [
            cls._calculate_direction_async(
                combined_mesh, request.window, direction_angle
            )
            for direction_angle in direction_angles
        ]

        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        total_rays = sum(r.get('rays_cast', 0) for r in results)
        logger.info(
            f"[GAP-PARALLEL] Calculated {num_directions} directions in {total_time:.2f}s "
            f"(total rays: {total_rays})"
        )

        return {
            ResponseField.RESULTS.value: results,
        }

    @classmethod
    def _combine_and_filter_meshes(
        cls,
        horizon_mesh: Optional[Mesh],
        zenith_mesh: Optional[Mesh],
        window: Window
    ) -> Mesh:
        """
        Combine horizon and zenith meshes into one and apply coarse pre-filter.

        Args:
            horizon_mesh: Horizon mesh (walls/buildings) or None
            zenith_mesh: Zenith mesh (roofs/slabs) or None
            window: Window for filtering

        Returns:
            Single combined and pre-filtered Mesh
        """
        h_tris = horizon_mesh.triangles if horizon_mesh and horizon_mesh.triangles else ()
        z_tris = zenith_mesh.triangles if zenith_mesh and zenith_mesh.triangles else ()

        # If they're the same object (legacy format), just use one
        if horizon_mesh is zenith_mesh:
            all_triangles = h_tris
        else:
            all_triangles = h_tris + z_tris

        if not all_triangles:
            return Mesh(())

        # Apply coarse pre-filter (remove triangles below/behind window)
        filtered = CoarseTriangleFilter.call(all_triangles, window)
        removed = len(all_triangles) - len(filtered)
        logger.debug(
            f"[PRE-FILTER] Combined mesh: {len(all_triangles)} -> {len(filtered)} "
            f"triangles (removed {removed})"
        )
        return Mesh(filtered)

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
        combined_mesh: Mesh,
        window_orig: Window,
        direction_angle: float,
    ):
        """Calculate obstruction for a single direction using gap-based approach."""
        window = Window.set_angle(window_orig, direction_angle)

        # Per-direction height filter on the combined mesh
        filtered_mesh = cls._direction_filter_combined(combined_mesh, window)

        loop = asyncio.get_event_loop()
        executor = cls._get_process_pool()

        gap_result: GapObstructionResult = await loop.run_in_executor(
            executor, _calculate_gap_worker, filtered_mesh, window, direction_angle
        )

        # Build backward-compatible response with horizon/zenith
        horizon_result, zenith_result = ObstructionResult.from_gap(
            horizon_deg=gap_result.horizon_deg,
            zenith_deg=gap_result.zenith_deg,
            gap_midpoint_deg=gap_result.gap_midpoint_deg,
            gap_amplitude_deg=gap_result.gap_amplitude_deg
        )

        return {
            ResponseField.DIRECTION_ANGLE.value: direction_angle,
            ResponseField.HORIZON.value: horizon_result.to_dict(),
            ResponseField.ZENITH.value: zenith_result.to_dict(),
            'gap_midpoint': gap_result.gap_midpoint_deg,
            'gap_amplitude': gap_result.gap_amplitude_deg,
            'rays_cast': gap_result.rays_cast,
        }

    @staticmethod
    def _direction_filter_combined(mesh: Mesh, window: Window) -> Mesh:
        """Apply height-only filtering for the combined mesh per direction."""
        if not mesh.triangles:
            return Mesh(())
        filtered = HeightTriangleFilter.call(mesh.triangles, window, ANGLES.HORIZON)
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

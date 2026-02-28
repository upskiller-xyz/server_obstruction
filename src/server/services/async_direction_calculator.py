"""Async direction calculator for parallel obstruction calculations"""

import asyncio
from typing import Any, Dict

from src.components.calculators.gap_obstruction_calculator import GapObstructionCalculator
from src.components.geometry import Mesh
from src.components.models import GapObstructionResult, ObstructionResult, Window
from src.server.base.constants import ResponseField
from src.server.services.mesh_filter_service import MeshFilterService
from src.server.services.process_pool_manager import ProcessPoolManager


class AsyncDirectionCalculator:
    """
    Calculates obstruction for single direction using async execution

    Single Responsibility:
    - Only handles async execution for single direction
    - Delegates to GapObstructionCalculator for actual calculation
    """

    @staticmethod
    async def calculate(
        combined_mesh: Mesh,
        window_orig: Window,
        direction_angle: float,
        pool_manager: ProcessPoolManager
    ) -> Dict[str, Any]:
        """
        Calculate obstruction for a single direction using gap-based approach

        Args:
            combined_mesh: Combined and pre-filtered mesh
            window_orig: Original window
            direction_angle: Direction angle in radians
            pool_manager: Process pool manager for parallel execution

        Returns:
            Dictionary with horizon and zenith results
        """
        # Create window rotated to this direction
        window = Window.set_angle(window_orig, direction_angle)

        # Per-direction height filter
        filtered_mesh = MeshFilterService.apply_height_filter(combined_mesh, window)

        # Execute gap calculation in process pool
        loop = asyncio.get_event_loop()
        executor = pool_manager.get_pool()

        gap_result: GapObstructionResult = await loop.run_in_executor(
            executor,
            GapObstructionCalculator.calculate,
            filtered_mesh,
            window,
            direction_angle
        )

        # Build backward-compatible response with horizon/zenith
        horizon_result, zenith_result = ObstructionResult.from_gap(
            horizon_deg=gap_result.horizon_deg,
            zenith_deg=gap_result.zenith_deg,
        )

        return {
            ResponseField.DIRECTION_ANGLE.value: direction_angle,
            ResponseField.HORIZON.value: horizon_result.to_dict(),
            ResponseField.ZENITH.value: zenith_result.to_dict(),
        }

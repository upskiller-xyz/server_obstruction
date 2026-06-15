"""Async direction calculator for parallel obstruction calculations"""

import asyncio
from functools import partial
from typing import Any, Dict

from src.components.calculators.gap_obstruction_calculator import (
    GapObstructionCalculator,
)
from src.components.calculators.ray_triangle_intersector import TriangleArrays
from src.components.models import GapObstructionResult, ObstructionResult, Window
from src.server.base.constants import ResponseField
from src.server.services.thread_pool_manager import ThreadPoolManager


class AsyncDirectionCalculator:
    """
    Calculates obstruction for single direction using async execution

    Single Responsibility:
    - Only handles async execution for single direction
    - Delegates to GapObstructionCalculator for actual calculation
    """

    @staticmethod
    async def calculate(
        tri_arrays: TriangleArrays,
        window_orig: Window,
        direction_angle: float,
        pool_manager: ThreadPoolManager
    ) -> Dict[str, Any]:
        """
        Calculate obstruction for a single direction using gap-based approach

        Args:
            tri_arrays: Pre-packed triangle arrays of the combined/filtered mesh,
                shared (read-only) across all directions — packed once by the caller
                instead of per direction (the mesh is identical for every direction)
            window_orig: Original window
            direction_angle: Direction angle in radians
            pool_manager: Thread pool manager for parallel execution

        Returns:
            Dictionary with horizon and zenith results
        """
        # Create window rotated to this direction
        window = Window.set_angle(window_orig, direction_angle)

        # Execute gap calculation in the thread pool, reusing the shared tri_arrays.
        # get_running_loop() is the supported accessor from inside a coroutine.
        loop = asyncio.get_running_loop()
        executor = pool_manager.get_pool()

        gap_result: GapObstructionResult = await loop.run_in_executor(
            executor,
            partial(
                GapObstructionCalculator.calculate_from_arrays,
                tri_arrays, window, direction_angle
            )
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

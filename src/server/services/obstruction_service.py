"""Obstruction service for coordinating obstruction calculations"""

import asyncio
import logging
import math
from typing import Any, Dict

from src.components.calculators.direction_calculator import DirectionCalculator
from src.components.calculators.intersection_calculator import IntersectionCalculator
from src.components.geometry.mesh import Mesh
from src.components.models import ObstructionRequest, ObstructionResult
from src.server.base.constants import ANGLES, AllDirectionDefaults, ResponseField, ResponseStatus
from src.server.services.async_direction_calculator import AsyncDirectionCalculator
from src.server.services.mesh_filter_service import MeshFilterService
from src.server.services.thread_pool_manager import ThreadPoolManager


class ObstructionService:
    """
    Service orchestrating obstruction calculation operations

    Single Responsibility:
    - Orchestrates calculations
    - Delegates filtering to MeshFilterService
    - Delegates async execution to AsyncDirectionCalculator
    - Delegates direction calculation to DirectionCalculator
    - Delegates thread pool management to ThreadPoolManager

    Uses gap-based unified calculation for multi-direction requests.
    Keeps legacy horizon/zenith split for single-direction endpoints.
    """

    def __init__(self):
        """Initialize with thread pool manager"""
        self._pool_manager = ThreadPoolManager()

    @classmethod
    def calculate_horizon(cls, request: ObstructionRequest) -> ObstructionResult:
        """
        Calculate horizon obstruction angle using mesh

        Args:
            request: Obstruction request with mesh

        Returns:
            ObstructionResult with horizon angle
        """
        if request.mesh is None:
            return ObstructionResult.no_obstruction()

        logging.debug(
            f"[CALC-START] Horizon calculation with "
            f"{len(request.mesh.triangles)} triangles"
        )
        return IntersectionCalculator.call(
            request.mesh, request.window, ANGLES.HORIZON
        )

    @classmethod
    def calculate_zenith_angle(cls, request: ObstructionRequest) -> ObstructionResult:
        """
        Calculate zenith obstruction angle using mesh

        Args:
            request: Obstruction request with mesh

        Returns:
            ObstructionResult with zenith angle
        """
        if request.mesh is None:
            return ObstructionResult.no_obstruction()

        logging.debug(
            f"[CALC-START] Zenith calculation with "
            f"{len(request.mesh.triangles)} triangles"
        )
        return IntersectionCalculator.call(
            request.mesh, request.window, angle_type=ANGLES.ZENITH
        )

    @classmethod
    def calculate_both_angles(
        cls,
        request: ObstructionRequest
    ) -> Dict[str, ObstructionResult]:
        """
        Calculate both horizon and zenith angles in a single request

        Args:
            request: Obstruction request with both meshes

        Returns:
            Dictionary with horizon and zenith results
        """
        return {
            ResponseField.HORIZON.value: cls.calculate_horizon(request),
            ResponseField.ZENITH.value: cls.calculate_zenith_angle(request),
        }

    async def calculate_all_directions_async(
        self,
        request: ObstructionRequest,
        num_directions: int | None = None,
        start_angle_degrees: float | None = None,
        end_angle_degrees: float | None = None
    ) -> Dict[str, Any]:
        """
        Calculate obstruction angles for multiple directions using gap-based approach

        Args:
            request: Obstruction request
            num_directions: Number of directions (default 64)
            start_angle_degrees: Start angle (default 17.5)
            end_angle_degrees: End angle (default 162.5)

        Returns:
            Dictionary with results for all directions
        """
        # Apply defaults using Enumerator Pattern
        if num_directions is None:
            num_directions = AllDirectionDefaults.NUM_DIRECTIONS.value
        if start_angle_degrees is None:
            start_angle_degrees = AllDirectionDefaults.START_ANGLE_DEGREES.value
        if end_angle_degrees is None:
            end_angle_degrees = AllDirectionDefaults.END_ANGLE_DEGREES.value

        # Delegate mesh combining and filtering to MeshFilterService
        mesh = MeshFilterService.apply_coarse_filter(request.mesh, request.window)
        mesh = MeshFilterService.apply_height_filter(mesh, request.window)

        # Delegate direction calculation to DirectionCalculator
        normal_arr = request.window.normal.to_array()
        base_direction_angle = math.atan2(normal_arr[1], normal_arr[0])

        direction_angles = DirectionCalculator.calculate_direction_angles(
            base_direction_angle,
            num_directions,
            start_angle_degrees,
            end_angle_degrees
        )

        # Create async tasks for all directions
        tasks = [
            AsyncDirectionCalculator.calculate(
                mesh,
                request.window,
                float(direction_angle),
                self._pool_manager
            )
            for direction_angle in direction_angles
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)

        return {
            ResponseField.RESULTS.value: results,
        }

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """
        Get service status

        Returns:
            Dictionary with status
        """
        return {
            ResponseField.STATUS.value: ResponseStatus.SUCCESS.value
        }

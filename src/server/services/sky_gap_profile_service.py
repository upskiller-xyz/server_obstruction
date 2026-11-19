"""Sky gap profile service: obstruction profile of every window of a room"""

import asyncio
from typing import List

from src.components.solar import SkyGapProfile, SolarRequest, SolarWindow
from src.components.solar.constants import SkyProfileDefaults
from src.server.base.constants import ResponseField
from src.server.services.mesh_filter_service import MeshFilterService
from src.server.services.obstruction_service import ObstructionService


class SkyGapProfileService:
    """
    Builds the sky gap profile of each window using the multi-direction
    obstruction calculation.

    Single Responsibility:
    - Only runs the obstruction calculation and wraps it as SkyGapProfile
    - Does NOT perform any solar calculation
    """

    @classmethod
    def profiles(cls, request: SolarRequest) -> List[SkyGapProfile]:
        """
        Sky gap profile per window, in request order.

        Args:
            request: Solar request with windows and optional mesh

        Returns:
            One SkyGapProfile per window (unobstructed when there is no mesh)
        """
        if not request.has_obstruction_data:
            return [SkyGapProfile.unobstructed() for _ in request.windows]

        return asyncio.run(cls._profiles_async(request))

    @classmethod
    async def _profiles_async(cls, request: SolarRequest) -> List[SkyGapProfile]:
        """Run the obstruction calculation of all windows concurrently"""
        service = ObstructionService()
        return list(await asyncio.gather(*[
            cls._window_profile(service, request, window) for window in request.windows
        ]))

    @classmethod
    def _has_no_relevant_geometry(cls, request: SolarRequest, window: SolarWindow) -> bool:
        """
        Whether no triangle is above and in front of the window.

        The gap calculation reports an empty mesh as fully obstructed,
        so the open-sky case has to be detected before running it.
        """
        mesh = MeshFilterService.apply_coarse_filter(request.mesh, window.window)
        mesh = MeshFilterService.apply_height_filter(mesh, window.window)
        return not mesh.triangles

    @classmethod
    async def _window_profile(
        cls,
        service: ObstructionService,
        request: SolarRequest,
        window: SolarWindow
    ) -> SkyGapProfile:
        """Calculate the sky gap profile of one window"""
        if cls._has_no_relevant_geometry(request, window):
            return SkyGapProfile.unobstructed()

        result = await service.calculate_all_directions_async(
            window.to_obstruction_request(request.mesh),
            SkyProfileDefaults.NUM_DIRECTIONS.value,
            SkyProfileDefaults.START_ANGLE_DEGREES.value,
            SkyProfileDefaults.END_ANGLE_DEGREES.value,
        )
        return SkyGapProfile.from_direction_results(
            result[ResponseField.RESULTS.value], window.direction_rad
        )

"""Solar service coordinating the SVL and sunlight hours calculations"""

import logging
from typing import Any, Dict

from src.components.solar import (
    SolarRequest,
    SunlightHoursCalculator,
    SunlightHoursResult,
    SvlCalculator,
    SvlResult,
)
from src.server.services.sky_gap_profile_service import SkyGapProfileService


class SolarService:
    """
    Service orchestrating the per-room solar analyses

    Single Responsibility:
    - Parses the request and orchestrates the calculation
    - Delegates obstruction masking to SkyGapProfileService
    - Delegates the physics to SvlCalculator / SunlightHoursCalculator
    """

    @classmethod
    def calculate_svl(cls, request_data: Dict[str, Any]) -> SvlResult:
        """
        Calculate the peak solar heat gain (SVL) of a room.

        Without a mesh in the request the sky is unobstructed.

        Args:
            request_data: Validated request dictionary

        Returns:
            SvlResult
        """
        request = SolarRequest.from_dict(request_data)
        if not request.has_obstruction_data:
            logging.info("[SVL] No mesh in request, unobstructed sky")
            return SvlCalculator.calculate(request, None)

        return SvlCalculator.calculate(request, SkyGapProfileService.profiles(request))

    @classmethod
    def calculate_sunlight_hours(cls, request_data: Dict[str, Any]) -> SunlightHoursResult:
        """
        Calculate the EN 17037 sunlight hours of a room.

        Args:
            request_data: Validated request dictionary

        Returns:
            SunlightHoursResult
        """
        request = SolarRequest.from_dict(request_data)
        return SunlightHoursCalculator.calculate(request, SkyGapProfileService.profiles(request))

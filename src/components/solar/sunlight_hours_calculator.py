"""
Sunlight hours calculator (EN 17037 exposure to sunlight)

Counts the time on the reference day (21 March) during which the sun
reaches a room through at least one of its windows:
  - solar altitude above γs,min
  - window faces within 120° of south
  - sun outside the ineffective angle ξ of the façade
  - sun not hidden by surrounding geometry
"""

from typing import Sequence

import numpy as np

from src.components.solar.constants import (
    SUNLIGHT_LEVEL_LIMITS,
    SunlightHoursDefaults,
    SunlightLevel,
)
from src.components.solar.sky_gap_profile import SkyGapProfile
from src.components.solar.solar_position import SolarPositionCalculator, SolarPositions
from src.components.solar.solar_request import SolarRequest, SolarWindow
from src.components.solar.solar_result import SunlightHoursResult, WindowSunlightHours

MINUTES_PER_HOUR = 60.0
HOURS_PER_DAY = 24.0


class SunlightHoursCalculator:
    """Calculates the sunlight hours of a room on the reference day"""

    @classmethod
    def calculate(
        cls,
        request: SolarRequest,
        profiles: Sequence[SkyGapProfile]
    ) -> SunlightHoursResult:
        """
        Calculate the room sunlight hours.

        Args:
            request: Room windows and site settings
            profiles: Sky gap profile per window

        Returns:
            SunlightHoursResult with room hours, level and window breakdown
        """
        step_hours = SunlightHoursDefaults.TIMESTEP_MINUTES.value / MINUTES_PER_HOUR
        positions = cls._reference_day_positions(request.latitude_deg, step_hours)

        masks = [
            cls._sunlit_mask(request, window, profile, positions)
            for window, profile in zip(request.windows, profiles)
        ]
        windows = tuple(
            WindowSunlightHours(
                window_index=index,
                identifier=window.identifier,
                sunlight_hours=float(mask.sum() * step_hours),
                excluded_by_orientation=cls._is_excluded(request, window),
            )
            for index, (window, mask) in enumerate(zip(request.windows, masks))
        )

        room_hours = float(np.any(masks, axis=0).sum() * step_hours)
        return SunlightHoursResult(
            sunlight_hours=room_hours,
            level=cls.level(room_hours),
            min_sun_altitude_deg=request.min_sun_altitude_deg,
            windows=windows,
        )

    @classmethod
    def level(cls, sunlight_hours: float) -> SunlightLevel:
        """EN 17037 performance level for a number of sunlight hours"""
        return next(
            (level for level, limit in SUNLIGHT_LEVEL_LIMITS if sunlight_hours >= limit),
            SunlightLevel.NOT_MET,
        )

    @classmethod
    def _reference_day_positions(cls, latitude_deg: float, step_hours: float) -> SolarPositions:
        """Solar positions at the midpoint of every timestep of the reference day"""
        hours = np.arange(step_hours / 2.0, HOURS_PER_DAY, step_hours)
        days = np.full(hours.shape, SunlightHoursDefaults.REFERENCE_DAY_OF_YEAR.value)
        return SolarPositionCalculator.calculate(latitude_deg, days, hours)

    @classmethod
    def _is_excluded(cls, request: SolarRequest, window: SolarWindow) -> bool:
        """Whether the window faces too far from south to be considered"""
        bearing = window.bearing_deg(request.model_y_bearing_deg)
        deviation = abs(
            (bearing - SunlightHoursDefaults.SOUTH_BEARING_DEGREES.value + 180.0) % 360.0 - 180.0
        )
        return deviation > SunlightHoursDefaults.MAX_SOUTH_DEVIATION_DEGREES.value

    @classmethod
    def _sunlit_mask(
        cls,
        request: SolarRequest,
        window: SolarWindow,
        profile: SkyGapProfile,
        positions: SolarPositions
    ) -> np.ndarray:
        """Boolean mask of the timesteps in which the window receives sunlight"""
        if cls._is_excluded(request, window):
            return np.zeros(positions.altitude_deg.shape, dtype=bool)

        sun_angle = positions.model_angle_rad(request.model_y_bearing_deg)
        relative = np.arctan2(
            np.sin(sun_angle - window.direction_rad),
            np.cos(sun_angle - window.direction_rad)
        )
        effective_half_angle = np.radians(
            90.0 - SunlightHoursDefaults.INEFFECTIVE_ANGLE_DEGREES.value
        )

        return (
            (positions.altitude_deg > request.min_sun_altitude_deg)
            & (np.abs(relative) < effective_half_angle)
            & profile.is_visible(sun_angle, positions.altitude_deg, window.direction_rad)
        )

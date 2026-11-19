"""
Peak solar heat gain (solvärmelast, SVL) calculator

Miljöbyggnad 3.2 Indikator 2. Physics-based: clear-sky irradiance on every
window for every hour of a cloudless year, with the direct beam removed
when the sun is hidden by surrounding geometry. The sky is that of the
climate station of the request, or a generic one when none is given.

    SVL_room = max over hours( Σ_windows g_syst * I_on_surface * A_window ) / A_room

Irradiance on a window (ASHRAE Fundamentals, chapter 14) is the sum of the
direct beam, the sky diffuse (brighter around the sun: Y factor) and the
sunlight reflected by the ground. Surrounding geometry removes the direct
beam when it hides the sun, and scales the sky diffuse and the
ground-reflected light by the sky view fraction of the window. Windows
facing north (outside 90°-270°) are not assessed and add nothing.

Without obstruction data the sky is unobstructed. The simplified value of
the manual (fixed 800 / 560 W/m², see svl_simplified) is returned next to
the calculated one as a reference.
"""

from typing import Optional, Sequence

import numpy as np

from src.components.solar.clear_sky import ClearSkyModel, ClearSkyModelProvider
from src.components.solar.constants import (
    BuildingType,
    SvlDefaults,
    SvlMethod,
    SvlRating,
    SvlRatingLimitsMap,
)
from src.components.solar.sky_gap_profile import SkyGapProfile
from src.components.solar.solar_position import SolarPositionCalculator, SolarPositions
from src.components.solar.solar_request import SolarRequest, SolarWindow
from src.components.solar.solar_result import SvlPeakTime, SvlResult, SvlWindowContribution
from src.components.solar.svl_orientation import SvlOrientation
from src.components.solar.svl_simplified import SimplifiedSvl
from src.components.solar.year_calendar import YearCalendar


class SvlCalculator:
    """Calculates the peak solar heat gain of a room"""

    # ASHRAE ratio of sky diffuse on a vertical surface to diffuse horizontal:
    # Y = max(minimum, c0 + c1 * cos(incidence) + c2 * cos²(incidence))
    _Y_COEFFICIENTS: tuple[float, float, float] = (0.55, 0.437, 0.313)
    _Y_MINIMUM: float = 0.45

    @classmethod
    def calculate(
        cls,
        request: SolarRequest,
        profiles: Optional[Sequence[SkyGapProfile]]
    ) -> SvlResult:
        """
        Calculate the room SVL.

        Args:
            request: Room, windows and site settings (room_area required)
            profiles: Sky gap profile per window, or None when no
                obstruction data is available (unobstructed sky)

        Returns:
            SvlResult with peak value, peak time, rating and window breakdown
        """
        method = SvlMethod.CLEAR_SKY_OBSTRUCTION
        if profiles is None:
            method = SvlMethod.CLEAR_SKY
            profiles = [SkyGapProfile.unobstructed()] * len(request.windows)

        positions = cls._summer_positions(request.latitude_deg)
        sky = ClearSkyModelProvider.for_station(request.climate_station)

        per_window = [
            cls._window_irradiance(request, window, profile, positions, sky)
            for window, profile in zip(request.windows, profiles)
        ]
        excluded = [SvlOrientation.is_excluded(request, w) for w in request.windows]
        irradiance = np.array([
            np.zeros_like(values) if skip else values
            for (values, _), skip in zip(per_window, excluded)
        ])
        gains = irradiance * np.array([[w.g_syst * w.area] for w in request.windows])
        peak = int(np.argmax(gains.sum(axis=0)))

        contributions = tuple(
            cls._contribution(
                index, window, float(irradiance[index, peak]), request.room_area,
                bool(per_window[index][1][peak]), profiles[index].sky_view_fraction(),
                excluded[index]
            )
            for index, window in enumerate(request.windows)
        )
        day = int(positions.day_of_year[peak])
        svl = float(sum(c.svl_w_m2 for c in contributions))
        return SvlResult(
            svl_peak_w_m2=svl,
            simplified_w_m2=SimplifiedSvl.calculate(request),
            peak_time=SvlPeakTime(
                month=int(YearCalendar.month_of(day)),
                day=YearCalendar.day_of_month(day),
                hour=float(positions.solar_hour[peak]),
            ),
            rating=cls.rate(svl, request.building_type),
            building_type=request.building_type,
            method=method,
            contributions=contributions,
            climate_station=sky.station_key,
        )

    @classmethod
    def rate(cls, svl_w_m2: float, building_type: BuildingType) -> SvlRating:
        """Miljöbyggnad rating for an SVL value in a building of the given type"""
        limits = SvlRatingLimitsMap.get(building_type)
        return next(
            (rating for rating, limit in limits if svl_w_m2 <= limit),
            SvlRating.EJ_UPPFYLLT,
        )

    @classmethod
    def _summer_positions(cls, latitude_deg: float) -> SolarPositions:
        """Solar positions for every hour between the spring and autumn equinox"""
        hours_per_day = SvlDefaults.HOURS_PER_DAY.value
        period = np.arange(
            SvlDefaults.FIRST_DAY_OF_YEAR.value, SvlDefaults.LAST_DAY_OF_YEAR.value + 1
        )
        days = np.repeat(period, hours_per_day)
        hours = np.tile(np.arange(hours_per_day, dtype=float), len(period))
        return SolarPositionCalculator.calculate(latitude_deg, days, hours)

    @classmethod
    def _window_irradiance(
        cls,
        request: SolarRequest,
        window: SolarWindow,
        profile: SkyGapProfile,
        positions: SolarPositions,
        sky: ClearSkyModel
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Irradiance on a window for every time sample.

        Returns:
            (irradiance in W/m², boolean sun-visible mask)
        """
        bearing = request.model_y_bearing_deg
        days, altitude = positions.day_of_year, positions.altitude_deg
        sun_up = altitude >= request.min_sun_altitude_deg

        beam_normal = np.where(sun_up, sky.beam_normal(days, altitude), 0.0)
        diffuse_horizontal = np.where(sun_up, sky.diffuse_horizontal(days, altitude), 0.0)
        cos_incidence = positions.direction_vectors(bearing) @ window.normal_array
        visible = sun_up & profile.is_visible(
            positions.model_angle_rad(bearing), altitude, window.direction_rad
        )

        direct = np.where(visible, beam_normal * np.clip(cos_incidence, 0.0, None), 0.0)
        sky_diffuse = diffuse_horizontal * cls._sky_diffuse_ratio(cos_incidence, window.tilt_deg)
        global_horizontal = beam_normal * np.sin(np.radians(altitude)) + diffuse_horizontal
        ground_view_factor = (1.0 - np.sin(np.radians(window.tilt_deg))) / 2.0
        reflected = global_horizontal * request.ground_reflectance * ground_view_factor
        return direct + (sky_diffuse + reflected) * profile.sky_view_fraction(), visible

    @classmethod
    def _sky_diffuse_ratio(cls, cos_incidence: np.ndarray, tilt_deg: float) -> np.ndarray:
        """
        Sky diffuse on the surface relative to diffuse horizontal.

        Args:
            cos_incidence: Cosine of the sun incidence angle (may be negative)
            tilt_deg: Surface tilt from vertical (0 = vertical, 90 = facing up)

        Returns:
            Y for a vertical surface; Y*sin(Σ) + cos(Σ) for a surface tilted
            upwards and Y*sin(Σ) for one tilted downwards (Σ from horizontal)
        """
        c0, c1, c2 = cls._Y_COEFFICIENTS
        vertical_ratio = np.maximum(
            cls._Y_MINIMUM, c0 + c1 * cos_incidence + c2 * cos_incidence ** 2
        )
        tilt = np.radians(tilt_deg)
        return vertical_ratio * np.cos(tilt) + max(np.sin(tilt), 0.0)

    @classmethod
    def _contribution(
        cls,
        index: int,
        window: SolarWindow,
        irradiance: float,
        room_area: float,
        sun_visible: bool,
        sky_view_fraction: float,
        excluded_by_orientation: bool
    ) -> SvlWindowContribution:
        """Build the contribution of one window"""
        gain = window.g_syst * irradiance * window.area
        return SvlWindowContribution(
            window_index=index,
            identifier=window.identifier,
            g_syst=window.g_syst,
            irradiance_w_m2=irradiance,
            solar_gain_w=gain,
            svl_w_m2=gain / room_area,
            sun_visible=sun_visible,
            sky_view_fraction=sky_view_fraction,
            excluded_by_orientation=excluded_by_orientation,
        )

"""Result models for the solar analyses (SVL and sunlight hours)"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from src.components.solar.constants import (
    BuildingType,
    SolarResponseField,
    SunlightLevel,
    SvlMethod,
    SvlRating,
)


@dataclass(frozen=True)
class SvlPeakTime:
    """When the SVL peak occurs (apparent solar time)"""
    month: int
    day: int
    hour: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            SolarResponseField.MONTH.value: self.month,
            SolarResponseField.DAY.value: self.day,
            SolarResponseField.HOUR.value: self.hour,
        }


@dataclass(frozen=True)
class SvlWindowContribution:
    """Contribution of one window to the room SVL at the peak hour"""
    window_index: int
    identifier: Optional[str]
    g_syst: float
    irradiance_w_m2: float
    solar_gain_w: float
    svl_w_m2: float
    sun_visible: bool
    sky_view_fraction: float
    excluded_by_orientation: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            SolarResponseField.WINDOW_INDEX.value: self.window_index,
            SolarResponseField.WINDOW_ID.value: self.identifier,
            SolarResponseField.G_SYST.value: self.g_syst,
            SolarResponseField.IRRADIANCE_W_M2.value: self.irradiance_w_m2,
            SolarResponseField.SOLAR_GAIN_W.value: self.solar_gain_w,
            SolarResponseField.SVL_W_M2.value: self.svl_w_m2,
            SolarResponseField.SUN_VISIBLE.value: self.sun_visible,
            SolarResponseField.SKY_VIEW_FRACTION.value: self.sky_view_fraction,
            SolarResponseField.EXCLUDED_BY_ORIENTATION.value: self.excluded_by_orientation,
        }


@dataclass(frozen=True)
class SvlResult:
    """Peak solar heat gain of a room"""
    svl_peak_w_m2: float
    simplified_w_m2: float
    peak_time: SvlPeakTime
    rating: SvlRating
    building_type: BuildingType
    method: SvlMethod
    contributions: Tuple[SvlWindowContribution, ...]
    climate_station: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            SolarResponseField.SVL_PEAK_W_M2.value: self.svl_peak_w_m2,
            SolarResponseField.SVL_SIMPLIFIED_W_M2.value: self.simplified_w_m2,
            SolarResponseField.SVL_PEAK_MONTH_HOUR.value: self.peak_time.to_dict(),
            SolarResponseField.SVL_RATING.value: self.rating.value,
            SolarResponseField.BUILDING_TYPE.value: self.building_type.value,
            SolarResponseField.SVL_METHOD.value: self.method.value,
            SolarResponseField.SVL_CLIMATE_STATION.value: self.climate_station,
            SolarResponseField.SVL_WINDOW_CONTRIBUTIONS.value: [
                c.to_dict() for c in self.contributions
            ],
        }


@dataclass(frozen=True)
class WindowSunlightHours:
    """Sunlight hours received through one window"""
    window_index: int
    identifier: Optional[str]
    sunlight_hours: float
    excluded_by_orientation: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            SolarResponseField.WINDOW_INDEX.value: self.window_index,
            SolarResponseField.WINDOW_ID.value: self.identifier,
            SolarResponseField.SUNLIGHT_HOURS.value: self.sunlight_hours,
            SolarResponseField.EXCLUDED_BY_ORIENTATION.value: self.excluded_by_orientation,
        }


@dataclass(frozen=True)
class SunlightHoursResult:
    """EN 17037 exposure to sunlight of a room"""
    sunlight_hours: float
    level: SunlightLevel
    min_sun_altitude_deg: float
    windows: Tuple[WindowSunlightHours, ...]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            SolarResponseField.SUNLIGHT_HOURS.value: self.sunlight_hours,
            SolarResponseField.SUNLIGHT_LEVEL.value: self.level.value,
            SolarResponseField.MIN_SUN_ALTITUDE_DEGREES.value: self.min_sun_altitude_deg,
            SolarResponseField.WINDOWS.value: [w.to_dict() for w in self.windows],
        }

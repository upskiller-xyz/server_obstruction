"""Solar analyses built on the obstruction calculation: SVL and sunlight hours"""

from src.components.solar.clear_sky import (
    ClearSkyModel,
    ClearSkyModelProvider,
    GenericClearSkyModel,
    StationClearSkyModel,
)
from src.components.solar.climate_station import ClimateStation, ClimateStationCatalogue
from src.components.solar.min_solar_altitude import (
    MinSolarAltitudeProvider,
    EquinoxMinSolarAltitude,
)
from src.components.solar.sky_gap_profile import SkyGapProfile
from src.components.solar.solar_position import SolarPositionCalculator, SolarPositions
from src.components.solar.solar_request import SolarRequest, SolarWindow
from src.components.solar.solar_result import (
    SunlightHoursResult,
    SvlPeakTime,
    SvlResult,
    SvlWindowContribution,
    WindowSunlightHours,
)
from src.components.solar.sunlight_hours_calculator import SunlightHoursCalculator
from src.components.solar.svl_calculator import SvlCalculator
from src.components.solar.year_calendar import YearCalendar

__all__ = [
    'ClearSkyModel',
    'ClearSkyModelProvider',
    'ClimateStation',
    'ClimateStationCatalogue',
    'GenericClearSkyModel',
    'MinSolarAltitudeProvider',
    'EquinoxMinSolarAltitude',
    'SkyGapProfile',
    'SolarPositionCalculator',
    'SolarPositions',
    'SolarRequest',
    'SolarWindow',
    'StationClearSkyModel',
    'SunlightHoursCalculator',
    'SunlightHoursResult',
    'SvlCalculator',
    'SvlPeakTime',
    'SvlResult',
    'SvlWindowContribution',
    'WindowSunlightHours',
    'YearCalendar',
]

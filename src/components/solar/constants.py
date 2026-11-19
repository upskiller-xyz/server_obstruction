"""Constants and enums for the solar analyses (SVL and sunlight hours)"""

from enum import Enum
from typing import Dict, Tuple

from src.utils.extended_enum import ExtendedEnumMixin
from src.utils.standard_map import StandardMap


class SolarRequestField(ExtendedEnumMixin, Enum):
    """Field names for solar analysis requests"""
    LATITUDE = "latitude"
    CITY = "city"
    MODEL_Y_BEARING_DEGREES = "model_y_bearing_degrees"
    MIN_SUN_ALTITUDE_DEGREES = "min_sun_altitude_degrees"
    ROOM_AREA = "room_area"
    BUILDING_TYPE = "building_type"
    GROUND_REFLECTANCE = "ground_reflectance"
    WINDOWS = "windows"

    # Per-window fields (x, y, z, direction_angle come from RequestField)
    WINDOW_ID = "id"
    AREA = "area"
    G_GLAZING = "g_glazing"
    G_SYST = "g_syst"
    SHADING_TYPE = "shading_type"
    TILT_DEGREES = "tilt_degrees"


class SolarResponseField(ExtendedEnumMixin, Enum):
    """Field names for solar analysis responses"""
    MIN_SUN_ALTITUDE_DEGREES = "min_sun_altitude_degrees"
    WINDOW_ID = "id"
    WINDOW_INDEX = "window_index"
    SUN_VISIBLE = "sun_visible"
    SKY_VIEW_FRACTION = "sky_view_fraction"

    # SVL
    SVL_PEAK_W_M2 = "svl_peak_w_m2"
    SVL_SIMPLIFIED_W_M2 = "svl_simplified_w_m2"
    SVL_PEAK_MONTH_HOUR = "svl_peak_month_hour"
    SVL_RATING = "svl_rating"
    BUILDING_TYPE = "building_type"
    SVL_METHOD = "svl_method"
    SVL_CLIMATE_STATION = "svl_climate_station"
    SVL_WINDOW_CONTRIBUTIONS = "svl_window_contributions"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    G_SYST = "g_syst"
    IRRADIANCE_W_M2 = "irradiance_w_m2"
    SOLAR_GAIN_W = "solar_gain_w"
    SVL_W_M2 = "svl_w_m2"

    # Sunlight hours
    SUNLIGHT_HOURS = "sunlight_hours"
    SUNLIGHT_LEVEL = "sunlight_level"
    EXCLUDED_BY_ORIENTATION = "excluded_by_orientation"
    WINDOWS = "windows"


class ShadingType(ExtendedEnumMixin, Enum):
    """
    Solar shading device types (per window), rows of DIN 4108-2 Table 7:
    internal and mid-pane blinds = "light colours or low transparency",
    external blind = venetian blind with rotatable slats at 45°,
    external screen = awning parallel to the glazing
    """
    NONE = "none"
    INTERNAL_BLIND = "internal_blind"
    MID_PANE_BLIND = "mid_pane_blind"
    EXTERNAL_BLIND = "external_blind"
    EXTERNAL_SCREEN = "external_screen"


class ShadingFactorMap(StandardMap):
    """
    Shading reduction factor Fc (g_syst = g_glazing * Fc) per shading type,
    guide values of DIN 4108-2:2013-02 Table 7 for double glazing with
    g > 0.40. The table gives the same value for blinds inside the room and
    between the panes. Triple glazing: internal and mid-pane 0.80, the rest
    equal.
    """
    _content: Dict[ShadingType, float] = {
        ShadingType.NONE: 1.00,
        ShadingType.INTERNAL_BLIND: 0.75,
        ShadingType.MID_PANE_BLIND: 0.75,
        ShadingType.EXTERNAL_BLIND: 0.25,
        ShadingType.EXTERNAL_SCREEN: 0.25,
    }
    _default: float = 1.00


class SolarControlShadingFactorMap(StandardMap):
    """
    Shading reduction factor Fc per shading type for solar control glazing
    (g <= 0.40), DIN 4108-2:2013-02 Table 7. A shading device removes a
    smaller share of the solar gain when the glazing already stops most of it.
    """
    _content: Dict[ShadingType, float] = {
        ShadingType.NONE: 1.00,
        ShadingType.INTERNAL_BLIND: 0.75,
        ShadingType.MID_PANE_BLIND: 0.75,
        ShadingType.EXTERNAL_BLIND: 0.30,
        ShadingType.EXTERNAL_SCREEN: 0.30,
    }
    _default: float = 1.00


class SvlMethod(ExtendedEnumMixin, Enum):
    """How the SVL value was obtained"""
    CLEAR_SKY_OBSTRUCTION = "clear_sky_obstruction"  # Surrounding mesh given
    CLEAR_SKY = "clear_sky"  # No mesh: unobstructed sky


class SvlRating(ExtendedEnumMixin, Enum):
    """Miljöbyggnad Indikator 2 ratings"""
    GULD = "Guld"
    SILVER = "Silver"
    BRONS = "Brons"
    EJ_UPPFYLLT = "Ej uppfyllt"


class BuildingType(ExtendedEnumMixin, Enum):
    """Building use that selects the Miljöbyggnad SVL limits"""
    RESIDENTIAL = "residential"  # Bostäder
    NON_RESIDENTIAL = "non-residential"  # Lokaler


class SvlRatingLimitsMap(StandardMap):
    """Upper SVL limit [W/m²] per rating, best first, for each building type"""
    _content: Dict[BuildingType, Tuple[Tuple[SvlRating, float], ...]] = {
        BuildingType.RESIDENTIAL: (
            (SvlRating.GULD, 18.0), (SvlRating.SILVER, 29.0), (SvlRating.BRONS, 38.0),
        ),
        BuildingType.NON_RESIDENTIAL: (
            (SvlRating.GULD, 22.0), (SvlRating.SILVER, 32.0), (SvlRating.BRONS, 40.0),
        ),
    }
    _default: Tuple[Tuple[SvlRating, float], ...] = ()


class SunlightLevel(ExtendedEnumMixin, Enum):
    """EN 17037 exposure to sunlight performance levels"""
    HIGH = "high"
    MEDIUM = "medium"
    MINIMUM = "minimum"
    NOT_MET = "not_met"


# Lower sunlight-hours limit [h] per level, best first
SUNLIGHT_LEVEL_LIMITS: Tuple[Tuple[SunlightLevel, float], ...] = (
    (SunlightLevel.HIGH, 4.0),
    (SunlightLevel.MEDIUM, 3.0),
    (SunlightLevel.MINIMUM, 1.5),
)


class SvlDefaults(ExtendedEnumMixin, Enum):
    """Default values for the SVL calculation"""
    G_GLAZING = 0.60  # Typical double glazing
    SOLAR_CONTROL_MAX_G = 0.40  # Solar control glazing up to this g (DIN 4108-2)
    GROUND_REFLECTANCE = 0.20  # ASHRAE default for mixed ground surfaces
    SIMPLIFIED_IRRADIANCE_W_M2 = 800.0  # Miljöbyggnad simplified formula
    SIMPLIFIED_COMBINED_IRRADIANCE_W_M2 = 560.0  # Two perpendicular façades
    SOUTH_BEARING_DEGREES = 180.0
    MAX_SOUTH_DEVIATION_DEGREES = 90.0  # Façades between 90° and 270° are assessed
    HOURS_PER_DAY = 24
    # Miljöbyggnad: peak between the spring and the autumn equinox
    FIRST_DAY_OF_YEAR = 80  # 21 March
    LAST_DAY_OF_YEAR = 266  # 23 September


class SunlightHoursDefaults(ExtendedEnumMixin, Enum):
    """Default values for the EN 17037 sunlight hours calculation"""
    REFERENCE_DAY_OF_YEAR = 80  # 21 March
    TIMESTEP_MINUTES = 10.0
    INEFFECTIVE_ANGLE_DEGREES = 25.0  # ξ for 300-550 mm walls
    MAX_SOUTH_DEVIATION_DEGREES = 120.0
    SOUTH_BEARING_DEGREES = 180.0


class SkyProfileDefaults(ExtendedEnumMixin, Enum):
    """Direction grid used to build the sky gap profile of a window"""
    NUM_DIRECTIONS = 35
    START_ANGLE_DEGREES = 5.0  # Relative to the left edge of the façade
    END_ANGLE_DEGREES = 175.0

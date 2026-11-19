"""OpenAPI paths and schemas of the solar endpoints (SVL and sunlight hours)"""
from typing import Any, Dict, List

from src.components.solar.constants import (
    BuildingType,
    ShadingType,
    SunlightLevel,
    SvlMethod,
    SvlRating,
)
from src.server.base.constants import EndpointName


class SolarOpenAPISpec:
    """Provides the OpenAPI fragments documenting the solar endpoints"""

    TAG: str = "Solar Analysis"

    @classmethod
    def paths(cls) -> Dict[str, Any]:
        """OpenAPI paths of the solar endpoints"""
        return {
            f"/{EndpointName.SVL.value}": cls._post(
                "Calculate peak solar heat gain (solvärmelast, SVL)",
                (
                    "Peak solar heat gain per floor area of a room (W/m²) for Miljöbyggnad "
                    "Indikator 2. With a mesh, every solar hour of a cloudless year is "
                    "evaluated and the direct sun is removed when it is hidden by the "
                    "surrounding geometry. With `city` the clear sky is that of the climate "
                    "station (same key as the daylight autonomy simulation); without it a "
                    "generic clear sky is used. Without a mesh the sky is unobstructed. "
                    "The simplified value of the manual (800 W/m² on one façade, 560 W/m² "
                    "on two perpendicular façades) is returned next to the calculated one."
                ),
                "SvlRequest",
                "SvlEnvelope",
            ),
            f"/{EndpointName.SUNLIGHT_HOURS.value}": cls._post(
                "Calculate sunlight hours of a room (EN 17037)",
                (
                    "Hours of direct sunlight a room receives on 21 March through its windows, "
                    "in apparent solar time. The sun counts when it is above the minimum solar "
                    "altitude, within the effective angle of the window and not hidden by the "
                    "surrounding geometry. Room hours are the union over all windows."
                ),
                "SunlightHoursRequest",
                "SunlightHoursEnvelope",
            ),
        }

    @classmethod
    def schemas(cls) -> Dict[str, Any]:
        """OpenAPI schemas of the solar endpoints"""
        return {
            "SolarWindow": cls._window_schema(),
            "SvlRequest": cls._request_schema(
                "Room, windows and site settings for the SVL calculation. "
                "Each window needs its glazed area. Give city, latitude or both.",
                ["room_area", "windows"],
            ),
            "SunlightHoursRequest": cls._request_schema(
                "Room windows and site settings for the sunlight hours calculation. "
                "Areas and glazing properties are ignored. Give city, latitude or both.",
                ["windows"],
            ),
            "SvlWindowContribution": cls._svl_window_contribution_schema(),
            "SvlEnvelope": cls._envelope(cls._svl_result_schema()),
            "SunlightHoursEnvelope": cls._envelope(cls._sunlight_hours_result_schema()),
        }

    @classmethod
    def _post(cls, summary: str, description: str, request: str, response: str) -> Dict[str, Any]:
        """POST operation with the standard success and error responses"""
        return {
            "post": {
                "summary": summary,
                "description": description,
                "tags": [cls.TAG],
                "requestBody": {"required": True, "content": cls._json(request)},
                "responses": {
                    "200": {
                        "description": "Calculated successfully",
                        "content": cls._json(response),
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": cls._json("ErrorResponse"),
                    },
                    "500": {
                        "description": "Internal server error",
                        "content": cls._json("ErrorResponse"),
                    },
                },
            }
        }

    @staticmethod
    def _json(schema: str) -> Dict[str, Any]:
        """JSON content referencing a component schema"""
        return {"application/json": {"schema": {"$ref": f"#/components/schemas/{schema}"}}}

    @staticmethod
    def _envelope(data_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Standard success envelope around a result schema"""
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string", "example": "success"},
                "data": data_schema,
            },
        }

    @staticmethod
    def _number(description: str, **extra: Any) -> Dict[str, Any]:
        """Number property"""
        return {"type": "number", "description": description, **extra}

    @staticmethod
    def _enum(values: List[str], description: str, **extra: Any) -> Dict[str, Any]:
        """String enum property"""
        return {"type": "string", "enum": values, "description": description, **extra}

    @classmethod
    def _window_schema(cls) -> Dict[str, Any]:
        """Window of a solar request"""
        return {
            "type": "object",
            "required": ["x", "y", "z", "direction_angle"],
            "properties": {
                "id": {"type": "string", "description": "Optional identifier echoed in the result"},
                "x": cls._number("Window centre X coordinate"),
                "y": cls._number("Window centre Y coordinate"),
                "z": cls._number("Window centre Z coordinate"),
                "direction_angle": cls._number(
                    "Outward window normal in radians, counter-clockwise from +X"
                ),
                "area": cls._number("Glazed area in m² (required for SVL)"),
                "g_glazing": cls._number("Solar factor of the glazing", default=0.6),
                "g_syst": cls._number(
                    "Solar factor of glazing and shading of the real product; replaces "
                    "g_glazing and shading_type",
                    nullable=True,
                ),
                "shading_type": cls._enum(
                    ShadingType.get_values(),
                    "Solar shading device; reduces g_glazing by the Fc guide value of "
                    "DIN 4108-2 Table 7",
                    default=ShadingType.NONE.value,
                ),
                "tilt_degrees": cls._number(
                    "Tilt of the glazing from vertical (0 = vertical, 90 = horizontal skylight)",
                    default=0.0,
                ),
            },
        }

    @classmethod
    def _request_schema(cls, description: str, required: List[str]) -> Dict[str, Any]:
        """Request shared by both solar endpoints"""
        return {
            "type": "object",
            "description": description,
            "required": required,
            "properties": {
                "city": {
                    "type": "string",
                    "description": (
                        "Climate station key, the same one sent to the daylight autonomy "
                        "simulation. Gives the site latitude and the clear sky of the station."
                    ),
                    "example": "stockholm-arlanda-ap",
                },
                "latitude": cls._number(
                    "Site latitude in degrees. Optional with city; overrides the latitude "
                    "of the station.",
                    example=59.33,
                ),
                "model_y_bearing_degrees": cls._number(
                    "Compass bearing of the model +Y axis (0 = +Y is true north)", default=0.0
                ),
                "min_sun_altitude_degrees": cls._number(
                    "Minimum solar altitude; defaults to the EN 17037 value for the site latitude"
                ),
                "room_area": cls._number("Room floor area in m² (required for SVL)"),
                "building_type": cls._enum(
                    BuildingType.get_values(),
                    "Building use that selects the Miljöbyggnad SVL limits (SVL only)",
                    default=BuildingType.RESIDENTIAL.value,
                ),
                "ground_reflectance": cls._number(
                    "Share of sunlight reflected by the ground, 0 to 1 (SVL only)",
                    default=0.2,
                ),
                "windows": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"$ref": "#/components/schemas/SolarWindow"},
                },
                "mesh": {
                    "type": "array",
                    "description": (
                        "Optional surrounding geometry as triangle vertices (groups of 3). "
                        "Without it the sky is treated as unobstructed."
                    ),
                    "items": {"type": "array", "items": {"type": "number"}},
                },
            },
        }

    @classmethod
    def _svl_result_schema(cls) -> Dict[str, Any]:
        """SVL result"""
        return {
            "type": "object",
            "properties": {
                "svl_peak_w_m2": cls._number("Peak solar heat gain per floor area (W/m²)"),
                "svl_simplified_w_m2": cls._number(
                    "Reference value of the simplified method of the manual (W/m²)"
                ),
                "svl_peak_month_hour": {
                    "type": "object",
                    "description": "Solar time of the peak",
                    "properties": {
                        "month": {"type": "integer"},
                        "day": {"type": "integer"},
                        "hour": cls._number("Solar hour"),
                    },
                },
                "svl_rating": cls._enum(SvlRating.get_values(), "Miljöbyggnad rating"),
                "building_type": cls._enum(
                    BuildingType.get_values(), "Building type the rating applies to"
                ),
                "svl_method": cls._enum(SvlMethod.get_values(), "Calculation method used"),
                "svl_climate_station": {
                    "type": "string",
                    "nullable": True,
                    "description": (
                        "Climate station whose clear sky was used (null for the generic "
                        "clear sky)"
                    ),
                },
                "svl_window_contributions": {
                    "type": "array",
                    "description": "Contribution of every window at the peak hour",
                    "items": {"$ref": "#/components/schemas/SvlWindowContribution"},
                },
            },
        }

    @classmethod
    def _svl_window_contribution_schema(cls) -> Dict[str, Any]:
        """Contribution of one window to the SVL at the peak hour"""
        return {
            "type": "object",
            "properties": {
                "window_index": {"type": "integer", "description": "Position in the request"},
                "id": {"type": "string", "nullable": True},
                "g_syst": cls._number("Solar factor of glazing and shading combined"),
                "irradiance_w_m2": cls._number("Solar irradiance on the glazing (W/m²)"),
                "solar_gain_w": cls._number("Solar heat gain through the window (W)"),
                "svl_w_m2": cls._number("Share of the room SVL (W/m²)"),
                "sun_visible": {
                    "type": "boolean",
                    "description": "Sun seen from the window at the peak hour",
                },
                "excluded_by_orientation": {
                    "type": "boolean",
                    "description": "Window facing north (outside 90°-270°), not assessed",
                },
                "sky_view_fraction": cls._number(
                    "Share of the sky diffuse and ground-reflected light left by the "
                    "surrounding geometry, 0 to 1",
                ),
            },
        }

    @classmethod
    def _sunlight_hours_result_schema(cls) -> Dict[str, Any]:
        """Sunlight hours result"""
        return {
            "type": "object",
            "properties": {
                "sunlight_hours": cls._number("Hours of direct sunlight of the room on 21 March"),
                "sunlight_level": cls._enum(SunlightLevel.get_values(), "EN 17037 level"),
                "min_sun_altitude_degrees": cls._number("Minimum solar altitude used"),
                "windows": {
                    "type": "array",
                    "description": "Sunlight hours of every window",
                    "items": {"type": "object"},
                },
            },
        }

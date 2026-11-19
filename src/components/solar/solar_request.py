"""
Solar analysis request models

A room with its windows, the site settings and the surrounding mesh.
Shared by the SVL and sunlight hours endpoints.
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np

from src.components.geometry import Mesh
from src.components.models import ObstructionRequest, Window
from src.components.solar.climate_station import ClimateStation, ClimateStationCatalogue
from src.components.solar.constants import (
    BuildingType,
    ShadingFactorMap,
    ShadingType,
    SolarControlShadingFactorMap,
    SolarRequestField,
    SvlDefaults,
)
from src.components.solar.min_solar_altitude import EquinoxMinSolarAltitude
from src.server.base.constants import RequestField


@dataclass(frozen=True)
class SolarWindow:
    """Window with the properties needed by the solar analyses"""
    window: Window
    direction_rad: float
    identifier: Optional[str]
    area: float
    g_glazing: float
    shading_type: ShadingType
    tilt_deg: float
    custom_g_syst: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolarWindow':
        """
        Create SolarWindow from a window dictionary.

        Args:
            data: Dict with x, y, z, direction_angle and optional id, area,
                g_glazing, shading_type, g_syst, tilt_degrees

        Returns:
            SolarWindow instance

        Raises:
            ValueError: If shading_type is not a known shading type
        """
        shading_value = data.get(SolarRequestField.SHADING_TYPE.value, ShadingType.NONE.value)
        shading_type = ShadingType.by_value(shading_value)
        if shading_type is None:
            raise ValueError(
                f"Unknown shading_type '{shading_value}'. "
                f"Expected one of: {', '.join(ShadingType.get_values())}"
            )

        identifier = data.get(SolarRequestField.WINDOW_ID.value)
        custom_g_syst = data.get(SolarRequestField.G_SYST.value)
        return cls(
            window=Window.from_dict(data),
            direction_rad=float(data[RequestField.DIRECTION_ANGLE.value]),
            identifier=None if identifier is None else str(identifier),
            area=float(data.get(SolarRequestField.AREA.value, 0.0)),
            g_glazing=float(data.get(
                SolarRequestField.G_GLAZING.value, SvlDefaults.G_GLAZING.value
            )),
            shading_type=shading_type,
            tilt_deg=float(data.get(SolarRequestField.TILT_DEGREES.value, 0.0)),
            custom_g_syst=None if custom_g_syst is None else float(custom_g_syst),
        )

    @property
    def g_syst(self) -> float:
        """
        System solar factor: the value given for the real product, or the
        glazing g-value reduced by the guide factor of the shading device
        """
        if self.custom_g_syst is not None:
            return self.custom_g_syst
        solar_control = self.g_glazing <= SvlDefaults.SOLAR_CONTROL_MAX_G.value
        factors = SolarControlShadingFactorMap if solar_control else ShadingFactorMap
        return self.g_glazing * factors.get(self.shading_type)

    @property
    def normal_array(self) -> np.ndarray:
        """Outward unit normal in model coordinates, including tilt"""
        tilt = math.radians(self.tilt_deg)
        return np.array([
            math.cos(tilt) * math.cos(self.direction_rad),
            math.cos(tilt) * math.sin(self.direction_rad),
            math.sin(tilt),
        ])

    def bearing_deg(self, model_y_bearing_deg: float) -> float:
        """Compass bearing of the window normal (clockwise from true north)"""
        return (90.0 - math.degrees(self.direction_rad) + model_y_bearing_deg) % 360.0

    def to_obstruction_request(self, mesh: Mesh) -> ObstructionRequest:
        """Obstruction request for this window against the given mesh"""
        return ObstructionRequest(window=self.window, mesh=mesh)


@dataclass(frozen=True)
class SolarRequest:
    """Input request for a per-room solar analysis"""
    latitude_deg: float
    model_y_bearing_deg: float
    min_sun_altitude_deg: float
    room_area: Optional[float]
    windows: Tuple[SolarWindow, ...]
    mesh: Optional[Mesh]
    climate_station: Optional[ClimateStation] = None
    ground_reflectance: float = SvlDefaults.GROUND_REFLECTANCE.value
    building_type: BuildingType = BuildingType.RESIDENTIAL

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolarRequest':
        """
        Create SolarRequest from dictionary.

        Args:
            data: Dict with windows, latitude and/or city (climate station
                key) and optional mesh, room_area, building_type,
                model_y_bearing_degrees, min_sun_altitude_degrees,
                ground_reflectance

        Returns:
            SolarRequest instance

        Raises:
            ValueError: If city is not a known climate station key or
                building_type is not a known building type
        """
        building_value = data.get(
            SolarRequestField.BUILDING_TYPE.value, BuildingType.RESIDENTIAL.value
        )
        building_type = BuildingType.by_value(building_value)
        if building_type is None:
            raise ValueError(
                f"Unknown building_type '{building_value}'. "
                f"Expected one of: {', '.join(BuildingType.get_values())}"
            )
        station = ClimateStationCatalogue.find(data.get(SolarRequestField.CITY.value))
        latitude = data.get(SolarRequestField.LATITUDE.value)
        latitude = station.latitude_deg if latitude is None else float(latitude)
        min_altitude = data.get(SolarRequestField.MIN_SUN_ALTITUDE_DEGREES.value)
        room_area = data.get(SolarRequestField.ROOM_AREA.value)

        return cls(
            latitude_deg=latitude,
            model_y_bearing_deg=float(
                data.get(SolarRequestField.MODEL_Y_BEARING_DEGREES.value, 0.0)
            ),
            min_sun_altitude_deg=(
                EquinoxMinSolarAltitude.get(latitude)
                if min_altitude is None else float(min_altitude)
            ),
            room_area=None if room_area is None else float(room_area),
            windows=tuple(
                SolarWindow.from_dict(w) for w in data[SolarRequestField.WINDOWS.value]
            ),
            mesh=ObstructionRequest._parse_mesh(data),
            climate_station=station,
            ground_reflectance=float(data.get(
                SolarRequestField.GROUND_REFLECTANCE.value,
                SvlDefaults.GROUND_REFLECTANCE.value,
            )),
            building_type=building_type,
        )

    @property
    def has_obstruction_data(self) -> bool:
        """Whether a surrounding mesh was provided"""
        return self.mesh is not None

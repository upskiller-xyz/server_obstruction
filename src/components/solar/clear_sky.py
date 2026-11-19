"""
Clear-sky irradiance models

A clear-sky model gives the beam irradiance normal to the sun and the diffuse
irradiance on a horizontal surface for a cloudless sky. Peak solar loads need
a cloudless year, which a typical weather year (EPW) is not.

- StationClearSkyModel: ASHRAE clear-sky model with the monthly optical
  depths (taub, taud) of a climate station. Location specific.
- GenericClearSkyModel: older ASHRAE A/B/C model with one set of monthly
  coefficients for every site. Used when no station is given.
"""

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from src.components.solar.climate_station import ClimateStation
from src.components.solar.year_calendar import YearCalendar


class ClearSkyModel(ABC):
    """Interface of a clear-sky irradiance model"""

    @property
    @abstractmethod
    def station_key(self) -> Optional[str]:
        """Key of the climate station the model belongs to (None = generic)"""

    @abstractmethod
    def beam_normal(self, day_of_year: np.ndarray, altitude_deg: np.ndarray) -> np.ndarray:
        """
        Beam irradiance on a surface normal to the sun.

        Args:
            day_of_year: Days of the year (1-365)
            altitude_deg: Solar altitude in degrees

        Returns:
            Irradiance in W/m² (0 when the sun is below the horizon)
        """

    @abstractmethod
    def diffuse_horizontal(self, day_of_year: np.ndarray, altitude_deg: np.ndarray) -> np.ndarray:
        """
        Sky diffuse irradiance on a horizontal surface.

        Args:
            day_of_year: Days of the year (1-365)
            altitude_deg: Solar altitude in degrees

        Returns:
            Irradiance in W/m² (0 when the sun is below the horizon)
        """


class GenericClearSkyModel(ClearSkyModel):
    """
    ASHRAE A/B/C clear-sky model, the same for every site

        I_bn = A * exp(-B / sin(altitude))        I_dh = C * I_bn
    """

    # Monthly coefficients, January to December (ASHRAE Fundamentals)
    _APPARENT_IRRADIANCE_W_M2 = np.array([
        1230.0, 1215.0, 1186.0, 1136.0, 1104.0, 1088.0,
        1085.0, 1107.0, 1151.0, 1192.0, 1221.0, 1233.0,
    ])
    _EXTINCTION_COEFFICIENT = np.array([
        0.142, 0.144, 0.156, 0.180, 0.196, 0.205,
        0.207, 0.201, 0.177, 0.160, 0.149, 0.142,
    ])
    _DIFFUSE_FACTOR = np.array([
        0.058, 0.060, 0.071, 0.097, 0.121, 0.134,
        0.136, 0.122, 0.092, 0.073, 0.063, 0.057,
    ])

    @property
    def station_key(self) -> Optional[str]:
        """The generic model belongs to no station"""
        return None

    def beam_normal(self, day_of_year: np.ndarray, altitude_deg: np.ndarray) -> np.ndarray:
        """Beam irradiance on a surface normal to the sun"""
        index = YearCalendar.month_of(day_of_year) - 1
        sin_altitude = np.sin(np.radians(altitude_deg))
        above = sin_altitude > 0.0

        safe_sin = np.where(above, sin_altitude, 1.0)
        beam = self._APPARENT_IRRADIANCE_W_M2[index] * np.exp(
            -self._EXTINCTION_COEFFICIENT[index] / safe_sin
        )
        return np.where(above, beam, 0.0)

    def diffuse_horizontal(self, day_of_year: np.ndarray, altitude_deg: np.ndarray) -> np.ndarray:
        """Sky diffuse irradiance on a horizontal surface"""
        index = YearCalendar.month_of(day_of_year) - 1
        return self._DIFFUSE_FACTOR[index] * self.beam_normal(day_of_year, altitude_deg)


class StationClearSkyModel(ClearSkyModel):
    """
    ASHRAE clear-sky model with the optical depths of a climate station

        E_b = E_0 * exp(-taub * m^ab)        E_d = E_0 * exp(-taud * m^ad)

    with E_0 the extraterrestrial normal irradiance and m the relative air
    mass (ASHRAE Fundamentals 2013, chapter 14).
    """

    _SOLAR_CONSTANT_W_M2: float = 1367.0
    _DAYS_PER_YEAR: float = 365.0

    def __init__(self, station: ClimateStation) -> None:
        self._station = station
        self._taub = np.array(station.taub)
        self._taud = np.array(station.taud)

    @property
    def station_key(self) -> Optional[str]:
        """Key of the climate station"""
        return self._station.key

    def beam_normal(self, day_of_year: np.ndarray, altitude_deg: np.ndarray) -> np.ndarray:
        """Beam irradiance on a surface normal to the sun"""
        taub, taud = self._optical_depths(day_of_year)
        exponent = 1.454 - 0.406 * taub - 0.268 * taud + 0.021 * taub * taud
        return self._attenuated(day_of_year, altitude_deg, taub, exponent)

    def diffuse_horizontal(self, day_of_year: np.ndarray, altitude_deg: np.ndarray) -> np.ndarray:
        """Sky diffuse irradiance on a horizontal surface"""
        taub, taud = self._optical_depths(day_of_year)
        exponent = 0.507 + 0.205 * taub - 0.080 * taud - 0.190 * taub * taud
        return self._attenuated(day_of_year, altitude_deg, taud, exponent)

    def _optical_depths(self, day_of_year: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Beam and diffuse optical depths of the month of each day"""
        index = YearCalendar.month_of(day_of_year) - 1
        return self._taub[index], self._taud[index]

    def _attenuated(
        self,
        day_of_year: np.ndarray,
        altitude_deg: np.ndarray,
        optical_depth: np.ndarray,
        exponent: np.ndarray
    ) -> np.ndarray:
        """Extraterrestrial irradiance attenuated through the atmosphere"""
        altitude = np.asarray(altitude_deg, dtype=float)
        above = altitude > 0.0
        safe_altitude = np.where(above, altitude, 90.0)

        air_mass = 1.0 / (
            np.sin(np.radians(safe_altitude))
            + 0.50572 * (6.07995 + safe_altitude) ** -1.6364
        )
        extraterrestrial = self._SOLAR_CONSTANT_W_M2 * (
            1.0 + 0.033 * np.cos(
                2.0 * np.pi * (np.asarray(day_of_year) - 3.0) / self._DAYS_PER_YEAR
            )
        )
        irradiance = extraterrestrial * np.exp(-optical_depth * air_mass ** exponent)
        return np.where(above, irradiance, 0.0)


class ClearSkyModelProvider:
    """Chooses the clear-sky model of a site"""

    @classmethod
    def for_station(cls, station: Optional[ClimateStation]) -> ClearSkyModel:
        """Station model when a station is known, generic model otherwise"""
        return GenericClearSkyModel() if station is None else StationClearSkyModel(station)

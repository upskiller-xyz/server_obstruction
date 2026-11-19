"""
Solar position calculator

Vectorised solar altitude / azimuth from latitude, day of year and
apparent solar time. Shared by the SVL and sunlight hours analyses.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SolarPositions:
    """Solar positions for a series of time samples"""
    day_of_year: np.ndarray
    solar_hour: np.ndarray
    altitude_deg: np.ndarray
    azimuth_deg: np.ndarray  # Compass bearing, clockwise from true north

    def model_angle_rad(self, model_y_bearing_deg: float) -> np.ndarray:
        """
        Horizontal sun direction in model coordinates.

        Args:
            model_y_bearing_deg: Compass bearing of the model +Y axis
                (0 when +Y points to true north)

        Returns:
            Angle in radians, counter-clockwise from the model +X axis
        """
        return np.radians(90.0 - (self.azimuth_deg - model_y_bearing_deg))

    def direction_vectors(self, model_y_bearing_deg: float) -> np.ndarray:
        """
        Unit vectors pointing to the sun in model coordinates (Z up).

        Returns:
            Array of shape (n, 3)
        """
        angle = self.model_angle_rad(model_y_bearing_deg)
        altitude = np.radians(self.altitude_deg)
        horizontal = np.cos(altitude)
        return np.column_stack((
            horizontal * np.cos(angle),
            horizontal * np.sin(angle),
            np.sin(altitude),
        ))


class SolarPositionCalculator:
    """
    Calculates solar positions in apparent solar time.

    Times are solar hours (12.0 = sun due south), so no longitude,
    time zone or equation of time is needed.
    """

    AXIAL_TILT_DEG: float = 23.45
    DAYS_PER_YEAR: float = 365.0
    DECLINATION_DAY_OFFSET: float = 284.0
    DEGREES_PER_HOUR: float = 15.0
    SOLAR_NOON_HOUR: float = 12.0
    SOUTH_BEARING_DEG: float = 180.0

    @classmethod
    def declination_deg(cls, day_of_year: np.ndarray) -> np.ndarray:
        """Solar declination (Cooper's equation)"""
        angle = 2.0 * np.pi * (cls.DECLINATION_DAY_OFFSET + day_of_year) / cls.DAYS_PER_YEAR
        return cls.AXIAL_TILT_DEG * np.sin(angle)

    @classmethod
    def calculate(
        cls,
        latitude_deg: float,
        day_of_year: np.ndarray,
        solar_hour: np.ndarray
    ) -> SolarPositions:
        """
        Calculate solar positions.

        Args:
            latitude_deg: Site latitude in degrees (north positive)
            day_of_year: Day numbers (1-365), one per sample
            solar_hour: Apparent solar time in hours, one per sample

        Returns:
            SolarPositions for all samples
        """
        days = np.asarray(day_of_year, dtype=float)
        hours = np.asarray(solar_hour, dtype=float)

        latitude = np.radians(latitude_deg)
        declination = np.radians(cls.declination_deg(days))
        hour_angle = np.radians(cls.DEGREES_PER_HOUR * (hours - cls.SOLAR_NOON_HOUR))

        sin_altitude = (
            np.sin(latitude) * np.sin(declination)
            + np.cos(latitude) * np.cos(declination) * np.cos(hour_angle)
        )
        altitude = np.arcsin(np.clip(sin_altitude, -1.0, 1.0))

        # Azimuth measured from south, west positive
        from_south = np.arctan2(
            np.sin(hour_angle),
            np.cos(hour_angle) * np.sin(latitude) - np.tan(declination) * np.cos(latitude)
        )
        azimuth = (cls.SOUTH_BEARING_DEG + np.degrees(from_south)) % 360.0

        return SolarPositions(
            day_of_year=days,
            solar_hour=hours,
            altitude_deg=np.degrees(altitude),
            azimuth_deg=azimuth,
        )

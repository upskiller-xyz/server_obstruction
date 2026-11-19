"""
Minimum solar altitude (γs,min) providers

EN 17037 only counts sunlight when the sun is above γs,min. The value
depends on the site latitude.
"""

import math
from abc import ABC, abstractmethod


class MinSolarAltitudeProvider(ABC):
    """Interface for obtaining γs,min for a site"""

    @classmethod
    @abstractmethod
    def get(cls, latitude_deg: float) -> float:
        """
        Get the minimum solar altitude.

        Args:
            latitude_deg: Site latitude in degrees

        Returns:
            γs,min in degrees
        """
        pass


class EquinoxMinSolarAltitude(MinSolarAltitudeProvider):
    """
    γs,min on 21 March from the site latitude, closed form of
    Vychytil & Mohelníková, "Sunlight exposure conditions for buildings in
    European localities", Results in Engineering 24 (2024) 103208, eq. 1,
    10 and 11. It reproduces the EN 17037 values of the capitals
    (Stockholm 8.26°, Oslo 8.16°, Copenhagen 9.92°).

    The sun reaches the limit azimuth of the window (55° from south, a
    window turned 120° from south with a 25° ineffective angle) at the hour
    angle ω. γs,min is the solar altitude 1.5 h (the minimum exposure)
    before that:

        A = tan(55°), B = sin(φ) * cos(φ) * tan(δ)
        cos(ω) = (2A²B + sqrt((2A²B)² - 4 (A²sin²φ + 1)(A²cos²φ tan²δ - 1)))
                 / (2 (A²sin²φ + 1))
        γs,min = asin(cos(ω + 22.5°) cos(φ) cos(δ) + sin(φ) sin(δ))
    """

    _LIMIT_AZIMUTH_DEG: float = 55.0  # Astronomical azimuth (from south)
    _DECLINATION_DEG: float = -0.02  # 21 March according to EN 17037
    _EXPOSURE_HOUR_ANGLE_DEG: float = 22.5  # 1.5 h of minimum sunlight exposure

    @classmethod
    def get(cls, latitude_deg: float) -> float:
        """Get γs,min in degrees for a latitude"""
        latitude = math.radians(latitude_deg)
        declination = math.radians(cls._DECLINATION_DEG)
        hour_angle = cls._limit_hour_angle(latitude, declination) + math.radians(
            cls._EXPOSURE_HOUR_ANGLE_DEG
        )
        sin_altitude = (
            math.cos(hour_angle) * math.cos(latitude) * math.cos(declination)
            + math.sin(latitude) * math.sin(declination)
        )
        return math.degrees(math.asin(max(-1.0, min(1.0, sin_altitude))))

    @classmethod
    def _limit_hour_angle(cls, latitude: float, declination: float) -> float:
        """Hour angle (radians) at which the sun is at the limit azimuth"""
        a_squared = math.tan(math.radians(cls._LIMIT_AZIMUTH_DEG)) ** 2
        b = math.sin(latitude) * math.cos(latitude) * math.tan(declination)
        quadratic = a_squared * math.sin(latitude) ** 2 + 1.0
        constant = a_squared * (math.cos(latitude) * math.tan(declination)) ** 2 - 1.0
        linear = 2.0 * a_squared * b
        cos_hour_angle = (
            linear + math.sqrt(linear ** 2 - 4.0 * quadratic * constant)
        ) / (2.0 * quadratic)
        return math.acos(max(-1.0, min(1.0, cos_hour_angle)))

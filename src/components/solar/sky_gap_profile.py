"""
Sky gap profile

Visible-sky elevation interval of a window per horizontal direction,
built from the gap-based obstruction results. Answers "is the sun
visible from this window?" for any sun position and "how much of the
sky diffuse light still reaches the window?".
"""

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np

from src.server.base.constants import ResponseField


@dataclass(frozen=True)
class SkyGapProfile:
    """Visible sky interval [lower, upper] per direction relative to the window normal"""
    relative_angles_rad: np.ndarray  # Ascending, counter-clockwise from the normal
    lower_deg: np.ndarray  # Sky starts above this elevation
    upper_deg: np.ndarray  # Sky ends below this elevation

    FULL_SKY_UPPER_DEG = 90.0
    _VIEW_FRACTION_STEPS = 180  # Horizontal integration steps over the front 180°

    @classmethod
    def unobstructed(cls) -> 'SkyGapProfile':
        """Profile of a window with a free view of the whole sky"""
        return cls(
            relative_angles_rad=np.array([-np.pi / 2.0, np.pi / 2.0]),
            lower_deg=np.zeros(2),
            upper_deg=np.full(2, cls.FULL_SKY_UPPER_DEG),
        )

    @classmethod
    def from_direction_results(
        cls,
        results: List[Dict[str, Any]],
        window_direction_rad: float
    ) -> 'SkyGapProfile':
        """
        Build a profile from multi-direction obstruction results.

        Args:
            results: Per-direction dicts with direction_angle, horizon and zenith
            window_direction_rad: Horizontal direction of the window normal

        Returns:
            SkyGapProfile sorted by relative angle
        """
        angle_key = ResponseField.OBSTRUCTION_ANGLE_DEGREES.value
        relative = np.array([
            r[ResponseField.DIRECTION_ANGLE.value] - window_direction_rad for r in results
        ])
        lower = np.array([r[ResponseField.HORIZON.value][angle_key] for r in results])
        zenith = np.array([r[ResponseField.ZENITH.value][angle_key] for r in results])

        order = np.argsort(relative)
        return cls(
            relative_angles_rad=relative[order],
            lower_deg=lower[order],
            upper_deg=cls.FULL_SKY_UPPER_DEG - zenith[order],
        )

    def is_visible(self, sun_angle_rad: np.ndarray, altitude_deg: np.ndarray,
                   window_direction_rad: float) -> np.ndarray:
        """
        Check whether the sun is visible from the window.

        Directions outside the sampled range use the nearest sampled
        direction; directions behind the window are never visible.

        Args:
            sun_angle_rad: Horizontal sun direction (model angle, radians)
            altitude_deg: Solar altitude in degrees
            window_direction_rad: Horizontal direction of the window normal

        Returns:
            Boolean array, True where the sun is inside the sky gap
        """
        relative = self._wrap(np.asarray(sun_angle_rad) - window_direction_rad)
        lower = np.interp(relative, self.relative_angles_rad, self.lower_deg)
        upper = np.interp(relative, self.relative_angles_rad, self.upper_deg)

        in_front = np.abs(relative) < np.pi / 2.0
        return in_front & (altitude_deg > lower) & (altitude_deg < upper)

    def sky_view_fraction(self) -> float:
        """
        Share of the sky diffuse light of a free vertical window that still
        reaches this window (0 = sky fully hidden, 1 = free view).

        Every piece of visible sky is weighted by the cosine of its
        incidence on a vertical glazing, for a sky of uniform brightness:

            fraction = ∫ cos(φ) * [F(upper) - F(lower)] dφ / (π/2)
            F(h) = h/2 + sin(2h)/4

        with φ the horizontal angle from the window normal and h the elevation.
        """
        step = np.pi / self._VIEW_FRACTION_STEPS
        angles = -np.pi / 2.0 + step * (np.arange(self._VIEW_FRACTION_STEPS) + 0.5)
        lower = np.radians(np.interp(angles, self.relative_angles_rad, self.lower_deg))
        upper = np.radians(np.interp(angles, self.relative_angles_rad, self.upper_deg))

        visible = np.clip(
            self._elevation_weight(upper) - self._elevation_weight(lower), 0.0, None
        )
        fraction = float(np.sum(np.cos(angles) * visible) * step / (np.pi / 2.0))
        return min(fraction, 1.0)

    @staticmethod
    def _elevation_weight(elevation_rad: np.ndarray) -> np.ndarray:
        """Integral of cos²(h) from the horizon up to an elevation"""
        return elevation_rad / 2.0 + np.sin(2.0 * elevation_rad) / 4.0

    @staticmethod
    def _wrap(angle_rad: np.ndarray) -> np.ndarray:
        """Wrap angles to (-π, π]"""
        return np.arctan2(np.sin(angle_rad), np.cos(angle_rad))

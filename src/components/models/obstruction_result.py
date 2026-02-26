"""
Obstruction result model

Result of obstruction calculation with angle and highest point.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from src.components.geometry import Point3D
from src.server.base.constants import ResponseField, RequestField


@dataclass(frozen=True)
class ObstructionResult:
    """Result of obstruction calculation"""
    obstruction_angle_degrees: float
    obstruction_angle_radians: float
    highest_point: Optional[Point3D]
    gap_midpoint_deg: float = 0.0
    gap_amplitude_deg: float = 0.0

    @classmethod
    def no_obstruction(cls, highest_point: Optional[Point3D] = None) -> 'ObstructionResult':
        """
        Create a result indicating no obstruction found

        Args:
            highest_point: Optional point to include in result

        Returns:
            ObstructionResult with zero angle
        """
        return cls(
            obstruction_angle_degrees=0.0,
            obstruction_angle_radians=0.0,
            highest_point=highest_point,
            gap_midpoint_deg=45.0,
            gap_amplitude_deg=90.0
        )

    @classmethod
    def from_gap(
        cls,
        horizon_deg: float,
        zenith_deg: float,
        gap_midpoint_deg: float,
        gap_amplitude_deg: float
    ) -> 'ObstructionResult':
        """
        Create horizon and zenith results from gap-based calculation.

        Returns a tuple of (horizon_result, zenith_result).
        """
        horizon = cls(
            obstruction_angle_degrees=horizon_deg,
            obstruction_angle_radians=float(np.radians(horizon_deg)),
            highest_point=None,
            gap_midpoint_deg=gap_midpoint_deg,
            gap_amplitude_deg=gap_amplitude_deg
        )
        zenith = cls(
            obstruction_angle_degrees=zenith_deg,
            obstruction_angle_radians=float(np.radians(zenith_deg)),
            highest_point=None,
            gap_midpoint_deg=gap_midpoint_deg,
            gap_amplitude_deg=gap_amplitude_deg
        )
        return horizon, zenith

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            ResponseField.OBSTRUCTION_ANGLE_DEGREES.value: self.obstruction_angle_degrees,
            ResponseField.OBSTRUCTION_ANGLE_RADIANS.value: self.obstruction_angle_radians,
            ResponseField.HIGHEST_POINT.value: {
                RequestField.X.value: self.highest_point.x,
                RequestField.Y.value: self.highest_point.y,
                RequestField.Z.value: self.highest_point.z
            } if self.highest_point else None,
            'gap_midpoint_deg': self.gap_midpoint_deg,
            'gap_amplitude_deg': self.gap_amplitude_deg
        }

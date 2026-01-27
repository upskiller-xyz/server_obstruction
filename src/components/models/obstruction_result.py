"""
Obstruction result model

Result of obstruction calculation with angle and highest point.
"""

from dataclasses import dataclass
from typing import Optional

from src.components.geometry import Point3D
from src.server.base.constants import ResponseField, RequestField


@dataclass(frozen=True)
class ObstructionResult:
    """Result of obstruction calculation"""
    obstruction_angle_degrees: float
    obstruction_angle_radians: float
    highest_point: Optional[Point3D]

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
            highest_point=highest_point
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            ResponseField.OBSTRUCTION_ANGLE_DEGREES.value: self.obstruction_angle_degrees,
            ResponseField.OBSTRUCTION_ANGLE_RADIANS.value: self.obstruction_angle_radians,
            ResponseField.HIGHEST_POINT.value: {
                RequestField.X.value: self.highest_point.x,
                RequestField.Y.value: self.highest_point.y,
                RequestField.Z.value: self.highest_point.z
            } if self.highest_point else None
        }

"""
Window model

Represents a window with center point and normal direction.
"""

from typing import List

from dataclasses import dataclass

from src.components.geometry import Point3D, Vector3D, ReferencePointCalculator
from src.server.base.constants import RequestField


@dataclass(frozen=True)
class Window:
    """Window definition with center point and normal direction"""
    center: Point3D
    normal: Vector3D

    @classmethod
    def set_angle(cls, other:'Window', angle:float)->'Window':
        vec = Vector3D.from_horizontal_angle(angle)
        return Window(other.center, vec)

    @classmethod
    def from_dict(cls, data: dict) -> 'Window':
        """
        Create Window from dictionary with pre-computed center

        Args:
            data: Dict with keys:
                - x, y, z: window center coordinates
                - direction_angle: horizontal rotation angle in radians (0 to 2π)

        Returns:
            Window instance
        """
        center = Point3D(
            x=float(data[RequestField.X.value]),
            y=float(data[RequestField.Y.value]),
            z=float(data[RequestField.Z.value])
        )

        normal = Vector3D.from_horizontal_angle(float(data[RequestField.DIRECTION_ANGLE.value]))

        return cls(center=center, normal=normal)

    @classmethod
    def from_endpoints(
        cls,
        x1: float, y1: float, z1: float,
        x2: float, y2: float, z2: float,
        direction_angle: float,
        room_polygon: List[List[float]],
    ) -> 'Window':
        """
        Create Window from window corner endpoints and room polygon.

        Calculates the reference point by projecting the window bounding box
        center onto the room polygon boundary.

        Args:
            x1, y1, z1: First window corner
            x2, y2, z2: Second window corner
            direction_angle: Horizontal rotation angle in radians (0 to 2π)
            room_polygon: List of [x, y] vertices forming the room boundary

        Returns:
            Window instance with projected center and direction normal
        """
        center = ReferencePointCalculator.calculate(
            x1, y1, z1, x2, y2, z2, room_polygon
        )
        normal = Vector3D.from_horizontal_angle(direction_angle)
        return cls(center=center, normal=normal)

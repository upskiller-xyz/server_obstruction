"""
Window model

Represents a window with center point and normal direction.
"""

from dataclasses import dataclass

from src.components.geometry import Point3D, Vector3D
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
        Create Window from dictionary

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

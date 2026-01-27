"""
3D vector representation

Immutable dataclass for 3D vectors with vector operations.
"""

from dataclasses import dataclass
import numpy as np

from src.components.geometry.coordinate_system import CoordinateSystem


@dataclass(frozen=True)
class Vector3D:
    """Immutable 3D vector representation"""
    x: float
    y: float
    z: float

    def to_array(self) -> np.ndarray:
        """Convert to numpy array"""
        return np.array([self.x, self.y, self.z])

    def magnitude(self) -> float:
        """Calculate vector magnitude"""
        return float(np.linalg.norm(self.to_array()))

    def normalize(self) -> 'Vector3D':
        """Return normalized vector"""
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize zero vector")
        arr = self.to_array() / mag
        return Vector3D(x=float(arr[0]), y=float(arr[1]), z=float(arr[2]))

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Vector3D':
        """Create Vector3D from numpy array"""
        return cls(x=float(arr[0]), y=float(arr[1]), z=float(arr[2]))

    def get_vertical(self, coord_system: type = CoordinateSystem) -> float:
        """
        Get vertical component according to coordinate system

        Args:
            coord_system: Coordinate system class to use

        Returns:
            Vertical component value
        """
        return coord_system.get_vertical_component(self.to_array())

    def get_horizontal(self, coord_system: type = CoordinateSystem) -> 'Vector3D':
        """
        Get horizontal components only (vertical removed)

        Args:
            coord_system: Coordinate system class to use

        Returns:
            Vector with vertical component set to 0
        """
        arr = coord_system.remove_vertical_component(self.to_array())
        return Vector3D.from_array(arr)

    @classmethod
    def from_horizontal_angle(cls, angle: float) -> 'Vector3D':
        """
        Create horizontal direction vector from single angle

        Coordinate system: Y-axis points up, rotation in XZ plane
        - angle=0: Points in +X direction
        - angle=π/2: Points in +Z direction
        - angle=π: Points in -X direction
        - angle=3π/2: Points in -Z direction

        Args:
            angle: Horizontal rotation angle in radians (0 to 2π)

        Returns:
            Unit vector in horizontal plane (y component = 0)
        """
        x = np.cos(angle)
        y = np.sin(angle)
        z = 0.0  # Horizontal plane only
        return cls(x=float(x), y=float(y), z=float(z))

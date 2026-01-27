"""
3D point representation

Immutable dataclass for 3D points with coordinate system utilities.
"""

from dataclasses import dataclass
import numpy as np

from src.components.geometry.coordinate_system import CoordinateSystem


@dataclass(frozen=True)
class Point3D:
    """Immutable 3D point representation"""
    x: float
    y: float
    z: float

    def to_array(self) -> np.ndarray:
        """Convert to numpy array"""
        return np.array([self.x, self.y, self.z])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Point3D':
        """Create Point3D from numpy array"""
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

    def get_horizontal_array(self, coord_system: type = CoordinateSystem) -> np.ndarray:
        """
        Get horizontal components as array according to coordinate system

        Args:
            coord_system: Coordinate system class to use

        Returns:
            Array with only horizontal components (vertical set to 0)
        """
        return coord_system.remove_vertical_component(self.to_array())

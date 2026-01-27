"""
Vertical plane representation for obstruction calculations

Defines a vertical plane passing through a point with a given direction.
"""
from dataclasses import dataclass
import numpy as np
from src.components.geometry import Point3D, Vector3D
from src.server.base.constants import MathConstants
from src.components.models import Window


@dataclass(frozen=True)
class VerticalPlane:
    """
    Vertical plane passing through a point with a given direction

    The plane contains:
    - The origin point
    - The horizontal direction vector
    - The vertical (up) direction

    Plane equation: normal · (P - origin) = 0
    where normal is perpendicular to both direction and up
    """
    origin: Point3D
    direction: Vector3D  # Horizontal direction (unit vector)
    normal: Vector3D  # Plane normal (perpendicular to direction and up)

    @classmethod
    def from_window(cls, window:Window) -> 'VerticalPlane':
        """
        Create vertical plane from window center and normal direction

        Args:
            window_center: Window center point
            window_normal: Window viewing direction (unit vector)

        Returns:
            VerticalPlane passing through window center in viewing direction
        """
        # Plane normal is perpendicular to both viewing direction and up
        # normal = direction × up
        direction_arr = window.normal.to_array()
        up = np.array([0.0, 0.0, 1.0])

        normal_arr = np.cross(direction_arr, up)
        normal_mag = np.linalg.norm(normal_arr)

        if normal_mag < MathConstants.EPSILON.value:
            # Direction is parallel to up (looking straight up/down)
            # Use forward direction as reference
            forward = np.array([1.0, 0.0, 0.0])
            normal_arr = np.cross(direction_arr, forward)
            normal_mag = np.linalg.norm(normal_arr)

        normal_arr = normal_arr / normal_mag

        return cls(
            origin=window.center,
            direction=window.normal,
            normal=Vector3D.from_array(normal_arr)
        )

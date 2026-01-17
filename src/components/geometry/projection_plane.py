"""
Projection plane representation

Vertical plane in 3D space for projecting points onto.
"""

from dataclasses import dataclass
import numpy as np

from src.components.geometry.point import Point3D
from src.components.geometry.vector import Vector3D
from src.components.geometry.coordinate_system import CoordinateSystem
from src.server.base.constants import MathConstants


@dataclass(frozen=True)
class ProjectionPlane:
    """
    Vertical plane in 3D space defined by origin and basis vectors

    The plane passes through the origin point and is defined by:
    - u_axis: horizontal direction vector
    - v_axis: vertical direction vector (always points up in world coordinates)
    """
    origin: Point3D
    u_axis: Vector3D  # Horizontal axis (perpendicular to normal and vertical)
    v_axis: Vector3D  # Vertical axis (always pointing up)
    normal: Vector3D  # Normal to the plane (viewing direction)

    @staticmethod
    def calculate_plane_normal(direction: Vector3D) -> Vector3D:
        """
        Calculate plane normal perpendicular to direction and world up

        The plane contains both the viewing direction and world up.
        The plane's geometric normal is perpendicular to both.

        Args:
            direction: Viewing direction vector

        Returns:
            Normalized plane normal vector
        """
        direction_arr = direction.to_array()
        plane_normal_arr = np.cross(direction_arr, CoordinateSystem.UP)
        plane_normal_mag = np.linalg.norm(plane_normal_arr)

        if plane_normal_mag < MathConstants.EPSILON.value:
            # Direction is parallel to world up (looking straight up/down)
            # Use forward direction as reference instead
            plane_normal_arr = np.cross(direction_arr, CoordinateSystem.FORWARD)

        normalized = plane_normal_arr / np.linalg.norm(plane_normal_arr)
        return Vector3D.from_array(normalized)

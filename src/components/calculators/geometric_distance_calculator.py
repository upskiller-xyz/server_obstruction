"""Geometric distance calculations for planes and points"""

import numpy as np

from src.components.geometry import Point3D
from src.components.geometry.vertical_plane import VerticalPlane
from src.components.models import Window
from src.server.base.constants import MathConstants


class GeometricDistanceCalculator:
    """
    Calculates geometric distances between points and planes

    Single Responsibility:
    - Only calculates geometric distances
    - Does NOT perform intersections or angle calculations
    """

    @staticmethod
    def point_to_plane_distance(point: Point3D, plane: VerticalPlane) -> float:
        """
        Calculate signed distance from point to plane

        Args:
            point: Point to test
            plane: Vertical plane

        Returns:
            Signed distance (positive on normal side, negative on other side)
        """
        # Distance = normal · (point - origin)
        point_vec = point.to_array() - plane.origin.to_array()
        return float(np.dot(plane.normal.to_array(), point_vec))

    @staticmethod
    def horizontal_distance(point: Point3D, window: Window) -> float:
        """
        Calculate horizontal distance from window to point along viewing direction

        Args:
            point: Target point
            window: Window with center and normal

        Returns:
            Horizontal distance (negative if behind window)
        """
        point_vec = point.to_array() - window.center.to_array()

        # Get horizontal component of viewing direction
        normal_arr = window.normal.to_array()
        normal_horizontal = np.array([normal_arr[0], normal_arr[1], 0.0])
        magnitude = np.linalg.norm(normal_horizontal)

        if magnitude < MathConstants.EPSILON.value:
            # Viewing straight up or down - use radial distance
            point_horizontal = np.array([point_vec[0], point_vec[1], 0.0])
            return float(np.linalg.norm(point_horizontal))

        # Project onto horizontal viewing direction
        normal_horizontal = normal_horizontal / magnitude
        return float(np.dot(point_vec, normal_horizontal))

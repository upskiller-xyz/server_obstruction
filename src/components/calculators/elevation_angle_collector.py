"""Elevation angle collector for gap-based obstruction calculations"""

from typing import List, Tuple

import numpy as np

from src.components.calculators.plane_triangle_intersector import PlaneTriangleIntersector
from src.components.geometry import Point3D, Triangle
from src.components.geometry.vertical_plane import VerticalPlane
from src.components.models import Window


class ElevationAngleCollector:
    """
    Collects all elevation angles from triangle intersections

    Single Responsibility:
    - Only collects and sorts elevation angles
    - Used by gap-based obstruction calculator
    """

    @classmethod
    def collect_all_angles(
        cls,
        triangles: Tuple[Triangle, ...],
        window: Window
    ) -> List[float]:
        """
        Collect ALL intersection point elevation angles from ALL triangles

        Used by gap-based obstruction calculator. No surface orientation
        filter (uses all triangles). No max_angle cap. Returns all valid
        intersection points (0-2 per triangle) as elevation angles in degrees.

        Args:
            triangles: All triangles (no horizon/zenith split)
            window: Window with center and normal for this direction

        Returns:
            Sorted list of elevation angles in degrees (0=horizontal, 90=up)
        """
        if not triangles:
            return []

        plane = VerticalPlane.from_window(window)
        angles: List[float] = []

        for triangle in triangles:
            points = PlaneTriangleIntersector.intersect_triangle_with_plane(
                triangle, plane
            )
            for point in points:
                angle = cls._calculate_elevation_angle(point, window)
                if angle is not None:
                    angles.append(angle)

        return sorted(angles)

    @classmethod
    def _calculate_elevation_angle(
        cls,
        point: Point3D,
        window: Window
    ) -> float | None:
        """
        Calculate elevation angle for a single point

        Args:
            point: Intersection point
            window: Window for reference

        Returns:
            Elevation angle in degrees, or None if point is invalid
        """
        vertical_distance = point.z - window.center.z
        if vertical_distance <= 0:
            return None

        horizontal_distance = PlaneTriangleIntersector._horizontal_distance(
            point, window
        )
        if horizontal_distance < 0:
            return None

        return float(np.degrees(
            np.arctan2(vertical_distance, horizontal_distance)
        ))

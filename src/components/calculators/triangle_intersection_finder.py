"""Triangle intersection finder for geometric calculations"""

import numpy as np

from src.components.calculators.distance_calculator import DistanceCalculator
from src.components.calculators.plane_triangle_intersector import PlaneTriangleIntersector
from src.components.geometry import Point3D, Triangle
from src.components.geometry.vertical_plane import VerticalPlane
from src.components.models import Window
from src.server.base.constants import ANGLES


class TriangleIntersectionFinder:
    """
    Finds intersection points between triangles and vertical planes

    Single Responsibility:
    - Only handles geometric intersection finding
    - Does NOT calculate angles or filter by angle
    """

    @classmethod
    def find_intersection(
        cls,
        triangle: Triangle,
        plane: VerticalPlane,
        window: Window,
        angle_type: ANGLES
    ) -> Point3D | None:
        """
        Get the intersection point with maximum distance

        Args:
            triangle: Triangle to intersect
            plane: Vertical plane
            window: Window for distance calculation
            angle_type: Type of angle being calculated

        Returns:
            Point with maximum distance, or None if no intersection
        """
        intersections = PlaneTriangleIntersector.intersect_triangle_with_plane(
            triangle, plane
        )

        if not intersections:
            return None

        distances = DistanceCalculator.call(intersections, angle_type, window)
        if not distances:
            return None

        # Get point with maximum distance
        max_index = np.argmax(distances)
        return intersections[max_index]

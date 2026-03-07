"""Plane-triangle intersection calculator"""

from typing import List

from src.components.calculators.edge_plane_intersector import EdgePlaneIntersector
from src.components.calculators.geometric_distance_calculator import GeometricDistanceCalculator
from src.components.calculators.obstruction_angle_calculator import ObstructionAngleCalculator
from src.components.geometry import Mesh, Point3D, Triangle
from src.components.geometry.intersection_point import IntersectionPoint
from src.components.geometry.vertical_plane import VerticalPlane
from src.components.models import Window
from src.server.base.constants import ANGLES


class PlaneTriangleIntersector:
    """
    Calculates plane-triangle intersections efficiently

    Single Responsibility:
    - Orchestrates plane-triangle intersection calculations
    - Delegates distance calculation to GeometricDistanceCalculator
    - Delegates edge intersection to EdgePlaneIntersector
    - Delegates angle calculation to ObstructionAngleCalculator

    Uses the plane equation to find where triangle edges intersect
    the vertical plane, then calculates obstruction angles.
    """

    @staticmethod
    def intersect_triangle_with_plane(
        triangle: Triangle,
        plane: VerticalPlane
    ) -> List[Point3D]:
        """
        Find all intersection points between triangle and plane

        Args:
            triangle: Triangle to test
            plane: Vertical plane

        Returns:
            List of intersection points (0, 1, or 2 points)
        """
        # Calculate signed distances for all vertices
        d1 = GeometricDistanceCalculator.point_to_plane_distance(triangle.v1, plane)
        d2 = GeometricDistanceCalculator.point_to_plane_distance(triangle.v2, plane)
        d3 = GeometricDistanceCalculator.point_to_plane_distance(triangle.v3, plane)

        # Check each edge for intersection
        edges = [
            (triangle.v1, triangle.v2, d1, d2),
            (triangle.v2, triangle.v3, d2, d3),
            (triangle.v3, triangle.v1, d3, d1)
        ]

        # Delegate edge intersection to EdgePlaneIntersector
        intersections = [
            EdgePlaneIntersector.intersect(p1, p2, dist1, dist2)
            for p1, p2, dist1, dist2 in edges
        ]

        return [point for point in intersections if point is not None]

    @classmethod
    def find_all_intersections(
        cls,
        mesh: Mesh,
        plane: VerticalPlane,
        window: Window,
        angle_type: ANGLES = ANGLES.HORIZON
    ) -> List[IntersectionPoint]:
        """
        Find all plane-triangle intersections with calculated angles

        Args:
            mesh: 3D mesh
            plane: Vertical viewing plane
            window: Window with center and normal
            angle_type: Type of angle to calculate (HORIZON or ZENITH)

        Returns:
            List of intersection points with angles
        """
        intersection_points = []

        for triangle in mesh.triangles:
            # Get intersection points for this triangle
            points = cls.intersect_triangle_with_plane(triangle, plane)

            # Calculate angles for each intersection point
            for point in points:
                angle = ObstructionAngleCalculator.calculate(point, window, angle_type)
                if angle is not None and angle > 0:
                    intersection_points.append(
                        IntersectionPoint(point, triangle, angle)
                    )

        return intersection_points

    @classmethod
    def calculate_obstruction_angle(
        cls,
        point: Point3D,
        window: Window,
        angle_type: ANGLES = ANGLES.HORIZON
    ) -> float | None:
        """
        Calculate obstruction angle from window to point with filtering

        Delegates to ObstructionAngleCalculator for separation of concerns

        Args:
            point: Intersection point
            window: Window with center and normal
            angle_type: Type of angle (HORIZON or ZENITH)

        Returns:
            Obstruction angle in radians, or None if point is invalid
        """
        return ObstructionAngleCalculator.calculate(point, window, angle_type)

    @classmethod
    def _horizontal_distance(cls, point: Point3D, window: Window) -> float:
        """
        Calculate horizontal distance from window to point

        Delegates to GeometricDistanceCalculator for separation of concerns

        Args:
            point: Target point
            window: Window with center and normal

        Returns:
            Horizontal distance (negative if behind window)
        """
        return GeometricDistanceCalculator.horizontal_distance(point, window)

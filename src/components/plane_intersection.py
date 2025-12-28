from __future__ import annotations
from typing import List, Optional
import numpy as np
from src.components.geometry import Point3D, Vector3D, Triangle, Mesh, AngleCalculator
from src.components.constants import ANGLES, MathConstants
from src.components.vertical_plane import VerticalPlane
from src.components.intersection_point import IntersectionPoint
import logging

logger = logging.getLogger(__name__)


class PlaneTriangleIntersector:
    """
    Calculates plane-triangle intersections efficiently

    Uses the plane equation to find where triangle edges intersect
    the vertical plane, then calculates obstruction angles.
    """

    @staticmethod
    def point_plane_distance(point: Point3D, plane: VerticalPlane) -> float:
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
    def intersect_edge_with_plane(
        p1: Point3D,
        p2: Point3D,
        d1: float,
        d2: float
    ) -> Optional[Point3D]:
        """
        Find intersection point of edge (p1, p2) with plane

        Args:
            p1: First endpoint
            p2: Second endpoint
            plane: Vertical plane
            d1: Signed distance of p1 to plane
            d2: Signed distance of p2 to plane

        Returns:
            Intersection point if edge crosses plane, None otherwise
        """
        # Edge crosses plane if d1 and d2 have opposite signs
        if d1 * d2 > 0:
            return None

        # Edge lies on plane if both distances are ~0
        if abs(d1) < MathConstants.EPSILON.value and abs(d2) < MathConstants.EPSILON.value:
            return None

        # Calculate intersection parameter t
        # P = p1 + t * (p2 - p1)
        # At intersection: normal · (P - origin) = 0
        # t = d1 / (d1 - d2)
        t = d1 / (d1 - d2)

        # Calculate intersection point
        p1_arr = p1.to_array()
        p2_arr = p2.to_array()
        intersection = p1_arr + t * (p2_arr - p1_arr)

        return Point3D.from_array(intersection)

    @classmethod
    def intersect_triangle_with_plane(
        cls,
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
        d1 = cls.point_plane_distance(triangle.v1, plane)
        d2 = cls.point_plane_distance(triangle.v2, plane)
        d3 = cls.point_plane_distance(triangle.v3, plane)

        intersections = []

        # Check each edge
        edges = [
            (triangle.v1, triangle.v2, d1, d2),
            (triangle.v2, triangle.v3, d2, d3),
            (triangle.v3, triangle.v1, d3, d1)
        ]

        for p1, p2, dist1, dist2 in edges:
            intersection = cls.intersect_edge_with_plane(p1, p2, dist1, dist2)
            if intersection is not None:
                intersections.append(intersection)

        return intersections

    @classmethod
    def find_all_intersections(
        cls,
        mesh: Mesh,
        plane: VerticalPlane,
        window_center: Point3D,
        window_normal: Vector3D
    ) -> List[IntersectionPoint]:
        """
        Find all plane-triangle intersections with calculated angles

        Args:
            mesh: 3D mesh
            plane: Vertical viewing plane
            window_center: Window center point
            window_normal: Window viewing direction

        Returns:
            List of intersection points with angles
        """
        intersection_points = []

        for triangle in mesh.triangles:
            # Find intersection points for this triangle
            points = cls.intersect_triangle_with_plane(triangle, plane)

            for point in points:
                # Calculate obstruction angle for this intersection
                angle = cls.calculate_obstruction_angle(
                    point, window_center, window_normal
                )

                if angle is not None and angle > 0:
                    intersection_points.append(
                        IntersectionPoint(
                            point=point,
                            triangle=triangle,
                            angle=angle
                        )
                    )

        return intersection_points

    @staticmethod
    def calculate_obstruction_angle(
        point: Point3D,
        window_center: Point3D,
        window_normal: Vector3D,
        min_horizontal_distance: float = 1.0,
        max_angle_degrees: float = 89.0  # Allow very steep angles for slanted roofs close to window
    ) -> Optional[float]:
        """
        Calculate obstruction angle from window to point with filtering

        Args:
            point: Intersection point
            window_center: Window center
            window_normal: Window viewing direction
            min_horizontal_distance: Minimum horizontal distance (meters) to consider
            max_angle_degrees: Maximum valid angle (degrees) - filters out roof

        Returns:
            Obstruction angle in radians, or None if point is invalid
        """
        # Calculate vertical distance
        vertical_distance = point.z - window_center.z

        # Skip points below window (horizon should only see upward)
        if vertical_distance <= 0:
            return None

        # Calculate horizontal distance along viewing direction
        # Project vector from window to point onto horizontal plane
        point_vec = point.to_array() - window_center.to_array()

        # Get horizontal component of viewing direction
        normal_arr = window_normal.to_array()
        normal_horizontal = np.array([normal_arr[0], normal_arr[1], 0.0])
        normal_horizontal_mag = np.linalg.norm(normal_horizontal)

        if normal_horizontal_mag < MathConstants.EPSILON.value:
            # Viewing straight up or down
            point_horizontal = np.array([point_vec[0], point_vec[1], 0.0])
            horizontal_distance = float(np.linalg.norm(point_horizontal))
        else:
            # Project onto horizontal viewing direction
            normal_horizontal = normal_horizontal / normal_horizontal_mag
            horizontal_distance = float(np.dot(point_vec, normal_horizontal))

            # FILTER 0: Point must be IN FRONT of window (positive dot product)
            if horizontal_distance <= 0:
                return None  # Behind window

        # FILTER 1: Skip points too close horizontally (likely same building/roof)
        if horizontal_distance < min_horizontal_distance:
            return None

        # Calculate angle
        angle = AngleCalculator.call(
            vertical_distance, horizontal_distance, ANGLES.ZENITH
        )

        if angle is None:
            return None

        # FILTER 2: Skip angles too steep (likely roof, not horizon obstruction)
        max_angle_rad = np.radians(max_angle_degrees)
        if angle > max_angle_rad:
            return None

        return angle




from __future__ import annotations
from typing import List, Optional
import numpy as np
from src.components.geometry import Point3D, Triangle, Mesh
from src.components.geometry.vertical_plane import VerticalPlane
from src.components.geometry.intersection_point import IntersectionPoint
from src.components.calculators import AngleCalculator
from src.server.base.constants import ANGLES, MathConstants
from src.components.models import Window
import logging

from src.utils.settings import Settings

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

        # Check each edge
        edges = [
            (triangle.v1, triangle.v2, d1, d2),
            (triangle.v2, triangle.v3, d2, d3),
            (triangle.v3, triangle.v1, d3, d1)
        ]
        intersections = [cls.intersect_edge_with_plane(p1, p2, dist1, dist2) for p1, p2, dist1, dist2 in edges]

        return [ii for ii in intersections if not ii is None]

    @classmethod
    def find_all_intersections(
        cls,
        mesh: Mesh,
        plane: VerticalPlane,
        window: Window
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

        def _intersect_triangle(triangle, plane)->List[IntersectionPoint]:
            points = cls.intersect_triangle_with_plane(triangle, plane)
            angles = [cls.calculate_obstruction_angle(p, window) for p in points]
            return [IntersectionPoint(p, triangle, a) for a,p in zip(angles, points) if not a is None and a > 0]

        intersection_points = [_intersect_triangle(triangle, plane) for triangle in mesh.triangles]
        return [item for sublist in intersection_points for item in sublist]

    @classmethod
    def calculate_obstruction_angle(
        cls,
        point: Point3D,
        window:Window,
        angle_type = ANGLES.HORIZON
        
    ) -> Optional[float]:
        """
        Calculate obstruction angle from window to point with filtering

        Args:
            point: Intersection point
            window_center: Window center
            window_normal: Window viewing direction
            angle: type of the angle to calculate, member of ANGLES

        Returns:
            Obstruction angle in radians, or None if point is invalid
        """
        # Calculate vertical distance
        vertical_distance = point.z - window.center.z
        # Skip points below window (both horizon and zenith should only look upwards)
        if vertical_distance <= 0:
            return None
        
        # Calculate horizontal distance along viewing direction
        # Project vector from window to point onto horizontal plane
        
        horizontal_distance = cls._horizontal_distance( point, window)
        _dists = {
            ANGLES.HORIZON: Settings.min_horizontal_distance,
            ANGLES.ZENITH: 0
        }
        
        if horizontal_distance < _dists.get(angle_type, 0):
            return None
        
        angle = AngleCalculator.call(
            vertical_distance, horizontal_distance, angle_type
        )
        
        if angle is None:
            return None

        # FILTER 2: Skip angles too steep (likely roof, not horizon obstruction)
        max_angle_rad = np.radians(Settings.max_angle_degrees)
        if angle > max_angle_rad:
            return None

        return angle
    
    @classmethod
    def _horizontal_distance(cls, point:Point3D, window: Window):
        point_vec = point.to_array() - window.center.to_array()
        # Get horizontal component of viewing direction
        normal_arr = window.normal.to_array()
        normal_horizontal = np.array([normal_arr[0], normal_arr[1], 0.0])
        magnitude = np.linalg.norm(normal_horizontal)

        if magnitude < MathConstants.EPSILON.value:
            # Viewing straight up or down
            point_horizontal = np.array([point_vec[0], point_vec[1], 0.0])
            return float(np.linalg.norm(point_horizontal))
        
        # Project onto horizontal viewing direction
        normal_horizontal = normal_horizontal / magnitude
        return float(np.dot(point_vec, normal_horizontal))




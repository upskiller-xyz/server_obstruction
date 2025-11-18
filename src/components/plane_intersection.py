"""
Plane-Triangle Intersection Calculator

Efficient obstruction calculation using plane-triangle intersections.
Instead of projecting all mesh points, we find only the triangles that
intersect the vertical viewing plane and calculate angles directly.
"""
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import time
from src.components.geometry import Point3D, Vector3D, Triangle, Mesh, AngleCalculator
from src.components.constants import MathConstants
import logging

logger = logging.getLogger(__name__)


class TriangleFilter:
    """Filters triangles based on spatial criteria for efficient obstruction calculation"""

    @staticmethod
    def filter_for_horizon(
        triangles: Tuple[Triangle, ...],
        window_center: Point3D,
        window_normal: Vector3D,
        min_horizontal_distance: float = 2.0
    ) -> List[Triangle]:
        """
        Filter triangles relevant for horizon obstruction calculation

        Criteria:
        1. Triangle must be in front of window (following view direction)
        2. At least min_horizontal_distance away horizontally
        3. Triangle's highest point must be above window center

        Args:
            triangles: All mesh triangles
            window_center: Window center point
            window_normal: Window viewing direction
            min_horizontal_distance: Minimum horizontal distance (meters)

        Returns:
            Filtered list of relevant triangles
        """
        filtered = []
        stats = {'below': 0, 'behind': 0, 'too_close': 0, 'kept': 0}

        normal_arr = window_normal.to_array()
        normal_horizontal = np.array([normal_arr[0], normal_arr[1], 0.0])
        normal_horizontal_mag = np.linalg.norm(normal_horizontal)

        if normal_horizontal_mag < MathConstants.EPSILON:
            # Viewing straight up/down - use all horizontal distances
            normal_horizontal = None
        else:
            normal_horizontal = normal_horizontal / normal_horizontal_mag

        for triangle in triangles:
            # Get all three vertices
            vertices = triangle.vertices()

            # Check if highest vertex is above window center
            max_z = max(v.z for v in vertices)
            if max_z <= window_center.z:
                stats['below'] += 1
                continue  # Entire triangle below window

            # Check if at least one vertex is in front and far enough
            has_valid_vertex = False
            all_behind = True
            all_too_close = True

            for vertex in vertices:
                vec_to_vertex = vertex.to_array() - window_center.to_array()

                if normal_horizontal is not None:
                    # Check if in front (positive dot product) AND far enough
                    forward_distance = float(np.dot(vec_to_vertex, normal_horizontal))

                    if forward_distance > 0:
                        all_behind = False

                    # Must be in front (forward_distance > 0) AND far enough (> min_horizontal_distance)
                    if forward_distance <= 0:
                        continue  # Behind window

                    if forward_distance >= min_horizontal_distance:
                        all_too_close = False
                        has_valid_vertex = True
                        break
                else:
                    # No horizontal normal - check Euclidean distance
                    horiz_vec = np.array([vec_to_vertex[0], vec_to_vertex[1], 0.0])
                    horiz_dist = float(np.linalg.norm(horiz_vec))
                    if horiz_dist >= min_horizontal_distance:
                        all_too_close = False
                        has_valid_vertex = True
                        break

            if has_valid_vertex:
                filtered.append(triangle)
                stats['kept'] += 1
            elif all_behind:
                stats['behind'] += 1
            elif all_too_close:
                stats['too_close'] += 1

        logger.info(
            f"        [HORIZON-FILTER] Kept {stats['kept']}/{len(triangles)} - "
            f"Filtered: {stats['below']} below window, {stats['behind']} behind, {stats['too_close']} too close (<{min_horizontal_distance}m)"
        )

        return filtered

    @staticmethod
    def filter_for_zenith(
        triangles: Tuple[Triangle, ...],
        window_center: Point3D,
        window_normal: Vector3D
    ) -> List[Triangle]:
        """
        Filter triangles relevant for zenith obstruction calculation

        Criteria:
        1. Triangle must be above window center (Z axis)
        2. Triangle must be at least partially forward (not entirely behind window)

        Args:
            triangles: All mesh triangles
            window_center: Window center point
            window_normal: Window viewing direction

        Returns:
            Filtered list of relevant triangles
        """
        filtered = []
        normal_arr = window_normal.to_array()
        normal_horizontal = np.array([normal_arr[0], normal_arr[1], 0.0])
        normal_horizontal_mag = np.linalg.norm(normal_horizontal)

        if normal_horizontal_mag < MathConstants.EPSILON:
            normal_horizontal = None
        else:
            normal_horizontal = normal_horizontal / normal_horizontal_mag

        for triangle in triangles:
            vertices = triangle.vertices()

            # Check if at least part of triangle is above window center
            # For slanted roofs, we need triangles that have ANY vertex above window
            max_z = max(v.z for v in vertices)
            if max_z <= window_center.z:
                continue  # Entire triangle at or below window

            # Check if at least one vertex is in front (or at) window
            has_forward_vertex = False
            for vertex in vertices:
                vec_to_vertex = vertex.to_array() - window_center.to_array()

                if normal_horizontal is not None:
                    forward_distance = float(np.dot(vec_to_vertex, normal_horizontal))
                    if forward_distance >= -MathConstants.EPSILON:  # Allow slightly behind
                        has_forward_vertex = True
                        break
                else:
                    # No horizontal normal - accept all
                    has_forward_vertex = True
                    break

            if has_forward_vertex:
                filtered.append(triangle)

        return filtered


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
    def from_window(cls, window_center: Point3D, window_normal: Vector3D) -> 'VerticalPlane':
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
        direction_arr = window_normal.to_array()
        up = np.array([0.0, 0.0, 1.0])

        normal_arr = np.cross(direction_arr, up)
        normal_mag = np.linalg.norm(normal_arr)

        if normal_mag < MathConstants.EPSILON:
            # Direction is parallel to up (looking straight up/down)
            # Use forward direction as reference
            forward = np.array([1.0, 0.0, 0.0])
            normal_arr = np.cross(direction_arr, forward)
            normal_mag = np.linalg.norm(normal_arr)

        normal_arr = normal_arr / normal_mag

        return cls(
            origin=window_center,
            direction=window_normal,
            normal=Vector3D.from_array(normal_arr)
        )


@dataclass(frozen=True)
class IntersectionPoint:
    """Point where plane intersects triangle, with metadata"""
    point: Point3D
    triangle: Triangle
    angle: float  # Obstruction angle in radians


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
        plane: VerticalPlane,
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
        if abs(d1) < MathConstants.EPSILON and abs(d2) < MathConstants.EPSILON:
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
            intersection = cls.intersect_edge_with_plane(p1, p2, plane, dist1, dist2)
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

        if normal_horizontal_mag < MathConstants.EPSILON:
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
        angle = AngleCalculator.calculate_obstruction_angle(
            vertical_distance, horizontal_distance
        )

        if angle is None:
            return None

        # FILTER 2: Skip angles too steep (likely roof, not horizon obstruction)
        max_angle_rad = np.radians(max_angle_degrees)
        if angle > max_angle_rad:
            return None

        return angle


class HorizonIntersectionCalculator:
    """
    Efficient horizon obstruction calculator using plane-triangle intersections

    Instead of projecting all points, finds only triangles that intersect
    the viewing plane and calculates angles directly.

    OPTIMIZATION: Sorts intersection points by Z coordinate (highest first)
    and uses early termination - once we find a point with angle >= max seen,
    we can stop checking lower points.
    """

    @staticmethod
    def calculate_max_obstruction_angle(
        mesh: Mesh,
        window_center: Point3D,
        window_normal: Vector3D
    ) -> Tuple[Optional[float], Optional[Point3D], int]:
        """
        Calculate maximum obstruction angle using plane intersections with early termination

        Algorithm:
        1. Find all plane-triangle intersections
        2. Sort by Z coordinate (highest first) - higher points more likely to have larger angles
        3. Calculate angles starting from highest
        4. Use early termination: once angle starts decreasing, we found the max

        Args:
            mesh: 3D mesh
            window_center: Window center point
            window_normal: Window viewing direction (unit vector)

        Returns:
            Tuple of (max_angle_radians, highest_point, intersection_count)
            Returns (None, None, 0) if no obstruction found
        """
        import time
        import logging
        logger = logging.getLogger(__name__)

        algo_start = time.time()

        # Step 0: Filter relevant triangles BEFORE intersection calculations
        step_start = time.time()
        total_triangles = len(mesh.triangles)
        relevant_triangles = TriangleFilter.filter_for_horizon(
            mesh.triangles, window_center, window_normal, min_horizontal_distance=1.0
        )
        filter_time = time.time() - step_start
        logger.info(
            f"        [HORIZON-EFFICIENT] Step 0/4: Filtered {len(relevant_triangles)}/{total_triangles} triangles "
            f"in {filter_time*1000:.2f}ms ({100*len(relevant_triangles)/total_triangles:.1f}% remaining)"
        )

        if not relevant_triangles:
            logger.info(f"        [HORIZON-EFFICIENT] No relevant triangles found after filtering")
            return None, None, 0

        # Step 1: Create vertical plane through window in viewing direction
        step_start = time.time()
        plane = VerticalPlane.from_window(window_center, window_normal)
        logger.info(f"        [HORIZON-EFFICIENT] Step 1/4: Plane created in {(time.time()-step_start)*1000:.2f}ms")

        # Step 2: Find plane-triangle intersections (only for filtered triangles)
        step_start = time.time()
        intersection_points = []
        triangles_checked = 0

        for triangle in relevant_triangles:
            triangles_checked += 1
            # Find intersection points for this triangle
            points = PlaneTriangleIntersector.intersect_triangle_with_plane(triangle, plane)

            for point in points:
                # Filter points: must be above window
                if point.z > window_center.z:
                    intersection_points.append((point, triangle))

        logger.info(
            f"        [HORIZON-EFFICIENT] Step 2/4: Found {len(intersection_points)} intersections "
            f"(checked {triangles_checked} triangles) in {(time.time()-step_start)*1000:.2f}ms"
        )

        if not intersection_points:
            logger.info(f"        [HORIZON-EFFICIENT] No intersections found, total time: {(time.time()-algo_start)*1000:.2f}ms")
            return None, None, 0

        total_intersections = len(intersection_points)

        # Step 3: Calculate angles for ALL points (no early termination)
        # The highest point by Z doesn't necessarily give the largest obstruction angle
        # A lower point that's closer horizontally might have a larger angle
        step_start = time.time()
        max_angle = 0.0
        max_point = None
        points_checked = 0
        filtered_by_angle = 0

        for point, triangle in intersection_points:
            # Calculate angle for this point
            angle = PlaneTriangleIntersector.calculate_obstruction_angle(
                point, window_center, window_normal
            )

            points_checked += 1

            if angle is None:
                filtered_by_angle += 1
            elif angle > max_angle:
                max_angle = angle
                max_point = point

        logger.info(
            f"        [HORIZON-EFFICIENT] Step 3/4: Calculated angles for {points_checked} points "
            f"({filtered_by_angle} filtered by angle/distance constraints) in {(time.time()-step_start)*1000:.2f}ms"
        )

        if max_point is None:
            logger.info(f"        [HORIZON-EFFICIENT] No valid angles found, total time: {(time.time()-algo_start)*1000:.2f}ms")
            return None, None, total_intersections

        total_time = time.time() - algo_start
        logger.info(f"        [HORIZON-EFFICIENT] ✓ TOTAL TIME: {total_time*1000:.2f}ms")

        return max_angle, max_point, total_intersections


class ZenithIntersectionCalculator:
    """
    Efficient zenith angle calculator using plane-triangle intersections

    Similar to horizon calculator but looks for overhead obstructions.
    """

    @staticmethod
    def calculate_max_zenith_angle(
        mesh: Mesh,
        window_center: Point3D,
        window_normal: Vector3D
    ) -> Tuple[Optional[float], Optional[Point3D], int]:
        """
        Calculate maximum zenith angle using plane intersections

        Args:
            mesh: 3D mesh
            window_center: Window center point
            window_normal: Window viewing direction (unit vector)

        Returns:
            Tuple of (max_angle_radians, furthest_point, intersection_count)
        """
        import time
        import logging
        logger = logging.getLogger(__name__)

        algo_start = time.time()

        # Step 0: Filter relevant triangles BEFORE intersection calculations
        step_start = time.time()
        total_triangles = len(mesh.triangles)
        relevant_triangles = TriangleFilter.filter_for_zenith(
            mesh.triangles, window_center, window_normal
        )
        filter_time = time.time() - step_start
        logger.info(
            f"        [ZENITH-EFFICIENT] Step 0/4: Filtered {len(relevant_triangles)}/{total_triangles} triangles "
            f"in {filter_time*1000:.2f}ms ({100*len(relevant_triangles)/total_triangles:.1f}% remaining)"
        )

        if not relevant_triangles:
            logger.info(f"        [ZENITH-EFFICIENT] No relevant triangles found after filtering")
            return None, None, 0

        # Step 1: Create plane
        step_start = time.time()
        plane = VerticalPlane.from_window(window_center, window_normal)
        logger.info(f"        [ZENITH-EFFICIENT] Step 1/4: Plane created in {(time.time()-step_start)*1000:.2f}ms")

        # Step 2: Find intersections (only for filtered triangles)
        step_start = time.time()
        intersection_points = []
        triangles_checked = 0
        for triangle in relevant_triangles:
            triangles_checked += 1
            points = PlaneTriangleIntersector.intersect_triangle_with_plane(triangle, plane)
            for point in points:
                if point.z > window_center.z:
                    intersection_points.append((point, triangle))

        logger.info(
            f"        [ZENITH-EFFICIENT] Step 2/4: Found {len(intersection_points)} intersections "
            f"(checked {triangles_checked} triangles) in {(time.time()-step_start)*1000:.2f}ms"
        )

        if not intersection_points:
            logger.info(f"        [ZENITH-EFFICIENT] No intersections found, total time: {(time.time()-algo_start)*1000:.2f}ms")
            return None, None, 0

        total_intersections = len(intersection_points)

        # Step 3: Calculate angles
        # For zenith: we want the MINIMUM angle (closest overhead obstruction)
        # Zenith angle is measured from vertical (0° = straight up, 90° = horizontal)
        step_start = time.time()
        min_zenith_angle = float('inf')
        closest_point = None
        max_zenith_degrees = 75.0  # Filter out points too far from vertical
        max_zenith_rad = np.radians(max_zenith_degrees)

        for point, _ in intersection_points:
            vertical_distance = point.z - window_center.z

            # Skip points not above window
            if vertical_distance <= 0:
                continue

            point_vec = point.to_array() - window_center.to_array()
            normal_arr = window_normal.to_array()
            normal_horizontal = np.array([normal_arr[0], normal_arr[1], 0.0])
            normal_horizontal_mag = np.linalg.norm(normal_horizontal)

            if normal_horizontal_mag < MathConstants.EPSILON:
                point_horizontal = np.array([point_vec[0], point_vec[1], 0.0])
                horizontal_distance = float(np.linalg.norm(point_horizontal))
            else:
                normal_horizontal = normal_horizontal / normal_horizontal_mag
                horizontal_distance = abs(float(np.dot(point_vec, normal_horizontal)))

            if horizontal_distance < MathConstants.EPSILON:
                # Point directly above - zenith angle = 0
                zenith_angle = 0.0
            else:
                elevation_angle = float(np.arctan(vertical_distance / horizontal_distance))
                zenith_angle = (np.pi / 2) - elevation_angle

            # Filter: skip angles > 75° (too far from vertical)
            if zenith_angle > max_zenith_rad:
                logger.debug(f"        [ZENITH-EFFICIENT] Filtered out point at ({point.x:.2f}, {point.y:.2f}, {point.z:.2f}) with angle {np.degrees(zenith_angle):.2f}° (> {max_zenith_degrees}°)")
                continue

            # Keep MINIMUM zenith angle (closest to vertical = most restrictive overhead obstruction)
            if zenith_angle < min_zenith_angle:
                min_zenith_angle = zenith_angle
                closest_point = point

        logger.info(
            f"        [ZENITH-EFFICIENT] Step 3/4: Calculated angles for {total_intersections} points "
            f"in {(time.time()-step_start)*1000:.2f}ms"
        )

        if closest_point is None or min_zenith_angle == float('inf'):
            logger.info(f"        [ZENITH-EFFICIENT] No valid angles found, total time: {(time.time()-algo_start)*1000:.2f}ms")
            return None, None, total_intersections

        total_time = time.time() - algo_start
        logger.info(f"        [ZENITH-EFFICIENT] ✓ TOTAL TIME: {total_time*1000:.2f}ms")

        return min_zenith_angle, closest_point, total_intersections

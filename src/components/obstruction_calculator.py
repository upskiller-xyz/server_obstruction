from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from src.components.raytracing_models import ProjectedPoint, RaytraceResult
from src.components.geometry import Point3D, Vector3D


class IObstructionCalculator(ABC):
    """Interface for obstruction angle calculations"""

    @abstractmethod
    def calculate_obstruction_angle(
        self,
        projected_points: List[ProjectedPoint],
        reference_height: float,
        window_center: Optional[Point3D] = None,
        window_normal: Optional[Vector3D] = None
    ) -> RaytraceResult:
        """
        Calculate obstruction angle from projected points

        Args:
            projected_points: List of 2D projected points on plane
            reference_height: Reference height (window center v-coordinate)
            window_center: 3D position of window center
            window_normal: Viewing direction (unit vector)

        Returns:
            RaytraceResult with obstruction angle and metadata
        """
        pass


class MaxHeightObstructionCalculator(IObstructionCalculator):
    """
    Calculates obstruction angle based on the highest point in the projection

    The obstruction angle is measured from the horizontal line at the reference
    height to the line connecting the reference point to the highest point.
    """

    def calculate_obstruction_angle(
        self,
        projected_points: List[ProjectedPoint],
        reference_height: float = 0.0,
        window_center: Optional[Point3D] = None,
        window_normal: Optional[Vector3D] = None
    ) -> RaytraceResult:
        """
        Calculate obstruction angle from the highest projected point

        The angle is calculated in the vertical viewing plane:
        - Find the highest point (maximum v coordinate on projection)
        - Calculate vertical distance: highest_point.y - window_center.y
        - Calculate horizontal distance along viewing direction: dot(point - center, normal)
        - Angle = arctan(vertical_distance / horizontal_distance)

        Args:
            projected_points: Points projected onto the plane
            reference_height: Reference height on the plane (typically 0 for window center)
            window_center: 3D position of window center
            window_normal: Viewing direction (unit vector)

        Returns:
            RaytraceResult with angle and metadata
        """
        if not projected_points:
            return RaytraceResult(
                obstruction_angle_degrees=0.0,
                obstruction_angle_radians=0.0,
                highest_point=None,
                projected_point_count=0
            )

        # Filter points: check if mesh triangles intersect the projection plane
        if window_center is not None and window_normal is not None:
            from src.components.geometry import Mesh

            window_arr = window_center.to_array()
            normal_arr = window_normal.to_array()

            # Calculate plane normal (perpendicular to view direction and world up)
            world_up_arr = np.array([0.0, 1.0, 0.0])
            plane_normal_arr = np.cross(normal_arr, world_up_arr)
            plane_normal_mag = np.linalg.norm(plane_normal_arr)

            if plane_normal_mag < 1e-6:
                # Looking straight up/down
                world_forward_arr = np.array([1.0, 0.0, 0.0])
                plane_normal_arr = np.cross(normal_arr, world_forward_arr)

            plane_normal_arr = plane_normal_arr / np.linalg.norm(plane_normal_arr)

            import logging
            logger = logging.getLogger(__name__)

            # Check each triangle to see if it crosses the plane
            # A triangle crosses the plane if its vertices are on different sides
            valid_points = []

            # Group projected points by triangles (every 3 points = 1 triangle)
            for i in range(0, len(projected_points), 3):
                if i + 2 >= len(projected_points):
                    break

                triangle_points = projected_points[i:i+3]

                # Calculate signed distances from vertices to plane
                signed_distances = []
                all_in_front = True

                for proj_point in triangle_points:
                    point_arr = proj_point.original.to_array()
                    point_to_window = point_arr - window_arr

                    # Distance along viewing direction
                    dist_along_view = float(np.dot(point_to_window, normal_arr))

                    # Signed distance to plane
                    dist_to_plane = float(np.dot(point_to_window, plane_normal_arr))
                    signed_distances.append(dist_to_plane)

                    if dist_along_view <= 1e-6:
                        all_in_front = False
                        break

                # Skip if any vertex is behind the window
                if not all_in_front:
                    continue

                # Check if triangle crosses the plane (vertices on different sides)
                # or if any vertex is very close to the plane
                min_dist = min(signed_distances)
                max_dist = max(signed_distances)

                # Triangle intersects plane if min and max have different signs
                # or if any vertex is within threshold of plane
                PLANE_THRESHOLD = 0.1

                if (min_dist < PLANE_THRESHOLD and max_dist > -PLANE_THRESHOLD):
                    # Triangle intersects or is very close to the plane
                    valid_points.extend(triangle_points)
                    logger.debug(f"Triangle vertices at distances {signed_distances}: INTERSECTS PLANE")
                else:
                    logger.debug(f"Triangle vertices at distances {signed_distances}: DOES NOT INTERSECT")

            # If no valid points (mesh doesn't intersect plane), return zero angle
            if not valid_points:
                return RaytraceResult(
                    obstruction_angle_degrees=0.0,
                    obstruction_angle_radians=0.0,
                    highest_point=None,
                    projected_point_count=len(projected_points)
                )

            projected_points = valid_points

        # Filter to only vertical or near-vertical surfaces (walls, buildings)
        vertical_points = []

        # Process triangles (every 3 points = 1 triangle)
        for i in range(0, len(projected_points), 3):
            if i + 2 >= len(projected_points):
                break

            triangle_points = projected_points[i:i+3]

            # Calculate triangle surface normal
            p0 = triangle_points[0].original.to_array()
            p1 = triangle_points[1].original.to_array()
            p2 = triangle_points[2].original.to_array()

            # Compute edges
            edge1 = p1 - p0
            edge2 = p2 - p0

            # Cross product gives surface normal
            surface_normal = np.cross(edge1, edge2)
            surface_normal_mag = np.linalg.norm(surface_normal)

            if surface_normal_mag < 1e-6:
                # Degenerate triangle
                continue

            surface_normal = surface_normal / surface_normal_mag

            # Check if surface is vertical (normal points mostly horizontally)
            # Y-component should be small (close to 0)
            y_component = abs(surface_normal[1])

            # Threshold: surface is "vertical" if normal Y-component < 0.3 (≈73° from horizontal)
            VERTICAL_THRESHOLD = 0.3

            if y_component < VERTICAL_THRESHOLD:
                # This is a vertical surface
                vertical_points.extend(triangle_points)

        if not vertical_points:
            return RaytraceResult(
                obstruction_angle_degrees=0.0,
                obstruction_angle_radians=0.0,
                highest_point=None,
                projected_point_count=len(projected_points)
            )

        # Find the highest point on vertical surfaces only
        highest_projected = max(vertical_points, key=lambda p: p.height)
        highest_3d = highest_projected.original

        # Calculate using 3D coordinates if window_center and normal provided
        if window_center is not None and window_normal is not None:
            # Vertical distance (height difference)
            vertical_distance = highest_3d.y - window_center.y

            # If highest point is below window, no obstruction
            if vertical_distance <= 0:
                return RaytraceResult(
                    obstruction_angle_degrees=0.0,
                    obstruction_angle_radians=0.0,
                    highest_point=highest_3d,
                    projected_point_count=len(projected_points)
                )

            # Horizontal distance: project onto horizontal plane (XZ plane)
            # Use only the horizontal component of the viewing direction
            normal_arr = window_normal.to_array()
            normal_horizontal = normal_arr.copy()
            normal_horizontal[1] = 0.0  # Remove Y component
            normal_horizontal_mag = np.linalg.norm(normal_horizontal)

            if normal_horizontal_mag < 1e-6:
                # Viewing straight up or down, use direct horizontal distance
                point_vec = highest_3d.to_array() - window_center.to_array()
                point_horizontal = point_vec.copy()
                point_horizontal[1] = 0.0
                horizontal_distance = float(np.linalg.norm(point_horizontal))
            else:
                # Normalize horizontal viewing direction
                normal_horizontal = normal_horizontal / normal_horizontal_mag

                # Project point vector onto horizontal viewing direction
                point_vec = highest_3d.to_array() - window_center.to_array()
                horizontal_distance = abs(float(np.dot(point_vec, normal_horizontal)))

            # Handle case where point is directly above (infinite angle)
            if horizontal_distance < 1e-6:
                angle_radians = np.pi / 2  # 90 degrees
            else:
                # Calculate angle using arctan
                angle_radians = float(np.arctan(vertical_distance / horizontal_distance))

        else:
            # Fallback: use projection coordinates (legacy behavior)
            vertical_distance = highest_projected.height - reference_height

            if vertical_distance <= 0:
                return RaytraceResult(
                    obstruction_angle_degrees=0.0,
                    obstruction_angle_radians=0.0,
                    highest_point=highest_3d,
                    projected_point_count=len(projected_points)
                )

            horizontal_distance = abs(highest_projected.u) if abs(highest_projected.u) > 1e-6 else 1e-6
            angle_radians = float(np.arctan(vertical_distance / horizontal_distance))

        angle_degrees = float(np.degrees(angle_radians))

        return RaytraceResult(
            obstruction_angle_degrees=angle_degrees,
            obstruction_angle_radians=angle_radians,
            highest_point=highest_3d,
            projected_point_count=len(projected_points)
        )


class ZenithAngleCalculator(IObstructionCalculator):
    """
    Calculates zenith angle based on the lowest overhead point in the projection

    The zenith angle is measured from the vertical (zenith) downward to the
    lowest overhead obstruction (like balconies or roofs above the window).
    Angle is measured from 90° (straight up) downward.
    """

    def calculate_obstruction_angle(
        self,
        projected_points: List[ProjectedPoint],
        reference_height: float = 0.0,
        window_center: Optional[Point3D] = None,
        window_normal: Optional[Vector3D] = None
    ) -> RaytraceResult:
        """
        Calculate zenith angle from the lowest overhead projected point

        The angle is calculated in the vertical viewing plane:
        - Find the lowest overhead point (minimum v coordinate, but still above window)
        - Calculate vertical distance: window_center.y - lowest_point.y (negative)
        - Calculate horizontal distance along viewing direction
        - Angle = 90° - arctan(horizontal_distance / abs(vertical_distance))

        Args:
            projected_points: Points projected onto the plane
            reference_height: Reference height on the plane (typically 0 for window center)
            window_center: 3D position of window center
            window_normal: Viewing direction (unit vector)

        Returns:
            RaytraceResult with zenith angle and metadata
        """
        if not projected_points:
            return RaytraceResult(
                obstruction_angle_degrees=0.0,
                obstruction_angle_radians=0.0,
                highest_point=None,
                projected_point_count=0
            )

        # Filter points: check if mesh triangles intersect the projection plane
        if window_center is not None and window_normal is not None:
            window_arr = window_center.to_array()
            normal_arr = window_normal.to_array()

            # Calculate plane normal
            world_up_arr = np.array([0.0, 1.0, 0.0])
            plane_normal_arr = np.cross(normal_arr, world_up_arr)
            plane_normal_mag = np.linalg.norm(plane_normal_arr)

            if plane_normal_mag < 1e-6:
                world_forward_arr = np.array([1.0, 0.0, 0.0])
                plane_normal_arr = np.cross(normal_arr, world_forward_arr)

            plane_normal_arr = plane_normal_arr / np.linalg.norm(plane_normal_arr)

            valid_points = []
            PLANE_THRESHOLD = 2.5  # Increased to capture triangles near the plane

            # Check each triangle
            for i in range(0, len(projected_points), 3):
                if i + 2 >= len(projected_points):
                    break

                triangle_points = projected_points[i:i+3]
                signed_distances = []
                all_in_front = True

                for proj_point in triangle_points:
                    point_arr = proj_point.original.to_array()
                    point_to_window = point_arr - window_arr
                    dist_along_view = float(np.dot(point_to_window, normal_arr))
                    dist_to_plane = float(np.dot(point_to_window, plane_normal_arr))
                    signed_distances.append(dist_to_plane)

                    if dist_along_view <= 1e-6:
                        all_in_front = False
                        break

                if not all_in_front:
                    continue

                min_dist = min(signed_distances)
                max_dist = max(signed_distances)

                if (min_dist < PLANE_THRESHOLD and max_dist > -PLANE_THRESHOLD):
                    valid_points.extend(triangle_points)

            if not valid_points:
                return RaytraceResult(
                    obstruction_angle_degrees=0.0,
                    obstruction_angle_radians=0.0,
                    highest_point=None,
                    projected_point_count=len(projected_points)
                )

            projected_points = valid_points

        # Find overhead points that belong to horizontal surfaces
        # Filter by triangle surface normal - only include horizontal-ish surfaces
        overhead_points = []

        # Process triangles (every 3 points = 1 triangle)
        for i in range(0, len(projected_points), 3):
            if i + 2 >= len(projected_points):
                break

            triangle_points = projected_points[i:i+3]

            # Check if all vertices are above window
            all_above = all(p.original.y > window_center.y for p in triangle_points)
            if not all_above:
                continue

            # Calculate triangle surface normal
            p0 = triangle_points[0].original.to_array()
            p1 = triangle_points[1].original.to_array()
            p2 = triangle_points[2].original.to_array()

            # Compute edges
            edge1 = p1 - p0
            edge2 = p2 - p0

            # Cross product gives surface normal
            surface_normal = np.cross(edge1, edge2)
            surface_normal_mag = np.linalg.norm(surface_normal)

            if surface_normal_mag < 1e-6:
                # Degenerate triangle
                continue

            surface_normal = surface_normal / surface_normal_mag

            # Check if surface is horizontal (normal points mostly up or down)
            # Y-component should be close to ±1
            y_component = abs(surface_normal[1])

            # Threshold: surface is "horizontal" if normal Y-component > 0.7 (≈45° tolerance)
            HORIZONTAL_THRESHOLD = 0.7

            if y_component > HORIZONTAL_THRESHOLD:
                # This is a horizontal surface
                overhead_points.extend(triangle_points)

        if not overhead_points:
            return RaytraceResult(
                obstruction_angle_degrees=0.0,
                obstruction_angle_radians=0.0,
                highest_point=None,
                projected_point_count=len(projected_points)
            )

        import logging
        logger = logging.getLogger(__name__)

        # Find point with maximum horizontal distance from window
        # For zenith, we want the furthest point along the viewing direction (not just horizontal)
        def get_distance_along_view(p: ProjectedPoint) -> float:
            if window_center is not None and window_normal is not None:
                normal_arr = window_normal.to_array()
                point_vec = p.original.to_array() - window_center.to_array()
                # Project onto horizontal component of viewing direction
                normal_horizontal = normal_arr.copy()
                normal_horizontal[1] = 0.0
                normal_horizontal_mag = np.linalg.norm(normal_horizontal)

                if normal_horizontal_mag < 1e-6:
                    # Looking straight up/down, use total horizontal distance
                    point_horizontal = point_vec.copy()
                    point_horizontal[1] = 0.0
                    return float(np.linalg.norm(point_horizontal))
                else:
                    # Distance along horizontal viewing direction
                    normal_horizontal = normal_horizontal / normal_horizontal_mag
                    dist = float(np.dot(point_vec, normal_horizontal))
                    logger.info(f"Point ({p.original.x:.1f}, {p.original.y:.1f}, {p.original.z:.1f}) -> distance along view: {dist:.2f}")
                    return dist
            return p.u

        furthest_overhead = max(overhead_points, key=get_distance_along_view)
        logger.info(f"Selected furthest point: ({furthest_overhead.original.x:.1f}, {furthest_overhead.original.y:.1f}, {furthest_overhead.original.z:.1f})")
        lowest_3d = furthest_overhead.original

        # Calculate using 3D coordinates
        if window_center is not None and window_normal is not None:
            # Vertical distance (negative because point is above)
            vertical_distance = lowest_3d.y - window_center.y

            # Must be above window
            if vertical_distance <= 0:
                return RaytraceResult(
                    obstruction_angle_degrees=0.0,
                    obstruction_angle_radians=0.0,
                    highest_point=lowest_3d,
                    projected_point_count=len(projected_points)
                )

            # Horizontal distance
            normal_arr = window_normal.to_array()
            normal_horizontal = normal_arr.copy()
            normal_horizontal[1] = 0.0
            normal_horizontal_mag = np.linalg.norm(normal_horizontal)

            if normal_horizontal_mag < 1e-6:
                point_vec = lowest_3d.to_array() - window_center.to_array()
                point_horizontal = point_vec.copy()
                point_horizontal[1] = 0.0
                horizontal_distance = float(np.linalg.norm(point_horizontal))
            else:
                normal_horizontal = normal_horizontal / normal_horizontal_mag
                point_vec = lowest_3d.to_array() - window_center.to_array()
                horizontal_distance = abs(float(np.dot(point_vec, normal_horizontal)))

            # Calculate zenith angle: 90° - arctan(horizontal / vertical)
            if horizontal_distance < 1e-6:
                # Point directly overhead
                angle_radians = 0.0
            else:
                elevation_angle = float(np.arctan(vertical_distance / horizontal_distance))
                angle_radians = (np.pi / 2) - elevation_angle

        else:
            # Fallback: use projection coordinates
            vertical_distance = lowest_overhead.height - reference_height

            if vertical_distance <= 0:
                return RaytraceResult(
                    obstruction_angle_degrees=0.0,
                    obstruction_angle_radians=0.0,
                    highest_point=lowest_3d,
                    projected_point_count=len(projected_points)
                )

            horizontal_distance = abs(lowest_overhead.u) if abs(lowest_overhead.u) > 1e-6 else 1e-6
            elevation_angle = float(np.arctan(vertical_distance / horizontal_distance))
            angle_radians = (np.pi / 2) - elevation_angle

        angle_degrees = float(np.degrees(angle_radians))

        return RaytraceResult(
            obstruction_angle_degrees=angle_degrees,
            obstruction_angle_radians=angle_radians,
            highest_point=lowest_3d,
            projected_point_count=len(projected_points)
        )


class WorstCaseObstructionCalculator(IObstructionCalculator):
    """
    Calculates worst-case obstruction angle considering all points

    For each projected point, calculates its obstruction angle and returns
    the maximum angle found.
    """

    def calculate_obstruction_angle(
        self,
        projected_points: List[ProjectedPoint],
        reference_height: float = 0.0,
        window_center: Optional[Point3D] = None,
        window_normal: Optional[Vector3D] = None
    ) -> RaytraceResult:
        """
        Calculate worst-case obstruction angle across all points

        Args:
            projected_points: Points projected onto the plane
            reference_height: Reference height on the plane
            window_center: 3D position of window center
            window_normal: Viewing direction (unit vector)

        Returns:
            RaytraceResult with maximum angle found
        """
        if not projected_points:
            return RaytraceResult(
                obstruction_angle_degrees=0.0,
                obstruction_angle_radians=0.0,
                highest_point=None,
                projected_point_count=0
            )

        # Filter points: check if mesh triangles intersect the projection plane
        if window_center is not None and window_normal is not None:
            window_arr = window_center.to_array()
            normal_arr = window_normal.to_array()

            # Calculate plane normal
            world_up_arr = np.array([0.0, 1.0, 0.0])
            plane_normal_arr = np.cross(normal_arr, world_up_arr)
            plane_normal_mag = np.linalg.norm(plane_normal_arr)

            if plane_normal_mag < 1e-6:
                world_forward_arr = np.array([1.0, 0.0, 0.0])
                plane_normal_arr = np.cross(normal_arr, world_forward_arr)

            plane_normal_arr = plane_normal_arr / np.linalg.norm(plane_normal_arr)

            valid_points = []
            PLANE_THRESHOLD = 2.5  # Increased to capture triangles near the plane

            # Check each triangle
            for i in range(0, len(projected_points), 3):
                if i + 2 >= len(projected_points):
                    break

                triangle_points = projected_points[i:i+3]
                signed_distances = []
                all_in_front = True

                for proj_point in triangle_points:
                    point_arr = proj_point.original.to_array()
                    point_to_window = point_arr - window_arr
                    dist_along_view = float(np.dot(point_to_window, normal_arr))
                    dist_to_plane = float(np.dot(point_to_window, plane_normal_arr))
                    signed_distances.append(dist_to_plane)

                    if dist_along_view <= 1e-6:
                        all_in_front = False
                        break

                if not all_in_front:
                    continue

                min_dist = min(signed_distances)
                max_dist = max(signed_distances)

                if (min_dist < PLANE_THRESHOLD and max_dist > -PLANE_THRESHOLD):
                    valid_points.extend(triangle_points)

            if not valid_points:
                return RaytraceResult(
                    obstruction_angle_degrees=0.0,
                    obstruction_angle_radians=0.0,
                    highest_point=None,
                    projected_point_count=len(projected_points)
                )

            projected_points = valid_points

        max_angle = 0.0
        worst_point = projected_points[0]

        for point in projected_points:
            if window_center is not None and window_normal is not None:
                # Use 3D geometry with viewing direction
                point_3d = point.original
                vertical_distance = point_3d.y - window_center.y

                # Skip points below window
                if vertical_distance <= 0:
                    continue

                # Calculate horizontal distance using horizontal component of viewing direction
                normal_arr = window_normal.to_array()
                normal_horizontal = normal_arr.copy()
                normal_horizontal[1] = 0.0  # Remove Y component
                normal_horizontal_mag = np.linalg.norm(normal_horizontal)

                if normal_horizontal_mag < 1e-6:
                    # Viewing straight up or down, use direct horizontal distance
                    point_vec = point_3d.to_array() - window_center.to_array()
                    point_horizontal = point_vec.copy()
                    point_horizontal[1] = 0.0
                    horizontal_distance = float(np.linalg.norm(point_horizontal))
                else:
                    # Normalize horizontal viewing direction and project
                    normal_horizontal = normal_horizontal / normal_horizontal_mag
                    point_vec = point_3d.to_array() - window_center.to_array()
                    horizontal_distance = abs(float(np.dot(point_vec, normal_horizontal)))

                # Calculate angle for this point
                if horizontal_distance < 1e-6:
                    angle = np.pi / 2
                else:
                    angle = float(np.arctan(vertical_distance / horizontal_distance))

            else:
                # Fallback: use projection coordinates
                vertical_distance = point.height - reference_height

                # Skip points below reference
                if vertical_distance <= 0:
                    continue

                horizontal_distance = abs(point.u)

                # Calculate angle for this point
                if horizontal_distance < 1e-6:
                    angle = np.pi / 2
                else:
                    angle = float(np.arctan(vertical_distance / horizontal_distance))

            # Update if this is worse
            if angle > max_angle:
                max_angle = angle
                worst_point = point

        angle_degrees = float(np.degrees(max_angle))

        return RaytraceResult(
            obstruction_angle_degrees=angle_degrees,
            obstruction_angle_radians=max_angle,
            highest_point=worst_point.original,
            projected_point_count=len(projected_points)
        )

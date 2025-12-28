from __future__ import annotations
import time
from typing import List, Any, Optional, Tuple
import numpy as np
import logging

from src.components.obstruction_models import ObstructionResult
logger = logging.getLogger(__name__)

from src.components.constants import MathConstants
from src.components.geometry import AngleCalculator, Mesh, Point3D, Triangle, Vector3D
from src.components.plane_intersection import PlaneTriangleIntersector
from src.components.triangle_filter import ZenithTriangleFilter
from src.components.vertical_plane import VerticalPlane


class ZenithIntersectionCalculator:
    """
    Efficient zenith angle calculator using plane-triangle intersections

    Similar to horizon calculator but looks for overhead obstructions.
    """

    @classmethod
    def call(
        cls,
        mesh: Mesh,
        window_center: Point3D,
        window_normal: Vector3D
    ) -> ObstructionResult:
        """Calculate zenith angle directly from mesh using plane intersections"""
        if window_center is None or window_normal is None:
            raise ValueError("window_center and window_normal are required")

        max_angle, furthest_point = (
            cls._call(
                list(mesh.triangles), window_center, window_normal
            )
        )

        if max_angle is None:
            return ObstructionResult.no_obstruction()

        angle_degrees = AngleCalculator.radians_to_degrees(max_angle)

        return ObstructionResult(
            obstruction_angle_degrees=angle_degrees,
            obstruction_angle_radians=max_angle,
            highest_point=furthest_point
        )

    @classmethod
    def _get_intersection(cls, triangle:Triangle,plane:VerticalPlane, max_height:float)->Point3D | None:
        # Early termination: skip triangles where max Z is below current max height
        if triangle.highest <= max_height:
            return
        intersections = PlaneTriangleIntersector.intersect_triangle_with_plane(triangle, plane)
        if len(intersections)<1:
            return
        ind = np.argmin([p.z for p in intersections])
        return intersections[ind]
    
    
    @classmethod
    def _no_intersection(cls)->tuple[None, None]:
        return None, None
    
    
    @classmethod
    def _normal_horizontal(cls, window_normal:Vector3D)->np.ndarray:
        normal_arr = window_normal.to_array()
        normal_horizontal = np.array([normal_arr[0], normal_arr[1], 0.0])
        normal_horizontal_mag = np.linalg.norm(normal_horizontal)
        if normal_horizontal_mag > MathConstants.EPSILON.value:
            normal_horizontal = normal_horizontal / normal_horizontal_mag
        return normal_horizontal
    
    @classmethod
    def _point_vec(cls, point:Point3D, window_center:Point3D)->np.ndarray:
        return point.to_array() - window_center.to_array()
    
    @classmethod
    def _adjust_hd_per_point(cls, point:Point3D, window_center:Point3D, magnitude:np.floating[Any], normal_horizontal:np.ndarray)->float | None:
        if point.z < window_center.z:
            return
        point_vec = cls._point_vec(point, window_center)
        if point_vec[2] <= 0:
            return

        if magnitude < MathConstants.EPSILON.value:
            point_horizontal = np.array([point_vec[0], point_vec[1], 0.0])
            return float(np.linalg.norm(point_horizontal))

        # Calculate signed distance along viewing direction (positive = ahead)
        forward_distance = float(np.dot(point_vec, normal_horizontal))

        # Only accept points ahead of window (positive dot product)
        if forward_distance <= 0:
            return None

        return forward_distance
    


    @classmethod
    def _call(
        cls,
        triangles: List[Triangle],
        window_center: Point3D,
        window_normal: Vector3D
    ) -> Tuple[Optional[float], Optional[Point3D]]:
        """
        Calculate maximum zenith angle using plane intersections on PRE-FILTERED triangles

        This method skips the filtering step (Step 0) and works directly with
        triangles that have already been filtered.

        Args:
            triangles: Pre-filtered list of relevant triangles
            window_center: Window center point
            window_normal: Window viewing direction (unit vector)

        Returns:
            Tuple of (max_angle_radians, furthest_point, intersection_count)
        """

        algo_start = time.time()

        if not triangles:
            logger.info(f"        [ZENITH-PREFILTERED] No triangles provided")
            return cls._no_intersection()
        
        step_start = time.time()
        relevant_triangles = ZenithTriangleFilter.call(
            triangles, window_center, window_normal
        )
        filter_time = time.time() - step_start
        logger.info(
            f"        [ZENITH-EFFICIENT] Step 0/4: Filtered {len(relevant_triangles)}/{len(triangles)} triangles "
            f"in {filter_time*1000:.2f}ms ({100*len(relevant_triangles)/len(triangles):.1f}% remaining)"
        )

        if not relevant_triangles:
            logger.info(f"        [ZENITH-EFFICIENT] No relevant triangles found after filtering")
            return cls._no_intersection()

        # Step 1: Create plane
        step_start = time.time()
        plane = VerticalPlane.from_window(window_center, window_normal)
        logger.info(f"        [ZENITH-PREFILTERED] Step 1/2: Plane created in {(time.time()-step_start)*1000:.2f}ms")

        # Step 2: Find intersections and calculate angles with early termination
        step_start = time.time()
        max_zenith_angle = 0.0  # Changed from min to max
        furthest_point = None  # Changed from closest to furthest

        max_zenith_rad = np.radians(90)

        normal_horizontal = cls._normal_horizontal(window_normal)
        normal_horizontal_mag = np.linalg.norm(normal_horizontal)

        for triangle in relevant_triangles:
            points = PlaneTriangleIntersector.intersect_triangle_with_plane(triangle, plane)

            hds = [cls._adjust_hd_per_point(p, window_center, normal_horizontal_mag, normal_horizontal) for p in points]
            hds = [a for a in hds if not a is None]

            # Skip if no valid points found
            if len(hds) == 0:
                continue

            ind = np.argmax(hds)
            horizontal_distance = hds[ind]
            point = points[ind]
            point_vec = cls._point_vec(point, window_center)

            zenith_angle = 0.0
            if horizontal_distance >= MathConstants.EPSILON.value:
                elevation_angle = float(np.arctan(point_vec[2] / horizontal_distance))
                zenith_angle = (np.pi / 2) - elevation_angle

            if zenith_angle > max_zenith_rad:
                continue
            if zenith_angle > max_zenith_angle:  # Changed from < min to > max
                max_zenith_angle = zenith_angle
                furthest_point = point

        if furthest_point is None or max_zenith_angle == 0.0:
            logger.info(f"        [ZENITH-PREFILTERED] No valid intersections found, total time: {(time.time()-algo_start)*1000:.2f}ms")
            return cls._no_intersection()

        total_time = time.time() - algo_start
        logger.info(f"        [ZENITH-PREFILTERED] ✓ TOTAL TIME: {total_time*1000:.2f}ms")

        return max_zenith_angle, furthest_point

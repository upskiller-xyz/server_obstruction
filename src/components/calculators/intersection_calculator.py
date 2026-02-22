
import logging

from src.server.base.constants import ANGLES
from src.components.models import Window, ObstructionResult
from src.components.models.intersection import IntersectionResult
logger = logging.getLogger(__name__)
import time
import numpy as np
from typing import Tuple

from src.components.geometry import Mesh, Point3D, Triangle, AngleCalculator
from src.components.geometry.vertical_plane import VerticalPlane
from src.components.calculators.distance_calculator import DistanceCalculator
from src.components.calculators.plane_triangle_intersector import PlaneTriangleIntersector
from src.components.filter import VerticalSurfaceFilter, NonVerticalSurfaceFilter




class IntersectionCalculator:
    """
    Horizon obstruction calculator using plane-triangle intersections

    Instead of projecting all points, finds only triangles that intersect
    the viewing plane and calculates angles directly.

    OPTIMIZATION: Sorts intersection points by Z coordinate (highest first)
    and uses early termination - once we find a point with angle >= max seen,
    we can stop checking lower points.
    """

    @classmethod
    def call(
        cls,
        mesh: Mesh,
        window: Window,
        angle_type:ANGLES = ANGLES.HORIZON
    ) -> ObstructionResult:
        """
        Calculate obstruction angle directly from mesh using plane intersections

        Args:
            mesh: 3D mesh
            window_center: 3D position of window center
            window_normal: Viewing direction unit vector

        Returns:
            ObstructionResult with angle and metadata
        """
        if window.center is None or window.normal is None:
            raise ValueError("window_center and window_normal are required")

        # Use the efficient intersection calculator
        res = cls._call(mesh.triangles, window, angle_type)

        if res.angle is None:
            return ObstructionResult.no_obstruction()
        
        return ObstructionResult(
            obstruction_angle_degrees=AngleCalculator.radians_to_degrees(res.angle),
            obstruction_angle_radians=res.angle,
            highest_point=res.point
        )
    
    @classmethod
    def _get_filter(cls, angle:ANGLES):
        _map = {
            ANGLES.HORIZON: VerticalSurfaceFilter,
            ANGLES.ZENITH: NonVerticalSurfaceFilter
        }
        return _map.get(angle, VerticalSurfaceFilter)

    @classmethod
    def _call(
        cls,
        triangles: Tuple[Triangle, ...],
        window:Window,
        angle_type = ANGLES.HORIZON
    ) -> IntersectionResult:
        """
        Calculate maximum obstruction angle using plane intersections on PRE-FILTERED triangles

        This method skips the filtering step (Step 0) and works directly with
        triangles that have already been filtered.

        Args:
            triangles: Pre-filtered list of relevant triangles
            window_center: Window center point
            window_normal: Window viewing direction (unit vector)

        Returns:
            Tuple of (max_angle_radians, highest_point, intersection_count)
        """

        algo_start = time.time()

        if not triangles:
            logger.debug(f"No triangles provided")
            return cls._no_intersection()
        
        fltr = cls._get_filter(angle_type)

        relevant_triangles = fltr.call(
            triangles, window, angle_type
        )

        if not relevant_triangles:
            logger.debug(f"No relevant triangles provided")
            return cls._no_intersection()
        
        plane = VerticalPlane.from_window(window)

        intersection_count = 0
        angle_filtered = 0  # Intersections found but angle calculation returned None
        int_point = IntersectionResult(None, 0)

        max_height = window.center.z  # Track highest Z found so far
        
        for triangle in relevant_triangles:

            point = cls._get_intersection(triangle, plane, window, angle_type, max_height)
            if point is None:
                continue
            
            intersection_count += 1
            angle = PlaneTriangleIntersector.calculate_obstruction_angle(
                    point, window, angle_type)
            
            if angle is None:
                angle_filtered += 1
                continue
            
            if angle > int_point.angle:
                int_point = IntersectionResult(point, angle)
                max_height = point.z 


        if int_point.point is None or int_point.angle == 0.0:
            logger.debug(f"No valid angles found, total time: {(time.time()-algo_start)*1000:.2f}ms")
            return cls._no_intersection()

        total_time = time.time() - algo_start
        logger.debug(f"✓ TOTAL TIME: {total_time*1000:.2f}ms")
        logger.debug("Final angle: {}\n Final point: {}".format(int_point.angle, int_point.point))
        return int_point
    
    @classmethod
    def _get_intersection(cls, triangle: Triangle, plane: VerticalPlane, window: Window, angle_type:ANGLES, max_height: float) -> Point3D | None:
        """Get the highest intersection point between triangle and plane

        Args:
            triangle: Triangle to intersect
            plane: Vertical plane
            max_height: Current maximum height found (for early termination)

        Returns:
            Highest intersection point, or None if no intersection or all points below max_height
        """

        intersections = PlaneTriangleIntersector.intersect_triangle_with_plane(triangle, plane)

        if len(intersections) <=0:
            return None
        distances = DistanceCalculator.call(intersections, angle_type, window)
        if len(distances)<=0:
            return None
        
        # TODO: check the logic
        ind = np.argmax(distances)
        return intersections[ind]
    
    
    @classmethod
    def _no_intersection(cls)->IntersectionResult:
        return IntersectionResult(None, 0)

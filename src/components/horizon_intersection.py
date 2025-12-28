
import logging

from src.components.obstruction_models import ObstructionResult
logger = logging.getLogger(__name__)
import time
import numpy as np
from typing import List, Optional, Tuple
from src.components.geometry import AngleCalculator, Mesh, Point3D, Triangle, Vector3D
from src.components.plane_intersection import PlaneTriangleIntersector
from src.components.triangle_filter import VerticalSurfaceFilter
from src.components.vertical_plane import VerticalPlane


class HorizonIntersectionCalculator:
    """
    Efficient horizon obstruction calculator using plane-triangle intersections

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
        window_center: Point3D,
        window_normal: Vector3D
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
        if window_center is None or window_normal is None:
            raise ValueError("window_center and window_normal are required")

        # Use the efficient intersection calculator
        max_angle, highest_point = (
            cls._call(
                mesh.triangles, window_center, window_normal
            )
        )

        if max_angle is None:
            return ObstructionResult.no_obstruction()

        angle_degrees = AngleCalculator.radians_to_degrees(max_angle)

        return ObstructionResult(
            obstruction_angle_degrees=angle_degrees,
            obstruction_angle_radians=max_angle,
            highest_point=highest_point
        )

    @classmethod
    def _call(
        cls,
        triangles: List[Triangle],
        window_center: Point3D,
        window_normal: Vector3D
    ) -> Tuple[Optional[float], Optional[Point3D]]:
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
            logger.info(f"No triangles provided")
            return cls._no_intersection()

        # Filter to only vertical surfaces (walls) - excludes horizontal surfaces (roofs)
        relevant_triangles = VerticalSurfaceFilter.call(
            triangles, window_center,
            window_normal,
            min_horizontal_distance=1.0,
            max_vertical_normal_z=0.5  # Only surfaces up to ~60° from vertical
        )

        if not relevant_triangles:
            logger.info(f"No relevant triangles provided")
            return cls._no_intersection()
        
        # Step 1: Create vertical plane through window in viewing direction
        step_start = time.time()
        plane = VerticalPlane.from_window(window_center, window_normal)
        logger.info(f"Step 1/3: Plane created in {(time.time()-step_start)*1000:.2f}ms")

        # Step 2: Find intersections and calculate angles with early termination
        step_start = time.time()
        max_angle = 0.0
        max_point = None
        max_height = window_center.z  # Track highest Z found so far

        intersection_count = 0
        skipped_below = 0
        no_intersection = 0
        angle_filtered = 0  # Intersections found but angle calculation returned None

        for triangle in relevant_triangles:

            ints_pt = cls._get_intersection(triangle, plane, max_height)
            if ints_pt is not None:
                intersection_count += 1
                angle = PlaneTriangleIntersector.calculate_obstruction_angle(
                        ints_pt, window_center, window_normal,
                        min_horizontal_distance=0.0  # Allow any distance for real-world data
                    )
                if angle is not None:
                    if angle > max_angle:
                        max_angle = angle
                        max_point = ints_pt
                        max_height = ints_pt.z  # Update for early termination
                else:
                    angle_filtered += 1
            else:
                # Check why no intersection
                triangle_max_z = max(triangle.v1.z, triangle.v2.z, triangle.v3.z)
                if triangle_max_z <= max_height:
                    skipped_below += 1
                else:
                    no_intersection += 1

        logger.info(
            f"Step 2/3: Intersections - {intersection_count} found, "
            f"{angle_filtered} filtered by angle calc, "
            f"{skipped_below} skipped (below), {no_intersection} no intersection"
        )

        if max_point is None:
            logger.info(f"No valid angles found, total time: {(time.time()-algo_start)*1000:.2f}ms")
            return cls._no_intersection()

        total_time = time.time() - algo_start
        logger.info(f"✓ TOTAL TIME: {total_time*1000:.2f}ms")

        return max_angle, max_point
    
    @classmethod
    def _get_intersection(cls, triangle: Triangle, plane: VerticalPlane, max_height: float) -> Point3D | None:
        """Get the highest intersection point between triangle and plane

        Args:
            triangle: Triangle to intersect
            plane: Vertical plane
            max_height: Current maximum height found (for early termination)

        Returns:
            Highest intersection point, or None if no intersection or all points below max_height
        """
        # Early termination: skip triangles entirely below current max height
        triangle_max_z = max(triangle.v1.z, triangle.v2.z, triangle.v3.z)
        if triangle_max_z <= max_height:
            return None

        intersections = PlaneTriangleIntersector.intersect_triangle_with_plane(triangle, plane)
        if len(intersections) < 1:
            return None
        # Return the highest intersection point
        ind = np.argmax([p.z for p in intersections])
        return intersections[ind]
    
    
    @classmethod
    def _no_intersection(cls)->tuple[None, None]:
        return None, None

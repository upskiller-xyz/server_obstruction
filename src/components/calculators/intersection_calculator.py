"""Intersection-based obstruction calculator"""

import logging
import time
from typing import List, Tuple

from src.components.calculators.filter_strategy_map import FilterStrategyMap
from src.components.calculators.plane_triangle_intersector import PlaneTriangleIntersector
from src.components.calculators.ray_triangle_intersector import TriangleArrays
from src.components.calculators.vectorized_elevation_angle_collector import VectorizedElevationAngleCollector
from src.components.calculators.triangle_intersection_finder import TriangleIntersectionFinder
from src.components.geometry import AngleCalculator, Mesh, Triangle
from src.components.geometry.vertical_plane import VerticalPlane
from src.components.models import ObstructionResult, Window
from src.components.models.intersection import IntersectionResult
from src.server.base.constants import ANGLES

class IntersectionCalculator:
    """
    Horizon/Zenith obstruction calculator using plane-triangle intersections

    Single Responsibility:
    - Orchestrates intersection-based obstruction calculation
    - Delegates filtering to FilterStrategyMap
    - Delegates intersection finding to TriangleIntersectionFinder
    - Delegates angle collection to VectorizedElevationAngleCollector

    OPTIMIZATION: Tracks maximum height/angle for early termination
    """

    @classmethod
    def call(
        cls,
        mesh: Mesh,
        window: Window,
        angle_type: ANGLES = ANGLES.HORIZON
    ) -> ObstructionResult:
        """
        Calculate obstruction angle directly from mesh using plane intersections

        Args:
            mesh: 3D mesh
            window: Window with center and normal
            angle_type: HORIZON or ZENITH

        Returns:
            ObstructionResult with angle and metadata
        """
        if window.center is None or window.normal is None:
            raise ValueError("window.center and window.normal are required")

        # Delegate to internal calculation
        result = cls._calculate_intersection(
            mesh.triangles, window, angle_type
        )

        if result.angle is None:
            return ObstructionResult.no_obstruction()

        return ObstructionResult(
            obstruction_angle_degrees=AngleCalculator.radians_to_degrees(result.angle),
            obstruction_angle_radians=result.angle,
            highest_point=result.point
        )

    @classmethod
    def _calculate_intersection(
        cls,
        triangles: Tuple[Triangle, ...],
        window: Window,
        angle_type: ANGLES = ANGLES.HORIZON
    ) -> IntersectionResult:
        """
        Calculate maximum obstruction angle using plane intersections

        Args:
            triangles: Triangles to process
            window: Window center and normal
            angle_type: HORIZON or ZENITH

        Returns:
            IntersectionResult with angle and point
        """
        algo_start = time.time()

        if not triangles:
            logging.debug("No triangles provided")
            return cls._no_intersection()

        # Get appropriate filter using Strategy Pattern
        filter_class = FilterStrategyMap.get_filter(angle_type)
        relevant_triangles = filter_class.call(triangles, window, angle_type)

        if not relevant_triangles:
            logging.debug("No relevant triangles after filtering")
            return cls._no_intersection()

        plane = VerticalPlane.from_window(window)
        intersection_count = 0
        angle_filtered = 0
        best_result = IntersectionResult(None, 0)
        max_height = window.center.z

        for triangle in relevant_triangles:
            # Delegate intersection finding
            point = TriangleIntersectionFinder.find_intersection(
                triangle, plane, window, angle_type
            )
            if point is None:
                continue

            intersection_count += 1
            angle = PlaneTriangleIntersector.calculate_obstruction_angle(
                point, window, angle_type
            )

            if angle is None:
                angle_filtered += 1
                continue

            if angle > best_result.angle:
                best_result = IntersectionResult(point, angle)
                max_height = point.z

        if best_result.point is None or best_result.angle == 0.0:
            total_time = (time.time() - algo_start) * 1000
            logging.debug(f"No valid angles found, total time: {total_time:.2f}ms")
            return cls._no_intersection()

        total_time = (time.time() - algo_start) * 1000
        logging.debug(f"✓ TOTAL TIME: {total_time:.2f}ms")
        logging.debug(
            f"Final angle: {best_result.angle}\nFinal point: {best_result.point}"
        )
        return best_result

    @classmethod
    def collect_all_elevation_angles(
        cls,
        triangles: Tuple[Triangle, ...],
        window: Window
    ) -> List[float]:
        """
        Collect ALL elevation angles for gap-based calculation

        Delegates to VectorizedElevationAngleCollector for separation of concerns

        Args:
            triangles: All triangles (no filtering)
            window: Window for reference

        Returns:
            Sorted list of elevation angles in degrees
        """
        return VectorizedElevationAngleCollector.collect_all_angles(triangles, window)

    @classmethod
    def collect_all_elevation_angles_from_arrays(
        cls,
        tri_arrays: TriangleArrays,
        window: Window
    ) -> List[float]:
        """
        Collect ALL elevation angles using pre-packed triangle arrays.

        Avoids redundant vertex packing when TriangleArrays are already
        available (e.g. shared with RayTriangleIntersector).

        Args:
            tri_arrays: Pre-packed triangle vertex arrays
            window: Window for reference

        Returns:
            Sorted list of elevation angles in degrees
        """
        return VectorizedElevationAngleCollector.collect_all_angles_from_arrays(
            tri_arrays, window
        )

    @classmethod
    def _no_intersection(cls) -> IntersectionResult:
        """Create empty intersection result"""
        return IntersectionResult(None, 0)

from abc import ABC, abstractmethod
from typing import List
import logging
import numpy as np
from src.components.obstruction_models import ProjectedPoint, ObstructionResult, ProjectionPlane
from src.components.geometry import Point3D, Vector3D, CoordinateSystem, AngleCalculator
from src.components.triangle_processing import (
    HorizonTriangleProcessor, ZenithTriangleProcessor, TriangleProcessor, PlaneIntersectionFilter
)
from src.components.constants import MathConstants, ThresholdConstants

logger = logging.getLogger(__name__)


class HorizontalDistanceCalculator:
    """
    Calculator for horizontal distances along viewing direction

    Encapsulates the logic for calculating horizontal distance from a point
    to the window center, projected onto the horizontal plane.
    """

    @staticmethod
    def calculate(
        point: Point3D,
        window_center: Point3D,
        window_normal: Vector3D
    ) -> float:
        """
        Calculate horizontal distance from point to window along viewing direction

        Args:
            point: 3D point
            window_center: Window center position
            window_normal: Window viewing direction (unit vector)

        Returns:
            Horizontal distance in meters
        """
        # Get horizontal component of viewing direction
        
        normal_horizontal = window_normal.get_horizontal().to_array()
        normal_horizontal_mag = np.linalg.norm(normal_horizontal)

        # Vector from window to point
        point_vec = point.to_array() - window_center.to_array()

        if normal_horizontal_mag < MathConstants.EPSILON:
            # Viewing straight up or down, use direct horizontal distance
            point_horizontal = CoordinateSystem.remove_vertical_component(point_vec)
            return float(np.linalg.norm(point_horizontal))
        
        # Normalize horizontal viewing direction and project
        normal_horizontal = normal_horizontal / normal_horizontal_mag
        return abs(float(np.dot(point_vec, normal_horizontal)))


class IObstructionCalculator(ABC):
    """Interface for obstruction angle calculations"""

    @abstractmethod
    def calculate_obstruction_angle(
        self,
        projected_points: List[ProjectedPoint],
        window_center: Point3D,
        window_normal: Vector3D
    ) -> ObstructionResult:
        """
        Calculate obstruction angle from projected points

        Args:
            projected_points: List of 2D projected points on plane
            window_center: 3D position of window center (required)
            window_normal: Viewing direction unit vector (required)

        Returns:
            ObstructionResult with obstruction angle and metadata
        """
        pass


class HorizonObstructionCalculator(IObstructionCalculator):
    """
    Calculates obstruction angle based on the highest point in the projection

    The obstruction angle is measured from the horizontal line at the reference
    height to the line connecting the reference point to the highest point.
    """

    def calculate_obstruction_angle(
        self,
        projected_points: List[ProjectedPoint],
        window_center: Point3D,
        window_normal: Vector3D
    ) -> ObstructionResult:
        """
        Calculate obstruction angle from the highest projected point

        The angle is calculated in the vertical viewing plane:
        - Find the highest point (maximum v coordinate on projection)
        - Calculate vertical distance: highest_point.z - window_center.z
        - Calculate horizontal distance along viewing direction
        - Angle = arctan(vertical_distance / horizontal_distance)

        Args:
            projected_points: Points projected onto the plane
            window_center: 3D position of window center (required)
            window_normal: Viewing direction unit vector (required)

        Returns:
            ObstructionResult with angle and metadata
        """
        if not projected_points:
            return ObstructionResult.no_obstruction()

        # Validate required parameters
        if window_center is None or window_normal is None:
            raise ValueError("window_center and window_normal are required for obstruction calculations")

        # Use specialized horizon triangle processor
        processor = HorizonTriangleProcessor(window_center, window_normal)
        triangles = processor.process(projected_points)

        if not triangles:
            return ObstructionResult.no_obstruction(projected_point_count=len(projected_points))

        # Get first (highest) triangle's points
        vertical_points = [point for triangle in triangles for point in triangle.points]

        # Find the highest point on vertical surfaces only
        highest_projected = max(vertical_points, key=lambda p: p.height)
        highest_3d = highest_projected.original

        # Calculate vertical distance
        vertical_distance = highest_3d.get_vertical() - window_center.get_vertical()

        # If highest point is below window, no obstruction
        if vertical_distance <= 0:
            return ObstructionResult.no_obstruction( 
                highest_point=highest_3d,
                projected_point_count=len(projected_points)
            )

        # Calculate horizontal distance using HorizontalDistanceCalculator
        horizontal_distance = HorizontalDistanceCalculator.calculate(
            highest_3d, window_center, window_normal
        )

        # Calculate angle using AngleCalculator
        angle_radians = AngleCalculator.calculate_obstruction_angle(
            vertical_distance, horizontal_distance
        )
        angle_degrees = AngleCalculator.radians_to_degrees(angle_radians)

        return ObstructionResult(
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
        window_center: Point3D,
        window_normal: Vector3D
    ) -> ObstructionResult:
        """
        Calculate zenith angle from the lowest overhead projected point

        The angle is calculated in the vertical viewing plane:
        - Find the furthest horizontal overhead point
        - Calculate vertical distance (positive = above window)
        - Calculate horizontal distance along viewing direction
        - Angle = 90° - arctan(vertical_distance / horizontal_distance)

        Args:
            projected_points: Points projected onto the plane
            window_center: 3D position of window center (required)
            window_normal: Viewing direction unit vector (required)

        Returns:
            ObstructionResult with zenith angle and metadata
        """
        if not projected_points:
            return ObstructionResult.no_obstruction()

        # Validate required parameters
        if window_center is None or window_normal is None:
            raise ValueError("window_center and window_normal are required for zenith angle calculations")

        # Use specialized zenith triangle processor
        processor = ZenithTriangleProcessor(window_center, window_normal)
        triangles = processor.process(projected_points)

        if not triangles:
            return ObstructionResult.no_obstruction(projected_point_count=len(projected_points))

        # Get first (furthest) triangle's points
        # The triangles are sorted by distance, so first is furthest
        overhead_points = [point for triangle in triangles for point in triangle.points]

        # Find furthest point (for logging and result)
        furthest_overhead = overhead_points[0] if overhead_points else projected_points[0]
        logger.info(f"Selected furthest point from first triangle: ({furthest_overhead.original.x:.1f}, {furthest_overhead.original.y:.1f}, {furthest_overhead.original.z:.1f})")
        lowest_3d = furthest_overhead.original

        # Calculate vertical distance (positive because point is above)
        vertical_distance = lowest_3d.get_vertical() - window_center.get_vertical()

        # Must be above window
        if vertical_distance <= 0:
            return ObstructionResult.no_obstruction(
                highest_point=lowest_3d,
                projected_point_count=len(projected_points)
            )

        # Calculate horizontal distance using HorizontalDistanceCalculator
        horizontal_distance = HorizontalDistanceCalculator.calculate(
            lowest_3d, window_center, window_normal
        )

        # Calculate zenith angle using AngleCalculator
        angle_radians = AngleCalculator.calculate_zenith_angle(
            vertical_distance, horizontal_distance
        )
        angle_degrees = AngleCalculator.radians_to_degrees(angle_radians)

        return ObstructionResult(
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
        window_center: Point3D,
        window_normal: Vector3D
    ) -> ObstructionResult:
        """
        Calculate worst-case obstruction angle across all points

        Args:
            projected_points: Points projected onto the plane
            window_center: 3D position of window center (required)
            window_normal: Viewing direction unit vector (required)

        Returns:
            ObstructionResult with maximum angle found
        """
        if not projected_points:
            return ObstructionResult.no_obstruction()

        # Validate required parameters
        if window_center is None or window_normal is None:
            raise ValueError("window_center and window_normal are required for worst-case obstruction calculations")

        # Use triangle processor with plane intersection filter only
        processor = TriangleProcessor()

        # Add plane intersection filter
        plane_normal_vec = ProjectionPlane.calculate_plane_normal(window_normal)
        plane_normal = plane_normal_vec.to_array()
        plane_filter = PlaneIntersectionFilter(
            window_center, window_normal, plane_normal,
            threshold=ThresholdConstants.PLANE_THRESHOLD_WIDE
        )
        processor.add_filter(plane_filter)

        # Get filtered triangles and extract points
        triangles = processor.process(projected_points)

        if not triangles:
            return ObstructionResult.no_obstruction(projected_point_count=len(projected_points))

        # Extract all points from filtered triangles
        filtered_points = [point for triangle in triangles for point in triangle.points]

        max_angle = 0.0
        worst_point = filtered_points[0]

        for point in filtered_points:
            point_3d = point.original

            # Calculate vertical distance
            vertical_distance = point_3d.get_vertical() - window_center.get_vertical()

            # Skip points below window
            if vertical_distance <= 0:
                continue

            # Calculate horizontal distance using HorizontalDistanceCalculator
            horizontal_distance = HorizontalDistanceCalculator.calculate(
                point_3d, window_center, window_normal
            )

            # Calculate angle for this point
            angle = AngleCalculator.calculate_obstruction_angle(
                vertical_distance, horizontal_distance
            )

            # Update if this is worse
            if angle > max_angle:
                max_angle = angle
                worst_point = point

        angle_degrees = AngleCalculator.radians_to_degrees(max_angle)

        return ObstructionResult(
            obstruction_angle_degrees=angle_degrees,
            obstruction_angle_radians=max_angle,
            highest_point=worst_point.original,
            projected_point_count=len(projected_points)
        )


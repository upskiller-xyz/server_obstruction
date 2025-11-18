from abc import ABC, abstractmethod
from typing import List
import logging
import numpy as np
from src.components.obstruction_models import ProjectedPoint, ObstructionResult, ProjectionPlane
from src.components.geometry import Point3D, Vector3D, CoordinateSystem, AngleCalculator, Mesh
from src.components.triangle_processing import (
    HorizonTriangleProcessor, ZenithTriangleProcessor, TriangleProcessor, PlaneIntersectionFilter
)
from src.components.constants import MathConstants, ThresholdConstants
from src.components.plane_intersection import HorizonIntersectionCalculator, ZenithIntersectionCalculator

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

        # Get all points from filtered triangles
        overhead_points = [point for triangle in triangles for point in triangle.points]

        # Step 1: Find the closest mesh on vertical (Z) axis
        min_vertical_distance = float('inf')
        for point in overhead_points:
            point_3d = point.original
            vert_dist = point_3d.get_vertical() - window_center.get_vertical()
            if vert_dist > 0 and vert_dist < min_vertical_distance:
                min_vertical_distance = vert_dist

        if min_vertical_distance == float('inf'):
            return ObstructionResult.no_obstruction(
                projected_point_count=len(projected_points)
            )

        # Step 2: Within the closest mesh, find the furthest point along view direction
        # Use a small tolerance for "same vertical distance"
        vertical_tolerance = 0.01
        max_angle = 0.0
        furthest_overhead = None

        for point in overhead_points:
            point_3d = point.original

            # Calculate vertical distance
            vert_dist = point_3d.get_vertical() - window_center.get_vertical()

            # Only consider points at the closest vertical distance
            if abs(vert_dist - min_vertical_distance) > vertical_tolerance:
                continue

            # Calculate horizontal distance
            horiz_dist = HorizontalDistanceCalculator.calculate(
                point_3d, window_center, window_normal
            )

            # Calculate zenith angle for this point
            angle = AngleCalculator.calculate_zenith_angle(vert_dist, horiz_dist)

            # Keep point with maximum angle (furthest horizontally)
            if angle > max_angle:
                max_angle = angle
                furthest_overhead = point

        # If no valid point found
        if furthest_overhead is None:
            return ObstructionResult.no_obstruction(
                projected_point_count=len(projected_points)
            )

        lowest_3d = furthest_overhead.original
        logger.info(f"Selected point from closest mesh (Z={lowest_3d.z:.1f}) with maximum angle: ({lowest_3d.x:.1f}, {lowest_3d.y:.1f}, {lowest_3d.z:.1f})")

        # Calculate final distances for the selected point
        vertical_distance = lowest_3d.get_vertical() - window_center.get_vertical()
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


class IntersectionObstructionCalculator(IObstructionCalculator):
    """
    EFFICIENT plane-intersection based obstruction calculator

    Instead of projecting all mesh points onto a 2D plane, this calculator:
    1. Creates a vertical plane through the window in the viewing direction
    2. Finds only the triangles that intersect this plane
    3. Calculates angles for intersection points
    4. Returns the maximum angle (highest obstruction)

    This is much more efficient than the projection approach because:
    - Only processes triangles that intersect the viewing plane
    - No 2D projection needed
    - Direct angle calculation from 3D intersection points
    - Can use early termination if angles are sorted
    """

    def calculate_obstruction_angle(
        self,
        projected_points: List[ProjectedPoint],
        window_center: Point3D,
        window_normal: Vector3D
    ) -> ObstructionResult:
        """
        Calculate obstruction angle using plane-triangle intersections

        NOTE: This method signature includes projected_points for interface compatibility,
        but they are not used. The calculation works directly with the mesh.

        Args:
            projected_points: Not used (for interface compatibility)
            window_center: 3D position of window center (required)
            window_normal: Viewing direction unit vector (required)

        Returns:
            ObstructionResult with angle and metadata
        """
        # This implementation requires access to the mesh
        # For now, return no obstruction - this will be called from service layer
        logger.warning("IntersectionObstructionCalculator.calculate_obstruction_angle called without mesh")
        return ObstructionResult.no_obstruction()

    def calculate_obstruction_angle_from_mesh(
        self,
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
        max_angle, highest_point, intersection_count = (
            HorizonIntersectionCalculator.calculate_max_obstruction_angle(
                mesh, window_center, window_normal
            )
        )

        if max_angle is None:
            return ObstructionResult.no_obstruction()

        angle_degrees = AngleCalculator.radians_to_degrees(max_angle)

        return ObstructionResult(
            obstruction_angle_degrees=angle_degrees,
            obstruction_angle_radians=max_angle,
            highest_point=highest_point,
            projected_point_count=intersection_count
        )


class IntersectionZenithCalculator(IObstructionCalculator):
    """
    EFFICIENT zenith calculator using plane-triangle intersections
    """

    def calculate_obstruction_angle(
        self,
        projected_points: List[ProjectedPoint],
        window_center: Point3D,
        window_normal: Vector3D
    ) -> ObstructionResult:
        """For interface compatibility - not used"""
        logger.warning("IntersectionZenithCalculator.calculate_obstruction_angle called without mesh")
        return ObstructionResult.no_obstruction()

    def calculate_zenith_angle_from_mesh(
        self,
        mesh: Mesh,
        window_center: Point3D,
        window_normal: Vector3D
    ) -> ObstructionResult:
        """Calculate zenith angle directly from mesh using plane intersections"""
        if window_center is None or window_normal is None:
            raise ValueError("window_center and window_normal are required")

        max_angle, furthest_point, intersection_count = (
            ZenithIntersectionCalculator.calculate_max_zenith_angle(
                mesh, window_center, window_normal
            )
        )

        if max_angle is None:
            return ObstructionResult.no_obstruction()

        angle_degrees = AngleCalculator.radians_to_degrees(max_angle)

        return ObstructionResult(
            obstruction_angle_degrees=angle_degrees,
            obstruction_angle_radians=max_angle,
            highest_point=furthest_point,
            projected_point_count=intersection_count
        )

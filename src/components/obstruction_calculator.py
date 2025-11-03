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

        # Find the highest point on the projection (maximum v coordinate)
        highest_projected = max(projected_points, key=lambda p: p.height)
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

            # Horizontal distance along viewing direction
            # Project the vector (point - center) onto the normal direction
            point_vec = highest_3d.to_array() - window_center.to_array()
            horizontal_distance = abs(float(np.dot(point_vec, window_normal.to_array())))

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

                # Calculate horizontal distance along viewing direction
                point_vec = point_3d.to_array() - window_center.to_array()
                horizontal_distance = abs(float(np.dot(point_vec, window_normal.to_array())))

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

from dataclasses import dataclass
from typing import List, Optional
import numpy as np
from src.components.geometry import Point3D, Vector3D, Mesh, CoordinateSystem
from src.components.constants import MathConstants, ResponseField, RequestField


@dataclass(frozen=True)
class Window:
    """Window definition with center point and normal direction"""
    center: Point3D
    normal: Vector3D

    @classmethod
    def from_dict(cls, data: dict) -> 'Window':
        """
        Create Window from dictionary

        Supports both old format (rad_x, rad_y) and new format (direction_angle)

        Args:
            data: Dict with keys:
                - x, y, z: window center coordinates
                - direction_angle: horizontal rotation angle in radians (0 to 2π)
                  OR (deprecated)
                - rad_x, rad_y: old two-angle system
        """
        center = Point3D(
            x=float(data[RequestField.X.value]),
            y=float(data[RequestField.Y.value]),
            z=float(data[RequestField.Z.value])
        )

        # Check for new single-angle format first
        if RequestField.DIRECTION_ANGLE.value in data:
            normal = Vector3D.from_horizontal_angle(float(data[RequestField.DIRECTION_ANGLE.value]))
        # Fallback to old two-angle format for backward compatibility
        elif RequestField.RAD_X.value in data and RequestField.RAD_Y.value in data:
            normal = Vector3D.from_angles(
                rad_x=float(data[RequestField.RAD_X.value]),
                rad_y=float(data[RequestField.RAD_Y.value])
            ).normalize()
        else:
            raise ValueError(f"Must provide either '{RequestField.DIRECTION_ANGLE.value}' or both '{RequestField.RAD_X.value}' and '{RequestField.RAD_Y.value}'")

        return cls(center=center, normal=normal)


@dataclass(frozen=True)
class ProjectedPoint:
    """2D point on projection plane with original 3D point reference"""
    u: float  # Horizontal coordinate on plane
    v: float  # Vertical coordinate on plane
    original: Point3D

    @property
    def height(self) -> float:
        """Get vertical component (v)"""
        return self.v


@dataclass(frozen=True)
class ProjectionPlane:
    """
    Vertical plane in 3D space defined by origin and basis vectors

    The plane passes through the origin point and is defined by:
    - u_axis: horizontal direction vector
    - v_axis: vertical direction vector (always points up in world coordinates)
    """
    origin: Point3D
    u_axis: Vector3D  # Horizontal axis (perpendicular to normal and vertical)
    v_axis: Vector3D  # Vertical axis (always pointing up)
    normal: Vector3D  # Normal to the plane (viewing direction)

    @staticmethod
    def calculate_plane_normal(direction: Vector3D) -> Vector3D:
        """
        Calculate plane normal perpendicular to direction and world up

        The plane contains both the viewing direction and world up.
        The plane's geometric normal is perpendicular to both.

        Args:
            direction: Viewing direction vector

        Returns:
            Normalized plane normal vector
        """
        direction_arr = direction.to_array()
        plane_normal_arr = np.cross(direction_arr, CoordinateSystem.UP)
        plane_normal_mag = np.linalg.norm(plane_normal_arr)

        if plane_normal_mag < MathConstants.EPSILON:
            # Direction is parallel to world up (looking straight up/down)
            # Use forward direction as reference instead
            plane_normal_arr = np.cross(direction_arr, CoordinateSystem.FORWARD)

        normalized = plane_normal_arr / np.linalg.norm(plane_normal_arr)
        return Vector3D.from_array(normalized)


@dataclass(frozen=True)
class ObstructionRequest:
    """Input request for obstruction calculation"""
    window: Window
    mesh: Mesh

    @classmethod
    def from_dict(cls, data: dict) -> 'ObstructionRequest':
        """
        Create ObstructionRequest from dictionary

        Args:
            data: Dict with keys:
                - x, y, z: window center coordinates
                - direction_angle: horizontal rotation angle in radians (0 to 2π)
                  OR (deprecated) rad_x, rad_y: old two-angle system
                - mesh: list of vertices (every 3 form a triangle)
        """
        window = Window.from_dict(data)
        mesh = Mesh.from_vertices(data[RequestField.MESH.value])
        return cls(window=window, mesh=mesh)


@dataclass(frozen=True)
class ObstructionResult:
    """Result of obstruction calculation"""
    obstruction_angle_degrees: float
    obstruction_angle_radians: float
    highest_point: Optional[Point3D]
    projected_point_count: int

    @classmethod
    def no_obstruction(cls, highest_point: Optional[Point3D] = None, projected_point_count: int = 0) -> 'ObstructionResult':
        """
        Create a result indicating no obstruction found

        Args:
            highest_point: Optional point to include in result
            projected_point_count: Number of projected points processed

        Returns:
            ObstructionResult with zero angle
        """
        return cls(
            obstruction_angle_degrees=0.0,
            obstruction_angle_radians=0.0,
            highest_point=highest_point,
            projected_point_count=projected_point_count
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            ResponseField.OBSTRUCTION_ANGLE_DEGREES.value: self.obstruction_angle_degrees,
            ResponseField.OBSTRUCTION_ANGLE_RADIANS.value: self.obstruction_angle_radians,
            ResponseField.HIGHEST_POINT.value: {
                RequestField.X.value: self.highest_point.x,
                RequestField.Y.value: self.highest_point.y,
                RequestField.Z.value: self.highest_point.z
            } if self.highest_point else None,
            ResponseField.PROJECTED_POINT_COUNT.value: self.projected_point_count
        }

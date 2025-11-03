from dataclasses import dataclass
from typing import List, Optional
from src.components.geometry import Point3D, Vector3D, Mesh


@dataclass(frozen=True)
class Window:
    """Window definition with center point and normal direction"""
    center: Point3D
    normal: Vector3D

    @classmethod
    def from_dict(cls, data: dict) -> 'Window':
        """
        Create Window from dictionary

        Args:
            data: Dict with keys: x, y, z, rad_x, rad_y
        """
        center = Point3D(
            x=float(data['x']),
            y=float(data['y']),
            z=float(data['z'])
        )
        normal = Vector3D.from_angles(
            rad_x=float(data['rad_x']),
            rad_y=float(data['rad_y'])
        ).normalize()
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


@dataclass(frozen=True)
class RaytraceRequest:
    """Input request for raytracing operation"""
    window: Window
    mesh: Mesh

    @classmethod
    def from_dict(cls, data: dict) -> 'RaytraceRequest':
        """
        Create RaytraceRequest from dictionary

        Args:
            data: Dict with keys:
                - x, y, z: window center coordinates
                - rad_x, rad_y: window normal angles
                - mesh: list of vertices (every 3 form a triangle)
        """
        window = Window.from_dict(data)
        mesh = Mesh.from_vertices(data['mesh'])
        return cls(window=window, mesh=mesh)


@dataclass(frozen=True)
class RaytraceResult:
    """Result of raytracing calculation"""
    obstruction_angle_degrees: float
    obstruction_angle_radians: float
    highest_point: Optional[Point3D]
    projected_point_count: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "obstruction_angle_degrees": self.obstruction_angle_degrees,
            "obstruction_angle_radians": self.obstruction_angle_radians,
            "highest_point": {
                "x": self.highest_point.x,
                "y": self.highest_point.y,
                "z": self.highest_point.z
            } if self.highest_point else None,
            "projected_point_count": self.projected_point_count
        }

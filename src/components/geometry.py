from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass(frozen=True)
class Point3D:
    """Immutable 3D point representation"""
    x: float
    y: float
    z: float

    def to_array(self) -> np.ndarray:
        """Convert to numpy array"""
        return np.array([self.x, self.y, self.z])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Point3D':
        """Create Point3D from numpy array"""
        return cls(x=float(arr[0]), y=float(arr[1]), z=float(arr[2]))


@dataclass(frozen=True)
class Vector3D:
    """Immutable 3D vector representation"""
    x: float
    y: float
    z: float

    def to_array(self) -> np.ndarray:
        """Convert to numpy array"""
        return np.array([self.x, self.y, self.z])

    def magnitude(self) -> float:
        """Calculate vector magnitude"""
        return float(np.linalg.norm(self.to_array()))

    def normalize(self) -> 'Vector3D':
        """Return normalized vector"""
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize zero vector")
        arr = self.to_array() / mag
        return Vector3D(x=float(arr[0]), y=float(arr[1]), z=float(arr[2]))

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Vector3D':
        """Create Vector3D from numpy array"""
        return cls(x=float(arr[0]), y=float(arr[1]), z=float(arr[2]))

    @classmethod
    def from_angles(cls, rad_x: float, rad_y: float) -> 'Vector3D':
        """
        Create vector from rotation angles

        Args:
            rad_x: Rotation around X axis (pitch)
            rad_y: Rotation around Y axis (yaw)
        """
        # Convert spherical coordinates to Cartesian
        x = np.cos(rad_y) * np.cos(rad_x)
        y = np.sin(rad_x)
        z = np.sin(rad_y) * np.cos(rad_x)
        return cls(x=float(x), y=float(y), z=float(z))


@dataclass(frozen=True)
class Triangle:
    """Triangle defined by three vertices"""
    v1: Point3D
    v2: Point3D
    v3: Point3D

    def vertices(self) -> List[Point3D]:
        """Return list of vertices"""
        return [self.v1, self.v2, self.v3]


@dataclass(frozen=True)
class Mesh:
    """3D mesh composed of triangles"""
    triangles: Tuple[Triangle, ...]

    @classmethod
    def from_vertices(cls, vertices: List[List[float]]) -> 'Mesh':
        """
        Create mesh from list of vertices (grouped by 3 for triangles)

        Args:
            vertices: List of [x, y, z] coordinates, every 3 vertices form a triangle
        """
        if len(vertices) == 0:
            raise ValueError("Mesh vertices cannot be empty")

        if len(vertices) % 3 != 0:
            raise ValueError("Number of vertices must be divisible by 3")

        triangles = []
        for i in range(0, len(vertices), 3):
            v1 = Point3D(*vertices[i])
            v2 = Point3D(*vertices[i + 1])
            v3 = Point3D(*vertices[i + 2])
            triangles.append(Triangle(v1, v2, v3))

        return cls(triangles=tuple(triangles))

    def get_all_points(self) -> List[Point3D]:
        """Get all unique points in the mesh"""
        points = []
        for triangle in self.triangles:
            points.extend(triangle.vertices())
        return points

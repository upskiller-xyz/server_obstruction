from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np


class CoordinateSystem:
    """
    World coordinate system definition

    Convention:
    - X-axis: Horizontal, points East (default forward direction at angle=0)
    - Y-axis: Horizontal, points North
    - Z-axis: Vertical, points Up

    This matches the single-angle rotation system where:
    - direction_angle = 0: faces +X (East)
    - direction_angle = π/2: faces +Y (North)
    """

    # Axis unit vectors as numpy arrays
    X_AXIS = np.array([1.0, 0.0, 0.0])
    Y_AXIS = np.array([0.0, 1.0, 0.0])
    Z_AXIS = np.array([0.0, 0.0, 1.0])

    # Semantic names (numpy arrays)
    UP = Z_AXIS          # Vertical up direction
    FORWARD = X_AXIS     # Default forward direction (angle=0)
    NORTH = Y_AXIS       # North direction (angle=π/2)

    # Index mapping for coordinate components
    VERTICAL_INDEX = 2   # Z component is vertical
    HORIZONTAL_INDICES = [0, 1]  # X, Y components are horizontal

    @classmethod
    def remove_vertical_component(cls, vector: np.ndarray) -> np.ndarray:
        """
        Remove the vertical component from a vector

        Args:
            vector: Input vector (numpy array)

        Returns:
            Vector with vertical component set to zero
        """
        result = vector.copy()
        result[cls.VERTICAL_INDEX] = 0.0
        return result

    @classmethod
    def get_vertical_component(cls, vector: np.ndarray) -> float:
        """
        Get the vertical component of a vector

        Args:
            vector: Input vector (numpy array)

        Returns:
            Vertical component value
        """
        return float(vector[cls.VERTICAL_INDEX])

    @classmethod
    def set_vertical_component(cls, vector: np.ndarray, value: float) -> np.ndarray:
        """
        Set the vertical component of a vector

        Args:
            vector: Input vector (numpy array)
            value: Value to set

        Returns:
            New vector with vertical component set
        """
        result = vector.copy()
        result[cls.VERTICAL_INDEX] = value
        return result


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

    def get_vertical(self, coord_system: type = CoordinateSystem) -> float:
        """
        Get vertical component according to coordinate system

        Args:
            coord_system: Coordinate system class to use

        Returns:
            Vertical component value
        """
        return coord_system.get_vertical_component(self.to_array())

    def get_horizontal_array(self, coord_system: type = CoordinateSystem) -> np.ndarray:
        """
        Get horizontal components as array according to coordinate system

        Args:
            coord_system: Coordinate system class to use

        Returns:
            Array with only horizontal components (vertical set to 0)
        """
        return coord_system.remove_vertical_component(self.to_array())


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

    def get_vertical(self, coord_system: type = CoordinateSystem) -> float:
        """
        Get vertical component according to coordinate system

        Args:
            coord_system: Coordinate system class to use

        Returns:
            Vertical component value
        """
        return coord_system.get_vertical_component(self.to_array())

    def get_horizontal(self, coord_system: type = CoordinateSystem) -> 'Vector3D':
        """
        Get horizontal components only (vertical removed)

        Args:
            coord_system: Coordinate system class to use

        Returns:
            Vector with vertical component set to 0
        """
        arr = coord_system.remove_vertical_component(self.to_array())
        return Vector3D.from_array(arr)

    @classmethod
    def from_horizontal_angle(cls, angle: float) -> 'Vector3D':
        """
        Create horizontal direction vector from single angle

        Coordinate system: Y-axis points up, rotation in XZ plane
        - angle=0: Points in +X direction
        - angle=π/2: Points in +Z direction
        - angle=π: Points in -X direction
        - angle=3π/2: Points in -Z direction

        Args:
            angle: Horizontal rotation angle in radians (0 to 2π)

        Returns:
            Unit vector in horizontal plane (y component = 0)
        """
        x = np.cos(angle)
        y = np.sin(angle)
        z = 0.0  # Horizontal plane only
        return cls(x=float(x), y=float(y), z=float(z))


class AngleCalculator:
    """
    Calculator for obstruction angles

    Encapsulates the logic for calculating angles from vertical and horizontal distances
    """

    @staticmethod
    def radians_to_degrees(radians: float) -> float:
        """
        Convert radians to degrees

        Args:
            radians: Angle in radians

        Returns:
            Angle in degrees
        """
        return float(np.degrees(radians))

    @staticmethod
    def calculate_obstruction_angle(
        vertical_distance: float,
        horizontal_distance: float
    ) -> float:
        """
        Calculate obstruction angle from vertical and horizontal distances

        Args:
            vertical_distance: Vertical distance (height difference)
            horizontal_distance: Horizontal distance along viewing direction

        Returns:
            Angle in radians (0 to π/2)
        """
        # Import here to avoid circular dependency
        from src.components.constants import MathConstants

        # Handle case where point is directly above (infinite angle)
        if horizontal_distance < MathConstants.EPSILON:
            return float(np.pi / 2)  # 90 degrees

        # Calculate angle using arctan
        return float(np.arctan(vertical_distance / horizontal_distance))

    @staticmethod
    def calculate_zenith_angle(
        vertical_distance: float,
        horizontal_distance: float
    ) -> float:
        """
        Calculate zenith angle from vertical and horizontal distances

        Zenith angle is measured from vertical: 90° - elevation_angle

        Args:
            vertical_distance: Vertical distance (positive = above)
            horizontal_distance: Horizontal distance along viewing direction

        Returns:
            Angle in radians (0 to π/2)
        """
        # Import here to avoid circular dependency
        from src.components.constants import MathConstants

        # Point directly overhead
        if horizontal_distance < MathConstants.EPSILON:
            return 0.0

        elevation_angle = float(np.arctan(vertical_distance / horizontal_distance))
        return (np.pi / 2) - elevation_angle


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

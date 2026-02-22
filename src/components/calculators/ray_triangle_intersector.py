"""
Ray-triangle intersection using Moller-Trumbore algorithm

Provides ray construction from elevation angles and efficient
vectorized intersection testing against mesh triangles.
"""

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from src.components.geometry import Point3D, Triangle
from src.components.geometry.coordinate_system import CoordinateSystem
from src.server.base.constants import MathConstants


@dataclass(frozen=True)
class Ray:
    """Immutable ray defined by origin and unit direction vector"""
    origin: np.ndarray
    direction: np.ndarray

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Ray):
            return NotImplemented
        return np.array_equal(self.origin, other.origin) and np.array_equal(self.direction, other.direction)

    def __hash__(self) -> int:
        return hash((tuple(self.origin), tuple(self.direction)))

    @classmethod
    def from_elevation(
        cls,
        origin: Point3D,
        horizontal_angle: float,
        elevation_rad: float
    ) -> 'Ray':
        """
        Create ray from window center, horizontal direction, and elevation angle.

        Args:
            origin: Ray origin point (window center)
            horizontal_angle: Horizontal direction angle in radians
            elevation_rad: Elevation angle in radians (0 = horizontal, pi/2 = straight up)

        Returns:
            Ray with unit direction vector
        """
        horizontal = np.array([np.cos(horizontal_angle), np.sin(horizontal_angle), 0.0])
        direction = np.cos(elevation_rad) * horizontal + np.sin(elevation_rad) * CoordinateSystem.UP
        norm = np.linalg.norm(direction)
        if norm < MathConstants.EPSILON.value:
            raise ValueError("Cannot create ray with zero direction")
        return cls(origin=origin.to_array(), direction=direction / norm)


@dataclass(frozen=True)
class TriangleArrays:
    """Pre-packed triangle vertex arrays for vectorized intersection testing"""
    v0: np.ndarray  # (N, 3)
    v1: np.ndarray  # (N, 3)
    v2: np.ndarray  # (N, 3)
    count: int


class RayTriangleIntersector:
    """
    Moller-Trumbore ray-triangle intersection test

    Supports both single-ray and vectorized batch testing.
    Only forward intersections (t > min_distance) count.

    The min_distance parameter skips geometry very close to the ray origin
    (e.g., the building's own wall surrounding the window), preventing
    self-intersection false positives.
    """

    EPSILON: float = MathConstants.EPSILON.value
    MIN_DISTANCE: float = 0.5  # Skip hits closer than 0.5m (wall thickness)

    @classmethod
    def prepare_arrays(cls, triangles: Tuple[Triangle, ...]) -> TriangleArrays:
        """
        Convert Triangle tuples to packed numpy arrays for vectorized testing.

        Args:
            triangles: Tuple of Triangle objects

        Returns:
            TriangleArrays with v0, v1, v2 each of shape (N, 3)
        """
        n = len(triangles)
        v0 = np.empty((n, 3))
        v1 = np.empty((n, 3))
        v2 = np.empty((n, 3))
        for i, tri in enumerate(triangles):
            v0[i] = (tri.v1.x, tri.v1.y, tri.v1.z)
            v1[i] = (tri.v2.x, tri.v2.y, tri.v2.z)
            v2[i] = (tri.v3.x, tri.v3.y, tri.v3.z)
        return TriangleArrays(v0=v0, v1=v1, v2=v2, count=n)

    @classmethod
    def batch_hits_any(
        cls,
        origin: np.ndarray,
        directions: np.ndarray,
        tri_arrays: TriangleArrays,
        min_distance: float = 0.5
    ) -> np.ndarray:
        """
        Test M rays (same origin) against N triangles using vectorized Moller-Trumbore.

        All M rays share the same origin point but have different directions.
        Uses numpy broadcasting to test all M×N combinations in a single pass.

        Args:
            origin: Ray origin point, shape (3,)
            directions: Ray direction vectors, shape (M, 3)
            tri_arrays: Pre-packed triangle vertex arrays
            min_distance: Minimum hit distance to avoid self-intersection

        Returns:
            Boolean array of shape (M,) — True if ray hits any triangle
        """
        # Expand dims for broadcasting: rays (M,1,3), triangles (1,N,3)
        rd = directions[:, np.newaxis, :]           # (M, 1, 3)
        v0 = tri_arrays.v0[np.newaxis, :, :]        # (1, N, 3)

        edge1 = tri_arrays.v1[np.newaxis, :, :] - v0  # (1, N, 3)
        edge2 = tri_arrays.v2[np.newaxis, :, :] - v0  # (1, N, 3)

        # h = cross(direction, edge2) → (M, N, 3)
        h = np.cross(rd, edge2)

        # a = dot(edge1, h) → (M, N)
        a = np.sum(edge1 * h, axis=2)

        # Mask non-parallel triangles
        valid = np.abs(a) > cls.EPSILON

        # Safe reciprocal (avoid division by zero)
        safe_a = np.where(valid, a, 1.0)
        f = np.where(valid, 1.0 / safe_a, 0.0)

        # s = origin - v0 → (1, N, 3) since origin is shared
        s = origin[np.newaxis, np.newaxis, :] - v0

        # u = f * dot(s, h) → (M, N)
        u = f * np.sum(s * h, axis=2)
        valid &= (u >= 0.0) & (u <= 1.0)

        # q = cross(s, edge1) → (1, N, 3) — same for all rays
        q = np.cross(s, edge1)

        # v = f * dot(direction, q) → (M, N)
        v = f * np.sum(rd * q, axis=2)
        valid &= (v >= 0.0) & (u + v <= 1.0)

        # t = f * dot(edge2, q) → (M, N)
        # edge2 and q are both (1,N,3), their dot is (1,N) — shared across rays
        edge2_dot_q = np.sum(edge2 * q, axis=2)  # (1, N)
        t = f * edge2_dot_q
        valid &= (t > min_distance)

        # For each ray: did it hit ANY triangle?
        return np.any(valid, axis=1)

    @classmethod
    def intersects(cls, ray: Ray, triangle: Triangle, min_distance: float = 0.5) -> bool:
        """
        Test if ray intersects triangle beyond min_distance.

        Args:
            ray: Ray to test
            triangle: Triangle to test against
            min_distance: Minimum hit distance (skip closer hits to avoid self-intersection)

        Returns:
            True if ray hits triangle at t > min_distance
        """
        v0 = triangle.v1.to_array()
        v1 = triangle.v2.to_array()
        v2 = triangle.v3.to_array()

        edge1 = v1 - v0
        edge2 = v2 - v0

        h = np.cross(ray.direction, edge2)
        a = np.dot(edge1, h)

        if abs(a) < cls.EPSILON:
            return False

        f = 1.0 / a
        s = ray.origin - v0
        u = f * np.dot(s, h)

        if u < 0.0 or u > 1.0:
            return False

        q = np.cross(s, edge1)
        v = f * np.dot(ray.direction, q)

        if v < 0.0 or u + v > 1.0:
            return False

        t = f * np.dot(edge2, q)
        return t > min_distance

    @classmethod
    def hits_any(cls, ray: Ray, triangles: Tuple[Triangle, ...], min_distance: float = 0.5) -> bool:
        """
        Test if ray hits any triangle beyond min_distance.

        Early-exits on first hit for efficiency.

        Args:
            ray: Ray to test
            triangles: Tuple of triangles to test against
            min_distance: Minimum hit distance (skip closer hits)

        Returns:
            True if ray hits at least one triangle beyond min_distance
        """
        return any(cls.intersects(ray, tri, min_distance) for tri in triangles)

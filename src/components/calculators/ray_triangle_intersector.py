"""
Ray-triangle intersection using Moller-Trumbore algorithm

Provides vectorized intersection testing against mesh triangles
for gap verification in the unified obstruction calculator.
"""

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from src.components.geometry import Triangle
from src.server.base.constants import MathConstants


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

    Supports vectorized batch testing of M rays against N triangles.
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
    def from_array(cls, vertices_array: np.ndarray) -> TriangleArrays:
        """
        Build TriangleArrays directly from an (M, 3, 3) vertex array.

        Pure numpy slicing (~ms) — no Python loop over Triangle objects. The
        all-directions path keeps the mesh as an array end-to-end, so this replaces
        ``prepare_arrays`` (which exists for legacy Triangle-object callers).

        Args:
            vertices_array: (M, 3, 3) — M triangles, 3 vertices, 3 coords

        Returns:
            TriangleArrays with v0, v1, v2 each of shape (M, 3)
        """
        n = len(vertices_array)
        if n == 0:
            empty = np.empty((0, 3))
            return TriangleArrays(v0=empty, v1=empty.copy(), v2=empty.copy(), count=0)
        return TriangleArrays(
            v0=np.ascontiguousarray(vertices_array[:, 0, :]),
            v1=np.ascontiguousarray(vertices_array[:, 1, :]),
            v2=np.ascontiguousarray(vertices_array[:, 2, :]),
            count=n,
        )

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
        Uses numpy broadcasting to test all M x N combinations in a single pass.

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

        # h = cross(direction, edge2) -> (M, N, 3)
        h = np.cross(rd, edge2)

        # a = dot(edge1, h) -> (M, N)
        a = np.sum(edge1 * h, axis=2)

        # Mask non-parallel triangles
        valid = np.abs(a) > cls.EPSILON

        # Safe reciprocal (avoid division by zero)
        safe_a = np.where(valid, a, 1.0)
        f = np.where(valid, 1.0 / safe_a, 0.0)

        # s = origin - v0 -> (1, N, 3) since origin is shared
        s = origin[np.newaxis, np.newaxis, :] - v0

        # u = f * dot(s, h) -> (M, N)
        u = f * np.sum(s * h, axis=2)
        valid &= (u >= 0.0) & (u <= 1.0)

        # q = cross(s, edge1) -> (1, N, 3) — same for all rays
        q = np.cross(s, edge1)

        # v = f * dot(direction, q) -> (M, N)
        v = f * np.sum(rd * q, axis=2)
        valid &= (v >= 0.0) & (u + v <= 1.0)

        # t = f * dot(edge2, q) -> (M, N)
        edge2_dot_q = np.sum(edge2 * q, axis=2)  # (1, N)
        t = f * edge2_dot_q
        valid &= (t > min_distance)

        # For each ray: did it hit ANY triangle?
        return np.any(valid, axis=1)

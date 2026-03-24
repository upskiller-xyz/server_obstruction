"""
Vectorized elevation angle collector for gap-based obstruction calculations

Replaces the scalar ElevationAngleCollector.collect_all_angles with a fully
vectorized NumPy implementation. Instead of iterating over triangles in Python,
all plane-triangle intersections and elevation angles are computed in batch
using array broadcasting.
"""

from typing import List, Tuple

import numpy as np

from src.components.geometry import Triangle
from src.components.geometry.vertical_plane import VerticalPlane
from src.components.models import Window
from src.server.base.constants import MathConstants


class VectorizedElevationAngleCollector:
    """
    Vectorized elevation angle collection from plane-triangle intersections.

    Replaces the scalar per-triangle loop in ElevationAngleCollector with
    batch NumPy operations for significant speedup on large meshes.

    Single Responsibility:
    - Only collects and sorts elevation angles (same as ElevationAngleCollector)
    - Operates on batched arrays instead of individual triangles

    Pipeline:
    1. Pack triangle vertices into (N, 3) arrays
    2. Compute signed distances to plane for all vertices
    3. Find edge-plane crossings for all 3N edges
    4. Interpolate intersection points
    5. Compute elevation angles with directional filtering
    6. Sort and return
    """

    EPSILON: float = MathConstants.EPSILON.value

    @classmethod
    def collect_all_angles(
        cls,
        triangles: Tuple[Triangle, ...],
        window: Window
    ) -> List[float]:
        """
        Collect ALL intersection point elevation angles from ALL triangles.

        Vectorized replacement for ElevationAngleCollector.collect_all_angles.
        Produces identical results but uses batch NumPy operations instead of
        Python for-loops.

        Args:
            triangles: All triangles (no horizon/zenith split)
            window: Window with center and normal for this direction

        Returns:
            Sorted list of elevation angles in degrees (0=horizontal, 90=up)
        """
        if not triangles:
            return []

        plane = VerticalPlane.from_window(window)

        v1, v2, v3 = cls._pack_vertices(triangles)

        origin = plane.origin.to_array()
        normal = plane.normal.to_array()
        d1 = cls._signed_distances(v1, origin, normal)
        d2 = cls._signed_distances(v2, origin, normal)
        d3 = cls._signed_distances(v3, origin, normal)

        window_center = window.center.to_array()
        window_normal = window.normal.to_array()

        edge_batches = [
            (v1, v2, d1, d2),
            (v2, v3, d2, d3),
            (v3, v1, d3, d1),
        ]

        angles_list = []
        for pa, pb, da, db in edge_batches:
            edge_angles = cls._process_edge_batch(
                pa, pb, da, db, window_center, window_normal
            )
            if edge_angles.size > 0:
                angles_list.append(edge_angles)

        if not angles_list:
            return []

        all_angles = np.concatenate(angles_list)
        all_angles.sort()
        return all_angles.tolist()

    @classmethod
    def _pack_vertices(
        cls,
        triangles: Tuple[Triangle, ...]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Pack triangle vertices into (N, 3) arrays.

        Args:
            triangles: Tuple of Triangle objects

        Returns:
            Tuple of (v1, v2, v3) arrays, each shape (N, 3)
        """
        n = len(triangles)
        v1 = np.empty((n, 3))
        v2 = np.empty((n, 3))
        v3 = np.empty((n, 3))
        for i, tri in enumerate(triangles):
            v1[i] = (tri.v1.x, tri.v1.y, tri.v1.z)
            v2[i] = (tri.v2.x, tri.v2.y, tri.v2.z)
            v3[i] = (tri.v3.x, tri.v3.y, tri.v3.z)
        return v1, v2, v3

    @classmethod
    def _signed_distances(
        cls,
        vertices: np.ndarray,
        origin: np.ndarray,
        normal: np.ndarray
    ) -> np.ndarray:
        """
        Compute signed distances from vertices to plane.

        distance = normal . (vertex - origin)

        Args:
            vertices: (N, 3) vertex positions
            origin: (3,) plane origin
            normal: (3,) plane normal

        Returns:
            (N,) signed distances
        """
        return (vertices - origin) @ normal

    @classmethod
    def _process_edge_batch(
        cls,
        pa: np.ndarray,
        pb: np.ndarray,
        da: np.ndarray,
        db: np.ndarray,
        window_center: np.ndarray,
        window_normal: np.ndarray
    ) -> np.ndarray:
        """
        Find plane intersections and elevation angles for a batch of edges.

        For N edges, determines which cross the plane, computes intersection
        points, and returns elevation angles for valid intersections.

        Args:
            pa: (N, 3) first endpoints
            pb: (N, 3) second endpoints
            da: (N,) signed distances of pa to plane
            db: (N,) signed distances of pb to plane
            window_center: (3,) window center position
            window_normal: (3,) window normal direction

        Returns:
            1D array of valid elevation angles in degrees
        """
        crosses = (da * db) <= 0

        both_on_plane = (np.abs(da) < cls.EPSILON) & (np.abs(db) < cls.EPSILON)
        crosses &= ~both_on_plane

        if not np.any(crosses):
            return np.empty(0)

        pa_c = pa[crosses]
        pb_c = pb[crosses]
        da_c = da[crosses]
        db_c = db[crosses]

        t = da_c / (da_c - db_c)
        points = pa_c + t[:, np.newaxis] * (pb_c - pa_c)

        vertical_distance = points[:, 2] - window_center[2]

        above = vertical_distance > 0
        if not np.any(above):
            return np.empty(0)

        points_above = points[above]
        vert_above = vertical_distance[above]

        horizontal_distance = cls._horizontal_distances(
            points_above, window_center, window_normal
        )

        in_front = horizontal_distance >= 0
        if not np.any(in_front):
            return np.empty(0)

        return np.degrees(np.arctan2(
            vert_above[in_front],
            horizontal_distance[in_front]
        ))

    @classmethod
    def _horizontal_distances(
        cls,
        points: np.ndarray,
        window_center: np.ndarray,
        window_normal: np.ndarray
    ) -> np.ndarray:
        """
        Compute horizontal distances from window to points along viewing direction.

        Projects the point-to-window vector onto the horizontal component of
        the window normal. Handles the edge case of vertical viewing direction.

        Args:
            points: (M, 3) intersection points
            window_center: (3,) window center
            window_normal: (3,) window normal direction

        Returns:
            (M,) horizontal distances (negative if behind window)
        """
        diff = points - window_center

        normal_horizontal = np.array([window_normal[0], window_normal[1], 0.0])
        magnitude = np.linalg.norm(normal_horizontal)

        if magnitude < cls.EPSILON:
            horizontal_diff = diff.copy()
            horizontal_diff[:, 2] = 0.0
            return np.linalg.norm(horizontal_diff, axis=1)

        normal_horizontal = normal_horizontal / magnitude
        return diff @ normal_horizontal

"""
Batched elevation angle collector for the all-directions path

Vectorizes ``VectorizedElevationAngleCollector`` over *directions* as well as
triangles. The scalar collector runs one O(N) NumPy sweep per direction (64×);
this collector computes the plane-triangle intersections for all D directions in
a handful of (N, D) broadcasts, then splits the result into one angle list per
direction for gap detection.

The plane normal and window normal differ per direction (the window rotates),
but the origin (window center) is shared — so signed distances become a single
``(V - origin) @ plane_normals.T`` matmul of shape (N, D).
"""

from typing import List

import numpy as np

from src.components.calculators.ray_triangle_intersector import TriangleArrays
from src.server.base.constants import MathConstants


class BatchedElevationAngleCollector:
    """
    Collect per-direction elevation angles for all directions in one batch.

    Single Responsibility:
    - Only collects elevation angles (batched over directions)
    - Produces identical per-direction results to VectorizedElevationAngleCollector

    Pipeline (all broadcast over D directions at once):
    1. Build per-direction plane normals and window horizontal normals
    2. Signed distances of all vertices to all planes -> (N, D)
    3. Edge-plane crossings, interpolated points, elevation angles -> (N, D)
    4. Split the (3N, D) angle matrix into one 1D array per direction
    """

    EPSILON: float = MathConstants.EPSILON.value

    @classmethod
    def collect(
        cls,
        tri_arrays: TriangleArrays,
        origin: np.ndarray,
        azimuths: np.ndarray
    ) -> List[np.ndarray]:
        """
        Collect elevation angles per direction.

        Args:
            tri_arrays: Pre-packed triangle vertex arrays (shared across directions)
            origin: (3,) window center — shared ray/plane origin for all directions
            azimuths: (D,) absolute direction angles in radians

        Returns:
            List of D 1D arrays; entry d holds the (unsorted) elevation angles in
            degrees for direction ``azimuths[d]`` (0=horizontal, 90=up)
        """
        azimuths = np.asarray(azimuths, dtype=float)
        num_directions = azimuths.shape[0]

        if tri_arrays.count == 0 or num_directions == 0:
            return [np.empty(0) for _ in range(num_directions)]

        origin = np.asarray(origin, dtype=float)
        cos_a = np.cos(azimuths)
        sin_a = np.sin(azimuths)

        # Plane normal per direction = normalize(cross(window_normal, up)).
        # window_normal = (cos a, sin a, 0) -> cross with (0,0,1) = (sin a, -cos a, 0),
        # already unit length (window normals are horizontal, magnitude 1).
        plane_normals = np.stack([sin_a, -cos_a, np.zeros_like(sin_a)], axis=-1)  # (D, 3)
        # Window horizontal normal (unit) used to project the forward distance.
        window_normals = np.stack([cos_a, sin_a, np.zeros_like(cos_a)], axis=-1)  # (D, 3)

        # Signed distances of each triangle vertex to each direction's plane: (N, D)
        d0 = (tri_arrays.v0 - origin) @ plane_normals.T
        d1 = (tri_arrays.v1 - origin) @ plane_normals.T
        d2 = (tri_arrays.v2 - origin) @ plane_normals.T

        edge_batches = [
            (tri_arrays.v0, tri_arrays.v1, d0, d1),
            (tri_arrays.v1, tri_arrays.v2, d1, d2),
            (tri_arrays.v2, tri_arrays.v0, d2, d0),
        ]

        # (3N, D) elevation matrix; invalid entries are NaN so each column can be
        # reduced to its direction's valid angle set without ragged bookkeeping.
        edge_angles = [
            cls._edge_elevations(pa, pb, da, db, origin, window_normals)
            for pa, pb, da, db in edge_batches
        ]
        angle_matrix = np.concatenate(edge_angles, axis=0)  # (3N, D)

        return [
            column[~np.isnan(column)]
            for column in angle_matrix.T
        ]

    @classmethod
    def _edge_elevations(
        cls,
        pa: np.ndarray,
        pb: np.ndarray,
        da: np.ndarray,
        db: np.ndarray,
        origin: np.ndarray,
        window_normals: np.ndarray
    ) -> np.ndarray:
        """
        Elevation angles for one triangle edge across all directions.

        Args:
            pa: (N, 3) edge start vertices
            pb: (N, 3) edge end vertices
            da: (N, D) signed distances of pa to each direction's plane
            db: (N, D) signed distances of pb to each direction's plane
            origin: (3,) window center
            window_normals: (D, 3) per-direction horizontal window normals (unit)

        Returns:
            (N, D) elevation angles in degrees, NaN where the edge does not yield a
            valid (crossing, above, in-front) intersection for that direction
        """
        crosses = (da * db) <= 0.0
        both_on_plane = (np.abs(da) < cls.EPSILON) & (np.abs(db) < cls.EPSILON)
        crosses &= ~both_on_plane

        # Interpolation parameter; guard the denominator where the edge does not
        # cross (those entries are masked out below anyway).
        denom = da - db
        safe_denom = np.where(np.abs(denom) < cls.EPSILON, 1.0, denom)
        t = np.where(crosses, da / safe_denom, 0.0)  # (N, D)

        # Intersection points: pa + t * (pb - pa), broadcast over directions.
        pa_e = pa[:, np.newaxis, :]           # (N, 1, 3)
        edge = (pb - pa)[:, np.newaxis, :]    # (N, 1, 3)
        points = pa_e + t[:, :, np.newaxis] * edge  # (N, D, 3)

        vertical = points[:, :, 2] - origin[2]       # (N, D)
        diff = points - origin                        # (N, D, 3)
        # Forward distance = diff . window_normal (per direction); window normals
        # are unit horizontal vectors, so this matches the scalar projection.
        horizontal = np.einsum('ndc,dc->nd', diff, window_normals)  # (N, D)

        valid = crosses & (vertical > 0.0) & (horizontal >= 0.0)
        angles = np.degrees(np.arctan2(vertical, horizontal))
        return np.where(valid, angles, np.nan)

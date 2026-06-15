"""
3D mesh representation.

NumPy-backed: the source of truth is an ``(M, 3, 3)`` float array (M triangles,
3 vertices, 3 coords). ``Mesh.from_vertices`` stores that array directly (cheap)
instead of building ``Point3D``/``Triangle`` objects up front — the heavy
all-directions path consumes the array (filters, ray casting) and never touches
the objects. ``triangles`` is built **lazily**, only when a legacy/single-direction
caller (``/horizon``, ``/zenith``, ``/obstruction``) needs the object form.
"""

from typing import List, Optional, Tuple

import numpy as np

from src.components.geometry.point import Point3D
from src.components.geometry.triangle import Triangle


class Mesh:
    """3D mesh composed of triangles, backed by an (M, 3, 3) vertex array."""

    def __init__(
        self,
        triangles: Optional[Tuple[Triangle, ...]] = None,
        *,
        vertices_array: Optional[np.ndarray] = None,
    ) -> None:
        # Exactly one source is provided; the other is materialized lazily.
        self._triangles: Optional[Tuple[Triangle, ...]] = (
            tuple(triangles) if triangles is not None else None
        )
        self._vertices_array: Optional[np.ndarray] = vertices_array
        if self._triangles is None and self._vertices_array is None:
            self._triangles = ()

    @classmethod
    def empty(cls) -> 'Mesh':
        """Create an empty mesh with no triangles."""
        return cls(())

    @classmethod
    def from_vertices(cls, vertices: List[List[float]]) -> 'Mesh':
        """
        Create mesh from a flat list of [x, y, z] vertices (every 3 → a triangle).

        Stores the data as an (M, 3, 3) numpy array; Triangle objects are built
        lazily on first access to ``triangles``.

        Raises:
            ValueError: If vertices list is empty or not divisible by 3
        """
        if len(vertices) == 0:
            raise ValueError("Mesh vertices cannot be empty")
        if len(vertices) % 3 != 0:
            raise ValueError("Number of vertices must be divisible by 3")

        array = np.asarray(vertices, dtype=np.float64).reshape(-1, 3, 3)
        return cls(vertices_array=array)

    @classmethod
    def from_array(cls, vertices_array: np.ndarray) -> 'Mesh':
        """Create a mesh from a vertex array — accepts (M, 3, 3) triangles or a flat
        (N, 3) vertex array (every 3 vertices → a triangle). Reshapes to (M, 3, 3)."""
        return cls(vertices_array=np.asarray(vertices_array, dtype=np.float64).reshape(-1, 3, 3))

    @property
    def vertices_array(self) -> np.ndarray:
        """The mesh as an (M, 3, 3) float array — the source of truth.

        Derived once from triangles for meshes that were built from objects.
        """
        if self._vertices_array is None:
            tris = self._triangles or ()
            array = np.empty((len(tris), 3, 3), dtype=np.float64)
            for i, t in enumerate(tris):
                array[i, 0] = t.v1.to_array()
                array[i, 1] = t.v2.to_array()
                array[i, 2] = t.v3.to_array()
            self._vertices_array = array
        return self._vertices_array

    @property
    def triangles(self) -> Tuple[Triangle, ...]:
        """Triangle objects, built lazily from the vertex array on first access."""
        if self._triangles is None:
            array = self._vertices_array
            if array is None or len(array) == 0:
                self._triangles = ()
            else:
                self._triangles = tuple(
                    Triangle(
                        Point3D(*array[i, 0].tolist()),
                        Point3D(*array[i, 1].tolist()),
                        Point3D(*array[i, 2].tolist()),
                    )
                    for i in range(len(array))
                )
        return self._triangles

    def get_all_points(self) -> List[Point3D]:
        """Get all points in the mesh"""
        points = []
        for triangle in self.triangles:
            points.extend(triangle.vertices())
        return points

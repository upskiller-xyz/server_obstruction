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
        # Exactly one source is the authority; the other is materialized lazily.
        # Passing both is ambiguous (which one is canonical?) — reject it.
        if triangles is not None and vertices_array is not None:
            raise ValueError("Mesh takes either 'triangles' or 'vertices_array', not both")
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
        """Create a mesh from a vertex array.

        Accepts an ``(M, 3, 3)`` triangle array or a flat ``(N, 3)`` vertex array
        (every 3 vertices → a triangle). The shape is validated explicitly so a
        wrongly-shaped array isn't silently reinterpreted into scrambled triangles.

        Raises:
            ValueError: if the array isn't (M, 3, 3) or (N, 3) with N divisible by 3
        """
        array = np.asarray(vertices_array, dtype=np.float64)
        if array.ndim == 3 and array.shape[1:] == (3, 3):
            return cls(vertices_array=array)
        if array.ndim == 2 and array.shape[1] == 3 and array.shape[0] % 3 == 0:
            return cls(vertices_array=array.reshape(-1, 3, 3))
        raise ValueError(
            f"vertices_array must be (M, 3, 3) or (N, 3) with N divisible by 3, "
            f"got shape {tuple(array.shape)}"
        )

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

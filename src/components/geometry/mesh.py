"""
3D mesh representation

Immutable dataclass for meshes composed of triangles.
"""

from dataclasses import dataclass
from typing import List, Tuple

from src.components.geometry.point import Point3D
from src.components.geometry.triangle import Triangle


@dataclass(frozen=True)
class Mesh:
    """3D mesh composed of triangles"""
    triangles: Tuple[Triangle, ...]

    @classmethod
    def empty(cls)->'Mesh':
        return cls(())

    @classmethod
    def from_vertices(cls, vertices: List[List[float]]) -> 'Mesh':
        """
        Create mesh from list of vertices (grouped by 3 for triangles)

        Args:
            vertices: List of [x, y, z] coordinates, every 3 vertices form a triangle

        Returns:
            Mesh instance

        Raises:
            ValueError: If vertices list is empty or not divisible by 3
        """
        if len(vertices) == 0:
            raise ValueError("Mesh vertices cannot be empty")

        if len(vertices) % 3 != 0:
            raise ValueError("Number of vertices must be divisible by 3")

        # OPTIMIZATION: Use tuple comprehension (avoids list append overhead)
        triangles = tuple(
            Triangle(
                Point3D(*vertices[i]),
                Point3D(*vertices[i + 1]),
                Point3D(*vertices[i + 2])
            )
            for i in range(0, len(vertices), 3)
        )

        return cls(triangles=triangles)

    def get_all_points(self) -> List[Point3D]:
        """Get all unique points in the mesh"""
        points = []
        for triangle in self.triangles:
            points.extend(triangle.vertices())
        return points

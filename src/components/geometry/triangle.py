"""
Triangle representation

Immutable dataclass for triangles defined by three vertices.
"""

from dataclasses import dataclass
from typing import List

from src.components.geometry.point import Point3D


@dataclass(frozen=True)
class Triangle:
    """Triangle defined by three vertices"""
    v1: Point3D
    v2: Point3D
    v3: Point3D

    def vertices(self) -> List[Point3D]:
        """Return list of vertices"""
        return [self.v1, self.v2, self.v3]

    @property
    def highest(self) -> float:
        """Get the highest Z coordinate of the triangle"""
        return max(self.v1.z, self.v2.z, self.v3.z)

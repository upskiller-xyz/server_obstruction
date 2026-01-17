"""
Projected point representation

2D point on projection plane with reference to original 3D point.
"""

from dataclasses import dataclass

from src.components.geometry.point import Point3D


@dataclass(frozen=True)
class ProjectedPoint:
    """2D point on projection plane with original 3D point reference"""
    u: float  # Horizontal coordinate on plane
    v: float  # Vertical coordinate on plane
    original: Point3D

    @property
    def height(self) -> float:
        """Get vertical component (v)"""
        return self.v

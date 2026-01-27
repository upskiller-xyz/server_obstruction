"""
Projected triangle representation

Triangle with projected points and orientation analysis.
"""

from typing import List, Tuple
import numpy as np

from src.components.geometry.projected_point import ProjectedPoint
from src.components.geometry.point import Point3D
from src.components.geometry.coordinate_system import CoordinateSystem
from src.server.base.constants import MathConstants, TriangleOrientation


class ProjectedTriangle:
    """Represents a triangle with its three projected vertices"""

    def __init__(self, points: List[ProjectedPoint]):
        """
        Initialize triangle from three projected points

        Args:
            points: List of exactly 3 ProjectedPoint objects
        """
        if len(points) != 3:
            raise ValueError("Triangle must have exactly 3 points")
        self.points = points

    def get_vertices(self) -> List[Point3D]:
        """Get 3D vertices of the triangle"""
        return [p.original for p in self.points]

    def get_vertex_arrays(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get triangle vertices as numpy arrays"""
        vertices = self.get_vertices()
        return (vertices[0].to_array(), vertices[1].to_array(), vertices[2].to_array())

    def calculate_normal(self) -> np.ndarray:
        """
        Calculate surface normal vector of the triangle

        Returns:
            Normalized normal vector
        """
        p0, p1, p2 = self.get_vertex_arrays()
        edge1 = p1 - p0
        edge2 = p2 - p0
        normal = np.cross(edge1, edge2)
        magnitude = np.linalg.norm(normal)

        if magnitude < MathConstants.EPSILON.value:
            # Degenerate triangle
            return CoordinateSystem.UP.copy()

        return normal / magnitude

    def get_orientation(self, vertical_threshold: float = 0.1) -> TriangleOrientation:
        """
        Determine if triangle is vertical, horizontal, or slanted

        Args:
            vertical_threshold: Threshold for vertical dot product (default 0.1)

        Returns:
            Triangle orientation type
        """
        normal = self.calculate_normal()
        vertical_component = abs(CoordinateSystem.get_vertical_component(normal))

        if vertical_component < vertical_threshold:
            # Normal is nearly horizontal -> surface is vertical
            return TriangleOrientation.VERTICAL
        elif vertical_component > (1.0 - vertical_threshold):
            # Normal is nearly vertical -> surface is horizontal
            return TriangleOrientation.HORIZONTAL
        else:
            return TriangleOrientation.SLANTED

    def get_highest_point(self) -> ProjectedPoint:
        """Get the point with maximum vertical coordinate"""
        return max(self.points, key=lambda p: p.original.get_vertical())

    def get_average_height(self) -> float:
        """Calculate average vertical coordinate of vertices"""
        return sum(p.original.get_vertical() for p in self.points) / 3

    def get_centroid(self) -> Point3D:
        """Calculate triangle centroid"""
        vertices = self.get_vertices()
        x = sum(v.x for v in vertices) / 3
        y = sum(v.y for v in vertices) / 3
        z = sum(v.z for v in vertices) / 3
        return Point3D(x=x, y=y, z=z)

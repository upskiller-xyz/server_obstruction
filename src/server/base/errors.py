"""Validators for geometric constraints and data integrity"""
from src.components.geometry import Point3D, Triangle


class PointOnTriangleError(ValueError):
    """Raised when a point lies on a triangle where it shouldn't"""

    def __init__(self, point: Point3D, triangle: Triangle):
        """
        Initialize error with point and triangle information

        Args:
            point: The point that lies on the triangle
            triangle: The triangle containing the point
        """
        self.point = point
        self.triangle = triangle
        super().__init__(
            f"Point ({point.x:.3f}, {point.y:.3f}, {point.z:.3f}) lies on mesh triangle "
            f"with vertices: "
            f"({triangle.v1.x:.3f}, {triangle.v1.y:.3f}, {triangle.v1.z:.3f}), "
            f"({triangle.v2.x:.3f}, {triangle.v2.y:.3f}, {triangle.v2.z:.3f}), "
            f"({triangle.v3.x:.3f}, {triangle.v3.y:.3f}, {triangle.v3.z:.3f})"
        )


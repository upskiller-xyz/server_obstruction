"""
Intersection point data structure

Represents a point where a plane intersects a triangle.
"""
from dataclasses import dataclass
from src.components.geometry import Point3D, Triangle


@dataclass(frozen=True)
class IntersectionPoint:
    """Point where plane intersects triangle, with metadata"""
    point: Point3D
    triangle: Triangle
    angle: float  # Obstruction angle in radians

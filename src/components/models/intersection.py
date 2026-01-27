from dataclasses import dataclass

from src.components.geometry import Point3D


@dataclass
class IntersectionResult:
    point: Point3D | None
    angle: float

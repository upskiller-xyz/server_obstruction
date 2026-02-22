"""Geometry components for 3D calculations"""

from src.components.geometry.coordinate_system import CoordinateSystem
from src.components.geometry.point import Point3D
from src.components.geometry.vector import Vector3D
from src.components.geometry.angle_calculator import AngleCalculator
from src.components.geometry.triangle import Triangle
from src.components.geometry.mesh import Mesh
from src.components.geometry.projected_point import ProjectedPoint
from src.components.geometry.projection_plane import ProjectionPlane
from src.components.geometry.projected_triangle import ProjectedTriangle
from src.components.geometry.reference_point import ReferencePointCalculator

# NOTE: VerticalPlane is NOT exported from here to avoid circular imports
# It depends on Window from models, which depends on geometry
# Import it directly: from src.components.geometry.vertical_plane import VerticalPlane

__all__ = [
    'CoordinateSystem',
    'Point3D',
    'Vector3D',
    'AngleCalculator',
    'Triangle',
    'Mesh',
    'ProjectedPoint',
    'ProjectionPlane',
    'ProjectedTriangle',
    'ReferencePointCalculator'
]

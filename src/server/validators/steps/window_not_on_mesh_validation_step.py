"""
Window not on mesh validation step

Validates that window center doesn't lie on any mesh triangle.
"""

from typing import Dict, Any

from src.server.base.constants import RequestField
from src.server.validators.geometry_validator import GeometryValidator
from src.components.geometry import Point3D, Mesh
from src.server.validators.steps.validation_step import ValidationStep


class WindowNotOnMeshValidationStep(ValidationStep):
    """Validates that window center doesn't lie on any mesh triangle"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check window center is not on mesh surface"""
        # Extract window center
        window_center = Point3D(
            x=float(data[RequestField.X.value]),
            y=float(data[RequestField.Y.value]),
            z=float(data[RequestField.Z.value])
        )

        # Create mesh from vertices
        mesh = Mesh.from_vertices(data[RequestField.MESH.value])

        # Validate window center doesn't lie on any triangle
        GeometryValidator.validate_point_not_on_mesh(
            window_center,
            mesh.triangles
        )

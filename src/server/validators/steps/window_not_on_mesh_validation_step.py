"""
Window not on mesh validation step

Validates that window center doesn't lie on any mesh triangle.
"""

from typing import Any, Dict

from src.components.geometry import Mesh, Point3D, ReferencePointCalculator
from src.server.base.constants import RequestField
from src.server.validators.geometry_validator import GeometryValidator
from src.server.validators.steps.validation_step import ValidationStep


class WindowNotOnMeshValidationStep(ValidationStep):
    """Validates that window center doesn't lie on any mesh triangle"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check window center is not on mesh surface (auto-detects format)"""
        window_center = cls._extract_center(data)

        # Collect all mesh keys present in request
        mesh_keys = [
            RequestField.MESH.value
        ]

        for key in mesh_keys:
            mesh_raw = data.get(key)
            if not mesh_raw:
                continue
            mesh = Mesh.from_vertices(mesh_raw)
            GeometryValidator.validate_point_not_on_mesh(window_center, mesh.triangles)

    @staticmethod
    def _extract_center(data: Dict[str, Any]) -> Point3D:
        """Extract or compute window center from request data."""
        if RequestField.X1.value in data:
            # Endpoint format: compute center from endpoints + room_polygon
            return ReferencePointCalculator.calculate(
                float(data[RequestField.X1.value]),
                float(data[RequestField.Y1.value]),
                float(data[RequestField.Z1.value]),
                float(data[RequestField.X2.value]),
                float(data[RequestField.Y2.value]),
                float(data[RequestField.Z2.value]),
                data[RequestField.ROOM_POLYGON.value],
            )

        # Center format
        return Point3D(
            x=float(data[RequestField.X.value]),
            y=float(data[RequestField.Y.value]),
            z=float(data[RequestField.Z.value])
        )

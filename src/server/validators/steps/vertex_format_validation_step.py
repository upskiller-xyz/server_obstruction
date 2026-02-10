"""
Vertex format validation step

Validates individual vertex format.
Supports both split (horizon_mesh/zenith_mesh) and legacy (mesh) formats.
"""

from typing import Dict, Any, List

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep


class VertexFormatValidationStep(ValidationStep):
    """Validates individual vertex format for all mesh fields present"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Validate each vertex has 3 coordinates in all mesh fields"""
        mesh_keys: List[str] = []

        if RequestField.MESH.value in data:
            mesh_keys.append(RequestField.MESH.value)
        if RequestField.HORIZON_MESH.value in data:
            mesh_keys.append(RequestField.HORIZON_MESH.value)
        if RequestField.ZENITH_MESH.value in data:
            mesh_keys.append(RequestField.ZENITH_MESH.value)

        for key in mesh_keys:
            mesh = data[key]
            if isinstance(mesh, dict):
                for sub_key in ("horizon", "zenith"):
                    cls._validate_vertices(mesh.get(sub_key, []), f"{key}.{sub_key}")
            else:
                cls._validate_vertices(mesh, key)

    @classmethod
    def _validate_vertices(cls, mesh: list, label: str) -> None:
        """Validate each vertex in a mesh list has 3 coordinates."""
        for i, vertex in enumerate(mesh):
            if not isinstance(vertex, (list, tuple)) or len(vertex) != 3:
                raise ValueError(
                    f"{label} vertex {i} must be a list/tuple of 3 coordinates [x, y, z]"
                )

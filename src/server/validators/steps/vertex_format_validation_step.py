"""
Vertex format validation step

Validates individual vertex format.
Supports both split (horizon_mesh/zenith_mesh) and legacy (mesh) formats.
"""

from typing import Dict, Any, List

from src.server.base.constants import ANGLES, RequestField
from src.server.validators.steps.validation_step import ValidationStep


class VertexFormatValidationStep(ValidationStep):
    """Validates individual vertex format for all mesh fields present"""

    @classmethod
    def call(cls, content: Dict[str, Any]) -> None: # type: ignore
        """Validate each vertex has 3 coordinates in all mesh fields"""
        mesh_keys: List[RequestField] = [RequestField.MESH, RequestField.HORIZON_MESH, RequestField.ZENITH_MESH]
        mesh_keys = [k for k in mesh_keys if k.value in content]
        

        for key in mesh_keys:
            mesh = content[key.value]
            if isinstance(mesh, dict):
                for angle in ANGLES:
                    cls._validate_vertices(mesh.get(angle.value, []), f"{key}.{angle.value}")
            else:
                cls._validate_vertices(mesh, key.value)

    @classmethod
    def _validate_vertices(cls, mesh: list, label: str) -> None:
        """Validate each vertex in a mesh list has 3 coordinates."""
        for i, vertex in enumerate(mesh):
            if not isinstance(vertex, (list, tuple)) or len(vertex) != 3:
                raise ValueError(
                    f"{label} vertex {i} must be a list/tuple of 3 coordinates [x, y, z]"
                )

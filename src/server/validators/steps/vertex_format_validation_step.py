"""
Vertex format validation step

Validates individual vertex format.
"""

from typing import Dict, Any

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep


class VertexFormatValidationStep(ValidationStep):
    """Validates individual vertex format"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Validate each vertex has 3 coordinates"""
        mesh = data[RequestField.MESH.value]

        for i, vertex in enumerate(mesh):
            if not isinstance(vertex, (list, tuple)) or len(vertex) != 3:
                raise ValueError(
                    f"Vertex {i} must be a list/tuple of 3 coordinates [x, y, z]"
                )

"""
Mesh format validation step

Validates mesh format and structure.
"""

from typing import Dict, Any
import logging

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep

logger = logging.getLogger(__name__)


class MeshFormatValidationStep(ValidationStep):
    """Validates mesh format and structure"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Validate mesh is a list with proper structure"""
        mesh = data[RequestField.MESH.value]

        if not isinstance(mesh, list):
            raise ValueError("Mesh must be a list of vertices")

        if len(mesh) == 0:
            raise ValueError("Mesh cannot be empty")

        # Handle mesh vertices not divisible by 3
        if len(mesh) % 3 != 0:
            extra_vertices = len(mesh) % 3
            original_count = len(mesh)
            # Trim extra vertices (1-2 vertices)
            data[RequestField.MESH.value] = mesh[:-extra_vertices]
            logger.warning(
                f"Mesh had {original_count} vertices (not divisible by 3). "
                f"Trimmed {extra_vertices} extra vertex/vertices. "
                f"Proceeding with {len(data[RequestField.MESH.value])} vertices."
            )

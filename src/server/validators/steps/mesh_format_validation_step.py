"""
Mesh format validation step

Validates mesh format and structure.
Supports both split (horizon_mesh/zenith_mesh) and legacy (mesh) formats.
"""

from typing import Dict, Any, List
import logging

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep

logger = logging.getLogger(__name__)


class MeshFormatValidationStep(ValidationStep):
    """Validates mesh format and structure for all mesh fields present"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Validate mesh(es) are lists with proper structure"""
        mesh_keys: List[str] = []

        if RequestField.MESH.value in data:
            mesh_keys.append(RequestField.MESH.value)
        if RequestField.HORIZON_MESH.value in data:
            mesh_keys.append(RequestField.HORIZON_MESH.value)
        if RequestField.ZENITH_MESH.value in data:
            mesh_keys.append(RequestField.ZENITH_MESH.value)

        for key in mesh_keys:
            cls._validate_single_mesh(data, key)

    @classmethod
    def _validate_single_mesh(cls, data: Dict[str, Any], key: str) -> None:
        """Validate a single mesh field."""
        mesh = data[key]

        if not isinstance(mesh, list):
            raise ValueError(f"{key} must be a list of vertices")

        if len(mesh) == 0:
            return

        if len(mesh) % 3 != 0:
            extra_vertices = len(mesh) % 3
            original_count = len(mesh)
            data[key] = mesh[:-extra_vertices]
            logger.warning(
                f"{key} had {original_count} vertices (not divisible by 3). "
                f"Trimmed {extra_vertices} extra vertex/vertices. "
                f"Proceeding with {len(data[key])} vertices."
            )

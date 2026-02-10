"""
Mesh format validation step

Validates mesh format and structure.
Supports both split (horizon_mesh/zenith_mesh) and legacy (mesh) formats.
"""

from typing import Dict, Any, List
import logging

from src.server.base.constants import ANGLES, RequestField
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
        """Validate a single mesh field.

        Accepts either:
        - A flat list of vertices: [[x,y,z], ...]
        - A nested dict with horizon/zenith: {"horizon": [...], "zenith": [...]}
        """
        mesh = data[key]

        if isinstance(mesh, dict):
            for angle in ANGLES:
                sub_mesh = mesh.get(angle.value, [])
                if not isinstance(sub_mesh, list):
                    raise ValueError(f"{key}.{angle.value} must be a list of vertices")
                cls._validate_vertex_count(sub_mesh, f"{key}.{angle.value}")
                mesh[angle.value] = sub_mesh
            return

        if not isinstance(mesh, list):
            raise ValueError(f"{key} must be a list of vertices or a dict with horizon/zenith")

        cls._validate_vertex_count(mesh, key)
        data[key] = mesh

    @classmethod
    def _validate_vertex_count(cls, mesh: list, label: str) -> None:
        """Warn and trim if vertex count is not divisible by 3."""
        if len(mesh) == 0:
            return

        if len(mesh) % 3 != 0:
            extra_vertices = len(mesh) % 3
            original_count = len(mesh)
            del mesh[-extra_vertices:]
            logger.warning(
                f"{label} had {original_count} vertices (not divisible by 3). "
                f"Trimmed {extra_vertices} extra vertex/vertices. "
                f"Proceeding with {len(mesh)} vertices."
            )

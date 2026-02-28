"""
Mesh format validation step

Validates mesh format and structure.
Supports both split (horizon_mesh/zenith_mesh) and legacy (mesh) formats.
"""

from typing import Dict, Any, List
import logging

from src.server.base.constants import ANGLES, RequestField
from src.server.validators.steps.validation_step import ValidationStep


class MeshFormatValidationStep(ValidationStep):
    """Validates mesh format and structure for all mesh fields present"""

    @classmethod
    def call(cls, content: Dict[str, Any]) -> None: # type: ignore
        """Validate mesh(es) are lists with proper structure"""
        mesh_keys: List[RequestField] = [RequestField.MESH, RequestField.HORIZON_MESH, RequestField.ZENITH_MESH]
        mesh_keys = [k for k in mesh_keys if k.value in content]
        
        _ = [cls._validate_single_mesh(content, key) for key in mesh_keys]

    @classmethod
    def _validate_single_mesh(cls, data: Dict[str, Any], key: RequestField) -> None:
        """Validate a single mesh field.

        Accepts either:
        - A flat list of vertices: [[x,y,z], ...]
        - A nested dict with horizon/zenith: {"horizon": [...], "zenith": [...]}
        """
        mesh = data[key.value]

        if isinstance(mesh, dict):
            for angle in ANGLES:
                sub_mesh = mesh.get(angle.value, [])
                if not isinstance(sub_mesh, list):
                    raise ValueError(f"{key.value}.{angle.value} must be a list of vertices")
                cls._validate_vertex_count(sub_mesh, f"{key.value}.{angle.value}")
                mesh[angle.value] = sub_mesh
            return

        if not isinstance(mesh, list):
            raise ValueError(f"{key.value} must be a list of vertices or a dict with horizon/zenith")

        cls._validate_vertex_count(mesh, key.value)
        data[key.value] = mesh

    @classmethod
    def _validate_vertex_count(cls, mesh: list, label: str) -> None:
        """Warn and trim if vertex count is not divisible by 3."""
        if len(mesh) == 0:
            return

        if len(mesh) % 3 != 0:
            extra_vertices = len(mesh) % 3
            original_count = len(mesh)
            del mesh[-extra_vertices:]
            logging.warning(
                f"{label} had {original_count} vertices (not divisible by 3). "
                f"Trimmed {extra_vertices} extra vertex/vertices. "
                f"Proceeding with {len(mesh)} vertices."
            )

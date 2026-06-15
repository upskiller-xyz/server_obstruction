"""
Mesh format validation step

Validates mesh format and structure.
Accepts a single mesh parameter with combined geometry.
"""

import logging
from typing import Any, Dict, List

import numpy as np

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep


class MeshFormatValidationStep(ValidationStep):
    """Validates mesh format and structure for all mesh fields present"""

    @classmethod
    def call(cls, content: Dict[str, Any]) -> None: # type: ignore
        """Validate mesh(es) are lists with proper structure"""
        mesh_keys: List[RequestField] = [RequestField.MESH]
        mesh_keys = [k for k in mesh_keys if k.value in content]
        
        _ = [cls._validate_single_mesh(content, key) for key in mesh_keys]

    @classmethod
    def _validate_single_mesh(cls, data: Dict[str, Any], key: RequestField) -> None:
        """Validate a single mesh field.

        Accepts a flat list of vertices ``[[x, y, z], ...]`` (JSON path) or an
        ``(N, 3)`` numpy array (binary path). Trims to a multiple of 3 vertices.
        """
        mesh = data[key.value]

        if isinstance(mesh, np.ndarray):
            if mesh.ndim != 2 or mesh.shape[1] != 3:
                raise ValueError(f"{key.value} must be an (N, 3) array of vertices")
            extra = len(mesh) % 3
            if extra:
                logging.warning(
                    f"{key.value} had {len(mesh)} vertices (not divisible by 3). "
                    f"Trimmed {extra}."
                )
                data[key.value] = mesh[: len(mesh) - extra]
            return

        if not isinstance(mesh, list):
            raise ValueError(f"{key.value} must be a list of vertices")

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

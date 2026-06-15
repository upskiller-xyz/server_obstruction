"""
Vertex format validation step

Validates individual vertex format.
Accepts a single mesh parameter with combined geometry.
"""

from typing import Any, Dict, List

import numpy as np

from src.server.base.constants import ANGLES, RequestField
from src.server.validators.steps.validation_step import ValidationStep


class VertexFormatValidationStep(ValidationStep):
    """Validates individual vertex format for all mesh fields present"""

    @classmethod
    def call(cls, content: Dict[str, Any]) -> None: # type: ignore
        """Validate each vertex has 3 coordinates in all mesh fields"""
        mesh_keys: List[RequestField] = [RequestField.MESH]
        mesh_keys = [k for k in mesh_keys if k.value in content]
        

        for key in mesh_keys:
            mesh = content[key.value]
            if isinstance(mesh, dict):
                for angle in ANGLES:
                    cls._validate_vertices(mesh.get(angle.value, []), f"{key}.{angle.value}")
            else:
                cls._validate_vertices(mesh, key.value)

    @classmethod
    def _validate_vertices(cls, mesh, label: str) -> None:
        """Validate each vertex has 3 coordinates (list path) or (N, 3) shape (array path)."""
        # Array path: shape already guarantees 3 coords per vertex — O(1), no loop.
        if isinstance(mesh, np.ndarray):
            if mesh.ndim != 2 or mesh.shape[1] != 3:
                raise ValueError(
                    f"{label} must be an (N, 3) array of [x, y, z] coordinates"
                )
            return

        for i, vertex in enumerate(mesh):
            if not isinstance(vertex, (list, tuple)) or len(vertex) != 3:
                raise ValueError(
                    f"{label} vertex {i} must be a list/tuple of 3 coordinates [x, y, z]"
                )

"""
Obstruction request model

Input request for obstruction calculation.
Accepts a single mesh parameter for all geometry.

Window formats:
  - Center format: x, y, z, direction_angle
  - Endpoint format: x1, y1, z1, x2, y2, z2, direction_angle, room_polygon
"""

from typing import Optional
from dataclasses import dataclass

from src.components.geometry import Mesh
from src.components.models.window import Window
from src.server.base.constants import RequestField


@dataclass(frozen=True)
class ObstructionRequest:
    """Input request for obstruction calculation"""
    window: Window
    mesh: Optional[Mesh]

    @classmethod
    def from_dict(cls, data: dict) -> 'ObstructionRequest':
        """
        Create ObstructionRequest from dictionary.

        Mesh format detection:
            - If mesh present: parse as mesh geometry

        Window format detection:
            - If x1 present: endpoint format (calculates reference point)
            - If x present: center format (pre-computed center)

        Args:
            data: Dict with mesh and window fields

        Returns:
            ObstructionRequest instance
        """
        window = Window.from_dict(data)
        mesh = cls._parse_mesh(data)
        return cls(window=window, mesh=mesh)

    @classmethod
    def _parse_mesh(cls, content: dict) -> Optional[Mesh]:
        """Parse mesh from request data.

        Supports:
          - List format:  {"mesh": [[x,y,z], ...]} → single combined Mesh

        Raises:
          ValueError: if mesh is present but not a list.
        """
        mesh_data = content.get(RequestField.MESH.value, {})

        # List format: all geometry in one mesh
        if isinstance(mesh_data, list):
            return Mesh.from_vertices(mesh_data) if mesh_data else None

        raise ValueError(
            f"Unsupported mesh format: expected a list of vertices, got {type(mesh_data).__name__}. "
            "Provide mesh as a flat list of [x, y, z] vertex coordinates."
        )
    
    

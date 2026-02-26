"""
Obstruction request model

Input request for obstruction calculation.
Supports two mesh formats:
  - Split format: horizon_mesh + zenith_mesh (caller pre-separates geometry)
  - Legacy format: mesh (single combined mesh, server classifies surfaces internally)

And two window formats:
  - Center format: x, y, z, direction_angle
  - Endpoint format: x1, y1, z1, x2, y2, z2, direction_angle, room_polygon
"""

from typing import Optional, Tuple
from dataclasses import dataclass

from src.components.geometry import Mesh
from src.components.models.window import Window
from src.server.base.constants import ANGLES, RequestField


@dataclass(frozen=True)
class ObstructionRequest:
    """Input request for obstruction calculation"""
    window: Window
    horizon_mesh: Optional[Mesh]
    zenith_mesh: Optional[Mesh]

    @classmethod
    def from_dict(cls, data: dict) -> 'ObstructionRequest':
        """
        Create ObstructionRequest from dictionary (auto-detects format).

        Mesh format detection:
            - If horizon_mesh or zenith_mesh present: split format
            - If mesh present: legacy format (assign to both)

        Window format detection:
            - If x1 present: endpoint format (calculates reference point)
            - If x present: center format (pre-computed center)

        Args:
            data: Dict with mesh(es) and window fields

        Returns:
            ObstructionRequest instance
        """
        window = Window.from_dict(data)
        horizon_mesh, zenith_mesh = cls._parse_meshes(data)
        return cls(window=window, horizon_mesh=horizon_mesh, zenith_mesh=zenith_mesh)

    @classmethod
    def _parse_meshes(cls, content: dict) -> Tuple[Optional[Mesh], Optional[Mesh]]:
        """Detect mesh format and parse accordingly.

        Supports:
          - Split dict: {"mesh": {"horizon": [...], "zenith": [...]}}
          - Flat list:  {"mesh": [[x,y,z], ...]} → all triangles go to horizon_mesh
        """
        mesh_data = content.get(RequestField.MESH.value, {})

        # Flat list format: all geometry in one mesh, no horizon/zenith split
        if isinstance(mesh_data, list):
            mesh = Mesh.from_vertices(mesh_data) if mesh_data else None
            return mesh, None

        return cls._parse_mesh(mesh_data, ANGLES.HORIZON), cls._parse_mesh(mesh_data, ANGLES.ZENITH)

    @classmethod
    def _parse_mesh(cls, mesh_data: dict, angle: ANGLES) -> Optional[Mesh]:
        """Parse a single mesh from split dict format.

        Accepts both string keys ("horizon", "zenith") and enum keys (ANGLES.HORIZON, ANGLES.ZENITH).
        """
        raw = mesh_data.get(angle.value) or mesh_data.get(angle, [])
        return Mesh.from_vertices(raw) if raw else None
    
    

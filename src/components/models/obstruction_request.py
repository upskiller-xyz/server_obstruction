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
        window = cls._parse_window(data)
        horizon_mesh, zenith_mesh = cls._parse_meshes(data)
        return cls(window=window, horizon_mesh=horizon_mesh, zenith_mesh=zenith_mesh)

    @staticmethod
    def _parse_meshes(data: dict) -> Tuple[Optional[Mesh], Optional[Mesh]]:
        """Detect mesh format and parse accordingly.

        Supports nested format: {"mesh": {"horizon": [...], "zenith": [...]}}
        and legacy format: {"mesh": [[x,y,z], ...]} (assigned to both).
        """
        mesh_data = data.get(RequestField.MESH.value, {})

        # Nested format: mesh is a dict with horizon/zenith sub-keys
        if isinstance(mesh_data, dict):
            horizon_raw = mesh_data.get(ANGLES.HORIZON.value, [])
            zenith_raw = mesh_data.get(ANGLES.ZENITH.value, [])
            horizon_mesh = Mesh.from_vertices(horizon_raw) if horizon_raw else None
            zenith_mesh = Mesh.from_vertices(zenith_raw) if zenith_raw else None
            return horizon_mesh, zenith_mesh

        # Legacy: single mesh list assigned to both
        if mesh_data:
            mesh = Mesh.from_vertices(mesh_data)
            return mesh, mesh
        return None, None

    @staticmethod
    def _parse_window(data: dict) -> Window:
        """Detect request format and create Window accordingly."""
        if RequestField.X1.value in data:
            return Window.from_endpoints(
                x1=float(data[RequestField.X1.value]),
                y1=float(data[RequestField.Y1.value]),
                z1=float(data[RequestField.Z1.value]),
                x2=float(data[RequestField.X2.value]),
                y2=float(data[RequestField.Y2.value]),
                z2=float(data[RequestField.Z2.value]),
                direction_angle=float(data[RequestField.DIRECTION_ANGLE.value]),
                room_polygon=data[RequestField.ROOM_POLYGON.value],
            )

        return Window.from_dict(data)

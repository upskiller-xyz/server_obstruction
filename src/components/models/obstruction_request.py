"""
Obstruction request model

Input request for obstruction calculation.
Supports two formats:
  - Center format: x, y, z, direction_angle, mesh
  - Endpoint format: x1, y1, z1, x2, y2, z2, direction_angle, room_polygon, mesh
"""

from dataclasses import dataclass

from src.components.geometry import Mesh
from src.components.models.window import Window
from src.server.base.constants import RequestField


@dataclass(frozen=True)
class ObstructionRequest:
    """Input request for obstruction calculation"""
    window: Window
    mesh: Mesh

    @classmethod
    def from_dict(cls, data: dict) -> 'ObstructionRequest':
        """
        Create ObstructionRequest from dictionary (auto-detects format).

        Endpoint format (x1, y1, z1, x2, y2, z2 + room_polygon):
            Calculates reference point by projecting window center onto
            room polygon boundary.

        Center format (x, y, z):
            Uses pre-computed center directly.

        Args:
            data: Dict with mesh and either center or endpoint fields

        Returns:
            ObstructionRequest instance
        """
        window = cls._parse_window(data)
        mesh = Mesh.from_vertices(data[RequestField.MESH.value])
        return cls(window=window, mesh=mesh)

    @staticmethod
    def _parse_window(data: dict) -> Window:
        """Detect request format and create Window accordingly."""
        # Endpoint format: x1, y1, z1, x2, y2, z2 + room_polygon
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

        # Center format: x, y, z
        return Window.from_dict(data)

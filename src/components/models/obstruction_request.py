"""
Obstruction request model

Input request for obstruction calculation.
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
        Create ObstructionRequest from dictionary

        Args:
            data: Dict with keys:
                - x, y, z: window center coordinates
                - direction_angle: horizontal rotation angle in radians (0 to 2π)
                - mesh: list of vertices (every 3 form a triangle)

        Returns:
            ObstructionRequest instance
        """
        window = Window.from_dict(data)
        mesh = Mesh.from_vertices(data[RequestField.MESH.value])
        return cls(window=window, mesh=mesh)

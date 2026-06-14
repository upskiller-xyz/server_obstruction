"""Request payload builders for microservice communication"""

from typing import Any, Dict, List



class ParallelRequestBuilder:
    """
    Builder Pattern implementation for constructing parallel request payloads

    Single Responsibility:
    - Only builds request payloads for microservice calls
    - Does NOT handle headers or HTTP concerns
    """

    def build_payload(
        self,
        x: float,
        y: float,
        z: float,
        direction_angle: float,
        mesh_vertices: List[List[float]]
    ) -> Dict[str, Any]:
        """
        Build payload for single direction request

        Args:
            x, y, z: Window position coordinates
            direction_angle: Absolute direction in radians
            mesh_vertices: 3D mesh geometry

        Returns:
            Dictionary payload for HTTP request
        """
        return {
            "x": x,
            "y": y,
            "z": z,
            "direction_angle": direction_angle,
            "mesh": mesh_vertices
        }

"""Mesh filtering service for combining and filtering meshes"""

import logging
from typing import Optional

from src.components.filter import CoarseTriangleFilter, HeightTriangleFilter
from src.components.geometry import Mesh
from src.components.models import Window
from src.server.base.constants import ANGLES


class MeshFilterService:
    """
    Service for filtering and combining meshes

    Single Responsibility:
    - Only handles mesh filtering operations
    - Does NOT perform calculations or direction computations
    """

    @staticmethod
    def apply_height_filter(
        mesh: Mesh,
        window: Window
    ) -> Mesh:
        """
        Apply height-only filtering (remove triangles below window)

        Args:
            mesh: Mesh to filter
            window: Window for filtering

        Returns:
            Filtered mesh
        """
        if not mesh.triangles:
            return Mesh.empty()

        filtered = HeightTriangleFilter.call(mesh.triangles, window, ANGLES.HORIZON)
        return Mesh(filtered)

    @staticmethod
    def apply_coarse_filter(
        mesh: Optional[Mesh],
        window: Window,
        label: str = ""
    ) -> Mesh:
        """
        Apply coarse triangle filter to a mesh

        Args:
            mesh: Mesh to filter or None
            window: Window for filtering
            label: Label for logging

        Returns:
            Filtered mesh (empty Mesh if input is None)
        """
        if mesh is None:
            return Mesh.empty()

        coarse_filtered = CoarseTriangleFilter.call(mesh.triangles, window)
        removed = len(mesh.triangles) - len(coarse_filtered)
        logging.debug(
            f"[PRE-FILTER] {label}: removed {removed} triangles "
            f"({len(coarse_filtered)} remaining)"
        )
        return Mesh(coarse_filtered)

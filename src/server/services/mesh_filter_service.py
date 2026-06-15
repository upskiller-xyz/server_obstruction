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
        # Array-native: mask the (M,3,3) vertex array directly, no Triangle objects.
        array = mesh.vertices_array
        if len(array) == 0:
            return Mesh.empty()

        keep_mask = HeightTriangleFilter.mask(array, window)
        return Mesh.from_array(array[keep_mask])

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

        # Array-native: mask the (M,3,3) vertex array directly, no Triangle objects.
        array = mesh.vertices_array
        if len(array) == 0:
            return Mesh.empty()

        keep_mask = CoarseTriangleFilter.mask(array, window)
        kept = array[keep_mask]
        logging.debug(
            f"[PRE-FILTER] {label}: removed {len(array) - len(kept)} triangles "
            f"({len(kept)} remaining)"
        )
        return Mesh.from_array(kept)

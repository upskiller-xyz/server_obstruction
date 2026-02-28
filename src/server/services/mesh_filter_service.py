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
    def combine_and_filter(
        horizon_mesh: Optional[Mesh],
        zenith_mesh: Optional[Mesh],
        window: Window
    ) -> Mesh:
        """
        Combine horizon and zenith meshes and apply coarse pre-filter

        Args:
            horizon_mesh: Horizon mesh (walls/buildings) or None
            zenith_mesh: Zenith mesh (roofs/slabs) or None
            window: Window for filtering

        Returns:
            Single combined and pre-filtered Mesh
        """
        h_tris = horizon_mesh.triangles if horizon_mesh and horizon_mesh.triangles else ()
        z_tris = zenith_mesh.triangles if zenith_mesh and zenith_mesh.triangles else ()

        all_triangles = h_tris + z_tris

        if not all_triangles:
            return Mesh(())

        # Apply coarse pre-filter (remove triangles below/behind window)
        filtered = CoarseTriangleFilter.call(all_triangles, window)
        removed = len(all_triangles) - len(filtered)
        logging.debug(
            f"[PRE-FILTER] Combined mesh: {len(all_triangles)} -> {len(filtered)} "
            f"triangles (removed {removed})"
        )
        return Mesh(filtered)

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
            return Mesh(())

        filtered = HeightTriangleFilter.call(mesh.triangles, window, ANGLES.HORIZON)
        return Mesh(filtered)

    @staticmethod
    def apply_coarse_filter(
        mesh: Optional[Mesh],
        window: Window,
        label: str = ""
    ) -> Optional[Mesh]:
        """
        Apply coarse triangle filter to a mesh

        Args:
            mesh: Mesh to filter or None
            window: Window for filtering
            label: Label for logging

        Returns:
            Filtered mesh or None
        """
        if mesh is None:
            return None

        coarse_filtered = CoarseTriangleFilter.call(mesh.triangles, window)
        removed = len(mesh.triangles) - len(coarse_filtered)
        logging.debug(
            f"[PRE-FILTER] {label}: removed {removed} triangles "
            f"({len(coarse_filtered)} remaining)"
        )
        return Mesh(coarse_filtered)

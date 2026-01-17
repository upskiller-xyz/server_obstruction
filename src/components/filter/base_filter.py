"""
Base class for triangle filtering strategies

Provides abstract base class and common filtering utilities using Template Method Pattern.
"""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np

from src.components.geometry import Vector3D, Triangle
from src.server.base.constants import ANGLES
from src.components.models import Window


class TriangleFilter(ABC):
    """
    Abstract base class for triangle filtering strategies

    Uses Template Method Pattern:
    - Common vectorization logic in base class
    - Specific filtering criteria in child classes

    Responsibilities (Single Responsibility Principle):
    - Vectorize triangle data for efficient numpy operations
    - Provide common filtering utilities (height, direction)
    - Define interface for specific filtering strategies
    """

    @classmethod
    def call(
        cls,
        triangles: Tuple[Triangle, ...],
        window: Window,
        angle_type: ANGLES,
        **kwargs
    ) -> Tuple[Triangle, ...]:
        """
        Filter triangles based on specific criteria (implemented by subclasses)

        Args:
            triangles: All mesh triangles
            window: Window
            angle_type: Type of angle calculation (HORIZON or ZENITH)
            **kwargs: Additional filter-specific parameters

        Returns:
            Filtered list of triangles
        """
        return tuple()

    @staticmethod
    def _vectorize_triangles(triangles: Tuple[Triangle, ...]) -> np.ndarray:
        """
        Convert triangles to vectorized numpy array for efficient operations

        Args:
            triangles: Tuple of Triangle objects

        Returns:
            Array of shape (N, 3, 3) where N is number of triangles,
            first 3 is vertices (v1, v2, v3), second 3 is coords (x, y, z)
        """
        n_triangles = len(triangles)
        vertices_array = np.empty((n_triangles, 3, 3), dtype=np.float64)
        for i, t in enumerate(triangles):
            vertices_array[i, 0] = t.v1.to_array()
            vertices_array[i, 1] = t.v2.to_array()
            vertices_array[i, 2] = t.v3.to_array()
        return vertices_array

    @staticmethod
    def _filter_by_height(
        vertices_array: np.ndarray,
        window_z: float
    ) -> np.ndarray:
        """
        Filter triangles by height (above window)

        Args:
            vertices_array: Vectorized triangles (N, 3, 3)
            window_z: Window Z coordinate

        Returns:
            Boolean mask of shape (N,) - True if triangle max Z > window Z
        """
        max_z_per_triangle = vertices_array[:, :, 2].max(axis=1)
        return max_z_per_triangle > window_z

    @staticmethod
    def _compute_horizontal_normal(window_normal: Vector3D) -> Tuple[np.ndarray, np.floating]:
        """
        Compute horizontal component of window normal and its magnitude

        Args:
            window_normal: Window viewing direction

        Returns:
            Tuple of (horizontal_normal_array, magnitude)
        """
        normal_arr = window_normal.to_array()
        normal_horizontal = np.array([normal_arr[0], normal_arr[1], 0.0])
        normal_horizontal_mag = np.linalg.norm(normal_horizontal)
        return normal_horizontal, normal_horizontal_mag

    @staticmethod
    def _build_filtered_list(
        triangles: Tuple[Triangle, ...],
        keep_mask: np.ndarray
    ) -> Tuple[Triangle, ...]:
        """
        Build filtered triangle list from boolean mask

        Args:
            triangles: Original triangles (tuple or list)
            keep_mask: Boolean mask (N,)

        Returns:
            List of triangles where keep_mask is True
        """
        keep_indices = np.where(keep_mask)[0]
        return tuple(triangles[int(i)] for i in keep_indices)

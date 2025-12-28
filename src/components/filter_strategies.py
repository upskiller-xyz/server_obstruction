"""
Triangle filtering strategies using Strategy Pattern

This module implements different filtering strategies for triangles,
following the Strategy Pattern and using classmethods for operations.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np
from src.components.geometry import Triangle, Point3D, Vector3D


class TriangleFilterStrategy(ABC):
    """
    Abstract base class for triangle filtering strategies

    Following Strategy Pattern: Each filter strategy is a separate class
    with a common interface, allowing strategies to be swapped easily.
    """

    @classmethod
    @abstractmethod
    def filter(
        cls,
        triangles: List[Triangle],
        window_center: Point3D,
        window_normal: Vector3D,
        **kwargs
    ) -> List[Triangle]:
        """
        Filter triangles based on strategy-specific criteria

        Args:
            triangles: Tuple of triangles to filter
            window_center: Window center point
            window_normal: Window normal vector
            **kwargs: Additional strategy-specific parameters

        Returns:
            List of filtered triangles
        """
        pass


class HeightAndDirectionFilter(TriangleFilterStrategy):
    """
    Filter triangles by height and direction

    Removes triangles that are:
    1. Below the window center (height filter)
    2. Behind the window (direction filter)
    """

    @classmethod
    def filter(
        cls,
        triangles: List[Triangle],
        window_center: Point3D,
        window_normal: Vector3D,
        **kwargs
    ) -> List[Triangle]:
        """Filter triangles below window and behind viewing direction"""
        if not triangles:
            return []

        # Convert to numpy arrays for vectorized operations
        vertices = np.array([[t.v1.to_array(), t.v2.to_array(), t.v3.to_array()] for t in triangles])
        centroids = vertices.mean(axis=1)

        # Height filter: keep triangles at or above window center
        height_mask = centroids[:, 2] >= window_center.z

        # Direction filter: keep triangles in front of window
        to_centroid = centroids - np.array([window_center.x, window_center.y, window_center.z])
        normal_arr = window_normal.to_array()
        dot_products = np.dot(to_centroid, normal_arr)
        direction_mask = dot_products > 0

        # Combine masks
        combined_mask = height_mask & direction_mask

        return [triangles[i] for i in range(len(triangles)) if combined_mask[i]]


class HeightOnlyFilter(TriangleFilterStrategy):
    """
    Filter triangles by height only

    Removes triangles below the window center.
    Used for calculations that don't depend on viewing direction.
    """

    @classmethod
    def filter(
        cls,
        triangles: List[Triangle],
        window_center: Point3D,
        window_normal: Vector3D,
        **kwargs
    ) -> List[Triangle]:
        """Filter triangles below window center"""
        if not triangles:
            return []

        vertices = np.array([[t.v1.to_array(), t.v2.to_array(), t.v3.to_array()] for t in triangles])
        centroids = vertices.mean(axis=1)

        # Keep triangles at or above window center
        height_mask = centroids[:, 2] >= window_center.z

        return [triangles[i] for i in range(len(triangles)) if height_mask[i]]


class DirectionOnlyFilter(TriangleFilterStrategy):
    """
    Filter triangles by direction only

    Removes triangles behind the viewing direction.
    Used when height filtering is not needed.
    """

    @classmethod
    def filter(
        cls,
        triangles: List[Triangle],
        window_center: Point3D,
        window_normal: Vector3D,
        **kwargs
    ) -> List[Triangle]:
        """Filter triangles behind viewing direction"""
        if not triangles:
            return []

        vertices = np.array([[t.v1.to_array(), t.v2.to_array(), t.v3.to_array()] for t in triangles])
        centroids = vertices.mean(axis=1)

        # Direction filter: keep triangles in front of window
        to_centroid = centroids - np.array([window_center.x, window_center.y, window_center.z])
        normal_arr = window_normal.to_array()
        dot_products = np.dot(to_centroid, normal_arr)
        direction_mask = dot_products > 0

        return [triangles[i] for i in range(len(triangles)) if direction_mask[i]]


class HorizonFilter(TriangleFilterStrategy):
    """
    Filter triangles for horizon angle calculations

    Applies multiple filters:
    1. Height filter (above window)
    2. Direction filter (in front of window)
    3. Distance filter (minimum horizontal distance)
    """

    @classmethod
    def filter(
        cls,
        triangles: List[Triangle],
        window_center: Point3D,
        window_normal: Vector3D,
        **kwargs
    ) -> List[Triangle]:
        """Filter triangles for horizon calculation"""
        min_horizontal_distance = kwargs.get('min_horizontal_distance', 1.0)

        if not triangles:
            return []

        vertices = np.array([[t.v1.to_array(), t.v2.to_array(), t.v3.to_array()] for t in triangles])
        centroids = vertices.mean(axis=1)

        # Height filter
        height_mask = centroids[:, 2] >= window_center.z

        # Direction filter
        to_centroid = centroids - np.array([window_center.x, window_center.y, window_center.z])
        normal_arr = window_normal.to_array()
        dot_products = np.dot(to_centroid, normal_arr)
        direction_mask = dot_products > 0

        # Distance filter (horizontal distance only - x,y plane)
        horizontal_distances = np.sqrt(
            (centroids[:, 0] - window_center.x)**2 +
            (centroids[:, 1] - window_center.y)**2
        )
        distance_mask = horizontal_distances >= min_horizontal_distance

        # Combine all masks
        combined_mask = height_mask & direction_mask & distance_mask

        return [triangles[i] for i in range(len(triangles)) if combined_mask[i]]


class ZenithFilter(TriangleFilterStrategy):
    """
    Filter triangles for zenith angle calculations

    Focuses on overhead obstructions, filtering triangles that:
    1. Are above the window
    2. Are in the viewing direction
    3. Meet minimum distance requirements
    """

    @classmethod
    def filter(
        cls,
        triangles: List[Triangle],
        window_center: Point3D,
        window_normal: Vector3D,
        **kwargs
    ) -> List[Triangle]:
        """Filter triangles for zenith calculation"""
        min_horizontal_distance = kwargs.get('min_horizontal_distance', 1.0)

        if not triangles:
            return []

        vertices = np.array([[t.v1.to_array(), t.v2.to_array(), t.v3.to_array()] for t in triangles])

        # For zenith, we look at max Z of each triangle (highest point)
        max_z_per_triangle = vertices[:, :, 2].max(axis=1)
        centroids = vertices.mean(axis=1)

        # Height filter: keep triangles above window
        height_mask = max_z_per_triangle > window_center.z

        # Direction filter
        to_centroid = centroids - np.array([window_center.x, window_center.y, window_center.z])
        normal_arr = window_normal.to_array()
        dot_products = np.dot(to_centroid, normal_arr)
        direction_mask = dot_products > 0

        # Distance filter
        horizontal_distances = np.sqrt(
            (centroids[:, 0] - window_center.x)**2 +
            (centroids[:, 1] - window_center.y)**2
        )
        distance_mask = horizontal_distances >= min_horizontal_distance

        # Combine masks
        combined_mask = height_mask & direction_mask & distance_mask

        return [triangles[i] for i in range(len(triangles)) if combined_mask[i]]


class CompositeFilter(TriangleFilterStrategy):
    """
    Composite filter that applies multiple strategies

    Uses Composite Pattern to combine multiple filter strategies.
    Useful for filtering with different criteria for different purposes.
    """

    @classmethod
    def filter(
        cls,
        triangles: List[Triangle],
        window_center: Point3D,
        window_normal: Vector3D,
        **kwargs
    ) -> Tuple[List[Triangle], List[Triangle]]:
        """
        Filter for both horizon and zenith simultaneously

        Returns:
            Tuple of (horizon_filtered, zenith_filtered) triangles
        """
        min_horizontal_distance = kwargs.get('min_horizontal_distance', 1.0)

        horizon_filtered = HorizonFilter.filter(
            triangles, window_center, window_normal,
            min_horizontal_distance=min_horizontal_distance
        )

        zenith_filtered = ZenithFilter.filter(
            triangles, window_center, window_normal,
            min_horizontal_distance=min_horizontal_distance
        )

        return horizon_filtered, zenith_filtered

"""
Triangle filtering for obstruction calculations

Provides base class and specialized filters using Strategy Pattern and Template Method Pattern.
Common vectorization and filtering logic is shared in the base class.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np
from src.components.geometry import Point3D, Vector3D, Triangle
from src.components.constants import MathConstants
import logging

logger = logging.getLogger(__name__)


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
    @abstractmethod
    def call(
        cls,
        triangles: List[Triangle],
        window_center: Point3D,
        window_normal: Vector3D,
        **kwargs
    ) -> List[List[Triangle]]:
        """
        Filter triangles based on specific criteria (implemented by subclasses)

        Args:
            triangles: All mesh triangles
            window_center: Window center point
            window_normal: Window viewing direction
            **kwargs: Additional filter-specific parameters

        Returns:
            Filtered list of triangles
        """
        pass

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
    ) -> List[Triangle]:
        """
        Build filtered triangle list from boolean mask

        Args:
            triangles: Original triangles (tuple or list)
            keep_mask: Boolean mask (N,)

        Returns:
            List of triangles where keep_mask is True
        """
        keep_indices = np.where(keep_mask)[0]
        return [triangles[int(i)] for i in keep_indices]


class HorizonTriangleFilter(TriangleFilter):
    """
    Filter triangles for horizon obstruction calculation

    Criteria:
    1. Triangle must be above window (Z axis)
    2. Triangle must be in front of window (following view direction)
    3. Triangle must be at least min_horizontal_distance away
    """

    @classmethod
    def call(
        cls,
        triangles: Tuple[Triangle, ...],
        window_center: Point3D,
        window_normal: Vector3D,
        min_horizontal_distance: float = 2.0
    ) -> List[Triangle]:
        """
        Filter triangles for horizon obstruction (VECTORIZED)

        Args:
            triangles: All mesh triangles
            window_center: Window center point
            window_normal: Window viewing direction
            min_horizontal_distance: Minimum horizontal distance (meters)

        Returns:
            Filtered list of relevant triangles
        """

        vecs, above_mask, normal_horizontal, normal_horizontal_mag = cls._precompute(triangles, window_center, window_normal)
        mask = cls._mask(normal_horizontal_mag, normal_horizontal, vecs, cls._extra_param(triangles, min_horizontal_distance))

        # Combine filters
        keep_mask = above_mask & mask

        # Build result and log stats
        filtered = cls._build_filtered_list(triangles, keep_mask)

        n_triangles = len(triangles)
        stats = {
            'kept': int(keep_mask.sum()),
            'below': int((~above_mask).sum()),
            'too_close_or_behind': int((above_mask & ~mask).sum())
        }

        logger.info(
            f"        [HORIZON-FILTER] Kept {stats['kept']}/{n_triangles} - "
            f"Filtered: {stats['below']} below window, "
            f"{stats['too_close_or_behind']} too close/behind (<{min_horizontal_distance}m)"
        )

        return filtered
    
    @classmethod
    def _extra_param(cls, triangles, min_hd):
        return min_hd
    
    @classmethod
    def _precompute(cls, triangles, window_center, window_normal):
        n_triangles = len(triangles)
        if n_triangles == 0:
            return []

        # Vectorize triangles
        vertices_array = cls._vectorize_triangles(triangles)
        window_arr = window_center.to_array()

        # Filter 1: Height (above window)
        above_mask = cls._filter_by_height(vertices_array, window_arr[2])

        # Filter 2: Direction and distance
        normal_horizontal, normal_horizontal_mag = cls._compute_horizontal_normal(window_normal)
        vecs = vertices_array - window_arr
        return vecs, above_mask, normal_horizontal, normal_horizontal_mag

    
    @classmethod
    def _mask(cls, normal_horizontal_mag, normal_horizontal, vecs, param):
        if normal_horizontal_mag < MathConstants.EPSILON.value:
            # Viewing straight up/down - check Euclidean horizontal distance
            horiz_vecs = vecs[:, :, :2]  # Only X, Y
            horiz_dists = np.linalg.norm(horiz_vecs, axis=2)
            return (horiz_dists >= param).any(axis=1)
        
        normal_horizontal = normal_horizontal / normal_horizontal_mag
        forward_distances = np.dot(vecs, normal_horizontal)

        # Triangle valid if ANY vertex is in front AND far enough
        in_front = forward_distances > 0
        far_enough = forward_distances >= param
        valid_vertex = in_front & far_enough
        return valid_vertex.any(axis=1)



class ZenithTriangleFilter(HorizonTriangleFilter):
    """
    Filter triangles for zenith (overhead) obstruction calculation

    Criteria:
    1. Triangle must be above window (Z axis)
    2. Triangle must be in front of window (along viewing direction)
    3. Triangle must be within maximum forward distance (e.g., 5m ahead)

    This ensures we only consider overhead obstructions that are directly
    in the viewing direction and close overhead, not distant surfaces.
    """

    @classmethod
    def call(
        cls,
        triangles: Tuple[Triangle, ...],
        window_center: Point3D,
        window_normal: Vector3D,
        max_forward_distance: float = 5.0  # Maximum distance ahead along viewing direction
    ) -> List[Triangle]:
        """
        Filter triangles for zenith calculation

        Args:
            triangles: Input triangles
            window_center: Window center point
            window_normal: Window viewing direction (unit vector)
            max_forward_distance: Maximum distance ahead (m) along viewing direction
                                 Default 5m means only surfaces within 5m ahead

        Returns:
            Filtered list of triangles that are above and directly overhead
        """
        if not triangles:
            return []

        # Vectorize triangles
        vertices_array = cls._vectorize_triangles(triangles)
        window_arr = window_center.to_array()

        # Filter 1: Height (above window)
        above_mask = cls._filter_by_height(vertices_array, window_arr[2])

        # Filter 2: Forward distance along viewing direction
        vecs = vertices_array - window_arr
        normal_horizontal, normal_horizontal_mag = cls._compute_horizontal_normal(window_normal)

        if normal_horizontal_mag < MathConstants.EPSILON.value:
            # Viewing straight up/down - use Euclidean horizontal distance
            horiz_vecs = vecs[:, :, :2]  # Only X, Y
            horiz_dists = np.linalg.norm(horiz_vecs, axis=2)
            # Keep triangles within max_forward_distance horizontally
            within_distance = horiz_dists <= max_forward_distance
        else:
            # Project onto horizontal viewing direction
            normal_horizontal = normal_horizontal / normal_horizontal_mag
            forward_distances = np.dot(vecs, normal_horizontal)

            # Keep triangles that are:
            # - In front (forward_distance > 0)
            # - Within max_forward_distance ahead
            within_distance = (forward_distances > 0) & (forward_distances <= max_forward_distance)

        # Triangle valid if ANY vertex is within the forward distance
        distance_mask = within_distance.any(axis=1)

        # Combine masks
        keep_mask = above_mask & distance_mask

        filtered = cls._build_filtered_list(triangles, keep_mask)

        logger.info(
            f"        [ZENITH-FILTER] Kept {len(filtered)}/{len(triangles)} - "
            f"Filtered: {(~above_mask).sum()} below window, "
            f"{(above_mask & ~distance_mask).sum()} too far (>{max_forward_distance:.1f}m ahead)"
        )

        return filtered


class VerticalSurfaceFilter(TriangleFilter):
    """
    Filter for vertical/near-vertical surfaces (walls) - for horizon calculations

    Filters out horizontal surfaces like roofs, keeping only walls and vertical obstructions.
    """

    @classmethod
    def call(
        cls,
        triangles: Tuple[Triangle, ...],
        window_center: Point3D,
        window_normal: Vector3D,
        min_horizontal_distance: float = 2.0,
        max_vertical_normal_z: float = 0.5
    ) -> List[Triangle]:
        """
        Filter triangles to only include vertical/near-vertical surfaces

        Args:
            triangles: Input triangles
            window_center: Window center point
            window_normal: Window viewing direction
            min_horizontal_distance: Minimum horizontal distance from window
            max_vertical_normal_z: Maximum Z component of normal for vertical surfaces
                                  (0.5 = surfaces up to ~60° from vertical)

        Returns:
            List of filtered triangles that are vertical surfaces
        """
        if not triangles:
            return []

        # First apply horizon filter (above, in front, minimum distance)
        horizon_filtered = HorizonTriangleFilter.call(
            triangles, window_center, window_normal, min_horizontal_distance
        )

        if not horizon_filtered:
            return []

        # Filter by surface orientation - keep only vertical surfaces
        vertical_triangles = []
        for triangle in horizon_filtered:
            # Calculate triangle normal
            v1 = triangle.v1.to_array()
            v2 = triangle.v2.to_array()
            v3 = triangle.v3.to_array()

            edge1 = v2 - v1
            edge2 = v3 - v1
            normal = np.cross(edge1, edge2)
            normal_mag = np.linalg.norm(normal)

            if normal_mag < MathConstants.EPSILON.value:
                continue  # Degenerate triangle

            normal = normal / normal_mag

            # Check if surface is vertical (normal has small Z component)
            if abs(normal[2]) <= max_vertical_normal_z:
                vertical_triangles.append(triangle)

        logger.info(
            f"        [VERTICAL-FILTER] Kept {len(vertical_triangles)}/{len(horizon_filtered)} - "
            f"Filtered: {len(horizon_filtered) - len(vertical_triangles)} horizontal surfaces"
        )

        return vertical_triangles


class CompositeTriangleFilter(HorizonTriangleFilter):
    """
    Filter triangles for BOTH horizon and zenith in a single pass

    Optimized to avoid duplicate vectorization and height filtering.
    """

    @classmethod
    def call(
        cls,
        triangles: Tuple[Triangle, ...],
        window_center: Point3D,
        window_normal: Vector3D,
        min_horizontal_distance: float = 2.0
    ) -> Tuple[List[Triangle], List[Triangle]]:
        """
        Filter triangles for both horizon and zenith simultaneously

        Args:
            triangles: All mesh triangles
            window_center: Window center point
            window_normal: Window viewing direction
            min_horizontal_distance: Minimum horizontal distance for horizon (meters)

        Returns:
            Tuple of (horizon_filtered, zenith_filtered)
        """
        vecs, above_mask, normal_horizontal, normal_horizontal_mag = cls._precompute(triangles, window_center, window_normal)

        z_mask = ZenithTriangleFilter._mask(normal_horizontal_mag, normal_horizontal, vecs, len(triangles))
        h_mask = HorizonTriangleFilter._mask(normal_horizontal_mag, normal_horizontal, vecs, min_horizontal_distance)

        # Build results
        h_filtered = cls._build_filtered_list(triangles, above_mask & h_mask)
        z_filtered = cls._build_filtered_list(triangles, above_mask & z_mask)

        logger.info(
            f"        [COMPOSITE-FILTER] Kept {len(h_filtered)} horizon, "
            f"{len(z_filtered)} zenith from {len(triangles)} triangles"
        )

        return (h_filtered, z_filtered)

"""Validators for geometric constraints and data integrity"""
from typing import Optional, Tuple

import numpy as np

from src.components.geometry import Point3D, Triangle
from src.server.base.constants import MathConstants
from src.server.base.errors import PointOnTriangleError


class GeometryValidator:
    """
    Validates geometric constraints for obstruction calculations

    Responsibilities (Single Responsibility Principle):
    - Check if points lie on triangles
    - Validate geometric relationships between elements
    """

    @staticmethod
    def _calculate_barycentric_coordinates(
        point: np.ndarray,
        v1: np.ndarray,
        v2: np.ndarray,
        v3: np.ndarray
    ) -> Optional[Tuple[float, float, float]]:
        """
        Calculate barycentric coordinates of point with respect to triangle

        Barycentric coordinates (u, v, w) represent point as:
        P = u*V1 + v*V2 + w*V3 where u + v + w = 1

        Args:
            point: Point to check
            v1, v2, v3: Triangle vertices

        Returns:
            Tuple of (u, v, w) barycentric coordinates, or None if triangle is degenerate
        """
        # Vectors from v1 to other vertices
        e1 = v2 - v1
        e2 = v3 - v1

        # Vector from v1 to point
        vp = point - v1

        # Calculate dot products
        d00 = np.dot(e1, e1)
        d01 = np.dot(e1, e2)
        d11 = np.dot(e2, e2)
        d20 = np.dot(vp, e1)
        d21 = np.dot(vp, e2)

        # Calculate barycentric coordinates
        denom = d00 * d11 - d01 * d01

        if abs(denom) < MathConstants.EPSILON.value:
            # Degenerate triangle - cannot calculate valid barycentric coordinates
            # This occurs when triangle vertices are collinear (zero area)
            return None

        v = (d11 * d20 - d01 * d21) / denom
        w = (d00 * d21 - d01 * d20) / denom
        u = 1.0 - v - w

        return (u, v, w)

    @staticmethod
    def _point_distance_to_plane(
        point: np.ndarray,
        v1: np.ndarray,
        v2: np.ndarray,
        v3: np.ndarray
    ) -> float:
        """
        Calculate perpendicular distance from point to triangle plane

        Args:
            point: Point to check
            v1, v2, v3: Triangle vertices

        Returns:
            Absolute distance from point to plane
        """
        # Calculate triangle normal
        e1 = v2 - v1
        e2 = v3 - v1
        normal = np.cross(e1, e2)

        normal_mag = np.linalg.norm(normal)
        if normal_mag < MathConstants.EPSILON.value:
            # Degenerate triangle
            return float('inf')

        normal = normal / normal_mag

        # Calculate distance to plane
        vp = point - v1
        distance = abs(np.dot(vp, normal))

        return float(distance)

    @staticmethod
    def is_point_on_triangle(
        point: Point3D,
        triangle: Triangle,
        tolerance: float = MathConstants.EPSILON.value
    ) -> bool:
        """
        Check if a point lies on a triangle (within tolerance)

        A point is on a triangle if:
        1. It lies on the triangle's plane (distance < tolerance)
        2. It lies within the triangle's boundaries (barycentric coordinates all >= 0)

        Args:
            point: Point to check
            triangle: Triangle to check against
            tolerance: Distance tolerance (default: MathConstants.EPSILON.value)

        Returns:
            True if point lies on triangle, False otherwise
        """
        if tolerance is None:
            tolerance = MathConstants.EPSILON.value

        # Convert to numpy arrays
        p = point.to_array()
        v1 = triangle.v1.to_array()
        v2 = triangle.v2.to_array()
        v3 = triangle.v3.to_array()

        # Check if point is on triangle plane
        distance = GeometryValidator._point_distance_to_plane(p, v1, v2, v3)
        if distance > tolerance:
            return False

        # Check if point is within triangle boundaries using barycentric coordinates
        barycentric = GeometryValidator._calculate_barycentric_coordinates(p, v1, v2, v3)

        # Degenerate triangle - point cannot be considered "on" it
        if barycentric is None:
            return False

        u, v, w = barycentric

        # Point is inside triangle if all barycentric coordinates are non-negative
        # Allow small negative values due to floating point errors
        epsilon = -MathConstants.EPSILON.value
        if u >= epsilon and v >= epsilon and w >= epsilon:
            return True

        return False

    @staticmethod
    def find_triangle_containing_point(
        point: Point3D,
        triangles: Tuple[Triangle, ...],
        tolerance: float = MathConstants.EPSILON.value
    ) -> Optional[Triangle]:
        """
        Find the first triangle that contains the given point (vectorized)

        Args:
            point: Point to check
            triangles: Tuple of triangles to search
            tolerance: Distance tolerance (default: MathConstants.EPSILON.value)

        Returns:
            First triangle containing the point, or None if not found
        """

        n_triangles = len(triangles)
        if n_triangles == 0:
            return None

        # Build vertices array
        vertices_array = np.empty((n_triangles, 3, 3), dtype=np.float64)
        for i, t in enumerate(triangles):
            vertices_array[i, 0] = t.v1.to_array()
            vertices_array[i, 1] = t.v2.to_array()
            vertices_array[i, 2] = t.v3.to_array()

        point_arr = point.to_array()

        # Vectorized plane distance check
        v1 = vertices_array[:, 0, :]
        v2 = vertices_array[:, 1, :]
        v3 = vertices_array[:, 2, :]

        # Compute plane normals
        edge1 = v2 - v1
        edge2 = v3 - v1
        normals = np.cross(edge1, edge2)
        normal_lengths = np.linalg.norm(normals, axis=1, keepdims=True)

        # Handle degenerate triangles
        valid_mask = normal_lengths.flatten() > 1e-10
        if not valid_mask.any():
            return None

        normals = normals / np.maximum(normal_lengths, 1e-10)

        # Compute distances to planes
        point_to_v1 = point_arr - v1
        distances = np.abs(np.sum(point_to_v1 * normals, axis=1))

        # Filter triangles by plane distance
        on_plane_mask = (distances <= tolerance) & valid_mask

        if not on_plane_mask.any():
            return None

        # Barycentric coordinates for triangles on plane
        on_plane_indices = np.where(on_plane_mask)[0]

        epsilon = -MathConstants.EPSILON.value

        for idx in on_plane_indices:
            v1_pt = vertices_array[idx, 0]
            v2_pt = vertices_array[idx, 1]
            v3_pt = vertices_array[idx, 2]

            barycentric = GeometryValidator._calculate_barycentric_coordinates(
                point_arr, v1_pt, v2_pt, v3_pt
            )

            # Skip degenerate triangles
            if barycentric is None:
                continue

            u, v, w = barycentric

            if u >= epsilon and v >= epsilon and w >= epsilon:
                return triangles[idx]

        return None

    @staticmethod
    def validate_point_not_on_mesh(
        point: Point3D,
        triangles: Tuple[Triangle, ...],
        tolerance: float = 0
    ) -> None:
        """
        Validate that a point does not lie on any triangle in the mesh

        Args:
            point: Point to validate (e.g., window center)
            triangles: Mesh triangles
            tolerance: Distance tolerance (default: MathConstants.EPSILON.value)

        Raises:
            PointOnTriangleError: If point lies on any triangle
        """
        triangle = GeometryValidator.find_triangle_containing_point(
            point, triangles, tolerance
        )

        if triangle is not None:
            raise PointOnTriangleError(point, triangle)

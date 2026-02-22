"""
Reference point calculation for windows

Projects window bounding box center onto the nearest point on
a room polygon boundary to determine the obstruction reference point.
"""

from typing import List

import numpy as np

from src.components.geometry import Point3D


class ReferencePointCalculator:
    """
    Calculates window reference point by projecting onto room polygon boundary.

    The reference point is the 2D center of the window bounding box projected
    onto the closest point on the room polygon boundary, combined with the
    vertical center of the window.

    This replicates the logic from server_encoder's
    WindowGeometry.calculate_reference_point_from_polygon using pure numpy
    (no Shapely dependency).
    """

    @classmethod
    def calculate(
        cls,
        x1: float, y1: float, z1: float,
        x2: float, y2: float, z2: float,
        room_polygon: List[List[float]],
    ) -> Point3D:
        """
        Calculate reference point from window endpoints and room polygon.

        Args:
            x1, y1, z1: First window corner
            x2, y2, z2: Second window corner
            room_polygon: List of [x, y] vertices forming the room polygon
                          (closed or unclosed — will be closed automatically)

        Returns:
            Point3D with projected (x, y) and vertical center z

        Raises:
            ValueError: If room_polygon has fewer than 3 vertices
        """
        if len(room_polygon) < 3:
            raise ValueError("Room polygon must have at least 3 vertices")

        # Window bounding box center in 2D
        center_x = (x1 + x2) * 0.5
        center_y = (y1 + y2) * 0.5
        point = np.array([center_x, center_y])

        # Project onto polygon boundary
        projected = cls._project_point_onto_polyline(point, room_polygon)

        # Vertical center
        ref_z = (z1 + z2) * 0.5

        return Point3D(x=float(projected[0]), y=float(projected[1]), z=ref_z)

    @staticmethod
    def _project_point_onto_polyline(
        point: np.ndarray,
        vertices: List[List[float]],
    ) -> np.ndarray:
        """
        Project a 2D point onto the nearest point on a closed polyline.

        Args:
            point: 2D point as numpy array [x, y]
            vertices: List of [x, y] polygon vertices (auto-closed)

        Returns:
            Nearest point on the polyline boundary as numpy array [x, y]
        """
        coords = [np.array(v[:2], dtype=float) for v in vertices]

        # Close the polygon if not already closed
        if not np.allclose(coords[0], coords[-1]):
            coords.append(coords[0])

        best_proj = coords[0]
        best_dist_sq = float("inf")

        for i in range(len(coords) - 1):
            seg_start = coords[i]
            seg_end = coords[i + 1]
            proj = _project_point_onto_segment(point, seg_start, seg_end)
            dist_sq = float(np.sum((point - proj) ** 2))
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_proj = proj

        return best_proj


def _project_point_onto_segment(
    point: np.ndarray,
    seg_start: np.ndarray,
    seg_end: np.ndarray,
) -> np.ndarray:
    """
    Project a 2D point onto a line segment, clamped to segment bounds.

    Args:
        point: The point to project
        seg_start: Segment start point
        seg_end: Segment end point

    Returns:
        Nearest point on the segment
    """
    seg_vec = seg_end - seg_start
    seg_len_sq = float(np.dot(seg_vec, seg_vec))

    # Degenerate segment (zero length)
    if seg_len_sq < 1e-12:
        return seg_start.copy()

    # Parameter t along segment (clamped to [0, 1])
    t = float(np.dot(point - seg_start, seg_vec)) / seg_len_sq
    t = max(0.0, min(1.0, t))

    return seg_start + t * seg_vec

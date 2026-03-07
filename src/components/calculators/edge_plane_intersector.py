"""Edge-plane intersection calculator"""

from typing import Optional

from src.components.geometry import Point3D
from src.server.base.constants import MathConstants


class EdgePlaneIntersector:
    """
    Calculates intersection of edges with planes

    Single Responsibility:
    - Only handles edge-plane intersection calculations
    - Does NOT handle triangle-level operations or angle calculations
    """

    @staticmethod
    def intersect(
        p1: Point3D,
        p2: Point3D,
        d1: float,
        d2: float
    ) -> Optional[Point3D]:
        """
        Find intersection point of edge (p1, p2) with plane

        Args:
            p1: First endpoint
            p2: Second endpoint
            d1: Signed distance of p1 to plane
            d2: Signed distance of p2 to plane

        Returns:
            Intersection point if edge crosses plane, None otherwise
        """
        # Edge crosses plane if d1 and d2 have opposite signs
        if d1 * d2 > 0:
            return None

        # Edge lies on plane if both distances are ~0
        if abs(d1) < MathConstants.EPSILON.value and abs(d2) < MathConstants.EPSILON.value:
            return None

        # Calculate intersection parameter t
        # P = p1 + t * (p2 - p1)
        # At intersection: normal · (P - origin) = 0
        # t = d1 / (d1 - d2)
        t = d1 / (d1 - d2)

        # Calculate intersection point
        p1_arr = p1.to_array()
        p2_arr = p2.to_array()
        intersection = p1_arr + t * (p2_arr - p1_arr)

        return Point3D.from_array(intersection)

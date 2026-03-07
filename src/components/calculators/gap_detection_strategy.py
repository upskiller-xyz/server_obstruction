"""
Gap detection strategy

Strategy for detecting angular gaps between elevation angles.
"""

from typing import List, Tuple


class GapDetectionStrategy:
    """Strategy for detecting angular gaps in elevation angles."""

    @staticmethod
    def find_gaps(
        elevation_angles: List[float],
        min_gap_deg: float
    ) -> List[Tuple[float, float, float]]:
        """
        Find angular gaps between consecutive intersection points.

        Adds 0 and 90 degree boundaries, sorts, and returns gaps
        larger than min_gap_deg, ranked by size (largest first).

        Args:
            elevation_angles: List of elevation angles in degrees
            min_gap_deg: Minimum gap size to include

        Returns:
            List of (low, high, size) tuples sorted by size descending
        """
        # Add boundaries and deduplicate
        boundaries = sorted(set([0.0] + list(elevation_angles) + [90.0]))

        gaps: List[Tuple[float, float, float]] = []
        for i in range(len(boundaries) - 1):
            size = boundaries[i + 1] - boundaries[i]
            if size > min_gap_deg:
                gaps.append((boundaries[i], boundaries[i + 1], size))

        # Largest gaps first
        gaps.sort(key=lambda g: g[2], reverse=True)
        return gaps

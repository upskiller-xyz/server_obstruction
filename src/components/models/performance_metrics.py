"""
Performance metrics for gap calculation

Tracks and logs performance metrics during obstruction calculation.
"""

import logging
from dataclasses import dataclass

from src.server.base.constants import ObstructionStatus


@dataclass(frozen=True)
class PerformanceMetrics:
    """Performance metrics for gap calculation."""
    elapsed_ms: float
    rays_cast: int
    gaps_tested: int
    intersection_points: int

    def log_summary(self, status: ObstructionStatus) -> None:
        """Log performance summary."""
        logging.debug(
            f"[GAP-CALC] Status: {status.value}. "
            f"Rays: {self.rays_cast}, Gaps tested: {self.gaps_tested}, "
            f"Intersections: {self.intersection_points}. "
            f"Elapsed: {self.elapsed_ms:.1f}ms"
        )

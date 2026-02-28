"""
Vertical surface filtering for horizon calculations

Filters out horizontal surfaces like roofs, keeping only walls and vertical obstructions.
"""


from src.components.geometry import Triangle
from src.components.filter import VerticalSurfaceFilter


class NonVerticalSurfaceFilter(VerticalSurfaceFilter):
    """
    Filter for non-vertical surfaces (roofs) - for zenith calculations

    Filters out vertical surfaces like walls, keeping only horizontal obstructions.
    """

    @classmethod
    def _should_keep(cls, triangle: Triangle) -> bool:
        """Return True if triangle should be kept (is NOT vertical surface)"""
        return not cls._is_vertical(triangle)

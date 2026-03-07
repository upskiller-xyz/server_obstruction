"""Strategy pattern map for surface filter selection"""

from src.components.filter import NonVerticalSurfaceFilter, VerticalSurfaceFilter
from src.server.base.constants import ANGLES


class FilterStrategyMap:
    """
    Strategy Pattern for surface filter selection

    Single Responsibility:
    - Maps angle type to appropriate filter class
    - Does NOT perform filtering or calculations
    """

    _FILTER_STRATEGY = {
        ANGLES.HORIZON: VerticalSurfaceFilter,
        ANGLES.ZENITH: NonVerticalSurfaceFilter
    }

    @classmethod
    def get_filter(cls, angle_type: ANGLES):
        """
        Get filter class for given angle type

        Args:
            angle_type: HORIZON or ZENITH

        Returns:
            Appropriate filter class
        """
        return cls._FILTER_STRATEGY.get(angle_type, VerticalSurfaceFilter)

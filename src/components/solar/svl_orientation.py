"""
Orientation rules of Miljöbyggnad Indikator 2

Only façades facing between 90° and 270° (east to west via south) are
assessed. The simplified method groups the windows per cardinal direction.
"""

from src.components.solar.constants import SvlDefaults
from src.components.solar.solar_request import SolarRequest, SolarWindow


class SvlOrientation:
    """Orientation of a window for the SVL assessment"""

    _TOLERANCE_DEG: float = 1e-6
    _HORIZONTAL_TILT_DEG: float = 90.0
    _CARDINAL_STEP_DEG: float = 90.0

    @classmethod
    def is_excluded(cls, request: SolarRequest, window: SolarWindow) -> bool:
        """Whether the window faces north (outside 90°-270°); skylights never are"""
        if cls.is_horizontal(window):
            return False
        limit = SvlDefaults.MAX_SOUTH_DEVIATION_DEGREES.value + cls._TOLERANCE_DEG
        return abs(cls._south_deviation(request, window)) > limit

    @classmethod
    def is_horizontal(cls, window: SolarWindow) -> bool:
        """Whether the window is a horizontal skylight"""
        return window.tilt_deg >= cls._HORIZONTAL_TILT_DEG

    @classmethod
    def cardinal(cls, request: SolarRequest, window: SolarWindow) -> int:
        """Nearest cardinal direction: -1 east, 0 south, 1 west"""
        return round(cls._south_deviation(request, window) / cls._CARDINAL_STEP_DEG)

    @classmethod
    def _south_deviation(cls, request: SolarRequest, window: SolarWindow) -> float:
        """Signed angle from south to the window bearing, -180° to 180°"""
        bearing = window.bearing_deg(request.model_y_bearing_deg)
        return (bearing - SvlDefaults.SOUTH_BEARING_DEGREES.value + 180.0) % 360.0 - 180.0

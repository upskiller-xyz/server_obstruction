"""
Simplified solar heat gain (SVL) of the Miljöbyggnad manual

The same formula as the calculation, with a fixed irradiance on the vertical
glazing instead of the one of the site:

    one direction:                 800 * Σ g_syst * A_glas / A_rum
    two perpendicular directions:  560 * Σ g_syst * A_glas / A_rum (both façades)

The largest of all cases is the value of the room. Opposite façades (east
and west) are never added: they do not receive sun at the same time. The
manual gives no value for skylights; a horizontal skylight is taken as a
direction of its own with the irradiance of one direction.
"""

from typing import Dict, Hashable

from src.components.solar.constants import SvlDefaults
from src.components.solar.solar_request import SolarRequest
from src.components.solar.svl_orientation import SvlOrientation


class SimplifiedSvl:
    """Simplified SVL of a room, reference value next to the calculated one"""

    _ROOF: str = "roof"

    @classmethod
    def calculate(cls, request: SolarRequest) -> float:
        """
        Calculate the simplified SVL of the room.

        Args:
            request: Room and windows (room_area required)

        Returns:
            Simplified SVL in W/m² of floor area
        """
        apertures = cls._apertures(request)
        single = SvlDefaults.SIMPLIFIED_IRRADIANCE_W_M2.value
        combined = SvlDefaults.SIMPLIFIED_COMBINED_IRRADIANCE_W_M2.value

        cases = [single * aperture for aperture in apertures.values()]
        cases += [
            combined * (apertures[first] + apertures[second])
            for first in apertures for second in apertures
            if cls._are_perpendicular(first, second)
        ]
        return max(cases, default=0.0) / request.room_area

    @classmethod
    def _apertures(cls, request: SolarRequest) -> Dict[Hashable, float]:
        """Sum of g_syst * area of the assessed windows per direction"""
        apertures: Dict[Hashable, float] = {}
        for window in request.windows:
            if SvlOrientation.is_excluded(request, window):
                continue
            direction = (
                cls._ROOF if SvlOrientation.is_horizontal(window)
                else SvlOrientation.cardinal(request, window)
            )
            apertures[direction] = apertures.get(direction, 0.0) + window.g_syst * window.area
        return apertures

    @classmethod
    def _are_perpendicular(cls, first: Hashable, second: Hashable) -> bool:
        """Whether two directions are neighbouring façades (east-south, south-west)"""
        if cls._ROOF in (first, second):
            return False
        return second - first == 1

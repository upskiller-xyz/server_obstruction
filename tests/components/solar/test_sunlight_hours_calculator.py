import math

import pytest

from src.components.solar import SkyGapProfile, SunlightHoursCalculator
from src.components.solar.constants import SunlightLevel
from tests.components.solar.solar_fixtures import (
    EAST,
    NORTH,
    SOUTH,
    blocked_profile,
    make_request,
    make_window,
)


class TestSunlightHoursCalculator:
    """Test cases for SunlightHoursCalculator class"""

    @pytest.mark.parametrize("hours, level", [
        (0.0, SunlightLevel.NOT_MET), (1.4, SunlightLevel.NOT_MET),
        (1.5, SunlightLevel.MINIMUM), (3.0, SunlightLevel.MEDIUM),
        (4.0, SunlightLevel.HIGH), (9.0, SunlightLevel.HIGH),
    ])
    def test_level(self, hours, level):
        assert SunlightHoursCalculator.level(hours) == level

    def test_unobstructed_southwindow(self):
        result = SunlightHoursCalculator.calculate(
            make_request([make_window()]), [SkyGapProfile.unobstructed()]
        )

        # Sun within ±65° of south on 21 March at 59.33°N
        assert result.sunlight_hours == pytest.approx(8.33, abs=0.2)
        assert result.level == SunlightLevel.HIGH
        assert result.min_sun_altitude_deg == pytest.approx(8.39, abs=0.02)

    def test_north_window_is_excluded(self):
        result = SunlightHoursCalculator.calculate(
            make_request([make_window(NORTH)]), [SkyGapProfile.unobstructed()]
        )

        assert result.sunlight_hours == 0.0
        assert result.windows[0].excluded_by_orientation is True
        assert result.level == SunlightLevel.NOT_MET

    def test_east_window_gets_morning_sun_only(self):
        south = SunlightHoursCalculator.calculate(
            make_request([make_window(SOUTH)]), [SkyGapProfile.unobstructed()]
        )
        east = SunlightHoursCalculator.calculate(
            make_request([make_window(EAST)]), [SkyGapProfile.unobstructed()]
        )

        assert 0.0 < east.sunlight_hours < south.sunlight_hours
        assert east.windows[0].excluded_by_orientation is False

    def test_blocked_window_gets_no_sun(self):
        result = SunlightHoursCalculator.calculate(
            make_request([make_window()]), [blocked_profile()]
        )

        assert result.sunlight_hours == 0.0

    def test_room_hours_are_union_of_windows(self):
        request = make_request([make_window(EAST), make_window(math.pi)])
        result = SunlightHoursCalculator.calculate(request, [SkyGapProfile.unobstructed()] * 2)

        per_window = [w.sunlight_hours for w in result.windows]
        assert result.sunlight_hours == pytest.approx(sum(per_window))
        assert result.sunlight_hours > max(per_window)

    def test_min_sun_altitude_reduces_hours(self):
        profiles = [SkyGapProfile.unobstructed()]
        low = SunlightHoursCalculator.calculate(
            make_request([make_window()], min_sun_altitude_degrees=5.0), profiles
        )
        high = SunlightHoursCalculator.calculate(
            make_request([make_window()], min_sun_altitude_degrees=25.0), profiles
        )

        assert high.sunlight_hours < low.sunlight_hours

    def test_to_dict_fields(self):
        result = SunlightHoursCalculator.calculate(
            make_request([make_window(id="W1")]), [SkyGapProfile.unobstructed()]
        )

        data = result.to_dict()

        assert set(data) == {
            "sunlight_hours", "sunlight_level", "min_sun_altitude_degrees", "windows",
        }
        assert data["windows"][0]["id"] == "W1"

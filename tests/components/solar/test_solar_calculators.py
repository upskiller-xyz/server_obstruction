import math

import numpy as np
import pytest

from src.components.solar import SkyGapProfile, SolarRequest, SvlCalculator
from src.components.solar.constants import ShadingType, SvlMethod
from tests.components.solar.solar_fixtures import (
    ARLANDA,
    EAST,
    NORTH,
    SOUTH,
    WEST,
    blocked_profile,
    horizon_profile,
    make_request,
    make_window,
)


class TestSolarRequest:
    """Test cases for SolarRequest and SolarWindow models"""

    def test_defaults(self):
        request = make_request([make_window()])
        window = request.windows[0]

        assert request.min_sun_altitude_deg == pytest.approx(8.39, abs=0.02)
        assert request.model_y_bearing_deg == 0.0
        assert request.mesh is None
        assert request.ground_reflectance == 0.20
        assert window.g_glazing == 0.60
        assert window.shading_type == ShadingType.NONE
        assert window.g_syst == pytest.approx(0.60)

    # Fc of DIN 4108-2:2013-02 Table 7, double glazing with g > 0.40
    @pytest.mark.parametrize("shading_type, factor", [
        ("none", 1.00),
        ("internal_blind", 0.75),
        ("mid_pane_blind", 0.75),
        ("external_blind", 0.25),
        ("external_screen", 0.25),
    ])
    def test_g_syst_with_shading(self, shading_type, factor):
        request = make_request([make_window(g_glazing=0.5, shading_type=shading_type)])

        assert request.windows[0].g_syst == pytest.approx(0.5 * factor)

    @pytest.mark.parametrize("shading_type, factor", [
        ("internal_blind", 0.75), ("external_blind", 0.30), ("external_screen", 0.30),
    ])
    def test_g_syst_with_shading_on_solar_control_glazing(self, shading_type, factor):
        request = make_request([make_window(g_glazing=0.4, shading_type=shading_type)])

        assert request.windows[0].g_syst == pytest.approx(0.4 * factor)

    def test_custom_g_syst_replaces_glazing_and_shading(self):
        request = make_request([make_window(g_syst=0.12, shading_type="internal_blind")])

        assert request.windows[0].g_syst == pytest.approx(0.12)

    def test_min_sun_altitude_override(self):
        request = make_request([make_window()], min_sun_altitude_degrees=12.0)

        assert request.min_sun_altitude_deg == 12.0

    def test_city_gives_latitude_and_station(self):
        request = SolarRequest.from_dict({"city": ARLANDA, "windows": [make_window()]})

        assert request.latitude_deg == pytest.approx(59.627)
        assert request.climate_station.key == ARLANDA

    def test_latitude_overrides_station_latitude(self):
        request = make_request([make_window()], city=ARLANDA)

        assert request.latitude_deg == 59.33
        assert request.climate_station.key == ARLANDA

    def test_without_city_there_is_no_station(self):
        assert make_request([make_window()]).climate_station is None

    def test_unknown_city_raises(self):
        with pytest.raises(ValueError, match="Unknown city"):
            make_request([make_window()], city="atlantis")

    def test_unknown_shading_type_raises(self):
        with pytest.raises(ValueError, match="shading_type"):
            make_request([make_window(shading_type="curtain")])

    @pytest.mark.parametrize("direction, bearing", [
        (SOUTH, 180.0), (NORTH, 0.0), (EAST, 90.0), (math.pi, 270.0),
    ])
    def test_window_bearing(self, direction, bearing):
        request = make_request([make_window(direction)])

        assert request.windows[0].bearing_deg(0.0) == pytest.approx(bearing)

    def test_tilted_normal_points_up(self):
        request = make_request([make_window(tilt_degrees=90.0)])

        assert request.windows[0].normal_array == pytest.approx([0.0, 0.0, 1.0], abs=1e-9)


class TestSvlCalculator:
    """Test cases for SvlCalculator class"""

    def test_without_profiles_the_sky_is_unobstructed(self):
        request = make_request([make_window()])
        result = SvlCalculator.calculate(request, None)
        open_sky = SvlCalculator.calculate(request, [SkyGapProfile.unobstructed()])

        assert result.method == SvlMethod.CLEAR_SKY
        assert result.svl_peak_w_m2 == pytest.approx(open_sky.svl_peak_w_m2)

    # Aperture (g_syst * area) is 1.2 per default window
    @pytest.mark.parametrize("windows, expected", [
        ([make_window()], 800.0 * 1.2),
        # 800 on the large south glazing beats 560 on south + small east
        ([make_window(), make_window(EAST, area=0.5)], 800.0 * 1.2),
        ([make_window(), make_window(EAST)], 560.0 * 2.4),
        # East and west are opposite façades: never added
        ([make_window(EAST), make_window(WEST)], 800.0 * 1.2),
        # Three façades: the best perpendicular pair
        ([make_window(EAST), make_window(), make_window(WEST, area=4.0)], 560.0 * 3.6),
        ([make_window(), make_window(NORTH)], 800.0 * 1.2),
        ([make_window(NORTH)], 0.0),
    ])
    def test_simplified_reference_value(self, windows, expected):
        result = SvlCalculator.calculate(make_request(windows), None)

        assert result.simplified_w_m2 == pytest.approx(expected / 15.0)

    @pytest.mark.parametrize("profiles", [None, [SkyGapProfile.unobstructed()] * 2])
    def test_north_window_is_not_assessed(self, profiles):
        alone = SvlCalculator.calculate(
            make_request([make_window()]), None if profiles is None else profiles[:1]
        )
        room = SvlCalculator.calculate(make_request([make_window(), make_window(NORTH)]), profiles)

        assert room.svl_peak_w_m2 == pytest.approx(alone.svl_peak_w_m2)
        assert room.contributions[1].excluded_by_orientation is True
        assert room.contributions[1].svl_w_m2 == 0.0
        assert room.contributions[0].excluded_by_orientation is False

    def test_horizontal_skylight_is_always_assessed(self):
        request = make_request([make_window(NORTH, tilt_degrees=90.0)])
        result = SvlCalculator.calculate(request, [SkyGapProfile.unobstructed()])

        assert result.contributions[0].excluded_by_orientation is False
        assert result.svl_peak_w_m2 > 0.0

    def test_unobstructed_south_window_is_close_to_simplified(self):
        result = SvlCalculator.calculate(
            make_request([make_window()]), [SkyGapProfile.unobstructed()]
        )

        assert result.method == SvlMethod.CLEAR_SKY_OBSTRUCTION
        assert result.svl_peak_w_m2 == pytest.approx(70.0, rel=0.05)
        assert result.peak_time.hour == 12.0
        assert result.contributions[0].sun_visible is True
        assert result.climate_station is None

    def test_station_sky_for_southwindow(self):
        result = SvlCalculator.calculate(
            make_request([make_window()], city=ARLANDA), [SkyGapProfile.unobstructed()]
        )

        # About 860 W/m² on the glazing at solar noon around the equinox:
        # direct beam + sky diffuse + ground-reflected
        assert result.climate_station == ARLANDA
        assert result.contributions[0].irradiance_w_m2 == pytest.approx(858.0, rel=0.03)
        assert result.peak_time.hour == 12.0

    def test_ground_reflection_adds_to_the_peak(self):
        profiles = [SkyGapProfile.unobstructed()]
        default = SvlCalculator.calculate(make_request([make_window()], city=ARLANDA), profiles)
        dark_ground = SvlCalculator.calculate(
            make_request([make_window()], city=ARLANDA, ground_reflectance=0.0), profiles
        )

        assert dark_ground.contributions[0].irradiance_w_m2 == pytest.approx(805.0, rel=0.03)
        assert dark_ground.svl_peak_w_m2 < default.svl_peak_w_m2

    @pytest.mark.parametrize("cos_incidence, tilt, ratio", [
        (1.0, 0.0, 1.3),      # Vertical, facing the sun
        (0.0, 0.0, 0.55),     # Vertical, sun in the plane of the glazing
        (-1.0, 0.0, 0.45),    # Vertical, sun behind: lower limit
        (0.5, 90.0, 1.0),     # Horizontal skylight sees the whole sky
    ])
    def test_sky_diffuse_ratio(self, cos_incidence, tilt, ratio):
        value = SvlCalculator._sky_diffuse_ratio(np.array([cos_incidence]), tilt)

        assert value[0] == pytest.approx(ratio)

    def test_station_sky_differs_from_generic_sky(self):
        profiles = [SkyGapProfile.unobstructed()]
        generic = SvlCalculator.calculate(make_request([make_window()]), profiles)
        station = SvlCalculator.calculate(make_request([make_window()], city=ARLANDA), profiles)

        assert station.svl_peak_w_m2 != pytest.approx(generic.svl_peak_w_m2, rel=0.01)

    def test_hidden_sun_leaves_reduced_diffuse(self):
        # Horizon at 60°: the sun never gets that high at Arlanda, and only
        # a small share of the sky and ground light is left
        request = make_request([make_window()], city=ARLANDA)
        open_sky = SvlCalculator.calculate(request, [SkyGapProfile.unobstructed()])
        hidden = SvlCalculator.calculate(request, [horizon_profile(60.0)])

        assert hidden.contributions[0].sun_visible is False
        assert hidden.contributions[0].sky_view_fraction == pytest.approx(0.058, abs=0.005)
        assert 0.0 < hidden.svl_peak_w_m2 < 0.05 * open_sky.svl_peak_w_m2

    def test_unobstructed_window_reports_full_sky_view(self):
        result = SvlCalculator.calculate(
            make_request([make_window()]), [SkyGapProfile.unobstructed()]
        )

        assert result.contributions[0].sky_view_fraction == pytest.approx(1.0)

    def test_full_obstruction_removes_almost_everything(self):
        request = make_request([make_window()])
        open_sky = SvlCalculator.calculate(request, [SkyGapProfile.unobstructed()])
        blocked = SvlCalculator.calculate(request, [blocked_profile()])

        assert blocked.svl_peak_w_m2 < 0.01 * open_sky.svl_peak_w_m2
        assert blocked.contributions[0].sun_visible is False

    def test_shading_scales_result(self):
        profiles = [SkyGapProfile.unobstructed()]
        bare = SvlCalculator.calculate(make_request([make_window()]), profiles)
        shaded = SvlCalculator.calculate(
            make_request([make_window(shading_type="external_blind")]), profiles
        )

        assert shaded.svl_peak_w_m2 == pytest.approx(0.25 * bare.svl_peak_w_m2)

    def test_north_window_gets_less_than_south(self):
        profiles = [SkyGapProfile.unobstructed()]
        south = SvlCalculator.calculate(make_request([make_window(SOUTH)]), profiles)
        north = SvlCalculator.calculate(make_request([make_window(NORTH)]), profiles)

        assert north.svl_peak_w_m2 < south.svl_peak_w_m2

    def test_room_peak_is_the_peak_of_the_summed_windows(self):
        # East and south windows peak at different hours: the room peak is
        # lower than the sum of the two separate peaks
        profiles = [SkyGapProfile.unobstructed()]
        east = SvlCalculator.calculate(make_request([make_window(direction=EAST)]), profiles)
        south = SvlCalculator.calculate(make_request([make_window()]), profiles)
        room = SvlCalculator.calculate(
            make_request([make_window(direction=EAST), make_window()]), profiles * 2
        )

        assert east.peak_time.hour != south.peak_time.hour
        assert room.svl_peak_w_m2 < east.svl_peak_w_m2 + south.svl_peak_w_m2
        assert room.svl_peak_w_m2 > max(east.svl_peak_w_m2, south.svl_peak_w_m2)

    def test_peak_is_between_the_equinoxes(self):
        result = SvlCalculator.calculate(
            make_request([make_window()]), [SkyGapProfile.unobstructed()]
        )

        assert (3, 21) <= (result.peak_time.month, result.peak_time.day) <= (9, 23)

    def test_contributions_sum_to_room_peak(self):
        request = make_request([make_window(SOUTH, id="S"), make_window(EAST, id="E", area=1.0)])
        result = SvlCalculator.calculate(request, [SkyGapProfile.unobstructed()] * 2)

        assert sum(c.svl_w_m2 for c in result.contributions) == pytest.approx(
            result.svl_peak_w_m2
        )
        assert [c.identifier for c in result.contributions] == ["S", "E"]

    def test_high_min_sun_altitude_removes_all_irradiance(self):
        request = make_request([make_window()], min_sun_altitude_degrees=89.0)
        result = SvlCalculator.calculate(request, [SkyGapProfile.unobstructed()])

        assert result.svl_peak_w_m2 == 0.0

    def test_to_dict_fields(self):
        result = SvlCalculator.calculate(
            make_request([make_window()]), [SkyGapProfile.unobstructed()]
        )

        data = result.to_dict()

        assert set(data) == {
            "svl_peak_w_m2", "svl_peak_month_hour", "svl_rating", "building_type",
            "svl_method", "svl_climate_station", "svl_window_contributions",
            "svl_simplified_w_m2",
        }
        assert set(data["svl_peak_month_hour"]) == {"month", "day", "hour"}

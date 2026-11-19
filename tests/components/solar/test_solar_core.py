import math

import numpy as np
import pytest

from src.components.solar import (
    ClearSkyModelProvider,
    ClimateStationCatalogue,
    GenericClearSkyModel,
    EquinoxMinSolarAltitude,
    SkyGapProfile,
    SolarPositionCalculator,
    StationClearSkyModel,
    YearCalendar,
)
from src.server.base.constants import ResponseField

ARLANDA = "stockholm-arlanda-ap"
JUNE_DAY = 172


class TestSolarPositionCalculator:
    """Test cases for SolarPositionCalculator class"""

    def test_noon_sun_is_due_south(self):
        positions = SolarPositionCalculator.calculate(59.33, np.array([172]), np.array([12.0]))

        assert positions.azimuth_deg[0] == pytest.approx(180.0)
        assert positions.altitude_deg[0] == pytest.approx(90.0 - 59.33 + 23.45, abs=0.05)

    def test_equinox_noon_altitude_is_colatitude(self):
        positions = SolarPositionCalculator.calculate(59.33, np.array([80]), np.array([12.0]))

        assert positions.altitude_deg[0] == pytest.approx(90.0 - 59.33, abs=0.5)

    def test_morning_sun_is_east_and_afternoon_sun_is_west(self):
        positions = SolarPositionCalculator.calculate(
            59.33, np.array([172, 172]), np.array([8.0, 16.0])
        )

        assert positions.azimuth_deg[0] < 180.0 < positions.azimuth_deg[1]
        assert positions.altitude_deg[0] == pytest.approx(positions.altitude_deg[1])

    def test_sun_below_horizon_at_midnight(self):
        positions = SolarPositionCalculator.calculate(55.68, np.array([80]), np.array([0.0]))

        assert positions.altitude_deg[0] < 0.0

    def test_model_angle_with_north_along_y(self):
        positions = SolarPositionCalculator.calculate(59.33, np.array([80]), np.array([12.0]))

        # Due south is -Y, i.e. -90° from +X
        assert positions.model_angle_rad(0.0)[0] == pytest.approx(-math.pi / 2)

    def test_model_angle_follows_model_rotation(self):
        positions = SolarPositionCalculator.calculate(59.33, np.array([80]), np.array([12.0]))

        # Model +Y points east, so south is along +X
        assert positions.model_angle_rad(90.0)[0] == pytest.approx(0.0, abs=1e-9)

    def test_direction_vectors_are_unit_length(self):
        hours = np.arange(0.0, 24.0)
        positions = SolarPositionCalculator.calculate(59.33, np.full(24, 172), hours)

        norms = np.linalg.norm(positions.direction_vectors(0.0), axis=1)

        assert norms == pytest.approx(np.ones(24))


class TestYearCalendar:
    """Test cases for YearCalendar class"""

    def test_month_of_day(self):
        months = YearCalendar.month_of(np.array([1, 31, 32, 80, 365]))

        assert months.tolist() == [1, 1, 2, 3, 12]

    def test_day_of_month(self):
        assert YearCalendar.day_of_month(80) == 21
        assert YearCalendar.day_of_month(1) == 1


class TestGenericClearSkyModel:
    """Test cases for GenericClearSkyModel class"""

    def test_beam_normal_at_zenith_in_june(self):
        beam = GenericClearSkyModel().beam_normal(np.array([JUNE_DAY]), np.array([90.0]))

        assert beam[0] == pytest.approx(1088.0 * math.exp(-0.205))

    def test_beam_normal_is_zero_below_horizon(self):
        beam = GenericClearSkyModel().beam_normal(
            np.array([JUNE_DAY, JUNE_DAY]), np.array([0.0, -10.0])
        )

        assert beam.tolist() == [0.0, 0.0]

    def test_beam_normal_grows_with_altitude(self):
        beam = GenericClearSkyModel().beam_normal(
            np.array([JUNE_DAY, JUNE_DAY]), np.array([10.0, 50.0])
        )

        assert beam[0] < beam[1]

    def test_diffuse_horizontal_is_a_fraction_of_the_beam(self):
        model = GenericClearSkyModel()
        days, altitude = np.array([JUNE_DAY]), np.array([50.0])

        diffuse = model.diffuse_horizontal(days, altitude)

        assert diffuse[0] == pytest.approx(0.134 * model.beam_normal(days, altitude)[0])

    def test_has_no_station(self):
        assert GenericClearSkyModel().station_key is None


class TestClimateStationCatalogue:
    """Test cases for ClimateStationCatalogue class"""

    def test_get_station(self):
        station = ClimateStationCatalogue.get(ARLANDA)

        assert station.latitude_deg == pytest.approx(59.627)
        assert len(station.taub) == 12
        assert len(station.taud) == 12
        assert station.tau_source == ARLANDA

    def test_unknown_station_raises(self):
        with pytest.raises(ValueError, match="Unknown city"):
            ClimateStationCatalogue.get("atlantis")

    def test_find_without_key(self):
        assert ClimateStationCatalogue.find(None) is None

    def test_every_station_has_plausible_optical_depths(self):
        stations = ClimateStationCatalogue._stations().values()

        assert len(stations) > 300
        assert all(0.1 < tau < 1.5 for s in stations for tau in s.taub)
        assert all(1.0 < tau < 3.5 for s in stations for tau in s.taud)


class TestStationClearSkyModel:
    """Test cases for StationClearSkyModel class"""

    def test_stockholm_june_noon(self):
        # Hand calculation with taub 0.367, taud 2.428 at 54 degrees altitude
        model = StationClearSkyModel(ClimateStationCatalogue.get(ARLANDA))
        days, altitude = np.array([JUNE_DAY]), np.array([54.0])

        assert model.beam_normal(days, altitude)[0] == pytest.approx(867.0, abs=2.0)
        assert model.diffuse_horizontal(days, altitude)[0] == pytest.approx(104.0, abs=1.0)

    def test_zero_below_horizon(self):
        model = StationClearSkyModel(ClimateStationCatalogue.get(ARLANDA))
        days, altitude = np.array([JUNE_DAY, JUNE_DAY]), np.array([0.0, -10.0])

        assert model.beam_normal(days, altitude).tolist() == [0.0, 0.0]
        assert model.diffuse_horizontal(days, altitude).tolist() == [0.0, 0.0]

    def test_beam_normal_grows_with_altitude(self):
        model = StationClearSkyModel(ClimateStationCatalogue.get(ARLANDA))

        beam = model.beam_normal(np.array([JUNE_DAY, JUNE_DAY]), np.array([10.0, 50.0]))

        assert beam[0] < beam[1]

    def test_station_key(self):
        model = StationClearSkyModel(ClimateStationCatalogue.get(ARLANDA))

        assert model.station_key == ARLANDA

    def test_provider_chooses_model(self):
        station = ClimateStationCatalogue.get(ARLANDA)

        assert isinstance(ClearSkyModelProvider.for_station(station), StationClearSkyModel)
        assert isinstance(ClearSkyModelProvider.for_station(None), GenericClearSkyModel)


class TestEquinoxMinSolarAltitude:
    """Test cases for EquinoxMinSolarAltitude class"""

    # Latitudes of EN 17037 and γs,min of Vychytil & Mohelníková 2024, table 3
    @pytest.mark.parametrize("latitude, expected", [
        (59.65, 8.26),   # Stockholm
        (59.90, 8.16),   # Oslo
        (55.63, 9.92),   # Copenhagen
        (60.32, 8.00),   # Helsinki
        (64.13, 6.63),   # Reykjavik
        (48.12, 13.65),  # Vienna
        (35.54, 22.28),  # Valletta
    ])
    def test_matches_published_capitals(self, latitude, expected):
        assert EquinoxMinSolarAltitude.get(latitude) == pytest.approx(expected, abs=0.02)

    def test_decreases_towards_the_north(self):
        assert EquinoxMinSolarAltitude.get(68.0) < EquinoxMinSolarAltitude.get(56.0)


class TestSkyGapProfile:
    """Test cases for SkyGapProfile class"""

    @staticmethod
    def _result(angle_rad: float, horizon: float, zenith: float) -> dict:
        key = ResponseField.OBSTRUCTION_ANGLE_DEGREES.value
        return {
            ResponseField.DIRECTION_ANGLE.value: angle_rad,
            ResponseField.HORIZON.value: {key: horizon},
            ResponseField.ZENITH.value: {key: zenith},
        }

    @pytest.mark.parametrize("horizon, fraction", [
        (0.0, 1.0), (15.0, 0.674), (30.0, 0.39), (45.0, 0.18), (90.0, 0.0),
    ])
    def test_sky_view_fraction_of_continuous_horizon(self, horizon, fraction):
        profile = SkyGapProfile(
            relative_angles_rad=np.array([-math.pi / 2, math.pi / 2]),
            lower_deg=np.full(2, horizon),
            upper_deg=np.full(2, 90.0),
        )

        assert profile.sky_view_fraction() == pytest.approx(fraction, abs=0.005)

    def test_sky_view_fraction_with_overhang(self):
        # Sky only visible between 0° and 45°: complement of a 45° horizon
        profile = SkyGapProfile(
            relative_angles_rad=np.array([-math.pi / 2, math.pi / 2]),
            lower_deg=np.zeros(2),
            upper_deg=np.full(2, 45.0),
        )

        assert profile.sky_view_fraction() == pytest.approx(0.82, abs=0.005)

    def test_unobstructed_sees_sun_in_front(self):
        profile = SkyGapProfile.unobstructed()

        visible = profile.is_visible(np.array([0.0, 1.0]), np.array([30.0, 80.0]), 0.0)

        assert visible.tolist() == [True, True]

    def test_sun_behind_window_is_never_visible(self):
        profile = SkyGapProfile.unobstructed()

        visible = profile.is_visible(np.array([math.pi, 2.0]), np.array([30.0, 30.0]), 0.0)

        assert visible.tolist() == [False, False]

    def test_from_direction_results_sorts_and_converts_zenith(self):
        results = [self._result(0.5, 10.0, 20.0), self._result(-0.5, 30.0, 0.0)]

        profile = SkyGapProfile.from_direction_results(results, 0.0)

        assert profile.relative_angles_rad.tolist() == [-0.5, 0.5]
        assert profile.lower_deg.tolist() == [30.0, 10.0]
        assert profile.upper_deg.tolist() == [90.0, 70.0]

    def test_sun_below_horizon_obstruction_is_hidden(self):
        results = [self._result(-0.5, 30.0, 0.0), self._result(0.5, 30.0, 0.0)]
        profile = SkyGapProfile.from_direction_results(results, 0.0)

        visible = profile.is_visible(np.array([0.0, 0.0]), np.array([20.0, 40.0]), 0.0)

        assert visible.tolist() == [False, True]

    def test_sun_above_overhang_limit_is_hidden(self):
        results = [self._result(-0.5, 0.0, 40.0), self._result(0.5, 0.0, 40.0)]
        profile = SkyGapProfile.from_direction_results(results, 0.0)

        visible = profile.is_visible(np.array([0.0, 0.0]), np.array([45.0, 60.0]), 0.0)

        assert visible.tolist() == [True, False]

    def test_interpolates_between_directions(self):
        results = [self._result(-0.5, 0.0, 0.0), self._result(0.5, 40.0, 0.0)]
        profile = SkyGapProfile.from_direction_results(results, 0.0)

        visible = profile.is_visible(np.array([0.0, 0.0]), np.array([15.0, 25.0]), 0.0)

        assert visible.tolist() == [False, True]

    def test_relative_to_window_direction(self):
        results = [self._result(math.pi - 0.5, 0.0, 0.0), self._result(math.pi + 0.5, 0.0, 0.0)]
        profile = SkyGapProfile.from_direction_results(results, math.pi)

        visible = profile.is_visible(np.array([math.pi, 0.0]), np.array([30.0, 30.0]), math.pi)

        assert visible.tolist() == [True, False]

    def test_fully_obstructed_fallback_is_never_visible(self):
        results = [self._result(-0.5, 45.0, 45.0), self._result(0.5, 45.0, 45.0)]
        profile = SkyGapProfile.from_direction_results(results, 0.0)

        visible = profile.is_visible(np.array([0.0, 0.0]), np.array([45.0, 60.0]), 0.0)

        assert visible.tolist() == [False, False]

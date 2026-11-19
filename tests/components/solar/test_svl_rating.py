"""Tests for the Miljöbyggnad SVL rating per building type"""

import pytest

from src.components.solar.constants import BuildingType, SvlRating
from src.components.solar.sky_gap_profile import SkyGapProfile
from src.components.solar.svl_calculator import SvlCalculator
from tests.components.solar.solar_fixtures import make_request, make_window


class TestSvlRating:
    """Test cases for the SVL rating"""

    @pytest.mark.parametrize("svl, rating", [
        (10.0, SvlRating.GULD), (18.0, SvlRating.GULD),
        (18.1, SvlRating.SILVER), (29.0, SvlRating.SILVER),
        (38.0, SvlRating.BRONS), (38.1, SvlRating.EJ_UPPFYLLT),
    ])
    def test_residential_limits(self, svl, rating):
        assert SvlCalculator.rate(svl, BuildingType.RESIDENTIAL) == rating

    @pytest.mark.parametrize("svl, rating", [
        (22.0, SvlRating.GULD), (22.1, SvlRating.SILVER),
        (32.0, SvlRating.SILVER), (32.1, SvlRating.BRONS),
        (40.0, SvlRating.BRONS), (40.1, SvlRating.EJ_UPPFYLLT),
    ])
    def test_non_residential_limits(self, svl, rating):
        assert SvlCalculator.rate(svl, BuildingType.NON_RESIDENTIAL) == rating

    def test_building_type_defaults_to_residential(self):
        request = make_request([make_window()])

        assert request.building_type == BuildingType.RESIDENTIAL

    def test_result_reports_the_building_type_of_the_request(self):
        request = make_request([make_window()], building_type="non-residential")
        result = SvlCalculator.calculate(request, [SkyGapProfile.unobstructed()])

        assert result.building_type == BuildingType.NON_RESIDENTIAL
        assert result.to_dict()["building_type"] == "non-residential"
        assert result.rating == SvlCalculator.rate(
            result.svl_peak_w_m2, BuildingType.NON_RESIDENTIAL
        )

    def test_unknown_building_type_is_rejected(self):
        with pytest.raises(ValueError, match="building_type"):
            make_request([make_window()], building_type="hotel")

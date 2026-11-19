import math

import pytest

from src.server.base.constants import EndpointName
from src.server.controllers.obstruction_controller import ObstructionController
from src.server.services.solar_service import SolarService

SOUTH = -math.pi / 2  # Model +Y is north


def _wall(distance: float, height: float, half_width: float = 30.0) -> list:
    """Vertical wall south of the origin, as two triangles"""
    y = -distance
    a, b = [-half_width, y, 0.0], [half_width, y, 0.0]
    c, d = [half_width, y, height], [-half_width, y, height]
    return [a, b, c, a, c, d]


def _request(**extra) -> dict:
    window = {"id": "W1", "x": 0.0, "y": 0.0, "z": 1.5, "direction_angle": SOUTH, "area": 2.0}
    return {"latitude": 59.33, "room_area": 15.0, "windows": [window], **extra}


class TestSolarService:
    """Test cases for SolarService class (real obstruction pipeline)"""

    def test_svl_without_mesh_is_unobstructed(self):
        result = SolarService.calculate_svl(_request())

        assert result.method.value == "clear_sky"
        assert result.svl_peak_w_m2 == pytest.approx(70.0, rel=0.05)
        assert result.simplified_w_m2 == pytest.approx(64.0)

    def test_svl_with_irrelevant_mesh_is_unobstructed(self):
        # Wall entirely below the window: nothing can hide the sun
        result = SolarService.calculate_svl(_request(mesh=_wall(50.0, 1.0)))

        assert result.method.value == "clear_sky_obstruction"
        assert result.svl_peak_w_m2 == pytest.approx(70.0, rel=0.05)

    def test_svl_is_reduced_by_tall_wall(self):
        open_sky = SolarService.calculate_svl(_request(mesh=_wall(50.0, 1.0)))
        obstructed = SolarService.calculate_svl(_request(mesh=_wall(10.0, 30.0)))

        assert obstructed.svl_peak_w_m2 < 0.5 * open_sky.svl_peak_w_m2

    def test_sunlight_hours_without_mesh(self):
        result = SolarService.calculate_sunlight_hours(_request())

        assert result.sunlight_hours == pytest.approx(8.33, abs=0.2)

    def test_sunlight_hours_blocked_by_tall_wall(self):
        result = SolarService.calculate_sunlight_hours(_request(mesh=_wall(10.0, 30.0)))

        assert result.sunlight_hours == 0.0
        assert result.level.value == "not_met"

    def test_sunlight_hours_reduced_by_partial_wall(self):
        # Wall hides the sun around noon (32° > 30° noon altitude) but not
        # beyond its ends (±56° of south)
        open_sky = SolarService.calculate_sunlight_hours(_request())
        obstructed = SolarService.calculate_sunlight_hours(_request(mesh=_wall(20.0, 14.0)))

        assert 0.0 < obstructed.sunlight_hours < open_sky.sunlight_hours


class TestSolarEndpoints:
    """Test cases for the solar endpoints through the controller"""

    def test_svl_success_envelope(self):
        response = ObstructionController.call(EndpointName.SVL, _request())

        assert response["status"] == "success"
        assert response["data"]["svl_rating"] == "Ej uppfyllt"

    def test_sunlight_hours_success_envelope(self):
        response = ObstructionController.call(EndpointName.SUNLIGHT_HOURS, _request())

        assert response["status"] == "success"
        assert response["data"]["sunlight_level"] == "high"

    def test_svl_with_city_reports_the_station(self):
        request = {**_request(mesh=_wall(50.0, 1.0)), "city": "stockholm-arlanda-ap"}
        del request["latitude"]

        response = ObstructionController.call(EndpointName.SVL, request)

        assert response["status"] == "success"
        assert response["data"]["svl_climate_station"] == "stockholm-arlanda-ap"
        assert response["data"]["svl_peak_w_m2"] == pytest.approx(68.6, rel=0.05)

    def test_sunlight_hours_with_city_only(self):
        request = {
            "city": "stockholm-arlanda-ap",
            "windows": [{"x": 0.0, "y": 0.0, "z": 1.5, "direction_angle": SOUTH}],
        }

        response = ObstructionController.call(EndpointName.SUNLIGHT_HOURS, request)

        assert response["status"] == "success"
        assert response["data"]["sunlight_hours"] > 4.0

    def test_sunlight_hours_does_not_need_areas(self):
        request = {
            "latitude": 59.33,
            "windows": [{"x": 0.0, "y": 0.0, "z": 1.5, "direction_angle": SOUTH}],
        }

        response = ObstructionController.call(EndpointName.SUNLIGHT_HOURS, request)

        assert response["status"] == "success"

    @pytest.mark.parametrize("change, message", [
        ({"latitude": None}, "numbers"),
        ({"latitude": 120.0}, "latitude"),
        ({"city": "atlantis"}, "Unknown city"),
        ({"city": 42}, "city"),
        ({"ground_reflectance": 1.5}, "ground_reflectance"),
        ({"windows": []}, "non-empty"),
        ({"room_area": 0.0}, "greater than 0"),
        ({"windows": [{"x": 0.0, "y": 0.0, "z": 1.5, "direction_angle": 0.0}]}, "area"),
        ({"windows": [{"x": 0.0, "y": 0.0, "z": 1.5, "direction_angle": 0.0,
                       "area": 2.0, "shading_type": "curtain"}]}, "shading_type"),
        ({"mesh": "not a list"}, "mesh"),
    ])
    def test_svl_validation_errors(self, change, message):
        response = ObstructionController.call(EndpointName.SVL, _request(**change))

        assert response["status"] == "error"
        assert message in response["error"]

    def test_svl_missing_fields(self):
        response = ObstructionController.call(EndpointName.SVL, {"latitude": 59.33})

        assert response["status"] == "error"
        assert "room_area" in response["error"]
        assert "windows" in response["error"]

    def test_site_is_required(self):
        request = _request()
        del request["latitude"]

        response = ObstructionController.call(EndpointName.SVL, request)

        assert response["status"] == "error"
        assert "city or latitude" in response["error"]

    def test_window_on_mesh_is_rejected(self):
        mesh = [[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 3.0]]

        response = ObstructionController.call(EndpointName.SVL, _request(mesh=mesh))

        assert response["status"] == "error"

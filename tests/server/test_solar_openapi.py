from src.server.openapi import OpenAPISpecGenerator
from src.server.solar_openapi import SolarOpenAPISpec


class TestSolarOpenAPISpec:
    """Test cases for SolarOpenAPISpec class"""

    def test_solar_paths_are_in_the_spec(self):
        spec = OpenAPISpecGenerator.generate_spec()

        assert "/svl" in spec["paths"]
        assert "/sunlight_hours" in spec["paths"]
        assert "/horizon" in spec["paths"]

    def test_solar_schemas_are_in_the_spec(self):
        schemas = OpenAPISpecGenerator.generate_spec()["components"]["schemas"]

        for name in ("SvlRequest", "SunlightHoursRequest", "SvlEnvelope",
                     "SunlightHoursEnvelope", "SolarWindow", "SvlWindowContribution",
                     "ErrorResponse"):
            assert name in schemas

    def test_svl_request_requires_room_area(self):
        schemas = SolarOpenAPISpec.schemas()

        assert "room_area" in schemas["SvlRequest"]["required"]
        assert "room_area" not in schemas["SunlightHoursRequest"]["required"]

    def test_window_contribution_documents_sky_view_fraction(self):
        schemas = SolarOpenAPISpec.schemas()
        items = schemas["SvlEnvelope"]["properties"]["data"]["properties"][
            "svl_window_contributions"]["items"]

        assert items["$ref"].endswith("/SvlWindowContribution")
        assert "sky_view_fraction" in schemas["SvlWindowContribution"]["properties"]

    def test_shading_types_are_listed(self):
        shading = SolarOpenAPISpec.schemas()["SolarWindow"]["properties"]["shading_type"]

        assert "external_blind" in shading["enum"]

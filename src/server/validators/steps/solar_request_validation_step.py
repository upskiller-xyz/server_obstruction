"""
Solar request validation steps

Validate the per-room requests of the SVL and sunlight hours endpoints.
"""

from numbers import Real
from typing import Any, Dict, FrozenSet, List

from src.components.solar.climate_station import ClimateStationCatalogue
from src.components.solar.constants import SolarRequestField
from src.server.base.constants import CENTER_WINDOW_FIELDS, RequestField
from src.server.validators.steps.validation_step import ValidationStep
from src.server.validators.steps.window_not_on_mesh_validation_step import (
    WindowNotOnMeshValidationStep,
)


class SolarRequestValidationStep(ValidationStep):
    """Validates site settings and windows of a solar analysis request"""

    MIN_LATITUDE: float = -90.0
    MAX_LATITUDE: float = 90.0

    _required_fields: FrozenSet[str] = frozenset([SolarRequestField.WINDOWS.value])
    _positive_fields: FrozenSet[str] = frozenset()
    _window_fields: FrozenSet[str] = CENTER_WINDOW_FIELDS | frozenset([
        RequestField.DIRECTION_ANGLE.value,
    ])
    _positive_window_fields: FrozenSet[str] = frozenset()

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check required fields, numeric values and the windows list"""
        cls._require(data, cls._required_fields, "request")
        cls._require_positive(data, cls._positive_fields, "request")
        cls._validate_site(data)
        cls._validate_ground_reflectance(data)

        windows = data[SolarRequestField.WINDOWS.value]
        if not isinstance(windows, list) or not windows:
            raise ValueError("windows must be a non-empty list")

        for index, window in enumerate(windows):
            cls._validate_window(window, f"windows[{index}]")

    @classmethod
    def _validate_site(cls, data: Dict[str, Any]) -> None:
        """The site is given by a climate station key (city), a latitude or both"""
        latitude_field = SolarRequestField.LATITUDE.value
        city = data.get(SolarRequestField.CITY.value)
        if latitude_field not in data and city is None:
            raise ValueError("Missing required fields in request: city or latitude")

        if city is not None:
            if not isinstance(city, str):
                raise ValueError("city must be a climate station key (string)")
            ClimateStationCatalogue.get(city)

        if latitude_field in data:
            cls._require_numbers(data, [latitude_field], "request")
            if not cls.MIN_LATITUDE <= data[latitude_field] <= cls.MAX_LATITUDE:
                raise ValueError("latitude must be between -90 and 90 degrees")

    @classmethod
    def _validate_ground_reflectance(cls, data: Dict[str, Any]) -> None:
        """Optional ground reflectance must be a number between 0 and 1"""
        field = SolarRequestField.GROUND_REFLECTANCE.value
        if field not in data:
            return

        cls._require_numbers(data, [field], "request")
        if not 0.0 <= data[field] <= 1.0:
            raise ValueError("ground_reflectance must be between 0 and 1")

    @classmethod
    def _validate_window(cls, window: Any, label: str) -> None:
        """Validate one window entry"""
        if not isinstance(window, dict):
            raise ValueError(f"{label} must be an object")

        required = cls._window_fields | cls._positive_window_fields
        cls._require(window, required, label)
        cls._require_numbers(window, sorted(required), label)
        cls._require_positive(window, cls._positive_window_fields, label)

    @classmethod
    def _require(cls, data: Dict[str, Any], fields: FrozenSet[str], label: str) -> None:
        """Raise if any required field is missing"""
        missing = sorted(field for field in fields if field not in data)
        if missing:
            raise ValueError(f"Missing required fields in {label}: {', '.join(missing)}")

    @classmethod
    def _require_numbers(cls, data: Dict[str, Any], fields: List[str], label: str) -> None:
        """Raise if any field is not a number"""
        invalid = [
            field for field in fields
            if isinstance(data[field], bool) or not isinstance(data[field], Real)
        ]
        if invalid:
            raise ValueError(f"Fields must be numbers in {label}: {', '.join(invalid)}")

    @classmethod
    def _require_positive(cls, data: Dict[str, Any], fields: FrozenSet[str], label: str) -> None:
        """Raise if any field is not a positive number"""
        cls._require_numbers(data, sorted(fields), label)
        invalid = sorted(field for field in fields if data[field] <= 0)
        if invalid:
            raise ValueError(f"Fields must be greater than 0 in {label}: {', '.join(invalid)}")


class SvlRequestValidationStep(SolarRequestValidationStep):
    """Validates an SVL request: also needs room area and window areas"""

    _required_fields: FrozenSet[str] = SolarRequestValidationStep._required_fields | frozenset([
        SolarRequestField.ROOM_AREA.value,
    ])
    _positive_fields: FrozenSet[str] = frozenset([SolarRequestField.ROOM_AREA.value])
    _positive_window_fields: FrozenSet[str] = frozenset([SolarRequestField.AREA.value])


class SolarWindowsNotOnMeshValidationStep(ValidationStep):
    """Validates that no window center lies on a mesh triangle"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check every window center against the mesh"""
        mesh = data.get(RequestField.MESH.value)
        if not mesh:
            return

        for window in data[SolarRequestField.WINDOWS.value]:
            WindowNotOnMeshValidationStep.call({**window, RequestField.MESH.value: mesh})

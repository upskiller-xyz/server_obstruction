"""
Multi-direction required fields validation step

Validates required fields for multi-direction requests (no direction_angle required).
Supports both center format (x, y, z) and endpoint format (x1..z2 + room_polygon).
Supports split mesh (horizon_mesh/zenith_mesh) and legacy mesh formats.
"""

from typing import Dict, Any, List

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep


def _has_any_mesh(data: Dict[str, Any]) -> bool:
    """Check if the request has mesh data in any supported format."""
    return (
        RequestField.MESH.value in data
        or RequestField.HORIZON_MESH.value in data
        or RequestField.ZENITH_MESH.value in data
    )


_CENTER_WINDOW_FIELDS: List[str] = [
    RequestField.X.value,
    RequestField.Y.value,
    RequestField.Z.value,
]

_ENDPOINT_WINDOW_FIELDS: List[str] = [
    RequestField.X1.value,
    RequestField.Y1.value,
    RequestField.Z1.value,
    RequestField.X2.value,
    RequestField.Y2.value,
    RequestField.Z2.value,
    RequestField.ROOM_POLYGON.value,
]


class MultiDirectionRequiredFieldsValidationStep(ValidationStep):
    """Validates required fields for multi-direction requests (auto-detects format)"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check for required fields in multi-direction requests"""
        is_endpoint_format = RequestField.X1.value in data
        window_fields = _ENDPOINT_WINDOW_FIELDS if is_endpoint_format else _CENTER_WINDOW_FIELDS

        missing_fields = [field for field in window_fields if field not in data]

        if not _has_any_mesh(data):
            missing_fields.append("mesh or horizon_mesh/zenith_mesh")

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

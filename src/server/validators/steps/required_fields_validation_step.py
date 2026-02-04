"""
Required fields validation step

Validates that all required fields are present in the request.
Supports mesh formats:
  - Split format: horizon_mesh and/or zenith_mesh
  - Legacy format: mesh (single combined mesh)

And window formats:
  - Center format: x, y, z, direction_angle
  - Endpoint format: x1, y1, z1, x2, y2, z2, direction_angle, room_polygon
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


# Window-only required fields (mesh checked separately)
_CENTER_WINDOW_FIELDS: List[str] = [
    RequestField.X.value,
    RequestField.Y.value,
    RequestField.Z.value,
    RequestField.DIRECTION_ANGLE.value,
]

_ENDPOINT_WINDOW_FIELDS: List[str] = [
    RequestField.X1.value,
    RequestField.Y1.value,
    RequestField.Z1.value,
    RequestField.X2.value,
    RequestField.Y2.value,
    RequestField.Z2.value,
    RequestField.DIRECTION_ANGLE.value,
    RequestField.ROOM_POLYGON.value,
]


class RequiredFieldsValidationStep(ValidationStep):
    """Validates that all required fields are present (auto-detects format)"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check for required fields based on detected format"""
        is_endpoint_format = RequestField.X1.value in data
        window_fields = _ENDPOINT_WINDOW_FIELDS if is_endpoint_format else _CENTER_WINDOW_FIELDS

        missing_fields = [field for field in window_fields if field not in data]

        if not _has_any_mesh(data):
            missing_fields.append("mesh or horizon_mesh/zenith_mesh")

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

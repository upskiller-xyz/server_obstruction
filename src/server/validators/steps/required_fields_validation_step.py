"""
Required fields validation step

Validates that all required fields are present in the request.
Supports two formats:
  - Center format: x, y, z, direction_angle, mesh
  - Endpoint format: x1, y1, z1, x2, y2, z2, direction_angle, room_polygon, mesh
"""

from typing import Dict, Any, List

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep


# Required fields per format
_CENTER_FIELDS: List[str] = [
    RequestField.X.value,
    RequestField.Y.value,
    RequestField.Z.value,
    RequestField.DIRECTION_ANGLE.value,
    RequestField.MESH.value,
]

_ENDPOINT_FIELDS: List[str] = [
    RequestField.X1.value,
    RequestField.Y1.value,
    RequestField.Z1.value,
    RequestField.X2.value,
    RequestField.Y2.value,
    RequestField.Z2.value,
    RequestField.DIRECTION_ANGLE.value,
    RequestField.ROOM_POLYGON.value,
    RequestField.MESH.value,
]


class RequiredFieldsValidationStep(ValidationStep):
    """Validates that all required fields are present (auto-detects format)"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check for required fields based on detected format"""
        is_endpoint_format = RequestField.X1.value in data

        required_fields = _ENDPOINT_FIELDS if is_endpoint_format else _CENTER_FIELDS
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

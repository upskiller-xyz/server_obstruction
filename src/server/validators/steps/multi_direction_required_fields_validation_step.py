"""
Multi-direction required fields validation step

Validates required fields for multi-direction requests (no direction_angle required).
Supports both center format (x, y, z) and endpoint format (x1..z2 + room_polygon).
"""

from typing import Dict, Any, List

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep


_CENTER_FIELDS: List[str] = [
    RequestField.X.value,
    RequestField.Y.value,
    RequestField.Z.value,
    RequestField.MESH.value,
]

_ENDPOINT_FIELDS: List[str] = [
    RequestField.X1.value,
    RequestField.Y1.value,
    RequestField.Z1.value,
    RequestField.X2.value,
    RequestField.Y2.value,
    RequestField.Z2.value,
    RequestField.ROOM_POLYGON.value,
    RequestField.MESH.value,
]


class MultiDirectionRequiredFieldsValidationStep(ValidationStep):
    """Validates required fields for multi-direction requests (auto-detects format)"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check for required fields in multi-direction requests"""
        is_endpoint_format = RequestField.X1.value in data

        required_fields = _ENDPOINT_FIELDS if is_endpoint_format else _CENTER_FIELDS
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

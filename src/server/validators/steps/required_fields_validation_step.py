"""
Required fields validation step

Validates that all required fields are present in the request.
Mesh format: single mesh parameter with combined geometry

Window formats:
  - Center format: x, y, z, direction_angle
  - Endpoint format: x1, y1, z1, x2, y2, z2, direction_angle, room_polygon
"""

from typing import Any, Dict

from src.server.base.constants import (
    CENTER_WINDOW_FIELDS,
    ENDPOINT_WINDOW_FIELDS,
    RequestField,
)
from src.server.validators.steps.validation_step import ValidationStep


def _has_any_mesh(data: Dict[str, Any]) -> bool:
    """Check if the request has mesh data in any supported format."""
    return (
        RequestField.MESH.value in data
    )

class RequiredFieldsValidationStep(ValidationStep):
    """Validates that all required fields are present (auto-detects format)"""

    @classmethod
    def call(cls, content: Dict[str, Any]) -> None: # type: ignore
        """Check for required fields based on detected format"""
        is_endpoint_format = RequestField.X1.value in content
        window_fields = ENDPOINT_WINDOW_FIELDS if is_endpoint_format else CENTER_WINDOW_FIELDS
        window_fields = [nn for nn in window_fields]
        window_fields.append(RequestField.DIRECTION_ANGLE.value)
        if is_endpoint_format:
            window_fields.append(RequestField.ROOM_POLYGON.value)

        missing_fields = [field for field in window_fields if field not in content]

        if not _has_any_mesh(content):
            missing_fields.append("mesh")

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

"""
Numeric fields validation step

Validates numeric fields are valid numbers.
"""

from typing import Dict, Any

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep


class NumericFieldsValidationStep(ValidationStep):
    """Validates numeric fields are valid numbers (auto-detects format)"""

    _CENTER_NUMERIC = [
        RequestField.X.value,
        RequestField.Y.value,
        RequestField.Z.value,
        RequestField.DIRECTION_ANGLE.value,
    ]

    _ENDPOINT_NUMERIC = [
        RequestField.X1.value,
        RequestField.Y1.value,
        RequestField.Z1.value,
        RequestField.X2.value,
        RequestField.Y2.value,
        RequestField.Z2.value,
        RequestField.DIRECTION_ANGLE.value,
    ]

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Validate numeric fields can be converted to float"""
        is_endpoint_format = RequestField.X1.value in data
        numeric_fields = cls._ENDPOINT_NUMERIC if is_endpoint_format else cls._CENTER_NUMERIC

        for field in numeric_fields:
            if field in data:  # Only validate if present
                try:
                    float(data[field])
                except (TypeError, ValueError):
                    raise ValueError(f"Field '{field}' must be a number")

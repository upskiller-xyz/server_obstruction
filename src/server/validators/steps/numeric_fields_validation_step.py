"""
Numeric fields validation step

Validates numeric fields are valid numbers.
"""

from typing import Any, Dict

from src.server.base.constants import (
    CENTER_WINDOW_FIELDS,
    ENDPOINT_WINDOW_FIELDS,
    RequestField,
)
from src.server.validators.steps.validation_step import ValidationStep


class NumericFieldsValidationStep(ValidationStep):
    """Validates numeric fields are valid numbers (auto-detects format)"""

 

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Validate numeric fields can be converted to float"""
        is_endpoint_format = RequestField.X1.value in data
        numeric_fields = ENDPOINT_WINDOW_FIELDS if is_endpoint_format else CENTER_WINDOW_FIELDS
        numeric_fields = [nn for nn in numeric_fields]

        numeric_fields.append(RequestField.DIRECTION_ANGLE.value)

        for field in numeric_fields:
            if field in data:  # Only validate if present
                try:
                    float(data[field])
                except (TypeError, ValueError):
                    raise ValueError(f"Field '{field}' must be a number")

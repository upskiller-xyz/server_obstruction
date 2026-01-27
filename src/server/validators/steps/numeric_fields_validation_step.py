"""
Numeric fields validation step

Validates numeric fields are valid numbers.
"""

from typing import Dict, Any

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep


class NumericFieldsValidationStep(ValidationStep):
    """Validates numeric fields are valid numbers"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Validate numeric fields can be converted to float"""
        numeric_fields = [
            RequestField.X.value,
            RequestField.Y.value,
            RequestField.Z.value,
            RequestField.DIRECTION_ANGLE.value
        ]

        for field in numeric_fields:
            if field in data:  # Only validate if present
                try:
                    float(data[field])
                except (TypeError, ValueError):
                    raise ValueError(f"Field '{field}' must be a number")

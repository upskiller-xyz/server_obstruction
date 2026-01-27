"""
Multi-direction required fields validation step

Validates required fields for multi-direction requests (no direction_angle required).
"""

from typing import Dict, Any

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep


class MultiDirectionRequiredFieldsValidationStep(ValidationStep):
    """Validates required fields for multi-direction requests (no direction_angle required)"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check for required fields in multi-direction requests"""
        required_fields = [
            RequestField.X.value,
            RequestField.Y.value,
            RequestField.Z.value,
            RequestField.MESH.value
        ]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

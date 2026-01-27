"""
Required fields validation step

Validates that all required fields are present in the request.
"""

from typing import Dict, Any

from src.server.base.constants import RequestField
from src.server.validators.steps.validation_step import ValidationStep


class RequiredFieldsValidationStep(ValidationStep):
    """Validates that all required fields are present"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check for required fields"""
        required_fields = [
            RequestField.X.value,
            RequestField.Y.value,
            RequestField.Z.value,
            RequestField.DIRECTION_ANGLE.value,
            RequestField.MESH.value
        ]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

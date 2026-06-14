"""
Optional parameters validation step

Validates optional parameters for multi-direction requests.
"""

from typing import Any, Dict

from src.server.base.constants import OptionalRequestField
from src.server.validators.steps.validation_step import ValidationStep


class OptionalParametersValidationStep(ValidationStep):
    """Validates optional parameters for multi-direction requests"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Validate optional multi-direction parameters"""
        # Validate num_directions if provided
        num_directions = data.get(OptionalRequestField.NUM_DIRECTIONS.value, None)
        if num_directions is not None:
            if not isinstance(num_directions, int) or num_directions < 1:
                raise ValueError("num_directions must be a positive integer")

        # Validate angle ranges if provided
        start_angle_degrees = data.get(OptionalRequestField.START_ANGLE_DEGREES.value, None)
        if start_angle_degrees is not None:
            if not isinstance(start_angle_degrees, (int, float)):
                raise ValueError("start_angle_degrees must be a number")

        end_angle_degrees = data.get(OptionalRequestField.END_ANGLE_DEGREES.value, None)
        if end_angle_degrees is not None:
            if not isinstance(end_angle_degrees, (int, float)):
                raise ValueError("end_angle_degrees must be a number")

"""Request validation logic for obstruction calculations"""

from typing import Dict, Any, List, Type
from src.components.constants import EndpointName
from src.server.validators.validation_steps import (
    ValidationStep,
    RequiredFieldsValidationStep,
    MultiDirectionRequiredFieldsValidationStep,
    MeshFormatValidationStep,
    VertexFormatValidationStep,
    NumericFieldsValidationStep,
    WindowNotOnMeshValidationStep,
    OptionalParametersValidationStep
)
from src.utils.standard_map import StandardMap

OBSTRUCTION_VALIDATION_STEPS: List[Type[ValidationStep]] = [
        RequiredFieldsValidationStep,
        MeshFormatValidationStep,
        VertexFormatValidationStep,
        NumericFieldsValidationStep,
        WindowNotOnMeshValidationStep
    ]

MULTI_DIRECTION_VALIDATION_STEPS: List[Type[ValidationStep]] = [
    MultiDirectionRequiredFieldsValidationStep,
    MeshFormatValidationStep,
    VertexFormatValidationStep,
    WindowNotOnMeshValidationStep,
    OptionalParametersValidationStep
]

class EndpointValidation(StandardMap):

    _content: Dict[EndpointName, list[Type[ValidationStep]]] = {
        EndpointName.OBSTRUCTION_ALL: MULTI_DIRECTION_VALIDATION_STEPS,
        EndpointName.OBSTRUCTION_PARALLEL: MULTI_DIRECTION_VALIDATION_STEPS,
        EndpointName.STATUS: []  # Status endpoint needs no validation
    }
    _default:list[Type[ValidationStep]] = OBSTRUCTION_VALIDATION_STEPS


class RequestValidator:
    """
    Validates request data for obstruction calculations using Strategy Pattern

    Responsibilities (Single Responsibility Principle):
    - Coordinate validation steps for different request types
    - Execute validation pipeline

    Uses Strategy Pattern:
    - Each validation step is a strategy
    - RequestValidator orchestrates the steps
    """

    # Strategy Pattern: Define validation pipelines for different request types
    

    @classmethod
    def call(cls, endpoint:EndpointName, data: Dict[str, Any]) -> None:
        """
        Validate obstruction calculation request data

        Args:
            data: Request data dictionary

        Raises:
            ValueError: If required fields are missing or invalid
            PointOnTriangleError: If window center lies on mesh
        """
        steps = EndpointValidation.get(endpoint)
        _ = [s.call(data) for s in steps]
        

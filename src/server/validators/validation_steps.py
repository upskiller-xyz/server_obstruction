"""Validation step classes for request validation using Strategy Pattern"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
from src.components.constants import RequestField, OptionalRequestField
from src.components.validators import GeometricValidator, PointOnTriangleError
from src.components.geometry import Point3D, Mesh

logger = logging.getLogger(__name__)


class ValidationStep(ABC):
    """
    Abstract base class for validation steps

    Each validation step implements a specific validation concern.
    Uses Strategy Pattern - each step is a strategy for validation.
    """

    @classmethod
    @abstractmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """
        Execute validation step

        Args:
            data: Request data dictionary

        Raises:
            ValueError: If validation fails
            PointOnTriangleError: If geometric validation fails
        """
        pass


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


class MeshFormatValidationStep(ValidationStep):
    """Validates mesh format and structure"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Validate mesh is a list with proper structure"""
        mesh = data[RequestField.MESH.value]

        if not isinstance(mesh, list):
            raise ValueError("Mesh must be a list of vertices")

        if len(mesh) == 0:
            raise ValueError("Mesh cannot be empty")

        # Handle mesh vertices not divisible by 3
        if len(mesh) % 3 != 0:
            extra_vertices = len(mesh) % 3
            original_count = len(mesh)
            # Trim extra vertices (1-2 vertices)
            data[RequestField.MESH.value] = mesh[:-extra_vertices]
            logger.warning(
                f"Mesh had {original_count} vertices (not divisible by 3). "
                f"Trimmed {extra_vertices} extra vertex/vertices. "
                f"Proceeding with {len(data[RequestField.MESH.value])} vertices."
            )


class VertexFormatValidationStep(ValidationStep):
    """Validates individual vertex format"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Validate each vertex has 3 coordinates"""
        mesh = data[RequestField.MESH.value]

        for i, vertex in enumerate(mesh):
            if not isinstance(vertex, (list, tuple)) or len(vertex) != 3:
                raise ValueError(
                    f"Vertex {i} must be a list/tuple of 3 coordinates [x, y, z]"
                )


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


class WindowNotOnMeshValidationStep(ValidationStep):
    """Validates that window center doesn't lie on any mesh triangle"""

    @classmethod
    def call(cls, data: Dict[str, Any]) -> None:
        """Check window center is not on mesh surface"""
        # Extract window center
        window_center = Point3D(
            x=float(data[RequestField.X.value]),
            y=float(data[RequestField.Y.value]),
            z=float(data[RequestField.Z.value])
        )

        # Create mesh from vertices
        mesh = Mesh.from_vertices(data[RequestField.MESH.value])

        # Validate window center doesn't lie on any triangle
        GeometricValidator.validate_point_not_on_mesh(
            window_center,
            mesh.triangles
        )


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

"""
Base validation step interface

Abstract base class for validation steps using Strategy Pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


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

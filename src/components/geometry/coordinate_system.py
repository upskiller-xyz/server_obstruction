"""
World coordinate system definition

Defines axes, directions, and coordinate manipulation utilities.
"""

import numpy as np


class CoordinateSystem:
    """
    World coordinate system definition

    Convention:
    - X-axis: Horizontal, points East (default forward direction at angle=0)
    - Y-axis: Horizontal, points North
    - Z-axis: Vertical, points Up

    This matches the single-angle rotation system where:
    - direction_angle = 0: faces +X (East)
    - direction_angle = π/2: faces +Y (North)
    """

    # Axis unit vectors as numpy arrays
    X_AXIS = np.array([1.0, 0.0, 0.0])
    Y_AXIS = np.array([0.0, 1.0, 0.0])
    Z_AXIS = np.array([0.0, 0.0, 1.0])

    # Semantic names (numpy arrays)
    UP = Z_AXIS          # Vertical up direction
    FORWARD = X_AXIS     # Default forward direction (angle=0)
    NORTH = Y_AXIS       # North direction (angle=π/2)

    # Index mapping for coordinate components
    VERTICAL_INDEX = 2   # Z component is vertical
    HORIZONTAL_INDICES = [0, 1]  # X, Y components are horizontal

    @classmethod
    def remove_vertical_component(cls, vector: np.ndarray) -> np.ndarray:
        """
        Remove the vertical component from a vector

        Args:
            vector: Input vector (numpy array)

        Returns:
            Vector with vertical component set to zero
        """
        result = vector.copy()
        result[cls.VERTICAL_INDEX] = 0.0
        return result

    @classmethod
    def get_vertical_component(cls, vector: np.ndarray) -> float:
        """
        Get the vertical component of a vector

        Args:
            vector: Input vector (numpy array)

        Returns:
            Vertical component value
        """
        return float(vector[cls.VERTICAL_INDEX])

    @classmethod
    def set_vertical_component(cls, vector: np.ndarray, value: float) -> np.ndarray:
        """
        Set the vertical component of a vector

        Args:
            vector: Input vector (numpy array)
            value: Value to set

        Returns:
            New vector with vertical component set
        """
        result = vector.copy()
        result[cls.VERTICAL_INDEX] = value
        return result

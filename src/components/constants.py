"""Constants and enums for the obstruction calculation system"""
from enum import Enum


class MathConstants:
    """Mathematical constants for calculations"""
    EPSILON = 1e-6  # Minimum distance threshold to avoid division by zero


class ThresholdConstants:
    """Threshold values for various calculations"""
    PLANE_THRESHOLD_TIGHT = 0.1  # Tight threshold for horizon calculations
    PLANE_THRESHOLD_WIDE = 2.5  # Wide threshold for zenith/worst-case calculations
    VERTICAL_SURFACE_THRESHOLD = 0.3  # Threshold for detecting vertical surfaces
    HORIZONTAL_SURFACE_THRESHOLD = 0.7  # Threshold for detecting horizontal surfaces


class ResponseStatus(Enum):
    """Response status values for API responses"""
    SUCCESS = "success"
    ERROR = "error"


class ControllerStatus(Enum):
    """Controller status values"""
    READY = "ready"
    ERROR = "error"


class RequestField(Enum):
    """Required and optional field names for requests"""
    # Position fields
    X = "x"
    Y = "y"
    Z = "z"

    # Direction field
    DIRECTION_ANGLE = "direction_angle"

    # Mesh
    MESH = "mesh"


class ResponseField(Enum):
    """Field names for responses"""
    STATUS = "status"
    DATA = "data"
    ERROR = "error"
    CONTROLLER = "controller"
    SERVICE = "service"
    HORIZON = "horizon"
    ZENITH = "zenith"

    # Result fields
    OBSTRUCTION_ANGLE_DEGREES = "obstruction_angle_degrees"
    OBSTRUCTION_ANGLE_RADIANS = "obstruction_angle_radians"
    HIGHEST_POINT = "highest_point"
    PROJECTED_POINT_COUNT = "projected_point_count"

    # Validation error fields
    WINDOW_CENTER = "window_center"
    TRIANGLE = "triangle"
    VERTICES = "vertices"

"""Constants and enums for the obstruction calculation system"""

from enum import Enum
from ...utils.extended_enum import ExtendedEnumMixin


class ANGLES(ExtendedEnumMixin, Enum):
    ZENITH = "zenith"
    HORIZON = "horizon"


class TriangleOrientation(ExtendedEnumMixin, Enum):
    """Triangle surface orientation types"""
    VERTICAL = "vertical"  # Walls, vertical surfaces
    HORIZONTAL = "horizontal"  # Roofs, floors
    SLANTED = "slanted"  # Neither vertical nor horizontal

class HTTPMethod(ExtendedEnumMixin, Enum):
    """HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class HTTPStatus(ExtendedEnumMixin, Enum):
    """HTTP status codes"""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


class ContentType(ExtendedEnumMixin, Enum):
    """Content type values"""
    JSON = "application/json"
    TEXT = "text/plain"
    HTML = "text/html"
    XML = "application/xml"


class EndpointName(ExtendedEnumMixin, Enum):
    """API endpoint names"""
    STATUS = "get_status"
    ROUTES = "routes"
    HORIZON_ANGLE = "horizon"
    OBSTRUCTION = "obstruction"
    ZENITH_ANGLE = "zenith"
    OBSTRUCTION_ALL = "obstruction_all"
    OBSTRUCTION_PARALLEL = "obstruction_parallel"

class MathConstants(ExtendedEnumMixin, Enum):
    """Mathematical constants for calculations"""
    EPSILON = 1e-6  # Minimum distance threshold to avoid division by zero


class ThresholdConstants(ExtendedEnumMixin, Enum):
    """Threshold values for various calculations"""
    PLANE_THRESHOLD_TIGHT = 0.1  # Tight threshold for horizon calculations
    PLANE_THRESHOLD_WIDE = 2.5  # Wide threshold for zenith/worst-case calculations
    VERTICAL_SURFACE_THRESHOLD = 0.3  # Threshold for detecting vertical surfaces
    HORIZONTAL_SURFACE_THRESHOLD = 0.7  # Threshold for detecting horizontal surfaces


class AllDirectionDefaults(ExtendedEnumMixin, Enum):
    """Default values for all-direction obstruction calculations"""
    NUM_DIRECTIONS = 64  # Default number of directions to sample
    START_ANGLE_DEGREES = 17.5  # Start angle in degrees (relative to window normal)
    END_ANGLE_DEGREES = 162.5  # End angle in degrees (relative to window normal)


class ResponseStatus(ExtendedEnumMixin, Enum):
    """Response status values for API responses"""
    SUCCESS = "success"
    ERROR = "error"


class ControllerStatus(ExtendedEnumMixin, Enum):
    """Controller status values"""
    READY = "ready"
    ERROR = "error"


class RequestField(ExtendedEnumMixin, Enum):
    """Required and optional field names for requests"""
    # Position fields
    X = "x"
    Y = "y"
    Z = "z"

    # Direction field
    DIRECTION_ANGLE = "direction_angle"

    # Mesh
    MESH = "mesh"


class OptionalRequestField(ExtendedEnumMixin, Enum):
    """Optional field names for multi-direction requests"""
    NUM_DIRECTIONS = "num_directions"
    START_ANGLE_DEGREES = "start_angle_degrees"
    END_ANGLE_DEGREES = "end_angle_degrees"


class ResponseField(ExtendedEnumMixin, Enum):
    """Field names for responses"""
    STATUS = "status"
    DATA = "data"
    ERROR = "error"
    CONTROLLER = "controller"
    SERVICE = "service"
    HORIZON = "horizon"
    ZENITH = "zenith"
    DIRECTION_ANGLE = "direction_angle"
    DIRECTION_ANGLE_DEGREES = "direction_angle_degrees"
    RESULTS = "results"
    NUM_DIRECTIONS = "num_directions"
    TOTAL_TIME_SECONDS = "total_time_seconds"

    # Result fields
    OBSTRUCTION_ANGLE_DEGREES = "obstruction_angle_degrees"
    OBSTRUCTION_ANGLE_RADIANS = "obstruction_angle_radians"
    HIGHEST_POINT = "highest_point"
    PROJECTED_POINT_COUNT = "projected_point_count"

    # Validation error fields
    WINDOW_CENTER = "window_center"
    TRIANGLE = "triangle"
    VERTICES = "vertices"

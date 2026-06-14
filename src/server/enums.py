from enum import Enum

from ..utils.extended_enum import ExtendedEnumMixin


class ModelStatus(ExtendedEnumMixin, Enum):
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


class ServerStatus(ExtendedEnumMixin, Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class LogLevel(ExtendedEnumMixin, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ContentType(ExtendedEnumMixin, Enum):
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_WEBP = "image/webp"
    IMAGE_BMP = "image/bmp"

    @classmethod
    def is_image(cls, content_type: str) -> bool:
        return content_type.startswith('image/')


class HTTPStatus(ExtendedEnumMixin, Enum):
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500
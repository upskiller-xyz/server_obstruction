from enum import Enum
from ..utils.extended_enum import ExtendedEnumMixin


class ModelStatus(ExtendedEnumMixin):
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


class ServerStatus(ExtendedEnumMixin):
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class LogLevel(ExtendedEnumMixin):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ContentType(ExtendedEnumMixin):
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_WEBP = "image/webp"
    IMAGE_BMP = "image/bmp"

    @classmethod
    def is_image(cls, content_type: str) -> bool:
        return content_type.startswith('image/')


class HTTPStatus(ExtendedEnumMixin):
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500
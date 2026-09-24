"""Internal exception details never reach the caller."""
from src.server.builders import ErrorResponseBuilder
from src.server.base.constants import ResponseField

SECRET = "/srv/app/secret.py"


def test_calculation_error_is_generic():
    body = ErrorResponseBuilder.from_exception(RuntimeError(SECRET), "horizon")
    assert SECRET not in body[ResponseField.ERROR.value]
    assert "horizon" in body[ResponseField.ERROR.value]


def test_validation_error_keeps_message():
    body = ErrorResponseBuilder.from_exception(ValueError("x must be a number"))
    assert "x must be a number" in body[ResponseField.ERROR.value]

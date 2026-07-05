"""JSON parsing adapter — prefer orjson, fall back to stdlib json.

Adapter Pattern: exposes a single ``loads`` interface (plus the decode-error type)
regardless of whether the optional high-performance ``orjson`` backend is present.
orjson stays the production default (fast parsing of the full-mesh request body);
the stdlib fallback keeps the code importable where the C extension is not
installed (e.g. minimal CI/test environments).
"""

import json
from typing import Any, Union

try:
    import orjson
    _HAS_ORJSON = True
except ImportError:  # pragma: no cover - depends on optional dependency
    orjson = None
    _HAS_ORJSON = False


class JsonCodec:
    """Unified JSON loader backed by orjson when available, stdlib json otherwise."""

    # orjson.JSONDecodeError subclasses json.JSONDecodeError, so catching the
    # stdlib type covers both backends.
    JSONDecodeError = json.JSONDecodeError

    @staticmethod
    def loads(data: Union[str, bytes]) -> Any:
        """Deserialize a JSON string/bytes payload to a Python object."""
        if _HAS_ORJSON:
            return orjson.loads(data)
        return json.loads(data)

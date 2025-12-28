from __future__ import annotations
from typing import Any, Dict


class StandardMap:
    _content:Dict[Any, Any] = {}
    _default: Any
    @classmethod
    def get(cls, key:Any)->Any:
        return cls._content.get(key, cls._default)
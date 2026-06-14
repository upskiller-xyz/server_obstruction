"""Lightweight stage timing for latency investigation.

Use as a context manager to log how long a named stage took. Logs at INFO with a
``[timing]`` prefix so it is greppable without enabling DEBUG.

    with StageTimer("mesh_build", logger):
        mesh = build(...)

Keep timers at *coarse* stages only (parse / mesh-build / whole compute). Do NOT
wrap per-direction or per-ray work — at 64 directions that would add thousands of
log lines and measurable overhead. One ``perf_counter`` pair + one log line per
stage is negligible.
"""
import logging
import time
from types import TracebackType
from typing import Optional, Type


class StageTimer:
    """Logs the wall time of a named stage on exit (always, even on exception)."""

    def __init__(self, stage: str, logger: logging.Logger):
        self._stage = stage
        self._logger = logger
        self._t0 = 0.0

    def __enter__(self) -> "StageTimer":
        self._t0 = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> bool:
        elapsed_ms = (time.perf_counter() - self._t0) * 1000
        # Parameterized logging: the message is only formatted if INFO is enabled.
        self._logger.info("[timing] %s: %.0fms", self._stage, elapsed_ms)
        return False  # never suppress exceptions

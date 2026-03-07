"""
Gap verification result model

Result of verifying a single gap with ray casting.
"""

from dataclasses import dataclass
from typing import Optional

from src.server.base.constants import GapVerificationStatus


@dataclass(frozen=True)
class GapVerificationResult:
    """Result of gap verification with ray casting."""
    status: GapVerificationStatus
    horizon_deg: Optional[float] = None
    zenith_deg: Optional[float] = None
    rays_cast: int = 0

"""
Server models (backward compatibility wrapper)

Re-exports models from src.components.models for backward compatibility.
New code should import directly from src.components.models.
"""

from src.components.models import IntersectionResult

__all__ = [
    'IntersectionResult'
]

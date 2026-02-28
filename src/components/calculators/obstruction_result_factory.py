"""
Obstruction result factory

Factory for creating obstruction results from gap calculations.
"""

from src.components.models import GapObstructionResult


class ObstructionResultFactory:
    """Factory for creating obstruction results."""

    @staticmethod
    def create_from_gap(
        horizon_deg: float=0,
        zenith_deg: float=0
    ) -> GapObstructionResult:
        """
        Create result from gap boundaries.

        Args:
            horizon_deg: Horizon angle in degrees
            zenith_deg: Zenith angle in degrees

        Returns:
            GapObstructionResult
        """
        return GapObstructionResult(
            horizon_deg=horizon_deg,
            zenith_deg=zenith_deg
        )

    @staticmethod
    def create_empty() -> GapObstructionResult:
        """
        Create empty result (fully obstructed).

        Returns:
            GapObstructionResult with default fallback angles
        """
        return GapObstructionResult(
            horizon_deg=45.0,  # Default fallback
            zenith_deg=45.0
        )

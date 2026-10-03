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
    def create_fully_obstructed() -> GapObstructionResult:
        """
        Create the fully-obstructed fallback result.

        Used only when geometry is present but no angular gap admits sky.

        Returns:
            GapObstructionResult with the 45°/45° fallback angles
        """
        return GapObstructionResult(
            horizon_deg=45.0,
            zenith_deg=45.0
        )

    @staticmethod
    def create_unobstructed() -> GapObstructionResult:
        """
        Create the unobstructed (full sky) result.

        Used when no geometry remains ahead of and above the window, i.e. nothing
        can block the sky.

        Returns:
            GapObstructionResult with 0°/0° (full sky visible)
        """
        return GapObstructionResult.empty()

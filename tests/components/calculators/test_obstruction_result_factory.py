import pytest

from src.components.calculators.obstruction_result_factory import ObstructionResultFactory
from src.components.models import GapObstructionResult


class TestObstructionResultFactory:
    """Test cases for ObstructionResultFactory"""

    def test_create_from_gap_creates_valid_result(self):
        """Test creating result from gap boundaries"""
        horizon_deg = 15.5
        zenith_deg = 25.3

        result = ObstructionResultFactory.create_from_gap(horizon_deg, zenith_deg)

        assert isinstance(result, GapObstructionResult)
        assert result.horizon_deg == horizon_deg
        assert result.zenith_deg == zenith_deg

    def test_create_from_gap_with_zero_values(self):
        """Test creating result with zero values"""
        result = ObstructionResultFactory.create_from_gap(0.0, 0.0)

        assert result.horizon_deg == 0.0
        assert result.zenith_deg == 0.0

    def test_create_from_gap_with_max_values(self):
        """Test creating result with maximum angle values"""
        result = ObstructionResultFactory.create_from_gap(90.0, 90.0)

        assert result.horizon_deg == 90.0
        assert result.zenith_deg == 90.0

    def test_create_empty_returns_default_fallback(self):
        """Test creating empty result returns default fallback values"""
        result = ObstructionResultFactory.create_empty()

        assert isinstance(result, GapObstructionResult)
        assert result.horizon_deg == 45.0
        assert result.zenith_deg == 45.0

    def test_create_from_gap_is_stateless(self):
        """Test that factory method is stateless"""
        horizon_deg = 20.0
        zenith_deg = 30.0

        result1 = ObstructionResultFactory.create_from_gap(horizon_deg, zenith_deg)
        result2 = ObstructionResultFactory.create_from_gap(horizon_deg, zenith_deg)

        assert result1.horizon_deg == result2.horizon_deg
        assert result1.zenith_deg == result2.zenith_deg

    def test_create_empty_is_stateless(self):
        """Test that create_empty is stateless"""
        result1 = ObstructionResultFactory.create_empty()
        result2 = ObstructionResultFactory.create_empty()

        assert result1.horizon_deg == result2.horizon_deg
        assert result1.zenith_deg == result2.zenith_deg

    def test_create_from_gap_preserves_precision(self):
        """Test that factory preserves float precision"""
        horizon_deg = 15.123456789
        zenith_deg = 25.987654321

        result = ObstructionResultFactory.create_from_gap(horizon_deg, zenith_deg)

        assert result.horizon_deg == horizon_deg
        assert result.zenith_deg == zenith_deg

    def test_create_from_gap_with_negative_values(self):
        """Test creating result with negative values (edge case)"""
        # Though unusual, factory should accept any float values
        result = ObstructionResultFactory.create_from_gap(-10.0, -5.0)

        assert result.horizon_deg == -10.0
        assert result.zenith_deg == -5.0

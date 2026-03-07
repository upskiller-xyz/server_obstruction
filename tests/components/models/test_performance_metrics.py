import logging
import pytest

from src.components.models.performance_metrics import PerformanceMetrics
from src.server.base.constants import ObstructionStatus


class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics"""

    def test_create_performance_metrics(self):
        """Test creating performance metrics dataclass"""
        metrics = PerformanceMetrics(
            elapsed_ms=123.45,
            rays_cast=42,
            gaps_tested=3,
            intersection_points=15
        )

        assert metrics.elapsed_ms == 123.45
        assert metrics.rays_cast == 42
        assert metrics.gaps_tested == 3
        assert metrics.intersection_points == 15

    def test_create_with_zero_values(self):
        """Test creating metrics with zero values"""
        metrics = PerformanceMetrics(
            elapsed_ms=0.0,
            rays_cast=0,
            gaps_tested=0,
            intersection_points=0
        )

        assert metrics.elapsed_ms == 0.0
        assert metrics.rays_cast == 0
        assert metrics.gaps_tested == 0
        assert metrics.intersection_points == 0

    def test_log_summary_fully_obstructed(self, caplog):
        """Test logging summary for fully obstructed status"""
        metrics = PerformanceMetrics(
            elapsed_ms=100.5,
            rays_cast=10,
            gaps_tested=5,
            intersection_points=20
        )

        with caplog.at_level(logging.DEBUG):
            metrics.log_summary(ObstructionStatus.FULLY_OBSTRUCTED)

        # Check log contains expected information
        assert len(caplog.records) == 1
        log_message = caplog.records[0].message
        assert "fully_obstructed" in log_message
        assert "Rays: 10" in log_message
        assert "Gaps tested: 5" in log_message
        assert "Intersections: 20" in log_message
        assert "100.5ms" in log_message

    def test_log_summary_partially_obstructed(self, caplog):
        """Test logging summary for partially obstructed status"""
        metrics = PerformanceMetrics(
            elapsed_ms=250.75,
            rays_cast=25,
            gaps_tested=2,
            intersection_points=30
        )

        with caplog.at_level(logging.DEBUG):
            metrics.log_summary(ObstructionStatus.PARTIALLY_OBSTRUCTED)

        assert len(caplog.records) == 1
        log_message = caplog.records[0].message
        assert "partially_obstructed" in log_message
        assert "Rays: 25" in log_message
        assert "250.8ms" in log_message  # Rounded to 1 decimal (250.75 rounds to 250.8)

    def test_log_summary_no_obstruction(self, caplog):
        """Test logging summary for no obstruction status"""
        metrics = PerformanceMetrics(
            elapsed_ms=50.0,
            rays_cast=5,
            gaps_tested=1,
            intersection_points=0
        )

        with caplog.at_level(logging.DEBUG):
            metrics.log_summary(ObstructionStatus.NO_OBSTRUCTION)

        assert len(caplog.records) == 1
        log_message = caplog.records[0].message
        assert "no_obstruction" in log_message
        assert "Rays: 5" in log_message

    def test_log_summary_uses_debug_level(self, caplog):
        """Test that log_summary uses DEBUG level"""
        metrics = PerformanceMetrics(
            elapsed_ms=100.0,
            rays_cast=10,
            gaps_tested=3,
            intersection_points=15
        )

        with caplog.at_level(logging.DEBUG):
            metrics.log_summary(ObstructionStatus.FULLY_OBSTRUCTED)

        assert caplog.records[0].levelname == "DEBUG"

    def test_log_summary_formats_elapsed_time(self, caplog):
        """Test that elapsed time is formatted to 1 decimal place"""
        metrics = PerformanceMetrics(
            elapsed_ms=123.456789,
            rays_cast=1,
            gaps_tested=1,
            intersection_points=1
        )

        with caplog.at_level(logging.DEBUG):
            metrics.log_summary(ObstructionStatus.FULLY_OBSTRUCTED)

        log_message = caplog.records[0].message
        assert "123.5ms" in log_message

    def test_dataclass_is_immutable(self):
        """Test that PerformanceMetrics dataclass is frozen (immutable)"""
        metrics = PerformanceMetrics(
            elapsed_ms=100.0,
            rays_cast=10,
            gaps_tested=3,
            intersection_points=15
        )

        # Attempting to modify should raise error
        with pytest.raises(AttributeError):
            metrics.elapsed_ms = 200.0

    def test_dataclass_equality(self):
        """Test that two metrics with same values are equal"""
        metrics1 = PerformanceMetrics(
            elapsed_ms=100.0,
            rays_cast=10,
            gaps_tested=3,
            intersection_points=15
        )

        metrics2 = PerformanceMetrics(
            elapsed_ms=100.0,
            rays_cast=10,
            gaps_tested=3,
            intersection_points=15
        )

        assert metrics1 == metrics2

    def test_log_summary_with_large_values(self, caplog):
        """Test logging with large metric values"""
        metrics = PerformanceMetrics(
            elapsed_ms=9999.99,
            rays_cast=10000,
            gaps_tested=1000,
            intersection_points=50000
        )

        with caplog.at_level(logging.DEBUG):
            metrics.log_summary(ObstructionStatus.PARTIALLY_OBSTRUCTED)

        log_message = caplog.records[0].message
        assert "Rays: 10000" in log_message
        assert "Gaps tested: 1000" in log_message
        assert "Intersections: 50000" in log_message

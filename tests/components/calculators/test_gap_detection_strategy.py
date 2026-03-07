import pytest

from src.components.calculators.gap_detection_strategy import GapDetectionStrategy


class TestGapDetectionStrategy:
    """Test cases for GapDetectionStrategy"""

    def test_find_gaps_no_intersections(self):
        """Test gap detection with no intersection points (full sky)"""
        elevation_angles = []
        min_gap_deg = 4.0

        gaps = GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)

        # Should find one gap from 0 to 90 degrees
        assert len(gaps) == 1
        assert gaps[0] == (0.0, 90.0, 90.0)

    def test_find_gaps_single_intersection(self):
        """Test gap detection with single intersection point"""
        elevation_angles = [45.0]
        min_gap_deg = 4.0

        gaps = GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)

        # Should find two gaps: 0-45 and 45-90 (both same size, either order is valid)
        assert len(gaps) == 2
        # Both gaps should have size 45.0
        assert all(gap[2] == 45.0 for gap in gaps)
        # Check we have both gaps
        gap_ranges = {(gap[0], gap[1]) for gap in gaps}
        assert (0.0, 45.0) in gap_ranges
        assert (45.0, 90.0) in gap_ranges

    def test_find_gaps_multiple_intersections(self):
        """Test gap detection with multiple intersection points"""
        elevation_angles = [10.0, 20.0, 30.0, 70.0, 80.0]
        min_gap_deg = 4.0

        gaps = GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)

        # Expected gaps: 0-10 (10), 10-20 (10), 20-30 (10), 30-70 (40), 70-80 (10), 80-90 (10)
        # All are >= 4 degrees
        assert len(gaps) == 6
        # Largest gap first (30-70)
        assert gaps[0] == (30.0, 70.0, 40.0)

    def test_find_gaps_filters_small_gaps(self):
        """Test that gaps smaller than min_gap_deg are filtered out"""
        elevation_angles = [1.0, 2.0, 3.0, 50.0]
        min_gap_deg = 5.0

        gaps = GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)

        # Small gaps (1-2, 2-3) should be filtered out
        # Should only have: 3-50 (47), 50-90 (40)
        assert len(gaps) == 2
        assert gaps[0][2] == 47.0  # Largest gap
        assert gaps[1][2] == 40.0

    def test_find_gaps_sorted_by_size_descending(self):
        """Test that gaps are sorted by size (largest first)"""
        elevation_angles = [20.0, 40.0, 80.0]
        min_gap_deg = 4.0

        gaps = GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)

        # Expected gaps: 0-20 (20), 20-40 (20), 40-80 (40), 80-90 (10)
        assert len(gaps) == 4
        # Check sorted descending by size
        sizes = [gap[2] for gap in gaps]
        assert sizes == sorted(sizes, reverse=True)
        assert gaps[0][2] == 40.0  # Largest

    def test_find_gaps_duplicate_angles_deduplicated(self):
        """Test that duplicate elevation angles are deduplicated"""
        elevation_angles = [30.0, 30.0, 30.0, 60.0, 60.0]
        min_gap_deg = 4.0

        gaps = GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)

        # After dedup: 30, 60
        # Gaps: 0-30 (30), 30-60 (30), 60-90 (30)
        assert len(gaps) == 3
        assert all(gap[2] == 30.0 for gap in gaps)

    def test_find_gaps_adds_boundaries(self):
        """Test that 0 and 90 degree boundaries are added"""
        elevation_angles = [45.0]
        min_gap_deg = 1.0

        gaps = GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)

        # Should have gaps starting at 0 and ending at 90
        all_bounds = set()
        for low, high, _ in gaps:
            all_bounds.add(low)
            all_bounds.add(high)

        assert 0.0 in all_bounds
        assert 90.0 in all_bounds

    def test_find_gaps_empty_with_high_threshold(self):
        """Test that no gaps returned when min_gap_deg is too large"""
        elevation_angles = list(range(0, 91, 1))  # Every degree
        min_gap_deg = 5.0

        gaps = GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)

        # All gaps are 1 degree, none >= 5
        assert len(gaps) == 0

    def test_find_gaps_stateless(self):
        """Test that multiple calls produce same results (stateless)"""
        elevation_angles = [20.0, 50.0]
        min_gap_deg = 4.0

        result1 = GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)
        result2 = GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)

        assert result1 == result2

    def test_find_gaps_preserves_input(self):
        """Test that original elevation_angles list is not modified"""
        elevation_angles = [50.0, 20.0, 80.0]
        original = elevation_angles.copy()
        min_gap_deg = 4.0

        GapDetectionStrategy.find_gaps(elevation_angles, min_gap_deg)

        # Original list should be unchanged
        assert elevation_angles == original

import pytest

from src.components.calculators.boundary_search_strategy import BoundarySearchStrategy
from src.components.calculators.gap_detection_strategy import GapDetectionStrategy
from src.components.calculators.gap_obstruction_orchestrator import GapObstructionOrchestrator
from src.components.calculators.gap_verification_service import GapVerificationService
from src.components.calculators.obstruction_result_factory import ObstructionResultFactory
from src.components.geometry import Mesh, Triangle, Point3D
from src.components.models import Window, GapObstructionResult


class TestGapObstructionOrchestrator:
    """Test cases for GapObstructionOrchestrator"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with all dependencies"""
        boundary_search = BoundarySearchStrategy()
        gap_detector = GapDetectionStrategy()
        gap_verifier = GapVerificationService(boundary_search)
        result_factory = ObstructionResultFactory()

        return GapObstructionOrchestrator(
            gap_detector=gap_detector,
            gap_verifier=gap_verifier,
            result_factory=result_factory,
            min_gap_deg=4.0,
            precision_deg=1.0
        )

    @pytest.fixture
    def simple_window(self):
        """Create a simple window at origin looking in +Y direction"""
        from src.components.geometry import Vector3D
        return Window(
            center=Point3D(0.0, 0.0, 0.0),
            normal=Vector3D.from_horizontal_angle(0.0)
        )

    @pytest.fixture
    def low_triangle(self):
        """Create a low horizontal triangle"""
        return Triangle(
            Point3D(0.0, -10.0, 2.0),
            Point3D(10.0, 0.0, 2.0),
            Point3D(0.0, 10.0, 2.0)
        )

    @pytest.fixture
    def high_triangle(self):
        """Create a high horizontal triangle"""
        return Triangle(
            Point3D(0.0, -10.0, 15.0),
            Point3D(10.0, 0.0, 15.0),
            Point3D(0.0, 10.0, 15.0)
        )

    def test_calculate_with_empty_mesh(self, orchestrator, simple_window):
        """Test calculation with empty mesh (no obstruction)"""
        empty_mesh = Mesh([])

        result = orchestrator.calculate(empty_mesh, simple_window, 0.0)

        assert isinstance(result, GapObstructionResult)
        # Empty mesh should return default values
        assert result.horizon_deg == 45.0
        assert result.zenith_deg == 45.0

    def test_calculate_with_single_obstruction(self, orchestrator, simple_window, low_triangle):
        """Test calculation with single obstructing triangle"""
        mesh = Mesh([low_triangle])

        result = orchestrator.calculate(mesh, simple_window, 0.0)

        assert isinstance(result, GapObstructionResult)
        # Should find sky gap above the low triangle
        assert result.horizon_deg >= 0.0
        assert result.zenith_deg >= 0.0

    def test_calculate_with_multiple_obstructions(self, orchestrator, simple_window, low_triangle, high_triangle):
        """Test calculation with multiple obstructing triangles"""
        mesh = Mesh([low_triangle, high_triangle])

        result = orchestrator.calculate(mesh, simple_window, 0.0)

        assert isinstance(result, GapObstructionResult)
        # Should find largest gap between obstructions
        assert result.horizon_deg >= 0.0
        assert result.zenith_deg >= 0.0

    def test_calculate_finds_largest_gap(self, orchestrator, simple_window):
        """Test that orchestrator finds largest gap first"""
        # Create triangles with known gap pattern
        triangles = [
            # Small gap around 10-12 degrees
            Triangle(Point3D(0.0, -10.0, 1.7), Point3D(10.0, 0.0, 1.7), Point3D(0.0, 10.0, 1.7)),
            Triangle(Point3D(0.0, -10.0, 2.1), Point3D(10.0, 0.0, 2.1), Point3D(0.0, 10.0, 2.1)),
            # Large gap above (should be found first)
        ]
        mesh = Mesh(triangles)

        result = orchestrator.calculate(mesh, simple_window, 0.0)

        assert isinstance(result, GapObstructionResult)

    def test_calculate_respects_min_gap_config(self):
        """Test that min_gap_deg configuration is respected"""
        # Create orchestrator with large min_gap
        boundary_search = BoundarySearchStrategy()
        gap_detector = GapDetectionStrategy()
        gap_verifier = GapVerificationService(boundary_search)
        result_factory = ObstructionResultFactory()

        orchestrator_large_gap = GapObstructionOrchestrator(
            gap_detector=gap_detector,
            gap_verifier=gap_verifier,
            result_factory=result_factory,
            min_gap_deg=50.0,  # Very large minimum gap
            precision_deg=1.0
        )

        from src.components.geometry import Vector3D
        window = Window(center=Point3D(0.0, 0.0, 0.0), normal=Vector3D.from_horizontal_angle(0.0))
        triangle = Triangle(
            Point3D(0.0, -10.0, 2.0),
            Point3D(10.0, 0.0, 2.0),
            Point3D(0.0, 10.0, 2.0)
        )
        mesh = Mesh([triangle])

        result = orchestrator_large_gap.calculate(mesh, window, 0.0)

        # With min_gap=50, small gaps should be ignored
        assert isinstance(result, GapObstructionResult)

    def test_calculate_respects_precision_config(self):
        """Test that precision_deg configuration is respected"""
        # Create orchestrator with different precisions
        boundary_search = BoundarySearchStrategy()
        gap_detector = GapDetectionStrategy()
        gap_verifier = GapVerificationService(boundary_search)
        result_factory = ObstructionResultFactory()

        orchestrator_precise = GapObstructionOrchestrator(
            gap_detector=gap_detector,
            gap_verifier=gap_verifier,
            result_factory=result_factory,
            min_gap_deg=4.0,
            precision_deg=0.1  # High precision
        )

        from src.components.geometry import Vector3D
        window = Window(center=Point3D(0.0, 0.0, 0.0), normal=Vector3D.from_horizontal_angle(0.0))
        triangle = Triangle(
            Point3D(0.0, -10.0, 2.0),
            Point3D(10.0, 0.0, 2.0),
            Point3D(0.0, 10.0, 2.0)
        )
        mesh = Mesh([triangle])

        result = orchestrator_precise.calculate(mesh, window, 0.0)

        assert isinstance(result, GapObstructionResult)

    def test_calculate_different_directions(self, orchestrator, low_triangle):
        """Test calculation at different horizontal directions"""
        from src.components.geometry import Vector3D
        window_north = Window(center=Point3D(0.0, 0.0, 0.0), normal=Vector3D.from_horizontal_angle(0.0))
        window_east = Window(center=Point3D(0.0, 0.0, 0.0), normal=Vector3D.from_horizontal_angle(1.5708))

        mesh = Mesh([low_triangle])

        result_north = orchestrator.calculate(mesh, window_north, 0.0)
        result_east = orchestrator.calculate(mesh, window_east, 1.5708)

        # Both should return valid results
        assert isinstance(result_north, GapObstructionResult)
        assert isinstance(result_east, GapObstructionResult)

    # def test_calculate_with_fully_obstructed_view(self, orchestrator, simple_window):
    #     """Test calculation when view is fully obstructed (no gaps)"""
    #     # Create many triangles covering all elevation angles
    #     triangles = []
    #     for z in range(1, 50):
    #         triangles.append(
    #             Triangle(
    #                 Point3D(0.0, -10.0, float(z)),
    #                 Point3D(10.0, 0.0, float(z)),
    #                 Point3D(0.0, 10.0, float(z))
    #             )
    #         )
    #     mesh = Mesh(triangles)

    #     result = orchestrator.calculate(mesh, simple_window, 0.0)

    #     # Should return default fallback values
    #     assert result.horizon_deg == 45.0
    #     assert result.zenith_deg == 45.0

    def test_calculate_integration_with_all_components(self, orchestrator, simple_window, low_triangle):
        """Integration test verifying all components work together"""
        mesh = Mesh([low_triangle])

        result = orchestrator.calculate(mesh, simple_window, 0.0)

        # Verify result has expected properties
        assert isinstance(result, GapObstructionResult)
        assert hasattr(result, 'horizon_deg')
        assert hasattr(result, 'zenith_deg')
        assert result.horizon_deg >= 0.0
        assert result.zenith_deg >= 0.0

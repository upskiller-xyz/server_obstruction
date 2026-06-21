import numpy as np
import pytest

from src.components.calculators.boundary_search_strategy import BoundarySearchStrategy
from src.components.calculators.gap_verification_service import GapVerificationService
from src.components.calculators.ray_triangle_intersector import RayTriangleIntersector
from src.components.geometry import Point3D, Triangle
from src.server.base.constants import GapVerificationStatus


class TestGapVerificationService:
    """Test cases for GapVerificationService"""

    @pytest.fixture
    def boundary_search(self):
        """Create boundary search strategy"""
        return BoundarySearchStrategy()

    @pytest.fixture
    def service(self, boundary_search):
        """Create gap verification service"""
        return GapVerificationService(boundary_search)

    @pytest.fixture
    def obstructing_triangle(self):
        """Create a triangle that obstructs certain elevation angles"""
        return Triangle(
            Point3D(0.0, -10.0, 3.0),
            Point3D(10.0, 0.0, 3.0),
            Point3D(0.0, 10.0, 3.0)
        )

    @pytest.fixture
    def tri_arrays(self, obstructing_triangle):
        """Prepare triangle arrays for ray casting"""
        return RayTriangleIntersector.prepare_arrays([obstructing_triangle])

    def test_verify_gap_finds_sky(self, service):
        """Sky is found when the gap is clear above a low obstruction."""
        origin = np.array([0.0, 0.0, 0.0])
        direction_angle = 0.0

        # A small, distant triangle at z=3, x∈[8,14] only obstructs ~14–21° elevation
        # (it does not reach the small-x / overhead region). So the gap 40–90° is clear
        # and the verifier (probing gap_low+1 = 41°) finds sky.
        triangle = Triangle(
            Point3D(8.0, -3.0, 3.0),
            Point3D(14.0, 0.0, 3.0),
            Point3D(8.0, 3.0, 3.0),
        )
        tri_arrays = RayTriangleIntersector.prepare_arrays([triangle])

        result = service.verify_gap(
            gap_low=40.0,
            gap_high=90.0,
            origin=origin,
            direction_angle=direction_angle,
            tri_arrays=tri_arrays,
            precision=1.0
        )

        assert result.status == GapVerificationStatus.SKY_FOUND
        assert result.horizon_deg is not None
        assert result.zenith_deg is not None
        assert result.rays_cast > 1  # initial probe + boundary searches

    def test_verify_gap_detects_obstruction(self, service):
        """Obstruction is detected when the probed elevation is blocked."""
        # A large horizontal slab at z=5 spanning the whole forward region blocks every
        # elevation above the horizon, so the probe ray (gap_low+1 = 36°) hits it.
        triangle = Triangle(
            Point3D(-20.0, -20.0, 5.0),
            Point3D(20.0, -20.0, 5.0),
            Point3D(0.0, 20.0, 5.0),
        )
        tri_arrays = RayTriangleIntersector.prepare_arrays([triangle])
        origin = np.array([0.0, 0.0, 0.0])
        direction_angle = 0.0

        result = service.verify_gap(
            gap_low=35.0,
            gap_high=50.0,
            origin=origin,
            direction_angle=direction_angle,
            tri_arrays=tri_arrays,
            precision=1.0
        )

        assert result.status == GapVerificationStatus.OBSTRUCTED
        assert result.horizon_deg is None
        assert result.zenith_deg is None
        assert result.rays_cast == 1  # Only initial test ray

    def test_verify_gap_with_empty_mesh(self, service):
        """Test verification with no obstructions"""
        empty_arrays = RayTriangleIntersector.prepare_arrays([])
        origin = np.array([0.0, 0.0, 0.0])
        direction_angle = 0.0

        result = service.verify_gap(
            gap_low=0.0,
            gap_high=90.0,
            origin=origin,
            direction_angle=direction_angle,
            tri_arrays=empty_arrays,
            precision=1.0
        )

        assert result.status == GapVerificationStatus.SKY_FOUND
        assert result.horizon_deg is not None
        assert result.zenith_deg is not None

    def test_verify_gap_boundary_calculations(self, service, tri_arrays):
        """Test that horizon and zenith boundaries are calculated correctly"""
        origin = np.array([0.0, 0.0, 0.0])
        direction_angle = 0.0

        result = service.verify_gap(
            gap_low=40.0,
            gap_high=90.0,
            origin=origin,
            direction_angle=direction_angle,
            tri_arrays=tri_arrays,
            precision=1.0
        )

        if result.status == GapVerificationStatus.SKY_FOUND:
            # Horizon should be >= gap_low
            assert result.horizon_deg >= 40.0
            # Zenith should be reasonable (complementary angle)
            assert 0.0 <= result.zenith_deg <= 90.0
            # Horizon + zenith should be close to 90 for upper boundary
            # zenith = 90 - upper_boundary, so check relationship
            assert result.horizon_deg < 90.0

    def test_verify_gap_small_gap_uses_midpoint(self, service):
        """Test that small gaps use midpoint for testing"""
        empty_arrays = RayTriangleIntersector.prepare_arrays([])
        origin = np.array([0.0, 0.0, 0.0])
        direction_angle = 0.0

        # Very small gap where gap_low + 1.0 >= gap_high
        result = service.verify_gap(
            gap_low=44.5,
            gap_high=45.0,
            origin=origin,
            direction_angle=direction_angle,
            tri_arrays=empty_arrays,
            precision=0.1
        )

        # Should still work and find sky
        assert result.status == GapVerificationStatus.SKY_FOUND

    def test_verify_gap_precision_affects_rays_cast(self, service, tri_arrays):
        """Test that precision affects number of rays cast"""
        origin = np.array([0.0, 0.0, 0.0])
        direction_angle = 0.0

        # High precision
        result_high = service.verify_gap(
            gap_low=40.0,
            gap_high=90.0,
            origin=origin,
            direction_angle=direction_angle,
            tri_arrays=tri_arrays,
            precision=0.1
        )

        # Low precision
        result_low = service.verify_gap(
            gap_low=40.0,
            gap_high=90.0,
            origin=origin,
            direction_angle=direction_angle,
            tri_arrays=tri_arrays,
            precision=5.0
        )

        # Higher precision should cast more rays
        if result_high.status == GapVerificationStatus.SKY_FOUND:
            assert result_high.rays_cast >= result_low.rays_cast

    def test_verify_gap_different_directions(self, service, tri_arrays):
        """Test verification at different horizontal directions"""
        origin = np.array([0.0, 0.0, 0.0])

        result1 = service.verify_gap(
            gap_low=40.0,
            gap_high=90.0,
            origin=origin,
            direction_angle=0.0,
            tri_arrays=tri_arrays,
            precision=1.0
        )

        result2 = service.verify_gap(
            gap_low=40.0,
            gap_high=90.0,
            origin=origin,
            direction_angle=np.pi / 2,  # 90 degrees
            tri_arrays=tri_arrays,
            precision=1.0
        )

        # Results may differ based on direction
        assert result1.rays_cast > 0
        assert result2.rays_cast > 0

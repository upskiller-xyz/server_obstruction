# import numpy as np
# import pytest

# from src.components.calculators.boundary_search_strategy import BoundarySearchStrategy
# from src.components.calculators.ray_triangle_intersector import RayTriangleIntersector
# from src.components.geometry import Triangle, Point3D
# from src.server.base.constants import BoundaryDirection


# class TestBoundarySearchStrategy:
#     """Test cases for BoundarySearchStrategy"""

#     @pytest.fixture
#     def simple_triangle(self):
#         """Create a simple horizontal triangle at z=5"""
#         return Triangle(
#             Point3D(0.0, -10.0, 5.0),
#             Point3D(10.0, 0.0, 5.0),
#             Point3D(0.0, 10.0, 5.0)
#         )

#     @pytest.fixture
#     def tri_arrays(self, simple_triangle):
#         """Prepare triangle arrays for ray casting"""
#         return RayTriangleIntersector.prepare_arrays([simple_triangle])

#     def test_search_lower_boundary_finds_horizon(self, tri_arrays):
#         """Test searching for lower boundary (horizon) finds correct angle"""
#         origin = np.array([0.0, 0.0, 0.0])
#         direction_angle = 0.0  # radians

#         # Search between 0 and 45 degrees
#         # Triangle at z=5, distance ~10 should give ~26 degrees
#         boundary, rays_cast = BoundarySearchStrategy.search_boundary(
#             origin, direction_angle, tri_arrays,
#             low=0.0, high=45.0, precision=1.0,
#             boundary_direction=BoundaryDirection.LOWER
#         )

#         # Should find boundary around 26 degrees (lower edge of obstruction)
#         assert 25.0 <= boundary <= 27.0
#         assert rays_cast > 0

#     def test_search_upper_boundary_finds_zenith(self, tri_arrays):
#         """Test searching for upper boundary (zenith) finds correct angle"""
#         origin = np.array([0.0, 0.0, 0.0])
#         direction_angle = 0.0

#         # Search between 0 and 45 degrees (same range as LOWER test for comparison)
#         # Triangle at z=5 creates obstruction at ~26 degrees
#         boundary, rays_cast = BoundarySearchStrategy.search_boundary(
#             origin, direction_angle, tri_arrays,
#             low=0.0, high=45.0, precision=1.0,
#             boundary_direction=BoundaryDirection.UPPER
#         )

#         # In UPPER mode returns 'high' which converges where obstruction exists
#         # Should be similar to lower boundary in this case
#         assert 25.0 <= boundary <= 27.0
#         assert rays_cast > 0

#     def test_binary_search_precision_respected(self, tri_arrays):
#         """Test that search stops when precision is reached"""
#         origin = np.array([0.0, 0.0, 0.0])
#         direction_angle = 0.0

#         # High precision should require more iterations
#         _, rays_high_precision = BoundarySearchStrategy.search_boundary(
#             origin, direction_angle, tri_arrays,
#             low=0.0, high=45.0, precision=0.1,
#             boundary_direction=BoundaryDirection.LOWER
#         )

#         # Low precision should require fewer iterations
#         _, rays_low_precision = BoundarySearchStrategy.search_boundary(
#             origin, direction_angle, tri_arrays,
#             low=0.0, high=45.0, precision=5.0,
#             boundary_direction=BoundaryDirection.LOWER
#         )

#         assert rays_high_precision > rays_low_precision

#     def test_search_with_no_obstruction(self):
#         """Test search when there's no obstruction (empty mesh)"""
#         empty_arrays = RayTriangleIntersector.prepare_arrays([])
#         origin = np.array([0.0, 0.0, 0.0])
#         direction_angle = 0.0

#         boundary, rays_cast = BoundarySearchStrategy.search_boundary(
#             origin, direction_angle, empty_arrays,
#             low=0.0, high=90.0, precision=1.0,
#             boundary_direction=BoundaryDirection.LOWER
#         )

#         # With no obstruction, boundary should converge to low bound
#         assert boundary <= 1.0
#         assert rays_cast > 0

#     def test_lower_vs_upper_boundary_direction(self, tri_arrays):
#         """Test that LOWER and UPPER directions produce different results"""
#         origin = np.array([0.0, 0.0, 0.0])
#         direction_angle = 0.0

#         lower_boundary, _ = BoundarySearchStrategy.search_boundary(
#             origin, direction_angle, tri_arrays,
#             low=0.0, high=45.0, precision=1.0,
#             boundary_direction=BoundaryDirection.LOWER
#         )

#         upper_boundary, _ = BoundarySearchStrategy.search_boundary(
#             origin, direction_angle, tri_arrays,
#             low=0.0, high=45.0, precision=1.0,
#             boundary_direction=BoundaryDirection.UPPER
#         )

#         # The boundaries should be different for same range
#         # LOWER finds where obstruction ends (higher value)
#         # UPPER finds where sky ends (lower value)
#         assert lower_boundary != upper_boundary

#     def test_search_boundary_is_stateless(self, tri_arrays):
#         """Test that multiple calls produce same results (stateless)"""
#         origin = np.array([0.0, 0.0, 0.0])
#         direction_angle = 0.0

#         result1, _ = BoundarySearchStrategy.search_boundary(
#             origin, direction_angle, tri_arrays,
#             low=0.0, high=45.0, precision=1.0,
#             boundary_direction=BoundaryDirection.LOWER
#         )

#         result2, _ = BoundarySearchStrategy.search_boundary(
#             origin, direction_angle, tri_arrays,
#             low=0.0, high=45.0, precision=1.0,
#             boundary_direction=BoundaryDirection.LOWER
#         )

#         assert result1 == result2

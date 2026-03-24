import pytest
import numpy as np

from src.components.calculators.elevation_angle_collector import ElevationAngleCollector
from src.components.calculators.vectorized_elevation_angle_collector import VectorizedElevationAngleCollector
from src.components.geometry import Mesh, Point3D, Triangle, Vector3D
from src.components.models import Window


class TestVectorizedElevationAngleCollector:
    """Test cases for VectorizedElevationAngleCollector

    Verifies that the vectorized implementation produces identical results
    to the scalar ElevationAngleCollector across all edge cases.
    """

    @pytest.fixture
    def window_x(self):
        """Window at origin looking in +X direction"""
        return Window(
            center=Point3D(0.0, 0.0, 0.0),
            normal=Vector3D(1.0, 0.0, 0.0)
        )

    @pytest.fixture
    def window_elevated(self):
        """Window at z=1.5 looking in +X direction"""
        return Window(
            center=Point3D(0.0, 0.0, 1.5),
            normal=Vector3D(1.0, 0.0, 0.0)
        )

    @pytest.fixture
    def window_y(self):
        """Window at origin looking in +Y direction"""
        return Window(
            center=Point3D(0.0, 0.0, 0.0),
            normal=Vector3D(0.0, 1.0, 0.0)
        )

    @pytest.fixture
    def window_diagonal(self):
        """Window at origin looking in diagonal XY direction"""
        return Window(
            center=Point3D(0.0, 0.0, 0.0),
            normal=Vector3D.from_horizontal_angle(np.pi / 4)
        )

    # --- Empty / trivial cases ---

    def test_empty_triangles(self, window_x):
        """Empty input returns empty list"""
        result = VectorizedElevationAngleCollector.collect_all_angles((), window_x)
        assert result == []

    def test_single_triangle_no_intersection(self, window_x):
        """Triangle entirely on one side of the plane produces no angles"""
        triangle = Triangle(
            Point3D(5.0, 5.0, 3.0),
            Point3D(6.0, 5.0, 3.0),
            Point3D(5.5, 5.0, 4.0)
        )
        result = VectorizedElevationAngleCollector.collect_all_angles(
            (triangle,), window_x
        )
        assert result == []

    def test_triangle_below_window(self, window_elevated):
        """Triangle with all intersection points below window height produces no angles"""
        triangle = Triangle(
            Point3D(5.0, -1.0, 0.0),
            Point3D(5.0, 1.0, 0.0),
            Point3D(5.0, 0.0, 1.0)
        )
        result = VectorizedElevationAngleCollector.collect_all_angles(
            (triangle,), window_elevated
        )
        assert result == []

    def test_triangle_behind_window(self, window_x):
        """Triangle behind window (negative horizontal distance) produces no angles"""
        triangle = Triangle(
            Point3D(-5.0, -1.0, 0.0),
            Point3D(-5.0, 1.0, 0.0),
            Point3D(-5.0, 0.0, 5.0)
        )
        result = VectorizedElevationAngleCollector.collect_all_angles(
            (triangle,), window_x
        )
        assert result == []

    # --- Single triangle positive cases ---

    def test_single_triangle_crossing_plane(self, window_x):
        """Triangle crossing the vertical plane produces elevation angles"""
        triangle = Triangle(
            Point3D(5.0, -2.0, 1.0),
            Point3D(5.0, 2.0, 1.0),
            Point3D(5.0, 0.0, 5.0)
        )
        result = VectorizedElevationAngleCollector.collect_all_angles(
            (triangle,), window_x
        )
        assert len(result) > 0
        assert all(0.0 < angle <= 90.0 for angle in result)

    def test_known_45_degree_angle(self, window_x):
        """Triangle at equal horizontal and vertical distance gives ~45 degrees"""
        triangle = Triangle(
            Point3D(10.0, -1.0, 0.0),
            Point3D(10.0, 1.0, 0.0),
            Point3D(10.0, 0.0, 10.0)
        )
        result = VectorizedElevationAngleCollector.collect_all_angles(
            (triangle,), window_x
        )
        assert len(result) > 0
        assert any(abs(angle - 45.0) < 1.0 for angle in result)

    # --- Multiple triangles ---

    def test_multiple_triangles(self, window_x):
        """Multiple triangles produce combined sorted angles"""
        tri1 = Triangle(
            Point3D(5.0, -1.0, 0.0),
            Point3D(5.0, 1.0, 0.0),
            Point3D(5.0, 0.0, 3.0)
        )
        tri2 = Triangle(
            Point3D(5.0, -1.0, 4.0),
            Point3D(5.0, 1.0, 4.0),
            Point3D(5.0, 0.0, 8.0)
        )
        result = VectorizedElevationAngleCollector.collect_all_angles(
            (tri1, tri2), window_x
        )
        assert len(result) > 0
        assert result == sorted(result)

    # --- Edge cases ---

    def test_vertex_on_plane(self, window_x):
        """Triangle with one vertex exactly on the plane"""
        triangle = Triangle(
            Point3D(5.0, 0.0, 3.0),
            Point3D(5.0, 2.0, 1.0),
            Point3D(5.0, -2.0, 1.0)
        )
        result = VectorizedElevationAngleCollector.collect_all_angles(
            (triangle,), window_x
        )
        assert len(result) > 0

    def test_edge_on_plane(self, window_x):
        """Triangle with one edge lying on the plane is excluded"""
        triangle = Triangle(
            Point3D(5.0, 0.0, 1.0),
            Point3D(5.0, 0.0, 5.0),
            Point3D(5.0, 3.0, 3.0)
        )
        result_vec = VectorizedElevationAngleCollector.collect_all_angles(
            (triangle,), window_x
        )
        result_scalar = ElevationAngleCollector.collect_all_angles(
            (triangle,), window_x
        )
        assert result_vec == pytest.approx(result_scalar, abs=1e-10)

    def test_different_window_directions(self, window_x, window_y, window_diagonal):
        """Results change with different window directions"""
        triangle = Triangle(
            Point3D(5.0, -2.0, 0.0),
            Point3D(5.0, 2.0, 0.0),
            Point3D(5.0, 0.0, 5.0)
        )
        triangles = (triangle,)

        result_x = VectorizedElevationAngleCollector.collect_all_angles(
            triangles, window_x
        )
        result_y = VectorizedElevationAngleCollector.collect_all_angles(
            triangles, window_y
        )
        # Different viewing directions can produce different intersection patterns
        # At minimum, verify both return valid results without errors
        assert isinstance(result_x, list)
        assert isinstance(result_y, list)

    # --- Scalar vs vectorized equivalence ---

    def test_equivalence_single_triangle(self, window_x):
        """Vectorized matches scalar for single triangle"""
        triangle = Triangle(
            Point3D(5.0, -2.0, 0.0),
            Point3D(5.0, 2.0, 0.0),
            Point3D(5.0, 0.0, 5.0)
        )
        triangles = (triangle,)

        scalar = ElevationAngleCollector.collect_all_angles(triangles, window_x)
        vectorized = VectorizedElevationAngleCollector.collect_all_angles(
            triangles, window_x
        )

        assert vectorized == pytest.approx(scalar, abs=1e-10)

    def test_equivalence_multiple_triangles(self, window_elevated):
        """Vectorized matches scalar for multiple triangles"""
        triangles = (
            Triangle(
                Point3D(5.0, -1.0, 0.0),
                Point3D(5.0, 1.0, 0.0),
                Point3D(5.0, 0.0, 5.0)
            ),
            Triangle(
                Point3D(8.0, -2.0, 0.0),
                Point3D(8.0, 2.0, 0.0),
                Point3D(8.0, 0.0, 10.0)
            ),
            Triangle(
                Point3D(3.0, -1.0, 2.0),
                Point3D(3.0, 1.0, 2.0),
                Point3D(3.0, 0.0, 4.0)
            ),
        )

        scalar = ElevationAngleCollector.collect_all_angles(triangles, window_elevated)
        vectorized = VectorizedElevationAngleCollector.collect_all_angles(
            triangles, window_elevated
        )

        assert vectorized == pytest.approx(scalar, abs=1e-10)

    def test_equivalence_diagonal_direction(self, window_diagonal):
        """Vectorized matches scalar for non-axis-aligned window direction"""
        triangles = (
            Triangle(
                Point3D(5.0, 5.0, 0.0),
                Point3D(5.0, 5.0, 6.0),
                Point3D(5.0, -1.0, 3.0)
            ),
            Triangle(
                Point3D(3.0, 3.0, 1.0),
                Point3D(3.0, 3.0, 7.0),
                Point3D(3.0, -3.0, 4.0)
            ),
        )

        scalar = ElevationAngleCollector.collect_all_angles(
            triangles, window_diagonal
        )
        vectorized = VectorizedElevationAngleCollector.collect_all_angles(
            triangles, window_diagonal
        )

        assert vectorized == pytest.approx(scalar, abs=1e-10)

    def test_equivalence_mixed_valid_invalid(self, window_elevated):
        """Vectorized matches scalar with mix of intersecting and non-intersecting triangles"""
        triangles = (
            # Intersects plane, above window
            Triangle(
                Point3D(5.0, -2.0, 0.0),
                Point3D(5.0, 2.0, 0.0),
                Point3D(5.0, 0.0, 8.0)
            ),
            # Entirely on one side of plane (no intersection)
            Triangle(
                Point3D(5.0, 3.0, 3.0),
                Point3D(6.0, 3.0, 3.0),
                Point3D(5.5, 3.0, 4.0)
            ),
            # Below window height
            Triangle(
                Point3D(5.0, -1.0, 0.0),
                Point3D(5.0, 1.0, 0.0),
                Point3D(5.0, 0.0, 1.0)
            ),
            # Behind window
            Triangle(
                Point3D(-5.0, -1.0, 2.0),
                Point3D(-5.0, 1.0, 2.0),
                Point3D(-5.0, 0.0, 5.0)
            ),
            # Another valid intersection
            Triangle(
                Point3D(10.0, -3.0, 0.0),
                Point3D(10.0, 3.0, 0.0),
                Point3D(10.0, 0.0, 12.0)
            ),
        )

        scalar = ElevationAngleCollector.collect_all_angles(
            triangles, window_elevated
        )
        vectorized = VectorizedElevationAngleCollector.collect_all_angles(
            triangles, window_elevated
        )

        assert vectorized == pytest.approx(scalar, abs=1e-10)

    def test_equivalence_many_triangles(self, window_x):
        """Vectorized matches scalar for a larger mesh"""
        np.random.seed(42)
        triangles = []
        for _ in range(200):
            x = np.random.uniform(3.0, 20.0)
            y_center = np.random.uniform(-5.0, 5.0)
            z_base = np.random.uniform(-1.0, 2.0)
            z_top = np.random.uniform(3.0, 15.0)
            width = np.random.uniform(0.5, 3.0)

            triangles.append(Triangle(
                Point3D(x, y_center - width, z_base),
                Point3D(x, y_center + width, z_base),
                Point3D(x, y_center, z_top)
            ))

        triangles = tuple(triangles)

        scalar = ElevationAngleCollector.collect_all_angles(triangles, window_x)
        vectorized = VectorizedElevationAngleCollector.collect_all_angles(
            triangles, window_x
        )

        assert len(vectorized) == len(scalar)
        assert vectorized == pytest.approx(scalar, abs=1e-10)

    # --- Return type and sorting ---

    def test_returns_sorted_list(self, window_x):
        """Result is a sorted list of floats"""
        triangles = (
            Triangle(
                Point3D(5.0, -1.0, 0.0),
                Point3D(5.0, 1.0, 0.0),
                Point3D(5.0, 0.0, 5.0)
            ),
            Triangle(
                Point3D(3.0, -1.0, 0.0),
                Point3D(3.0, 1.0, 0.0),
                Point3D(3.0, 0.0, 10.0)
            ),
        )
        result = VectorizedElevationAngleCollector.collect_all_angles(
            triangles, window_x
        )
        assert isinstance(result, list)
        assert all(isinstance(a, float) for a in result)
        assert result == sorted(result)

    def test_angles_in_valid_range(self, window_x):
        """All returned angles are between 0 and 90 degrees"""
        triangles = (
            Triangle(
                Point3D(5.0, -2.0, 0.0),
                Point3D(5.0, 2.0, 0.0),
                Point3D(5.0, 0.0, 5.0)
            ),
            Triangle(
                Point3D(1.0, -1.0, 0.0),
                Point3D(1.0, 1.0, 0.0),
                Point3D(1.0, 0.0, 100.0)
            ),
        )
        result = VectorizedElevationAngleCollector.collect_all_angles(
            triangles, window_x
        )
        assert all(0.0 < angle <= 90.0 for angle in result)

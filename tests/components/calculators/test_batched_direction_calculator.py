"""Tests for the batched all-directions calculator.

The batched path must produce results identical (within binary-search precision)
to the async per-direction path it replaces, and honour the fallback settings.
"""

import asyncio
import os

import numpy as np
import pytest

from src.components.calculators.batched_direction_calculator import (
    BatchedDirectionCalculator,
    BatchedDirectionSettings,
)
from src.components.geometry import Mesh, Point3D, Vector3D
from src.components.models import ObstructionRequest, Window
from src.server.services.obstruction_service import ObstructionService


def _skyline_mesh(count: int = 40, seed: int = 0) -> Mesh:
    """A ring of vertical quads around the origin to exercise gaps and sky."""
    rng = np.random.default_rng(seed)
    vertices = []
    for _ in range(count):
        cx = rng.uniform(-60.0, 60.0)
        cy = rng.uniform(5.0, 60.0)
        h = rng.uniform(3.0, 25.0)
        w = rng.uniform(1.0, 6.0)
        vertices.extend([
            [cx - w, cy, 0.0], [cx + w, cy, 0.0], [cx + w, cy, h],
            [cx - w, cy, 0.0], [cx + w, cy, h], [cx - w, cy, h],
        ])
    return Mesh.from_vertices(vertices)


def _window() -> Window:
    return Window(center=Point3D(0.0, 0.0, 1.5), normal=Vector3D(0.0, 1.0, 0.0))


def _run(request: ObstructionRequest, num_directions: int, batched: bool):
    os.environ["OBSTRUCTION_BATCHED"] = "1" if batched else "0"
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            ObstructionService().calculate_all_directions_async(
                request, num_directions=num_directions
            )
        )
    finally:
        loop.close()
        os.environ.pop("OBSTRUCTION_BATCHED", None)
    return result["results"]


class TestBatchedDirectionCalculator:
    """Equivalence and behaviour of the batched all-directions path."""

    def test_matches_async_path_within_precision(self):
        """Batched horizon/zenith equal the async path within 1° search precision."""
        request = ObstructionRequest(window=_window(), mesh=_skyline_mesh())
        num_directions = 64

        batched = _run(request, num_directions, batched=True)
        async_results = _run(request, num_directions, batched=False)

        assert len(batched) == len(async_results) == num_directions
        for b, a in zip(batched, async_results):
            assert b["direction_angle"] == pytest.approx(a["direction_angle"])
            assert b["horizon"]["obstruction_angle_degrees"] == pytest.approx(
                a["horizon"]["obstruction_angle_degrees"], abs=1.0
            )
            assert b["zenith"]["obstruction_angle_degrees"] == pytest.approx(
                a["zenith"]["obstruction_angle_degrees"], abs=1.0
            )

    def test_empty_mesh_is_unobstructed(self):
        """No triangles -> every direction falls back to the obstructed default."""
        empty = Mesh.from_array(np.empty((0, 3, 3)))
        results = BatchedDirectionCalculator.calculate(
            _pack(empty), _window(), np.linspace(0.0, np.pi, 8)
        )
        assert len(results) == 8

    def test_chunking_is_invariant(self):
        """Result is independent of how directions are chunked."""
        request = ObstructionRequest(window=_window(), mesh=_skyline_mesh())
        from src.server.services.mesh_filter_service import MeshFilterService
        from src.components.calculators.ray_triangle_intersector import (
            RayTriangleIntersector,
        )

        mesh = MeshFilterService.apply_coarse_filter(request.mesh, request.window)
        mesh = MeshFilterService.apply_height_filter(mesh, request.window)
        tri_arrays = RayTriangleIntersector.from_array(mesh.vertices_array)
        azimuths = np.linspace(0.0, np.pi, 20)

        one = BatchedDirectionCalculator.calculate(
            tri_arrays, request.window, azimuths, chunk_size=1
        )
        many = BatchedDirectionCalculator.calculate(
            tri_arrays, request.window, azimuths, chunk_size=7
        )
        for a, b in zip(one, many):
            assert a["horizon"]["obstruction_angle_degrees"] == pytest.approx(
                b["horizon"]["obstruction_angle_degrees"]
            )
            assert a["zenith"]["obstruction_angle_degrees"] == pytest.approx(
                b["zenith"]["obstruction_angle_degrees"]
            )

    def test_within_budget_threshold(self):
        """Budget check routes oversized workloads to the fallback path."""
        os.environ["OBSTRUCTION_BATCH_MAX_CELLS"] = "100"
        try:
            assert not BatchedDirectionSettings.within_budget(50, 64)
            assert BatchedDirectionSettings.within_budget(1, 64)
        finally:
            os.environ.pop("OBSTRUCTION_BATCH_MAX_CELLS", None)


def _pack(mesh: Mesh):
    from src.components.calculators.ray_triangle_intersector import RayTriangleIntersector
    return RayTriangleIntersector.from_array(mesh.vertices_array)

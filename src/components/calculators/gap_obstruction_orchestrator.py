"""
Gap obstruction orchestrator

Orchestrates gap-based obstruction calculation pipeline.
"""

import logging
import time

from src.components.calculators.gap_detection_strategy import GapDetectionStrategy
from src.components.calculators.gap_verification_service import GapVerificationService
from src.components.calculators.intersection_calculator import IntersectionCalculator
from src.components.calculators.obstruction_result_factory import ObstructionResultFactory
from src.components.calculators.ray_triangle_intersector import RayTriangleIntersector
from src.components.geometry import Mesh
from src.components.models import Window, GapObstructionResult
from src.components.models.performance_metrics import PerformanceMetrics
from src.server.base.constants import GapVerificationStatus, ObstructionStatus


class GapObstructionOrchestrator:
    """Orchestrates gap-based obstruction calculation."""

    def __init__(
        self,
        gap_detector: GapDetectionStrategy,
        gap_verifier: GapVerificationService,
        result_factory: ObstructionResultFactory,
        min_gap_deg: float,
        precision_deg: float
    ):
        self._gap_detector = gap_detector
        self._gap_verifier = gap_verifier
        self._result_factory = result_factory
        self._min_gap_deg = min_gap_deg
        self._precision_deg = precision_deg

    def calculate(
        self,
        mesh: Mesh,
        window: Window,
        direction_angle: float
    ) -> GapObstructionResult:
        """
        Calculate obstruction using gap detection for a single direction.

        Args:
            mesh: Combined mesh (all triangles, no horizon/zenith split)
            window: Window with center and normal set to this direction
            direction_angle: Horizontal direction angle in radians

        Returns:
            GapObstructionResult with gap info and derived horizon/zenith
        """
        start = time.time()
        rays_cast = 0

        # Step 1: Collect elevation angles from plane intersections
        elevation_angles = IntersectionCalculator.collect_all_elevation_angles(
            mesh.triangles, window
        )

        # Step 2: Find gaps
        gaps = self._gap_detector.find_gaps(
            elevation_angles,
            self._min_gap_deg
        )

        if not gaps or not mesh.triangles:
            # No gaps — fully obstructed
            metrics = PerformanceMetrics(
                elapsed_ms=(time.time() - start) * 1000,
                rays_cast=0,
                gaps_tested=0,
                intersection_points=len(elevation_angles)
            )
            metrics.log_summary(ObstructionStatus.FULLY_OBSTRUCTED)
            return self._result_factory.create_empty()

        # Prepare for ray casting
        tri_arrays = RayTriangleIntersector.prepare_arrays(mesh.triangles)
        origin = window.center.to_array()

        # Step 3: Test gaps largest-first
        for gap_index, (gap_low, gap_high, _) in enumerate(gaps):
            verification = self._gap_verifier.verify_gap(
                gap_low, gap_high, origin, direction_angle,
                tri_arrays, self._precision_deg
            )
            rays_cast += verification.rays_cast

            if verification.status == GapVerificationStatus.SKY_FOUND:
                metrics = PerformanceMetrics(
                    elapsed_ms=(time.time() - start) * 1000,
                    rays_cast=rays_cast,
                    gaps_tested=gap_index + 1,
                    intersection_points=len(elevation_angles)
                )
                metrics.log_summary(ObstructionStatus.PARTIALLY_OBSTRUCTED)

                return self._result_factory.create_from_gap(
                    verification.horizon_deg,
                    verification.zenith_deg
                )

        # All gaps obstructed
        metrics = PerformanceMetrics(
            elapsed_ms=(time.time() - start) * 1000,
            rays_cast=rays_cast,
            gaps_tested=len(gaps),
            intersection_points=len(elevation_angles)
        )
        metrics.log_summary(ObstructionStatus.FULLY_OBSTRUCTED)

        return self._result_factory.create_empty()

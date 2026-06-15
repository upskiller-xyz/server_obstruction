"""
Gap-based unified obstruction calculator

Replaces the separate horizon/zenith calculation with a single pass:
1. Intersect ALL geometry with the vertical sweep plane
2. Collect elevation angles of all intersection points
3. Find the largest gap between consecutive angles
4. Verify gap with a single ray, then binary search boundaries to 1 degree

Output: gap_midpoint (center of sky opening) and gap_amplitude (width).
Derived horizon/zenith angles for backward compatibility.
"""

from dataclasses import dataclass
from typing import Optional

from src.components.calculators.boundary_search_strategy import BoundarySearchStrategy
from src.components.calculators.gap_detection_strategy import GapDetectionStrategy
from src.components.calculators.gap_obstruction_orchestrator import (
    GapObstructionOrchestrator,
)
from src.components.calculators.gap_verification_service import GapVerificationService
from src.components.calculators.obstruction_result_factory import (
    ObstructionResultFactory,
)
from src.components.calculators.ray_triangle_intersector import TriangleArrays
from src.components.geometry import Mesh
from src.components.models import GapObstructionResult, Window


@dataclass(frozen=True)
class GapObstructionConfig:
    """Configuration for gap-based obstruction calculation"""
    MIN_GAP_DEG: float = 4.0
    BINARY_SEARCH_PRECISION_DEG: float = 1.0


class GapObstructionCalculator:
    """
    Unified obstruction calculator using gap detection.

    For each direction, finds all plane-mesh intersection points,
    sorts by elevation angle, identifies the largest angular gap
    between consecutive points, and verifies it with ray casting.

    The gap boundaries directly yield horizon and zenith angles
    without needing separate mesh splits or calculation passes.
    """

    @classmethod
    def calculate(
        cls,
        mesh: Optional[Mesh],
        window: Window,
        direction_angle: float,
        config: GapObstructionConfig = GapObstructionConfig(),
        tri_arrays: Optional[TriangleArrays] = None
    ) -> GapObstructionResult:
        """
        Calculate obstruction using gap detection for a single direction.

        Args:
            mesh: Combined mesh (all triangles, no horizon/zenith split)
            window: Window with center and normal set to this direction
            direction_angle: Horizontal direction angle in radians
            config: Gap detection configuration

        Returns:
            GapObstructionResult with gap info and derived horizon/zenith
        """
        if mesh is None and tri_arrays is None:
            raise ValueError(
                "calculate requires either 'mesh' or pre-packed 'tri_arrays'"
            )

        # Initialize components
        boundary_search = BoundarySearchStrategy()
        gap_detector = GapDetectionStrategy()
        gap_verifier = GapVerificationService(boundary_search)
        result_factory = ObstructionResultFactory()

        # Create orchestrator
        orchestrator = GapObstructionOrchestrator(
            gap_detector=gap_detector,
            gap_verifier=gap_verifier,
            result_factory=result_factory,
            min_gap_deg=config.MIN_GAP_DEG,
            precision_deg=config.BINARY_SEARCH_PRECISION_DEG
        )

        # Delegate to orchestrator (pre-packed tri_arrays reused across directions)
        return orchestrator.calculate(mesh, window, direction_angle, tri_arrays=tri_arrays)

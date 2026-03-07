"""Parallel obstruction service for multi-direction calculations"""

import asyncio
import math
import time
from typing import Any, Dict, List, Optional

import aiohttp
import logging
from src.components.calculators.direction_calculator import DirectionCalculator
from src.components.models.obstruction_request import ObstructionRequest
from src.server.base.constants import ResponseField
from src.server.services.http_header_builder import HTTPHeaderBuilder
from src.server.services.request_builder import ParallelRequestBuilder
from src.server.services.result_assembler import ParallelResultAssembler


class ParallelObstructionService:
    """
    Service for calculating obstructions in parallel across multiple directions

    Single Responsibility:
    - Coordinates parallel microservice calls
    - Delegates header building to HTTPHeaderBuilder
    - Delegates payload building to ParallelRequestBuilder
    - Delegates result assembly to ParallelResultAssembler

    Uses Strategy Pattern:
    - Async HTTP requests via aiohttp
    - Parallel execution via asyncio.gather

    Follows OOP principles:
    - Encapsulates parallel request logic
    - Dependency Injection: microservice URL
    """

    def __init__(
        self,
        microservice_url: str,
        auth_token: Optional[str] = None
    ):
        """
        Initialize parallel obstruction service

        Args:
            microservice_url: Base URL of obstruction microservice
            auth_token: Optional bearer token for GCP authentication
        """
        self._microservice_url = microservice_url
        self._auth_token = auth_token
        self._request_builder = ParallelRequestBuilder()

    async def calculate_single_direction(
        self,
        session: aiohttp.ClientSession,
        x: float,
        y: float,
        z: float,
        direction_angle: float,
        mesh_vertices: List[List[float]],
        direction_index: int
    ) -> Dict[str, Any]:
        """
        Calculate obstruction for a single direction (async)

        Args:
            session: Shared aiohttp session for connection reuse
            x, y, z: Window position
            direction_angle: Absolute direction in radians
            mesh_vertices: Mesh geometry
            direction_index: Index of this direction (for logging)

        Returns:
            Dictionary with horizon/zenith angles and highest points
        """
        # Build payload using Builder Pattern
        payload = self._request_builder.build_payload(
            x=x, y=y, z=z,
            direction_angle=direction_angle,
            mesh_vertices=mesh_vertices
        )

        # Build headers using HTTPHeaderBuilder
        headers = HTTPHeaderBuilder.build_headers(auth_token=self._auth_token)

        try:
            start_time = time.time()

            # Make async HTTP request
            async with session.post(
                self._microservice_url,
                json=payload,
                headers=headers
            ) as response:
                response.raise_for_status()
                result = await response.json()

            elapsed_ms = (time.time() - start_time) * 1000
            logging.info(
                f"[PARALLEL] Direction {direction_index} "
                f"({math.degrees(direction_angle):.1f}°) completed in {elapsed_ms:.2f}ms"
            )

            return {
                ResponseField.DIRECTION_ANGLE.value: direction_angle,
                ResponseField.DIRECTION_ANGLE_DEGREES.value: math.degrees(direction_angle),
                ResponseField.HORIZON.value: result.get("data", {}).get("horizon"),
                ResponseField.ZENITH.value: result.get("data", {}).get("zenith")
            }

        except aiohttp.ClientError as e:
            logging.error(
                f"[PARALLEL] Direction {direction_index} failed: HTTP error {str(e)}"
            )
            return {
                ResponseField.DIRECTION_ANGLE.value: direction_angle,
                ResponseField.DIRECTION_ANGLE_DEGREES.value: math.degrees(direction_angle),
                "error": str(e)
            }
        except Exception as e:
            logging.error(
                f"[PARALLEL] Direction {direction_index} failed: {str(e)}"
            )
            return {
                ResponseField.DIRECTION_ANGLE.value: direction_angle,
                ResponseField.DIRECTION_ANGLE_DEGREES.value: math.degrees(direction_angle),
                "error": str(e)
            }

    async def calculate_all_directions_parallel(
        self,
        request: ObstructionRequest,
        num_directions: int = 64,
        start_angle_degrees: float = 17.5,
        end_angle_degrees: float = 162.5
    ) -> Dict[str, Any]:
        """
        Calculate obstruction angles for 64 directions in parallel

        Uses asyncio.gather to execute all HTTP requests simultaneously,
        reusing a single aiohttp session for connection pooling.

        Args:
            request: Obstruction request with window and mesh
            num_directions: Number of directions (default 64)
            start_angle_degrees: Start angle (default 17.5°)
            end_angle_degrees: End angle (default 162.5°)

        Returns:
            Dictionary with results array and metadata
        """
        start_time = time.time()

        # Extract base direction from window normal
        normal_arr = request.window.normal.to_array()
        base_direction_angle = math.atan2(normal_arr[1], normal_arr[0])

        # Calculate all direction angles using DirectionCalculator
        direction_angles = DirectionCalculator.calculate_direction_angles(
            base_direction_angle, num_directions, start_angle_degrees, end_angle_degrees
        )

        if request.mesh is None:
            raise ValueError("ObstructionRequest.mesh is required for parallel calculation but was None.")

        # Extract mesh vertices for payload
        mesh_vertices = [
            [v.x, v.y, v.z]
            for triangle in request.mesh.triangles
            for v in [triangle.v1, triangle.v2, triangle.v3]
        ]

        logging.info(
            f"[PARALLEL] Starting parallel calculation for {len(direction_angles)} directions"
        )

        # Create single aiohttp session with connection pooling
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=100)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Create tasks for all directions (Task creation pattern)
            tasks = [
                self.calculate_single_direction(
                    session,
                    request.window.center.x,
                    request.window.center.y,
                    request.window.center.z,
                    direction_angle,
                    mesh_vertices,
                    i
                )
                for i, direction_angle in enumerate(direction_angles)
            ]

            # Execute all tasks in parallel (Parallel execution pattern)
            results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time
        logging.info(
            f"[PARALLEL] Completed {len(direction_angles)} directions in {total_time:.2f}s"
        )

        # Delegate result assembly to ResultAssembler
        return ParallelResultAssembler.assemble_results(
            results=results,
            total_time=total_time
        )


class ParallelObstructionServiceFactory:
    """
    Factory Pattern for creating ParallelObstructionService instances

    Centralizes service configuration
    """

    @staticmethod
    def create_service(
        microservice_url: str,
        auth_token: Optional[str] = None
    ) -> ParallelObstructionService:
        """
        Create parallel obstruction service

        Args:
            microservice_url: Base URL of microservice
            auth_token: Optional authentication token

        Returns:
            Configured ParallelObstructionService
        """
        return ParallelObstructionService(
            microservice_url=microservice_url,
            auth_token=auth_token
        )

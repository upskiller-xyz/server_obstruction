"""Result assemblers for parallel execution results"""

import logging
from typing import Any, Dict, List

from src.server.base.constants import ResponseField


class ParallelResultAssembler:
    """
    Assembles results from parallel microservice calls

    Single Responsibility:
    - Only assembles and formats results from multiple directions
    - Does NOT make HTTP calls or handle errors
    """

    @staticmethod
    def assemble_results(
        results: List[Any],
        total_time: float
    ) -> Dict[str, Any]:
        """
        Assemble results from parallel execution into final response

        Args:
            results: List of individual direction results or exceptions
            total_time: Total execution time in seconds

        Returns:
            Dictionary with assembled results and metadata
        """
        horizon_angles = []
        zenith_angles = []
        direction_angles_degrees = []

        for result in results:
            # Skip exceptions
            if isinstance(result, Exception):
                logging.error(f"[PARALLEL] Task raised exception: {str(result)}")
                continue

            # Skip results with errors
            if ResponseField.ERROR.value in result:
                continue

            # Extract direction angle
            direction_angles_degrees.append(
                result[ResponseField.DIRECTION_ANGLE_DEGREES.value]
            )

            # Extract horizon angle
            horizon_data = result.get(ResponseField.HORIZON.value)
            if horizon_data:
                horizon_angles.append(
                    horizon_data.get("obstruction_angle_degrees", 0.0)
                )

            # Extract zenith angle
            zenith_data = result.get(ResponseField.ZENITH.value)
            if zenith_data:
                zenith_angles.append(
                    zenith_data.get("obstruction_angle_degrees", 0.0)
                )

        return {
            ResponseField.RESULTS.value: results,
            "horizon_angles": horizon_angles,
            "zenith_angles": zenith_angles,
            "direction_angles_degrees": direction_angles_degrees,
            "num_directions": len(results),
            "total_time_seconds": total_time
        }

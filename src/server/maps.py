from __future__ import annotations

from typing import Callable, Dict

from src.server.builders import ResponseBuilder

from ..utils.standard_map import StandardMap
from .base.constants import EndpointName


class EndpointResponseMap(StandardMap):
    """Maps endpoints to response builder methods"""
    _content: Dict[EndpointName, Callable] = {
        EndpointName.OBSTRUCTION: ResponseBuilder.success_with_both_angles,
        EndpointName.OBSTRUCTION_ALL: ResponseBuilder.success_with_multi_direction,
        EndpointName.OBSTRUCTION_PARALLEL: ResponseBuilder.success_with_multi_direction,
        EndpointName.STATUS: ResponseBuilder.status
    }
    _default: Callable = ResponseBuilder.success_with_result
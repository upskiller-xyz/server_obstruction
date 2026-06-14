"""Endpoint configuration mapping endpoints to validation and service methods"""

from enum import Enum
from typing import Callable, Dict

from src.server.base.constants import BinaryEndpointName, EndpointName, HTTPMethod
from src.server.services.obstruction_service import ObstructionService
from src.utils.extended_enum import ExtendedEnumMixin
from src.utils.standard_map import StandardMap


class ServiceMethod(StandardMap):
    """Service method names"""
    _content:Dict[EndpointName, Callable] = {
        EndpointName.STATUS : ObstructionService.get_status,
        EndpointName.HORIZON : ObstructionService.calculate_horizon,
        EndpointName.ZENITH: ObstructionService.calculate_zenith_angle,
        EndpointName.OBSTRUCTION_ALL: ObstructionService.calculate_all_directions_async,
        EndpointName.OBSTRUCTION_PARALLEL: ObstructionService.calculate_all_directions_async,
        EndpointName.OBSTRUCTION: ObstructionService.calculate_both_angles
    }
    _default: Callable = ObstructionService.calculate_horizon

class EndpointMethodMap(StandardMap):
    _content:Dict[EndpointName, HTTPMethod] = {
        EndpointName.STATUS: HTTPMethod.GET,
        EndpointName.ROUTES: HTTPMethod.GET
    }
    _default:HTTPMethod = HTTPMethod.POST


class BinaryEndpointLogicalMap(StandardMap):
    """Maps a binary transport endpoint to the logical endpoint whose
    validation/service/response strategies it reuses (Strategy Pattern)."""
    _content:Dict[BinaryEndpointName, EndpointName] = {
        BinaryEndpointName.OBSTRUCTION_PARALLEL_BIN: EndpointName.OBSTRUCTION_PARALLEL,
    }
    _default:EndpointName = EndpointName.OBSTRUCTION_PARALLEL


class ResponseType(ExtendedEnumMixin, Enum):
    """Types of response formatting"""
    SINGLE_RESULT = "single_result"
    BOTH_ANGLES = "both_angles"
    MULTI_DIRECTION = "multi_direction"
    STATUS = "status"



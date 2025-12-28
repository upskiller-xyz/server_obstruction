"""Endpoint configuration mapping endpoints to validation and service methods"""

from typing import Dict, Callable
from enum import Enum
from src.utils.extended_enum import ExtendedEnumMixin
from src.utils.standard_map import StandardMap
from src.components.constants import EndpointName, HTTPMethod
from src.server.services.obstruction_service import ObstructionService


class ServiceMethod(StandardMap):
    """Service method names"""
    _content:Dict[EndpointName, Callable] = {
        EndpointName.STATUS : ObstructionService.get_status,
        EndpointName.HORIZON_ANGLE : ObstructionService.calculate_horizon,
        EndpointName.ZENITH_ANGLE: ObstructionService.calculate_zenith_angle,
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
    
class ResponseType(ExtendedEnumMixin, Enum):
    """Types of response formatting"""
    SINGLE_RESULT = "single_result"
    BOTH_ANGLES = "both_angles"
    MULTI_DIRECTION = "multi_direction"
    STATUS = "status"



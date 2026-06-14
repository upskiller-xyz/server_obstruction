"""API request/response models using Pydantic for type safety and validation in Flask"""
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field


class ObstructionCalculationRequest(BaseModel):
    """
    Obstruction angle calculation request model for type safety and validation.

    Can be used with endpoint_error_handler decorator for automatic validation:
        @endpoint_error_handler(EndpointType.HORIZON_ANGLE, ObstructionCalculationRequest)
    """
    x: float = Field(..., description="Window center X coordinate")
    y: float = Field(..., description="Window center Y coordinate")
    z: float = Field(..., description="Window center Z coordinate (height)")
    direction_angle: float = Field(..., description="Window direction angle in radians (0-2π)")
    mesh: Union[List[List[float]], Dict[str, List[List[float]]]] = Field(
        ...,
        description="Mesh data - either flat list of vertices [[x,y,z],...] or nested {horizon: [...], zenith: [...]}"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "x": 0.0,
                "y": 0.0,
                "z": 3.0,
                "direction_angle": 0.0,
                "mesh": {
                    "horizon": [
                        [10.0, -5.0, 0.0],
                        [10.0, -5.0, 5.0],
                        [10.0, 5.0, 0.0],
                        [10.0, 5.0, 0.0],
                        [10.0, -5.0, 5.0],
                        [10.0, 5.0, 5.0]
                    ]
                }
            }
        }


class MultiDirectionRequest(BaseModel):
    """
    Multi-direction obstruction calculation request model.

    Calculates obstruction angles for multiple directions around a window.
    """
    x: float = Field(..., description="Window center X coordinate")
    y: float = Field(..., description="Window center Y coordinate")
    z: float = Field(..., description="Window center Z coordinate (height)")
    direction_angle: float = Field(..., description="Base window direction angle in radians")
    mesh: List[List[float]] = Field(..., description="Mesh vertices [[x,y,z],...]")
    num_directions: Optional[int] = Field(64, description="Number of directions to calculate (default: 64)")
    start_angle_degrees: Optional[float] = Field(-90.0, description="Start angle offset in degrees (default: -90)")
    end_angle_degrees: Optional[float] = Field(90.0, description="End angle offset in degrees (default: 90)")

    class Config:
        json_schema_extra = {
            "example": {
                "x": 0.0,
                "y": 0.0,
                "z": 3.0,
                "direction_angle": 0.0,
                "mesh": [[10.0, -5.0, 0.0], [10.0, -5.0, 5.0], [10.0, 5.0, 0.0]],
                "num_directions": 64,
                "start_angle_degrees": -90.0,
                "end_angle_degrees": 90.0
            }
        }


class Point3DResponse(BaseModel):
    """3D point response model"""
    x: float
    y: float
    z: float


class ObstructionAngleResponse(BaseModel):
    """
    Single obstruction angle response model.
    """
    obstruction_angle_degrees: float = Field(..., description="Obstruction angle in degrees")
    obstruction_angle_radians: float = Field(..., description="Obstruction angle in radians")
    highest_point: Optional[Point3DResponse] = Field(None, description="Highest obstruction point")

    class Config:
        json_schema_extra = {
            "example": {
                "obstruction_angle_degrees": 11.31,
                "obstruction_angle_radians": 0.197,
                "highest_point": {"x": 10.0, "y": 0.0, "z": 5.0}
            }
        }


class CombinedObstructionResponse(BaseModel):
    """
    Combined horizon and zenith obstruction response model.
    """
    horizon: ObstructionAngleResponse
    zenith: ObstructionAngleResponse

    class Config:
        json_schema_extra = {
            "example": {
                "horizon": {
                    "obstruction_angle_degrees": 11.31,
                    "obstruction_angle_radians": 0.197,
                    "highest_point": {"x": 10.0, "y": 0.0, "z": 5.0}
                },
                "zenith": {
                    "obstruction_angle_degrees": 78.69,
                    "obstruction_angle_radians": 1.373,
                    "highest_point": {"x": 5.0, "y": 1.0, "z": 4.0}
                }
            }
        }


class MultiDirectionResponse(BaseModel):
    """
    Multi-direction obstruction calculation response model.
    """
    horizon_angles: List[float] = Field(..., description="Horizon angles for each direction (degrees)")
    zenith_angles: List[float] = Field(..., description="Zenith angles for each direction (degrees)")
    directions: List[float] = Field(..., description="Direction angles (radians)")
    num_directions: int = Field(..., description="Number of directions calculated")

    class Config:
        json_schema_extra = {
            "example": {
                "horizon_angles": [10.5, 11.2, 12.1],
                "zenith_angles": [75.3, 76.8, 78.2],
                "directions": [0.0, 0.0349, 0.0698],
                "num_directions": 64
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Error type")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid mesh format",
                "error_type": "ValueError"
            }
        }


class StatusResponse(BaseModel):
    """Server status response model"""
    status: str = Field(..., description="Server status")
    version: Optional[str] = Field(None, description="API version")
    services: Optional[Dict[str, str]] = Field(None, description="Service statuses")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "running",
                "version": "1.0.0",
                "services": {
                    "obstruction_service": "ready"
                }
            }
        }

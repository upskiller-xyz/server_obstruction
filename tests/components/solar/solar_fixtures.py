"""Shared requests, windows and sky profiles of the solar tests"""
import math

import numpy as np

from src.components.solar import SkyGapProfile, SolarRequest

SOUTH = -math.pi / 2  # Model +Y is north
NORTH = math.pi / 2
EAST = 0.0
WEST = math.pi
ARLANDA = "stockholm-arlanda-ap"


def make_window(direction: float = SOUTH, **extra) -> dict:
    return {"x": 0.0, "y": 0.0, "z": 1.5, "direction_angle": direction, "area": 2.0, **extra}


def make_request(windows: list, **extra) -> SolarRequest:
    return SolarRequest.from_dict(
        {"latitude": 59.33, "room_area": 15.0, "windows": windows, **extra}
    )


def horizon_profile(horizon_deg: float) -> SkyGapProfile:
    """Profile of a long continuous building in front of the window"""
    return SkyGapProfile(
        relative_angles_rad=np.array([-math.pi / 2, math.pi / 2]),
        lower_deg=np.full(2, horizon_deg),
        upper_deg=np.full(2, 90.0),
    )


def blocked_profile() -> SkyGapProfile:
    """Profile hiding the whole sky (horizon at 89°)"""
    return SkyGapProfile(
        relative_angles_rad=np.array([-math.pi / 2, math.pi / 2]),
        lower_deg=np.full(2, 89.0),
        upper_deg=np.full(2, 90.0),
    )

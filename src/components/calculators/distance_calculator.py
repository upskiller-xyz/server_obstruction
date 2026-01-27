from __future__ import annotations
import time
from typing import List
import numpy as np
import logging

from src.components.models import Window

logger = logging.getLogger(__name__)

from src.server.base.constants import ANGLES, MathConstants
from src.components.geometry import Point3D, Vector3D


class DistanceCalculator:
    
    
    @classmethod
    def _get_vertical(cls, intersections:List[Point3D], 
                      *args
                      )->List[float]:
        return [p.z for p in intersections]
    
    @classmethod
    def _get_horizontal(cls, intersections:List[Point3D], window: Window)->List[float]:
        hds = [cls._adjust_horizontal(p, window) for p in intersections]
        return [a for a in hds if not a is None]
    
    

    @classmethod
    def call(cls, intersections:List[Point3D], angle_type:ANGLES, window:Window):
        _content_map = {
            ANGLES.HORIZON: cls._get_vertical,
            ANGLES.ZENITH: cls._get_horizontal
        }
        _default = cls._get_vertical
        return _content_map.get(angle_type, _default)(intersections, window)
    
    @classmethod
    def _adjust_horizontal(cls, point:Point3D, window:Window)->float | None:
        if point.z < window.center.z:
            return None
        point_vec = point.to_array() - window.center.to_array()
        if point_vec[2] <= 0:
            return None
        
        normal_horizontal = cls._normal_horizontal(window.normal)

        if normal_horizontal is None:
            point_horizontal = np.array([point_vec[0], point_vec[1], 0.0])
            return float(np.linalg.norm(point_horizontal))

        # Calculate signed distance along viewing direction (positive = ahead)
        forward_distance = float(np.dot(point_vec, normal_horizontal))

        # Only accept points ahead of window (positive dot product)
        if forward_distance <= 0:
            return None

        return forward_distance
    
    @classmethod
    def _normal_horizontal(cls, window_normal:Vector3D)->np.ndarray | None:
        normal_arr = window_normal.to_array()
        normal_horizontal = np.array([normal_arr[0], normal_arr[1], 0.0])
        magnitude = np.linalg.norm(normal_horizontal)
        if magnitude < MathConstants.EPSILON.value:
            return 
        return normal_horizontal / magnitude
"""Settings singleton for application-wide configuration"""
from __future__ import annotations


class Settings:
    max_horizontal_distance:float = 5 # limit for zenith angle
    min_horizontal_distance:float = 5 # limit for horizon angle
    max_vertical_normal_z = 0.5 # declination to determine vertical surfaces
    max_angle_degrees:float = 80 # obstruction angle limit

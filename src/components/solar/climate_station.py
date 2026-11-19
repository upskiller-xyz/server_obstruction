"""
Climate stations with their clear-sky optical depths

Same station keys as the climate files (EPW) used by the daylight autonomy
simulation, so every analysis of a project refers to the same location. The
table holds the monthly ASHRAE clear-sky optical depths (taub, taud) taken
from the .stat file of each station's TMYx package.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class ClimateStation:
    """Weather station with monthly clear-sky optical depths (January to December)"""
    key: str
    latitude_deg: float
    longitude_deg: float
    taub: Tuple[float, ...]
    taud: Tuple[float, ...]
    tau_source: str


class ClimateStationCatalogue:
    """Looks up climate stations by key"""

    _DATA_PATH: Path = Path(__file__).parent / "data" / "clear_sky_taus.json"

    @classmethod
    def get(cls, key: str) -> ClimateStation:
        """
        Get a station by key.

        Raises:
            ValueError: If no station has that key
        """
        station = cls._stations().get(key)
        if station is None:
            raise ValueError(f"Unknown city '{key}': not a climate station key")
        return station

    @classmethod
    def find(cls, key: Optional[str]) -> Optional[ClimateStation]:
        """Station for a key, or None when no key is given"""
        return None if key is None else cls.get(key)

    @classmethod
    @lru_cache(maxsize=1)
    def _stations(cls) -> Dict[str, ClimateStation]:
        """Load the station table once"""
        with open(cls._DATA_PATH, encoding="utf-8") as file:
            stations = json.load(file)["stations"]
        return {
            key: ClimateStation(
                key=key,
                latitude_deg=float(entry["lat"]),
                longitude_deg=float(entry["lon"]),
                taub=tuple(entry["taub"]),
                taud=tuple(entry["taud"]),
                tau_source=entry["tau_source"],
            )
            for key, entry in stations.items()
        }

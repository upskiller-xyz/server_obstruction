"""
Coordinate system conversion utilities

The real-world JSON samples use XZY order (x, z, y) instead of XYZ (x, y, z).
This module provides utilities to convert between these coordinate systems.

In our server:
- X-axis: Horizontal (East)
- Y-axis: Horizontal (North)
- Z-axis: Vertical (Up)

In the JSON samples (incorrect order):
- Position 0: X (correct)
- Position 1: Z (should be Y)
- Position 2: Y (should be Z)
"""
from typing import List, Dict, Any
import numpy as np


class CoordinateConverter:
    """Converts between XZY and XYZ coordinate systems"""

    @staticmethod
    def xzy_to_xyz(point: List[float]) -> List[float]:
        """
        Convert XZY to XYZ coordinate order

        Args:
            point: [x, z, y] coordinates

        Returns:
            [x, y, z] coordinates
        """
        if len(point) != 3:
            raise ValueError(f"Point must have 3 coordinates, got {len(point)}")

        x, z, y = point
        return [x, y, z]

    @staticmethod
    def xyz_to_xzy(point: List[float]) -> List[float]:
        """
        Convert XYZ to XZY coordinate order

        Args:
            point: [x, y, z] coordinates

        Returns:
            [x, z, y] coordinates
        """
        if len(point) != 3:
            raise ValueError(f"Point must have 3 coordinates, got {len(point)}")

        x, y, z = point
        return [x, z, y]

    @classmethod
    def convert_mesh_xzy_to_xyz(cls, mesh: List[List[float]]) -> List[List[float]]:
        """
        Convert entire mesh from XZY to XYZ

        Args:
            mesh: List of [x, z, y] vertices

        Returns:
            List of [x, y, z] vertices
        """
        return [cls.xzy_to_xyz(vertex) for vertex in mesh]

    @classmethod
    def convert_mesh_xyz_to_xzy(cls, mesh: List[List[float]]) -> List[List[float]]:
        """
        Convert entire mesh from XYZ to XZY

        Args:
            mesh: List of [x, y, z] vertices

        Returns:
            List of [x, z, y] vertices
        """
        return [cls.xyz_to_xzy(vertex) for vertex in mesh]

    @classmethod
    def convert_request_data_xzy_to_xyz(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert request data from XZY to XYZ coordinate system

        Converts:
        - Window position (x, z, y) -> (x, y, z)
        - Mesh vertices

        Args:
            data: Request dictionary with XZY coordinates

        Returns:
            Request dictionary with XYZ coordinates
        """
        converted = data.copy()

        # Convert window position
        # Assuming the data has x, z as second coord, y as third coord
        if 'x' in data and 'y' in data and 'z' in data:
            # The keys are named correctly, but values are in wrong order
            # We need to swap y and z values
            converted['y'] = data['z']  # What was called 'z' is actually Y
            converted['z'] = data['y']  # What was called 'y' is actually Z

        # Convert mesh
        if 'mesh' in data:
            converted['mesh'] = cls.convert_mesh_xzy_to_xyz(data['mesh'])

        return converted

    @classmethod
    def analyze_coordinate_system(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze coordinate system to detect if conversion is needed

        Args:
            data: Request data dictionary

        Returns:
            Analysis results
        """
        mesh = np.array(data['mesh'])

        # Calculate ranges for each coordinate
        ranges = {
            'coord_0': (mesh[:, 0].min(), mesh[:, 0].max()),
            'coord_1': (mesh[:, 1].min(), mesh[:, 1].max()),
            'coord_2': (mesh[:, 2].min(), mesh[:, 2].max())
        }

        # Window position
        window = [data.get('x', 0), data.get('y', 0), data.get('z', 0)]

        # Heuristic: vertical axis typically has smaller range
        # In correct XYZ system, Z (index 2) should be vertical
        coord_1_range = ranges['coord_1'][1] - ranges['coord_1'][0]
        coord_2_range = ranges['coord_2'][1] - ranges['coord_2'][0]

        likely_swapped = coord_1_range > coord_2_range

        return {
            'ranges': ranges,
            'window_position': window,
            'likely_xzy_format': likely_swapped,
            'recommendation': 'Use convert_request_data_xzy_to_xyz()' if likely_swapped else 'Coordinates appear correct',
            'coord_1_range': coord_1_range,
            'coord_2_range': coord_2_range
        }


# Convenience functions
def convert_xzy_to_xyz(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to convert request data from XZY to XYZ

    Args:
        data: Request dictionary with XZY coordinates

    Returns:
        Request dictionary with XYZ coordinates
    """
    return CoordinateConverter.convert_request_data_xzy_to_xyz(data)


def analyze_coordinates(data: Dict[str, Any]) -> None:
    """
    Analyze and print coordinate system information

    Args:
        data: Request dictionary
    """
    analysis = CoordinateConverter.analyze_coordinate_system(data)

    print("📊 Coordinate System Analysis:")
    print(f"   Window position: ({analysis['window_position'][0]:.2f}, "
          f"{analysis['window_position'][1]:.2f}, {analysis['window_position'][2]:.2f})")
    print(f"\n   Coordinate ranges:")
    for coord, (min_val, max_val) in analysis['ranges'].items():
        print(f"   {coord}: [{min_val:.2f}, {max_val:.2f}] (range: {max_val - min_val:.2f})")

    print(f"\n   Coord 1 range: {analysis['coord_1_range']:.2f}")
    print(f"   Coord 2 range: {analysis['coord_2_range']:.2f}")

    if analysis['likely_xzy_format']:
        print(f"\n   ⚠️  Data appears to be in XZY format!")
        print(f"   📝 {analysis['recommendation']}")
    else:
        print(f"\n   ✅ Data appears to be in correct XYZ format")

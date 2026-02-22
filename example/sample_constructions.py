"""Sample construction builders for demo scenarios following OOP principles

COORDINATE SYSTEM: Z-up (X=East, Y=North, Z=Up)
- X-axis: East/West (horizontal)
- Y-axis: North/South (horizontal)
- Z-axis: Up/Down (vertical)
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from enum import Enum


class MeshType(Enum):
    """Types of mesh constructions"""
    VERTICAL_WALL = "vertical_wall"
    HORIZONTAL_ROOF = "horizontal_roof"
    BUILDING = "building"


class IMeshBuilder(ABC):
    """Interface for mesh construction builders"""

    @abstractmethod
    def build(self) -> List[List[float]]:
        """Build and return mesh vertices as triangles"""
        pass


class VerticalWallBuilder(IMeshBuilder):
    """Builds a vertical wall mesh (building facade)"""

    def __init__(self, distance: float, height: float, width: float):
        """
        Initialize vertical wall builder

        Args:
            distance: Distance from origin along X-axis (East)
            height: Height of wall (Z-axis, vertical)
            width: Width of wall (Y-axis, North-South, centered at 0)
        """
        self.distance = distance
        self.height = height
        self.width = width

    def build(self) -> List[List[float]]:
        """Build vertical wall as two triangles forming a rectangle

        Coordinates: [x, y, z] where z is height
        """
        half_width = self.width / 2

        # Two triangles forming vertical rectangle facing -X direction
        return [
            # Triangle 1: bottom-left, top-left, bottom-right
            [self.distance, -half_width, 0.0],
            [self.distance, -half_width, self.height],
            [self.distance, half_width, 0.0],

            # Triangle 2: bottom-right, top-left, top-right
            [self.distance, half_width, 0.0],
            [self.distance, -half_width, self.height],
            [self.distance, half_width, self.height]
        ]


class HorizontalRoofBuilder(IMeshBuilder):
    """Builds a horizontal roof/balcony mesh (overhead obstruction)"""

    def __init__(self, start_distance: float, end_distance: float,
                 height: float, width: float):
        """
        Initialize horizontal roof builder

        Args:
            start_distance: Start distance along X-axis (East)
            end_distance: End distance along X-axis (East)
            height: Height of roof (Z-axis, vertical)
            width: Width of roof (Y-axis, North-South, centered at 0)
        """
        self.start_distance = start_distance
        self.end_distance = end_distance
        self.height = height
        self.width = width

    def build(self) -> List[List[float]]:
        """Build horizontal roof as two triangles forming a rectangle

        Coordinates: [x, y, z] where z is height
        Normal points up (+Z direction)
        """
        half_width = self.width / 2

        # Two triangles forming horizontal rectangle (normal pointing up)
        return [
            # Triangle 1
            [self.start_distance, -half_width, self.height],
            [self.start_distance, half_width, self.height],
            [self.end_distance, -half_width, self.height],

            # Triangle 2
            [self.start_distance, half_width, self.height],
            [self.end_distance, half_width, self.height],
            [self.end_distance, -half_width, self.height]
        ]


class ScenarioConfiguration:
    """Configuration for a test scenario"""

    def __init__(self, window_center: List[float], direction_angle: float):
        """
        Initialize scenario configuration

        Args:
            window_center: [x, y, z] position of window
            direction_angle: Horizontal rotation angle in radians (0 to 2π)
                - 0: Points in +X direction
                - π/2: Points in +Z direction
                - π: Points in -X direction
                - 3π/2: Points in -Z direction
        """
        self.window_center = window_center
        self.direction_angle = direction_angle
        self.meshes: List[List[List[float]]] = []

    def add_mesh(self, builder: IMeshBuilder) -> 'ScenarioConfiguration':
        """
        Add a mesh to the scenario using a builder

        Args:
            builder: Mesh builder instance

        Returns:
            Self for chaining
        """
        self.meshes.append(builder.build())
        return self

    def get_combined_mesh(self) -> List[List[float]]:
        """Get all meshes combined into a single list"""
        combined = []
        for mesh in self.meshes:
            combined.extend(mesh)
        return combined

    def to_request_data(self, mesh_type: str = "combined") -> dict:
        """Convert to API request format

        Args:
            mesh_type: Type of mesh format to use
                - "combined": Single flat mesh array (for /obstruction endpoint)
                - "horizon": Mesh wrapped in {"horizon": [...]} (for /horizon_angle endpoint)
                - "zenith": Mesh wrapped in {"zenith": [...]} (for /zenith_angle endpoint)

        Returns:
            Request data dictionary
        """
        mesh_data = self.get_combined_mesh()

        # Format mesh based on endpoint type
        if mesh_type == "horizon":
            mesh_value = {"horizon": mesh_data}
        elif mesh_type == "zenith":
            mesh_value = {"zenith": mesh_data}
        else:  # combined or default
            mesh_value = mesh_data

        return {
            "x": self.window_center[0],
            "y": self.window_center[1],
            "z": self.window_center[2],
            "direction_angle": self.direction_angle,
            "mesh": mesh_value
        }


class StandardScenarios:
    """Factory for creating standard test scenarios"""

    @staticmethod
    def vertical_building(window_height: float = 3.0,
                         building_distance: float = 10.0,
                         building_height: float = 5.0,
                         building_width: float = 10.0) -> ScenarioConfiguration:
        """
        Create scenario with vertical building wall

        Args:
            window_height: Height of window center
            building_distance: Distance to building
            building_height: Height of building
            building_width: Width of building

        Returns:
            Configured scenario
        """
        scenario = ScenarioConfiguration(
            window_center=[0.0, 0.0, window_height],  # Z-up: [x, y, z]
            direction_angle=0.0  # Facing +X direction (East)
        )

        wall_builder = VerticalWallBuilder(
            distance=building_distance,
            height=building_height,
            width=building_width
        )

        return scenario.add_mesh(wall_builder)

    @staticmethod
    def horizontal_overhead(window_height: float = 3.0,
                           roof_start: float = 5.0,
                           roof_end: float = 8.0,
                           roof_height: float = 7.0,
                           roof_width: float = 4.0) -> ScenarioConfiguration:
        """
        Create scenario with horizontal overhead obstruction

        Args:
            window_height: Height of window center (Z coordinate)
            roof_start: Start distance of roof along X-axis (use positive value for in front)
            roof_end: End distance of roof along X-axis
            roof_height: Height of roof (Z coordinate)
            roof_width: Width of roof (Y-axis, North-South)

        Returns:
            Configured scenario

        Note:
            For the roof to be detected, it must be:
            - Above the window (roof_height > window_height)
            - In front of the window (roof_start > 0, roof_end > 0)
        """
        scenario = ScenarioConfiguration(
            window_center=[0.0, 0.0, window_height],  # Z-up: [x, y, z]
            direction_angle=0.0  # Facing +X direction (East)
        )

        roof_builder = HorizontalRoofBuilder(
            start_distance=roof_start,
            end_distance=roof_end,
            height=roof_height,
            width=roof_width
        )

        return scenario.add_mesh(roof_builder)

    @staticmethod
    def mixed_obstruction(window_height: float = 3.0) -> ScenarioConfiguration:
        """
        Create scenario with both vertical and horizontal obstructions

        Args:
            window_height: Height of window center (Z coordinate)

        Returns:
            Configured scenario
        """
        scenario = ScenarioConfiguration(
            window_center=[0.0, 0.0, window_height],  # Z-up: [x, y, z]
            direction_angle=0.0  # Facing +X direction (East)
        )

        # Add vertical wall
        wall_builder = VerticalWallBuilder(
            distance=10.0,
            height=5.0,
            width=10.0
        )

        # Add horizontal roof
        roof_builder = HorizontalRoofBuilder(
            start_distance=5.0,
            end_distance=8.0,
            height=7.0,
            width=4.0
        )

        return scenario.add_mesh(wall_builder).add_mesh(roof_builder)

"""Sample construction builders for demo scenarios following OOP principles"""
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
            distance: Distance from origin along X-axis
            height: Height of wall (Y-axis)
            width: Width of wall (Z-axis, centered at 0)
        """
        self.distance = distance
        self.height = height
        self.width = width

    def build(self) -> List[List[float]]:
        """Build vertical wall as two triangles forming a rectangle"""
        half_width = self.width / 2

        # Two triangles forming vertical rectangle facing -X direction
        return [
            # Triangle 1: bottom-left, top-left, bottom-right
            [self.distance, 0.0, -half_width],
            [self.distance, self.height, -half_width],
            [self.distance, 0.0, half_width],

            # Triangle 2: bottom-right, top-left, top-right
            [self.distance, 0.0, half_width],
            [self.distance, self.height, -half_width],
            [self.distance, self.height, half_width]
        ]


class HorizontalRoofBuilder(IMeshBuilder):
    """Builds a horizontal roof/balcony mesh (overhead obstruction)"""

    def __init__(self, start_distance: float, end_distance: float,
                 height: float, width: float):
        """
        Initialize horizontal roof builder

        Args:
            start_distance: Start distance along X-axis
            end_distance: End distance along X-axis
            height: Height of roof (Y-axis)
            width: Width of roof (Z-axis, centered at 0)
        """
        self.start_distance = start_distance
        self.end_distance = end_distance
        self.height = height
        self.width = width

    def build(self) -> List[List[float]]:
        """Build horizontal roof as two triangles forming a rectangle"""
        half_width = self.width / 2

        # Two triangles forming horizontal rectangle (normal pointing up)
        return [
            # Triangle 1
            [self.start_distance, self.height, -half_width],
            [self.start_distance, self.height, half_width],
            [self.end_distance, self.height, -half_width],

            # Triangle 2
            [self.start_distance, self.height, half_width],
            [self.end_distance, self.height, half_width],
            [self.end_distance, self.height, -half_width]
        ]


class ScenarioConfiguration:
    """Configuration for a test scenario"""

    def __init__(self, window_center: List[float], window_angles: List[float]):
        """
        Initialize scenario configuration

        Args:
            window_center: [x, y, z] position of window
            window_angles: [rad_x, rad_y] viewing angles
        """
        self.window_center = window_center
        self.window_angles = window_angles
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

    def to_request_data(self) -> dict:
        """Convert to API request format"""
        return {
            "x": self.window_center[0],
            "y": self.window_center[1],
            "z": self.window_center[2],
            "rad_x": self.window_angles[0],
            "rad_y": self.window_angles[1],
            "mesh": self.get_combined_mesh()
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
            window_center=[0.0, window_height, 0.0],
            window_angles=[0.03, 0.0]
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
            window_height: Height of window center
            roof_start: Start distance of roof
            roof_end: End distance of roof
            roof_height: Height of roof
            roof_width: Width of roof

        Returns:
            Configured scenario
        """
        scenario = ScenarioConfiguration(
            window_center=[0.0, window_height, 0.0],
            window_angles=[0.0, 0.0]
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
            window_height: Height of window center

        Returns:
            Configured scenario
        """
        scenario = ScenarioConfiguration(
            window_center=[0.0, window_height, 0.0],
            window_angles=[0.03, 0.0]
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

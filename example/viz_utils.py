"""Visualization utilities for raytracing demo"""
from abc import ABC, abstractmethod
from typing import Tuple, List
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class DirectionVectorCalculator:
    """Calculate direction vectors from rotation angles"""

    @staticmethod
    def from_angles(rad_x: float, rad_y: float) -> np.ndarray:
        """
        Convert rotation angles to unit direction vector

        Returns vector in calculation space (X, Y, Z) where Y is up
        """
        return np.array([
            np.cos(rad_y) * np.cos(rad_x),
            np.sin(rad_x),
            np.sin(rad_y) * np.cos(rad_x)
        ])

    @staticmethod
    def get_horizontal_component(direction_vec: np.ndarray) -> np.ndarray:
        """Extract horizontal component of direction vector (remove Y which is up)"""
        horiz = direction_vec.copy()
        horiz[1] = 0.0
        mag = np.linalg.norm(horiz)
        return horiz / mag if mag > 1e-6 else np.array([1.0, 0.0, 0.0])


class ProjectionPlaneBuilder:
    """Build vertical projection plane geometry"""

    def __init__(self, window_center: List[float], horizontal_dir: np.ndarray):
        self.window_center = np.array(window_center)
        self.u_axis = horizontal_dir / np.linalg.norm(horizontal_dir)
        self.v_axis = np.array([0, 1, 0])  # World up (Y-axis in calc space)

    def build_mesh(self, width: float = 12, height_range: Tuple[float, float] = (-2, 10),
                   resolution: int = 8) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Build projection plane mesh for visualization

        Returns:
            (X, Y, Z) arrays for plot_surface
        """
        u_vals = np.linspace(-width/2, width/2, resolution)
        v_vals = np.linspace(height_range[0], height_range[1], resolution)
        U, V = np.meshgrid(u_vals, v_vals)

        points = np.zeros((resolution, resolution, 3))
        for i in range(resolution):
            for j in range(resolution):
                points[i, j] = (
                    self.window_center +
                    U[i, j] * self.u_axis +
                    V[i, j] * self.v_axis
                )

        return points[:, :, 0], points[:, :, 1], points[:, :, 2]

    def project_point(self, point: np.ndarray) -> np.ndarray:
        """Project a 3D point onto this plane"""
        relative = point - self.window_center
        u = np.dot(relative, self.u_axis)
        v = np.dot(relative, self.v_axis)
        return self.window_center + u * self.u_axis + v * self.v_axis


class MeshProjector:
    """Project mesh vertices onto projection plane"""

    def __init__(self, plane_builder: ProjectionPlaneBuilder):
        self.plane_builder = plane_builder

    def find_highest_projected_point(self, mesh_vertices: List[List[float]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Find the highest point when mesh vertices are projected onto the plane

        Returns:
            (projected_point, original_point) tuple
        """
        highest_projected = None
        highest_original = None
        max_height = -float('inf')

        for vertex in mesh_vertices:
            projected = self.plane_builder.project_point(np.array(vertex))

            # Y component is height in calc space
            if projected[1] > max_height:
                max_height = projected[1]
                highest_projected = projected
                highest_original = np.array(vertex)

        return highest_projected, highest_original


class MeshRenderer:
    """Render 3D mesh geometry"""

    @staticmethod
    def create_collection(mesh_vertices: List[List[float]]) -> Poly3DCollection:
        """Create Poly3DCollection from mesh vertices (groups of 3)"""
        triangles = [mesh_vertices[i:i+3] for i in range(0, len(mesh_vertices), 3)]
        return Poly3DCollection(
            triangles,
            alpha=0.6,
            facecolor='skyblue',
            edgecolor='darkblue',
            linewidths=1.5
        )


class AxisConfigurator:
    """Configure 3D plot axes"""

    @staticmethod
    def setup(ax, max_range: float = 15, title: str = "",
              view_elev: int = 20, view_azim: int = 45):
        """
        Setup 3D axes with proper labels and viewing angle

        Note: We plot (X, Z, Y) so that Y (up) appears as the vertical axis
        """
        ax.set_xlabel('X (m) →', fontsize=10, fontweight='bold')
        ax.set_ylabel('Z (m) →', fontsize=10, fontweight='bold')
        ax.set_zlabel('Y (m) ↑', fontsize=10, fontweight='bold')
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlim(-2, max_range)
        ax.set_ylim(-max_range/2, max_range/2)
        ax.set_zlim(-1, max_range)
        ax.view_init(elev=view_elev, azim=view_azim)
        ax.grid(True, alpha=0.3)


class PlotElementRenderer:
    """Render individual plot elements with proper labels"""

    @staticmethod
    def add_window(ax, window_center: List[float]):
        """Add window marker to plot (swap Y and Z for matplotlib)"""
        ax.scatter(window_center[0], window_center[2], window_center[1],
                   c='red', s=200, marker='o', label='Window', edgecolors='k', lw=2)

    @staticmethod
    def add_mesh(ax, mesh_vertices: List[List[float]]):
        """Add mesh to plot (swap Y and Z for matplotlib)"""
        mesh_viz = [[v[0], v[2], v[1]] for v in mesh_vertices]
        ax.add_collection3d(MeshRenderer.create_collection(mesh_viz))

    @staticmethod
    def add_viewing_direction(ax, window_center: List[float], direction_vec: np.ndarray, length: float):
        """Add viewing direction arrow (swap Y and Z for matplotlib)"""
        ax.quiver(window_center[0], window_center[2], window_center[1],
                  direction_vec[0]*length, direction_vec[2]*length, direction_vec[1]*length,
                  color='magenta', lw=2, arrow_length_ratio=0.03, label='View Dir')

    @staticmethod
    def add_projection_plane(ax, plane_builder: ProjectionPlaneBuilder,
                            width: float = 12, height_range: Tuple[float, float] = (-2, 10)):
        """Add projection plane surface (swap Y and Z for matplotlib)"""
        pX, pY, pZ = plane_builder.build_mesh(width=width, height_range=height_range)
        ax.plot_surface(pX, pZ, pY, alpha=0.15, color='green')

    @staticmethod
    def add_highest_point(ax, point: np.ndarray):
        """Add highest projected point marker (swap Y and Z for matplotlib)"""
        ax.scatter(point[0], point[2], point[1], c='orange', s=150, marker='^',
                   label='Highest (on plane)', edgecolors='k', lw=2)

    @staticmethod
    def add_obstruction_line(ax, start: List[float], end: np.ndarray, angle_degrees: float):
        """Add obstruction line from window to highest point (swap Y and Z for matplotlib)"""
        ax.plot([start[0], end[0]], [start[2], end[2]], [start[1], end[1]],
                'r--', lw=3, label=f'Obstruction {angle_degrees:.1f}°')

    @staticmethod
    def add_projection_line(ax, original: np.ndarray, projected: np.ndarray):
        """Add line showing projection from mesh to plane (swap Y and Z for matplotlib)"""
        ax.plot([original[0], projected[0]], [original[2], projected[2]], [original[1], projected[1]],
                'b--', lw=2, alpha=0.8, label='Projection')


class VisualizationFactory:
    """Factory for creating visualization components"""

    @staticmethod
    def create_projection_components(window_center: List[float], window_angles: Tuple[float, float]):
        """
        Create all components needed for projection visualization

        Returns:
            (direction_vec, horizontal_dir, plane_builder, mesh_projector)
        """
        calc = DirectionVectorCalculator()
        direction_vec = calc.from_angles(*window_angles)
        horizontal_dir = calc.get_horizontal_component(direction_vec)

        plane_builder = ProjectionPlaneBuilder(window_center, horizontal_dir)
        mesh_projector = MeshProjector(plane_builder)

        return direction_vec, horizontal_dir, plane_builder, mesh_projector

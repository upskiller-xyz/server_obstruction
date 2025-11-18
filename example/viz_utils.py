"""Visualization utilities for raytracing demo

Coordinate System Transformation:
- Calculation Space: X=East, Y=North, Z=Up (Z-up system)
- Matplotlib 3D Space: X=right, Y=up, Z=forward (Y-up system)
- Transformation: (calc_x, calc_y, calc_z) -> (mpl_x, mpl_z, mpl_y)
  - X stays X
  - Y (North) becomes Z (forward in matplotlib)
  - Z (Up) becomes Y (up in matplotlib)
"""
from abc import ABC, abstractmethod
from typing import Tuple, List, Union
from enum import Enum
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class CoordinateTransform:
    """Transform between calculation space (Z-up) and matplotlib space (Y-up)"""

    @staticmethod
    def calc_to_mpl(point: Union[np.ndarray, List[float]]) -> np.ndarray:
        """
        Transform from calculation space to matplotlib 3D space

        Calculation: (X=East, Y=North, Z=Up)
        Matplotlib: (X=right, Y=up, Z=forward)

        Transform: [calc_x, calc_y, calc_z] -> [mpl_x, mpl_y, mpl_z]
                   [x, y, z] -> [x, z, y]

        Args:
            point: Point in calculation space [x, y, z]

        Returns:
            Point in matplotlib space [x, z, y]
        """
        p = np.array(point) if isinstance(point, list) else point
        return np.array([p[0], p[1], p[2]])  # Swap Y and Z

    @staticmethod
    def calc_to_mpl_batch(points: List[List[float]]) -> List[List[float]]:
        """Transform multiple points from calculation to matplotlib space"""
        return [[p[0], p[1], p[2]] for p in points]


class Color(Enum):
    """Standard colors for visualization"""
    RED = 'red'
    SKYBLUE = 'skyblue'
    DARKBLUE = 'darkblue'
    MAGENTA = 'magenta'
    GREEN = 'green'
    ORANGE = 'orange'
    BLUE = 'blue'
    BLACK = 'black'


class Marker(Enum):
    """Marker shapes for scatter plots"""
    CIRCLE = 'o'
    CROSS = 'x'
    TRIANGLE_UP = '^'
    SQUARE = 's'


class LineStyle(Enum):
    """Line styles for plotting"""
    SOLID = '-'
    DASHED = '--'


class AxisLabel(Enum):
    """Axis labels for matplotlib (Y-up system)"""
    X_METERS = 'X (m) - East →'
    Y_METERS = 'Y (m) - Up ↑'  # matplotlib Y is vertical
    Z_METERS = 'Z (m) - North →'  # matplotlib Z is horizontal (was Y in calc)


class PlotLabel(Enum):
    """Standard plot labels"""
    WINDOW = 'Window'
    VIEW_DIR = 'View Dir'
    VIEW_DIRECTION = 'View Direction'
    HIGHEST_ON_PLANE = 'Highest (on plane)'
    PROJECTION = 'Projection'
    FURTHEST_OVERHEAD = 'Furthest overhead point'
    API_POINT_OFF_PLANE = 'API point (off plane)'
    HORIZONTAL_REFERENCE = 'Horizontal reference'
    VERTICAL_COMPONENT = 'Vertical component'
    DIRECTION_PLANE = 'Direction Plane'


class DirectionVectorCalculator:
    """Calculate direction vectors from rotation angles"""

    @staticmethod
    def from_horizontal_angle(angle: float) -> np.ndarray:
        """
        Convert horizontal rotation angle to unit direction vector

        Coordinate system: Z-axis points up, rotation in XY plane
        - angle=0: Points in +X direction (East)
        - angle=π/2: Points in +Y direction (North)
        - angle=π: Points in -X direction (West)
        - angle=3π/2: Points in -Y direction (South)

        Args:
            angle: Horizontal rotation angle in radians (0 to 2π)

        Returns:
            Unit vector in horizontal plane [x, y, z] where z=0
        """
        return np.array([
            np.cos(angle),
            np.sin(angle),
            0.0  # Horizontal plane only (Z is up)
        ])

    @staticmethod
    def from_angles(rad_x: float, rad_y: float) -> np.ndarray:
        """
        DEPRECATED: Use from_horizontal_angle instead

        Convert rotation angles to unit direction vector (old two-angle system)

        Returns vector in calculation space (X, Y, Z) where Z is up
        """
        return np.array([
            np.cos(rad_y) * np.cos(rad_x),
            np.sin(rad_y) * np.cos(rad_x),
            np.sin(rad_x)
        ])

    @staticmethod
    def get_horizontal_component(direction_vec: np.ndarray) -> np.ndarray:
        """Extract horizontal component of direction vector (remove Z which is up)"""
        horiz = direction_vec.copy()
        horiz[2] = 0.0  # Remove Z component (vertical)
        mag = np.linalg.norm(horiz)
        return horiz / mag if mag > 1e-6 else np.array([1.0, 0.0, 0.0])


class ProjectionPlaneBuilder:
    """Build vertical projection plane geometry"""

    def __init__(self, window_center: List[float], horizontal_dir: np.ndarray):
        self.window_center = np.array(window_center)
        self.u_axis = horizontal_dir / np.linalg.norm(horizontal_dir)
        self.v_axis = np.array([0, 0, 1])  # World up

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
        wc = self.window_center
        wc[2] = point[2]
        relative = point - wc
        relative[2] = point[2]
        u = np.dot(relative, self.u_axis)
        v = np.dot(relative, self.v_axis)
        res = wc + u * self.u_axis + v * self.v_axis
        res[2] = point[2]
        return res


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

            # Z component is height in calc space (Z-up coordinate system)
            if projected[2] > max_height:
                max_height = projected[2]
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
            facecolor=Color.SKYBLUE.value,
            edgecolor=Color.DARKBLUE.value,
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
        ax.set_xlabel(AxisLabel.X_METERS.value, fontsize=10, fontweight='bold')
        ax.set_ylabel(AxisLabel.Z_METERS.value, fontsize=10, fontweight='bold')
        ax.set_zlabel(AxisLabel.Y_METERS.value, fontsize=10, fontweight='bold')
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
        """Add window marker to plot"""
        mpl_pos = CoordinateTransform.calc_to_mpl(window_center)
        ax.scatter(mpl_pos[0], mpl_pos[1], mpl_pos[2],
                   c=Color.RED.value, s=200, marker=Marker.CIRCLE.value,
                   label=PlotLabel.WINDOW.value, edgecolors=Color.BLACK.value, lw=2)
        

    @staticmethod
    def add_mesh(ax, mesh_vertices: List[List[float]]):
        """Add mesh to plot"""
        mesh_viz = CoordinateTransform.calc_to_mpl_batch(mesh_vertices)
        m = MeshRenderer.create_collection(mesh_vertices)
        ax.add_collection3d(MeshRenderer.create_collection(mesh_vertices))

    @staticmethod
    def add_viewing_direction(ax, window_center: List[float], direction_vec: np.ndarray, length: float):
        """Add viewing direction arrow"""
        mpl_pos = CoordinateTransform.calc_to_mpl(window_center)
        mpl_dir = CoordinateTransform.calc_to_mpl(direction_vec)
        ax.quiver(mpl_pos[0], mpl_pos[1], mpl_pos[2],
                  mpl_dir[0]*length, mpl_dir[1]*length, mpl_dir[2]*length,
                  color=Color.BLUE.value, lw=2, arrow_length_ratio=0.03,
                  label=PlotLabel.VIEW_DIR.value)

    @staticmethod
    def add_projection_plane(ax, plane_builder: ProjectionPlaneBuilder,
                            width: float = 12, height_range: Tuple[float, float] = (-2, 10)):
        """Add projection plane surface"""
        pX, pY, pZ = plane_builder.build_mesh(width=width, height_range=height_range)
        # Transform each point in the mesh to matplotlib space
        resolution = pX.shape[0]
        mpl_X, mpl_Y, mpl_Z = np.zeros_like(pX), np.zeros_like(pY), np.zeros_like(pZ)
        for i in range(resolution):
            for j in range(resolution):
                calc_point = [pX[i,j], pY[i,j], pZ[i,j]]
                mpl_point = CoordinateTransform.calc_to_mpl(calc_point)
                mpl_X[i,j], mpl_Y[i,j], mpl_Z[i,j] = mpl_point
        ax.plot_surface(mpl_X, mpl_Y, mpl_Z, alpha=0.15, color=Color.GREEN.value)

    @staticmethod
    def add_highest_point(ax, point: np.ndarray):
        """Add highest projected point marker"""
        mpl_pos = CoordinateTransform.calc_to_mpl(point)
        ax.scatter(mpl_pos[0], mpl_pos[1], mpl_pos[2], c=Color.ORANGE.value, s=150,
                   marker=Marker.TRIANGLE_UP.value, label=PlotLabel.HIGHEST_ON_PLANE.value,
                   edgecolors=Color.BLACK.value, lw=2)

    @staticmethod
    def add_obstruction_line(ax, start: List[float], end: np.ndarray, angle_degrees: float):
        """Add obstruction line from window to highest point"""
        mpl_start = CoordinateTransform.calc_to_mpl(start)
        mpl_end = CoordinateTransform.calc_to_mpl(end)
        ax.plot([mpl_start[0], mpl_end[0]], [mpl_start[1], mpl_end[1]], [mpl_start[2], mpl_end[2]],
                color=Color.RED.value, linestyle=LineStyle.DASHED.value, lw=3,
                label=f'Obstruction {angle_degrees:.1f}°')

    @staticmethod
    def add_projection_line(ax, original: np.ndarray, projected: np.ndarray):
        """Add line showing projection from mesh to plane"""
        
        mpl_orig = CoordinateTransform.calc_to_mpl(original)
        
        mpl_proj = CoordinateTransform.calc_to_mpl(projected)
        ax.plot([mpl_orig[0], mpl_proj[0]], [mpl_orig[1], mpl_proj[1]], [mpl_orig[2], mpl_proj[2]],
                color=Color.BLUE.value, linestyle=LineStyle.DASHED.value, lw=2, alpha=0.8,
                label=PlotLabel.PROJECTION.value)


class ZenithVisualizationHelper:
    """Helper for zenith angle visualization components"""

    @staticmethod
    def project_point_onto_direction_plane(point: np.ndarray, window_center: np.ndarray,
                                          direction_vec: np.ndarray) -> np.ndarray:
        """
        Project a 3D point onto the direction plane

        The direction plane is perpendicular to (direction × world_up)
        """
        world_up = np.array([0.0, 0.0, 1.0])  # Z-up coordinate system
        plane_normal = np.cross(direction_vec, world_up)
        plane_normal_mag = np.linalg.norm(plane_normal)

        if plane_normal_mag < 1e-6:
            # Looking straight up/down, no projection needed
            return point

        plane_normal = plane_normal / plane_normal_mag

        # Project point onto plane
        point_to_window = point - window_center
        dist_to_plane = np.dot(point_to_window, plane_normal)
        projected_point = point - dist_to_plane * plane_normal

        return projected_point

    @staticmethod
    def calculate_horizontal_reference_point(projected_point: np.ndarray,
                                            window_center: np.ndarray) -> np.ndarray:
        """
        Calculate horizontal reference point (same X,Y as projected point, same Z as window)
        Z-up coordinate system: horizontal plane is XY (constant Z)
        """
        return np.array([projected_point[0], projected_point[1], window_center[2]])


class ZenithPlotRenderer:
    """Render zenith angle visualization elements"""

    @staticmethod
    def add_overhead_point(ax, point: np.ndarray, label: str = PlotLabel.FURTHEST_OVERHEAD.value):
        """Add overhead obstruction point marker"""
        print("overhead ", point)
        mpl_pos = CoordinateTransform.calc_to_mpl(point)
        print("overhead converted", mpl_pos)
        ax.scatter(mpl_pos[0], mpl_pos[1], mpl_pos[2],
                   c=Color.RED.value, s=150, marker=Marker.CIRCLE.value, label=label,
                   edgecolors=Color.BLACK.value, linewidths=2)

    @staticmethod
    def add_api_point(ax, point: np.ndarray):
        """Add original API point marker (off-plane)"""
        print("api ", point)
        # mpl_pos = CoordinateTransform.calc_to_mpl(point)
        # print("api converted", mpl_pos)
        ax.scatter(point[0], point[1], point[2],
                   c=Color.ORANGE.value, s=100, marker=Marker.CROSS.value,
                   label=PlotLabel.API_POINT_OFF_PLANE.value, linewidths=2)

    @staticmethod
    def add_zenith_line(ax, window_pos: np.ndarray, overhead_point: np.ndarray, angle_degrees: float):
        """Add zenith line from window to overhead point"""
        print("window pos ", window_pos)
        print("ovhd pnt ", overhead_point)
        mpl_win = window_pos # CoordinateTransform.calc_to_mpl(window_pos)
        mpl_point = overhead_point #CoordinateTransform.calc_to_mpl(overhead_point)
        # print("window pos converted", mpl_win)
        # print("ovhd pnt converted", mpl_point)
        ax.plot([mpl_win[0], mpl_point[0]],
                [mpl_win[1], mpl_point[1]],
                [mpl_win[2], mpl_point[2]],
                color=Color.RED.value, linestyle=LineStyle.DASHED.value, linewidth=3,
                label=f'Zenith line: {angle_degrees:.1f}°')

    @staticmethod
    def add_horizontal_reference(ax, window_pos: np.ndarray, horizontal_ref_point: np.ndarray):
        """Add horizontal reference line (parallel to XY plane)"""
        print("window pos ", window_pos)
        print("hr pnt ", horizontal_ref_point)
        mpl_win = window_pos #CoordinateTransform.calc_to_mpl(window_pos)
        mpl_ref = horizontal_ref_point #CoordinateTransform.calc_to_mpl(horizontal_ref_point)
        # print("window pos converted", mpl_win)
        # print("href pnt converted", mpl_ref)
        ax.plot([mpl_win[0], mpl_ref[0]],
                [mpl_win[1], mpl_ref[1]],
                [mpl_win[2], mpl_ref[2]],
                color=Color.GREEN.value, linestyle=LineStyle.SOLID.value, linewidth=2.5, alpha=0.8,
                label=PlotLabel.HORIZONTAL_REFERENCE.value)
        ax.scatter(mpl_ref[0], mpl_ref[1], mpl_ref[2],
                   c=Color.GREEN.value, s=100, marker=Marker.SQUARE.value,
                   edgecolors=Color.BLACK.value, linewidths=1)

    @staticmethod
    def add_vertical_component(ax, horizontal_ref_point: np.ndarray, overhead_point: np.ndarray):
        """Add vertical component line (parallel to Z axis)"""
        mpl_ref = CoordinateTransform.calc_to_mpl(horizontal_ref_point)
        mpl_point = CoordinateTransform.calc_to_mpl(overhead_point)
        ax.plot([mpl_ref[0], mpl_point[0]],
                [mpl_ref[1], mpl_point[1]],
                [mpl_ref[2], mpl_point[2]],
                color=Color.BLUE.value, linestyle=LineStyle.SOLID.value, linewidth=2.5, alpha=0.8,
                label=PlotLabel.VERTICAL_COMPONENT.value)


class VisualizationFactory:
    """Factory for creating visualization components"""

    @staticmethod
    def create_projection_components(window_center: List[float], direction_angle: float):
        """
        Create all components needed for projection visualization

        Args:
            window_center: [x, y, z] window position
            direction_angle: Horizontal rotation angle in radians

        Returns:
            (direction_vec, horizontal_dir, plane_builder, mesh_projector)
        """
        calc = DirectionVectorCalculator()
        direction_vec = calc.from_horizontal_angle(direction_angle)
        horizontal_dir = calc.get_horizontal_component(direction_vec)

        plane_builder = ProjectionPlaneBuilder(window_center, horizontal_dir)
        mesh_projector = MeshProjector(plane_builder)

        return direction_vec, horizontal_dir, plane_builder, mesh_projector


class HorizonAngleVisualizer:
    """Complete horizon angle visualization orchestrator"""

    def __init__(self, window_center: List[float], direction_angle: float,
                 mesh_vertices: List[List[float]], building_dimensions: Tuple[float, float, float]):
        """
        Initialize visualizer with scene parameters

        Args:
            window_center: [x, y, z] position of window
            direction_angle: Horizontal rotation angle in radians
            mesh_vertices: List of mesh triangle vertices
            building_dimensions: (distance, height, width) for axis scaling
        """
        self.window_center = window_center
        self.direction_angle = direction_angle
        self.mesh_vertices = mesh_vertices
        self.building_dist, self.building_height, self.building_width = building_dimensions

    def visualize(self, ax, highest_point: dict, obstruction_angle: float):
        """
        Create complete horizon angle visualization

        Args:
            ax: Matplotlib 3D axis
            highest_point: Dict with 'x', 'y', 'z' keys from API response
            obstruction_angle: Angle in degrees from API response
        """
        # Create visualization components
        dir_vec, dir_h, plane_builder, mesh_projector = VisualizationFactory.create_projection_components(
            self.window_center, self.direction_angle)

        # Setup renderer
        renderer = PlotElementRenderer()

        # Add basic elements
        renderer.add_window(ax, self.window_center)
        renderer.add_mesh(ax, self.mesh_vertices)
        renderer.add_viewing_direction(ax, self.window_center, dir_vec, self.building_dist)
        renderer.add_projection_plane(ax, plane_builder, width=12,
                                     height_range=(-2, self.building_height + 2))

        # Add highest point and lines if exists
        if highest_point:
            print("highest point", highest_point)
            hp_3d = np.array([highest_point['x'], highest_point['y'], highest_point['z']])
            print("HP3D", hp_3d)
            hp_proj = plane_builder.project_point(hp_3d)
            print("HP_porj", hp_proj)
            renderer.add_highest_point(ax, hp_proj)
            renderer.add_obstruction_line(ax, self.window_center, hp_proj, obstruction_angle)

            # Calculate point along view direction from window
            view_point = np.array(self.window_center) + dir_vec * self.building_dist
            renderer.add_projection_line(ax, view_point, hp_proj)

        # Configure axes
        max_range = max(self.building_dist, self.building_height, self.building_width)
        AxisConfigurator.setup(ax, max_range=max_range,
                              title=f'Horizon Angle: {obstruction_angle:.1f}°')
        ax.legend(fontsize=8)


class ZenithAngleVisualizer:
    """Complete zenith angle visualization orchestrator"""

    def __init__(self, window_center: List[float], direction_angle: float,
                 mesh_vertices: List[List[float]], scene_dimensions: Tuple[float, float, float]):
        """
        Initialize visualizer with scene parameters

        Args:
            window_center: [x, y, z] position of window
            direction_angle: Horizontal rotation angle in radians
            mesh_vertices: List of mesh triangle vertices
            scene_dimensions: (distance, height, width) for axis scaling
        """
        self.window_center = np.array(window_center)
        self.direction_angle = direction_angle
        self.mesh_vertices = mesh_vertices
        self.scene_dist, self.scene_height, self.scene_width = scene_dimensions

    def visualize(self, ax, overhead_point: dict, zenith_angle: float):
        """
        Create complete zenith angle visualization

        Args:
            ax: Matplotlib 3D axis
            overhead_point: Dict with 'x', 'y', 'z' keys from API response
            zenith_angle: Angle in degrees from API response
        """
        # Create visualization components
        dir_vec, _, plane_builder, _ = VisualizationFactory.create_projection_components(
            self.window_center.tolist(), self.direction_angle)

        # Setup renderers
        base_renderer = PlotElementRenderer()
        zenith_renderer = ZenithPlotRenderer()
        zenith_helper = ZenithVisualizationHelper()

        # Add basic scene elements
        base_renderer.add_window(ax, self.window_center.tolist())
        base_renderer.add_mesh(ax, self.mesh_vertices)
        base_renderer.add_viewing_direction(ax, self.window_center.tolist(), dir_vec,
                                           self.scene_dist + 3)
        base_renderer.add_projection_plane(ax, plane_builder, width=10,
                                          height_range=(-2, self.scene_height + 2))

        # Process and render overhead point
        if overhead_point and zenith_angle > 0:
            print("OVERHEAD", overhead_point)
            lp_3d = np.array([overhead_point['x'], overhead_point['y'], overhead_point['z']])
            print("LP3D", lp_3d)

            # Project point onto direction plane
            projected_point = zenith_helper.project_point_onto_direction_plane(
                lp_3d, self.window_center, dir_vec)
            horizontal_ref = zenith_helper.calculate_horizontal_reference_point(
                projected_point, self.window_center)

            # Show API point if off-plane
            dist_to_plane = np.linalg.norm(lp_3d - projected_point)
            if dist_to_plane > 0.01:
                zenith_renderer.add_api_point(ax, lp_3d)

            # Add zenith visualization elements
            zenith_renderer.add_overhead_point(ax, projected_point)
            zenith_renderer.add_zenith_line(ax, self.window_center, projected_point, zenith_angle)
            zenith_renderer.add_horizontal_reference(ax, self.window_center, horizontal_ref)
            zenith_renderer.add_vertical_component(ax, horizontal_ref, projected_point)

        # Configure axes
        max_range = max(self.scene_dist + 3, self.scene_height, self.scene_width)
        AxisConfigurator.setup(ax, max_range=max_range,
                              title=f'Overhead Obstruction - Zenith Angle: {zenith_angle:.1f}°')
        ax.legend(fontsize=8, loc='upper right')


class DualAngleVisualizer:
    """Dual visualization showing both horizon and zenith angles side-by-side"""

    def __init__(self, window_center: List[float], direction_angle: float,
                 mesh_vertices: List[List[float]], building_dimensions: Tuple[float, float, float]):
        """
        Initialize dual visualizer

        Args:
            window_center: [x, y, z] position of window
            direction_angle: Horizontal rotation angle in radians
            mesh_vertices: List of mesh triangle vertices
            building_dimensions: (distance, height, width) for axis scaling
        """
        self.horizon_viz = HorizonAngleVisualizer(
            window_center, direction_angle, mesh_vertices, building_dimensions)
        self.zenith_viz = ZenithAngleVisualizer(
            window_center, direction_angle, mesh_vertices, building_dimensions)

    def visualize(self, fig, horizon_data: dict, zenith_data: dict):
        """
        Create side-by-side visualization of both angles

        Args:
            fig: Matplotlib figure (should be created with figsize=(18, 8) or larger)
            horizon_data: Dict with 'obstruction_angle_degrees' and 'highest_point'
            zenith_data: Dict with 'obstruction_angle_degrees' and 'highest_point'
        """
        # Create two subplots
        ax1 = fig.add_subplot(121, projection='3d')
        ax2 = fig.add_subplot(122, projection='3d')

        # Render horizon angle on left
        self.horizon_viz.visualize(
            ax1,
            horizon_data.get('highest_point'),
            horizon_data.get('obstruction_angle_degrees', 0.0)
        )

        # Render zenith angle on right
        self.zenith_viz.visualize(
            ax2,
            zenith_data.get('highest_point'),
            zenith_data.get('obstruction_angle_degrees', 0.0)
        )

        # Add overall title
        horizon_angle = horizon_data.get('obstruction_angle_degrees', 0.0)
        zenith_angle = zenith_data.get('obstruction_angle_degrees', 0.0)
        sum_angle = horizon_angle + zenith_angle

        fig.suptitle(
            f'Horizon: {horizon_angle:.1f}° + Zenith: {zenith_angle:.1f}° = {sum_angle:.1f}°',
            fontsize=16, fontweight='bold', y=0.98
        )


class TopViewVisualizer:
    """Top-down view visualizer showing XZ plane"""

    def __init__(self, window_center: List[float], direction_angle: float):
        """
        Initialize top view visualizer

        Args:
            window_center: [x, y, z] position of window
            direction_angle: Horizontal rotation angle in radians
        """
        self.window_center = np.array(window_center)
        self.direction_angle = direction_angle

    def visualize(self, ax, view_distance: float = 10.0, plane_width: float = 8.0):
        """
        Create top-down view showing direction plane

        Args:
            ax: Matplotlib 2D axis
            view_distance: How far to extend the viewing direction
            plane_width: Width of direction plane to show
        """
        # Calculate direction vector
        calc = DirectionVectorCalculator()
        dir_vec = calc.from_horizontal_angle(self.direction_angle)

        # Calculate plane normal (perpendicular to direction in horizontal plane)
        world_up = np.array([0.0, 0.0, 1.0])  # Z-up coordinate system
        plane_normal = np.cross(dir_vec, world_up)
        plane_normal_mag = np.linalg.norm(plane_normal)

        if plane_normal_mag > 1e-6:
            plane_normal = plane_normal / plane_normal_mag
        else:
            # Direction is vertical, use default perpendicular
            plane_normal = np.array([0.0, 1.0, 0.0])
            

        # Draw window
        ax.scatter(self.window_center[0], self.window_center[1],
                  c=Color.RED.value, s=300, marker=Marker.CIRCLE.value,
                  label=PlotLabel.WINDOW.value, edgecolors=Color.BLACK.value,
                  linewidths=2, zorder=5)

        # Draw viewing direction arrow
        ax.arrow(self.window_center[0], self.window_center[1],
                dir_vec[0] * view_distance, dir_vec[1] * view_distance,
                head_width=0.5, head_length=0.5, fc=Color.MAGENTA.value, ec=Color.MAGENTA.value,
                linewidth=2, label=PlotLabel.VIEW_DIRECTION.value, zorder=4)

        # Draw direction plane (as a line in top view, since plane is vertical)
        # Plane extends perpendicular to viewing direction
        plane_start = self.window_center + plane_normal * (plane_width / 2)
        plane_end = self.window_center - plane_normal * (plane_width / 2)

        ax.plot([plane_start[0], plane_end[0]], [plane_start[1], plane_end[1]],
               color=Color.GREEN.value, linestyle=LineStyle.SOLID.value, linewidth=3,
               alpha=0.7, label=PlotLabel.DIRECTION_PLANE.value, zorder=3)

        # Extend plane forward along viewing direction
        plane_length = view_distance + 5
        for offset in [-plane_width/2, 0, plane_width/2]:
            p1 = self.window_center + plane_normal * offset
            p2 = p1 + dir_vec * plane_length
            alpha = 0.7 if offset == 0 else 0.3
            lw = 3 if offset == 0 else 1
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
                   color=Color.GREEN.value, linestyle=LineStyle.SOLID.value,
                   linewidth=lw, alpha=alpha, zorder=2)

        # Configure axes
        ax.set_xlabel(AxisLabel.X_METERS.value, fontsize=12, fontweight='bold')
        ax.set_ylabel(AxisLabel.Y_METERS.value, fontsize=12, fontweight='bold')
        ax.set_title('Top View (Looking Down at XY Plane)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.axis('equal')
        ax.legend(fontsize=10, loc='upper right')

        # Set axis limits
        margin = 3
        ax.set_xlim(self.window_center[0] - margin, self.window_center[0] + view_distance + margin)
        ax.set_ylim(self.window_center[1] - plane_width, self.window_center[1] + plane_width)


class CombinedObstructionVisualizer:
    """
    Visualize both horizon and zenith angles on a single 3D plot

    Displays vertical and horizontal obstructions together, showing:
    - Window position and viewing direction
    - Mesh geometry
    - Projection plane
    - Horizon angle line (red, for vertical surfaces)
    - Zenith angle line (magenta, for horizontal surfaces)
    """

    def __init__(self, window_center: list, direction_angle: float, mesh_vertices: list):
        """
        Initialize combined obstruction visualizer

        Args:
            window_center: [x, y, z] window center position
            direction_angle: Horizontal rotation angle in radians
            mesh_vertices: List of mesh vertices (triangles)
        """
        self.window_center = window_center
        self.direction_angle = direction_angle
        self.mesh_vertices = mesh_vertices

    def visualize(self, ax, horizon_data: dict, zenith_data: dict):
        """
        Create combined visualization of both obstruction angles

        Args:
            ax: Matplotlib 3D axis
            horizon_data: Horizon angle response data from API
            zenith_data: Zenith angle response data from API
        """
        # Calculate direction vectors and plane
        calc = DirectionVectorCalculator()
        dir_vec = calc.from_horizontal_angle(self.direction_angle)
        horizontal_dir = calc.get_horizontal_component(dir_vec)
        plane_builder = ProjectionPlaneBuilder(self.window_center, horizontal_dir)

        # Setup renderer
        renderer = PlotElementRenderer()

        # Add basic scene elements
        renderer.add_window(ax, self.window_center)
        renderer.add_mesh(ax, self.mesh_vertices)

        # Calculate max range for viewing direction
        max_x = max(v[0] for v in self.mesh_vertices)
        max_y = max(v[1] for v in self.mesh_vertices)
        view_distance = max(max_x, 10.0)

        renderer.add_viewing_direction(ax, self.window_center, dir_vec, view_distance)
        renderer.add_projection_plane(ax, plane_builder, width=12,
                                     height_range=(-2, max_y + 2))

        # Extract angles
        horizon_angle = horizon_data["obstruction_angle_degrees"]
        zenith_angle = zenith_data["obstruction_angle_degrees"]

        # Add horizon angle visualization (if exists)
        if horizon_angle > 0 and horizon_data.get('highest_point'):
            hp = horizon_data['highest_point']
            
            hp_3d = np.array([hp['x'], hp['y'], hp['z']])
            hp_proj = plane_builder.project_point(hp_3d)
            mpl_hp = CoordinateTransform.calc_to_mpl(hp_proj)

            # Add highest point marker (orange triangle)
            ax.scatter(mpl_hp[0], mpl_hp[1], mpl_hp[2],
                      c=Color.ORANGE.value, s=150, marker=Marker.TRIANGLE_UP.value,
                      label=f'Horizon: {horizon_angle:.1f}°',
                      edgecolors=Color.BLACK.value, lw=2)

            # Add horizon line (red dashed)
            mpl_win = CoordinateTransform.calc_to_mpl(self.window_center)
            ax.plot([mpl_win[0], mpl_hp[0]],
                   [mpl_win[1], mpl_hp[1]],
                   [mpl_win[2], mpl_hp[2]],
                   color=Color.RED.value, linestyle=LineStyle.DASHED.value,
                   lw=3, label=f'Vertical obstruction')

        # Add zenith angle visualization (if exists)
        if zenith_angle > 0 and zenith_data.get('highest_point'):
            zp = zenith_data['highest_point']
            zp_3d = np.array([zp['x'], zp['y'], zp['z']])
            zp_proj = plane_builder.project_point(zp_3d)
            mpl_zp = CoordinateTransform.calc_to_mpl(zp_proj)

            # Add furthest overhead point marker (magenta circle)
            ax.scatter(mpl_zp[0], mpl_zp[1], mpl_zp[2],
                      c=Color.MAGENTA.value, s=150, marker=Marker.CIRCLE.value,
                      label=f'Zenith: {zenith_angle:.1f}°',
                      edgecolors=Color.BLACK.value, lw=2)

            # Add zenith line (magenta dashed)
            mpl_win = CoordinateTransform.calc_to_mpl(self.window_center)
            ax.plot([mpl_win[0], mpl_zp[0]],
                   [mpl_win[1], mpl_zp[1]],
                   [mpl_win[2], mpl_zp[2]],
                   color=Color.MAGENTA.value, linestyle=LineStyle.DASHED.value,
                   lw=3, label=f'Horizontal obstruction')

        # Configure axes
        max_range = max(view_distance, max_y, 15.0)
        title = f'Combined Obstruction: H={horizon_angle:.1f}° + Z={zenith_angle:.1f}°'

        AxisConfigurator.setup(ax, max_range=max_range, title=title)
        ax.legend(fontsize=10, loc='upper right')


class MeshExporter:
    """Export mesh data to various file formats"""

    @staticmethod
    def to_obj(mesh_vertices: list, output_path: str, window_center: list = None) -> None:
        """
        Export mesh vertices to Wavefront OBJ file format

        Args:
            mesh_vertices: List of vertices forming triangles [[x1,y1,z1], [x2,y2,z2], [x3,y3,z3], ...]
            output_path: Path to save the OBJ file
            window_center: Optional window position to include as a comment
        """
        with open(output_path, 'w') as f:
            # Write header
            f.write("# Wavefront OBJ file\n")
            f.write("# Generated from obstruction calculation mesh data\n")

            if window_center:
                f.write(f"# Window position: {window_center[0]}, {window_center[1]}, {window_center[2]}\n")

            f.write(f"# Vertices: {len(mesh_vertices)}\n")
            f.write(f"# Triangles: {len(mesh_vertices) // 3}\n\n")

            # Write vertices
            for vertex in mesh_vertices:
                f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")

            f.write("\n")

            # Write faces (groups of 3 vertices form triangles)
            # OBJ uses 1-based indexing
            for i in range(0, len(mesh_vertices), 3):
                v1, v2, v3 = i + 1, i + 2, i + 3
                f.write(f"f {v1} {v2} {v3}\n")

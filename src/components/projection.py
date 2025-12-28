from abc import ABC, abstractmethod
from typing import List
import numpy as np
from src.components.geometry import Point3D, Vector3D, Mesh, CoordinateSystem
from src.components.obstruction_models import Window, ProjectionPlane, ProjectedPoint
from src.components.constants import MathConstants


class IProjectionCalculator(ABC):
    """Interface for projection calculations"""

    @abstractmethod
    def create_projection_plane(self, window: Window) -> ProjectionPlane:
        """
        Create a vertical projection plane from window definition

        Args:
            window: Window with center point and normal direction

        Returns:
            ProjectionPlane definition
        """
        pass

    @abstractmethod
    def project_point(self, point: Point3D, plane: ProjectionPlane) -> ProjectedPoint:
        """
        Project a 3D point onto the projection plane

        Args:
            point: 3D point to project
            plane: Projection plane

        Returns:
            ProjectedPoint with 2D coordinates on plane
        """
        pass

    @abstractmethod
    def project_mesh(self, mesh: Mesh, plane: ProjectionPlane) -> List[ProjectedPoint]:
        """
        Project all mesh points onto the projection plane

        Args:
            mesh: 3D mesh
            plane: Projection plane

        Returns:
            List of projected points
        """
        pass


class OrthographicProjectionCalculator(IProjectionCalculator):
    """
    Static orthographic projection calculator

    Projects 3D geometry onto a vertical plane using orthographic projection.
    The plane is vertical and contains the window's viewing direction.

    All methods are classmethods (no instance state).
    """

    @classmethod
    def create_projection_plane(cls, window: Window) -> ProjectionPlane:
        """
        Create vertical projection plane from window

        The plane:
        - Passes through the window center point
        - CONTAINS the window direction vector (viewing direction lies in the plane)
        - Is vertical (contains the world up vector)
        - The plane's geometric normal is perpendicular to both the viewing direction and world up
        """
        direction = window.normal  # Window viewing direction

        # Calculate plane normal (perpendicular to both viewing direction and world up)
        plane_normal = ProjectionPlane.calculate_plane_normal(direction)

        # Calculate u-axis (horizontal component of viewing direction)
        u_axis_arr = cls._calculate_horizontal_component(direction.to_array())
        u_axis = Vector3D.from_array(u_axis_arr)

        # The vertical axis is always world up
        v_axis = Vector3D.from_array(CoordinateSystem.UP)

        return ProjectionPlane(
            origin=window.center,
            u_axis=u_axis,
            v_axis=v_axis,
            normal=plane_normal  # Geometric normal to the plane
        )

    @classmethod
    def _calculate_horizontal_component(cls, direction_arr: np.ndarray) -> np.ndarray:
        """
        Extract horizontal component of direction vector

        Args:
            direction_arr: Direction vector

        Returns:
            Normalized horizontal component (vertical removed)
        """
        direction_horizontal = CoordinateSystem.remove_vertical_component(direction_arr)
        direction_horizontal_mag = np.linalg.norm(direction_horizontal)

        if direction_horizontal_mag > MathConstants.EPSILON.value:
            return direction_horizontal / direction_horizontal_mag

        # Viewing straight up/down, use default forward direction
        return CoordinateSystem.FORWARD.copy()

    @classmethod
    def project_point(cls, point: Point3D, plane: ProjectionPlane) -> ProjectedPoint:
        """
        Project point onto plane using orthographic projection

        The projection is done by:
        1. Translating point relative to plane origin
        2. Projecting onto plane by dotting with basis vectors
        """
        # Vector from plane origin to point
        point_arr = point.to_array()
        origin_arr = plane.origin.to_array()
        relative = point_arr - origin_arr

        # Project onto plane axes
        u = float(np.dot(relative, plane.u_axis.to_array()))
        v = float(np.dot(relative, plane.v_axis.to_array()))

        return ProjectedPoint(u=u, v=v, original=point)

    @classmethod
    def project_mesh(cls, mesh: Mesh, plane: ProjectionPlane) -> List[ProjectedPoint]:
        """Project all mesh vertices onto the plane"""
        points = mesh.get_all_points()
        return [cls.project_point(point, plane) for point in points]

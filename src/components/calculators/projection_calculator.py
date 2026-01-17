from typing import List
import numpy as np
from src.components.geometry import Point3D, Vector3D, Mesh, CoordinateSystem, ProjectionPlane, ProjectedPoint
from src.components.models import Window
from src.server.base.constants import MathConstants


class OrthographicProjectionCalculator:
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

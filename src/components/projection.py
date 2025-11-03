from abc import ABC, abstractmethod
from typing import List
import numpy as np
from src.components.geometry import Point3D, Vector3D, Mesh
from src.components.raytracing_models import Window, ProjectionPlane, ProjectedPoint


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
    Orthographic projection calculator

    Projects 3D geometry onto a vertical plane using orthographic projection.
    The plane is perpendicular to the window's normal direction.
    """

    def create_projection_plane(self, window: Window) -> ProjectionPlane:
        """
        Create vertical projection plane from window

        The plane:
        - Passes through the window center point
        - Is perpendicular to the window normal
        - Has a vertical v-axis (pointing up in world space)
        - Has a horizontal u-axis (perpendicular to both normal and v-axis)
        """
        # World up vector
        world_up = Vector3D(x=0.0, y=1.0, z=0.0)
        normal_arr = window.normal.to_array()
        world_up_arr = world_up.to_array()

        # Calculate horizontal axis (u) - perpendicular to normal and world_up
        u_axis_arr = np.cross(world_up_arr, normal_arr)
        u_axis_mag = np.linalg.norm(u_axis_arr)

        if u_axis_mag < 1e-6:
            # Normal is parallel to world up, use a different reference
            world_forward = Vector3D(x=0.0, y=0.0, z=1.0)
            u_axis_arr = np.cross(world_forward.to_array(), normal_arr)

        u_axis_arr = u_axis_arr / np.linalg.norm(u_axis_arr)
        u_axis = Vector3D.from_array(u_axis_arr)

        # Calculate vertical axis (v) - perpendicular to normal and u_axis
        v_axis_arr = np.cross(normal_arr, u_axis_arr)
        v_axis_arr = v_axis_arr / np.linalg.norm(v_axis_arr)
        v_axis = Vector3D.from_array(v_axis_arr)

        return ProjectionPlane(
            origin=window.center,
            u_axis=u_axis,
            v_axis=v_axis,
            normal=window.normal
        )

    def project_point(self, point: Point3D, plane: ProjectionPlane) -> ProjectedPoint:
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

    def project_mesh(self, mesh: Mesh, plane: ProjectionPlane) -> List[ProjectedPoint]:
        """Project all mesh vertices onto the plane"""
        points = mesh.get_all_points()
        return [self.project_point(point, plane) for point in points]

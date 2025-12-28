"""Triangle processing classes for mesh filtering and sorting"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from enum import Enum
import numpy as np
from src.components.obstruction_models import ProjectedPoint, ProjectionPlane
from src.components.geometry import Point3D, Vector3D, CoordinateSystem
from src.components.constants import MathConstants


class TriangleOrientation(Enum):
    """Triangle surface orientation types"""
    VERTICAL = "vertical"      # Walls, vertical surfaces
    HORIZONTAL = "horizontal"  # Roofs, floors
    SLANTED = "slanted"       # Neither vertical nor horizontal


class Triangle:
    """Represents a triangle with its three vertices"""

    def __init__(self, points: List[ProjectedPoint]):
        """
        Initialize triangle from three projected points

        Args:
            points: List of exactly 3 ProjectedPoint objects
        """
        if len(points) != 3:
            raise ValueError("Triangle must have exactly 3 points")
        self.points = points

    def get_vertices(self) -> List[Point3D]:
        """Get 3D vertices of the triangle"""
        return [p.original for p in self.points]

    def get_vertex_arrays(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get triangle vertices as numpy arrays"""
        vertices = self.get_vertices()
        return (vertices[0].to_array(),
                vertices[1].to_array(),
                vertices[2].to_array())

    def calculate_normal(self) -> np.ndarray:
        """
        Calculate surface normal vector of the triangle

        Returns:
            Normalized normal vector
        """
        p0, p1, p2 = self.get_vertex_arrays()
        edge1 = p1 - p0
        edge2 = p2 - p0
        normal = np.cross(edge1, edge2)
        magnitude = np.linalg.norm(normal)

        if magnitude < MathConstants.EPSILON.value:
            # Degenerate triangle
            return CoordinateSystem.UP.copy()

        return normal / magnitude

    def get_orientation(self, vertical_threshold: float = 0.1) -> TriangleOrientation:
        """
        Determine if triangle is vertical, horizontal, or slanted

        Args:
            vertical_threshold: Threshold for vertical dot product (default 0.1)

        Returns:
            Triangle orientation type
        """
        normal = self.calculate_normal()
        vertical_component = abs(CoordinateSystem.get_vertical_component(normal))

        if vertical_component < vertical_threshold:
            # Normal is nearly horizontal -> surface is vertical
            return TriangleOrientation.VERTICAL
        elif vertical_component > (1.0 - vertical_threshold):
            # Normal is nearly vertical -> surface is horizontal
            return TriangleOrientation.HORIZONTAL
        else:
            return TriangleOrientation.SLANTED

    def get_highest_point(self) -> ProjectedPoint:
        """Get the point with maximum vertical coordinate"""
        return max(self.points, key=lambda p: p.original.get_vertical())

    def get_average_height(self) -> float:
        """Calculate average vertical coordinate of vertices"""
        return sum(p.original.get_vertical() for p in self.points) / 3

    def get_centroid(self) -> Point3D:
        """Calculate triangle centroid"""
        vertices = self.get_vertices()
        x = sum(v.x for v in vertices) / 3
        y = sum(v.y for v in vertices) / 3
        z = sum(v.z for v in vertices) / 3
        return Point3D(x=x, y=y, z=z)


class ITriangleFilter(ABC):
    """Interface for filtering triangles based on criteria"""

    @abstractmethod
    def filter(self, triangles: List[Triangle]) -> List[Triangle]:
        """
        Filter triangles based on specific criteria

        Args:
            triangles: Input list of triangles

        Returns:
            Filtered list of triangles
        """
        pass


class PlaneIntersectionFilter(ITriangleFilter):
    """Filters triangles that intersect a given plane"""

    def __init__(self, window_center: Point3D, window_normal: Vector3D,
                 plane_normal: np.ndarray, threshold: float = 0.1):
        """
        Initialize plane intersection filter

        Args:
            window_center: Window center position
            window_normal: Window viewing direction
            plane_normal: Normal vector of the vertical plane
            threshold: Distance threshold for plane intersection
        """
        self.window_center = window_center
        self.window_normal = window_normal
        self.plane_normal = plane_normal
        self.threshold = threshold
        self.window_arr = window_center.to_array()
        self.normal_arr = window_normal.to_array()

    def filter(self, triangles: List[Triangle]) -> List[Triangle]:
        """Filter triangles that intersect the projection plane"""
        return [tri for tri in triangles if self._intersects_plane(tri)]

    def _intersects_plane(self, triangle: Triangle) -> bool:
        """Check if triangle intersects the plane"""
        # Check if all vertices are in front of window
        if not self._all_vertices_in_front(triangle):
            return False

        # Calculate signed distances to plane for each vertex
        signed_distances = self._calculate_signed_distances(triangle)

        # Triangle intersects if vertices span the plane
        min_dist = min(signed_distances)
        max_dist = max(signed_distances)

        return min_dist < self.threshold and max_dist > -self.threshold

    def _all_vertices_in_front(self, triangle: Triangle) -> bool:
        """Check if all vertices are in front of the window"""
        for point in triangle.points:
            point_arr = point.original.to_array()
            point_to_window = point_arr - self.window_arr
            dist_along_view = float(np.dot(point_to_window, self.normal_arr))

            if dist_along_view <= MathConstants.EPSILON:
                return False

        return True

    def _calculate_signed_distances(self, triangle: Triangle) -> List[float]:
        """Calculate signed distances from vertices to plane"""
        distances = []
        for point in triangle.points:
            point_arr = point.original.to_array()
            point_to_window = point_arr - self.window_arr
            dist_to_plane = float(np.dot(point_to_window, self.plane_normal))
            distances.append(dist_to_plane)

        return distances


class OrientationFilter(ITriangleFilter):
    """Filters triangles by surface orientation"""

    def __init__(self, orientation: TriangleOrientation, vertical_threshold: float = 0.1):
        """
        Initialize orientation filter

        Args:
            orientation: Desired triangle orientation
            vertical_threshold: Threshold for vertical detection
        """
        self.orientation = orientation
        self.vertical_threshold = vertical_threshold

    def filter(self, triangles: List[Triangle]) -> List[Triangle]:
        """Filter triangles matching the desired orientation"""
        return [tri for tri in triangles
                if tri.get_orientation(self.vertical_threshold) == self.orientation]


class AboveWindowFilter(ITriangleFilter):
    """Filters triangles that are above the window"""

    def __init__(self, window_center: Point3D):
        """
        Initialize above window filter

        Args:
            window_center: Window center position
        """
        self.window_center = window_center

    def filter(self, triangles: List[Triangle]) -> List[Triangle]:
        """Filter triangles where all vertices are above window"""
        return [
            tri for tri in triangles
            if all(
                p.original.get_vertical() > self.window_center.get_vertical()
                for p in tri.points
            )
        ]


class UpperForwardQuarterFilter(ITriangleFilter):
    """
    Filters triangles in the upper forward quarter

    Only keeps triangles where at least one vertex is in the region:
    - In front of the window (positive dot product with viewing direction)
    - Above the window (positive vertical distance)

    This is the only region where obstructions can affect both horizon and zenith angles.
    """

    def __init__(self, window_center: Point3D, window_normal: Vector3D):
        """
        Initialize upper forward quarter filter

        Args:
            window_center: Window center position
            window_normal: Window viewing direction (unit vector)
        """
        self.window_center = window_center
        self.window_normal = window_normal

    def filter(self, triangles: List[Triangle]) -> List[Triangle]:
        """
        Filter triangles with at least one vertex in upper forward quarter

        A point is in the upper forward quarter if:
        1. It's above the window (vertical component > window vertical)
        2. It's in front of the window (dot product with view direction > 0)
        """
        window_arr = self.window_center.to_array()
        normal_arr = self.window_normal.to_array()
        window_vertical = self.window_center.get_vertical()

        filtered = []
        for triangle in triangles:
            # Check if any vertex is in the upper forward quarter
            for point in triangle.points:
                point_arr = point.original.to_array()

                # Check if above window
                if point.original.get_vertical() <= window_vertical:
                    continue

                # Check if in front of window (positive distance along view direction)
                # IMPORTANT: This filters out obstructions directly above (perpendicular to view)
                # because dot product of perpendicular vectors = 0, and we require > 0
                # Example: Window facing East [1,0,0], point directly above [0,0,height]
                #          dot([0,0,height], [1,0,0]) = 0, which fails > 0 test
                point_to_window = point_arr - window_arr
                dist_along_view = float(np.dot(point_to_window, normal_arr))

                if dist_along_view > 0:
                    # At least one vertex is in upper forward quarter
                    filtered.append(triangle)
                    break

        return filtered


class ITriangleSorter(ABC):
    """Interface for sorting triangles"""

    @abstractmethod
    def sort(self, triangles: List[Triangle]) -> List[Triangle]:
        """
        Sort triangles based on specific criteria

        Args:
            triangles: Input list of triangles

        Returns:
            Sorted list of triangles
        """
        pass


class HeightSorter(ITriangleSorter):
    """Sorts triangles by height (for horizon angle calculation)"""

    def __init__(self, descending: bool = True):
        """
        Initialize height sorter

        Args:
            descending: If True, sort from highest to lowest (default)
        """
        self.descending = descending

    def sort(self, triangles: List[Triangle]) -> List[Triangle]:
        """Sort triangles by their highest point's vertical coordinate"""
        return sorted(triangles,
                     key=lambda tri: tri.get_highest_point().original.get_vertical(),
                     reverse=self.descending)


class DistanceSorter(ITriangleSorter):
    """Sorts triangles by horizontal distance from view direction"""

    def __init__(self, window_center: Point3D, window_normal: Vector3D,
                 ascending: bool = True):
        """
        Initialize distance sorter

        Args:
            window_center: Window center position
            window_normal: Window viewing direction (horizontal)
            ascending: If True, sort from closest to furthest (default)
        """
        self.window_center = window_center
        self.window_normal = window_normal
        self.ascending = ascending

    def sort(self, triangles: List[Triangle]) -> List[Triangle]:
        """Sort triangles by distance along view direction"""
        return sorted(triangles,
                     key=lambda tri: self._calculate_distance(tri),
                     reverse=not self.ascending)

    def _calculate_distance(self, triangle: Triangle) -> float:
        """Calculate distance of triangle centroid along view direction"""
        centroid = triangle.get_centroid()
        centroid_arr = centroid.to_array()
        window_arr = self.window_center.to_array()
        direction_arr = self.window_normal.to_array()

        vector_to_centroid = centroid_arr - window_arr
        distance = float(np.dot(vector_to_centroid, direction_arr))

        return distance


class TriangleProcessor:
    """
    Main processor for triangle operations

    Coordinates filtering and sorting operations using Strategy pattern
    """

    def __init__(self):
        """Initialize triangle processor"""
        self.filters: List[ITriangleFilter] = []
        self.sorter: ITriangleSorter = None

    def add_filter(self, filter_strategy: ITriangleFilter) -> 'TriangleProcessor':
        """
        Add a filter to the processing pipeline

        Args:
            filter_strategy: Filter to add

        Returns:
            Self for chaining
        """
        self.filters.append(filter_strategy)
        return self

    def set_sorter(self, sorter: ITriangleSorter) -> 'TriangleProcessor':
        """
        Set the sorting strategy

        Args:
            sorter: Sorter to use

        Returns:
            Self for chaining
        """
        self.sorter = sorter
        return self

    def process(self, projected_points: List[ProjectedPoint]) -> List[Triangle]:
        """
        Process projected points through filters and sorting

        Args:
            projected_points: List of projected points (groups of 3 form triangles)

        Returns:
            Filtered and sorted list of triangles
        """
        # Convert points to triangles
        triangles = self._group_into_triangles(projected_points)

        # Apply filters
        filtered_triangles = self._apply_filters(triangles)

        # Apply sorting
        if self.sorter:
            filtered_triangles = self.sorter.sort(filtered_triangles)

        return filtered_triangles

    def _group_into_triangles(self, points: List[ProjectedPoint]) -> List[Triangle]:
        """Group projected points into triangles (every 3 points)"""
        triangles = []
        for i in range(0, len(points), 3):
            if i + 2 < len(points):
                tri_points = points[i:i+3]
                triangles.append(Triangle(tri_points))

        return triangles

    def _apply_filters(self, triangles: List[Triangle]) -> List[Triangle]:
        """Apply all filters in sequence"""
        result = triangles
        for filter_strategy in self.filters:
            result = filter_strategy.filter(result)

        return result


class HorizonTriangleProcessor(TriangleProcessor):
    """
    Specialized triangle processor for horizon angle calculations

    Automatically configures filters and sorters for horizon calculations:
    - Filters to upper forward quarter only (above window and in front)
    - Filters triangles intersecting the projection plane
    - Filters vertical surfaces
    - Sorts from highest to lowest
    """

    def __init__(
        self,
        window_center: Point3D,
        window_normal: Vector3D,
        vertical_threshold: float = 0.3,
        plane_threshold: float = 0.1
    ):
        """
        Initialize horizon triangle processor

        Args:
            window_center: Window center position
            window_normal: Window viewing direction
            vertical_threshold: Threshold for vertical surface detection
            plane_threshold: Threshold for plane intersection detection
        """
        super().__init__()

        # First: Filter to upper forward quarter only (region where obstructions matter)
        quarter_filter = UpperForwardQuarterFilter(window_center, window_normal)
        self.add_filter(quarter_filter)

        # Calculate plane normal for intersection filter
        plane_normal_vec = ProjectionPlane.calculate_plane_normal(window_normal)
        plane_normal = plane_normal_vec.to_array()

        # Add plane intersection filter
        plane_filter = PlaneIntersectionFilter(
            window_center, window_normal, plane_normal, threshold=plane_threshold
        )
        self.add_filter(plane_filter)

        # Add vertical orientation filter
        vertical_filter = OrientationFilter(
            TriangleOrientation.VERTICAL,
            vertical_threshold=vertical_threshold
        )
        self.add_filter(vertical_filter)

        # Set height sorter (highest to lowest)
        height_sorter = HeightSorter(descending=True)
        self.set_sorter(height_sorter)


class ZenithTriangleProcessor(TriangleProcessor):
    """
    Specialized triangle processor for zenith angle calculations

    Automatically configures filters and sorters for zenith calculations:
    - Filters to upper forward quarter only (above window and in front)
    - Filters triangles intersecting the projection plane
    - Filters to points above window
    - Filters horizontal surfaces
    - Sorts from furthest to closest (to find maximum zenith angle)
    """

    def __init__(
        self,
        window_center: Point3D,
        window_normal: Vector3D,
        horizontal_threshold: float = 0.7,
        plane_threshold: float = 2.5
    ):
        """
        Initialize zenith triangle processor

        Args:
            window_center: Window center position
            window_normal: Window viewing direction
            horizontal_threshold: Threshold for horizontal surface detection
            plane_threshold: Threshold for plane intersection detection
        """
        super().__init__()

        # First: Filter to upper forward quarter only (region where obstructions matter)
        quarter_filter = UpperForwardQuarterFilter(window_center, window_normal)
        self.add_filter(quarter_filter)

        # Calculate plane normal for intersection filter
        plane_normal_vec = ProjectionPlane.calculate_plane_normal(window_normal)
        plane_normal = plane_normal_vec.to_array()

        # Add plane intersection filter
        plane_filter = PlaneIntersectionFilter(
            window_center, window_normal, plane_normal, threshold=plane_threshold
        )
        self.add_filter(plane_filter)

        # Add above window filter (redundant with UpperForwardQuarterFilter but kept for clarity)
        above_filter = AboveWindowFilter(window_center)
        self.add_filter(above_filter)

        # Add horizontal orientation filter
        horizontal_filter = OrientationFilter(
            TriangleOrientation.HORIZONTAL,
            vertical_threshold=horizontal_threshold
        )
        self.add_filter(horizontal_filter)

        # Set distance sorter (furthest to closest)
        # For zenith angle, we want the furthest point to get the largest angle
        distance_sorter = DistanceSorter(
            window_center=window_center,
            window_normal=window_normal,
            ascending=False  # Furthest first for maximum zenith angle
        )
        self.set_sorter(distance_sorter)

import pytest
from src.components.geometry import Point3D, Vector3D
from src.components.models import Window
from src.server.base.constants import RequestField


class TestWindow:
    """Test cases for Window model"""

    def test_window_creation(self):
        """Test basic window creation"""
        center = Point3D(x=0.0, y=1.5, z=0.0)
        normal = Vector3D(x=1.0, y=0.0, z=0.0)

        window = Window(center=center, normal=normal)

        assert window.center == center
        assert window.normal == normal

    def test_window_immutability(self):
        """Test that window is immutable"""
        center = Point3D(x=0.0, y=1.5, z=0.0)
        normal = Vector3D(x=1.0, y=0.0, z=0.0)
        window = Window(center=center, normal=normal)

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            window.center = Point3D(x=1.0, y=1.0, z=1.0)

    def test_from_dict_with_center_format(self):
        """Test creating window from dictionary with center format"""
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 0.0
        }

        window = Window.from_dict(data)

        assert window.center.x == 0.0
        assert window.center.y == 1.5
        assert window.center.z == 0.0
        assert isinstance(window.normal, Vector3D)

    def test_from_dict_with_direction_angle(self):
        """Test that direction angle creates normalized vector"""
        data = {
            RequestField.X.value: 0.0,
            RequestField.Y.value: 1.5,
            RequestField.Z.value: 0.0,
            RequestField.DIRECTION_ANGLE.value: 1.5708  # 90 degrees
        }

        window = Window.from_dict(data)

        assert isinstance(window.normal, Vector3D)
        # Normal should be a unit vector
        magnitude = (window.normal.x**2 + window.normal.y**2 + window.normal.z**2)**0.5
        assert abs(magnitude - 1.0) < 0.01

    def test_set_angle(self):
        """Test set_angle creates new window with updated direction"""
        window1 = Window(
            center=Point3D(x=0.0, y=1.5, z=0.0),
            normal=Vector3D(x=1.0, y=0.0, z=0.0)
        )

        window2 = Window.set_angle(window1, 1.5708)

        # Original window unchanged
        assert window1.normal.x == 1.0
        # New window has different normal
        assert window2.center == window1.center
        assert isinstance(window2.normal, Vector3D)

    def test_from_endpoints(self):
        """Test creating window from endpoints"""
        data = {
            RequestField.X1.value: 5.0,
            RequestField.Y1.value: 0.0,
            RequestField.Z1.value: 1.5,
            RequestField.X2.value: 5.0,
            RequestField.Y2.value: 2.0,
            RequestField.Z2.value: 3.5,
            RequestField.DIRECTION_ANGLE.value: 0.0,
            RequestField.ROOM_POLYGON.value: [
                [0.0, 0.0],
                [10.0, 0.0],
                [10.0, 10.0],
                [0.0, 10.0]
            ]
        }

        window = Window.from_endpoints(data)

        assert isinstance(window, Window)
        assert isinstance(window.center, Point3D)
        assert isinstance(window.normal, Vector3D)
        # Vertical center should be (1.5 + 3.5) / 2 = 2.5
        assert abs(window.center.z - 2.5) < 0.01

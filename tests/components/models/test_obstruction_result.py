import pytest
from src.components.geometry import Point3D
from src.components.models import ObstructionResult
from src.server.base.constants import ResponseField, RequestField


class TestObstructionResult:
    """Test cases for ObstructionResult model"""

    def test_obstruction_result_creation(self):
        """Test basic obstruction result creation"""
        point = Point3D(x=1.0, y=3.0, z=0.0)

        result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=0.785,
            highest_point=point
        )

        assert result.obstruction_angle_degrees == 45.0
        assert result.obstruction_angle_radians == 0.785
        assert result.highest_point == point

    def test_obstruction_result_immutability(self):
        """Test that obstruction result is immutable"""
        point = Point3D(x=1.0, y=3.0, z=0.0)
        result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=0.785,
            highest_point=point
        )

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            result.obstruction_angle_degrees = 30.0

    def test_no_obstruction_factory(self):
        """Test no_obstruction factory method"""
        result = ObstructionResult.no_obstruction()

        assert result.obstruction_angle_degrees == 0.0
        assert result.obstruction_angle_radians == 0.0
        assert result.highest_point is None

    def test_no_obstruction_with_point(self):
        """Test no_obstruction factory with highest_point"""
        point = Point3D(x=1.0, y=2.0, z=3.0)
        result = ObstructionResult.no_obstruction(highest_point=point)

        assert result.obstruction_angle_degrees == 0.0
        assert result.obstruction_angle_radians == 0.0
        assert result.highest_point == point

    def test_to_dict(self):
        """Test conversion to dictionary"""
        point = Point3D(x=1.0, y=3.0, z=0.5)
        result = ObstructionResult(
            obstruction_angle_degrees=45.0,
            obstruction_angle_radians=0.785,
            highest_point=point
        )

        result_dict = result.to_dict()

        assert result_dict[ResponseField.OBSTRUCTION_ANGLE_DEGREES.value] == 45.0
        assert result_dict[ResponseField.OBSTRUCTION_ANGLE_RADIANS.value] == 0.785
        assert result_dict[ResponseField.HIGHEST_POINT.value] is not None
        assert result_dict[ResponseField.HIGHEST_POINT.value][RequestField.X.value] == 1.0
        assert result_dict[ResponseField.HIGHEST_POINT.value][RequestField.Y.value] == 3.0
        assert result_dict[ResponseField.HIGHEST_POINT.value][RequestField.Z.value] == 0.5

    def test_to_dict_no_highest_point(self):
        """Test conversion to dictionary with no highest point"""
        result = ObstructionResult(
            obstruction_angle_degrees=0.0,
            obstruction_angle_radians=0.0,
            highest_point=None
        )

        result_dict = result.to_dict()

        assert result_dict[ResponseField.OBSTRUCTION_ANGLE_DEGREES.value] == 0.0
        assert result_dict[ResponseField.OBSTRUCTION_ANGLE_RADIANS.value] == 0.0
        assert result_dict[ResponseField.HIGHEST_POINT.value] is None

    def test_to_dict_with_large_angle(self):
        """Test to_dict with large obstruction angle"""
        point = Point3D(x=5.0, y=10.0, z=2.0)
        result = ObstructionResult(
            obstruction_angle_degrees=89.5,
            obstruction_angle_radians=1.562,
            highest_point=point
        )

        result_dict = result.to_dict()

        assert result_dict[ResponseField.OBSTRUCTION_ANGLE_DEGREES.value] == 89.5
        assert result_dict[ResponseField.OBSTRUCTION_ANGLE_RADIANS.value] == 1.562

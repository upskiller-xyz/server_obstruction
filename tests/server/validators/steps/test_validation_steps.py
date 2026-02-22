import pytest
from src.server.validators.steps.required_fields_validation_step import RequiredFieldsValidationStep
from src.server.validators.steps.numeric_fields_validation_step import NumericFieldsValidationStep
from src.server.validators.steps.mesh_format_validation_step import MeshFormatValidationStep


class TestRequiredFieldsValidationStep:
    """Test cases for RequiredFieldsValidationStep"""

    def test_valid_request_passes(self):
        """Test that valid request passes validation"""
        data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": {"horizon": [[1.0, 0.0, 0.0], [1.0, 3.0, 0.0], [1.0, 1.5, 1.0]]}
        }

        # call() raises ValueError on failure, returns None on success
        try:
            RequiredFieldsValidationStep.call(data)
            validation_passed = True
        except ValueError:
            validation_passed = False

        assert validation_passed is True

    def test_missing_required_field_fails(self):
        """Test that missing required field fails validation"""
        data = {
            "x": 0.0,
            "y": 1.5,
            # Missing 'z'
            "direction_angle": 0.0,
            "mesh": {"horizon": [[1.0, 0.0, 0.0]]}
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            RequiredFieldsValidationStep.call(data)

    def test_missing_mesh_field_fails(self):
        """Test that missing mesh field fails validation"""
        data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0
            # Missing 'mesh'
        }

        with pytest.raises(ValueError):
            RequiredFieldsValidationStep.call(data)


class TestNumericFieldsValidationStep:
    """Test cases for NumericFieldsValidationStep"""

    def test_valid_numeric_fields_pass(self):
        """Test that valid numeric fields pass validation"""
        data = {
            "x": 0.0,
            "y": 1.5,
            "z": -2.3,
            "direction_angle": 1.57,
            "mesh": {"horizon": [[1.0, 0.0, 0.0]]}
        }

        # call() raises ValueError on failure, returns None on success
        try:
            NumericFieldsValidationStep.call(data)
            validation_passed = True
        except ValueError:
            validation_passed = False

        assert validation_passed is True

    def test_string_numeric_fields_pass(self):
        """Test that string numeric fields are converted"""
        data = {
            "x": "0.0",
            "y": "1.5",
            "z": "-2.3",
            "direction_angle": "1.57",
            "mesh": {"horizon": [[1.0, 0.0, 0.0]]}
        }

        # call() raises ValueError on failure, returns None on success
        try:
            NumericFieldsValidationStep.call(data)
            validation_passed = True
        except ValueError:
            validation_passed = False

        assert validation_passed is True

    def test_invalid_numeric_field_fails(self):
        """Test that invalid numeric field fails validation"""
        data = {
            "x": "not_a_number",
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": {"horizon": [[1.0, 0.0, 0.0]]}
        }

        with pytest.raises(ValueError, match="must be a number"):
            NumericFieldsValidationStep.call(data)


class TestMeshFormatValidationStep:
    """Test cases for MeshFormatValidationStep"""

    def test_valid_nested_mesh_passes(self):
        """Test that valid nested mesh format passes"""
        data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": {
                "horizon": [
                    [1.0, 0.0, 0.0],
                    [1.0, 3.0, 0.0],
                    [1.0, 1.5, 1.0]
                ]
            }
        }

        # call() raises ValueError on failure, returns None on success
        try:
            MeshFormatValidationStep.call(data)
            validation_passed = True
        except ValueError:
            validation_passed = False

        assert validation_passed is True

    def test_valid_flat_mesh_passes(self):
        """Test that valid flat mesh format passes"""
        data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": [
                [1.0, 0.0, 0.0],
                [1.0, 3.0, 0.0],
                [1.0, 1.5, 1.0]
            ]
        }

        # call() raises ValueError on failure, returns None on success
        try:
            MeshFormatValidationStep.call(data)
            validation_passed = True
        except ValueError:
            validation_passed = False

        assert validation_passed is True

    def test_mesh_not_list_fails(self):
        """Test that non-list mesh fails validation"""
        data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": "not_a_list"
        }

        with pytest.raises(ValueError):
            MeshFormatValidationStep.call(data)

    def test_empty_mesh_passes(self):
        """Test that empty mesh passes validation (warns but doesn't fail)"""
        data = {
            "x": 0.0,
            "y": 1.5,
            "z": 0.0,
            "direction_angle": 0.0,
            "mesh": {"horizon": []}
        }

        # Empty mesh should pass (it just logs a warning)
        try:
            MeshFormatValidationStep.call(data)
            validation_passed = True
        except ValueError:
            validation_passed = False

        assert validation_passed is True

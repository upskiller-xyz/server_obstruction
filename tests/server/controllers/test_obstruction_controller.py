"""Tests for ObstructionController"""
import pytest
from unittest.mock import Mock, patch
from src.server.controllers.obstruction_controller import ObstructionController
from src.server.base.constants import EndpointName, ResponseStatus


class TestObstructionController:
    """Test suite for ObstructionController"""

    def test_get_status(self):
        """Test get_status returns server status"""
        status = ObstructionController.get_status()
        assert isinstance(status, dict)
        # Controller returns either 'status' or 'controller' key
        assert 'controller' in status or 'status' in status

    def test_call_with_horizon_endpoint(self):
        """Test call method with horizon endpoint"""
        request_data = {
            "x": 0.0,
            "y": 0.0,
            "z": 1.0,
            "width": 1.2,
            "height": 1.5,
            "direction_angle": 0.0,
            "mesh": {"horizon": []}
        }
        result = ObstructionController.call(EndpointName.HORIZON, request_data)
        assert isinstance(result, dict)
        assert 'status' in result

    def test_call_with_zenith_endpoint(self):
        """Test call method with zenith endpoint"""
        request_data = {
            "x": 0.0,
            "y": 0.0,
            "z": 1.0,
            "width": 1.2,
            "height": 1.5,
            "direction_angle": 0.0,
            "mesh": {"zenith": []}
        }
        result = ObstructionController.call(EndpointName.ZENITH, request_data)
        assert isinstance(result, dict)
        assert 'status' in result

    def test_call_with_invalid_data_returns_error(self):
        """Test call with invalid data returns error status"""
        request_data = {}  # Missing required fields
        result = ObstructionController.call(EndpointName.HORIZON, request_data)
        assert isinstance(result, dict)
        assert 'status' in result
        assert result['status'] == ResponseStatus.ERROR.value

    def test_call_with_valid_mesh_data(self):
        """Test call with valid mesh data"""
        request_data = {
            "x": 0.0,
            "y": 0.0,
            "z": 1.0,
            "width": 1.2,
            "height": 1.5,
            "direction_angle": 0.0,
            "mesh": {
                "horizon": [
                    [0.0, 10.0, 0.0],
                    [5.0, 10.0, 0.0],
                    [5.0, 10.0, 5.0]
                ]
            }
        }
        result = ObstructionController.call(EndpointName.HORIZON, request_data)
        assert isinstance(result, dict)
        assert 'status' in result

    def test_call_with_obstruction_endpoint(self):
        """Test call method with obstruction endpoint"""
        request_data = {
            "x": 0.0,
            "y": 0.0,
            "z": 1.0,
            "width": 1.2,
            "height": 1.5,
            "direction_angle": 0.0,
            "mesh": []
        }
        result = ObstructionController.call(EndpointName.OBSTRUCTION, request_data)
        assert isinstance(result, dict)
        assert 'status' in result

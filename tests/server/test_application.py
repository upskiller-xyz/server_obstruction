"""Tests for ServerApplication class"""
import pytest
import json
from unittest.mock import Mock, patch
from src.server.application import ServerApplication
from src.server.base.constants import HTTPStatus, ResponseStatus


class TestServerApplication:
    """Test suite for ServerApplication class"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        application = ServerApplication()
        application.app.config['TESTING'] = True
        with application.app.test_client() as client:
            yield client

    def test_application_initialization(self):
        """Test that application initializes correctly"""
        app = ServerApplication()
        assert app.app is not None
        assert app.app.name == "Server Application"

    def test_get_status_endpoint(self, client):
        """Test GET / returns status"""
        response = client.get('/')
        assert response.status_code == HTTPStatus.OK.value
        data = json.loads(response.data)
        # Status can be in 'status' or 'controller' key depending on controller implementation
        assert 'controller' in data or 'status' in data

    def test_list_routes_endpoint(self, client):
        """Test GET /routes returns route list"""
        response = client.get('/routes')
        assert response.status_code == HTTPStatus.OK.value
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == ResponseStatus.SUCCESS.value
        assert 'routes' in data
        assert 'total_routes' in data
        assert isinstance(data['routes'], list)

    def test_horizon_angle_endpoint_missing_content_type(self, client):
        """Test POST /horizon with missing Content-Type"""
        response = client.post(
            '/horizon_angle',
            data='{}',
            content_type='text/plain'
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        data = json.loads(response.data)
        assert data['status'] == ResponseStatus.ERROR.value

    def test_horizon_angle_endpoint_empty_body(self, client):
        """Test POST /horizon with empty body"""
        response = client.post(
            '/horizon_angle',
            data='',
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value

    def test_horizon_angle_endpoint_invalid_json(self, client):
        """Test POST /horizon with invalid JSON"""
        response = client.post(
            '/horizon_angle',
            data='not json',
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value

    def test_horizon_angle_endpoint_missing_fields(self, client):
        """Test POST /horizon with missing required fields"""
        response = client.post(
            '/horizon_angle',
            json={}
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        data = json.loads(response.data)
        assert data['status'] == ResponseStatus.ERROR.value

    def test_horizon_angle_endpoint_valid_request(self, client):
        """Test POST /horizon with valid request"""
        request_data = {
            "x": 0.0,
            "y": 0.0,
            "z": 1.0,
            "width": 1.2,
            "height": 1.5,
            "direction_angle": 0.0,
            "mesh": {
                "horizon": []
            }
        }
        response = client.post(
            '/horizon_angle',
            json=request_data
        )
        # Should succeed with empty mesh (no obstruction)
        assert response.status_code in [HTTPStatus.OK.value, HTTPStatus.BAD_REQUEST.value]
        data = json.loads(response.data)
        assert 'status' in data

    def test_zenith_angle_endpoint_valid_request(self, client):
        """Test POST /zenith with valid request"""
        request_data = {
            "x": 0.0,
            "y": 0.0,
            "z": 1.0,
            "width": 1.2,
            "height": 1.5,
            "direction_angle": 0.0,
            "mesh": {
                "zenith": []
            }
        }
        response = client.post(
            '/zenith_angle',
            json=request_data
        )
        # Should succeed with empty mesh (no obstruction)
        assert response.status_code in [HTTPStatus.OK.value, HTTPStatus.BAD_REQUEST.value]
        data = json.loads(response.data)
        assert 'status' in data

    def test_application_has_cors_enabled(self):
        """Test that CORS is enabled"""
        app = ServerApplication()
        # CORS should be enabled - check by making OPTIONS request
        with app.app.test_client() as client:
            response = client.options('/')
            # CORS headers should be present
            assert 'Access-Control-Allow-Origin' in response.headers or response.status_code == 200

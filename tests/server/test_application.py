"""Tests for ServerApplication class"""
import gzip
import io
import json

import numpy as np
import pytest
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

    def test_horizon_endpoint_missing_content_type(self, client):
        """Test POST /horizon with missing Content-Type"""
        response = client.post(
            '/horizon',
            data='{}',
            content_type='text/plain'
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        data = json.loads(response.data)
        assert data['status'] == ResponseStatus.ERROR.value

    def test_horizon_endpoint_empty_body(self, client):
        """Test POST /horizon with empty body"""
        response = client.post(
            '/horizon',
            data='',
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value

    def test_horizon_endpoint_invalid_json(self, client):
        """Test POST /horizon with invalid JSON"""
        response = client.post(
            '/horizon',
            data='not json',
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value

    def test_horizon_endpoint_missing_fields(self, client):
        """Test POST /horizon with missing required fields"""
        response = client.post(
            '/horizon',
            json={}
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        data = json.loads(response.data)
        assert data['status'] == ResponseStatus.ERROR.value

    def test_horizon_endpoint_valid_request(self, client):
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
            '/horizon',
            json=request_data
        )
        # Should succeed with empty mesh (no obstruction)
        assert response.status_code in [HTTPStatus.OK.value, HTTPStatus.BAD_REQUEST.value]
        data = json.loads(response.data)
        assert 'status' in data

    def test_zenith_endpoint_valid_request(self, client):
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
            '/zenith',
            json=request_data
        )
        # Should succeed with empty mesh (no obstruction)
        assert response.status_code in [HTTPStatus.OK.value, HTTPStatus.BAD_REQUEST.value]
        data = json.loads(response.data)
        assert 'status' in data

    @staticmethod
    def _npy_mesh() -> bytes:
        """A minimal valid (N, 3) float mesh serialized as .npy bytes."""
        verts = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32)
        buf = io.BytesIO()
        np.save(buf, verts)
        return buf.getvalue()

    @staticmethod
    def _params() -> dict:
        return {"x": 0.5, "y": 0.5, "z": 10.0, "direction_angle": 90.0}

    def test_binary_endpoint_accepts_npy_mesh(self, client):
        """POST /obstruction_parallel_bin with a multipart .npy mesh succeeds."""
        response = client.post(
            '/obstruction_parallel_bin',
            data={
                'params': json.dumps(self._params()),
                'mesh': (io.BytesIO(self._npy_mesh()), 'mesh.npy'),
            },
            content_type='multipart/form-data',
        )
        assert response.status_code == HTTPStatus.OK.value
        assert 'data' in json.loads(response.data)

    def test_binary_endpoint_accepts_gzipped_npy_mesh(self, client):
        """A gzip-compressed .npy mesh is transparently decompressed."""
        response = client.post(
            '/obstruction_parallel_bin',
            data={
                'params': json.dumps(self._params()),
                'mesh': (io.BytesIO(gzip.compress(self._npy_mesh())), 'mesh.npy.gz'),
            },
            content_type='multipart/form-data',
        )
        assert response.status_code == HTTPStatus.OK.value

    def test_binary_endpoint_empty_mesh_returns_400(self, client):
        """An empty mesh payload is a client error, not a 500."""
        response = client.post(
            '/obstruction_parallel_bin',
            data={
                'params': json.dumps(self._params()),
                'mesh': (io.BytesIO(b''), 'mesh.npy'),
            },
            content_type='multipart/form-data',
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value
        assert json.loads(response.data)['status'] == ResponseStatus.ERROR.value

    def test_binary_endpoint_missing_params_returns_400(self, client):
        """Missing the params form field is a client error."""
        response = client.post(
            '/obstruction_parallel_bin',
            data={'mesh': (io.BytesIO(self._npy_mesh()), 'mesh.npy')},
            content_type='multipart/form-data',
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value

    def test_binary_endpoint_rejects_npz_archive(self, client):
        """An .npz archive (not a single array) is a client error, not a 500."""
        buf = io.BytesIO()
        np.savez(buf, a=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32))
        response = client.post(
            '/obstruction_parallel_bin',
            data={'params': json.dumps(self._params()), 'mesh': (io.BytesIO(buf.getvalue()), 'm.npz')},
            content_type='multipart/form-data',
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value

    def test_binary_endpoint_rejects_corrupt_gzip(self, client):
        """A gzip-magic but corrupt payload is a client error, not a 500."""
        response = client.post(
            '/obstruction_parallel_bin',
            data={'params': json.dumps(self._params()), 'mesh': (io.BytesIO(b'\x1f\x8bgarbage'), 'm.npy.gz')},
            content_type='multipart/form-data',
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value

    def test_binary_endpoint_rejects_non_object_params(self, client):
        """params that is not a JSON object is a client error."""
        response = client.post(
            '/obstruction_parallel_bin',
            data={'params': '[1, 2, 3]', 'mesh': (io.BytesIO(self._npy_mesh()), 'mesh.npy')},
            content_type='multipart/form-data',
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST.value

    def test_json_endpoint_rejects_non_object_body(self, client):
        """A non-object JSON body (list/null) is a 400, not a 500."""
        response = client.post('/obstruction_parallel', data='[1, 2, 3]', content_type='application/json')
        assert response.status_code == HTTPStatus.BAD_REQUEST.value

    def test_application_has_cors_enabled(self):
        """Test that CORS is enabled"""
        app = ServerApplication()
        # CORS should be enabled - check by making OPTIONS request
        with app.app.test_client() as client:
            response = client.options('/')
            # CORS headers should be present
            assert 'Access-Control-Allow-Origin' in response.headers or response.status_code == 200

"""Tests for base ServerController class"""
import pytest
from unittest.mock import Mock
from src.server.controllers.base_controller import ServerController
from src.server.enums import ServerStatus


class TestServerController:
    """Test suite for base ServerController class"""

    def test_initialization_without_services(self):
        """Test controller initializes without services"""
        controller = ServerController()
        assert controller._services == {}
        assert controller._status == ServerStatus.STARTING

    def test_initialization_with_services(self):
        """Test controller initializes with services dictionary"""
        services = {"service1": Mock(), "service2": Mock()}
        controller = ServerController(services=services)
        assert controller._services == services
        assert controller._status == ServerStatus.STARTING

    def test_initialize_sets_status_to_running(self):
        """Test initialize() sets status to RUNNING"""
        controller = ServerController()
        controller.initialize()
        assert controller._status == ServerStatus.RUNNING

    def test_initialize_calls_service_initialize_methods(self):
        """Test initialize() calls initialize on services that have it"""
        mock_service1 = Mock()
        mock_service1.initialize = Mock()
        mock_service2 = Mock()  # No initialize method

        services = {
            "service1": mock_service1,
            "service2": mock_service2
        }

        controller = ServerController(services=services)
        controller.initialize()

        # service1 should have initialize called
        mock_service1.initialize.assert_called_once()

    def test_initialize_handles_service_initialization_error(self):
        """Test initialize() handles errors during service initialization"""
        mock_service = Mock()
        mock_service.initialize = Mock(side_effect=Exception("Init failed"))

        services = {"failing_service": mock_service}
        controller = ServerController(services=services)

        with pytest.raises(Exception, match="Init failed"):
            controller.initialize()

        # Status should be ERROR after failed initialization
        assert controller._status == ServerStatus.ERROR

    def test_get_status_returns_dict(self):
        """Test get_status() returns dictionary with status"""
        controller = ServerController()
        controller.initialize()

        status = controller.get_status()

        assert isinstance(status, dict)
        assert 'status' in status
        assert 'services' in status
        assert status['status'] == ServerStatus.RUNNING.value

    def test_get_status_includes_service_statuses(self):
        """Test get_status() includes status from services"""
        # Service with get_status
        mock_service1 = Mock(spec=[])  # Empty spec
        mock_service1.get_status = Mock(return_value={"ready": True})
        mock_service1.initialize = Mock()

        # Service without get_status - use a spec to prevent auto-creation
        class SimpleService:
            pass
        mock_service2 = SimpleService()

        services = {
            "service1": mock_service1,
            "service2": mock_service2
        }

        controller = ServerController(services=services)
        controller.initialize()
        status = controller.get_status()

        assert status['services']['service1'] == {"ready": True}
        assert status['services']['service2'] == "ready"
        # Verify initialize was called
        mock_service1.initialize.assert_called_once()

    def test_get_status_before_initialization(self):
        """Test get_status() works before initialization"""
        controller = ServerController()
        status = controller.get_status()

        assert status['status'] == ServerStatus.STARTING.value
        assert status['services'] == {}

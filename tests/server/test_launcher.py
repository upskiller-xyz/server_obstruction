"""Tests for ServerLauncher class"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.server.launcher import ServerLauncher
from src.server.application import ServerApplication


class TestServerLauncher:
    """Test suite for ServerLauncher class"""

    def test_create_application(self):
        """Test that create_application returns ServerApplication instance"""
        launcher = ServerLauncher()
        app = launcher.create_application()
        assert isinstance(app, ServerApplication)
        assert app.app is not None

    def test_create_multiple_applications(self):
        """Test that create_application can be called multiple times"""
        launcher = ServerLauncher()
        app1 = launcher.create_application()
        app2 = launcher.create_application()
        # Should create separate instances
        assert app1 is not app2
        assert app1.app is not app2.app

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_calls_flask_run(self, mock_app_class):
        """Test that run_server calls Flask's run method"""
        # Setup mock
        mock_app_instance = Mock()
        mock_flask_app = Mock()
        mock_flask_app.name = "Test App"
        mock_flask_app.logger = Mock()
        mock_app_instance.app = mock_flask_app

        # Run server
        launcher = ServerLauncher()
        launcher.run_server(mock_app_instance, host="0.0.0.0", port=8081, debug=True)

        # Verify Flask run was called with correct parameters
        mock_flask_app.run.assert_called_once_with(
            host="0.0.0.0",
            port=8081,
            debug=True,
            use_reloader=True
        )

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_default_parameters(self, mock_app_class):
        """Test run_server with default parameters"""
        # Setup mock
        mock_app_instance = Mock()
        mock_flask_app = Mock()
        mock_flask_app.name = "Test App"
        mock_flask_app.logger = Mock()
        mock_app_instance.app = mock_flask_app

        # Run server with defaults
        launcher = ServerLauncher()
        launcher.run_server(mock_app_instance)

        # Verify Flask run was called with defaults
        mock_flask_app.run.assert_called_once()
        call_kwargs = mock_flask_app.run.call_args[1]
        assert call_kwargs['host'] == "0.0.0.0"
        assert call_kwargs['port'] == 8081
        assert call_kwargs['debug'] == True

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_logs_startup_message(self, mock_app_class):
        """Test that run_server logs startup information"""
        # Setup mock
        mock_app_instance = Mock()
        mock_flask_app = Mock()
        mock_flask_app.name = "Test App"
        mock_logger = Mock()
        mock_flask_app.logger = mock_logger
        mock_app_instance.app = mock_flask_app

        # Run server
        launcher = ServerLauncher()
        launcher.run_server(mock_app_instance, host="127.0.0.1", port=9000, debug=False)

        # Verify logger was called
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "Test App" in log_message
        assert "127.0.0.1" in log_message
        assert "9000" in log_message
        assert "False" in log_message

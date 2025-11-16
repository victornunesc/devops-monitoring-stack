"""
Tests for health check server
"""
import pytest
from unittest.mock import MagicMock, patch

from src.utils.health_check import HealthCheckHandler, HealthCheckServer


class TestHealthCheckHandler:
    """Test suite for HealthCheckHandler"""

    @pytest.fixture
    def handler(self):
        """Create a handler instance"""
        # Mock the request socket to prevent actual network operations
        mock_request = MagicMock()
        mock_request.makefile = MagicMock(side_effect=lambda *args, **kwargs: MagicMock())
        
        # Create handler without calling __init__ to avoid BaseHTTPRequestHandler initialization
        handler = HealthCheckHandler.__new__(HealthCheckHandler)
        handler.request = mock_request
        handler.client_address = ('127.0.0.1', 12345)
        handler.server = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = MagicMock()
        return handler

    def test_do_get_health_endpoint(self, handler):
        """Test GET request to /health endpoint"""
        handler.path = '/health'
        handler.do_GET()
        
        handler.send_response.assert_called_once_with(200)
        handler.send_header.assert_called_once_with('Content-Type', 'application/json')
        handler.end_headers.assert_called_once()
        handler.wfile.write.assert_called_once_with(b'{"status": "healthy"}')

    def test_do_get_unknown_endpoint(self, handler):
        """Test GET request to unknown endpoint"""
        handler.path = '/unknown'
        handler.do_GET()
        
        handler.send_response.assert_called_once_with(404)
        handler.end_headers.assert_called_once()
        handler.wfile.write.assert_not_called()

    def test_do_get_root_endpoint(self, handler):
        """Test GET request to root endpoint"""
        handler.path = '/'
        handler.do_GET()
        
        handler.send_response.assert_called_once_with(404)
        handler.end_headers.assert_called_once()

    def test_log_message_disabled(self, handler):
        """Test that log_message does nothing (disabled)"""
        # Should not raise any exception
        handler.log_message("test format", "arg1", "arg2")


class TestHealthCheckServer:
    """Test suite for HealthCheckServer"""

    def test_server_initialization(self):
        """Test server initialization"""
        server = HealthCheckServer(port=8081)
        
        assert server.port == 8081
        assert server.server is None

    def test_server_initialization_custom_port(self):
        """Test server initialization with custom port"""
        server = HealthCheckServer(port=9090)
        
        assert server.port == 9090

    def test_start_server(self):
        """Test starting the server"""
        server = HealthCheckServer(port=8081)
        
        with patch('src.utils.health_check.HTTPServer') as mock_http_server:
            mock_server_instance = MagicMock()
            mock_http_server.return_value = mock_server_instance
            
            # Run start in a way that we can control
            with patch.object(mock_server_instance, 'serve_forever', side_effect=KeyboardInterrupt):
                try:
                    server.start()
                except KeyboardInterrupt:
                    pass
            
            # Verify server was created
            mock_http_server.assert_called_once_with(('0.0.0.0', 8081), HealthCheckHandler)
            assert server.server == mock_server_instance

    def test_stop_server(self):
        """Test stopping the server"""
        server = HealthCheckServer(port=8081)
        server.server = MagicMock()
        
        server.stop()
        
        server.server.shutdown.assert_called_once()

    def test_stop_server_when_not_started(self):
        """Test stopping server when it hasn't been started"""
        server = HealthCheckServer(port=8081)
        
        # Should not raise exception
        server.stop()

    def test_server_binds_to_all_interfaces(self):
        """Test that server binds to 0.0.0.0"""
        server = HealthCheckServer(port=8081)
        
        with patch('src.utils.health_check.HTTPServer') as mock_http_server:
            mock_server_instance = MagicMock()
            mock_http_server.return_value = mock_server_instance
            
            with patch.object(mock_server_instance, 'serve_forever', side_effect=KeyboardInterrupt):
                try:
                    server.start()
                except KeyboardInterrupt:
                    pass
            
            # Verify it binds to all interfaces (0.0.0.0)
            call_args = mock_http_server.call_args
            assert call_args[0][0] == ('0.0.0.0', 8081)

"""
Tests for configuration module
"""

from src.utils.config import Config


class TestConfig:
    """Test suite for Config"""

    def test_config_from_env_defaults(self, monkeypatch):
        """Test configuration with default values"""
        # Clear all environment variables
        for key in ['VIAIPE_API_URL', 'VIAIPE_POLL_INTERVAL', 'OTEL_EXPORTER_OTLP_ENDPOINT',
                    'OTEL_SERVICE_NAME', 'HEALTH_PORT', 'VIAIPE_TIMEOUT']:
            monkeypatch.delenv(key, raising=False)
        
        config = Config.from_env()
        
        assert config.api_url == 'https://legadoviaipe.rnp.br/api/norte'
        assert config.poll_interval == 60
        assert config.otel_endpoint == 'http://otel-collector:4317'
        assert config.service_name == 'viaipe-collector'
        assert config.health_port == 8081
        assert config.timeout == 30

    def test_config_from_env_custom_values(self, monkeypatch):
        """Test configuration with custom environment variables"""
        monkeypatch.setenv('VIAIPE_API_URL', 'https://custom-api.example.com/api')
        monkeypatch.setenv('VIAIPE_POLL_INTERVAL', '60')
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://custom-otel:4317')
        monkeypatch.setenv('OTEL_SERVICE_NAME', 'custom-collector')
        monkeypatch.setenv('HEALTH_PORT', '9090')
        monkeypatch.setenv('VIAIPE_TIMEOUT', '45')
        
        config = Config.from_env()
        
        assert config.api_url == 'https://custom-api.example.com/api'
        assert config.poll_interval == 60
        assert config.otel_endpoint == 'http://custom-otel:4317'
        assert config.service_name == 'custom-collector'
        assert config.health_port == 9090
        assert config.timeout == 45

    def test_config_from_env_partial_custom(self, monkeypatch):
        """Test configuration with some custom values and some defaults"""
        monkeypatch.setenv('VIAIPE_API_URL', 'https://custom-api.example.com/api')
        monkeypatch.setenv('VIAIPE_POLL_INTERVAL', '120')
        # Other values should use defaults
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)
        monkeypatch.delenv('OTEL_SERVICE_NAME', raising=False)
        monkeypatch.delenv('HEALTH_PORT', raising=False)
        monkeypatch.delenv('VIAIPE_TIMEOUT', raising=False)
        
        config = Config.from_env()
        
        assert config.api_url == 'https://custom-api.example.com/api'
        assert config.poll_interval == 120
        assert config.otel_endpoint == 'http://otel-collector:4317'
        assert config.service_name == 'viaipe-collector'
        assert config.health_port == 8081
        assert config.timeout == 30

    def test_config_direct_instantiation(self):
        """Test direct Config instantiation"""
        config = Config(
            api_url='https://test-api.example.com',
            poll_interval=180,
            otel_endpoint='http://test-otel:4317',
            service_name='test-service',
            health_port=8888,
            timeout=60
        )
        
        assert config.api_url == 'https://test-api.example.com'
        assert config.poll_interval == 180
        assert config.otel_endpoint == 'http://test-otel:4317'
        assert config.service_name == 'test-service'
        assert config.health_port == 8888
        assert config.timeout == 60

    def test_config_dataclass_properties(self):
        """Test that Config is a proper dataclass"""
        config = Config(
            api_url='https://test.example.com',
            poll_interval=60,
            otel_endpoint='http://otel:4317',
            service_name='test',
            health_port=8081,
            timeout=30
        )
        
        # Dataclass should have __dict__
        assert hasattr(config, '__dict__')
        
        # Should be able to access all fields
        assert hasattr(config, 'api_url')
        assert hasattr(config, 'poll_interval')
        assert hasattr(config, 'otel_endpoint')
        assert hasattr(config, 'service_name')
        assert hasattr(config, 'health_port')
        assert hasattr(config, 'timeout')

    def test_config_integer_conversion(self, monkeypatch):
        """Test that integer fields are properly converted from strings"""
        monkeypatch.setenv('VIAIPE_POLL_INTERVAL', '600')
        monkeypatch.setenv('HEALTH_PORT', '9999')
        monkeypatch.setenv('VIAIPE_TIMEOUT', '90')
        
        config = Config.from_env()
        
        assert isinstance(config.poll_interval, int)
        assert isinstance(config.health_port, int)
        assert isinstance(config.timeout, int)
        assert config.poll_interval == 600
        assert config.health_port == 9999
        assert config.timeout == 90

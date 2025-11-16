"""
Unit tests for Network Monitor - Refactored Version
Removed redundancies and improved organization
"""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.utils import Config
from src.monitoring import PingMonitor, HTTPMonitor, NetworkMonitor
from src.metrics import MetricsManager


# ============================================================================
# FIXTURES COMPARTILHADOS
# ============================================================================

@pytest.fixture
def metrics_manager():
    """Mock do MetricsManager reutilizável"""
    mock = Mock(spec=MetricsManager)
    mock.ping_rtt = Mock()
    mock.ping_packet_loss = Mock()
    mock.http_duration = Mock()
    mock.http_status = Mock()
    return mock


@pytest.fixture
def test_config():
    """Configuração padrão para testes"""
    return Config(
        targets=['example.com', 'test.com'],
        ping_interval=0.1,  # Intervalo curto para testes
        http_interval=0.1,
        otel_endpoint='http://localhost:4317',
        service_name='test-monitor',
        health_port=8080
    )


# ============================================================================
# CONFIG TESTS
# ============================================================================

class TestConfig:
    """Testes para Config"""
    
    def test_config_defaults(self):
        """Testa valores padrão da configuração"""
        config = Config.from_env()
        
        assert 'google.com' in config.targets
        assert config.ping_interval == 30
        assert config.http_interval == 60
        assert config.service_name == 'network-monitor'
        assert config.health_port == 8080
    
    @patch.dict('os.environ', {
        'MONITOR_TARGETS': 'example.com,test.com',
        'PING_INTERVAL': '60',
        'HTTP_INTERVAL': '120'
    })
    def test_config_custom_env_vars(self):
        """Testa configuração customizada via env vars"""
        config = Config.from_env()
        
        assert config.targets == ['example.com', 'test.com']
        assert config.ping_interval == 60
        assert config.http_interval == 120


# ============================================================================
# PING MONITOR TESTS
# ============================================================================

class TestPingMonitor:
    """Testes para PingMonitor"""
    
    @pytest.fixture
    def ping_monitor(self, metrics_manager):
        """Fixture do PingMonitor"""
        return PingMonitor(metrics_manager)
    
    @pytest.mark.asyncio
    async def test_successful_ping(self, ping_monitor):
        """Testa ping bem-sucedido"""
        with patch('ping3.ping', return_value=0.05):
            result = await ping_monitor.check('example.com', ping_count=3)
            
            assert result['target'] == 'example.com'
            assert result['successful_pings'] == 3
            assert result['total_pings'] == 3
            assert result['packet_loss_percent'] == 0.0
            assert result['avg_rtt_ms'] > 0
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("side_effects,expected_success,expected_loss", [
        ([0.05, None, 0.06, None], 2, 50.0),  # 50% perda
        ([None, None, None], 0, 100.0),        # 100% perda
    ])
    async def test_ping_with_packet_loss(self, ping_monitor, side_effects, expected_success, expected_loss):
        """Testa ping com diferentes percentuais de perda de pacotes"""
        with patch('ping3.ping', side_effect=side_effects):
            result = await ping_monitor.check('example.com', ping_count=len(side_effects))
            
            assert result['successful_pings'] == expected_success
            assert result['packet_loss_percent'] == expected_loss
            if expected_loss == 100.0:
                assert result['avg_rtt_ms'] == 0
    
    @pytest.mark.asyncio
    async def test_ping_with_individual_exceptions(self, ping_monitor):
        """Testa que exceções individuais não quebram o processo"""
        with patch('ping3.ping', side_effect=[0.05, Exception("Network error"), 0.06]):
            result = await ping_monitor.check('example.com', ping_count=3)
            
            assert result['successful_pings'] == 2
            assert result['total_pings'] == 3
    
    @pytest.mark.asyncio
    async def test_ping_fatal_exception(self, ping_monitor, metrics_manager):
        """Testa exceção fatal durante gravação de métricas"""
        metrics_manager.ping_packet_loss.record.side_effect = Exception("Metrics error")
        
        with patch('ping3.ping', return_value=0.05):
            result = await ping_monitor.check('example.com', ping_count=1)
            
            assert 'error' in result
            assert 'Metrics error' in result['error']


# ============================================================================
# HTTP MONITOR TESTS
# ============================================================================

class TestHTTPMonitor:
    """Testes para HTTPMonitor"""
    
    @pytest.fixture
    def http_monitor(self, metrics_manager):
        """Fixture do HTTPMonitor"""
        return HTTPMonitor(metrics_manager)
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [200, 301, 404, 500])
    async def test_http_status_codes(self, http_monitor, status_code):
        """Testa diferentes códigos de status HTTP"""
        mock_response = AsyncMock()
        mock_response.status_code = status_code
        mock_response.content = b'test content'
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await http_monitor.check('example.com')
            
            assert result['status_code'] == status_code
            assert result['target'] == 'example.com'
            assert result['url'] == 'https://example.com'
            assert 'duration_ms' in result
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("exception_class,expected_error", [
        ('TimeoutException', 'timeout'),
        ('RequestError', 'error'),
    ])
    async def test_http_exceptions(self, http_monitor, exception_class, expected_error):
        """Testa diferentes exceções HTTP"""
        import httpx
        
        exception = getattr(httpx, exception_class)('Test error')
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=exception
            )
            
            result = await http_monitor.check('example.com')
            
            assert expected_error in result.get('error', result)
            assert result['target'] == 'example.com'


# ============================================================================
# METRICS MANAGER TESTS
# ============================================================================

class TestMetricsManager:
    """Testes para MetricsManager"""
    
    def test_metrics_manager_initialization(self):
        """Testa inicialização e disponibilidade de métricas"""
        with patch('src.metrics.OTLPMetricExporter'), \
             patch('src.metrics.PeriodicExportingMetricReader'), \
             patch('src.metrics.MeterProvider'):
            
            manager = MetricsManager(
                service_name='test-service',
                otel_endpoint='http://localhost:4317'
            )
            
            assert manager.service_name == 'test-service'
            assert manager.otel_endpoint == 'http://localhost:4317'
            
            # Verifica que todas as métricas necessárias existem
            for metric in ['ping_rtt', 'ping_packet_loss', 'http_duration', 'http_status']:
                assert hasattr(manager, metric)
    
    def test_metrics_recording(self):
        """Testa que métricas podem ser gravadas sem erros"""
        with patch('src.metrics.OTLPMetricExporter'), \
             patch('src.metrics.PeriodicExportingMetricReader'), \
             patch('src.metrics.MeterProvider'):
            
            manager = MetricsManager(
                service_name='test-service',
                otel_endpoint='http://localhost:4317'
            )
            
            # Testa gravação de cada tipo de métrica
            manager.ping_rtt.record(50.5, {"target": "example.com"})
            manager.ping_packet_loss.record(0.0, {"target": "example.com"})
            manager.http_duration.record(150.0, {
                "target": "example.com",
                "http.method": "GET",
                "http.status_code": 200
            })
            manager.http_status.add(1, {
                "target": "example.com",
                "http.method": "GET",
                "http.status_code": 200
            })


# ============================================================================
# HEALTH CHECK SERVER TESTS
# ============================================================================

class TestHealthCheckServer:
    """Testes para HealthCheckServer"""
    
    def test_health_check_handler_success(self):
        """Testa resposta de sucesso do health check"""
        from src.utils.health_check import HealthCheckHandler
        from io import BytesIO
        
        mock_wfile = BytesIO()
        handler = HealthCheckHandler.__new__(HealthCheckHandler)
        handler.wfile = mock_wfile
        handler.path = '/health'
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(200)
        handler.send_header.assert_called_with('Content-Type', 'application/json')
        assert mock_wfile.getvalue() == b'{"status": "healthy"}'
    
    def test_health_check_handler_not_found(self):
        """Testa resposta 404 para rota desconhecida"""
        from src.utils.health_check import HealthCheckHandler
        from io import BytesIO
        
        handler = HealthCheckHandler.__new__(HealthCheckHandler)
        handler.wfile = BytesIO()
        handler.path = '/unknown'
        handler.send_response = Mock()
        handler.end_headers = Mock()
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(404)
    
    def test_health_check_handler_silent_logging(self):
        """Testa que log_message é silencioso"""
        from src.utils.health_check import HealthCheckHandler
        
        handler = HealthCheckHandler.__new__(HealthCheckHandler)
        result = handler.log_message("test %s", "message")
        
        assert result is None
    
    def test_health_check_server_lifecycle(self):
        """Testa ciclo de vida do servidor (start/stop)"""
        from src.utils.health_check import HealthCheckServer

        with patch('src.utils.health_check.HTTPServer') as mock_http_server:
            mock_server_instance = Mock()
            mock_http_server.return_value = mock_server_instance
            
            server = HealthCheckServer(8080)
            server.server = mock_server_instance
            
            # Testa stop com servidor ativo
            server.stop()
            mock_server_instance.shutdown.assert_called_once()
            
            # Testa stop sem servidor (não deve lançar exceção)
            server.server = None
            server.stop()  # Não deve falhar


# ============================================================================
# NETWORK MONITOR TESTS
# ============================================================================

class TestNetworkMonitor:
    """Testes para NetworkMonitor"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, test_config):
        """Testa inicialização do NetworkMonitor"""
        with patch('src.monitoring.monitor.MetricsManager'):
            monitor = NetworkMonitor(test_config)
            
            assert monitor.config == test_config
            assert monitor.running is False
            assert hasattr(monitor, 'ping_monitor')
            assert hasattr(monitor, 'http_monitor')
    
    @pytest.mark.asyncio
    async def test_stop(self, test_config):
        """Testa parada do NetworkMonitor"""
        with patch('src.monitoring.monitor.MetricsManager'):
            monitor = NetworkMonitor(test_config)
            monitor.running = True
            
            await monitor.stop()
            
            assert monitor.running is False
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("loop_method,monitor_attr", [
        ('_ping_loop', 'ping_monitor'),
        ('_http_loop', 'http_monitor'),
    ])
    async def test_monitoring_loops(self, test_config, loop_method, monitor_attr):
        """Testa loops de monitoramento (ping e HTTP)"""
        with patch('src.monitoring.monitor.MetricsManager'):
            monitor = NetworkMonitor(test_config)
            
            # Mock do check específico
            check_mock = AsyncMock(return_value={'success': True})
            getattr(monitor, monitor_attr).check = check_mock
            
            # Executa loop e para após algumas iterações
            call_count = 0
            original_check = check_mock
            
            async def counting_check(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count >= 3:
                    monitor.running = False
                return await original_check(*args, **kwargs)
            
            getattr(monitor, monitor_attr).check = counting_check
            
            monitor.running = True
            await getattr(monitor, loop_method)()
            
            assert call_count >= 2
    
    @pytest.mark.asyncio
    async def test_run_with_exception(self, test_config):
        """Testa tratamento de exceção durante execução"""
        with patch('src.monitoring.monitor.MetricsManager'):
            monitor = NetworkMonitor(test_config)
            
            async def mock_ping_loop():
                await asyncio.sleep(0.05)
                raise Exception("Test error")
            
            async def mock_http_loop():
                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    pass
            
            monitor._ping_loop = mock_ping_loop
            monitor._http_loop = mock_http_loop
            
            await monitor.run()
            
            assert monitor.running is False

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Testes de integração simplificados"""
    
    def test_health_check_server_threading(self):
        """Testa servidor de health check em thread separada"""
        from src.utils.health_check import HealthCheckServer
        import threading
        import time
        
        server = HealthCheckServer(18080)
        
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        time.sleep(0.3)
        
        assert server.server is not None
        
        server.stop()
        time.sleep(0.1)
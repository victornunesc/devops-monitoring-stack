"""
Tests for ViaIpe Collector
"""
import pytest
import httpx
from unittest.mock import MagicMock, AsyncMock, patch

from src.collector import ViaIpeCollector
from src.utils.config import Config


@pytest.mark.asyncio
class TestViaIpeCollector:
    """Test suite for ViaIpeCollector"""

    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        return Config(
            api_url='https://test-api.example.com/api',
            poll_interval=1,  # Short interval for testing
            otel_endpoint='http://test-otel:4317',
            service_name='test-collector',
            health_port=8081,
            timeout=30
        )

    @pytest.fixture
    def mock_otel_setup(self):
        """Mock OpenTelemetry setup"""
        with patch('metrics.metrics_exporter.Resource'), \
             patch('metrics.metrics_exporter.OTLPMetricExporter'), \
             patch('metrics.metrics_exporter.PeriodicExportingMetricReader'), \
             patch('metrics.metrics_exporter.MeterProvider'), \
             patch('metrics.metrics_exporter.metrics') as mock_metrics:
            
            # Mock gauge
            mock_gauge = MagicMock()
            mock_gauge.set = MagicMock()
            
            # Mock counter
            mock_counter = MagicMock()
            mock_counter.add = MagicMock()
            
            mock_meter = MagicMock()
            mock_meter.create_gauge = MagicMock(return_value=mock_gauge)
            mock_meter.create_counter = MagicMock(return_value=mock_counter)
            mock_metrics.get_meter.return_value = mock_meter
            
            yield mock_metrics

    @pytest.fixture
    def collector(self, config, mock_otel_setup):
        """Create a collector instance"""
        collector = ViaIpeCollector(config)
        
        # Mock the metrics exporter methods
        collector.metrics_exporter.record_api_request = MagicMock()
        collector.metrics_exporter.record_clients_total = MagicMock()
        collector.metrics_exporter.record_client_metrics = MagicMock()
        
        return collector

    @pytest.fixture
    def sample_api_data(self):
        """Sample API response data"""
        return [
            {
                "id": "client1",
                "name": "Client 1",
                "data": {
                    "smoke": {
                        "val": 25.5,
                        "loss": 0.5,
                        "avg_loss": 1.2
                    },
                    "interfaces": [
                        {
                            "avg_in": 1000000,
                            "avg_out": 500000,
                            "max_in": 2000000,
                            "max_out": 1000000
                        }
                    ]
                }
            }
        ]

    def test_collector_initialization(self, collector, config):
        """Test collector initialization"""
        assert collector.config == config
        assert collector.running is False
        assert collector.api_client is not None
        assert collector.metrics_exporter is not None
        assert collector.data_processor is not None

    async def test_fetch_and_process_data_success(self, collector, sample_api_data):
        """Test successful data fetch and processing"""
        with patch.object(collector.api_client, 'fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_api_data
            
            await collector.fetch_and_process_data()
            
            mock_fetch.assert_called_once()
            collector.metrics_exporter.record_api_request.assert_called_with(success=True)

    async def test_fetch_and_process_data_timeout(self, collector):
        """Test handling of API timeout"""
        with patch.object(collector.api_client, 'fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = httpx.TimeoutException("Timeout")
            
            await collector.fetch_and_process_data()
            
            collector.metrics_exporter.record_api_request.assert_called_with(
                success=False,
                error_type="timeout"
            )

    async def test_fetch_and_process_data_http_error(self, collector):
        """Test handling of HTTP error"""
        with patch.object(collector.api_client, 'fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_fetch.side_effect = httpx.HTTPStatusError(
                "Server Error",
                request=MagicMock(),
                response=mock_response
            )
            
            await collector.fetch_and_process_data()
            
            collector.metrics_exporter.record_api_request.assert_called_with(
                success=False,
                error_type="http_500"
            )

    async def test_fetch_and_process_data_http_404(self, collector):
        """Test handling of HTTP 404 error"""
        with patch.object(collector.api_client, 'fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_fetch.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=mock_response
            )
            
            await collector.fetch_and_process_data()
            
            collector.metrics_exporter.record_api_request.assert_called_with(
                success=False,
                error_type="http_404"
            )

    async def test_fetch_and_process_data_unexpected_error(self, collector):
        """Test handling of unexpected error"""
        with patch.object(collector.api_client, 'fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Unexpected error")
            
            await collector.fetch_and_process_data()
            
            collector.metrics_exporter.record_api_request.assert_called_with(
                success=False,
                error_type="unknown"
            )

    async def test_collection_loop_runs_while_running(self, collector, sample_api_data):
        """Test collection loop runs while running flag is True"""
        collector.running = True
        
        with patch.object(collector, 'fetch_and_process_data', new_callable=AsyncMock) as mock_fetch:
            async def stop_after_first():
                if mock_fetch.call_count >= 1:
                    collector.running = False
            
            mock_fetch.side_effect = stop_after_first
            
            await collector.collection_loop()
            
            assert mock_fetch.call_count >= 1

    async def test_collection_loop_respects_poll_interval(self, collector):
        """Test collection loop respects poll interval"""
        collector.running = True
        collector.config.poll_interval = 0.1  # Very short for testing
        
        call_times = []
        
        with patch.object(collector, 'fetch_and_process_data', new_callable=AsyncMock) as mock_fetch:
            import time
            
            async def record_time():
                call_times.append(time.time())
                if len(call_times) >= 2:
                    collector.running = False
            
            mock_fetch.side_effect = record_time
            
            await collector.collection_loop()
            
            # Check that there was a delay between calls
            if len(call_times) >= 2:
                time_diff = call_times[1] - call_times[0]
                assert time_diff >= 0.1

    def test_stop_method(self, collector):
        """Test stop method sets running flag to False"""
        collector.running = True
        collector.stop()
        assert collector.running is False

    async def test_run_starts_collection(self, collector, sample_api_data):
        """Test run method starts collection loop"""
        with patch.object(collector, 'collection_loop', new_callable=AsyncMock) as mock_loop:
            # Make collection_loop return immediately
            mock_loop.return_value = None
            
            await collector.run()
            
            assert collector.running is False  # After run completes
            mock_loop.assert_called_once()

    async def test_run_handles_keyboard_interrupt(self, collector):
        """Test run method handles KeyboardInterrupt gracefully"""
        with patch.object(collector, 'collection_loop', new_callable=AsyncMock) as mock_loop:
            mock_loop.side_effect = KeyboardInterrupt()
            
            await collector.run()
            
            assert collector.running is False

    async def test_run_handles_exception(self, collector):
        """Test run method handles exceptions"""
        with patch.object(collector, 'collection_loop', new_callable=AsyncMock) as mock_loop:
            mock_loop.side_effect = Exception("Test error")
            
            await collector.run()
            
            assert collector.running is False

    async def test_integration_fetch_and_process(self, collector):
        """Test integration of fetch and process"""
        sample_data = [
            {
                "id": "test-client",
                "name": "Test Client",
                "data": {
                    "smoke": {"val": 20, "loss": 0.3, "avg_loss": 1.0},
                    "interfaces": [
                        {"avg_in": 500000, "avg_out": 250000, "max_in": 1000000, "max_out": 500000}
                    ]
                }
            }
        ]
        
        with patch.object(collector.api_client, 'fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_data
            
            await collector.fetch_and_process_data()
            
            # Verify API request was recorded
            collector.metrics_exporter.record_api_request.assert_called_with(success=True)
            
            # Verify clients total was recorded
            collector.metrics_exporter.record_clients_total.assert_called_with(1)
            
            # Verify client metrics were recorded
            assert collector.metrics_exporter.record_client_metrics.call_count >= 1

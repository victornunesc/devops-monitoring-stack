"""
Tests for metrics exporter
"""
import pytest
from unittest.mock import MagicMock, patch

from src.metrics.metrics_exporter import MetricsExporter


class TestMetricsExporter:
    """Test suite for MetricsExporter"""

    @pytest.fixture
    def mock_otel_setup(self):
        """Mock OpenTelemetry setup"""
        with patch('src.metrics.metrics_exporter.Resource'), \
             patch('src.metrics.metrics_exporter.OTLPMetricExporter'), \
             patch('src.metrics.metrics_exporter.PeriodicExportingMetricReader'), \
             patch('src.metrics.metrics_exporter.MeterProvider'), \
             patch('src.metrics.metrics_exporter.metrics') as mock_metrics:
            
            # Create a function that returns a new mock gauge each time
            def create_mock_gauge(*args, **kwargs):
                mock_gauge = MagicMock()
                return mock_gauge
            
            # Create a function that returns a new mock counter each time
            def create_mock_counter(*args, **kwargs):
                mock_counter = MagicMock()
                return mock_counter
            
            mock_meter = MagicMock()
            mock_meter.create_gauge = MagicMock(side_effect=create_mock_gauge)
            mock_meter.create_counter = MagicMock(side_effect=create_mock_counter)
            mock_metrics.get_meter.return_value = mock_meter
            
            yield mock_metrics

    @pytest.fixture
    def exporter(self, mock_otel_setup):
        """Create a metrics exporter instance"""
        return MetricsExporter(
            service_name="test-service",
            otel_endpoint="http://test-otel:4317"
        )

    def test_initialization(self, exporter):
        """Test metrics exporter initialization"""
        assert exporter.service_name == "test-service"
        assert exporter.otel_endpoint == "http://test-otel:4317"
        assert exporter.meter is not None

    def test_metrics_created(self, exporter):
        """Test that all required metrics are created"""
        assert hasattr(exporter, 'client_availability')
        assert hasattr(exporter, 'bandwidth_usage_in')
        assert hasattr(exporter, 'bandwidth_usage_out')
        assert hasattr(exporter, 'bandwidth_peak_in')
        assert hasattr(exporter, 'bandwidth_peak_out')
        assert hasattr(exporter, 'connection_quality')
        assert hasattr(exporter, 'smoke_latency')
        assert hasattr(exporter, 'smoke_loss')
        assert hasattr(exporter, 'api_requests')
        assert hasattr(exporter, 'api_errors')
        assert hasattr(exporter, 'clients_total')

    def test_record_client_metrics(self, exporter):
        """Test recording client metrics"""
        client_id = "client123"
        client_name = "Test Client"
        availability = 98.5
        bandwidth_stats = {
            'avg_in': 1000000,
            'avg_out': 500000,
            'max_in': 2000000,
            'max_out': 1000000
        }
        quality = 95.0
        smoke_data = {
            'val': 25.5,
            'loss': 0.5
        }
        
        exporter.record_client_metrics(
            client_id=client_id,
            client_name=client_name,
            availability=availability,
            bandwidth_stats=bandwidth_stats,
            quality=quality,
            smoke_data=smoke_data
        )
        
        # Verify metrics were set
        expected_attrs = {
            "client_id": client_id,
            "client_name": client_name
        }
        
        exporter.client_availability.set.assert_called_with(availability, expected_attrs)
        exporter.connection_quality.set.assert_called_with(quality, expected_attrs)
        exporter.bandwidth_usage_in.set.assert_called_with(bandwidth_stats['avg_in'], expected_attrs)
        exporter.bandwidth_usage_out.set.assert_called_with(bandwidth_stats['avg_out'], expected_attrs)
        exporter.bandwidth_peak_in.set.assert_called_with(bandwidth_stats['max_in'], expected_attrs)
        exporter.bandwidth_peak_out.set.assert_called_with(bandwidth_stats['max_out'], expected_attrs)
        exporter.smoke_latency.set.assert_called_with(25.5, expected_attrs)
        exporter.smoke_loss.set.assert_called_with(0.5, expected_attrs)

    def test_record_client_metrics_missing_smoke_values(self, exporter):
        """Test recording client metrics with missing smoke values"""
        smoke_data = {}
        bandwidth_stats = {
            'avg_in': 1000000,
            'avg_out': 500000,
            'max_in': 2000000,
            'max_out': 1000000
        }
        
        exporter.record_client_metrics(
            client_id="client123",
            client_name="Test Client",
            availability=98.5,
            bandwidth_stats=bandwidth_stats,
            quality=95.0,
            smoke_data=smoke_data
        )
        
        # Should use default value of 0
        expected_attrs = {
            "client_id": "client123",
            "client_name": "Test Client"
        }
        exporter.smoke_latency.set.assert_called_with(0.0, expected_attrs)
        exporter.smoke_loss.set.assert_called_with(0.0, expected_attrs)

    def test_record_clients_total(self, exporter):
        """Test recording total clients count"""
        exporter.record_clients_total(42)
        
        exporter.clients_total.set.assert_called_once_with(42, {})

    def test_record_clients_total_zero(self, exporter):
        """Test recording zero clients"""
        exporter.record_clients_total(0)
        
        exporter.clients_total.set.assert_called_once_with(0, {})

    def test_record_api_request_success(self, exporter):
        """Test recording successful API request"""
        exporter.record_api_request(success=True)
        
        exporter.api_requests.add.assert_called_once_with(1, {"status": "success"})
        exporter.api_errors.add.assert_not_called()

    def test_record_api_request_failure_with_error_type(self, exporter):
        """Test recording failed API request with error type"""
        exporter.record_api_request(success=False, error_type="timeout")
        
        exporter.api_errors.add.assert_called_once_with(1, {"error": "timeout"})
        exporter.api_requests.add.assert_not_called()

    def test_record_api_request_failure_without_error_type(self, exporter):
        """Test recording failed API request without error type"""
        exporter.record_api_request(success=False)
        
        exporter.api_errors.add.assert_called_once_with(1, {"error": "unknown"})

    def test_record_api_request_http_error(self, exporter):
        """Test recording API request with HTTP error"""
        exporter.record_api_request(success=False, error_type="http_500")
        
        exporter.api_errors.add.assert_called_once_with(1, {"error": "http_500"})

    def test_multiple_client_metrics_records(self, exporter):
        """Test recording metrics for multiple clients"""
        clients = [
            {
                "id": "client1",
                "name": "Client 1",
                "availability": 99.0,
                "bandwidth_stats": {'avg_in': 1000, 'avg_out': 500, 'max_in': 2000, 'max_out': 1000},
                "quality": 98.0,
                "smoke_data": {'val': 10, 'loss': 0.1}
            },
            {
                "id": "client2",
                "name": "Client 2",
                "availability": 95.0,
                "bandwidth_stats": {'avg_in': 2000, 'avg_out': 1000, 'max_in': 4000, 'max_out': 2000},
                "quality": 90.0,
                "smoke_data": {'val': 30, 'loss': 0.5}
            }
        ]
        
        for client in clients:
            exporter.record_client_metrics(
                client_id=client["id"],
                client_name=client["name"],
                availability=client["availability"],
                bandwidth_stats=client["bandwidth_stats"],
                quality=client["quality"],
                smoke_data=client["smoke_data"]
            )
        
        # Should have been called twice
        assert exporter.client_availability.set.call_count == 2
        assert exporter.connection_quality.set.call_count == 2

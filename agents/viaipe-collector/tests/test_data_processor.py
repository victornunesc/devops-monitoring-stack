"""
Tests for data processor
"""
import pytest
from unittest.mock import MagicMock

from src.metrics.data_processor import DataProcessor
from src.metrics.metrics_exporter import MetricsExporter


class TestDataProcessor:
    """Test suite for DataProcessor"""

    @pytest.fixture
    def mock_metrics_exporter(self):
        """Create a mock metrics exporter"""
        exporter = MagicMock(spec=MetricsExporter)
        exporter.record_client_metrics = MagicMock()
        exporter.record_clients_total = MagicMock()
        return exporter

    @pytest.fixture
    def processor(self, mock_metrics_exporter):
        """Create a data processor instance"""
        return DataProcessor(mock_metrics_exporter)

    @pytest.fixture
    def sample_client_data(self):
        """Sample client data"""
        return {
            "id": "client123",
            "name": "Test Client",
            "data": {
                "smoke": {
                    "val": 25.5,
                    "loss": 0.5,
                    "avg_loss": 1.2
                },
                "interfaces": [
                    {
                        "name": "eth0",
                        "avg_in": 1000000,
                        "avg_out": 500000,
                        "max_in": 2000000,
                        "max_out": 1000000
                    }
                ]
            }
        }

    def test_process_client_data_success(self, processor, mock_metrics_exporter, sample_client_data):
        """Test successful client data processing"""
        processor.process_client_data(sample_client_data)
        
        # Verify metrics exporter was called
        mock_metrics_exporter.record_client_metrics.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_metrics_exporter.record_client_metrics.call_args
        assert call_args[1]["client_id"] == "client123"
        assert call_args[1]["client_name"] == "Test Client"
        assert call_args[1]["availability"] == 98.8  # 100 - 1.2
        assert call_args[1]["bandwidth_stats"]["avg_in"] == 1000000
        assert call_args[1]["quality"] > 0

    def test_process_client_data_missing_id(self, processor, mock_metrics_exporter):
        """Test processing client data with missing ID"""
        client_data = {
            "name": "Test Client",
            "data": {
                "smoke": {"val": 25, "loss": 0, "avg_loss": 0},
                "interfaces": []
            }
        }
        
        processor.process_client_data(client_data)
        
        # Should use 'unknown' as default ID
        call_args = mock_metrics_exporter.record_client_metrics.call_args
        assert call_args[1]["client_id"] == "unknown"

    def test_process_client_data_missing_name(self, processor, mock_metrics_exporter):
        """Test processing client data with missing name"""
        client_data = {
            "id": "client123",
            "data": {
                "smoke": {"val": 25, "loss": 0, "avg_loss": 0},
                "interfaces": []
            }
        }
        
        processor.process_client_data(client_data)
        
        # Should use 'Unknown' as default name
        call_args = mock_metrics_exporter.record_client_metrics.call_args
        assert call_args[1]["client_name"] == "Unknown"

    def test_process_client_data_missing_smoke_data(self, processor, mock_metrics_exporter):
        """Test processing client data with missing smoke data"""
        client_data = {
            "id": "client123",
            "name": "Test Client",
            "data": {
                "interfaces": []
            }
        }
        
        processor.process_client_data(client_data)
        
        # Should handle missing smoke data gracefully
        mock_metrics_exporter.record_client_metrics.assert_called_once()

    def test_process_client_data_missing_interfaces(self, processor, mock_metrics_exporter):
        """Test processing client data with missing interfaces"""
        client_data = {
            "id": "client123",
            "name": "Test Client",
            "data": {
                "smoke": {"val": 25, "loss": 0, "avg_loss": 0}
            }
        }
        
        processor.process_client_data(client_data)
        
        # Should handle missing interfaces gracefully
        call_args = mock_metrics_exporter.record_client_metrics.call_args
        assert call_args[1]["bandwidth_stats"]["avg_in"] == 0

    def test_process_client_data_empty_interfaces(self, processor, mock_metrics_exporter):
        """Test processing client data with empty interfaces list"""
        client_data = {
            "id": "client123",
            "name": "Test Client",
            "data": {
                "smoke": {"val": 25, "loss": 0, "avg_loss": 0},
                "interfaces": []
            }
        }
        
        processor.process_client_data(client_data)
        
        call_args = mock_metrics_exporter.record_client_metrics.call_args
        assert call_args[1]["bandwidth_stats"]["avg_in"] == 0
        assert call_args[1]["bandwidth_stats"]["avg_out"] == 0

    def test_process_client_data_exception_handling(self, processor, mock_metrics_exporter):
        """Test exception handling in process_client_data"""
        # Pass invalid data that will cause an exception
        invalid_data = None
        
        # Should not raise exception
        processor.process_client_data(invalid_data)
        
        # Metrics should not be recorded
        mock_metrics_exporter.record_client_metrics.assert_not_called()

    def test_process_api_data_list(self, processor, mock_metrics_exporter, sample_client_data):
        """Test processing API data with list of clients"""
        api_data = [sample_client_data, sample_client_data]
        
        processor.process_api_data(api_data)
        
        # Should record total clients
        mock_metrics_exporter.record_clients_total.assert_called_once_with(2)
        
        # Should process each client
        assert mock_metrics_exporter.record_client_metrics.call_count == 2

    def test_process_api_data_single_client(self, processor, mock_metrics_exporter, sample_client_data):
        """Test processing API data with single client"""
        api_data = [sample_client_data]
        
        processor.process_api_data(api_data)
        
        mock_metrics_exporter.record_clients_total.assert_called_once_with(1)
        mock_metrics_exporter.record_client_metrics.assert_called_once()

    def test_process_api_data_empty_list(self, processor, mock_metrics_exporter):
        """Test processing empty API data"""
        api_data = []
        
        processor.process_api_data(api_data)
        
        # Should not process anything
        mock_metrics_exporter.record_clients_total.assert_not_called()
        mock_metrics_exporter.record_client_metrics.assert_not_called()

    def test_process_api_data_none(self, processor, mock_metrics_exporter):
        """Test processing None API data"""
        processor.process_api_data(None)
        
        # Should not process anything
        mock_metrics_exporter.record_clients_total.assert_not_called()
        mock_metrics_exporter.record_client_metrics.assert_not_called()

    def test_process_api_data_invalid_format(self, processor, mock_metrics_exporter):
        """Test processing API data with invalid format (not a list)"""
        api_data = {"error": "not a list"}
        
        processor.process_api_data(api_data)
        
        # Should not process non-list data
        mock_metrics_exporter.record_clients_total.assert_not_called()
        mock_metrics_exporter.record_client_metrics.assert_not_called()

    def test_process_api_data_multiple_clients_with_different_data(self, processor, mock_metrics_exporter):
        """Test processing multiple clients with different data"""
        api_data = [
            {
                "id": "client1",
                "name": "Client 1",
                "data": {
                    "smoke": {"val": 10, "loss": 0, "avg_loss": 0.5},
                    "interfaces": [{"avg_in": 1000, "avg_out": 500, "max_in": 2000, "max_out": 1000}]
                }
            },
            {
                "id": "client2",
                "name": "Client 2",
                "data": {
                    "smoke": {"val": 50, "loss": 2, "avg_loss": 5.0},
                    "interfaces": []
                }
            }
        ]
        
        processor.process_api_data(api_data)
        
        mock_metrics_exporter.record_clients_total.assert_called_once_with(2)
        assert mock_metrics_exporter.record_client_metrics.call_count == 2

    def test_processor_calculator_integration(self, processor):
        """Test that processor uses calculator correctly"""
        assert processor.calculator is not None
        assert hasattr(processor.calculator, 'calculate_availability')
        assert hasattr(processor.calculator, 'calculate_bandwidth_stats')
        assert hasattr(processor.calculator, 'calculate_quality_score')

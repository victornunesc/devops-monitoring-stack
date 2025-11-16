"""
Data processor module
"""
import logging
from typing import Dict, Any

from .metrics_calculator import MetricsCalculator
from .metrics_exporter import MetricsExporter

logger = logging.getLogger(__name__)


class DataProcessor:
    """ViaIpe client data processor"""
    
    def __init__(self, metrics_exporter: MetricsExporter):
        self.metrics_exporter = metrics_exporter
        self.calculator = MetricsCalculator()
    
    def process_client_data(self, client: Dict[str, Any]):
        """
        Processes client data and sends metrics
        
        (via OpenTelemetry → VictoriaMetrics)
        
        Args:
            client: Complete client data from API
        """
        try:
            client_id = client.get('id', 'unknown')
            client_name = client.get('name', 'Unknown')
            data = client.get('data', {})
            
            smoke_data = data.get('smoke', {})
            
            interfaces = data.get('interfaces', [])
            
            availability = self.calculator.calculate_availability(smoke_data)
            bandwidth_stats = self.calculator.calculate_bandwidth_stats(interfaces)
            quality = self.calculator.calculate_quality_score(availability, smoke_data)
            
            self.metrics_exporter.record_client_metrics(
                client_id=client_id,
                client_name=client_name,
                availability=availability,
                bandwidth_stats=bandwidth_stats,
                quality=quality,
                smoke_data=smoke_data
            )
            
            logger.info(
                f"Processed client '{client_name}' ({client_id}): "
                f"Availability={availability:.2f}%, "
                f"BW In={bandwidth_stats['avg_in']:.2f}bps, "
                f"BW Out={bandwidth_stats['avg_out']:.2f}bps, "
                f"Quality={quality:.2f}, "
                f"Latency={smoke_data.get('val', 0)}ms"
            )
            
        except Exception as e:
            logger.error(f"Error processing client: {e}")
    
    def process_api_data(self, data: Any):
        """
        Processes ViaIpe API data
        
        Args:
            data: Data returned by API (list of clients)
        """
        if not data:
            logger.warning("No data to process")
            return
        
        if isinstance(data, list):
            logger.info(f"Processing {len(data)} clients")
            self.metrics_exporter.record_clients_total(len(data))
            
            for client in data:
                self.process_client_data(client)
        else:
            logger.warning(f"Unexpected data format: {type(data)}, expected list")

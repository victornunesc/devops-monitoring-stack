"""
ViaIpe Collector service module
"""
import asyncio
import logging
import httpx

from utils.config import Config
from api_client import ViaIpeClient
from metrics.data_processor import DataProcessor
from metrics.metrics_exporter import MetricsExporter

logger = logging.getLogger(__name__)


class ViaIpeCollector:
    """ViaIpe statistics collector with OpenTelemetry"""
    
    def __init__(self, config: Config):
        self.config = config
        self.running = False
        
        self.api_client = ViaIpeClient(config.api_url, config.timeout)
        self.metrics_exporter = MetricsExporter(config.service_name, config.otel_endpoint)
        self.data_processor = DataProcessor(self.metrics_exporter)
        
        logger.info(f"ViaIpe Collector initialized with API: {config.api_url}")
    
    async def fetch_and_process_data(self):
        """Fetches data from API and processes it"""
        try:
            data = await self.api_client.fetch_data()
            
            self.metrics_exporter.record_api_request(success=True)
            
            self.data_processor.process_api_data(data)
            
        except httpx.TimeoutException:
            self.metrics_exporter.record_api_request(success=False, error_type="timeout")
            
        except httpx.HTTPStatusError as e:
            error_type = f"http_{e.response.status_code}"
            self.metrics_exporter.record_api_request(success=False, error_type=error_type)
            
        except Exception as e:
            logger.error(f"Unexpected error during data collection: {e}")
            self.metrics_exporter.record_api_request(success=False, error_type="unknown")
    
    async def collection_loop(self):
        """Data collection loop"""
        while self.running:
            logger.info("Starting ViaIpe data collection...")
            
            await self.fetch_and_process_data()
            
            logger.info(f"Waiting {self.config.poll_interval}s for next collection...")
            await asyncio.sleep(self.config.poll_interval)
    
    async def run(self):
        """Runs the collection loop"""
        self.running = True
        logger.info("ViaIpe Collector started")
        
        try:
            await self.collection_loop()
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
        except Exception as e:
            logger.error(f"Collector error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """Stops the collector"""
        logger.info("Stopping ViaIpe Collector...")
        self.running = False

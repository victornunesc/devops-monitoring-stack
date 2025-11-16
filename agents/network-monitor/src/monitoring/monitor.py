"""
Network Monitor orchestrator
"""
import asyncio
import logging

from src.utils import Config
from src.metrics import MetricsManager
from .ping_monitor import PingMonitor
from .http_monitor import HTTPMonitor

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """Network monitor with OpenTelemetry"""
    
    def __init__(self, config: Config):
        """
        Initializes the network monitor
        
        Args:
            config: Monitor configuration
        """
        self.config = config
        self.running = False
        
        self.metrics_manager = MetricsManager(
            service_name=config.service_name,
            otel_endpoint=config.otel_endpoint
        )
        
        self.ping_monitor = PingMonitor(self.metrics_manager)
        self.http_monitor = HTTPMonitor(self.metrics_manager)
        
        logger.info(f"Network Monitor initialized with targets: {config.targets}")

    async def run(self):
        """Runs the monitoring loops"""
        self.running = True
        logger.info("Network Monitor started")
        
        try:
            await asyncio.gather(
                self._ping_loop(),
                self._http_loop()
            )
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
            self.running = False
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            self.running = False
    
    async def stop(self):
        """Stops the monitor"""
        logger.info("Stopping Network Monitor...")
        self.running = False
    
    async def _ping_loop(self):
        """Ping checks loop"""
        while self.running:
            logger.info("Starting ping checks...")
            tasks = [
                self.ping_monitor.check(target) 
                for target in self.config.targets
            ]
            await asyncio.gather(*tasks)
            await asyncio.sleep(self.config.ping_interval)
    
    async def _http_loop(self):
        """HTTP checks loop"""
        while self.running:
            logger.info("Starting HTTP checks...")
            tasks = [
                self.http_monitor.check(target) 
                for target in self.config.targets
            ]
            await asyncio.gather(*tasks)
            await asyncio.sleep(self.config.http_interval)

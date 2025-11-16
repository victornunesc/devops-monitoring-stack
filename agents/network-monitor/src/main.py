"""
Network Monitor Agent - Teste Técnico DevOps
Monitora latência (ping) e HTTP de targets específicos
"""
import asyncio
import logging
import threading

from monitoring.monitor import NetworkMonitor
from utils.config import Config
from utils.health_check import HealthCheckServer


logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function"""
    config = Config.from_env()
    
    health_server = HealthCheckServer(config.health_port)
    health_thread = threading.Thread(
        target=health_server.start,
        daemon=True
    )
    health_thread.start()
    
    monitor = NetworkMonitor(config)
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
"""
ViaIpe Collector Agent - Teste Técnico DevOps
Coleta estatísticas da API ViaIpe e calcula métricas de qualidade
"""
import asyncio
import logging
import threading

from utils.config import Config
from utils.health_check import HealthCheckServer
from .collector import ViaIpeCollector

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
    
    collector = ViaIpeCollector(config)
    await collector.run()


if __name__ == "__main__":
    asyncio.run(main())
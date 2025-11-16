"""
Configuration module for ViaIpe Collector
"""
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Agent configuration"""
    api_url: str
    poll_interval: int
    otel_endpoint: str
    service_name: str
    health_port: int
    timeout: int

    @classmethod
    def from_env(cls) -> 'Config':
        """Loads configuration from environment variables"""
        return cls(
            api_url=os.getenv('VIAIPE_API_URL', 'https://legadoviaipe.rnp.br/api/norte'),
            poll_interval=int(os.getenv('VIAIPE_POLL_INTERVAL', '60')),
            otel_endpoint=os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://otel-collector:4317'),
            service_name=os.getenv('OTEL_SERVICE_NAME', 'viaipe-collector'),
            health_port=int(os.getenv('HEALTH_PORT', '8081')),
            timeout=int(os.getenv('VIAIPE_TIMEOUT', '30'))
        )

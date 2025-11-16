"""
Configuration module for Network Monitor
"""
import os
from typing import List
from dataclasses import dataclass


@dataclass
class Config:
    """Agent configuration"""
    targets: List[str]
    ping_interval: int
    http_interval: int
    otel_endpoint: str
    service_name: str
    health_port: int

    @classmethod
    def from_env(cls) -> 'Config':
        """Loads configuration from environment variables"""
        return cls(
            targets=os.getenv('MONITOR_TARGETS', 'google.com,youtube.com,rnp.br').split(','),
            ping_interval=int(os.getenv('PING_INTERVAL', '30')),
            http_interval=int(os.getenv('HTTP_INTERVAL', '60')),
            otel_endpoint=os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://otel-collector:4317'),
            service_name=os.getenv('OTEL_SERVICE_NAME', 'network-monitor'),
            health_port=int(os.getenv('HEALTH_PORT', '8080'))
        )

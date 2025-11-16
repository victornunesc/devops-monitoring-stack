"""
OpenTelemetry metrics setup module
"""
import logging
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)


class MetricsExporter:
    """OpenTelemetry metrics manager"""
    
    def __init__(self, service_name: str, otel_endpoint: str):
        self.service_name = service_name
        self.otel_endpoint = otel_endpoint
        
        self._setup_otel()

        self._create_metrics()
    
    def _setup_otel(self):
        """Configures OpenTelemetry provider"""
        resource = Resource.create({
            "service.name": self.service_name,
            "service.namespace": "monitoring",
            "deployment.environment": "production"
        })
        
        exporter = OTLPMetricExporter(
            endpoint=self.otel_endpoint,
            insecure=True
        )
        
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=10000)
        
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)
        
        self.meter = metrics.get_meter(__name__)
        
        logger.info(f"OpenTelemetry configured for service: {self.service_name}")
    
    def _create_metrics(self):
        """Creates service metrics"""

        self.client_availability = self.meter.create_gauge(
            name="viaipe.client.availability",
            description="Client availability percentage based on smoke ping loss",
            unit="%"
        )
        
        self.bandwidth_usage_in = self.meter.create_gauge(
            name="viaipe.bandwidth.usage.in",
            description="Average inbound bandwidth usage",
            unit="bps"
        )
        
        self.bandwidth_usage_out = self.meter.create_gauge(
            name="viaipe.bandwidth.usage.out",
            description="Average outbound bandwidth usage",
            unit="bps"
        )
        
        self.bandwidth_peak_in = self.meter.create_gauge(
            name="viaipe.bandwidth.peak.in",
            description="Peak inbound bandwidth",
            unit="bps"
        )
        
        self.bandwidth_peak_out = self.meter.create_gauge(
            name="viaipe.bandwidth.peak.out",
            description="Peak outbound bandwidth",
            unit="bps"
        )
        
        self.connection_quality = self.meter.create_gauge(
            name="viaipe.connection.quality",
            description="Connection quality score (0-100)",
            unit="score"
        )
        
        self.smoke_latency = self.meter.create_gauge(
            name="viaipe.smoke.latency",
            description="Smoke ping latency",
            unit="ms"
        )
        
        self.smoke_loss = self.meter.create_gauge(
            name="viaipe.smoke.loss",
            description="Smoke ping packet loss",
            unit="%"
        )
        
        self.api_requests = self.meter.create_counter(
            name="viaipe.api.requests",
            description="Number of API requests",
            unit="1"
        )
        
        self.api_errors = self.meter.create_counter(
            name="viaipe.api.errors",
            description="Number of API errors",
            unit="1"
        )
        
        self.clients_total = self.meter.create_gauge(
            name="viaipe.clients.total",
            description="Total number of clients",
            unit="1"
        )
    
    def record_client_metrics(
        self,
        client_id: str,
        client_name: str,
        availability: float,
        bandwidth_stats: dict,
        quality: float,
        smoke_data: dict
    ):
        """
        Records client metrics
        
        Args:
            client_id: Client ID
            client_name: Client name
            availability: Availability in %
            bandwidth_stats: Dict with avg_in, avg_out, max_in, max_out
            quality: Quality score (0-100)
            smoke_data: Smoke ping data (val, loss)
        """
        attributes = {
            "client_id": client_id,
            "client_name": client_name
        }
        
        self.client_availability.set(availability, attributes)
        self.connection_quality.set(quality, attributes)
        
        self.bandwidth_usage_in.set(bandwidth_stats['avg_in'], attributes)
        self.bandwidth_usage_out.set(bandwidth_stats['avg_out'], attributes)
        self.bandwidth_peak_in.set(bandwidth_stats['max_in'], attributes)
        self.bandwidth_peak_out.set(bandwidth_stats['max_out'], attributes)
        
        self.smoke_latency.set(float(smoke_data.get('val', 0)), attributes)
        self.smoke_loss.set(float(smoke_data.get('loss', 0)), attributes)
    
    def record_clients_total(self, count: int):
        """
        Records the total number of clients
        
        Args:
            count: Number of clients
        """
        self.clients_total.set(count, {})
    
    def record_api_request(self, success: bool, error_type: str = None):
        """
        Records an API request
        
        Args:
            success: Whether the request was successful
            error_type: Error type (if any)
        """
        if success:
            self.api_requests.add(1, {"status": "success"})
        else:
            self.api_errors.add(1, {"error": error_type or "unknown"})

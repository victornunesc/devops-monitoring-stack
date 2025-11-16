"""
OpenTelemetry metrics module
"""
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource


class MetricsManager:
    """OpenTelemetry metrics manager"""
    
    def __init__(self, service_name: str, otel_endpoint: str):
        """
        Initializes the metrics manager
        
        Args:
            service_name: Service name
            otel_endpoint: OTEL Collector endpoint
        """
        self.service_name = service_name
        self.otel_endpoint = otel_endpoint
        self._setup_provider()
        self.meter = metrics.get_meter(__name__)
        self._create_metrics()
    
    def _setup_provider(self):
        """Configures the OpenTelemetry provider"""
        resource = Resource.create({
            "service.name": self.service_name,
            "service.namespace": "monitoring",
            "deployment.environment": "production"
        })
        
        exporter = OTLPMetricExporter(
            endpoint=self.otel_endpoint,
            insecure=True
        )
        
        reader = PeriodicExportingMetricReader(
            exporter, 
            export_interval_millis=10000
        )
        
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)
    
    def _create_metrics(self):
        """Creates metrics following OpenTelemetry conventions"""
        self.ping_rtt = self.meter.create_histogram(
            name="network.ping.rtt",
            description="Ping round-trip time in milliseconds",
            unit="ms"
        )
        
        self.ping_packet_loss = self.meter.create_histogram(
            name="network.ping.packet_loss",
            description="Ping packet loss percentage",
            unit="%"
        )
        
        self.http_duration = self.meter.create_histogram(
            name="http.client.duration",
            description="HTTP request duration in milliseconds",
            unit="ms"
        )
        
        self.http_status = self.meter.create_counter(
            name="http.client.status",
            description="HTTP response status code count",
            unit="1"
        )

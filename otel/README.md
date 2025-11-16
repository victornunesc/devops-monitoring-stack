# OpenTelemetry Collector

Pipeline de telemetria centralizado para processamento de métricas seguindo padrões CNCF.

## 📋 Visão Geral

O OpenTelemetry Collector atua como um **middleware de telemetria** que recebe, processa e exporta métricas dos agentes de monitoramento para o backend de armazenamento (VictoriaMetrics).

## 🏗️ Arquitetura do Pipeline

```
┌─────────────┐
│  Receivers  │  ◄─── Recebe métricas via OTLP (gRPC/HTTP)
└──────┬──────┘
       │
┌──────▼──────┐
│ Processors  │  ◄─── Transforma, agrega e enriquece
└──────┬──────┘
       │
┌──────▼──────┐
│  Exporters  │  ◄─── Envia para storage backend
└─────────────┘
```

## ⚙️ Componentes

### Receivers

Recebem telemetria dos agentes em formato OTLP (OpenTelemetry Protocol):

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317  # Porta padrão OTLP gRPC
      http:
        endpoint: 0.0.0.0:4318  # Porta padrão OTLP HTTP
```

**Protocolos suportados:**
- **gRPC** (porta 4317): Alta performance, binary protocol
- **HTTP** (porta 4318): REST-based, maior compatibilidade

### Processors

Transformam e enriquecem os dados antes do export:

#### 1. Memory Limiter
Protege o collector contra OOM (Out of Memory):

```yaml
memory_limiter:
  limit_mib: 512          # Limite de memória: 512 MB
  spike_limit_mib: 128    # Limite para picos: 128 MB
  check_interval: 1s      # Intervalo de verificação
```

**Comportamento:**
- Monitora uso de memória a cada segundo
- Rejeita novos dados quando próximo ao limite
- Previne crashes por falta de memória

#### 2. Batch Processor
Agrupa métricas para otimizar a exportação:

```yaml
batch:
  timeout: 10s           # Envia batch a cada 10s
  send_batch_size: 1024  # Ou quando atingir 1024 métricas
```

**Benefícios:**
- Reduz número de requisições ao backend
- Otimiza uso de rede
- Melhora throughput geral

#### 3. Resource Processor
Adiciona metadados contextuais:

```yaml
resource:
  attributes:
    - key: service.namespace
      value: monitoring
      action: insert
```

**Função:**
- Enriquece métricas com contexto adicional
- Facilita filtragem e agregação
- Padroniza metadados

### Exporters

Enviam dados processados para backends de armazenamento:

#### 1. Prometheus Remote Write
Exporta para VictoriaMetrics:

```yaml
prometheusremotewrite:
  endpoint: http://victoriametrics:8428/api/v1/write
  tls:
    insecure: true  # Comunicação interna sem TLS
```

**Características:**
- Protocolo Prometheus Remote Write
- Compatível com VictoriaMetrics
- Alta performance

#### 2. Logging Exporter
Logs para debug e auditoria:

```yaml
logging:
  loglevel: info
```

**Uso:**
- Debug durante desenvolvimento
- Auditoria de métricas
- Troubleshooting

## 🔧 Configuração

### Service Configuration

```yaml
service:
  extensions: [health_check]
  
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [prometheusremotewrite, logging]
  
  telemetry:
    logs:
      level: info
    metrics:
      address: 0.0.0.0:8888  # Métricas internas do collector
```

### Extensions

```yaml
extensions:
  health_check:
    endpoint: 0.0.0.0:13133  # Health check endpoint
```

## 🌐 Portas Expostas

| Porta | Protocolo | Descrição |
|-------|-----------|-----------|
| 4317 | gRPC | OTLP receiver (binary) |
| 4318 | HTTP | OTLP receiver (JSON) |
| 8888 | HTTP | Métricas internas (Prometheus format) |
| 13133 | HTTP | Health check endpoint |

## 📊 Métricas Internas

O collector exporta suas próprias métricas em `http://localhost:8888/metrics`:

```promql
# Taxa de métricas recebidas
rate(otelcol_receiver_accepted_metric_points[1m])

# Taxa de métricas exportadas
rate(otelcol_exporter_sent_metric_points[1m])

# Métricas descartadas
rate(otelcol_processor_dropped_metric_points[1m])

# Uso de memória
process_runtime_go_mem_heap_alloc_bytes
```

## 🔄 Pipeline Flow

```
Network Monitor ─┐
                 ├─► OTLP Receiver
ViaIPE Collector ┘        │
                          │
                   ┌──────▼──────┐
                   │ Memory Check│
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │   Resource  │ (add namespace)
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │    Batch    │ (aggregate)
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │  Exporters  │
                   └──────┬──────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
    ┌─────▼─────┐                  ┌─────▼─────┐
    │ VictoriaM │                  │  Logging  │
    └───────────┘                  └───────────┘
```

## 📚 Referências

- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)
- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)
- [Prometheus Remote Write](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#remote_write)
- [VictoriaMetrics Integration](https://docs.victoriametrics.com/Single-server-VictoriaMetrics.html#prometheus-setup)

## ⚡ Performance

### Tuning Recommendations

```yaml
# Para alta carga, ajuste:
processors:
  batch:
    timeout: 5s              # Reduzir timeout
    send_batch_size: 2048    # Aumentar batch size
  
  memory_limiter:
    limit_mib: 1024          # Aumentar limite de memória
    spike_limit_mib: 256
```

### Horizontal Scaling

Para escalar o collector:

```yaml
# docker-compose.yml
otel-collector:
  deploy:
    replicas: 3
```

Configure um load balancer (nginx/HAProxy) na frente dos collectors.

## 📈 Monitoramento

### KPIs do Collector

- **Throughput**: Métricas processadas por segundo
- **Latency**: Tempo de processamento no pipeline
- **Drop Rate**: Taxa de métricas descartadas
- **Memory Usage**: Uso de memória
- **Error Rate**: Taxa de erros de export

---

Para voltar ao README principal: [📖 README.md](../README.md)

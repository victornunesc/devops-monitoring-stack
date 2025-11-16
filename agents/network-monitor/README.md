# Network Monitor Agent

Agente de monitoramento de rede que realiza testes de latência (ping) e HTTP com exportação via OpenTelemetry.

## 📋 Visão Geral

O Network Monitor é um agente especializado que:
- 🏓 Monitora latência via ICMP ping
- 🌐 Monitora disponibilidade e tempo de resposta HTTP/HTTPS
- 📊 Exporta métricas via OpenTelemetry (OTLP)
- ✅ Fornece health check endpoint
- 🎯 Suporta múltiplos targets configuráveis

## 🏗️ Estrutura do Projeto

```
agents/network-monitor/
├── Dockerfile              # Container image definition
├── requirements.txt        # Python dependencies
├── pytest.ini             # Pytest configuration
├── README.md              # Este arquivo
├── src/                   # Código fonte
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── metrics.py         # OpenTelemetry metrics manager
│   ├── monitoring/        # Módulo de monitoramento
│   │   ├── __init__.py
│   │   ├── monitor.py         # Orquestrador principal
│   │   ├── ping_monitor.py    # Monitor de latência (ICMP)
│   │   └── http_monitor.py    # Monitor HTTP/HTTPS
│   └── utils/             # Utilitários
│       ├── __init__.py
│       ├── config.py          # Configuration management
│       └── health_check.py    # Health check server
└── tests/                 # Testes unitários
    ├── ...
```

## 🎯 Responsabilidades

### Monitor (`monitor.py`)
- Orquestração dos ciclos de monitoramento
- Loops assíncronos independentes para ping e HTTP
- Coordenação de múltiplos targets
- Logging e observabilidade

### Ping Monitor (`ping_monitor.py`)
- Execução de testes ICMP ping
- Cálculo de latência média (RTT)
- Detecção de packet loss
- Estatísticas de conectividade

### HTTP Monitor (`http_monitor.py`)
- Requisições HTTP/HTTPS
- Medição de tempo de carregamento
- Captura de status codes
- Suporte a redirects

### Metrics Manager (`metrics.py`)
- Configuração do OpenTelemetry SDK
- Criação e gerenciamento de métricas
- Export periódico via OTLP gRPC
- Resource attributes e namespacing

### Config (`config.py`)
- Carregamento de variáveis de ambiente
- Validação de configurações
- Defaults seguros

### Health Check (`health_check.py`)
- Endpoint HTTP `/health`
- Status do agente
- Informações de uptime

## 📊 Métricas Coletadas

### Métricas de Ping (ICMP)

```python
# Exemplos de métricas exportadas
network.ping.latency_ms (Gauge)
  - Latência média em milissegundos
  - Labels: target, protocol=icmp

network.ping.packet_loss_percentage (Gauge)
  - Percentual de perda de pacotes (0-100)
  - Labels: target

network.ping.availability (Gauge)
  - Status de disponibilidade (0=down, 1=up)
  - Labels: target
```

### Métricas HTTP

```python
network.http.response_time_ms (Histogram)
  - Tempo de resposta HTTP em ms
  - Labels: target, status_code, method=GET

network.http.availability (Gauge)
  - Status de disponibilidade HTTP (0=down, 1=up)
  - Labels: target

network.http.status_code (Counter)
  - Contador de códigos de status
  - Labels: target, status_code
```

### Métricas do Sistema

```python
network.monitor.checks_total (Counter)
  - Total de verificações realizadas
  - Labels: target, check_type (ping|http), status (success|error)

network.monitor.errors_total (Counter)
  - Total de erros durante monitoramento
  - Labels: target, check_type, error_type
```

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# Targets de Monitoramento
MONITOR_TARGETS=google.com,youtube.com,rnp.br    # Lista separada por vírgulas

# Intervalos de Monitoramento
PING_INTERVAL=30                                 # Intervalo de ping em segundos
HTTP_INTERVAL=60                                 # Intervalo de HTTP em segundos

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=network-monitor

# Health Check
HEALTH_PORT=8080

# Logging
LOG_LEVEL=INFO                                   # DEBUG, INFO, WARNING, ERROR
```

### Configuração Avançada

```python
# src/utils/config.py
@dataclass
class Config:
    # Monitoring targets
    targets: List[str]
    
    # Intervals (seconds)
    ping_interval: int = 30
    http_interval: int = 60
    
    # OTEL Settings
    otel_endpoint: str
    service_name: str = "network-monitor"
    
    # Health Check
    health_port: int = 8080
```

## 🚀 Uso

### Com Docker Compose

```bash
# Iniciar o serviço
docker compose up -d network-monitor

# Visualizar logs
docker compose logs -f network-monitor

# Verificar health
curl http://localhost:8080/health
```

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/test_monitors.py -v

# Ver relatório de cobertura
open htmlcov/index.html
```

## 🔍 Health Check

### Endpoint

```bash
GET http://localhost:8080/health
```

### Resposta Saudável

```json
{
  "status": "healthy",
  "service": "network-monitor",
  "timestamp": "2025-11-16T12:00:00Z",
  "uptime_seconds": 3600,
  "targets": ["google.com", "youtube.com", "rnp.br"],
  "checks_completed": {
    "ping": 120,
    "http": 60
  },
  "last_check": {
    "ping": "2025-11-16T11:59:30Z",
    "http": "2025-11-16T11:59:00Z"
  }
}
```

### Status Codes

- `200 OK`: Serviço saudável e operacional
- `503 Service Unavailable`: Serviço com problemas

## 🔄 Fluxo de Monitoramento

```
┌─────────────────┐
│  Main Loop      │
│  (asyncio)      │
└────┬───────┬────┘
     │       │
     │       │ Parallel execution
     ▼       ▼
┌─────────┐ ┌─────────┐
│  Ping   │ │  HTTP   │
│  Loop   │ │  Loop   │
└────┬────┘ └───────┬─┘
     │              │
     │PING_INTERVAL │ HTTP_INTERVAL
     ▼              ▼
┌─────────────────────┐
│ For each target:    │
│ - Execute check     │
│ - Calculate metrics │
│ - Record to OTEL    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────┐
│ OTEL Collector  │
│ (via gRPC)      │
└─────────────────┘
```

## 📦 Dependências

### Production

```txt
# requirements.txt
opentelemetry-api==1.38.0
opentelemetry-sdk==1.38.0
opentelemetry-exporter-otlp-proto-grpc==1.38.0
ping3==4.0.4                      # ICMP ping library
httpx==0.25.2                     # Async HTTP client
asyncio==3.4.3                    # Async runtime
```

### Development

```txt
pytest==7.4.3
pytest-asyncio==0.21.1            # Async test support
pytest-cov==4.1.0                 # Coverage reports
```

## 📈 Monitoramento

### Métricas do Agente

```promql
# Latência média por target
avg(network_ping_latency_ms{job="network-monitor"}) by (target)

# Packet loss por target
network_ping_packet_loss_percentage{job="network-monitor"}

# Disponibilidade HTTP
network_http_availability{job="network-monitor"}

# Taxa de sucesso de checks
rate(network_monitor_checks_total{status="success"}[5m])

# P95 de tempo de resposta HTTP
histogram_quantile(0.95, rate(network_http_response_time_ms_bucket[5m]))

# Uptime do agente
up{service="network-monitor"}
```

### Dashboards Grafana

Visualize métricas no dashboard **Network Monitoring** em:
http://localhost:3000

**Painéis disponíveis:**
- 🏓 Latência ICMP (Ping) por Target
- 📉 Packet Loss Timeline
- 🌐 HTTP Response Times
- ✅ Availability Heatmap
- 📊 Status Code Distribution

## 📚 Referências

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [ping3 Documentation](https://github.com/kyan001/ping3)
- [httpx Documentation](https://www.python-httpx.org/)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

## 🔄 Ciclo de Vida

```
START
  ↓
Initialize Config
  ↓
Setup OpenTelemetry
  ↓
Create Metrics Manager
  ↓
Initialize Monitors
  ↓
Start Health Check Server
  ↓
┌──────────────────────────┐
│  Parallel Monitoring     │
├──────────┬───────────────┤
│ Ping Loop│  HTTP Loop    │
│ (30s)    │  (60s)        │
├──────────┼───────────────┤
│ For each target:         │
│ 1. Execute check         │
│ 2. Record metrics        │
│ 3. Handle errors         │
│ 4. Wait interval         │
└──────────┴───────────────┘
         │
    Ctrl+C / SIGTERM
         │
         ▼
    Graceful Shutdown
```

Para voltar ao README principal: [📖 README.md](../../README.md)

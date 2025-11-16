# ViaIPE Collector Agent

Agente de coleta de métricas da API VIAIPE (RNP - Rede Nacional de Ensino e Pesquisa) com exportação via OpenTelemetry.

## 📋 Visão Geral

O ViaIPE Collector é um agente especializado que:
- 📡 Coleta dados da API VIAIPE (legado RNP)
- 🔄 Processa e transforma métricas de tráfego de rede
- 📊 Exporta métricas via OpenTelemetry (OTLP)
- ✅ Fornece health check endpoint

## 🏗️ Estrutura do Projeto

```
agents/viaipe-collector/
├── Dockerfile              # Container image definition
├── requirements.txt        # Python dependencies
├── pytest.ini             # Pytest configuration
├── README.md              # Este arquivo
├── src/                   # Código fonte
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── config.py          # Configuration management
│   ├── health_check.py    # Health check server
│   └── collector/         # Módulo de coleta
│       ├── __init__.py
│       ├── api_client.py      # Client da API VIAIPE
│       ├── data_processor.py  # Processamento de dados
│       └── collector.py       # Orquestrador principal
└── tests/                 # Testes unitários
    └── ...
```

## 🎯 Responsabilidades

### API Client (`api_client.py`)
- Requisições HTTP para API VIAIPE
- Autenticação e headers
- Tratamento de erros de rede
- Retry logic

### Data Processor (`data_processor.py`)
- Transformação de dados JSON
- Cálculo de métricas agregadas
- Normalização de valores
- Validação de dados

### Collector (`collector.py`)
- Orquestração do ciclo de coleta
- Loop assíncrono de polling
- Integração com OpenTelemetry
- Logging e observabilidade

### Health Check (`health_check.py`)
- Endpoint HTTP `/health`
- Status do agente
- Informações de saúde

## 📊 Métricas Coletadas

### Métricas de Tráfego RNP

```python
# Exemplos de métricas exportadas
viaipe.traffic.ingress (Gauge)
  - Tráfego de entrada em Mbps
  - Labels: region, router, interface

viaipe.traffic.egress (Gauge)
  - Tráfego de saída em Mbps
  - Labels: region, router, interface

viaipe.utilization.percentage (Gauge)
  - Utilização da interface em %
  - Labels: region, router, interface

viaipe.api.response_time (Histogram)
  - Tempo de resposta da API
  - Labels: endpoint, status_code

viaipe.api.errors (Counter)
  - Erros de coleta
  - Labels: error_type
```

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# API VIAIPE
VIAIPE_API_URL=https://legadoviaipe.rnp.br/api/norte
VIAIPE_POLL_INTERVAL=60              # Intervalo de coleta em segundos

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=viaipe-collector

# Health Check
HEALTH_PORT=8081

# Logging
LOG_LEVEL=INFO                       # DEBUG, INFO, WARNING, ERROR
```

### Configuração Avançada

```python
# src/config.py
class Config:
    # API Settings
    VIAIPE_API_URL: str
    VIAIPE_POLL_INTERVAL: int = 60
    VIAIPE_TIMEOUT: int = 30
    VIAIPE_RETRIES: int = 3
    
    # OTEL Settings
    OTEL_EXPORTER_OTLP_ENDPOINT: str
    OTEL_SERVICE_NAME: str = "viaipe-collector"
    
    # Health Check
    HEALTH_PORT: int = 8081
```

## 🚀 Uso

### Com Docker Compose

```bash
# Iniciar o serviço
docker compose up -d viaipe-collector

# Visualizar logs
docker compose logs -f viaipe-collector
```

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/test_api_client.py
pytest tests/test_data_processor.py

# Ver relatório de cobertura
open htmlcov/index.html
```

### Estrutura de Testes

```
tests/
├── __init__.py
├── test_config.py              # Testes de configuração
├── test_health_check.py        # Testes de health check
├── test_api_client.py          # Testes do cliente API
├── test_data_processor.py      # Testes de processamento
└── test_collector.py           # Testes de integração
```

## 🔍 Health Check

### Endpoint

```bash
GET http://localhost:8081/health
```

### Resposta

```json
{
  "status": "healthy",
  "service": "viaipe-collector",
  "timestamp": "2025-11-16T12:00:00Z",
  "uptime_seconds": 3600,
  "last_collection": "2025-11-16T11:59:00Z",
  "collections_total": 60,
  "errors_total": 0
}
```

### Status Codes

- `200 OK`: Serviço saudável
- `503 Service Unavailable`: Serviço com problemas

## 🔄 Fluxo de Coleta

```
┌─────────────────┐
│  Main Loop      │
│  (asyncio)      │
└────────┬────────┘
         │ a cada VIAIPE_POLL_INTERVAL
         ▼
┌─────────────────┐
│  API Client     │
│  GET /api/norte │
└────────┬────────┘
         │ JSON response
         ▼
┌─────────────────┐
│ Data Processor  │
│ Transform data  │
└────────┬────────┘
         │ Structured metrics
         ▼
┌─────────────────┐
│ OTEL Exporter   │
│ Send via gRPC   │
└────────┬────────┘
         │ OTLP
         ▼
┌─────────────────┐
│ OTEL Collector  │
└─────────────────┘
```

## 📦 Dependências

### Production

```txt
# requirements.txt
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-otlp==1.21.0
aiohttp==3.9.1                    # HTTP client async
pydantic==2.5.0                   # Data validation
python-dotenv==1.0.0              # Environment variables
```

### Development

```txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
black==23.12.1
flake8==7.0.0
mypy==1.7.1
```

## 📈 Monitoramento

### Métricas do Agente

```promql
# Taxa de coleta bem-sucedida
rate(viaipe_collections_total{status="success"}[5m])

# Taxa de erros
rate(viaipe_api_errors_total[5m])

# Tempo de resposta da API
histogram_quantile(0.95, rate(viaipe_api_response_time_bucket[5m]))

# Uptime do agente
up{service="viaipe-collector"}
```

### Dashboards Grafana

Visualize métricas no dashboard **VIAIPE Metrics** em:
http://localhost:3000

## 📚 Referências

- [API VIAIPE RNP](https://legadoviaipe.rnp.br/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [aiohttp Documentation](https://docs.aiohttp.org/)

## 🔄 Ciclo de Vida

```
START
  ↓
Initialize Config
  ↓
Setup OpenTelemetry
  ↓
Start Health Check Server
  ↓
┌──────────────────┐
│ Collection Loop  │ ←──┐
│ (every interval) │    │
└────────┬─────────┘    │
         │              │
      Success?          │
         │              │
    Yes  │  No          │
         │              │
         ▼              │
     Log Result         │
         │              │
    Wait interval       │
         │              │
         └──────────────┘
```

---

Para voltar ao README principal: [📖 README.md](../../README.md)

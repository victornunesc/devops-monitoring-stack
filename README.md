# 📊 DevOps Monitoring Platform

> **Plataforma de Monitoramento Cloud-Native com OpenTelemetry, VictoriaMetrics e Grafana**

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-000000?style=flat&logo=opentelemetry&logoColor=white)](https://opentelemetry.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Grafana](https://img.shields.io/badge/Grafana-F46800?style=flat&logo=grafana&logoColor=white)](https://grafana.com/)

![Workflow](./workflow.gif)

## 📋 Índice

### 🎯 Documentação de Alto Nível
- [Visão Geral](#-visão-geral)
- [High Level Design (HLD)](#-high-level-design-hld)
- [Arquitetura](#️-arquitetura)
- [Componentes](#-componentes)
- [Stack Tecnológico](#-stack-tecnológico)
- [Qualidades Arquiteturais](#-qualidades-arquiteturais)
- [Início Rápido](#-início-rápido)
- [Configuração](#️-configuração)
- [Monitoramento](#-monitoramento)
- [Estrutura do Projeto](#-estrutura-do-projeto)

### 📚 Documentação de Baixo Nível
- 📘 [Network Monitor - Detalhes técnicos](./agents/network-monitor/README.md)
- 📘 [ViaIPE Collector - Detalhes técnicos](./agents/viaipe-collector/README.md)
- 📙 [OpenTelemetry Collector - Configuração](./otel/README.md)
- 📙 [Grafana - Dashboards e Alerting](./grafana/README.md)
---

## 🎯 Visão Geral

Esta plataforma implementa uma **arquitetura de monitoramento distribuída** seguindo padrões **CNCF (Cloud Native Computing Foundation)** e práticas de **observabilidade moderna**. O sistema coleta, processa e visualiza métricas de infraestrutura de rede e APIs externas em tempo real.

### Casos de Uso

- 🌐 **Monitoramento de Latência de Rede**: Rastreamento contínuo de RTT e perda de pacotes
- 🔍 **Disponibilidade HTTP/HTTPS**: Verificação de uptime e performance de endpoints
- 📡 **Coleta de Métricas de APIs**: Integração com APIs externas (VIAIPE/RNP)
- 📊 **Visualização em Tempo Real**: Dashboards interativos com histórico de 90 dias
- 🚨 **Alertas Proativos**: Sistema de alerting configurável via Grafana

---

## 🏗️ High Level Design (HLD)

### Visão Arquitetural

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MONITORING PLATFORM                             │
│                     Cloud-Native Observability Stack                    │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐          ┌──────────────────────┐
│   DATA COLLECTION    │          │   EXTERNAL SOURCES   │
│      (Agents)        │          │                      │
├──────────────────────┤          ├──────────────────────┤
│                      │          │                      │
│  Network Monitor     │───ping───│  • Google            │
│  • Ping Monitor      │          │  • YouTube           │
│  • HTTP Monitor      │          │  • RNP               │
│  • OpenTelemetry SDK │          │                      │
│                      │          └──────────────────────┘
│  ViaIPE Collector    │          ┌──────────────────────┐
│  • API Client        │───http───│  VIAIPE API - RNP    │
│  • Data Processor    │          └──────────────────────┘
│  • Metrics Exporter  │          
│                      │
└──────────┬───────────┘
           │ OTLP/gRPC (4317)
           │ OTLP/HTTP (4318)
           ▼
┌──────────────────────┐
│  TELEMETRY PIPELINE  │
│   (OTEL Collector)   │
├──────────────────────┤
│                      │
│  ┌────────────────┐  │
│  │   Receivers    │  │ ◄─── Receive OTLP metrics from agents
│  └────────┬───────┘  │
│           │          │
│  ┌────────▼───────┐  │
│  │   Processors   │  │ ◄─── Transform, batch, enrich
│  └────────┬───────┘  │
│           │          │
│  ┌────────▼───────┐  │
│  │   Exporters    │  │ ◄─── Send to storage backend
│  └────────────────┘  │
│                      │
└──────────┬───────────┘
           │ Prometheus RemoteWrite
           ▼
┌──────────────────────┐
│   STORAGE LAYER      │
│  (VictoriaMetrics)   │
├──────────────────────┤
│                      │
│  • TSDB Optimized    │
│  • 90d Retention     │
│  • High Compression  │
│  • Fast Queries      │
│  • PromQL Support    │
│                      │
└──────────┬───────────┘
           │ PromQL/HTTP API
           ▼
┌──────────────────────┐
│  VISUALIZATION       │
│     (Grafana)        │
├──────────────────────┤
│                      │
│  • Network Dashboard │
│  • VIAIPE Dashboard  │
│  • Alerting Rules    │
│  • Data Sources      │
│                      │
└──────────────────────┘
           │
           ▼
   ┌──────────────┐
   │    USERS     │
   └──────────────┘
```

### Fluxo de Dados

```
1. COLLECTION
   ├─ Network Monitor → [Ping + HTTP Checks] → Metrics
   └─ ViaIPE Collector → [API Poll] → Metrics

2. INSTRUMENTATION
   └─ OpenTelemetry SDK → Standardized Metrics (OTLP format)

3. TELEMETRY
   └─ OTEL Collector → [Receive → Process → Export]

4. STORAGE
   └─ VictoriaMetrics → Time-Series Database (90d retention)

5. VISUALIZATION
   └─ Grafana → Dashboards + Alerts + Queries
```

### Padrões de Design Aplicados

| Padrão | Implementação | Benefício |
|--------|---------------|-----------|
| **Sidecar Pattern** | OTEL Collector como proxy de telemetria | Desacoplamento e flexibilidade |
| **Pipeline Pattern** | Receivers → Processors → Exporters | Processamento modular |
| **Repository Pattern** | Agentes isolados com responsabilidades únicas | Manutenibilidade |
| **Health Check Pattern** | Endpoints `/health` em todos os serviços | Orquestração confiável |
| **12-Factor App** | Configuração via env vars | Portabilidade |
| **Observability Pattern** | Métricas estruturadas com OpenTelemetry | Padronização CNCF |

---

## 🏛️ Arquitetura

### Camadas da Aplicação

```
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                     │
│                 (Grafana Dashboards)                    │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    STORAGE LAYER                        │
│               (VictoriaMetrics TSDB)                    │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                  TELEMETRY LAYER                        │
│             (OpenTelemetry Collector)                   │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                  APPLICATION LAYER                      │
│                 (Monitoring Agents)                     │
│    ┌──────────────────┐    ┌───────────────────┐        │
│    │ Network Monitor  │    │ ViaIPE Collector  │        │
│    └──────────────────┘    └───────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### Comunicação entre Componentes

```
Network Monitor  ──┐
                   ├─► OTLP/gRPC:4317 ──► OTEL Collector
ViaIPE Collector ──┘                           │
                                               │
                                               ▼
                                     Prometheus RemoteWrite
                                               │
                                               ▼
                                      VictoriaMetrics:8428
                                               │
                                               ▼
                                          PromQL API
                                               │
                                               ▼
                                         Grafana:3000
```

---

## 🧩 Componentes

### Application Layer (Monitoring Agents)

| Componente | Descrição | Documentação |
|------------|-----------|--------------|
| **Network Monitor** 🌐 | Monitora latência de rede e disponibilidade HTTP/HTTPS | [📖 README](./agents/network-monitor/README.md) |
| **ViaIPE Collector** 📡 | Coleta métricas da API VIAIPE (RNP) | [📖 README](./agents/viaipe-collector/README.md) |

### Telemetry Layer

| Componente | Descrição | Documentação |
|------------|-----------|--------------|
| **OpenTelemetry Collector** 🔄 | Pipeline de processamento de métricas (Receivers → Processors → Exporters) | [📖 README](./otel/README.md) |

### Storage Layer

| Componente | Descrição | Documentação |
|------------|-----------|--------------|
| **VictoriaMetrics** 💾 | Time-Series Database com 90 dias de retenção | - |

### Presentation Layer

| Componente | Descrição | Documentação |
|------------|-----------|--------------|
| **Grafana** 📈 | Visualização de métricas e sistema de alertas | [� README](./grafana/README.md) |

---

## 🛠️ Stack Tecnológico

| Camada | Tecnologia | Versão | Propósito |
|--------|-----------|--------|-----------|
| **Agents** | Python | 3.11+ | Desenvolvimento dos agentes |
| **Telemetry** | OpenTelemetry Collector | 0.91.0 | Pipeline de métricas |
| **Storage** | VictoriaMetrics | 1.96.0 | Time-series database |
| **Visualization** | Grafana | 10.2.3 | Dashboards e alerting |
| **Orchestration** | Docker Compose | 3.8+ | Orquestração de containers |


---

## ✨ Qualidades Arquiteturais

### 1. **Observabilidade** 🔍

- **Instrumentação Padronizada**: OpenTelemetry como padrão CNCF
- **Métricas Estruturadas**: Labels consistentes e semântica clara
- **Rastreabilidade**: Logs correlacionados com métricas
- **Visibilidade**: Dashboards em tempo real

### 2. **Escalabilidade** 📈

- **Horizontal Scaling**: Agentes stateless podem ser replicados
- **Pipeline Distribuído**: OTEL Collector suporta clustering
- **TSDB Otimizado**: VictoriaMetrics para alta cardinalidade
- **Async Processing**: Operações não-bloqueantes

### 3. **Resiliência** 🛡️

- **Health Checks**: Todos os serviços monitorados
- **Restart Policies**: Auto-recuperação de falhas
- **Circuit Breaking**: Timeouts e retries configurados
- **Graceful Degradation**: Falhas isoladas não propagam

### 4. **Manutenibilidade** 🔧

- **Separação de Responsabilidades**: Cada componente com função única
- **Código Testável**: Cobertura de testes unitários (pytest)
- **Documentação**: README por componente
- **Configuração Declarativa**: Infrastructure as Code

### 5. **Portabilidade** 🚀

- **Containerização**: Docker para todos os serviços
- **12-Factor App**: Configuração via variáveis de ambiente
- **Vendor Agnostic**: OpenTelemetry suporta múltiplos backends
- **Cloud Ready**: Deploy em qualquer plataforma Docker

### 6. **Segurança** 🔐

- **Network Isolation**: Rede dedicada para containers
- **Least Privilege**: Capabilities mínimas (NET_RAW apenas onde necessário)
- **Health Checks**: Detecção precoce de anomalias
- **Immutable Infrastructure**: Containers imutáveis

### 7. **Performance** ⚡

- **Async I/O**: Operações não-bloqueantes (asyncio)
- **Batch Processing**: Agregação de métricas
- **Memory Management**: Limitadores configurados
- **Efficient Storage**: Alta compressão em VictoriaMetrics

---

## 🚀 Início Rápido

### Pré-requisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4 GB RAM disponível
- Portas livres: 3000, 4317, 4318, 8080, 8081, 8428, 8888

### Instalação

```bash
# Clone o repositório
git clone <repository-url>
cd devops-monitoring-stack

# Inicie todos os serviços
./start.sh

# Ou use Docker Compose diretamente
docker compose up -d

# Check status dos containers
docker compose ps

# Visualize logs
docker compose logs -f
```

### Acesso aos Serviços

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin/admin |
| VictoriaMetrics | http://localhost:8428 | - |
| OTEL Collector Metrics | http://localhost:8888/metrics | - |
| Network Monitor Health | http://localhost:8080/health | - |
| ViaIPE Collector Health | http://localhost:8081/health | - |

---

## ⚙️ Configuração

### Variáveis de Ambiente

As configurações de cada componente são gerenciadas via variáveis de ambiente.

Para detalhes completos de configuração de cada componente, consulte:
- 📖 [Network Monitor Configuration](./agents/network-monitor/README.md#variáveis-de-ambiente)
- 📖 [ViaIPE Collector Configuration](./agents/viaipe-collector/README.md)
- 📖 [OTEL Collector Configuration](./otel/README.md)
- 📖 [Grafana Configuration](./grafana/README.md)

### Personalização

Edite os arquivos em `containers/` para customizar configurações específicas de cada serviço.

---

## 📊 Monitoramento

### Dashboards Grafana

A plataforma disponibiliza dashboards pré-configurados para visualização das métricas:

- 🌐 **Network Monitoring Dashboard**: Latência, perda de pacotes e disponibilidade HTTP
- 📡 **VIAIPE Metrics Dashboard**: Métricas de tráfego RNP e performance da API

### Acesso

| Interface | URL | Descrição |
|-----------|-----|-----------|
| Grafana | http://localhost:3000 | Dashboards e alerting (admin/admin) |
| VictoriaMetrics | http://localhost:8428 | TSDB UI e queries |
| OTEL Collector | http://localhost:8888/metrics | Métricas internas do collector |

> 📖 **Para detalhes sobre métricas disponíveis e queries PromQL, consulte:**
> - [Network Monitor Metrics](./agents/network-monitor/README.md#métricas)
> - [Grafana Dashboards Guide](./grafana/README.md)

---

## 📁 Estrutura do Projeto

```
devops-monitoring-stack/
├── README.md                      # 📖 Este arquivo (High Level)
├── docker-compose.yml             # Orquestração principal
├── start.sh                       # Script de inicialização
│
├── agents/                        # Agentes de monitoramento
│   ├── network-monitor/           # 📖 Monitor de rede
│   │   ├── README.md              # Documentação detalhada
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── pytest.ini
│   │   ├── src/                   # Código fonte
│   │   └── tests/                 # Testes unitários
│   │
│   └── viaipe-collector/          # 📖 Coletor VIAIPE
│       ├── README.md              # Documentação detalhada
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── pytest.ini
│       ├── src/
│       └── tests/
│
├── containers/                    # 📖 Configurações Docker Compose
│   ├── README.md                  # Documentação de containers
│   ├── network-monitor.yml
│   ├── viaipe-collector.yml
│   ├── otel-collector.yml
│   ├── victoriametrics.yml
│   └── grafana.yml
│
├── otel/                          # 📖 Configuração OTEL
│   ├── README.md                  # Documentação do OTEL Collector
│   └── otel-collector-config.yaml
│
└── grafana/                       # 📖 Configuração Grafana
    ├── README.md                  # Documentação do Grafana
    ├── dashboards/
    │   ├── Network/               # Dashboards de rede
    │   └── viaipe/                # Dashboards VIAIPE
    └── provisioning/
        ├── datasources/           # Data sources
        ├── dashboards/            # Provisioning
        └── alerting/              # Alerting rules
```

---

<p align="center">
  <i>Construído com ❤️ usando tecnologias cloud-native</i>
</p>

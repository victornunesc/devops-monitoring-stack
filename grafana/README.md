# Grafana - Visualization & Alerting

Plataforma de visualização de métricas e sistema de alertas para a stack de monitoramento.

## 📋 Visão Geral

Grafana é a camada de apresentação da plataforma, oferecendo:
- 📊 Dashboards interativos em tempo real
- 🚨 Sistema de alertas unificado
- 📈 Queries PromQL para análise de dados
- 🎨 Visualizações customizáveis

## 🚀 Acesso

| Item | Valor |
|------|-------|
| **URL** | http://localhost:3000 |
| **Usuário padrão** | admin |
| **Senha padrão** | admin |
| **Porta** | 3000 |

## 📁 Estrutura de Arquivos

```
grafana/
├── README.md                      # Este arquivo
├── dashboards/                    # Dashboards JSON
│   ├── Network/                   # Dashboards de monitoramento de rede
│   │   └── network-monitor.json
│   └── viaipe/                    # Dashboards VIAIPE/RNP
│       └── viaipe-metrics.json
└── provisioning/                  # Configuração automática
    ├── datasources/               # Data sources pré-configurados
    │   └── victoriametrics.yaml
    ├── dashboards/                # Provisioning de dashboards
    │   └── default.yaml
    └── alerting/                  # Regras de alerta
        └── alerts.yaml
```

## 🔧 Configuração

### Variáveis de Ambiente

```yaml
# Credenciais de administrador
GF_SECURITY_ADMIN_USER: admin
GF_SECURITY_ADMIN_PASSWORD: admin

# Configurações de autenticação
GF_USERS_ALLOW_SIGN_UP: false
GF_AUTH_ANONYMOUS_ENABLED: false

# Alerting
GF_ALERTING_ENABLED: false              # Legacy alerting (desabilitado)
GF_UNIFIED_ALERTING_ENABLED: true       # Unified alerting (habilitado)
WEBHOOK_URL: http://localhost:8080/alerts
```

### Data Sources

#### VictoriaMetrics (Pré-configurado)

```yaml
# provisioning/datasources/victoriametrics.yaml
apiVersion: 1

datasources:
  - name: VictoriaMetrics
    type: prometheus
    access: proxy
    url: http://victoriametrics:8428
    isDefault: true
    editable: false
```

**Características:**
- Tipo: Prometheus-compatible
- URL: `http://victoriametrics:8428`
- Suporte completo a PromQL
- Configurado como datasource padrão

## 📊 Dashboards

### 1. Network Monitoring Dashboard 🌐

Dashboard para monitoramento de rede e HTTP.

**Painéis disponíveis:**

#### Latência de Rede (RTT)
```promql
# RTT médio por target
rate(network_ping_rtt_sum[5m]) / rate(network_ping_rtt_count[5m])

# RTT por quantile (p50, p95, p99)
histogram_quantile(0.95, rate(network_ping_rtt_bucket[5m]))
```

#### Perda de Pacotes
```promql
# Percentual de perda de pacotes
network_ping_packet_loss{target="google.com"}

# Tendência de perda
rate(network_ping_packet_loss[5m])
```

#### Disponibilidade HTTP
```promql
# Taxa de sucesso HTTP (status 2xx)
sum(rate(http_client_status_total{status=~"2.."}[5m])) 
/ 
sum(rate(http_client_status_total[5m])) * 100

# Total de requisições por status
sum by (status) (rate(http_client_status_total[5m]))
```

#### Duração de Requisições HTTP
```promql
# Duração média
rate(http_client_duration_sum[5m]) / rate(http_client_duration_count[5m])

# Percentil 95
histogram_quantile(0.95, rate(http_client_duration_bucket[5m]))
```

**Variáveis do Dashboard:**
- `$target`: Seletor de targets monitorados
- `$interval`: Intervalo de agregação
- `$percentile`: Percentil para latência

---

### 2. VIAIPE Metrics Dashboard 📡

Dashboard para métricas da API VIAIPE (RNP).

**Painéis disponíveis:**
- Tráfego de rede RNP
- Performance da API VIAIPE
- Taxa de coleta de dados
- Erros e disponibilidade

---

## 🚨 Sistema de Alertas

### Configuração de Alertas

O Grafana Unified Alerting está configurado com alertas automáticos baseados em queries PromQL.

#### Alertas de Monitoramento de Rede 🌐

**Grupo: Ping Monitoring Alerts**
- **High Ping Latency** ⚠️ - Latência alta (>100ms p95)
- **Critical Ping Latency** 🚨 - Latência crítica (>200ms p95)
- **Progressive Latency Degradation** ⚠️ - Degradação progressiva de latência (>50% comparado à média de 1h)
- **High Packet Loss** ⚠️ - Alta perda de pacotes
- **Critical Packet Loss** 🚨 - Perda crítica de pacotes

**Grupo: HTTP Monitoring Alerts**
- **High HTTP Response Time** ⚠️ - Alto tempo de resposta HTTP
- **Critical HTTP Response Time** 🚨 - Tempo crítico de resposta HTTP
- **High HTTP 5xx Error Rate** 🚨 - Alta taxa de erros 5xx
- **High HTTP 4xx Error Rate** ⚠️ - Alta taxa de erros 4xx
- **Low Uptime** 🚨 - Baixa disponibilidade
- **Target Unreachable** 🚨 - Target inacessível
- **Multiple Targets with Issues** 🚨 - Múltiplos targets com problemas
- **Ping Target Unreachable** 🚨 - Target ping inacessível

#### Alertas VIAIPE/RNP 📡

**Grupo: VIAIPE Analytics Alerts**
- **Low Client Availability** ⚠️ - Baixa disponibilidade de clientes
- **Critical Client Availability** 🚨 - Disponibilidade crítica de clientes
- **Low Regional Availability** ⚠️ - Baixa disponibilidade regional
- **Low Connection Quality Score** ⚠️ - Baixa qualidade de conexão
- **Critical Connection Quality Score** 🚨 - Qualidade crítica de conexão
- **Low Regional Quality Score** ⚠️ - Baixa qualidade regional
- **High Bandwidth Usage (Inbound)** ⚠️ - Alto uso de banda (entrada)
- **High Bandwidth Usage (Outbound)** ⚠️ - Alto uso de banda (saída)
- **Abnormal Bandwidth Peak** 🚨 - Pico anormal de banda
- **API Errors Detected** ⚠️ - Erros da API detectados
- **High API Error Rate** 🚨 - Alta taxa de erros da API
- **No Clients Being Monitored** 🚨 - Nenhum cliente sendo monitorado

### Notification Channels

Configure canais de notificação em:
- **Alerting** → **Contact points**

Canais suportados:
- Email
- Slack
- Microsoft Teams
- PagerDuty
- Webhook
- Telegram
- Discord

## 📈 Queries PromQL Úteis

### Latência

```promql
# Latência média nos últimos 5 minutos
avg(rate(network_ping_rtt_sum[5m]) / rate(network_ping_rtt_count[5m]))

# Latência máxima por target
max by (target) (network_ping_rtt)

# Tendência de latência (1 hora)
rate(network_ping_rtt_sum[1h]) / rate(network_ping_rtt_count[1h])
```

### HTTP Monitoring

```promql
# Distribuição de status codes
sum by (status) (rate(http_client_status_total[5m]))

# Taxa de erros (4xx + 5xx)
sum(rate(http_client_status_total{status=~"[45].."}[5m]))

# Uptime percentual (últimas 24h)
sum(rate(http_client_status_total{status=~"2.."}[24h])) 
/ 
sum(rate(http_client_status_total[24h])) * 100
```

### Performance

```promql
# Requisições por segundo
sum(rate(http_client_status_total[1m]))

# Duração p99
histogram_quantile(0.99, rate(http_client_duration_bucket[5m]))

# Comparação de performance entre targets
rate(http_client_duration_sum[5m]) / rate(http_client_duration_count[5m])
```

### Problemas Comuns

#### Dashboard não carrega métricas
- Verifique se VictoriaMetrics está rodando
- Confirme a conectividade: `docker compose exec grafana ping victoriametrics`
- Verifique queries PromQL no painel

#### Alertas não disparam
- Verifique regras em Alerting → Alert rules
- Confirme contact points configurados
- Cheque logs: `docker compose logs grafana | grep alert`

## 📚 Referências

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/)
- [VictoriaMetrics + Grafana](https://docs.victoriametrics.com/Single-server-VictoriaMetrics.html#grafana-setup)

---

Para voltar ao README principal: [📖 README.md](../README.md)

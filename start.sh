#!/bin/bash
echo "🚀 Iniciando projeto de monitoramento..."
echo ""

echo "📦 Verificando Docker Compose..."
if command -v docker compose &> /dev/null; then
    echo "✓ Docker Compose V2 encontrado"
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    echo "✓ Docker Compose V1 encontrado (pode não suportar 'include')"
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "✗ Docker Compose não encontrado!"
    exit 1
fi

echo ""
echo "🔨 Fazendo build das imagens..."
$DOCKER_COMPOSE_CMD build

echo ""
echo "🚀 Iniciando containers..."
$DOCKER_COMPOSE_CMD up -d

echo ""
echo "📊 Status dos containers:"
$DOCKER_COMPOSE_CMD ps

echo ""
echo "✅ Pronto! Acesse:"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo "   - VictoriaMetrics: http://localhost:8428"
echo "   - Network Monitor Health: http://localhost:8080/health"
echo "   - Viaipe Collector Health: http://localhost:8081/health"
echo ""
echo "📝 Para ver logs: $DOCKER_COMPOSE_CMD logs -f"
echo "🛑 Para parar: $DOCKER_COMPOSE_CMD down"

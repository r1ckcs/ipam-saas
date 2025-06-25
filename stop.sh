#!/bin/bash

# IPAM - Script de Parada
# Este script para todos os serviços do IPAM

set -e

echo "🛑 Parando IPAM - IP Address Management"
echo "======================================="

# Verificar se há containers rodando
RUNNING_CONTAINERS=$(docker ps -q --filter "name=ipam-" 2>/dev/null | wc -l)

if [ "$RUNNING_CONTAINERS" -eq 0 ]; then
    echo "ℹ️  Nenhum container IPAM está rodando"
    exit 0
fi

# Parar todos os serviços
echo "⏹️  Parando serviços..."
docker stop ipam-frontend-1 ipam-backend-1 ipam-db-1 2>/dev/null || true
docker rm ipam-frontend-1 ipam-backend-1 ipam-db-1 2>/dev/null || true

# Opção para limpar volumes
if [[ "$1" == "--clean" ]]; then
    echo "🧹 Removendo volumes e dados..."
    docker volume rm ipam_postgres_data 2>/dev/null || true
    docker network rm ipam_default 2>/dev/null || true
    docker system prune -f
    echo "✅ Dados removidos"
fi

echo ""
echo "✅ IPAM parado com sucesso!"
echo ""
echo "📋 Para reiniciar:"
echo "   ./start.sh                 # Iniciar normalmente"
echo "   ./start.sh --clean         # Iniciar limpando dados"
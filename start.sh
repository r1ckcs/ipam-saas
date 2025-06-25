#!/bin/bash

# IPAM - Script de Inicialização
# Este script automatiza o processo de inicialização do SaaS IPAM

set -e

echo "🚀 Iniciando IPAM - IP Address Management"
echo "========================================"

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale o Docker primeiro."
    exit 1
fi

# Verificar se Docker está rodando
if ! docker info &> /dev/null; then
    echo "❌ Docker não está rodando. Inicie o Docker primeiro."
    exit 1
fi

echo "✅ Docker verificado com sucesso"

# Parar e remover containers existentes se estiverem rodando
echo "🔄 Parando containers existentes..."
docker stop ipam-frontend-1 ipam-backend-1 ipam-db-1 2>/dev/null || true
docker rm ipam-frontend-1 ipam-backend-1 ipam-db-1 2>/dev/null || true

# Limpar volumes antigos se solicitado
if [[ "$1" == "--clean" ]]; then
    echo "🧹 Limpando volumes antigos..."
    docker volume rm ipam_postgres_data 2>/dev/null || true
    docker system prune -f
fi

# Criar rede se não existir
echo "🌐 Criando rede..."
docker network create ipam_default 2>/dev/null || true

# Criar volume se não existir
echo "💾 Criando volume de dados..."
docker volume create ipam_postgres_data 2>/dev/null || true

# Construir imagens
echo "🏗️  Construindo imagens..."
docker build -t ipam-backend ./backend
docker build -t ipam-frontend ./frontend

# Iniciar banco de dados
echo "📊 Iniciando banco de dados..."
docker run -d \
    --name ipam-db-1 \
    --network ipam_default \
    -e POSTGRES_DB=ipam \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -v ipam_postgres_data:/var/lib/postgresql/data \
    -p 5432:5432 \
    postgres:15-alpine

# Aguardar banco ficar pronto
echo "⏳ Aguardando banco de dados..."
for i in {1..30}; do
    if docker exec ipam-db-1 pg_isready -U postgres &>/dev/null; then
        echo "✅ Banco de dados pronto"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Timeout aguardando banco de dados"
        docker logs ipam-db-1
        exit 1
    fi
    sleep 2
done

# Iniciar backend
echo "🐍 Iniciando backend..."
docker run -d \
    --name ipam-backend-1 \
    --network ipam_default \
    -p 8000:8000 \
    -e DATABASE_URL=postgresql://postgres:postgres@ipam-db-1:5432/ipam \
    ipam-backend

# Verificar se o backend está pronto
echo "⏳ Aguardando backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ &>/dev/null; then
        echo "✅ Backend pronto"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Timeout aguardando backend"
        docker logs ipam-backend-1
        exit 1
    fi
    sleep 2
done

# Iniciar frontend
echo "🌐 Iniciando frontend..."
docker run -d \
    --name ipam-frontend-1 \
    --network ipam_default \
    -p 3000:80 \
    ipam-frontend

# Verificar se o frontend está pronto
echo "⏳ Aguardando frontend..."
for i in {1..30}; do
    if curl -s http://localhost:3000/ &>/dev/null; then
        echo "✅ Frontend pronto"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Timeout aguardando frontend"
        docker logs ipam-frontend-1
        exit 1
    fi
    sleep 2
done

# Criar usuário admin padrão
echo "👤 Criando usuário administrador..."
sleep 3  # Aguardar backend estar completamente pronto
curl -X POST "http://localhost:8000/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@internetflex.com", "password": "N3tfl3x@", "role": "ADMIN"}' \
    &>/dev/null && echo "✅ Usuário admin criado" || echo "⚠️  Usuário admin pode já existir"

echo ""
echo "🎉 IPAM iniciado com sucesso!"
echo "========================================"
echo "📱 Frontend:     http://localhost:3000"
echo "🔌 API Backend:  http://localhost:8000"
echo "📚 Documentação: http://localhost:8000/docs"
echo "🗄️  Database:    localhost:5432"
echo ""
echo "👤 Credenciais do Admin:"
echo "   Email: admin@internetflex.com"
echo "   Senha: N3tfl3x@"
echo ""
echo "📋 Comandos úteis:"
echo "   docker logs -f ipam-backend-1   # Ver logs do backend"
echo "   docker logs -f ipam-frontend-1  # Ver logs do frontend"
echo "   docker logs -f ipam-db-1        # Ver logs do banco"
echo "   ./stop.sh                       # Parar todos os serviços"
echo "   ./start.sh --clean              # Reiniciar limpando dados"
echo ""
echo "✨ Pronto para usar!"
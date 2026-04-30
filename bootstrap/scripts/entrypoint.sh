#!/bin/bash
# entrypoint.sh — Aguarda todos os serviços ficarem saudáveis e executa bootstrap
set -e

echo ""
echo "┌─────────────────────────────────────────────────┐"
echo "│  Homeserver Bootstrap Container                 │"
echo "│  Configurando serviços automaticamente          │"
echo "└─────────────────────────────────────────────────┘"
echo ""

# ── Aguarda serviços ficarem prontos ─────────────────────────────────────────

wait_for_service() {
    local name=$1
    local url=$2
    local max_retries=${3:-60}
    local retry_count=0

    echo "⏳ Aguardando $name..."

    while [ $retry_count -lt $max_retries ]; do
        if curl -sf --max-time 5 "$url" > /dev/null 2>&1; then
            echo "✅ $name está pronto!"
            return 0
        fi

        retry_count=$((retry_count + 1))
        sleep 2
    done

    echo "⚠️  Timeout aguardando $name"
    return 1
}

# ── Health checks ─────────────────────────────────────────────────────────────

echo ""
echo "🔍 Verificando saúde dos serviços..."

# Authentik (health check via HTTP)
wait_for_service "Authentik" "http://authentik-server:9000/-/health/live/" || true

# Opcional: aguardar outros serviços conforme necessário
# wait_for_service "AdGuard" "http://adguard:3000" || true

echo ""
echo "✅ Todos os serviços verificados!"

# ── Executa scripts de bootstrap ─────────────────────────────────────────────

echo ""
echo "🚀 Executando scripts de bootstrap..."

# Carrega variáveis de ambiente do .env se disponível
if [ -f "/app/.env" ]; then
    export $(grep -v '^#' /app/.env | xargs)
fi

# Executa bootstrap do Authentik
echo ""
echo "🔧 Configurando Authentik..."
cd /app
python3 scripts/authentik_bootstrap.py || {
    echo "⚠️  Bootstrap do Authentik falhou (pode ser executado novamente manualmente)"
}

echo ""
echo "┌─────────────────────────────────────────────────┐"
echo "│  ✅ Bootstrap concluído!                        │"
echo "│                                                 │"
echo "│  Serviços configurados:                         │"
echo "│  - Traefik Dashboard                            │"
echo "│  - AdGuard DNS                                  │"
echo "│                                                 │"
echo "│  Acesse:                                        │"
echo "│  - https://auth.maroto.online                   │"
echo "│  - https://traefik.maroto.online                │"
echo "│  - https://dns.maroto.online                    │"
echo "└─────────────────────────────────────────────────┘"
echo ""

# Container finaliza após bootstrap (não fica rodando)
exit 0

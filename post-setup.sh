#!/bin/bash
# post-setup.sh — Sobe os containers e executa bootstrap automático
# Uso: ./post-setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "┌─────────────────────────────────────────────────┐"
echo "│  Homeserver Post-Setup                          │"
echo "│  Subindo containers e configurando serviços     │"
echo "└─────────────────────────────────────────────────┘"
echo ""

# ── Verificações ─────────────────────────────────────────────────────────────

if [ ! -f "output/docker-compose.yml" ]; then
    echo "❌ docker-compose.yml não encontrado!"
    echo "   Execute ./setup.py primeiro."
    exit 1
fi

if [ ! -f "output/.env" ]; then
    echo "❌ .env não encontrado!"
    echo "   Execute ./setup.py primeiro."
    exit 1
fi

# ── Sobe containers ─────────────────────────────────────────────────────────

echo "📦 Subindo containers..."
docker compose -f output/docker-compose.yml up -d --build

echo ""
echo "⏳ Aguardando bootstrap container configurar os serviços..."
echo "   (isso pode levar 2-3 minutos)"
echo ""

# ── Acompanha logs do bootstrap ──────────────────────────────────────────────

docker compose -f output/docker-compose.yml logs -f bootstrap &
LOGS_PID=$!

# Aguarda bootstrap container terminar
while true; do
    STATUS=$(docker inspect -f '{{.State.Status}}' homeserver-bootstrap 2>/dev/null || echo "not_found")
    
    if [ "$STATUS" = "exited" ]; then
        # Verifica exit code
        EXIT_CODE=$(docker inspect -f '{{.State.ExitCode}}' homeserver-bootstrap 2>/dev/null || echo "1")
        
        kill $LOGS_PID 2>/dev/null || true
        
        echo ""
        if [ "$EXIT_CODE" = "0" ]; then
            echo "┌─────────────────────────────────────────────────┐"
            echo "│  ✅ Setup concluído com sucesso!                │"
            echo "│                                                 │"
            echo "│  Acesse:                                        │"
            echo "│  - Authentik: https://auth.maroto.online        │"
            echo "│  - Traefik: https://traefik.maroto.online       │"
            echo "│  - AdGuard: https://dns.maroto.online           │"
            echo "│  - Teste: https://test.maroto.online            │"
            echo "└─────────────────────────────────────────────────┘"
        else
            echo "┌─────────────────────────────────────────────────┐"
            echo "│  ⚠️  Bootstrap finalizado com código: $EXIT_CODE │"
            echo "│                                                 │"
            echo "│  Verifique logs:                                │"
            echo "│  docker compose logs bootstrap                  │"
            echo "│                                                 │"
            echo "│  Configure manualmente:                         │"
            echo "│  https://auth.maroto.online/if/admin/           │"
            echo "└─────────────────────────────────────────────────┘"
        fi
        
        # Remove container bootstrap (não é necessário manter)
        docker rm homeserver-bootstrap > /dev/null 2>&1 || true
        
        exit $EXIT_CODE
    elif [ "$STATUS" = "not_found" ]; then
        kill $LOGS_PID 2>/dev/null || true
        echo "❌ Container bootstrap não encontrado!"
        exit 1
    fi
    
    sleep 2
done

#!/bin/bash
# post-setup.sh — Sobe os containers do homeserver
# Uso: ./post-setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "┌─────────────────────────────────────────────────┐"
echo "│  Homeserver Post-Setup                          │"
echo "│  Subindo containers...                          │"
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
echo "┌─────────────────────────────────────────────────┐"
echo "│  ✅ Containers iniciados!                       │"
echo "│                                                 │"
echo "│  Os serviços estão se configurando              │"
echo "│  automaticamente (post-setup dentro de cada     │"
echo "│  container). Isso pode levar 2-3 minutos.       │"
echo "│                                                 │"
echo "│  Verifique logs:                                │"
echo "│  docker compose -f output/docker-compose.yml logs -f"
echo "└─────────────────────────────────────────────────┘"

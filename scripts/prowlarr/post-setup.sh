#!/bin/sh
set -e

CONFIG_XML="/config/config.xml"
TRACKERS_FILE="/app/trackers.txt"
BASE_URL="http://localhost:9696/api/v1"
MAX_RETRIES=60

log() {
  echo "[prowlarr-post-setup] $1"
}

# ── Aguarda Prowlarr ──────────────────────────────────────────────────────────

log "Aguardando Prowlarr..."
for i in $(seq 1 $MAX_RETRIES); do
  if curl -sf --max-time 5 "http://localhost:9696/health" > /dev/null 2>&1; then
    log "✅ Prowlarr pronto!"
    break
  fi
  if [ "$i" -eq "$MAX_RETRIES" ]; then
    log "⚠️  Timeout aguardando Prowlarr"
    exit 0
  fi
  sleep 2
done

# ── Descobre API key ──────────────────────────────────────────────────────────

if [ ! -f "$CONFIG_XML" ]; then
  log "⚠️  config.xml não encontrado"
  exit 0
fi

API_KEY=$(python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('$CONFIG_XML')
    print(tree.getroot().findtext('ApiKey', ''))
except Exception:
    pass
")

if [ -z "$API_KEY" ]; then
  log "⚠️  API key não encontrada"
  exit 0
fi

# ── Verifica idempotência (já tem indexadores?) ─────────────────────────────

INDEXERS=$(curl -sf --max-time 10 -H "X-Api-Key: $API_KEY" "$BASE_URL/indexer" 2>/dev/null || echo "[]")
INDEXER_COUNT=$(echo "$INDEXERS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$INDEXER_COUNT" -gt 5 ]; then
  log "ℹ️  Prowlarr já possui indexadores configurados — pulando"
  exit 0
fi

# ── Injeta trackers ───────────────────────────────────────────────────────────

if [ ! -f "$TRACKERS_FILE" ]; then
  log "⚠️  trackers.txt não encontrado"
  exit 0
fi

log "Configurando indexadores..."

added=0
total=0
while IFS= read -r tracker; do
  [ -z "$tracker" ] && continue
  total=$((total + 1))

  url="$tracker"
  case "$url" in
    http*) ;;
    *) url="http://$url" ;;
  esac

  payload=$(printf '{"name":"Tracker-%d","implementation":"Torznab","configContract":"TorznabSettings","enable":true,"priority":25,"fields":[{"name":"baseUrl","value":"%s"},{"name":"apiKey","value":""},{"name":"categories","value":[2000,5000,5030,5040]}],"protocol":"torrent"}' "$total" "$url")

  if curl -sf --max-time 10 -H "X-Api-Key: $API_KEY" -H "Content-Type: application/json" -X POST -d "$payload" "$BASE_URL/indexer" > /dev/null 2>&1; then
    added=$((added + 1))
    log "  ✅ Tracker $total adicionado"
  else
    log "  ⚠️  Falha ao adicionar tracker $total"
  fi
done < "$TRACKERS_FILE"

log "✅ $added/$total trackers adicionados ao Prowlarr"

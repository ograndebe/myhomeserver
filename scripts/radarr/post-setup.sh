#!/bin/sh
set -e

SELF="radarr"
PORT=7878
CONFIG_XML="/config/config.xml"
PROWLARR_CONFIG="/prowlarr-config/config.xml"
MAX_RETRIES=60

log() {
  echo "[$SELF-post-setup] $1"
}

# ── Aguarda serviço próprio ──────────────────────────────────────────────────

log "Aguardando $SELF..."
for i in $(seq 1 $MAX_RETRIES); do
  if curl -sf --max-time 5 "http://localhost:$PORT/health" > /dev/null 2>&1; then
    log "✅ $SELF pronto!"
    break
  fi
  if [ "$i" -eq "$MAX_RETRIES" ]; then
    log "⚠️  Timeout aguardando $SELF"
    exit 0
  fi
  sleep 2
done

# ── Descobre API key própria ─────────────────────────────────────────────────

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

BASE="http://localhost:$PORT/api/v3"
HEADERS="X-Api-Key: $API_KEY"

# ── Aguarda dependências ───────────────────────────────────────────────────────

log "Aguardando dependências..."
for dep in "http://qbittorrent:8080/api/v2/app/version" \
           "http://prowlarr:9696/health"; do
  name=$(echo "$dep" | cut -d/ -f3 | cut -d: -f1)
  for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf --max-time 5 "$dep" > /dev/null 2>&1; then
      log "✅ $name pronto!"
      break 2
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
      log "⚠️  Timeout aguardando $name"
      exit 0
    fi
    sleep 2
  done
done

# ── Download Client (qBittorrent) ────────────────────────────────────────────

log "Configurando download client..."

DC_PAYLOAD='{"name":"qBittorrent","implementation":"QBittorrent","configContract":"QBittorrentSettings","enable":true,"protocol":"torrent","fields":[{"name":"host","value":"qbittorrent"},{"name":"port","value":8080},{"name":"username","value":"admin"},{"name":"password","value":"adminadmin"},{"name":"movieCategory","value":""},{"name":"tvCategory","value":""}]}'

EXISTING_DC=$(curl -sf --max-time 10 -H "$HEADERS" "$BASE/downloadclient" 2>/dev/null || echo "[]")
HAS_QBIT=$(echo "$EXISTING_DC" | python3 -c "import sys,json; d=json.load(sys.stdin); print('1' if any(x.get('implementation')=='QBittorrent' for x in d) else '')" 2>/dev/null)

if [ -z "$HAS_QBIT" ]; then
  if curl -sf --max-time 10 -H "$HEADERS" -H "Content-Type: application/json" -X POST -d "$DC_PAYLOAD" "$BASE/downloadclient" > /dev/null 2>&1; then
    log "✅ qBittorrent adicionado"
  else
    log "⚠️  Falha ao adicionar qBittorrent"
  fi
else
  log "ℹ️  qBittorrent já existe"
fi

# ── Indexer (Prowlarr) ───────────────────────────────────────────────────────

log "Configurando indexer Prowlarr..."

# Lê API key do Prowlarr
if [ ! -f "$PROWLARR_CONFIG" ]; then
  log "⚠️  Config do Prowlarr não encontrado"
  exit 0
fi

PROWLARR_KEY=$(python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('$PROWLARR_CONFIG')
    print(tree.getroot().findtext('ApiKey', ''))
except Exception:
    pass
")

if [ -z "$PROWLARR_KEY" ]; then
  log "⚠️  Prowlarr API key não encontrada"
  exit 0
fi

IDX_PAYLOAD=$(printf '{"name":"Prowlarr","implementation":"Newznab","configContract":"NewznabSettings","enable":true,"protocol":"torrent","fields":[{"name":"baseUrl","value":"http://prowlarr:9696/1/api"},{"name":"apiKey","value":"%s"}]}' "$PROWLARR_KEY")

EXISTING_IDX=$(curl -sf --max-time 10 -H "$HEADERS" "$BASE/indexer" 2>/dev/null || echo "[]")
HAS_PROWLARR=$(echo "$EXISTING_IDX" | python3 -c "import sys,json; d=json.load(sys.stdin); print('1' if any(x.get('name')=='Prowlarr' for x in d) else '')" 2>/dev/null)

if [ -z "$HAS_PROWLARR" ]; then
  if curl -sf --max-time 10 -H "$HEADERS" -H "Content-Type: application/json" -X POST -d "$IDX_PAYLOAD" "$BASE/indexer" > /dev/null 2>&1; then
    log "✅ Prowlarr indexer adicionado"
  else
    log "⚠️  Falha ao adicionar Prowlarr indexer"
  fi
else
  log "ℹ️  Prowlarr indexer já existe"
fi

log "✅ $SELF post-setup concluído!"

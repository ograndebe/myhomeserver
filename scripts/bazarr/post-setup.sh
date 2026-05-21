#!/bin/sh
set -e

SELF="bazarr"
PORT=6767
CONFIG_INI="/config/config/config.ini"
RADARR_CONFIG="/radarr-config/config.xml"
SONARR_CONFIG="/sonarr-config/config.xml"
MAX_RETRIES=60

log() {
  echo "[$SELF-post-setup] $1"
}

# ── Aguarda Bazarr ────────────────────────────────────────────────────────────

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

# ── Descobre API key do Bazarr ────────────────────────────────────────────────

if [ ! -f "$CONFIG_INI" ]; then
  log "⚠️  config.ini não encontrado"
  exit 0
fi

API_KEY=$(python3 -c "
import re
try:
    with open('$CONFIG_INI') as f:
        m = re.search(r'api_key\s*=\s*(.+)', f.read())
        print(m.group(1).strip() if m else '')
except Exception:
    pass
")

if [ -z "$API_KEY" ]; then
  log "⚠️  API key não encontrada"
  exit 0
fi

BASE="http://localhost:$PORT/api"
HEADERS="X-API-Key: $API_KEY"

# ── Aguarda dependências ───────────────────────────────────────────────────────

log "Aguardando dependências..."
for dep in "http://radarr:7878/health" \
           "http://sonarr:8989/health"; do
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

# ── Lê API keys do Radarr e Sonarr ───────────────────────────────────────────

read_api_key() {
  python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('$1')
    print(tree.getroot().findtext('ApiKey', ''))
except Exception:
    pass
"
}

RADARR_KEY=""
SONARR_KEY=""

if [ -f "$RADARR_CONFIG" ]; then
  RADARR_KEY=$(read_api_key "$RADARR_CONFIG")
fi

if [ -f "$SONARR_CONFIG" ]; then
  SONARR_KEY=$(read_api_key "$SONARR_CONFIG")
fi

# ── Configura conexões ───────────────────────────────────────────────────────

log "Configurando conexões..."

# Verifica settings atuais para idempotência
SETTINGS=$(curl -sf --max-time 10 -H "$HEADERS" "$BASE/system/settings" 2>/dev/null || echo "{}")

# Radarr
if [ -n "$RADARR_KEY" ]; then
  RADARR_CFG='{"ip":"radarr","port":7878,"base_url":"/","ssl":false,"apikey":"'$RADARR_KEY'","enabled":true}'
  HAS_RADARR=$(echo "$SETTINGS" | python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get('settings',{}).get('radarr',{}); print('1' if s.get('enabled') and s.get('apikey') else '')" 2>/dev/null)
  if [ -z "$HAS_RADARR" ]; then
    if curl -sf --max-time 10 -H "$HEADERS" -H "Content-Type: application/json" -X PATCH -d '{"radarr":'$RADARR_CFG'}' "$BASE/system/settings" > /dev/null 2>&1; then
      log "✅ Bazarr conectado ao Radarr"
    else
      log "⚠️  Falha ao conectar Bazarr ao Radarr"
    fi
  else
    log "ℹ️  Radarr já configurado"
  fi
else
  log "⚠️  Radarr API key não encontrada"
fi

# Sonarr
if [ -n "$SONARR_KEY" ]; then
  SONARR_CFG='{"ip":"sonarr","port":8989,"base_url":"/","ssl":false,"apikey":"'$SONARR_KEY'","enabled":true}'
  HAS_SONARR=$(echo "$SETTINGS" | python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get('settings',{}).get('sonarr',{}); print('1' if s.get('enabled') and s.get('apikey') else '')" 2>/dev/null)
  if [ -z "$HAS_SONARR" ]; then
    if curl -sf --max-time 10 -H "$HEADERS" -H "Content-Type: application/json" -X PATCH -d '{"sonarr":'$SONARR_CFG'}' "$BASE/system/settings" > /dev/null 2>&1; then
      log "✅ Bazarr conectado ao Sonarr"
    else
      log "⚠️  Falha ao conectar Bazarr ao Sonarr"
    fi
  else
    log "ℹ️  Sonarr já configurado"
  fi
else
  log "⚠️  Sonarr API key não encontrada"
fi

log "✅ $SELF post-setup concluído!"

#!/bin/sh
set -e

TRACKERS_FILE="/app/trackers.txt"
BASE_URL="http://localhost:8080/api/v2"
MAX_RETRIES=60
QBIT_USER="admin"
QBIT_PASS="adminadmin"

log() {
  echo "[qbittorrent-post-setup] $1"
}

# ── Aguarda qBittorrent ───────────────────────────────────────────────────────

log "Aguardando qBittorrent..."
for i in $(seq 1 $MAX_RETRIES); do
  if curl -sf --max-time 5 "$BASE_URL/app/version" > /dev/null 2>&1; then
    log "✅ qBittorrent pronto!"
    break
  fi
  if [ "$i" -eq "$MAX_RETRIES" ]; then
    log "⚠️  Timeout aguardando qBittorrent"
    exit 0
  fi
  sleep 2
done

# ── Login ──────────────────────────────────────────────────────────────────────

log "Autenticando no qBittorrent..."
LOGIN=$(curl -sf --max-time 10 -X POST \
  -d "username=$QBIT_USER&password=$QBIT_PASS" \
  "$BASE_URL/auth/login" 2>/dev/null || echo "")

if [ "$LOGIN" != "Ok." ]; then
  log "⚠️  Falha no login (senha pode ter sido alterada)"
  exit 0
fi

# ── Verifica idempotência ────────────────────────────────────────────────────

PREFS=$(curl -sf --max-time 10 "$BASE_URL/app/preferences" 2>/dev/null || echo "{}")
TRACKERS_ENABLED=$(echo "$PREFS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('add_trackers_enabled',False))" 2>/dev/null || echo "False")
EXISTING_TRACKERS=$(echo "$PREFS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('add_trackers',''))" 2>/dev/null || echo "")

if [ "$TRACKERS_ENABLED" = "True" ] && [ -n "$EXISTING_TRACKERS" ]; then
  log "ℹ️  Trackers já configurados — pulando"
  exit 0
fi

# ── Injeta trackers ───────────────────────────────────────────────────────────

if [ ! -f "$TRACKERS_FILE" ]; then
  log "⚠️  trackers.txt não encontrado"
  exit 0
fi

log "Configurando trackers..."

# Constrói lista de trackers separados por \\n
trackers=""
while IFS= read -r tracker; do
  [ -z "$tracker" ] && continue
  if [ -n "$trackers" ]; then
    trackers="${trackers}\\n${tracker}"
  else
    trackers="$tracker"
  fi
done < "$TRACKERS_FILE"

if [ -z "$trackers" ]; then
  log "⚠️  Nenhum tracker encontrado"
  exit 0
fi

# Escapa para JSON
json_trackers=$(printf '%s' "$trackers" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()), end=""')

payload="{\"add_trackers_enabled\":true,\"add_trackers\":$json_trackers}"

if curl -sf --max-time 10 -X POST \
  -d "json=$payload" \
  "$BASE_URL/app/setPreferences" > /dev/null 2>&1; then
  log "✅ Trackers injetados no qBittorrent"
else
  log "⚠️  Falha ao injetar trackers"
fi

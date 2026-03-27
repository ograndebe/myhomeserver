#!/usr/bin/env bash
# =============================================================================
# sync-server.sh — Sincroniza o repositório local com o servidor remoto
# =============================================================================
# Uso: ./scripts/sync-server.sh [OPÇÕES]
#
# Exemplo:
#   ./scripts/sync-server.sh                    # modo interativo
#   ./scripts/sync-server.sh --dry-run           # preview sem copiar
#   ./scripts/sync-server.sh --force             # sem confirmação
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DRY_RUN=""
FORCE=""
EXCLUDE_FILE=""
RSYNC_OPTS="-avz --progress"

SERVER_HOST="192.168.15.6"
SERVER_USER="rafael"
SERVER_PATH="/home/rafael/homeserver"

show_help() {
  cat << EOF
Uso: $(basename "$0") [OPÇÕES]

Sincroniza o repositório local com o servidor via rsync + SSH.

Opções:
  -h, --help           Mostra esta ajuda
  -d, --dry-run        Preview sem copiar (rsync --dry-run)
  -f, --force          Ignora confirmação antes de sincronizar
  -H, --host HOST      Host do servidor (padrão: $SERVER_HOST)
  -u, --user USER      Usuário SSH (padrão: $SERVER_USER)
  -p, --path PATH      Caminho remoto (padrão: $SERVER_PATH)
  -e, --exclude FILE   Arquivo .rsyncignore customizado

Variáveis de ambiente:
  SSH_KEY              Caminho para chave SSH (padrão: ~/.ssh/id_rsa)

Exemplos:
  $(basename "$0")                    # modo interativo
  $(basename "$0") --dry-run          # preview
  $(basename "$0") --force            # sincroniza direto
  SSH_KEY=\$HOME/.ssh/minha_chave $(basename "$0")

EOF
}

log_info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}   $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error()   { echo -e "${RED}[ERR]${NC}  $*" >&2; exit 1; }

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        show_help
        exit 0
        ;;
      -d|--dry-run)
        DRY_RUN="--dry-run"
        RSYNC_OPTS="$RSYNC_OPTS --dry-run"
        shift
        ;;
      -f|--force)
        FORCE="yes"
        shift
        ;;
      -H|--host)
        SERVER_HOST="$2"
        shift 2
        ;;
      -u|--user)
        SERVER_USER="$2"
        shift 2
        ;;
      -p|--path)
        SERVER_PATH="$2"
        shift 2
        ;;
      -e|--exclude)
        EXCLUDE_FILE="$2"
        shift 2
        ;;
      *)
        log_error "Opção desconhecida: $1"
        ;;
    esac
  done
}

get_rsync_excludes() {
  local excludes=(
    ".git/"
    ".gitignore"
    "*.md"
    ".opencode/"
    "credentials.txt"
    "build/"
  )

  if [[ -n "$EXCLUDE_FILE" && -f "$EXCLUDE_FILE" ]]; then
    cat "$EXCLUDE_FILE"
  else
    printf '%s\n' "${excludes[@]}"
  fi
}

check_prerequisites() {
  if ! command -v rsync &>/dev/null; then
    log_error "rsync não encontrado. Instale com: apt-get install rsync ou brew install rsync"
  fi

  if ! ssh -o BatchMode=yes "${SERVER_USER}@${SERVER_HOST}" echo "ok" &>/dev/null; then
    log_error "Não foi possível conectar via SSH em ${SERVER_USER}@${SERVER_HOST}"
  fi
}

show_summary() {
  echo ""
  echo -e "${BOLD}╔════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}║       Sync Server — Resumo             ║${NC}"
  echo -e "${BOLD}╚════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "  ${CYAN}Origem:${NC}      $(pwd)/"
  echo -e "  ${CYAN}Destino:${NC}     ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"
  echo ""
  echo "  Arquivos excluídos:"
  while IFS= read -r line; do
    [[ -n "$line" ]] && echo -e "    ${YELLOW}- $line${NC}"
  done < <(get_rsync_excludes)
  echo ""
}

confirm_sync() {
  if [[ -n "$FORCE" ]]; then
    return 0
  fi

  local confirm
  read -rp "  Continuar com a sincronização? [s/N]: " confirm
  confirm="${confirm:-n}"

  if [[ ! "$confirm" =~ ^[sS]$ ]]; then
    echo "Sincronização cancelada."
    exit 0
  fi
}

sync_to_server() {
  local ssh_cmd="ssh -o StrictHostKeyChecking=no"

  log_info "Sincronizando..."
  echo ""

  local excludes_args=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && excludes_args+=(--exclude="$line")
  done < <(get_rsync_excludes)

  if rsync -avz \
    -e "$ssh_cmd" \
    "${excludes_args[@]}" \
    --delete \
    ./ \
    "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"; then
    echo ""
    log_success "Sincronização concluída!"
  else
    log_error "Falha na sincronização."
  fi
}

main() {
  parse_args "$@"

  echo ""
  echo -e "${BOLD}╔════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}║       Sync Server                     ║${NC}"
  echo -e "${BOLD}╚════════════════════════════════════════╝${NC}"
  echo ""

  check_prerequisites
  show_summary
  confirm_sync
  sync_to_server
}

main "$@"

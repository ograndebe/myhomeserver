#!/usr/bin/env bash
# =============================================================================
# build.sh — Mecanismo central de build para home server
# =============================================================================
# Uso: ./build.sh [--help] [--version]
# Fluxo:
#   1. Verifica dependências (envsubst, openssl, docker)
#   2. Detecta ou cria build/.env
#   3. Gera senhas e hashes se necessário
#   4. Processa templates via envsubst → build/
# =============================================================================

set -euo pipefail

VERSION="1.0.0"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*" >&2; exit 1; }

usage() {
  cat << EOF
Uso: $(basename "$0") [OPÇÕES]

Gera artefatos em build/ a partir de templates/ usando variáveis de ambiente.

Opções:
  -h, --help     Mostra esta ajuda
  -v, --version  Mostra a versão

Fluxo:
  1. Verifica dependências (envsubst, openssl, docker)
  2. Se build/.env não existir, solicita dados interativamente
  3. Gera senhas e hashes para Traefik e AdGuard
  4. Processa templates/*.tmpl → build/ via envsubst

EOF
}

check_dependencies() {
  if ! command -v envsubst &>/dev/null; then
    error "envsubst não encontrado. Instale com: apt-get install gettext-base"
  fi
  if ! command -v openssl &>/dev/null; then
    error "openssl não encontrado."
  fi
  if ! command -v docker &>/dev/null; then
    error "docker não encontrado."
  fi
}

gen_password() {
  openssl rand -base64 32 | tr -d '/+=' | cut -c1-32
}

gen_htpasswd() {
  local user="$1"
  local pass="$2"
  docker run --rm httpd:alpine htpasswd -nbB "$user" "$pass" 2>/dev/null \
    || error "Falha ao gerar hash htpasswd."
}

gen_adguard_hash() {
  local pass="$1"
  docker run --rm httpd:alpine htpasswd -nbB "" "$pass" 2>/dev/null \
    | cut -d: -f2 \
    || error "Falha ao gerar hash para AdGuard."
}

detect_ip() {
  local ip
  ip=$(hostname -I 2>/dev/null | awk '{print $1}')
  if [[ -z "$ip" ]]; then
    ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}')
  fi
  echo "$ip"
}

collect_env_data() {
  local detected_ip
  detected_ip=$(detect_ip)

  echo ""
  echo -e "${BOLD}>> Configuração do servidor${NC}"
  echo ""

  read -rp "  Domínio (ex: example.com): " DOMAIN
  if [[ -z "$DOMAIN" ]]; then
    error "Domínio não pode ser vazio."
  fi

  read -rp "  IP local do servidor (padrão: $detected_ip): " SERVER_IP
  SERVER_IP="${SERVER_IP:-$detected_ip}"
  if [[ -z "$SERVER_IP" ]]; then
    error "IP não pode ser vazio."
  fi

  read -rp "  Diretório de dados (padrão: /opt/homeserver/data): " DATA_DIR
  DATA_DIR="${DATA_DIR:-/opt/homeserver/data}"

  read -rp "  Usuário do Traefik Dashboard (padrão: admin): " TRAEFIK_DASHBOARD_USER
  TRAEFIK_DASHBOARD_USER="${TRAEFIK_DASHBOARD_USER:-admin}"

  echo ""
  echo -e "${BOLD}>> Cloudflare (DNS Challenge)${NC}"
  echo -e "   ${YELLOW}Crie um token em: https://dash.cloudflare.com/profile/api-tokens${NC}"
  echo -e "   ${YELLOW}Permissões: Zone / DNS / Edit${NC}"
  echo ""

  read -rp "  Cloudflare Email: " CLOUDFLARE_EMAIL
  if [[ -z "$CLOUDFLARE_EMAIL" ]]; then
    error "Email não pode ser vazio."
  fi

  read -rp "  Cloudflare API Token: " CLOUDFLARE_API_TOKEN
  if [[ -z "$CLOUDFLARE_API_TOKEN" ]]; then
    error "API Token não pode ser vazio."
  fi

  read -rp "  Quantos peers WireGuard? (padrão: 5): " WIREGUARD_PEER_COUNT
  WIREGUARD_PEER_COUNT="${WIREGUARD_PEER_COUNT:-5}"

  echo ""
  echo -e "${BOLD}>> Resumo${NC}"
  echo ""
  echo "  Domínio:              $DOMAIN"
  echo "  IP do Servidor:       $SERVER_IP"
  echo "  Diretório de dados:   $DATA_DIR"
  echo "  Usuário Traefik:      $TRAEFIK_DASHBOARD_USER"
  echo "  Cloudflare Email:     $CLOUDFLARE_EMAIL"
  echo "  Cloudflare API Token: ${CLOUDFLARE_API_TOKEN:0:8}..."
  echo "  Peers WireGuard:      $WIREGUARD_PEER_COUNT"
  echo ""

  read -rp "  Criar build/.env com esses dados? [s/N]: " confirm
  confirm="${confirm:-n}"
  if [[ ! "$confirm" =~ ^[sS]$ ]]; then
    error "Criação do .env cancelada."
  fi
}

ensure_build_dir() {
  if [[ ! -d "$BUILD_DIR" ]]; then
    info "Criando diretório $BUILD_DIR..."
    mkdir -p "$BUILD_DIR"
  fi
}

create_env_file() {
  {
    printf '%s=%s\n' "DOMAIN" "$DOMAIN"
    printf '%s=%s\n' "SERVER_IP" "$SERVER_IP"
    printf '%s=%s\n' "DATA_DIR" "$DATA_DIR"
    printf '%s=%s\n' "CLOUDFLARE_EMAIL" "$CLOUDFLARE_EMAIL"
    printf '%s=%s\n' "CLOUDFLARE_API_TOKEN" "$CLOUDFLARE_API_TOKEN"
    printf '%s=%s\n' "TRAEFIK_DASHBOARD_USER" "$TRAEFIK_DASHBOARD_USER"
    printf '%s=%s\n' "TRAEFIK_DASHBOARD_PASSWORD" "$TRAEFIK_DASHBOARD_PASSWORD"
    printf '%s=%s\n' "ADGUARD_ADMIN_PASSWORD" "$ADGUARD_ADMIN_PASSWORD"
    printf '%s=%s\n' "WIREGUARD_PEER_COUNT" "$WIREGUARD_PEER_COUNT"
  } > "$BUILD_DIR/.env"
  success "build/.env criado."
}

generate_passwords() {
  TRAEFIK_DASHBOARD_USER="${TRAEFIK_DASHBOARD_USER:-admin}"
  if [[ -z "${TRAEFIK_DASHBOARD_PASSWORD:-}" ]]; then
    info "Gerando senhas..."
    TRAEFIK_DASHBOARD_PASSWORD=$(gen_password)
    ADGUARD_ADMIN_PASSWORD=$(gen_password)
    export TRAEFIK_DASHBOARD_USER TRAEFIK_DASHBOARD_PASSWORD ADGUARD_ADMIN_PASSWORD
    success "Senhas geradas."
  fi
}

load_env() {
  if [[ ! -f "$BUILD_DIR/.env" ]]; then
    return 1
  fi
  set -a
  # shellcheck source=/dev/null
  source "$BUILD_DIR/.env"
  set +a
  TRAEFIK_DASHBOARD_USERS=$(gen_htpasswd "$TRAEFIK_DASHBOARD_USER" "$TRAEFIK_DASHBOARD_PASSWORD")
  ADGUARD_ADMIN_PASSWORD_HASH=$(gen_adguard_hash "$ADGUARD_ADMIN_PASSWORD")
}

process_templates() {
  if [[ ! -d "templates" ]]; then
    warn "Diretório templates/ não encontrado. Nenhum template processado."
    return 0
  fi

  local tmpl_count
  tmpl_count=$(find templates/ -name "*.tmpl" 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$tmpl_count" -eq 0 ]]; then
    warn "Nenhum arquivo *.tmpl encontrado em templates/."
    return 0
  fi

  info "Processando $tmpl_count template(s)..."

  while IFS= read -r -d '' tmpl; do
    local relative_path="${tmpl#templates/}"
    local output_path="$BUILD_DIR/$relative_path"
    output_path="${output_path%.tmpl}"

    local output_dir
    output_dir=$(dirname "$output_path")
    if [[ ! -d "$output_dir" ]]; then
      mkdir -p "$output_dir"
    fi

    local hash_value="$ADGUARD_ADMIN_PASSWORD_HASH"
    local users_value="$TRAEFIK_DASHBOARD_USERS"
    ADGUARD_ADMIN_PASSWORD_HASH="__ADGUARD_HASH__"
    TRAEFIK_DASHBOARD_USERS="__TRAEFIK_USERS__"
    export ADGUARD_ADMIN_PASSWORD_HASH TRAEFIK_DASHBOARD_USERS
    envsubst < "$tmpl" > "$output_path"
    sed -i \
      -e "s/__ADGUARD_HASH__/$hash_value/g" \
      -e "s/__TRAEFIK_USERS__/$users_value/g" \
      "$output_path"
    unset ADGUARD_ADMIN_PASSWORD_HASH TRAEFIK_DASHBOARD_USERS
    success "  $relative_path → build/$relative_path"
  done < <(find templates/ -name "*.tmpl" -print0)

  success "Templates processados."
}

show_credentials() {
  if [[ -n "${TRAEFIK_DASHBOARD_PASSWORD:-}" ]]; then
    echo ""
    echo -e "${YELLOW}${BOLD}>> Credenciais geradas (guarde em local seguro)${NC}"
    echo ""
    echo "  Traefik Dashboard: https://traefik.$DOMAIN"
    echo "    Usuário: $TRAEFIK_DASHBOARD_USER"
    echo "    Senha:   $TRAEFIK_DASHBOARD_PASSWORD"
    echo ""
    echo "  AdGuard Home: https://adguard.$DOMAIN"
    echo "    Usuário: admin"
    echo "    Senha:   $ADGUARD_ADMIN_PASSWORD"
    echo ""
  fi
}

main() {
  local build_dir="${BUILD_DIR:-$(pwd)/build}"
  export BUILD_DIR="$build_dir"

  check_dependencies

  if load_env; then
    info "build/.env encontrado. Prosseguindo..."
  else
    echo ""
    echo -e "${BOLD}╔════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║       Home Server — Build Script       ║${NC}"
    echo -e "${BOLD}╚════════════════════════════════════════╝${NC}"
    echo ""
    warn "build/.env não encontrado. Coletando dados..."
    echo ""

    collect_env_data
    ensure_build_dir
    generate_passwords
    create_env_file
    load_env
  fi

  generate_passwords
  ensure_build_dir
  process_templates

  echo ""
  echo -e "${GREEN}${BOLD}╔════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}${BOLD}║         Build concluído! ✓             ║${NC}"
  echo -e "${GREEN}${BOLD}╚════════════════════════════════════════╝${NC}"
  echo ""
  info "Artefatos gerados:"
  ls -la "$BUILD_DIR/"

  show_credentials
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
  -v|--version)
    echo "build.sh version $VERSION"
    exit 0
    ;;
  *)
    main
    ;;
esac

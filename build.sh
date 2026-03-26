#!/usr/bin/env bash
# =============================================================================
# build.sh — Gerador de artefato para home server Docker
# =============================================================================
# Uso: ./build.sh
# Gera a pasta ./build/ com todos os arquivos prontos para deploy.
# =============================================================================

set -euo pipefail

# --- Cores ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Helpers ---
info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*" >&2; exit 1; }

require_cmd() {
  command -v "$1" &>/dev/null || error "Comando '$1' não encontrado. Instale antes de continuar."
}

# --- Verifica dependências ---
require_cmd docker
require_cmd openssl

gen_password() {
  openssl rand -base64 32 | tr -d '/+=' | cut -c1-32
}

# Gera hash bcrypt via container httpd — consistente em qualquer host
gen_htpasswd() {
  local user="$1"
  local pass="$2"
  local raw
  raw=$(docker run --rm httpd:alpine htpasswd -nbB "$user" "$pass" 2>/dev/null) \
    || error "Falha ao gerar hash bcrypt via Docker. Verifique se o Docker está rodando."
  # Escapa $ → $$ para uso em docker-compose labels
  echo "$raw" | sed 's/\$/\$\$/g'
}

# Gera hash bcrypt para o AdGuard (formato htpasswd sem escape)
gen_adguard_hash() {
  local pass="$1"
  docker run --rm httpd:alpine htpasswd -nbB "" "$pass" 2>/dev/null \
    | cut -d: -f2 \
    || error "Falha ao gerar hash para AdGuard."
}

# =============================================================================
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║       Home Server — Build Script         ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""

# =============================================================================
# 1. Coleta de informações
# =============================================================================
echo -e "${BOLD}>> Configuração do servidor${NC}"
echo ""

read -rp "  Domínio (ex: meuserver.com.br): " DOMAIN
[[ -z "$DOMAIN" ]] && error "Domínio não pode ser vazio."

read -rp "  IP local do servidor (ex: 192.168.1.100): " SERVER_IP
[[ -z "$SERVER_IP" ]] && error "IP não pode ser vazio."

read -rp "  E-mail para Let's Encrypt: " ACME_EMAIL
[[ -z "$ACME_EMAIL" ]] && error "E-mail não pode ser vazio."

echo ""
echo -e "${BOLD}>> Cloudflare DNS Challenge${NC}"
echo -e "   ${YELLOW}Crie um token em: https://dash.cloudflare.com/profile/api-tokens${NC}"
echo -e "   ${YELLOW}Permissões necessárias: Zone / DNS / Edit${NC}"
echo ""
read -rp "  Cloudflare API Token: " CF_DNS_API_TOKEN
[[ -z "$CF_DNS_API_TOKEN" ]] && error "CF API Token não pode ser vazio."

echo ""
echo -e "${BOLD}>> Diretório de dados${NC}"
echo -e "   ${YELLOW}Todos os volumes dos containers serão armazenados aqui.${NC}"
echo -e "   ${YELLOW}Faça backup deste diretório para preservar seus dados.${NC}"
echo ""
read -rp "  Diretório de dados (padrão: /opt/homeserver/data): " DATA_DIR
DATA_DIR="${DATA_DIR:-/opt/homeserver/data}"

echo ""
echo -e "${BOLD}>> Usuário do Traefik Dashboard${NC}"
read -rp "  Usuário admin (padrão: admin): " TRAEFIK_DASHBOARD_USER
TRAEFIK_DASHBOARD_USER="${TRAEFIK_DASHBOARD_USER:-admin}"

# =============================================================================
# 2. Gera senhas e hashes
# =============================================================================
echo ""
info "Gerando senhas e hashes (pode demorar alguns segundos)..."

TRAEFIK_DASHBOARD_PASSWORD=$(gen_password)
ADGUARD_ADMIN_PASSWORD=$(gen_password)
WIREGUARD_PEER_COUNT=5

info "  Gerando hash bcrypt para Traefik..."
TRAEFIK_DASHBOARD_PASSWORD_HASH=$(gen_htpasswd "$TRAEFIK_DASHBOARD_USER" "$TRAEFIK_DASHBOARD_PASSWORD")

info "  Gerando hash bcrypt para AdGuard..."
ADGUARD_ADMIN_PASSWORD_HASH=$(gen_adguard_hash "$ADGUARD_ADMIN_PASSWORD")

success "Senhas e hashes gerados."

# =============================================================================
# 3. Prepara a pasta build/
# =============================================================================
BUILD_DIR="$(pwd)/build"

if [[ -d "$BUILD_DIR" ]]; then
  warn "Pasta build/ já existe. Sobrescrevendo..."
  rm -rf "$BUILD_DIR"
fi

info "Copiando arquivos de src/ para build/..."
cp -r "$(pwd)/src/." "$BUILD_DIR"

# =============================================================================
# 4. Copia AdGuardHome.yaml para o diretório de conf que será montado
# O arquivo precisa estar em DATA_DIR/adguard/conf/ no servidor.
# O build.sh gera o arquivo processado em build/adguard/AdGuardHome.yaml
# e o install.sh (gerado abaixo) cuida de colocá-lo no lugar certo.
# =============================================================================
mkdir -p "$BUILD_DIR/adguard"

# =============================================================================
# 5. Função de substituição de placeholders
# =============================================================================
replace_placeholders() {
  local file="$1"

  # Usa arquivos temporários para substituições com caracteres especiais
  local tmp
  tmp=$(mktemp)

  sed \
    -e "s|{{DOMAIN}}|${DOMAIN}|g" \
    -e "s|{{SERVER_IP}}|${SERVER_IP}|g" \
    -e "s|{{DATA_DIR}}|${DATA_DIR}|g" \
    -e "s|{{ACME_EMAIL}}|${ACME_EMAIL}|g" \
    -e "s|{{TRAEFIK_DASHBOARD_USER}}|${TRAEFIK_DASHBOARD_USER}|g" \
    -e "s|{{ADGUARD_ADMIN_PASSWORD}}|${ADGUARD_ADMIN_PASSWORD}|g" \
    "$file" > "$tmp"

  # CF_DNS_API_TOKEN e hashes podem ter caracteres especiais — usa python para esses
  python3 - "$tmp" \
    "$CF_DNS_API_TOKEN" \
    "$TRAEFIK_DASHBOARD_PASSWORD_HASH" \
    "$ADGUARD_ADMIN_PASSWORD_HASH" << 'PYEOF'
import sys

filepath = sys.argv[1]
cf_token = sys.argv[2]
traefik_hash = sys.argv[3]
adguard_hash = sys.argv[4]

with open(filepath, 'r') as f:
    content = f.read()

content = content.replace('{{CF_DNS_API_TOKEN}}', cf_token)
content = content.replace('{{TRAEFIK_DASHBOARD_PASSWORD_HASH}}', traefik_hash)
content = content.replace('{{ADGUARD_ADMIN_PASSWORD_HASH}}', adguard_hash)

with open(filepath, 'w') as f:
    f.write(content)
PYEOF

  cp "$tmp" "$file"
  rm "$tmp"
}

# Processa todos os arquivos de template no build/
info "Substituindo placeholders..."
while IFS= read -r -d '' file; do
  replace_placeholders "$file"
done < <(find "$BUILD_DIR" -type f \( \
  -name "*.yml" -o -name "*.yaml" \
  -o -name "*.env" -o -name "*.conf" \
  -o -name "*.toml" \) -print0)

success "Placeholders substituídos."

# =============================================================================
# 6. Gera install.sh — script a ser rodado no servidor
# =============================================================================
INSTALL_FILE="$BUILD_DIR/install.sh"
cat > "$INSTALL_FILE" << INSTALL_EOF
#!/usr/bin/env bash
# =============================================================================
# install.sh — Prepara o servidor e sobe os containers
# Execute este script no servidor após copiar a pasta build/
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
info()    { echo -e "\${CYAN}[INFO]\${NC} \$*"; }
success() { echo -e "\${GREEN}[OK]\${NC}   \$*"; }
warn()    { echo -e "\${YELLOW}[WARN]\${NC} \$*"; }
error()   { echo -e "\${RED}[ERR]\${NC}  \$*" >&2; exit 1; }

echo ""
echo -e "\${BOLD}╔══════════════════════════════════════════╗\${NC}"
echo -e "\${BOLD}║     Home Server — Install Script         ║\${NC}"
echo -e "\${BOLD}╚══════════════════════════════════════════╝\${NC}"
echo ""

# --- 1. Libera porta 53 (systemd-resolved) ---
info "Configurando systemd-resolved para liberar porta 53..."
if grep -q "DNSStubListener" /etc/systemd/resolved.conf 2>/dev/null; then
  sudo sed -i 's/.*DNSStubListener=.*/DNSStubListener=no/' /etc/systemd/resolved.conf
else
  echo "DNSStubListener=no" | sudo tee -a /etc/systemd/resolved.conf > /dev/null
fi
sudo systemctl restart systemd-resolved
success "Porta 53 liberada."

# --- 2. Cria diretórios de dados ---
info "Criando diretório de dados em ${DATA_DIR}..."
sudo mkdir -p \\
  "${DATA_DIR}/traefik/acme" \\
  "${DATA_DIR}/adguard/work" \\
  "${DATA_DIR}/adguard/conf" \\
  "${DATA_DIR}/wireguard"

# --- 3. Copia config do AdGuard (apenas se não existir — preserva dados) ---
ADGUARD_CONF="${DATA_DIR}/adguard/conf/AdGuardHome.yaml"
if [[ ! -f "\$ADGUARD_CONF" ]]; then
  info "Instalando configuração do AdGuard Home..."
  sudo cp "\$(dirname "\$0")/adguard/AdGuardHome.yaml" "\$ADGUARD_CONF"
  success "AdGuard configurado."
else
  warn "AdGuard já configurado — mantendo configuração existente."
fi

# Ajusta permissões
sudo chown -R 1000:1000 "${DATA_DIR}" 2>/dev/null || true

# --- 4. Sobe os containers ---
info "Subindo containers..."
docker compose up -d
success "Containers no ar!"

echo ""
echo -e "\${GREEN}\${BOLD}════════════════════════════════════════════\${NC}"
echo -e "\${GREEN}\${BOLD}  Instalação concluída! ✓\${NC}"
echo -e "\${GREEN}\${BOLD}════════════════════════════════════════════\${NC}"
echo ""
echo "  Configure o DNS do seu roteador para: ${SERVER_IP}"
echo ""
echo "  Acesse:"
echo "    https://traefik.${DOMAIN}"
echo "    https://adguard.${DOMAIN}"
echo "    https://app1.${DOMAIN}"
echo "    https://app2.${DOMAIN}"
echo ""
INSTALL_EOF

chmod +x "$INSTALL_FILE"
success "install.sh gerado."

# =============================================================================
# 7. Gera credentials.txt
# =============================================================================
CREDS_FILE="$(pwd)/credentials.txt"
cat > "$CREDS_FILE" << EOF
=============================================================
  Home Server — Credenciais geradas em $(date)
=============================================================

  Domínio:          ${DOMAIN}
  IP do Servidor:   ${SERVER_IP}
  Diretório dados:  ${DATA_DIR}

  --- Traefik Dashboard ---
  URL:              https://traefik.${DOMAIN}
  Usuário:          ${TRAEFIK_DASHBOARD_USER}
  Senha:            ${TRAEFIK_DASHBOARD_PASSWORD}

  --- AdGuard Home ---
  URL:              https://adguard.${DOMAIN}
  Usuário:          admin
  Senha:            ${ADGUARD_ADMIN_PASSWORD}

  --- WireGuard ---
  Porta:            51820/UDP
  Peers gerados:    ${WIREGUARD_PEER_COUNT}

  --- Serviços de teste ---
  app1:             https://app1.${DOMAIN}
  app2:             https://app2.${DOMAIN}

  --- Backup ---
  Diretório:        ${DATA_DIR}
  Comando sugerido: rsync -av ${DATA_DIR} usuario@backup-server:/backups/homeserver

=============================================================
  GUARDE ESTE ARQUIVO COM SEGURANÇA. NÃO COMMITE NO GIT.
=============================================================
EOF

chmod 600 "$CREDS_FILE"

# =============================================================================
# 8. Resumo final
# =============================================================================
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║           Build concluído! ✓             ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  📁 Artefato:     ${BOLD}./build/${NC}"
echo -e "  🔑 Credenciais:  ${BOLD}./credentials.txt${NC}"
echo ""
echo -e "${BOLD}  Para instalar no servidor:${NC}"
echo ""
echo "    scp -r build/ usuario@${SERVER_IP}:~/homeserver"
echo "    ssh usuario@${SERVER_IP} 'cd ~/homeserver && bash install.sh'"
echo ""
warn "Adicione credentials.txt ao .gitignore!"
echo ""

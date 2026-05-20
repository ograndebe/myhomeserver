# Homeserver Setup Script — Especificação Técnica

## Objetivo

Script interativo que provisiona um home server de forma reproduzível. O usuário responde
algumas perguntas, o script descobre informações do ambiente (IP, disco, etc.) e gera os
arquivos necessários para subir os serviços via Docker Compose.

---

## Stack de Tecnologia

### Linguagem: Python 3.11+

Python foi escolhido sobre Shell por suportar:
- Template rendering com lógica condicional (`if service == "nextcloud"`)
- UX interativa de alta qualidade (seleção múltipla, autocomplete)
- Validação de entrada, defaults inteligentes e tratamento de erros legível

### Gerenciador de dependências: `uv`

`uv` elimina a necessidade de instalar Python ou pip manualmente. Ele lê um bloco de
metadados no topo do script, baixa o Python correto se necessário, instala as dependências
em cache isolado (`~/.cache/uv`) e executa — tudo em um único comando.

Não polui o sistema: sem `venv` manual, sem `sudo pip`, sem conflito com outras versões.

### Dependências do script

| Pacote         | Uso                                              |
|----------------|--------------------------------------------------|
| `jinja2`       | Renderização dos templates (docker-compose, .env)|
| `questionary`  | Perguntas interativas com seleção múltipla       |
| `click`        | Estrutura do CLI (flags, help, subcomandos)      |
| `python-dotenv`| Leitura e escrita de arquivos `.env`             |

---

## Arquitetura de Rede e Serviços

### Serviços Obrigatórios (sempre provisionados)

| Serviço     | Função                                                        |
|-------------|---------------------------------------------------------------|
| **Traefik** | Reverse proxy + TLS automático via Let's Encrypt              |
| **AdGuard** | DNS local — resolve `*.dominio.com` para o IP interno         |
| **WireGuard**| VPN — acesso externo aos serviços como se estivesse na rede  |
| **Authentik**| SSO/IdP centralizado — autenticação unificada para todos os serviços |

### Como o acesso por nome funciona

```
Dentro da rede local (sem VPN):
  Browser → nextcloud.meudominio.com
         → AdGuard resolve para IP interno do servidor
         → Traefik roteia para o container correto
         → Certificado TLS válido (Let's Encrypt wildcard)

Fora da rede (com WireGuard):
  Phone → WireGuard VPN → rede interna
       → mesmo fluxo acima
```

O domínio real é necessário para emissão de certificados TLS válidos via ACME/Let's Encrypt.
AdGuard sobrescreve a resolução DNS para `*.dominio.com` apontando para o IP interno,
garantindo que o tráfego nunca saia da rede local.

### Autenticação com Authentik

Authentik provê SSO (Single Sign-On) via OAuth2/OIDC e LDAP.
Todos os serviços opcionais são configurados para autenticar via Authentik.
Traefik usa o ForwardAuth do Authentik como middleware para proteger serviços que não
suportam SSO nativamente.

---

## Serviços Opcionais (selecionáveis no setup)

| Serviço       | Descrição                                                          |
|---------------|--------------------------------------------------------------------|
| **Jellyfin**  | Media server. Inclui a stack *arr completa (ver abaixo)            |
| **Nextcloud** | Storage pessoal, calendário, contatos, colaboração de documentos   |
| **Immich**    | Backup e galeria de fotos/vídeos (alternativa ao Google Photos)    |

### Stack *arr (incluída com Jellyfin)

Quando Jellyfin é selecionado, toda a stack de automação de mídia é provisionada:

| Serviço         | Função                                              |
|-----------------|-----------------------------------------------------|
| **Radarr**      | Gerenciamento e download automático de filmes       |
| **Sonarr**      | Gerenciamento e download automático de séries       |
| **Prowlarr**    | Indexador centralizado para Radarr e Sonarr         |
| **qBittorrent** | Cliente de download (com interface web)             |
| **Bazarr**      | Download automático de legendas                     |

---

## Estrutura de Pastas do Projeto

```
homeserver/
├── setup.py                        # Entry point executável
├── CONTEXT.md                      # Este arquivo — especificação técnica
├── config/
│   └── services.yml                # Definição de todos os serviços disponíveis
├── templates/
│   ├── docker-compose.yml.j2       # Template principal
│   ├── .env.j2                     # Variáveis de ambiente
│   └── services/                   # Fragmentos por serviço
│       ├── traefik.j2
│       ├── adguard.j2
│       ├── wireguard.j2
│       ├── authentik.j2
│       ├── jellyfin.j2
│       ├── arr-stack.j2
│       ├── nextcloud.j2
│       └── immich.j2
├── scripts/
│   └── checks.py                   # Funções de descoberta do ambiente
├── docs/
│   ├── post-setup.md               # Instruções pós-instalação
│   └── authentik-setup.md          # Configuração inicial do Authentik
└── output/                         # Arquivos gerados (gitignored)
    ├── docker-compose.yml
    ├── .env
    └── traefik/
        └── traefik.yml
```

---

## Cabeçalho do Script (uv inline metadata — PEP 723)

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jinja2",
#   "questionary",
#   "click",
#   "python-dotenv",
# ]
# ///
```

O `uv` detecta este bloco, instala as dependências automaticamente e executa o script.
Não requer `pip install`, `venv`, ou Python pré-instalado além do `uv`.

---

## Fluxo de Perguntas (UX do Setup)

```
? Qual é o domínio principal do servidor? › meudominio.com

? Qual o provedor DNS do seu domínio? (necessário para certificado wildcard)
  › Cloudflare
    Route53
    Outro (manual)

? Qual disco/caminho usar para volumes persistentes? › /mnt/storage

? Quais serviços opcionais deseja ativar?
  ◉ Jellyfin + Stack *arr (Radarr, Sonarr, Prowlarr, qBittorrent, Bazarr)
  ◉ Nextcloud
  ◯ Immich

✔ IP local detectado: 192.168.1.100
✔ Espaço disponível em /mnt/storage: 3.6TB
✔ Docker instalado: 26.1.4
✔ Docker Compose: 2.27.0

Gerando arquivos...
✔ output/docker-compose.yml
✔ output/.env
✔ output/traefik/traefik.yml

Pronto!
Próximos passos:
  1. Configure o DNS wildcard: docs/post-setup.md
  2. Execute: docker compose -f output/docker-compose.yml up -d
  3. Configure o Authentik: https://auth.meudominio.com
```

---

## Comando de Uso

### Primeira vez em uma máquina nova

```bash
# 1. Instalar uv (uma única vez por máquina)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clonar o repositório
git clone git@github.com:usuario/homeserver
cd homeserver

# 3. Executar o setup
chmod +x setup.py
./setup.py

# 4. Subir os serviços
docker compose -f output/docker-compose.yml up -d
```

### Reexecutar / atualizar configuração

```bash
./setup.py           # Sobrescreve os arquivos em output/
docker compose -f output/docker-compose.yml up -d --force-recreate
```

---

## Regras e Decisões de Design

- **Templates usam Jinja2**: suporte a condicionais, loops e inclusão de fragmentos por serviço.
- **Nenhum arquivo gerado é commitado**: `output/` está no `.gitignore`.
- **Serviços obrigatórios**: Traefik, AdGuard, WireGuard e Authentik são sempre provisionados.
- **Jellyfin implica a stack *arr completa**: se Jellyfin for selecionado, todos os serviços de automação de mídia são incluídos.
- **Authentik protege todos os serviços**: via ForwardAuth no Traefik ou integração nativa OAuth2/OIDC.
- **O script é idempotente**: pode ser re-executado sem efeitos colaterais.
- **Certificado wildcard**: Traefik usa challenge DNS-01 para emitir `*.dominio.com`, eliminando a necessidade de expor a porta 80 externamente.
- **Tráfego sempre interno**: AdGuard resolve o domínio para o IP local; o tráfego nunca sai da rede mesmo usando um domínio público.
- **Sem dependência de sistema além do `uv`**: o script não assume `pip`, `python3` no PATH, ou virtualenv ativo.

---

## Padrão de Inicialização de Containers

Todo container no projeto segue um padrão unificado de inicialização para permitir customização automática (post-setup) sem sidecars ou dependências externas.

### Estrutura

```
custom-entrypoint.sh
  └── post-setup.sh (montado via volume ou embutido)
        └── exec "$@" (chama o entrypoint original do container)
```

### Fluxo de Execução

1. **`custom-entrypoint.sh`** é definido como `entrypoint` do container no docker-compose.
2. Ao iniciar, executa **`post-setup.sh`**, que contém toda lógica de customização necessária:
   - Comandos no banco de dados
   - Geração de configs iniciais
   - Acesso a volumes montados especificamente para isso
   - Qualquer outra configuração pré-inicialização
3. Ao final, `post-setup.sh` chama **`exec "$@"`**, que delega para o entrypoint original do container (passado como `command` ou herdado da imagem).

### Regras

- **Sem sidecars**: toda customização acontece dentro do próprio container.
- **Sem Docker socket**: o container não precisa controlar o Docker host.
- **Volume de scripts**: scripts de post-setup são montados via volume `ro` ou embutidos na imagem.
- **Idempotência**: `post-setup.sh` deve ser seguro para re-execução (ex: verificar se já foi rodado, usar flags, ou ser naturalmente idempotente).
- **Fallback**: se `post-setup.sh` falhar, o container não deve iniciar (fail-fast).

### Exemplo no docker-compose

```yaml
servico:
  image: imagem:tag
  entrypoint: ["/custom-entrypoint.sh"]
  command: ["comando", "original", "do", "container"]
  volumes:
    - ../scripts/servico/post-setup.sh:/post-setup.sh:ro
    - ../scripts/servico/custom-entrypoint.sh:/custom-entrypoint.sh:ro
```

### Exemplo de `custom-entrypoint.sh`

```bash
#!/bin/sh
set -e

echo "Running post-setup for service..."
/post-setup.sh

echo "Starting original process..."
exec "$@"
```

### Exemplo de `post-setup.sh`

```bash
#!/bin/sh
set -e

# Exemplo: rodar comandos no banco via CLI do serviço
if [ ! -f /data/.post-setup-done ]; then
  echo "Initial setup..."
  # comandos de setup
  touch /data/.post-setup-done
fi
```


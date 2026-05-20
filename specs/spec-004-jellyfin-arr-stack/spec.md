# Spec-004 — Jellyfin + Stack *arr Completa

> **Status:** draft
> **Backlog:** —
> **Criado em:** 2026-05-04

---

## 1. Visão Geral

Implementar a stack completa de media server com automação de downloads, organização automática de mídia, **configuração inicial automatizada durante a subida dos containers** e integração com Authentik. Atualmente existem templates básicos (`jellyfin.j2`, `arr-stack.j2`) mas com problemas: imagens com tag `latest`, volumes inconsistentes, serviços faltando (Lidarr, Jellyseerr, Unpackerr), qBittorrent ausente do DNS AdGuard e das notas pós-build, e bootstrap Authentik incompleto para os serviços *arr.

A stack deve funcionar como um ecossistema integrado: Jellyseerr recebe requisições de mídia → Radarr/Sonarr/Lidarr gerenciam downloads → qBittorrent baixa → Unpackerr extrai → serviços *arr organizam em `/media/` → Jellyfin serve o conteúdo → Bazarr baixa legendas.

**Configuração inicial automatizada:** todos os serviços *arr devem subir já configurados e conectados entre si — indexadores no Prowlarr, API keys cruzadas, trackers no qBittorrent e integração Jellyfin↔Jellyseerr. O `setup.py` coleta os valores necessários e o bootstrap aplica as configurações durante a primeira subida dos containers.

---

## 2. Critérios de Aceite

- [ ] **CA-01:** `./setup.py --dry-run` com Jellyfin habilitado gera `docker-compose.yml` com todos os serviços (jellyfin, radarr, sonarr, lidarr, prowlarr, qbittorrent, bazarr, jellyseerr, unpackerr) sem erros de template
- [ ] **CA-02:** Todas as imagens Docker usam tags específicas e versionadas, nunca `latest`
- [ ] **CA-02a:** `setup.py` valida que cada tag de imagem existe no registry antes de gerar os arquivos — falha com erro claro se a tag não existir
- [ ] **CA-03:** Volumes de mídia são consistentes entre Jellyfin e serviços *arr — todos apontam para os mesmos caminhos em `{{ storage_path }}/media/`
- [ ] **CA-04:** qBittorrent aparece nos DNS rewrites do AdGuard (`qbit.{{ domain }}`) e nas notas pós-build do setup
- [ ] **CA-05:** O fluxo de download → organização funciona: qBittorrent baixa em `{{ storage_path }}/downloads`, serviços *arr movem arquivos organizados para `{{ storage_path }}/media/{movies,shows,music}`, Jellyfin lê de `{{ storage_path }}/media/`
- [ ] **CA-06:** Unpackerr monitora `{{ storage_path }}/downloads` e extrai arquivos compactados automaticamente para que os serviços *arr possam mover os arquivos descompactados
- [ ] **CA-07:** Jellyseerr está acessível via `jellyseerr.{{ domain }}` com middleware Authentik e integrado ao Jellyfin via variáveis de ambiente
- [ ] **CA-08:** Lidarr gerencia música com subdomínio `lidarr.{{ domain }}`, middleware Authentik, volumes para `{{ storage_path }}/media/music` e `{{ storage_path }}/downloads`
- [ ] **CA-09:** Bootstrap Authentik cria aplicações/proxies automaticamente para todos os serviços *arr (radarr, sonarr, lidarr, prowlarr, bazarr, qbittorrent, jellyseerr)
- [ ] **CA-10:** Re-executar `./setup.py` é idempotente — secrets e configs existentes são preservados
- [ ] **CA-11:** Todos os serviços *arr e Jellyseerr possuem labels Traefik com TLS e middleware Authentik
- [ ] **CA-12:** `config/services.yml` reflete todos os serviços incluídos na stack quando Jellyfin é selecionado
- [ ] **CA-13:** Prowlarr sobe com todos os indexadores do `trackers.txt` (~320 trackers) pré-configurados como indexadores públicos
- [ ] **CA-14:** Radarr, Sonarr e Lidarr conectam ao Prowlarr automaticamente via API key gerada pelo bootstrap
- [ ] **CA-15:** qBittorrent sobe com lista de trackers do `trackers.txt` pré-injetada na configuração
- [ ] **CA-16:** Jellyseerr conecta ao Jellyfin automaticamente — API key do Jellyfin gerada e configurada pelo bootstrap
- [ ] **CA-17:** Bazarr conecta a Radarr e Sonarr automaticamente via API keys
- [ ] **CA-18:** Unpackerr recebe API keys de Radarr, Sonarr e Lidarr via variáveis de ambiente geradas pelo bootstrap

---

## 3. Fora de Escopo

- Integração SABnzbd/Usenet — apenas qBittorrent (torrent) nesta spec
- Gluetun/VPN para downloads — será tratado em spec separada
- Tdarr (transcodificação automática) — será tratado em spec separada
- Huntarr, Readarr, Mylar — não incluídos nesta fase
- Configuração do plugin OIDC do Jellyfin — documentado em `docs/authentik-setup.md`, feito manualmente

---

## 4. Dependências

- **Depende de:** spec-002 (Cloudflare DDNS) e spec-003 (WireGuard Multi-Device) — já concluídas
- **Depende de:** Bootstrap Authentik existente (`scripts/authentik_bootstrap.py`) — precisa ser estendido para incluir configuração de todos os serviços *arr
- **Depende de:** `trackers.txt` na raiz do projeto — lista de ~320 trackers para Prowlarr e qBittorrent
- **Premissas assumidas:**
  - Traefik já configurado com TLS e middleware Authentik
  - AdGuard Home resolve `*.{{ domain }}` para IP interno
  - `{{ storage_path }}` é configurável via `config/services.yml` ou prompt interativo
  - PUID=1000/PGID=1000 funcionam no host do usuário
  - Serviços *arr expõem APIs HTTP acessíveis internamente na rede Docker

---

## 5. Notas Técnicas

### 5.1 Serviços a adicionar

| Serviço | Imagem (tag a pinar) | Subdomínio | Porta interna |
|---------|---------------------|------------|---------------|
| Lidarr | `lscr.io/linuxserver/lidarr` | `lidarr` | 8686 |
| Jellyseerr | `fallenbagel/jellyseerr` | `jellyseerr` | 5055 |
| Unpackerr | `golift/unpackerr` | — (sem UI web) | — |

### 5.2 Imagens a fixar (remover `latest`)

| Serviço | Tag atual | Tag alvo |
|---------|-----------|----------|
| jellyfin | `latest` | `10.10.5` (última stable) |
| prowlarr | `latest` | `2.0.5` |
| radarr | `latest` | `5.21.1` |
| sonarr | `latest` | `4.0.15` |
| bazarr | `latest` | `1.5.2` |
| qbittorrent | `latest` | `5.0.4` |

### 5.2a Validação de tags Docker

Antes de gerar os arquivos, `setup.py` deve validar que cada tag de imagem existe no Docker Hub (ou registry correspondente):

- Usar Docker Registry HTTP API V2 (`GET /v2/{namespace}/{repo}/tags/list`) ou `docker manifest inspect {imagem}:{tag}` para verificar existência
- Se alguma tag não existir, abortar com erro claro: `"Imagem {imagem}:{tag} não encontrada — verifique a tag em config/services.yml"`
- Validação deve ocorrer antes de gerar qualquer arquivo (fail-fast)
- Imagens linuxserver.io e outras devem ser validadas nos seus respectivos registries
- `--dry-run` também executa a validação de tags
- Se o usuário estiver offline, pular validação com warning

### 5.3 Estrutura de volumes

```
{{ storage_path }}/
├── jellyfin/config/
├── media/
│   ├── movies/     ← Radarr deposita aqui, Jellyfin lê, Bazarr lê
│   ├── shows/      ← Sonarr deposita aqui, Jellyfin lê, Bazarr lê
│   └── music/      ← Lidarr deposita aqui, Jellyfin lê
├── downloads/      ← qBittorrent baixa aqui, Unpackerr extrai aqui
├── prowlarr/config/
├── radarr/config/
├── sonarr/config/
├── lidarr/config/
├── bazarr/config/
├── qbittorrent/config/
├── jellyseerr/config/
└── unpackerr/config/
```

### 5.4 Unpackerr

- Não tem interface web — roda como daemon
- Monitora `{{ storage_path }}/downloads` por arquivos `.rar`, `.zip`, `.7z`
- Extrai no local e move para o diretório correto do serviço *arr
- Precisa de API keys de Radarr, Sonarr e Lidarr para notificar quando extração completa
- Deve estar na rede `internal` apenas (não exposto)

### 5.5 Jellyseerr

- Usa variáveis de ambiente para integração com Jellyfin (`JELLYFIN_HOST`, `JELLYFIN_API_KEY`)
- `JELLYFIN_API_KEY` é gerada automaticamente pelo bootstrap via API local do Jellyfin
- Precisa de banco de dados SQLite em volume persistente
- Integrado com Authentik via ForwardAuth

### 5.6 Bootstrap (Authentik + Configuração de Serviços)

- Estender `scripts/authentik_bootstrap.py` (ou criar script dedicado) para:
  1. Criar Proxy Providers + Proxy Outposts + Applications para: radarr, sonarr, lidarr, prowlarr, bazarr, qbittorrent, jellyseerr
  2. Gerar e distribuir API keys entre todos os serviços *arr
  3. Configurar indexadores do Prowlarr via API usando `trackers.txt`
  4. Configurar download clients (qBittorrent) em Radarr/Sonarr/Lidarr
  5. Gerar API key do Jellyfin e configurar no Jellyseerr
  6. Salvar todas as keys em `output/.env` para idempotência
- Usar mesmo padrão já existente para traefik e adguard
- Bootstrap deve aguardar healthchecks antes de configurar cada serviço

### 5.7 services.yml

Atualizar `config/services.yml` para incluir os novos serviços no `includes` e `subdomains` do Jellyfin:

```yaml
includes:
  - radarr
  - sonarr
  - lidarr
  - prowlarr
  - qbittorrent
  - bazarr
  - jellyseerr
  - unpackerr
subdomains:
  - { subdomain: radarr, name: Radarr }
  - { subdomain: sonarr, name: Sonarr }
  - { subdomain: lidarr, name: Lidarr }
  - { subdomain: prowlarr, name: Prowlarr }
  - { subdomain: qbit, name: qBittorrent }
  - { subdomain: bazarr, name: Bazarr }
  - { subdomain: jellyseerr, name: Jellyseerr }
```

### 5.8 Configuração inicial automatizada

A configuração dos serviços deve ocorrer durante a primeira subida dos containers, sem necessidade de intervenção manual via UI.

**setup.py — novos prompts (quando Jellyfin selecionado):**
- Nenhum prompt adicional necessário — trackers vêm do `trackers.txt`, API keys são geradas automaticamente

**Bootstrap estendido (`scripts/authentik_bootstrap.py` ou novo script):**
1. Aguardar cada serviço *arr ficar saudável (healthcheck)
2. Gerar API keys para: Prowlarr, Radarr, Sonarr, Lidarr, Bazarr
3. Configurar Prowlarr: injetar todos os trackers do `trackers.txt` como indexadores públicos via API
4. Configurar Radarr/Sonarr/Lidarr: registrar Prowlarr como index manager via API key
5. Configurar Radarr/Sonarr/Lidarr: registrar qBittorrent como download client
6. Configurar Bazarr: conectar a Radarr e Sonarr via API keys
7. Configurar Unpackerr: API keys injetadas via variáveis de ambiente no docker-compose
8. Gerar API key do Jellyfin via API local e configurar no Jellyseerr (`JELLYFIN_API_KEY`)
9. Salvar todas as API keys em `output/.env` para idempotência em re-runs

**Arquivo `trackers.txt`:**
- Localizado na raiz do projeto
- ~320 linhas com URLs de trackers (udp://, http://, https://)
- Linhas vazias devem ser ignoradas
- Usado como fonte para indexadores do Prowlarr e lista de trackers do qBittorrent

**Idempotência:**
- Se `output/.env` já contém API keys da stack *arr, re-executar `setup.py` não reconfigura serviços
- Configuração só roda na primeira subida ou quando flags de reset são usadas

---

## 7. Bugfixes

- [fix-002-post-setup-command](../fix-002-post-setup-command/spec.md) — Comando YAML inválido no post-setup.j2 — 2026-05-06

---

## 6. Checklist de Aprovação da Spec

- [ ] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [ ] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [ ] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [ ] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [ ] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [ ] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [ ] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes

# Plan — Spec-004 — Jellyfin + Stack *arr Completa

> **Status:** draft
> **Spec:** [spec.md](./spec.md)
> **Criado em:** 2026-05-06

---

## Visão Geral

Expandir a stack Jellyfin existente adicionando os serviços ausentes (Lidarr, Jellyseerr, Unpackerr), corrigir tags de imagens para versões stable verificadas no Docker Hub, estender o bootstrap Authentik para todos os serviços *arr e automatizar a configuração cruzada entre serviços via API. A abordagem reutiliza o padrão existente de templates Jinja2 + `setup.py` + `scripts/authentik_bootstrap.py`, estendendo cada camada incrementalmente.

**Tags verificadas no Docker Hub (2026-05-06):**

| Serviço | Imagem | Tag stable confirmada |
|---|---|---|
| jellyfin | `linuxserver/jellyfin` | `10.11.8` |
| radarr | `linuxserver/radarr` | `6.1.1` |
| sonarr | `linuxserver/sonarr` | `4.0.17` |
| lidarr | `linuxserver/lidarr` | `3.1.0` |
| prowlarr | `linuxserver/prowlarr` | `2.3.5` |
| bazarr | `linuxserver/bazarr` | `1.5.6` |
| qbittorrent | `linuxserver/qbittorrent` | `5.1.4` |
| jellyseerr | `fallenbagel/jellyseerr` | `develop` (sem stable) |
| unpackerr | `golift/unpackerr` | `0.15.2` |

---

## Etapas de Implementação

### Etapa 1 — Atualizar `config/services.yml` com serviços completos do Jellyfin

- **Objetivo:** Adicionar Lidarr, Jellyseerr e Unpackerr ao `includes` e subdomínios correspondentes no bloco Jellyfin do `config/services.yml`
- **Arquivos afetados:** `config/services.yml`
- **Resultado esperado:** `config/services.yml` contém todos os 9 serviços (radarr, sonarr, lidarr, prowlarr, qbittorrent, bazarr, jellyseerr, unpackerr) no `includes` do Jellyfin e subdomínios para os 7 serviços com UI web
- **Notas:** qBittorrent usa subdomínio `qbit`, Unpackerr não tem subdomínio (sem UI web). Tags hardcoded conforme tabela acima.

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Criar/atualizar templates Jinja2 dos novos serviços

- **Objetivo:** Criar `templates/services/lidarr.j2`, `templates/services/jellyseerr.j2`, `templates/services/unpackerr.j2` e atualizar `templates/services/arr-stack.j2` para incluir todos os serviços com tags versionadas
- **Arquivos afetados:** `templates/services/lidarr.j2`, `templates/services/jellyseerr.j2`, `templates/services/unpackerr.j2`, `templates/services/arr-stack.j2`, `templates/docker-compose.yml.j2`
- **Resultado esperado:** Todos os 9 serviços definidos em templates com: imagens com tags específicas (não `latest`), volumes consistentes apontando para `{{ storage_path }}/media/` e `{{ storage_path }}/downloads`, labels Traefik com TLS e middleware Authentik para serviços com UI, redes corretas (`proxy` ou `internal`)
- **Notas:** Unpackerr fica apenas na rede `internal` (sem UI). Jellyseerr usa tag `develop` (única disponível).

- [x] Implementado
- [x] Validado

---

### Etapa 3 — Adicionar diretórios de dados no `setup.py`

- **Objetivo:** Criar diretórios de dados para Lidarr, Jellyseerr e Unpackerr em `create_data_directories()` e garantir estrutura completa de volumes
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:** `create_data_directories()` cria: `lidarr/config/`, `jellyseerr/config/`, `unpackerr/config/`, além de `media/{movies,shows,music}`, `downloads/` e diretórios existentes
- **Notas:** Seguir padrão existente de `chmod 777` onde aplicável

- [x] Implementado
- [x] Validado

---

### Etapa 4 — Criar container de post-setup para bootstrap automatizado

- **Objetivo:** Criar um container dedicado `post-setup` no docker-compose que roda automaticamente quando a stack sobe, executando todo o bootstrap (Authentik + configuração cruzada dos serviços *arr)
- **Arquivos afetados:** `templates/services/post-setup.j2`, `templates/docker-compose.yml.j2`, `scripts/post_setup.py`
- **Resultado esperado:** Container `post-setup` definido no compose com `restart: "no"`, `depends_on` com healthchecks de todos os serviços alvo, e monta `scripts/post_setup.py` + `output/.env` como volumes. Sobe automaticamente com `docker compose up -d`, aguarda os serviços ficarem saudáveis, executa toda a configuração e finaliza
- **Notas:** `restart: "no"` garante que o container não re-executa após completar. Idempotência: se API keys já existem em `output/.env`, pula configuração dos serviços (só cria apps Authentik se não existirem). Container usa imagem Python slim com `requests` disponível

- [x] Implementado
- [x] Validado

---

### Etapa 5 — Implementar script `post_setup.py` (Authentik + configuração cruzada)

- **Objetivo:** Criar `scripts/post_setup.py` que executa em sequência: (1) cria Proxy Providers/Outposts/Applications no Authentik para radarr, sonarr, lidarr, prowlarr, bazarr, qbittorrent, jellyseerr; (2) gera API keys para todos os serviços *arr; (3) configura Prowlarr com trackers do `trackers.txt`; (4) conecta Radarr/Sonarr/Lidarr ao Prowlarr e qBittorrent; (5) conecta Bazarr a Radarr/Sonarr; (6) gera API key do Jellyfin e configura no Jellyseerr; (7) salva tudo em `output/.env`
- **Arquivos afetados:** `scripts/post_setup.py`
- **Resultado esperado:** Script aguarda healthcheck de cada serviço antes de configurar; gera API keys via APIs locais; lê `trackers.txt` (~320 trackers) e injeta no Prowlarr; conecta todos os serviços entre si; salva keys em `output/.env` para idempotência em re-runs; log claro do progresso e erros
- **Notas:** Reutilizar padrão do `scripts/authentik_bootstrap.py` existente para a parte Authentik. Variáveis de ambiente do container vêm do `.env` gerado pelo `setup.py` (AUTHENTIK_URL, AUTHENTIK_TOKEN, URLs dos serviços, etc.)

- [x] Implementado
- [x] Validado

---

### Etapa 6 — Adicionar qBittorrent ao DNS AdGuard e notas pós-build

- **Objetivo:** Incluir `qbit.{{ domain }}` nos DNS rewrites do AdGuard e adicionar entrada nas notas pós-build do `setup.py`
- **Arquivos afetados:** `templates/services/adguard.j2` (ou template equivalente), `setup.py` (seção de notas pós-build)
- **Resultado esperado:** `qbit.{{ domain }}` resolve para IP interno no AdGuard; notas pós-build mencionam qBittorrent com URL de acesso
- **Notas:** Seguir padrão existente de DNS rewrites do AdGuard

- [x] Implementado
- [x] Validado

---

### Etapa 7 — Testar com `--dry-run` e validar geração completa

- **Objetivo:** Executar `./setup.py --dry-run` com Jellyfin habilitado e verificar que todos os serviços são gerados sem erros
- **Arquivos afetados:** Nenhum (apenas validação)
- **Resultado esperado:** `docker-compose.yml` gerado contém todos os 9 serviços; nenhum erro de template; volumes consistentes entre serviços
- **Notas:** Validar manualmente a saída do `--dry-run` contra todos os 18 critérios de aceite

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: docker-compose com todos os 9 serviços | Etapa 2, 7 |
| CA-02: Tags específicas, nunca `latest` | Etapa 1, 2 |
| CA-02a: Validação de tags no registry | Verificada manualmente (tabela acima) |
| CA-03: Volumes de mídia consistentes | Etapa 2, 3 |
| CA-04: qBittorrent no DNS AdGuard e notas | Etapa 6 |
| CA-05: Fluxo download → organização funcional | Etapa 2, 5 |
| CA-06: Unpackerr monitora e extrai downloads | Etapa 2, 5 |
| CA-07: Jellyseerr com TLS + Authentik + integração Jellyfin | Etapa 2, 5 |
| CA-08: Lidarr com subdomínio, Authentik, volumes | Etapa 2 |
| CA-09: Bootstrap Authentik para todos os serviços *arr | Etapa 4, 5 |
| CA-10: Idempotência do setup.py | Etapa 4, 5 |
| CA-11: Labels Traefik com TLS + Authentik em todos os serviços | Etapa 2 |
| CA-12: services.yml reflete todos os serviços | Etapa 1 |
| CA-13: Prowlarr com ~320 trackers pré-configurados | Etapa 5 |
| CA-14: Radarr/Sonarr/Lidarr conectados ao Prowlarr | Etapa 5 |
| CA-15: qBittorrent com trackers pré-injetados | Etapa 5 |
| CA-16: Jellyseerr conectado ao Jellyfin | Etapa 5 |
| CA-17: Bazarr conectado a Radarr e Sonarr | Etapa 5 |
| CA-18: Unpackerr com API keys via variáveis de ambiente | Etapa 2, 5 |

---

## Checklist de Aprovação do Plan

- [ ] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [ ] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [ ] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [ ] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [ ] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [ ] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [ ] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes

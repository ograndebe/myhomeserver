# Plan — Spec-007 — Container Post-Setup Pattern

> **Status:** done
> **Atualizado em:** 2026-05-21
> **Spec:** [spec.md](./spec.md)
> **Criado em:** 2026-05-20

---

## Visão Geral

Migrar a lógica de inicialização dos containers sidecar `bootstrap` e `post-setup` para dentro dos próprios containers alvo, usando o padrão `custom-entrypoint.sh` → `post-setup.sh` → `exec "$@"`. Cada serviço afetado recebe scripts próprios montados como volumes, eliminando a necessidade de Docker socket e `docker exec` cruzado. A abordagem preserva a lógica existente de configuração, apenas mudando onde é executada.

---

## Etapas de Implementação

### Etapa 1 — Criar estrutura de diretórios e templates genéricos

- **Objetivo:** Criar `scripts/<servico>/` para cada serviço afetado com `custom-entrypoint.sh` genérico e `post-setup.sh` esqueleto
- **Arquivos afetados:**
  - `scripts/authentik-server/custom-entrypoint.sh`
  - `scripts/authentik-server/post-setup.sh`
  - `scripts/prowlarr/custom-entrypoint.sh`
  - `scripts/prowlarr/post-setup.sh`
  - `scripts/qbittorrent/custom-entrypoint.sh`
  - `scripts/qbittorrent/post-setup.sh`
  - `scripts/radarr/custom-entrypoint.sh`
  - `scripts/radarr/post-setup.sh`
  - `scripts/sonarr/custom-entrypoint.sh`
  - `scripts/sonarr/post-setup.sh`
  - `scripts/lidarr/custom-entrypoint.sh`
  - `scripts/lidarr/post-setup.sh`
  - `scripts/bazarr/custom-entrypoint.sh`
  - `scripts/bazarr/post-setup.sh`
- **Resultado esperado:** Todos os 14 arquivos existem com permissão de execução; `custom-entrypoint.sh` segue o template genérico `post-setup.sh` → `exec "$@"`
- **Notas:** `custom-entrypoint.sh` é idêntico para todos os serviços, variando apenas o echo. `post-setup.sh` começa como esqueleto idempotente (exit 0) e será preenchido nas etapas seguintes.

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Implementar post-setup do authentik-server

- **Objetivo:** Migrar toda a lógica do container `bootstrap` para `scripts/authentik-server/post-setup.sh`, executando `ak shell` internamente
- **Arquivos afetados:**
  - `scripts/authentik-server/post-setup.sh` (preencher com lógica)
  - `templates/services/authentik.j2` (adicionar volumes de scripts + entrypoint)
- **Resultado esperado:** Script cria token, providers, apps e outpost via `ak shell` dentro do próprio container; idempotente com `get_or_create_*`
- **Notas:** O script deve aguardar PostgreSQL e Redis estarem prontos (polling healthcheck). Usa variáveis de ambiente do `.env` para credenciais.

- [x] Implementado
- [x] Validado

---

### Etapa 3 — Implementar post-setup do prowlarr

- **Objetivo:** Migrar injeção de trackers do `post_setup.py` para `scripts/prowlarr/post-setup.sh`
- **Arquivos afetados:**
  - `scripts/prowlarr/post-setup.sh` (preencher com lógica)
  - `templates/services/prowlarr.j2` (adicionar volumes de scripts + entrypoint)
- **Resultado esperado:** Script lê `trackers.txt` e injeta via API REST do Prowlarr; verifica existência antes de adicionar (idempotente)
- **Notas:** Usa `curl` para chamadas API. Aguarda Prowlarr estar disponível via polling HTTP.

- [x] Implementado
- [x] Validado

---

### Etapa 4 — Implementar post-setup do qbittorrent

- **Objetivo:** Migrar injeção de trackers para `scripts/qbittorrent/post-setup.sh`
- **Arquivos afetados:**
  - `scripts/qbittorrent/post-setup.sh` (preencher com lógica)
  - `templates/services/qbittorrent.j2` (adicionar volumes de scripts + entrypoint)
- **Resultado esperado:** Script injeta trackers via API do qBittorrent; verifica existência antes de injetar (idempotente)
- **Notas:** Usa `curl` para chamadas API. Aguarda qBittorrent estar disponível via polling HTTP.

- [x] Implementado
- [x] Validado

---

### Etapa 5 — Implementar post-setup do radarr, sonarr e lidarr

- **Objetivo:** Migrar configuração de conexão com qBittorrent e Prowlarr para scripts individuais
- **Arquivos afetados:**
  - `scripts/radarr/post-setup.sh` (preencher com lógica)
  - `scripts/sonarr/post-setup.sh` (preencher com lógica)
  - `scripts/lidarr/post-setup.sh` (preencher com lógica)
  - `templates/services/radarr.j2` (adicionar volumes + entrypoint)
  - `templates/services/sonarr.j2` (adicionar volumes + entrypoint)
  - `templates/services/lidarr.j2` (adicionar volumes + entrypoint)
- **Resultado esperado:** Cada script conecta qBittorrent (download client) e Prowlarr (indexer) via API REST; verifica existência antes de criar (idempotente)
- **Notas:** Cada script faz polling HTTP aguardando Prowlarr e qBittorrent estarem disponíveis antes de configurar.

- [x] Implementado
- [x] Validado

---

### Etapa 6 — Implementar post-setup do bazarr

- **Objetivo:** Migrar configuração de conexão com Radarr e Sonarr para `scripts/bazarr/post-setup.sh`
- **Arquivos afetados:**
  - `scripts/bazarr/post-setup.sh` (preencher com lógica)
  - `templates/services/bazarr.j2` (adicionar volumes + entrypoint)
- **Resultado esperado:** Script conecta Bazarr a Radarr e Sonarr via API REST; verifica settings antes de atualizar (idempotente)
- **Notas:** Aguarda Radarr e Sonarr estarem disponíveis via polling HTTP.

- [x] Implementado
- [x] Validado

---

### Etapa 7 — Atualizar templates docker-compose e remover containers sidecar

- **Objetivo:** Remover `bootstrap` e `post-setup` do `docker-compose.yml.j2`, adicionar entrypoint/volumes nos serviços afetados
- **Arquivos afetados:**
  - `templates/docker-compose.yml.j2` (remover bootstrap, remover post-setup, atualizar serviços com entrypoint+volumes)
  - `templates/services/authentik.j2`
  - `templates/services/prowlarr.j2`
  - `templates/services/qbittorrent.j2`
  - `templates/services/radarr.j2`
  - `templates/services/sonarr.j2`
  - `templates/services/lidarr.j2`
  - `templates/services/bazarr.j2`
- **Resultado esperado:** Zero referência a `bootstrap` ou `post-setup` no template gerado; todos os serviços afetados têm `entrypoint: ["/custom-entrypoint.sh"]` e volumes dos scripts
- **Notas:** Os volumes montam os scripts como `:ro`. O entrypoint sobrescreve o padrão da imagem.

- [x] Implementado
- [x] Validado

---

### Etapa 8 — Remover arquivos obsoletos

- **Objetivo:** Deletar `bootstrap/`, `scripts/post_setup.py` e qualquer referência residual
- **Arquivos afetados:**
  - `bootstrap/` (diretório inteiro — deletar)
  - `scripts/post_setup.py` (deletar)
- **Resultado esperado:** Diretório `bootstrap/` não existe mais; `scripts/post_setup.py` não existe mais; nenhuma referência a eles no código
- **Notas:** Verificar com `grep` que não sobrou referência em nenhum template ou script.

- [x] Implementado
- [x] Validado

---

### Etapa 9 — Validação final com dry-run

- **Objetivo:** Executar `./setup.py --dry-run` e validar saída sem erros
- **Arquivos afetados:** Nenhum (apenas validação)
- **Resultado esperado:** `./setup.py --dry-run` executa sem erros; output/docker-compose.yml gerado não contém `bootstrap` ou `post-setup` containers
- **Notas:** Inspecionar visualmente o `output/docker-compose.yml` gerado para confirmar CA-01, CA-02, CA-08, CA-09.

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: Container `bootstrap` removido | Etapa 7, 8 |
| CA-02: Container `post-setup` removido | Etapa 7, 8 |
| CA-03: `authentik-server` executa bootstrap próprio | Etapa 2, 7 |
| CA-04: `prowlarr` injeta trackers via post-setup próprio | Etapa 3, 7 |
| CA-05: `radarr`, `sonarr`, `lidarr` conectam qBittorrent + Prowlarr | Etapa 5, 7 |
| CA-06: `bazarr` conecta Radarr + Sonarr | Etapa 6, 7 |
| CA-07: `qbittorrent` injeta trackers via post-setup próprio | Etapa 4, 7 |
| CA-08: Nenhum container usa Docker socket | Etapa 7, 8, 9 |
| CA-09: Nenhum container usa `docker exec` contra outro | Etapa 7, 8, 9 |
| CA-10: Todos os post-setup.sh são idempotentes | Etapa 1–6 |
| CA-11: `./setup.py --dry-run` funciona sem erros | Etapa 9 |
| CA-12: Diretório `bootstrap/` removido | Etapa 8 |

---

## Checklist de Aprovação do Plan

- [ ] Todos os critérios de aceite da spec estão cobertos por pelo menos uma etapa
- [ ] Nenhuma etapa viola premissas do `context.md`
- [ ] Templates seguem convenções Jinja2 (`trim_blocks=True`, `lstrip_blocks=True`)
- [ ] Serviços usam `restart: unless-stopped` e tags específicas (não `latest`)
- [ ] Scripts são idempotentes e usam polling para dependências
- [ ] Nenhuma referência a Docker socket ou `docker exec` cruzado permanece
- [ ] `./setup.py --dry-run` valida sem erros

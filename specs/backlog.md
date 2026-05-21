# Backlog — Homeserver

> Última atualização: 2026-05-20

---

## Pendente

- [ ] **BACK-007** Fix: Jellyfin falha com `group_add: render` inexistente no host
  - Descrição: Grupo `render` não existe no servidor, causando erro "Unable to find group render: no matching entries in group file". Remover `group_add` ou condicionar à existência do grupo.
  - Spec: —
  - Prioridade: alta

- [ ] **BACK-008** Fix: Unpackerr — diretório `/downloads` não existe no host
  - Descrição: Unpackerr reporta erro `stat /mnt/data/myhomeserver/downloads: no such file or directory`. Criar diretório no `create_data_directories()` ou ajustar volume.
  - Spec: —
  - Prioridade: média

- [ ] **BACK-009** Fix: Jellyseerr healthcheck falhando com servidor funcional
  - Descrição: Healthcheck `curl -sf http://localhost:5055/api/v1/status` marca container como unhealthy mesmo com servidor rodando. Aumentar `start_period` ou ajustar endpoint.
  - Spec: —
  - Prioridade: baixa

- [ ] **BACK-010** Fix: qBittorrent healthcheck falhando com WebUI funcional
  - Descrição: Healthcheck `curl -sf http://localhost:8080/api/v2/app/version` marca container como unhealthy mesmo com WebUI respondendo. Aumentar `start_period` ou ajustar endpoint.
  - Spec: —
  - Prioridade: baixa

---

## Em Progresso

- [~] **BACK-004** Jellyfin + Stack *arr Completa
  - Spec: [spec-004](spec-004-jellyfin-arr-stack/spec.md)
  - Nota: Containers subiram mas com bugs (BACK-007, BACK-009, BACK-010)

---

## Concluído

- [x] **BACK-001** WireGuard + DuckDNS
  - Concluído em: 2026-04-30
  - Spec: [spec-001](spec-001-wireguard-duckdns/spec.md)
- [x] **BACK-002** Substituir DuckDNS por Cloudflare DDNS
  - Concluído em: 2026-05-01
  - Spec: [spec-002](spec-002-cloudflare-ddns/spec.md)
- [x] **BACK-003** WireGuard Multi-Device Peer Setup
  - Concluído em: 2026-05-02
  - Spec: [spec-003](spec-003-wireguard-multi-device/spec.md)
- [x] **BACK-005** Gestão de Permissões de Diretórios no Host
  - Concluído em: 2026-05-06
  - Spec: [spec-005](spec-005-gestao-permissoes-host/spec.md)
  - Plan: [plan-005](spec-005-gestao-permissoes-host/plan.md)
- [x] **BACK-006** Fix: AdGuard Home crash — YAML `bind_hosts` → `bind_host` + permissões do arquivo
  - Concluído em: 2026-05-07
  - Fix: [fix-003](fix-003-adguard-crash/spec.md)
- [x] **BACK-011** Modo Não Interativo — `setup.py` lê tudo do `.env` sem perguntas
  - Concluído em: 2026-05-07
  - Spec: [spec-006](spec-006-modo-nao-interativo/spec.md)
  - Plan: [plan-006](spec-006-modo-nao-interativo/plan.md)
- [x] **BACK-012** Refatorar containers para adotar padrão de post-setup interno
  - Concluído em: 2026-05-21
  - Spec: [spec-007](spec-007-container-post-setup-pattern/spec.md)
  - Plan: [plan-007](spec-007-container-post-setup-pattern/plan.md)

---

## Legenda

- `[ ]` — Pendente
- `[~]` — Em progresso
- `[x]` — Concluído

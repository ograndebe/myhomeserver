# Plan — Fix-003 — AdGuard Home crash: YAML bind_hosts e permissões

> **Status:** done
> **Spec:** [spec.md](./spec.md)
> **Spec original:** Feature base (AdGuard Home — serviço obrigatório)
> **Backlog:** [BACK-006](../backlog.md)
> **Criado em:** 2026-05-07
> **Atualizado em:** 2026-05-07

---

## Visão Geral

O AdGuard Home falha ao iniciar por dois bugs: (1) o template usa `bind_hosts` (sequência) ao invés de `bind_host` (string), causando erro de parse YAML; (2) o arquivo gerado herda permissões restritivas do umask, impedindo leitura pelo container. A correção é pontual: ajustar o template e garantir permissões `644` no arquivo gerado.

---

## Etapas de Correção

### Etapa 1 — Corrigir chave YAML no template AdGuardHome.yaml.j2

- **Objetivo:** Trocar `bind_hosts:\n  - 0.0.0.0` por `bind_host: "0.0.0.0"` no template
- **Arquivos afetados:** `templates/adguard/AdGuardHome.yaml.j2`
- **Resultado esperado:** Template gera YAML válido com `bind_host` como string
- **Notas:** A chave correta é `bind_host` (singular, string) conforme documentação oficial do AdGuard Home

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Garantir permissões legíveis no arquivo gerado

- **Objetivo:** Aplicar `chmod(0o644)` no arquivo `AdGuardHome.yaml` após `write_text()` no `setup.py`
- **Arquivos afetados:** `setup.py` (função `render_templates()`)
- **Resultado esperado:** Arquivo gerado sempre com permissão `644`, independente do umask
- **Notas:** Adicionar `output_path.chmod(0o644)` logo após `write_text()` apenas para o AdGuardHome.yaml (ou para todos os arquivos gerados, se fizer sentido)

- [x] Implementado
- [x] Validado

---

### Etapa 3 — Validar com `--dry-run`

- **Objetivo:** Executar `./setup.py --dry-run` e verificar que o YAML renderizado está correto
- **Arquivos afetados:** Nenhum (validação apenas)
- **Resultado esperado:** Output mostra `bind_host: "0.0.0.0"` como string e sem erros de renderização
- **Notas:** Inspecionar visualmente o YAML gerado

- [x] Implementado
- [x] Validado

---

### Etapa 4 — Atualizar backlog.md

- **Objetivo:** Marcar BACK-006 como concluído no backlog
- **Arquivos afetados:** `specs/backlog.md`
- **Resultado esperado:** BACK-006 aparece na seção "Concluído" com link para o fix
- **Notas:** Adicionar link para `fix-003-adguard-crash/spec.md`

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: bind_host como string | Etapa 1 |
| CA-02: Permissões 644 no arquivo | Etapa 2 |
| CA-03: --dry-run exibe YAML correto | Etapa 3 |
| CA-04: Idempotência | Etapa 2 |

---

## Checklist de Aprovação do Plan

- [ ] Todos os critérios de aceite do fix estão cobertos por pelo menos uma etapa
- [ ] A correção não viola premissas do context.md
- [ ] O risco de regressão foi considerado e mitigado
- [ ] As etapas são atômicas e podem ser validadas individualmente
- [ ] O plano é executável sem dependências externas pendentes

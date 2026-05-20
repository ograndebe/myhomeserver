# Plan — Fix-002 — Comando YAML Inválido no post-setup.j2

> **Status:** done
> **Spec:** [spec.md](./spec.md)
> **Spec original:** [spec-004-jellyfin-arr-stack](../spec-004-jellyfin-arr-stack/spec.md)
> **Criado em:** 2026-05-06
> **Atualizado em:** 2026-05-06

---

## Visão Geral

O template `post-setup.j2` usa YAML folded style (`>`) para o `command`. Com `trim_blocks=True` no Jinja2, o comentário da primeira linha do próximo template (`static-page.j2`) é concatenado na linha do comando, gerando YAML inválido. A correção substitui o folded style por uma lista YAML explícita.

---

## Etapas de Correção

### Etapa 1 — Corrigir o command no post-setup.j2

- **Objetivo:** Substituir `command: >` por lista YAML explícita para evitar concatenação com templates seguintes
- **Arquivos afetados:** `templates/services/post-setup.j2`
- **Resultado esperado:** `docker-compose.yml` gerado tem `command` como lista YAML válida, sem conteúdo de outros templates
- **Notas:** Usar formato `command: ["sh", "-c", "..."]` que é imune a problemas de whitespace do Jinja2

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Validar com --dry-run

- **Objetivo:** Executar `./setup.py --dry-run` com Jellyfin habilitado e verificar que o YAML gerado é válido
- **Arquivos afetados:** nenhum (apenas validação)
- **Resultado esperado:** `output/docker-compose.yml` tem o `command` do `post-setup` como lista YAML limpa, sem comentários concatenados
- **Notas:** Validar também com `docker compose config` se disponível

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: command é string YAML válida | Etapa 1, Etapa 2 |
| CA-02: docker compose parseia sem erros | Etapa 2 |
| CA-03: nenhuma outra seção afetada | Etapa 1, Etapa 2 |

---

## Checklist de Aprovação do Plan

- [ ] Todos os critérios de aceite do fix estão cobertos por pelo menos uma etapa
- [ ] A correção não viola premissas do context.md
- [ ] O risco de regressão foi considerado (baixo — mudança isolada)

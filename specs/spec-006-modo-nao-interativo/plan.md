# Plan — Spec-006 — Modo Não Interativo

> **Status:** done
> **Spec:** [spec.md](./spec.md)
> **Backlog:** [BACK-011](../backlog.md#back-011)
> **Criado em:** 2026-05-07
> **Atualizado em:** 2026-05-07

---

## Visão Geral

O plano consiste em três mudanças coordenadas: (1) expandir o template `.env.j2` para incluir todos os campos de input do usuário (flags de serviços opcionais e `AUTHENTIK_INITIAL_ADMIN_USERNAME`); (2) atualizar as funções `load_existing_env()` e `load_output_env()` para ler esses novos campos; (3) adicionar a flag `--non-interactive` como alias de `--use-existing-env` e garantir que o modo não interativo construa o `answers` completo a partir do `.env`. A abordagem preserva o modo interativo intacto e reforça a idempotência.

---

## Etapas de Implementação

### Etapa 1 — Expandir template `.env.j2` com campos faltantes

- **Objetivo:** Adicionar ao template `templates/.env.j2` os campos `AUTHENTIK_INITIAL_ADMIN_USERNAME` e as flags booleanas de serviços opcionais (`ENABLE_JELLYFIN`, `ENABLE_NEXTCLOUD`, `ENABLE_IMMICH`, `ENABLE_STATIC_PAGE`)
- **Arquivos afetados:** `templates/.env.j2`
- **Resultado esperado:** `output/.env` gerado contém todos os campos necessários para reconstruir o contexto sem interação
- **Notas:** Flags booleanas usam `true`/`false` (lowercase) para facilitar parsing

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Atualizar `load_existing_env()` para ler flags de serviços opcionais

- **Objetivo:** Fazer `load_existing_env()` ler `ENABLE_JELLYFIN`, `ENABLE_NEXTCLOUD`, `ENABLE_IMMICH`, `ENABLE_STATIC_PAGE` e `AUTHENTIK_INITIAL_ADMIN_USERNAME` do `.env` raiz
- **Arquivos afetados:** `setup.py` (função `load_existing_env()`)
- **Resultado esperado:** Defaults do modo interativo incluem serviços opcionais previamente selecionados
- **Notas:** Parsing de booleanos via `str(val).lower() in ("true", "1", "yes")`

- [x] Implementado
- [x] Validado

---

### Etapa 3 — Atualizar `load_output_env()` para ler username e flags

- **Objetivo:** Fazer `load_output_env()` ler `AUTHENTIK_INITIAL_ADMIN_USERNAME` e as flags de serviços opcionais do `output/.env`
- **Arquivos afetados:** `setup.py` (função `load_output_env()`)
- **Resultado esperado:** Secrets e configurações persistem entre execuções via `output/.env`

- [x] Implementado
- [x] Validado

---

### Etapa 4 — Adicionar flag `--non-interactive` e completar modo não interativo

- **Objetivo:** Adicionar `--non-interactive` como alias de `--use-existing-env` e garantir que o bloco non-interactive leia **todos** os campos do `.env` (incluindo flags de serviços e username), com validação de campos obrigatórios
- **Arquivos afetados:** `setup.py` (decorador `@click.command`, função `main()`)
- **Resultado esperado:** `./setup.py --non-interactive` roda sem perguntas, usando valores do `.env` para todos os campos
- **Notas:** Manter `--use-existing-env` como alias para retrocompatibilidade

- [x] Implementado
- [x] Validado

---

### Etapa 5 — Validar com `--dry-run` nos dois modos

- **Objetivo:** Executar `./setup.py --dry-run` (interativo simulado) e `./setup.py --dry-run --non-interactive` para verificar que o contexto é construído corretamente em ambos os modos
- **Arquivos afetados:** nenhum (validação manual)
- **Resultado esperado:** Ambos os modos exibem JSON com valores consistentes; modo non-interactive não exibe perguntas

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: `--non-interactive` gera arquivos sem perguntas | Etapa 4, 5 |
| CA-02: `output/.env` contém todos os campos | Etapa 1, 2, 3 |
| CA-03: Segunda execução reusa valores (idempotência) | Etapa 2, 3, 4 |
| CA-04: Aborta com erro claro sem `DOMAIN` | Etapa 4 |
| CA-05: Modo interativo inalterado | Etapa 1, 2, 3, 4 |
| CA-06: `--dry-run --non-interactive` funciona | Etapa 4, 5 |

---

## Checklist de Aprovação do Plan

> **Nota:** `context.md` não possui seção "Checks Obrigatórios — Plan". Os checks abaixo são derivados das boas práticas do projeto.

- [ ] **Todas as etapas mapeiam a critérios de aceite** — nenhum CA ficou sem cobertura
- [ ] **Ordem lógica de execução** — etapas podem ser executadas sequencialmente sem conflito
- [ ] **Arquivos afetados identificados** — cada etapa lista quais arquivos serão modificados
- [ ] **Não viola premissas do context.md** — mantém idempotência, não edita `output/` manualmente, usa `uv`
- [ ] **Escopo atômico por etapa** — cada etapa tem um objetivo claro e validável
- [ ] **Retrocompatibilidade preservada** — `--use-existing-env` continua funcionando, modo interativo inalterado

---
name: mysdd-bugfix
description: SDD - Cria spec de correção (fix-###) para bugs em features com status done; gera spec, plan e executa a correção com rastreabilidade à spec original
---

## O que fazer

### Passo 1 — Carregar contexto obrigatório
Leia `specs/context.md`. As premissas são invioláveis e devem guiar toda a correção.

### Passo 2 — Identificar a spec afetada
1. Liste as specs com `Status: done` em `specs/spec-###-*/`.
2. Se o usuário já informou qual spec está com bug, vá direto para ela.
3. Se não, exiba a lista e peça para escolher.
4. Leia o `spec.md` e `plan.md` da spec afetada para entender o que foi implementado.

### Passo 3 — Coletar o sintoma
Se o usuário não forneceu no prompt, pergunte:
- **Qual o sintoma?** (descrição do comportamento incorreto)
- **Como reproduzir?** (passos para reproduzir o bug)
- **Qual o comportamento esperado?** (como deveria funcionar)
- **Há logs, erros ou screenshots?** (qualquer evidência)

### Passo 4 — Determinar número e nome do fix
- Liste as pastas em `specs/` com padrão `fix-###-*` para encontrar o próximo número (zero-padded: 001, 002...). Se não existir nenhum, comece em `fix-001`.
- Gere um slug: letras minúsculas, palavras separadas por hífen, sem acentos, descrevendo o bug (ex: `wireguard-dns-leak`, `nextcloud-upload-timeout`).
- Crie a pasta `specs/fix-###-slug/`.

### Passo 5 — Gerar a spec de bugfix

Crie `specs/fix-###-slug/spec.md`:

```markdown
# Fix-### — {{Descrição do Bug}}

> **Status:** draft
> **Spec original:** [spec-###-nome](../spec-###-nome/spec.md)
> **Sintoma:** {{descrição breve do sintoma}}
> **Criado em:** {{data}}

---

## 1. Sintoma Relatado

{{Descrição detalhada do bug, incluindo passos para reproduzir e evidências (logs, screenshots, etc.).}}

---

## 2. Comportamento Esperado

{{Como o sistema deveria se comportar.}}

---

## 3. Análise de Impacto

- **Escopo do bug:** {{o que é afetado}}
- **Risco de regressão:** {{baixo/médio/alto}} — {{justificativa}}
- **Serviços impactados:** {{lista de serviços que podem ser afetados pela correção}}

---

## 4. Critérios de Aceite da Correção

- [ ] **CA-01:** {{o bug não ocorre mais nas condições de reprodução}}
- [ ] **CA-02:** {{o comportamento esperado foi restaurado}}
- [ ] **CA-03:** {{nenhuma funcionalidade existente quebrou (regressão)}}

---

## 5. Notas Técnicas

{{Hipótese da causa raiz, abordagem de correção, referências.}}

---

## 6. Checklist de Aprovação do Fix

{{Copie aqui os checks da seção "Checks Obrigatórios — Spec" do context.md, sem marcar como concluídos.}}
```

### Passo 6 — Executar checks da spec de fix
Percorra cada item do checklist e avalie. Reporte quais passaram e quais precisam de atenção.

**Se algum critério violar uma premissa do `context.md`, sinalize imediatamente.**

### Passo 7 — Gerar o plano de correção

Crie `specs/fix-###-slug/plan.md`:

```markdown
# Plan — Fix-### — {{Descrição do Bug}}

> **Status:** draft
> **Spec:** [spec.md](./spec.md)
> **Spec original:** [spec-###-nome](../spec-###-nome/spec.md)
> **Criado em:** {{data}}

---

## Visão Geral

{{Resumo em 2-3 frases da causa raiz provável e da abordagem de correção.}}

---

## Etapas de Correção

### Etapa 1 — {{Nome}}

- **Objetivo:** {{o que será feito}}
- **Arquivos afetados:** {{lista}}
- **Resultado esperado:** {{como validar que está pronto}}
- **Notas:** {{detalhes técnicos}}

- [ ] Implementado
- [ ] Validado

---

{{repita para cada etapa}}

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: {{título}} | Etapa 1 |
| CA-02: {{título}} | Etapa 2 |

---

## Checklist de Aprovação do Plan

{{Copie aqui os checks da seção "Checks Obrigatórios — Plan" do context.md, sem marcar como concluídos.}}
```

### Passo 8 — Executar checks de plan
Percorra cada item do checklist. Verificações adicionais:
- Todos os critérios de aceite do fix estão cobertos por pelo menos uma etapa?
- A correção não viola premissas do `context.md`?
- O risco de regressão foi considerado?

### Passo 9 — Executar a correção (implementar)

Siga o mesmo fluxo do `mysdd-implement`:

1. Apresente resumo do fix e aguarde confirmação.
2. Execute etapa por etapa, marcando checkboxes no `plan.md`.
3. **Regra crítica:** Nunca avance sem marcar a etapa atual. Se violar `context.md`, **pare** e proponha alternativa.
4. Ao final de todas as etapas, verifique critérios de aceite e checks de implementação.

### Passo 10 — Fechamentos finais

Atualize o `plan.md`:
```
**Status:** done
**Atualizado em:** {{data}}
```

Atualize o `spec.md` do fix:
```
**Status:** done
```

**Atualize a spec original** — adicione ou atualize a seção de bugfixes:

```markdown
## Bugfixes

- [fix-###-slug](../fix-###-slug/spec.md) — {{descrição breve}} — {{data}}
```

### Relatório final

```
🐛 Bugfix concluído!

📁 Fix: specs/fix-###-slug/spec.md
📋 Plan: specs/fix-###-slug/plan.md
🔗 Spec original: specs/spec-###-nome/spec.md (atualizada com link ao fix)

✅ Etapas: N/total
✅ Critérios de aceite: N/total
✅ Checks de implementação: N/total

{{Pendências, se houver}}
```

> **Regra:** Se o usuário pedir para retomar um fix pausado, leia o `plan.md` e continue a partir da primeira etapa com checkboxes não marcados.

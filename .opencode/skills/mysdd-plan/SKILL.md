---
name: mysdd-plan
description: SDD - Cria um plano de implementação para uma spec existente em specs/spec-###-nome/plan.md com etapas, checkboxes e rastreabilidade
---

## O que fazer

### Passo 1 — Carregar contexto obrigatório
Leia `specs/context.md`. Premissas, stack e convenções devem guiar todas as decisões do plano.

### Passo 2 — Identificar a spec alvo

**Se o usuário informou a spec:** use diretamente.

**Se não informou:**
1. Liste as pastas `specs/spec-###-*/` que contenham `spec.md`
2. Para cada uma, exiba: número, nome e status
3. Peça ao usuário para escolher

Após identificar, leia o `spec.md` completo.

### Passo 3 — Verificar pré-condições
- A spec tem critérios de aceite definidos? (necessário para planejar)
- O checklist de aprovação da spec foi satisfeito? Se não, avise e pergunte se deseja prosseguir assim mesmo.

### Passo 4 — Gerar o arquivo

Crie `specs/spec-###-nome/plan.md`:

```markdown
# Plan — Spec-### — {{Nome}}

> **Status:** draft
> **Spec:** [spec.md](./spec.md)
> **Criado em:** {{data}}

---

## Visão Geral

{{Resumo em 2-3 frases da abordagem técnica e por que foi escolhida.}}

---

## Etapas de Implementação

### Etapa 1 — {{Nome}}

- **Objetivo:** {{o que será feito}}
- **Arquivos afetados:** {{lista}}
- **Resultado esperado:** {{como validar que está pronto}}
- **Notas:** {{detalhes técnicos relevantes}}

- [ ] Implementado
- [ ] Validado

---

### Etapa 2 — {{Nome}}

- **Objetivo:** {{...}}
- **Arquivos afetados:** {{...}}
- **Resultado esperado:** {{...}}

- [ ] Implementado
- [ ] Validado

---

{{repita para cada etapa}}

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: {{título}} | Etapa 1 |
| CA-02: {{título}} | Etapa 2, 3 |

---

## Checklist de Aprovação do Plan

{{Copie aqui os checks da seção "Checks Obrigatórios — Plan" do context.md, sem marcar como concluídos.}}
```

### Passo 5 — Executar checks de plan
Percorra cada item do checklist e avalie o plano. Reporte quais passaram e quais precisam de atenção.

Verificações adicionais obrigatórias:
- Todos os critérios de aceite da spec estão cobertos por pelo menos uma etapa?
- Alguma etapa viola premissas do `context.md`?

Informe o caminho do arquivo criado e o total de etapas ao final.

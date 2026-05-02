---
name: mysdd-triage
description: SDD - Triagem inicial de sintomas/bugs; classifica o problema e recomenda o caminho correto (bugfix, reabrir spec, ou nova feature)
---

## O que fazer

### Passo 1 — Carregar contexto
Leia `specs/context.md` se existir. As premissas ajudam a classificar se o relato é de fato um bug ou uma mudança de requisito.

### Passo 2 — Coletar o sintoma
Pergunte ao usuário (ou extraia do prompt):
- **Qual o sintoma observado?** (o que está acontecendo de errado)
- **Qual o comportamento esperado?** (como deveria funcionar)
- **A qual feature/spec se refere?** (se souber)
- **Quando começou?** (após update, após nova spec, sempre existiu?)

### Passo 3 — Analisar o estado atual
1. Leia `specs/backlog.md` se existir.
2. Liste todas as specs em `specs/spec-###-*/` e `specs/fix-###-*/`.
3. Para cada spec, verifique o status (`draft` ou `done`).
4. Identifique qual spec (se alguma) está relacionada ao sintoma.

### Passo 4 — Classificar e recomendar

Aplique esta lógica de classificação:

| Cenário | Classificação | Caminho recomendado |
|---|---|---|
| Sintoma em spec com `Status: done` | **Bug** | `mysdd-bugfix` |
| Sintoma em spec com `Status: draft` | **Spec incompleta** | `mysdd-implement` (retomar) |
| Sintoma em spec `done` mas o "bug" é na verdade uma mudança de requisito | **Mudança de escopo** | `mysdd-backlog` → `mysdd-spec` (nova feature) |
| Sintoma sem spec associada (algo novo) | **Nova demanda** | `mysdd-backlog` → `mysdd-spec` |
| Sintoma já coberto por um `fix-###` existente | **Bug já registrado** | `mysdd-implement` (retomar fix existente) |

### Passo 5 — Apresentar diagnóstico

```
🔍 Triagem concluída

Sintoma: {{descrição breve}}
Classificação: {{bug / spec incompleta / mudança de escopo / nova demanda}}
Spec afetada: {{spec-###-nome ou nenhuma}}
Status atual: {{done / draft / inexistente}}

→ Caminho recomendado: {{mysdd-bugfix / mysdd-implement / mysdd-backlog + mysdd-spec}}
```

### Passo 6 — Executar o caminho recomendado

Pergunte ao usuário se deseja prosseguir com o caminho recomendado:
- Se sim: invoque a skill correspondente (ou guie o usuário a invocá-la)
- Se não: encerre a triagem

> **Regra:** Se o sintoma descreve um comportamento perigoso (perda de dados, exposição de secrets, crash), sinalize como **crítico** e recomende ação imediata via `mysdd-bugfix`.

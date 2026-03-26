---
name: mysdd-backlog
description: SDD - Cria ou atualiza specs/backlog.md com features e fases do projeto; gerencia IDs, status e links para specs
---

## O que fazer

### Passo 1 — Carregar contexto
Leia `specs/context.md` se existir. As premissas devem guiar quais itens fazem sentido.

### Passo 2 — Ler backlog existente
Se `specs/backlog.md` existir, leia para não duplicar itens e entender o estado atual.

### Passo 3 — Coletar novos itens
Se o usuário não listou os itens no prompt, pergunte:
- Quais features, melhorias ou fases deseja adicionar?
- Alguma ordem de prioridade ou dependência entre os itens?

### Passo 4 — Gerar ou atualizar o arquivo

**Regras:**
- IDs seguem o formato `BACK-001`, `BACK-002`, em ordem crescente. Nunca reutilize um ID.
- Nunca remova itens já marcados como `[x]` (done).
- Não reordene itens existentes além do necessário.
- Se algum item violar premissas do `context.md`, avise antes de adicionar.

**Estrutura do arquivo:**

```markdown
# Backlog

> Última atualização: {{data}}

---

## 🔲 Pendente

- [ ] **BACK-001** {{título}}
  - Descrição: {{descrição breve}}
  - Spec: —
  - Prioridade: alta/média/baixa

---

## 🔄 Em Progresso

- [~] **BACK-XXX** {{título}}
  - Spec: [spec-###-nome](specs/spec-###-nome/spec.md)

---

## ✅ Concluído

- [x] **BACK-XXX** {{título}}
  - Concluído em: {{data}}
  - Spec: [spec-###-nome](specs/spec-###-nome/spec.md)
```

Após criar/atualizar, exiba um resumo dos itens adicionados ou alterados.

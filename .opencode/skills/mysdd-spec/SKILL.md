---
name: mysdd-spec
description: SDD - Cria uma especificação detalhada em specs/spec-###-nome-feature/spec.md com critérios de aceite, escopo e checks obrigatórios
---

## O que fazer

### Passo 1 — Carregar contexto obrigatório
Leia `specs/context.md`. As premissas são invioláveis e devem guiar toda a spec.

### Passo 2 — Identificar item de backlog (opcional)
Se o usuário mencionou um `BACK-XXX`, leia `specs/backlog.md` para entender o contexto. Se não mencionou, pergunte se esta spec está relacionada a algum item do backlog.

### Passo 3 — Coletar informações
Se o usuário não forneceu um prompt detalhado, pergunte:
- **O que deve ser feito?** (descrição em 1-2 frases)
- **Critérios de aceite**: Como saberemos que está pronto? (cenários verificáveis)
- **Fora de escopo**: O que explicitamente NÃO faz parte desta spec?
- **Dependências**: Depende de outra spec, sistema externo ou decisão pendente?

Se o usuário forneceu um prompt rico, extraia essas informações sem fazer perguntas redundantes.

### Passo 4 — Determinar número e nome da spec
- Liste as pastas em `specs/` com padrão `spec-###-*` para encontrar o próximo número (zero-padded: 001, 002...).
- Gere um slug: letras minúsculas, palavras separadas por hífen, sem acentos.
- Crie a pasta `specs/spec-###-nome-feature/`.

### Passo 5 — Gerar o arquivo

```markdown
# Spec-### — {{Nome da Feature}}

> **Status:** draft
> **Backlog:** {{BACK-XXX ou —}}
> **Criado em:** {{data}}

---

## 1. Visão Geral

{{Descrição clara do que deve ser feito e por quê.}}

---

## 2. Critérios de Aceite

- [ ] **CA-01:** {{comportamento esperado}}
- [ ] **CA-02:** {{comportamento esperado}}
- [ ] **CA-03:** {{cenário de erro ou edge case}}

---

## 3. Fora de Escopo

- {{item}}

---

## 4. Dependências

- **Depende de:** {{spec, sistema ou decisão — ou "nenhuma"}}
- **Premissas assumidas:** {{lista}}

---

## 5. Notas Técnicas

{{Decisões técnicas relevantes, referências, diagramas.}}

---

## 6. Checklist de Aprovação da Spec

{{Copie aqui os checks da seção "Checks Obrigatórios — Spec" do context.md, sem marcar como concluídos.}}
```

### Passo 6 — Executar checks de spec
Percorra cada item do checklist (seção 6) e avalie se a spec os satisfaz. Reporte quais passaram e quais precisam de atenção.

**Se algum critério violar uma premissa do `context.md`, sinalize imediatamente.**

Após criar, pergunte se deseja atualizar o item de backlog relacionado para `[~]` (em progresso). Informe o caminho completo do arquivo criado.

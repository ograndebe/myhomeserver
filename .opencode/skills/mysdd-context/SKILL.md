---
name: mysdd-context
description: SDD - Cria ou atualiza specs/context.md com premissas invioláveis, stack, convenções e checks obrigatórios para spec, plan e implement
---

## O que fazer

1. Se `specs/context.md` já existir, leia o conteúdo atual e pergunte o que o usuário deseja alterar em cada seção antes de reescrever.

2. Se não existir, entreviste o usuário sobre:
   - **Premissas gerais**: regras de negócio, restrições técnicas ou decisões arquiteturais que nunca podem ser quebradas
   - **Stack e convenções**: tecnologias, frameworks, padrões de código, estrutura de pastas
   - **Checks de Spec**: o que verificar ao final de cada spec
   - **Checks de Plan**: o que verificar ao final de cada plano
   - **Checks de Implement**: o que verificar ao final de cada implementação

3. Crie o arquivo `specs/context.md` com esta estrutura:

```markdown
# Project Context

> Arquivo central de premissas. Consultado em TODOS os comandos mysdd.
> Última atualização: {{data}}

---

## 1. Premissas e Regras Invioláveis

> NUNCA podem ser quebradas em nenhuma fase.

- {{premissa}}

---

## 2. Stack e Convenções

- {{item}}

---

## 3. Checks Obrigatórios — Spec

- [ ] Todos os critérios de aceite são verificáveis e binários
- [ ] Casos de erro e edge cases foram considerados
- [ ] A spec não viola nenhuma premissa do context.md
- [ ] Escopo claro e sem ambiguidades
{{checks adicionais definidos pelo usuário}}

---

## 4. Checks Obrigatórios — Plan

- [ ] Cada etapa tem escopo claro e resultado esperado
- [ ] Dependências entre etapas estão mapeadas
- [ ] Nenhuma breaking change não planejada
- [ ] O plano cobre todos os critérios de aceite da spec
{{checks adicionais definidos pelo usuário}}

---

## 5. Checks Obrigatórios — Implement

- [ ] Todos os checkboxes do plano foram concluídos
- [ ] Nenhuma premissa do context.md foi violada
- [ ] Sem TODOs críticos pendentes no código
- [ ] Implementação satisfaz os critérios de aceite da spec
{{checks adicionais definidos pelo usuário}}
```

Após criar, confirme com o usuário e informe que este arquivo será consultado automaticamente por todos os outros comandos mysdd.

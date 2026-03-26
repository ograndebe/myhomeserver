---
name: mysdd-implement
description: SDD - Executa o plano de implementação etapa a etapa, marca checkboxes no plan.md e ao final pergunta se deve fechar plan, spec e backlog
---

## O que fazer

### Passo 1 — Carregar contexto obrigatório
Leia `specs/context.md`. Todas as premissas devem ser respeitadas durante toda a implementação.

### Passo 2 — Identificar o plano alvo

**Se o usuário informou a spec/plan:** use diretamente.

**Se não informou:**
1. Liste pastas `specs/spec-###-*/` que contenham `plan.md`
2. Para cada plan, exiba: número, nome, status e quantas etapas estão pendentes
3. Peça ao usuário para escolher

Leia os arquivos `plan.md` e `spec.md` da spec escolhida.

### Passo 3 — Apresentar resumo antes de começar

```
📋 Plano: spec-### — {{nome}}
📍 Etapas pendentes: N de {{total}}
🎯 Critérios de aceite: {{lista resumida}}

Posso iniciar a implementação?
```

Aguarde confirmação.

### Passo 4 — Implementar etapa por etapa

Para cada etapa **ainda não marcada como concluída**:

1. Anuncie: "▶️ Iniciando Etapa N — {{nome}}"
2. Execute as alterações nos arquivos conforme descrito na etapa
3. Verifique se o resultado esperado foi atingido
4. **Atualize os checkboxes no `plan.md`:**
   ```
   - [x] Implementado
   - [x] Validado
   ```
5. Reporte: "✅ Etapa N concluída — {{resultado breve}}"
6. Pergunte se deve continuar ou pausar

> **Regra crítica:** Nunca avance para a próxima etapa sem marcar a atual no `plan.md`. Se uma decisão violar uma premissa do `context.md`, **pare**, sinalize e proponha alternativa antes de continuar.

### Passo 5 — Verificar critérios de aceite

```
✅ CA-01: {{descrição}} — satisfeito por {{como}}
✅ CA-02: {{descrição}} — satisfeito por {{como}}
⚠️ CA-03: {{descrição}} — ATENÇÃO: {{problema}}
```

### Passo 6 — Executar checks de implementação

Percorra os **Checks Obrigatórios — Implement** do `context.md`:

```
✅ {{check 1}} — ok
❌ {{check 2}} — {{o que falta}}
```

Se algum check falhar, liste o que precisa ser corrigido e pergunte ao usuário como proceder.

### Passo 7 — Fechamentos finais

Atualize o `plan.md`:
```
**Status:** done
**Atualizado em:** {{data}}
```

Depois pergunte separadamente:

**1.** Deseja marcar o item de backlog **{{BACK-XXX}}** como concluído no `specs/backlog.md`?
- Se sim: mova para "✅ Concluído", adicione data e links para spec e plan.

**2.** Deseja atualizar o status da spec para `done`?
- Se sim: atualize o campo `**Status:**` no `spec.md`.

### Relatório final

```
🎉 Implementação concluída!

📁 Spec: specs/spec-###-nome/spec.md
📋 Plan: specs/spec-###-nome/plan.md
📌 Backlog: BACK-XXX marcado como done / não alterado

✅ Etapas: N/total
✅ Critérios de aceite: N/total
✅ Checks de implementação: N/total

{{Pendências, se houver}}
```

> Se o usuário pedir para retomar uma implementação pausada, leia o `plan.md` e continue a partir da primeira etapa com checkboxes não marcados.

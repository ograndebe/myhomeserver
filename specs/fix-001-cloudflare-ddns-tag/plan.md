# Plan — Fix-001 — Tag inválida da imagem cloudflare-ddns

> **Status:** done
> **Spec:** [spec.md](./spec.md)
> **Spec original:** [spec-002-cloudflare-ddns](../spec-002-cloudflare-ddns/spec.md)
> **Criado em:** 2026-05-01
> **Atualizado em:** 2026-05-01

---

## Visão Geral

O template `docker-compose.yml.j2` referencia a tag inexistente `3.1.0` da imagem `oznu/cloudflare-ddns`. A correção consiste em trocar para `latest`, conforme indicado na nota técnica da spec-002.

---

## Etapas de Correção

### Etapa 1 — Corrigir tag da imagem no template

- **Objetivo:** Trocar `oznu/cloudflare-ddns:3.1.0` por `oznu/cloudflare-ddns:latest` no template Jinja2
- **Arquivos afetados:** `templates/docker-compose.yml.j2`
- **Resultado esperado:** O docker-compose gerado deve referenciar `oznu/cloudflare-ddns:latest`
- **Notas:** A spec-002 já indicava `latest` na nota técnica; a tag `3.1.0` foi um erro de implementação

- [x] Implementado
- [ ] Validado

### Etapa 2 — Re-executar setup.py e validar docker compose

- **Objetivo:** Regenerar o docker-compose.yml e confirmar que o pull funciona
- **Arquivos afetados:** `output/docker-compose.yml` (gerado automaticamente)
- **Resultado esperado:** `docker compose -f output/docker-compose.yml pull cloudflare-ddns` completa sem erro
- **Notas:** Usar `./setup.py` para regenerar; não editar output/ manualmente

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: Pull sem erro de manifest | Etapa 1, Etapa 2 |
| CA-02: Container inicia e permanece rodando | Etapa 2 |
| CA-03: Nenhuma regressão | Etapa 2 |

---

## Checklist de Aprovação do Plan

- [x] Todos os critérios de aceite do fix estão cobertos por pelo menos uma etapa
- [x] A correção não viola premissas do context.md
- [x] O risco de regressão foi considerado e mitigado
- [x] As etapas são atômicas e podem ser validadas individualmente

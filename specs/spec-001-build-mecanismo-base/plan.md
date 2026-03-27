# Plan — Spec-001 — Mecanismo Base de Build em Shell

> **Status:** done
> **Spec:** [spec.md](./spec.md)
> **Criado em:** 26/03/2026
> **Atualizado em:** 26/03/2026

---

## Visão Geral

Script `build.sh` em bash puro que detecta/cria `.env` e processa templates via `envsubst`. Estrutura modular com funções separadas para verificação de dependências, coleta interativa de dados, geração de `.env` e processamento de templates recursivo.

---

## Etapas de Implementação

### Etapa 1 — Estrutura base do build.sh

- **Objetivo:** Criar a estrutura inicial do script com shebang, variáveis, função de logging e parse de argumentos básicos
- **Arquivos afetados:** `build.sh`
- **Resultado esperado:** Script executável que responde a `--help` e `--version`
- **Notas:** Usar `set -euo pipefail` para Fail fast; logging com timestamps

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Verificação de dependências (envsubst)

- **Objetivo:** Verificar se `envsubst` está disponível no sistema; caso contrário, exibir instrução de instalação e sair com erro
- **Arquivos afetados:** `build.sh`
- **Resultado esperado:** Script verifica dependência ao iniciar; erro claro se ausente
- **Notas:** `which envsubst || (echo "Instale: apt-get install gettext-base" && exit 1)`

- [x] Implementado
- [x] Validado

---

### Etapa 3 — Função de coleta interativa de dados

- **Objetivo:** Solicitar ao usuário domínio, email Cloudflare e API token com validação básica (não vazio)
- **Arquivos afetados:** `build.sh`
- **Resultado esperado:** Função `collect_env_data()` retorna as 3 variáveis necessárias
- **Notas:** Usar `read -p`; adicionar validação de formato de domínio básico

- [x] Implementado
- [x] Validado

---

### Etapa 4 — Lógica de detecção/criação do .env

- **Objetivo:** Verificar se `build/.env` existe; se não, chamar coleta interativa e criar o arquivo
- **Arquivos afetados:** `build.sh`, `build/.env` (gerado)
- **Resultado esperado:** Fluxo correto: detectar existente OU criar novo com confirmação
- **Notas:** Carregar `.env` com `set -a && source` para exportar variáveis

- [x] Implementado
- [x] Validado

---

### Etapa 5 — Função de processamento de templates

- **Objetivo:** Processar todos `*.tmpl` em `templates/` recursivamente, preservando estrutura de diretórios, gerando em `build/`
- **Arquivos afetados:** `build.sh`
- **Resultado esperado:** Templates processados aparecem em `build/` com mesmo path relativo
- **Notas:** Usar `find templates/ -name "*.tmpl"` e `envsubst < "$file" > "${file/templates\/build}"`

- [x] Implementado
- [x] Validado

---

### Etapa 6 — Função principal e output final

- **Objetivo:** Integrar todas as funções na função `main()`; exibir resumo dos artefatos gerados
- **Arquivos afetados:** `build.sh`
- **Resultado esperado:** Script executa fluxo completo e lista arquivos em `build/`
- **Notas:** Adicionar mensagem de sucesso com `ls -la build/`

- [x] Implementado
- [x] Validado

---

### Etapa 7 — Validação com shellcheck

- **Objetivo:** Executar `shellcheck build.sh` e corrigir todos os warnings/errors
- **Arquivos afetados:** `build.sh`
- **Resultado esperado:** `shellcheck` passa sem errors/warnings
- **Notas:** Instalar com `apt-get install shellcheck` ou `brew install shellcheck`

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: Detecta se build/.env existe | Etapa 4 |
| CA-02: Prossegue sem input se .env existe | Etapa 4 |
| CA-03: Solicita interativamente se .env não existe | Etapa 3, 4 |
| CA-04: .env contém variáveis necessárias | Etapa 4 |
| CA-05: Cria diretório build/ se necessário | Etapa 4 |
| CA-06: Processa templates via envsubst | Etapa 2, 5 |
| CA-07: Preserva estrutura de diretórios em build/ | Etapa 5 |
| CA-08: Idempotente | Etapa 4, 5 |
| CA-09: Bash puro com envsubst | Etapa 2 |

---

## Checklist de Aprovação do Plan

- [ ] Cada etapa tem escopo claro e resultado esperado
- [ ] Dependências entre etapas estão mapeadas
- [ ] Nenhuma breaking change não planejada
- [ ] O plano cobre todos os critérios de aceite da spec
- [ ] Não inclui tarefas do "não escopo" do PROJECT.md
- [ ] Validação de sintaxe (shellcheck, yamllint) está prevista

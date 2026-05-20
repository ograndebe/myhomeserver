# Plan — Fix-001 — Permissões de Diretórios Falham Após Correção no Storage Path

> **Status:** done
> **Atualizado em:** 2026-05-06
> **Spec:** [spec.md](./spec.md)
> **Spec original:** [spec-005](../spec-005-gestao-permissoes-host/spec.md)
> **Criado em:** 2026-05-06

---

## Visão Geral

O `check_storage_permissions()` corrige apenas o diretório raiz do `storage_path`, mas `create_data_directories()` tenta `os.chown`/`chmod` em subdiretórios que já existem com ownership diferente (ex: root), gerando `Operation not permitted`. Além disso, `output/` e seus subdiretórios não passam por verificação de permissões, causando `Permission denied` na renderização de templates. A correção adiciona tratamento de exceção em `create_data_directories()`, oferece `sudo chown` recursivo quando necessário, e garante que `output/` seja gravável antes de gerar arquivos.

---

## Fora de Escopo

- Refatoração completa da arquitetura de diretórios (ex: unificar `storage_path` e `output/`)
- Adicionar testes automatizados para permissões (o projeto não possui test suite)
- Suporte a sistemas de arquivos especiais (NFS, ZFS com quotas, etc.)

---

## Dependências

- **Depende de:** spec-005 (implementação anterior de `check_storage_permissions()` e `create_data_directories()`)
- **Premissas:**
  - O usuário tem acesso a `sudo chown` ou pode corrigir manualmente
  - O ambiente de execução permite `subprocess.run(["sudo", ...])`

---

## Etapas de Correção

### Etapa 1 — Tolerar `os.chown`/`chmod` em diretórios existentes com ownership diferente

- **Objetivo:** Evitar que `create_data_directories()` quebre com `Operation not permitted` ao encontrar subdiretórios preexistentes owned por outro usuário.
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:**
  - Envolver `os.chown()` e `chmod()` em `try/except (PermissionError, OSError)`.
  - Se o diretório **já existia** e a operação falha, tentar `sudo chown` naquele caminho específico (reaproveitando a lógica de `check_storage_permissions`).
  - Se `sudo` também falhar, exibir um warning em vez de erro fatal (pois as permissões podem já ser suficientes para o container).
  - Se o diretório foi **criado agora** e a operação falha, manter como erro fatal, mas com mensagem mais descritiva.
  - Continuar processando os demais diretórios em vez de parar no primeiro erro.
- **Notas:** Preservar o comportamento de exibição "✔ dir (existente)" / "✔ dir (criado)" e adicionar "⚠ dir (permissão não ajustada)" quando o sudo não resolver.

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Garantir permissões no diretório `output/`

- **Objetivo:** Evitar `Permission denied` ao escrever arquivos em `output/adguard/` ou outros subdiretórios do `output/`.
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:**
  - Criar uma função `check_output_permissions()` similar a `check_storage_permissions()`, mas aplicada ao diretório `OUTPUT` (raiz do projeto + `/output`).
  - Chamá-la antes de `render_templates()` quando não estiver em `--dry-run`.
  - Se `OUTPUT` ou algum subdiretório (`output/traefik`, `output/adguard`) não for gravável, oferecer `sudo chown` com confirmação explícita.
  - Se o usuário recusar, abortar com mensagem clara.
- **Notas:** O diretório `output/` é local ao projeto e pode ter sido criado por outro usuário em execuções anteriores. A lógica deve ser idêntica à do `storage_path`: verificar `os.access`, oferecer `sudo`, abortar se recusado.

- [x] Implementado
- [x] Validado

---

### Etapa 3 — Preservar idempotência e segurança no `--dry-run`

- **Objetivo:** Confirmar que `--dry-run` não tenta modificar permissões nem criar diretórios.
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:**
  - `check_output_permissions()` NÃO é chamada quando `dry_run=True`.
  - A nova lógica de `try/except` dentro de `create_data_directories()` não afeta o comportamento do `--dry-run` (que já retorna antes de chamar `create_data_directories`).
  - Adicionar nota no dry-run indicando que permissões de `output/` também não foram verificadas.
- **Notas:** Apenas validação — nenhuma mudança estrutural necessária, pois o dry-run já retorna cedo.

- [x] Implementado
- [x] Validado

---

### Etapa 4 — Validação final

- **Objetivo:** Garantir que `./setup.py` executa sem erros de permissão nos cenários afetados.
- **Arquivos afetados:** Nenhum (validação manual)
- **Resultado esperado:**
  - `./setup.py --dry-run` executa sem erros e sem criar/modificar diretórios.
  - `./setup.py` em um ambiente onde `storage_path` e `output/` têm subdiretórios existentes com ownership diferente: oferece `sudo`, corrige, e completa sem erros.
  - Re-executar `./setup.py` em um ambiente já corrigido não gera warnings desnecessários.
- **Notas:** Testar simulando diretórios owned por root: `sudo mkdir -p /mnt/data/myhomeserver/traefik/acme && sudo chown root:root /mnt/data/myhomeserver/traefik/acme`.

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: `create_data_directories()` tolera diretórios existentes com ownership diferente | Etapa 1 |
| CA-02: `render_templates()` garante que `output/` é gravável | Etapa 2 |
| CA-03: Re-executar `./setup.py` é idempotente | Etapas 1, 2 |
| CA-04: `./setup.py --dry-run` não modifica permissões | Etapa 3 |

---

## Checklist de Aprovação do Plan

- [ ] Especifica o QUE, não o COMO — descreve comportamento desejado, não detalhes de implementação
- [ ] Critérios de aceite verificáveis — cada CA pode ser testado manualmente ou automaticamente
- [ ] Fora de escopo explícito — delimita claramente o que NÃO será feito
- [ ] Dependências declaradas — lista specs, sistemas ou decisões pendentes
- [ ] Alinhada com context.md — não viola nenhuma premissa inviolável
- [ ] Escopo atômico — uma feature por spec, sem misturar funcionalidades independentes
- [ ] Notas técnicas justificam decisões — explica o "porquê" de escolhas técnicas relevantes

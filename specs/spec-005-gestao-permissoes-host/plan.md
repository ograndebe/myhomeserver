# Plan — Spec-005 — Gestão de Permissões de Diretórios no Host

> **Status:** done
> **Atualizado em:** 2026-05-06
> **Spec:** [spec.md](./spec.md)
> **Criado em:** 2026-05-06

---

## Visão Geral

Adicionar verificação de permissões no `storage_path` antes de criar diretórios, com opção de correção via `sudo` mediante consentimento explícito. Refatorar `create_data_directories()` para usar permissões seguras (755/775) em vez de 777 indiscriminado, mantendo a exceção do AdGuard. Garantir idempotência e segurança no `--dry-run`.

---

## Etapas de Implementação

### Etapa 1 — Verificação de permissões no `storage_path`

- **Objetivo:** Verificar se o usuário tem permissão de escrita no `storage_path` antes de chamar `create_data_directories()`. Se não tiver, oferecer correção via `sudo chown`.
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:**
  - Nova função `check_storage_permissions(storage_path: Path) -> bool` que usa `os.access(path, os.W_OK)`
  - Se `False`, exibir prompt com `questionary.confirm()` perguntando se deseja executar `sudo chown $USER:$USER <storage_path>`
  - Se usuário confirmar: executar `subprocess.run(["sudo", "chown", f"{os.getuid()}:{os.getgid()}", str(path)])`, validar exit code
  - Se usuário recusar: `sys.exit(1)` com mensagem clara instruindo como resolver manualmente
  - Chamada inserida no `main()` entre `run_environment_checks()` e `create_data_directories()`
- **Notas:** `sudo` só executa com confirmação explícita — nunca silenciosamente. Capturar stderr do `sudo` e exibir em caso de falha.

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Refatorar `create_data_directories()` com permissões seguras

- **Objetivo:** Criar diretórios com permissões 755 (padrão) ou 775 (quando grupo precisa write), mantendo AdGuard em 777 como exceção justificada.
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:**
  - Após `mkdir(parents=True, exist_ok=True)`, aplicar `chmod(0o755)` em todos os diretórios
  - AdGuard mantém `chmod(0o777)` (exceção explícita com comentário justificando)
  - Ownership dos diretórios alinhado ao usuário que executou `setup.py` (já é o comportamento padrão do `mkdir`, mas adicionar `chown` explícito se PUID/PGID != uid/gid atual)
- **Notas:** PUID/PGID ainda não é configurável via `services.yml` — nesta etapa, usar `os.getuid()`/`os.getgid()` do usuário atual como referência. Se no futuro PUID/PGID for customizável, o `chown` já estará preparado.

- [x] Implementado
- [x] Validado

---

### Etapa 3 — Idempotência nas permissões

- **Objetivo:** Garantir que re-executar `setup.py` não quebre permissões de diretórios existentes.
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:**
  - Antes de aplicar `chmod`, verificar se as permissões atuais já são as esperadas — só alterar se diferente
  - Antes de aplicar `chown`, verificar ownership atual — só alterar se diferente
  - Mensagem no console indica "✔ dir (existente)" vs "✔ dir (criado)" para clareza
- **Notas:** Usar `path.stat().st_mode & 0o777` para comparar permissões atuais com as esperadas. Usar `path.stat().st_uid` e `path.stat().st_gid` para comparar ownership.

- [x] Implementado
- [x] Validado

---

### Etapa 4 — Garantir segurança no `--dry-run`

- **Objetivo:** Confirmar que `./setup.py --dry-run` não tenta modificar permissões nem criar diretórios.
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:**
  - O `--dry-run` já retorna cedo (linha 679) antes de chamar `create_data_directories()` — verificar que a nova função `check_storage_permissions()` também NÃO é chamada no modo dry-run
  - Adicionar nota no output do dry-run indicando que permissões não foram verificadas
- **Notas:** A verificação é simples — basta garantir que a chamada de `check_storage_permissions()` fique após o `if dry_run: return` block, ou dentro do bloco de geração de arquivos.

- [ ] Implementado
- [ ] Validado

---

### Etapa 5 — Validação final com `--dry-run` e execução real

- **Objetivo:** Validar que todas as mudanças funcionam corretamente.
- **Arquivos afetados:** Nenhum (validação manual)
- **Resultado esperado:**
  - `./setup.py --dry-run` executa sem erros, não cria diretórios, não modifica permissões
  - `./setup.py` em um `storage_path` sem permissão oferece `sudo`, aborta se recusado
  - `./setup.py` em um `storage_path` com permissão cria diretórios com 755/775, AdGuard com 777
  - Re-executar `setup.py` não altera permissões de diretórios existentes
- **Notas:** Testar com um path temporário (`/tmp/test-storage`) para validação segura.

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: Verifica permissão de escrita no storage_path | Etapa 1 |
| CA-02: Oferece sudo chown com confirmação explícita | Etapa 1 |
| CA-03: Aborta com mensagem clara se sudo recusado | Etapa 1 |
| CA-04: Diretórios criados com 755/775 (não 777) | Etapa 2 |
| CA-05: AdGuard mantém 777 (exceção justificada) | Etapa 2 |
| CA-06: Diretórios herdam ownership do usuário | Etapa 2 |
| CA-07: Idempotência — não quebra permissões existentes | Etapa 3 |
| CA-08: --dry-run não modifica permissões nem cria diretórios | Etapa 4 |

---

## Checklist de Aprovação do Plan

- [ ] Especifica o QUE, não o COMO — descreve comportamento desejado, não detalhes de implementação
- [ ] Critérios de aceite verificáveis — cada CA pode ser testado manualmente ou automaticamente
- [ ] Fora de escopo explícito — delimita claramente o que NÃO será feito
- [ ] Dependências declaradas — lista specs, sistemas ou decisões pendentes
- [ ] Alinhada com context.md — não viola nenhuma premissa inviolável
- [ ] Escopo atômico — uma feature por spec, sem misturar funcionalidades independentes
- [ ] Notas técnicas justificam decisões — explica o "porquê" de escolhas técnicas relevantes

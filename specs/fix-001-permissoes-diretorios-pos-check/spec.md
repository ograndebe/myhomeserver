# Fix-001 — Permissões de Diretórios Falham Após Correção no Storage Path

> **Status:** done
> **Spec original:** [spec-005](../spec-005-gestao-permissoes-host/spec.md)
> **Sintoma:** `setup.py` reporta permissões corrigidas no `storage_path`, mas em seguida falha ao criar/configurar subdiretórios de dados e ao gerar arquivos em `output/`
> **Criado em:** 2026-05-06

---

## 1. Sintoma Relatado

Ao executar `./setup.py`, o script exibe:

```
✔ Permissões corrigidas em /mnt/data/myhomeserver
Criando diretórios de dados...
  ✘ traefik/acme — [Errno 1] Operation not permitted: '/mnt/data/myhomeserver/traefik/acme'
  ✘ traefik/logs — [Errno 1] Operation not permitted: '/mnt/data/myhomeserver/traefik/logs'
  ✘ adguard/work — [Errno 1] Operation not permitted: '/mnt/data/myhomeserver/adguard/work'
  ✘ adguard/conf — [Errno 13] Permission denied: '/mnt/data/myhomeserver/adguard/conf'
  ✘ authentik/custom-templates — [Errno 1] Operation not permitted: '/mnt/data/myhomeserver/authentik/custom-templates'
```

E na geração de arquivos:

```
  ✘ output/adguard/AdGuardHome.yaml — [Errno 13] Permission denied: '/home/rafael/myhomeserver/output/adguard/AdGuardHome.yaml'
```

### Passos para reproduzir

1. Ter um `storage_path` e/ou `output/` com subdiretórios previamente criados (possivelmente por outro usuário ou execução anterior com permissões elevadas).
2. Executar `./setup.py` com um usuário não-root.
3. Aceitar a correção de permissões no `storage_path` raiz quando perguntado.
4. Observar que o erro persiste em subdiretórios existentes dentro do `storage_path` e no `output/`.

---

## 2. Comportamento Esperado

- `setup.py` deve conseguir criar e configurar todos os diretórios necessários sem erros de permissão, mesmo quando subdiretórios existem com ownership diferente.
- A geração de arquivos em `output/` deve funcionar sem `Permission denied`.
- O script deve ser resiliente: se não puder ajustar ownership de um diretório existente, deve tentar com `sudo` (mediante confirmação prévia ou explícita) ou ao menos não falhar silenciosamente em massa.

---

## 3. Análise de Impacto

- **Escopo do bug:** Criação de diretórios de dados (`create_data_directories`) e renderização de templates (`render_templates`). Afeta subdiretórios preexistentes com ownership incorreto.
- **Risco de regressão:** Baixo — a correção limita-se a tratamento de exceção e verificação de permissões no `output/`, sem alterar a lógica de serviços ou templates.
- **Serviços impactados:** Todos os serviços que dependem de diretórios em `storage_path` e `output/` (Traefik, AdGuard, Authentik, Jellyfin stack, etc.).

---

## 4. Critérios de Aceite da Correção

- [ ] **CA-01:** `create_data_directories()` não falha com `Operation not permitted` ou `Permission denied` quando encontra subdiretórios existentes com ownership diferente — tenta `sudo chown` ou trata o erro de forma elegante
- [ ] **CA-02:** `render_templates()` garante que `output/` e seus subdiretórios são graváveis antes de escrever arquivos — oferecendo correção via `sudo` quando necessário
- [ ] **CA-03:** Re-executar `./setup.py` é idempotente e não gera erros de permissão em diretórios já existentes
- [ ] **CA-04:** `./setup.py --dry-run` continua não modificando permissões nem criando diretórios

---

## 5. Fora de Escopo

- Correção de permissões em diretórios de mídia (`media/movies`, `downloads`, etc.) que não são criados pelo `setup.py`
- Suporte a ACLs avançadas (POSIX ACLs) ou SELinux/AppArmor
- Alteração da arquitetura de armazenamento (ex: mover `output/` para fora do projeto)

---

## 6. Dependências

- **Depende de:** spec-005 (Gestão de Permissões de Diretórios no Host) — a correção atua sobre a implementação existente
- **Premissas assumidas:**
  - `sudo` está disponível no host
  - O usuário tem capacidade de executar `sudo chown` (ou pode resolver manualmente)

---

## 7. Notas Técnicas

### 5.1 Causa raiz provável

A função `check_storage_permissions()` faz `sudo chown` apenas no diretório raiz (`storage_path`). No entanto, `create_data_directories()` tenta aplicar `os.chown()` e `chmod()` em cada subdiretório. Se um subdiretório já existe e é owned por `root` (ou outro usuário), `os.chown()` chamado sem privilégios elevados levanta `OSError: [Errno 1] Operation not permitted`.

Além disso, o diretório `output/` (local, no projeto) não passa por nenhuma verificação de permissões. Se `output/adguard/` foi criado previamente com outro ownership, `output_path.write_text()` falha com `Permission denied`.

### 5.2 Abordagem de correção

1. **Em `create_data_directories()`:**
   - Separar a lógica de criação (`mkdir`) da aplicação de permissões (`chown`/`chmod`).
   - Se `os.chown()` falhar com `EPERM` ou `EACCES` em um diretório **existente**, tentar `sudo chown` naquele caminho específico (reaproveitando a lógica já existente no `check_storage_permissions`).
   - Se `sudo` também falhar, exibir warning em vez de erro fatal, pois o diretório pode já ter permissões suficientes.
   - Se o diretório foi **criado agora** e `chown`/`chmod` falha, isso indica problema mais grave no sistema de arquivos — manter como erro, mas com mensagem mais clara.

2. **Em `render_templates()` / `OUTPUT`:**
   - Antes de renderizar, verificar se `OUTPUT` e seus subdiretórios são graváveis.
   - Se não forem, aplicar a mesma lógica de `check_storage_permissions()` ao diretório `output/` (ou aos subdiretórios específicos que falharem).

3. **Idempotência:**
   - Verificar permissões atuais antes de tentar alterar, evitando chamadas desnecessárias.
   - No `--dry-run`, não chamar nenhuma função que toque em diretórios ou permissões.

---

## 8. Checklist de Aprovação do Fix

- [ ] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [ ] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [ ] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [ ] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [ ] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [ ] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [ ] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes

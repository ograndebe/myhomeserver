# Spec-005 — Gestão de Permissões de Diretórios no Host

> **Status:** done
> **Backlog:** BACK-005
> **Criado em:** 2026-05-06

---

## 1. Visão Geral

`setup.py` deve verificar e corrigir permissões do `storage_path` antes de criar diretórios de dados. Quando o usuário não tem permissão de escrita, o script deve oferecer ajuste via `sudo` (com consentimento explícito). Os diretórios criados devem receber permissões alinhadas ao PUID/PGID que serão usados nos containers, garantindo que os containers tenham acesso de leitura/gravação sem usar `777` indiscriminadamente.

---

## 2. Critérios de Aceite

- [ ] **CA-01:** `setup.py` verifica se o usuário tem permissão de escrita no `storage_path` antes de chamar `create_data_directories()`
- [ ] **CA-02:** Se não tiver permissão, o script oferece executar `sudo chown $USER:$USER <storage_path>` — só executa com confirmação explícita do usuário
- [ ] **CA-03:** Se o usuário recusar `sudo`, o script aborta com mensagem clara instruindo como resolver manualmente
- [ ] **CA-04:** `create_data_directories()` cria diretórios com permissões `755` (ou `775` se grupo precisa write) — não `777`
- [ ] **CA-05:** AdGuard mantém permissões `777` (exceção justificada pelo design do container)
- [ ] **CA-06:** Diretórios herdam ownership do usuário que executou `setup.py` (alinhado com PUID/PGID dos containers)
- [ ] **CA-07:** Re-executar `setup.py` é idempotente — não quebra permissões de diretórios existentes
- [ ] **CA-08:** `./setup.py --dry-run` não tenta modificar permissões nem criar diretórios

---

## 3. Fora de Escopo

- Gestão de ACLs avançadas (POSIX ACLs, NFS permissions)
- Suporte a múltiplos usuários no host
- Alteração de permissões em diretórios já existentes que não foram criados pelo `setup.py`
- Suporte a filesystems com permissões especiais (ZFS, Btrfs subvolumes com flags)

---

## 4. Dependências

- **Depende de:** Nenhuma spec existente
- **Premissas assumidas:**
  - `sudo` está disponível no host do usuário
  - O PUID/PGID dos containers é configurável via `config/services.yml` ou prompt (padrão: 1000/1000)
  - O `storage_path` é um caminho local válido (NFS/remote mounts não tratados nesta spec)

---

## 5. Notas Técnicas

### 5.1 Fluxo de verificação de permissões

```
1. Verificar os.access(storage_path, os.W_OK)
2. Se False → perguntar ao usuário se deseja ajustar com sudo
3. Se True → prosseguir normalmente
4. Criar diretórios com pathlib.Path.mkdir(parents=True, exist_ok=True)
5. Aplicar chmod adequado (755 ou 775) após criação
6. AdGuard: exceção com chmod 777 (já existente)
```

### 5.2 Execução de sudo

- Usar `subprocess.run(["sudo", "chown", f"{os.getuid()}:{os.getgid()}", str(storage_path)])`
- Capturar exit code — se falhar, abortar com erro claro
- Nunca executar sudo silenciosamente — sempre com prompt explícito

### 5.3 PUID/PGID

- O `setup.py` já conhece os valores de PUID/PGID (gera env vars do docker-compose)
- Se PUID/PGID != uid/gid do usuário atual, aplicar `chown` nos diretórios criados para os valores corretos
- Isso garante que os containers (que rodam com PUID/PGID) tenham acesso aos diretórios do host

### 5.4 Idempotência

- `mkdir(parents=True, exist_ok=True)` já é idempotente
- `chmod` só é aplicado se o diretório foi criado agora OU se as permissões atuais são diferentes das esperadas
- `chown` via sudo só roda se necessário (verificar ownership atual antes)

---

## 6. Bugfixes

- [fix-001-permissoes-diretorios-pos-check](../fix-001-permissoes-diretorios-pos-check/spec.md) — `create_data_directories()` e `output/` falhavam com `Operation not permitted` / `Permission denied` quando subdiretórios existiam com ownership diferente — 2026-05-06

---

## 7. Checklist de Aprovação da Spec

- [ ] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [ ] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [ ] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [ ] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [ ] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [ ] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [ ] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes

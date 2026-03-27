---
name: sync-server
description: Sincroniza o repositório local com o servidor via rsync (apaga remoto e copia local)
---

## O que fazer

Executa `./scripts/sync-server.sh` para sincronizar o projeto com o servidor de teste.

### Passo 1 — Verificar script

Confirme que `scripts/sync-server.sh` existe e é executável.

### Passo 2 — Testar conexão SSH

Execute um teste de conexão básica:
```bash
ssh -o BatchMode=yes rafael@192.168.15.6 echo "ok"
```

Se falhar, avise o usuário para configurar SSH.

### Passo 3 — Perguntar modo de execução

```
🔄 Modos disponíveis:

  1. --dry-run  → Preview do que será sincronizado (sem copiar)
  2. --force    → Sincroniza direto (sem confirmação)
  3. [Enter]    → Modo interativo (com confirmação)

Qual modo deseja usar?
```

### Passo 4 — Executar sincronização

Execute o script com o modo escolhido:
```bash
./scripts/sync-server.sh [modo]
```

### Passo 5 — Reportar resultado

Informe se a sincronização foi bem-sucedida e quanto tempo levou.

---

## Notas

- **Origem:** diretório atual (.)
- **Destino:** `rafael@192.168.15.6:/home/rafael/homeserver/`
- **Excluídos:** `.git/`, `*.md`, `.opencode/`, `credentials.txt`, `build/`
- **Flag `--delete`:** arquivos no servidor que não existem localmente são apagados

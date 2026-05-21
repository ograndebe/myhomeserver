# Spec-007 — Container Post-Setup Pattern

> **Status:** done
> **Backlog:** BACK-012
> **Criado em:** 2026-05-20

---

## 1. Visão Geral

Eliminar os containers `bootstrap` e `post-setup` migrando toda a lógica de inicialização para dentro dos próprios containers alvo, usando o padrão unificado de `custom-entrypoint.sh` → `post-setup.sh` → `exec "$@"` definido em `CONTEXT.md`.

Atualmente dois containers sidecar fazem configuração em outros serviços:
- **`bootstrap`**: configura Authentik (token, providers, apps, outpost) via `docker exec` + Docker socket
- **`post-setup`**: configura stack *arr (trackers, API keys, integrações) + Authentik via API REST

Ambos violam as regras do projeto: usam Docker socket, não seguem o pattern de entrypoint, e criam dependência de orquestrador externo.

---

## 2. Critérios de Aceite

- [ ] **CA-01:** Container `bootstrap` removido do `docker-compose.yml.j2` — zero referência a ele
- [ ] **CA-02:** Container `post-setup` removido do `docker-compose.yml.j2` — zero referência a ele
- [ ] **CA-03:** `authentik-server` executa seu próprio bootstrap (token, providers, apps, outpost) via `post-setup.sh` montado como volume
- [ ] **CA-04:** `prowlarr` injeta trackers do `trackers.txt` via `post-setup.sh` próprio
- [ ] **CA-05:** `radarr`, `sonarr`, `lidarr` conectam a qBittorrent e Prowlarr via `post-setup.sh` próprio
- [ ] **CA-06:** `bazarr` conecta a Radarr e Sonarr via `post-setup.sh` próprio
- [ ] **CA-07:** `qbittorrent` injeta trackers via `post-setup.sh` próprio
- [ ] **CA-08:** Nenhum container usa Docker socket (`/var/run/docker.sock`) — exceto se estritamente necessário e justificado
- [ ] **CA-09:** Nenhum container usa `docker exec` contra outro container
- [ ] **CA-10:** Todos os `post-setup.sh` são idempotentes — re-executar não duplica configurações
- [ ] **CA-11:** `./setup.py --dry-run` funciona sem erros
- [ ] **CA-12:** Diretório `bootstrap/` removido do projeto

---

## 3. Fora de Escopo

- Alterar a lógica de configuração do Authentik (apenas onde é executada muda, não o que é configurado)
- Alterar a lógica de configuração da stack *arr (idem)
- Adicionar novos serviços ou funcionalidades
- Modificar o `post-setup.sh` raiz do projeto (script de subir containers)
- Refatorar healthchecks ou redes

---

## 4. Dependências

- **Depende de:** Nenhuma spec pendente
- **Premissas assumidas:**
  - `authentik-server` roda Django e aceita `ak shell` internamente (já comprovado)
  - Serviços *arr expõem API REST na porta configurada
  - `curl` ou `python3` estão disponíveis nas imagens base (ou podem ser instalados via volume de script)

---

## 5. Notas Técnicas

### 5.1 — Estrutura de scripts

Cada serviço ganha um diretório em `scripts/<servico>/` com dois arquivos:

```
scripts/
├── authentik-server/
│   ├── custom-entrypoint.sh
│   └── post-setup.sh        (lógica atual do bootstrap + parte do post-setup.py)
├── prowlarr/
│   ├── custom-entrypoint.sh
│   └── post-setup.sh        (injeção de trackers)
├── radarr/
│   ├── custom-entrypoint.sh
│   └── post-setup.sh        (conexão qBittorrent + Prowlarr)
├── sonarr/
│   ├── custom-entrypoint.sh
│   └── post-setup.sh        (conexão qBittorrent + Prowlarr)
├── lidarr/
│   ├── custom-entrypoint.sh
│   └── post-setup.sh        (conexão qBittorrent + Prowlarr)
├── bazarr/
│   ├── custom-entrypoint.sh
│   └── post-setup.sh        (conexão Radarr + Sonarr)
└── qbittorrent/
    ├── custom-entrypoint.sh
    └── post-setup.sh        (injeção de trackers)
```

### 5.2 — `custom-entrypoint.sh` genérico

Todos os entrypoints seguem o mesmo template:

```bash
#!/bin/sh
set -e

echo "Running post-setup for <servico>..."
/post-setup.sh

echo "Starting original process..."
exec "$@"
```

### 5.3 — Como evitar `docker exec` no Authentik

O `bootstrap` atual usa `docker exec authentik-server ak shell` para acessar a Django ORM.
A solução é montar o script como volume e executá-lo **dentro** do `authentik-server`:

- O `post-setup.sh` do authentik é executado dentro do próprio container
- Usa `ak shell` diretamente (sem `docker exec`)
- O `custom-entrypoint.sh` chama o script antes de `exec "$@"`

### 5.4 — Imagens que não têm `python3` ou `curl`

Serviços *arr usam imagens `lscr.io/linuxserver/*` que incluem `python3` e `curl` por padrão.
Para imagens que não têm, o `post-setup.sh` pode instalar via `apk` (Alpine) ou `apt` (Debian) na primeira execução.

### 5.5 — Ordem de execução

Como não há mais um orquestrador central, cada `post-setup.sh` deve aguardar suas dependências:

| Container | Aguarda |
|---|---|
| `authentik-server` | PostgreSQL + Redis (já tem healthcheck) |
| `prowlarr` | Nada (independente) |
| `radarr/sonarr/lidarr` | `prowlarr` + `qbittorrent` (polling HTTP) |
| `bazarr` | `radarr` + `sonarr` (polling HTTP) |
| `qbittorrent` | Nada (independente) |

### 5.6 — Idempotência

Cada `post-setup.sh` deve usar flags ou verificações:

- Authentik: `get_or_create_*` já é idempotente (busca antes de criar)
- Prowlarr: verificar se indexadores já existem antes de adicionar
- *arr: verificar se download client / indexer já existe
- Bazarr: verificar settings antes de atualizar
- qBittorrent: verificar trackers antes de injetar

### 5.7 — O que acontece com `scripts/post_setup.py`

O arquivo `scripts/post_setup.py` é **desmembrado**:
- Parte Authentik → `scripts/authentik-server/post-setup.sh`
- Parte Prowlarr → `scripts/prowlarr/post-setup.sh`
- Parte Radarr/Sonarr/Lidarr → `scripts/<servico>/post-setup.sh`
- Parte Bazarr → `scripts/bazarr/post-setup.sh`
- Parte qBittorrent → `scripts/qbittorrent/post-setup.sh`
- Parte Jellyfin (apenas leitura de API key) → **removida** (não há setup a fazer)

O arquivo original é deletado.

### 5.8 — Templates docker-compose

Cada serviço afetado ganha no template:

```yaml
servico:
  image: imagem:tag
  entrypoint: ["/custom-entrypoint.sh"]
  volumes:
    - ../scripts/servico/custom-entrypoint.sh:/custom-entrypoint.sh:ro
    - ../scripts/servico/post-setup.sh:/post-setup.sh:ro
```

---

## 6. Checklist de Aprovação da Spec

- [ ] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [ ] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [ ] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [ ] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [ ] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [ ] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [ ] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes

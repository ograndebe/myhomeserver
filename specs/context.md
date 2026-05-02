# specs/context.md — Premissas Invioláveis

> Este arquivo define premissas que TODAS as specs, plans e implementações devem respeitar.

---

## 1. Stack e Convenções

- **Linguagem:** Python 3.11+ via `uv` (PEP 723 inline metadata)
- **Templates:** Jinja2 com `trim_blocks=True` e `lstrip_blocks=True`
- **Orquestração:** Docker Compose, serviços com `restart: unless-stopped`
- **Imagens:** Tags específicas, nunca `latest` (exceto onde justificado)
- **Redes:** `proxy` (exposta) e `internal` (isolada)
- **Docstrings em Português** (estilo Google)
- **Divisores de seção:** `# ── Nome ──` com dashes até o fim da linha

---

## 2. Regras Críticas

1. **Nunca editar arquivos em `output/`** — modificar templates e re-executar `./setup.py`
2. **Nunca commitar secrets** — `*.env` e `output/` são gitignored
3. **Templates devem ser idempotentes** — re-executar `setup.py` reusa secrets existentes
4. **Usar `uv` para Python** — shebang: `#!/usr/bin/env -S uv run --script`
5. **Porta 80/443 obrigatórias** — Traefik precisa para Let's Encrypt
6. **AdGuard dirs precisam chmod 777** — `create_data_directories()` faz isso explicitamente

---

## 3. Arquitetura de Serviços

| Serviço      | Obrigatório? | Função |
|--------------|-------------|--------|
| Traefik      | Sim         | Reverse proxy + TLS wildcard |
| AdGuard Home | Sim         | DNS local, resolve `*.domain` para IP interno |
| WireGuard    | Sim         | VPN para acesso remoto |
| Authentik    | Sim         | SSO centralizado |
| Jellyfin     | Não         | Media server + stack *arr |
| Nextcloud    | Não         | Storage pessoal |
| Immich       | Não         | Backup de fotos |

---

## 4. Fluxo de Adição de Serviço

1. Adicionar definição em `config/services.yml`
2. Criar template fragment em `templates/services/<servico>.j2`
3. Adicionar include condicional em `templates/docker-compose.yml.j2`
4. Adicionar diretórios em `create_data_directories()` se necessário
5. Testar com `./setup.py --dry-run`

---

## 5. Checks Obrigatórios — Spec

Toda spec deve passar nestes checks antes de ser considerada pronta para implementação:

- [ ] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [ ] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [ ] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [ ] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [ ] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [ ] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [ ] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes

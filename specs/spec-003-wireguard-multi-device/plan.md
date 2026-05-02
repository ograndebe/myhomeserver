# Plan — Spec-003 — WireGuard Multi-Device Peer Setup

> **Status:** done
> **Spec:** [spec.md](./spec.md)
> **Criado em:** 2026-05-02
> **Atualizado em:** 2026-05-02

---

## Visão Geral

Adicionar uma pergunta interativa ao `setup.py` para coletar uma lista de nomes de devices WireGuard, normalizá-los, persisti-los no `.env` (com idempotência) e passar a lista correta via `PEERS` no docker-compose. Além disso, atualizar o `docs/post-setup.md` com instruções claras de como gerar QR Codes e conectar cada device. A abordagem usa a variável `PEERS` nativa do container linuxserver/wireguard, que gera automaticamente as configs e QR codes dos peers na primeira inicialização.

---

## Etapas de Implementação

### Etapa 1 — Pergunta interativa de devices no setup.py

- **Objetivo:** Adicionar pergunta para lista de devices WireGuard no fluxo interativo, com normalização e valor padrão
- **Arquivos afetados:** `setup.py`
- **Detalhes:**
  - Adicionar função `normalize_peer_name(name: str) -> str` que: converte para lowercase, substitui espaços por underscore, remove caracteres especiais (regex `[^a-z0-9_]`)
  - Adicionar pergunta `questionary.text` em `ask_questions()` após a seção de serviços opcionais
  - Valor padrão: `"phone"`
  - Se input vazio, usar `"phone"` como fallback
  - Retornar `wireguard_peers` como string comma-separated normalizada no dict de respostas
  - Adicionar `wireguard_peers` ao `load_existing_env()` para idempotência (ler `WIREGUARD_PEERS` do `.env` raiz)
- **Resultado esperado:** `./setup.py` pergunta devices, normaliza, e inclui `wireguard_peers` no contexto
- **Notas:** A pergunta deve ser feita antes do environment check, junto com as demais perguntas

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Idempotência: persistir e reusar wireguard_peers

- **Objetivo:** Garantir que ao re-executar `setup.py`, a lista de devices existente seja preservada
- **Arquivos afetados:** `setup.py`
- **Detalhes:**
  - Estender `load_existing_env()` para ler `WIREGUARD_PEERS` do `.env` na raiz
  - Estender `load_output_env()` para também ler `WIREGUARD_PEERS` do `output/.env`
  - No `main()`, usar `existing_wireguard_peers or answers["wireguard_peers"]` ao montar o contexto
  - No modo `--use-existing-env`, incluir `wireguard_peers` com valor do `.env` ou default `"phone"`
- **Resultado esperado:** Re-executar `./setup.py` mantém os mesmos devices sem perguntar novamente (se já exists no .env)

- [x] Implementado
- [x] Validado

---

### Etapa 3 — Atualizar template .env.j2

- **Objetivo:** Usar a variável `wireguard_peers` do contexto no template
- **Arquivos afetados:** `templates/.env.j2`
- **Detalhes:**
  - A linha `WIREGUARD_PEERS={{ wireguard_peers }}` já existe no template (linha 34) — verificar que está correta
  - Confirmar que o valor renderizado é a lista normalizada comma-separated
- **Resultado esperado:** `output/.env` contém `WIREGUARD_PEERS=phone,laptop,tablet` (exemplo)

- [ ] Implementado
- [ ] Validado

---

### Etapa 4 — Atualizar template docker-compose.yml.j2

- **Objetivo:** Garantir que o serviço WireGuard use `${WIREGUARD_PEERS}` corretamente
- **Arquivos afetados:** `templates/docker-compose.yml.j2`
- **Detalhes:**
  - A linha `PEERS=${WIREGUARD_PEERS:-laptop,phone}` já existe (linha 104) — atualizar o fallback para usar o mesmo default do setup (`phone`)
  - Alterar para `PEERS=${WIREGUARD_PEERS:-phone}` para consistência
- **Resultado esperado:** Container WireGuard recebe a lista correta de peers via env var

- [x] Implementado
- [x] Validado

---

### Etapa 5 — Documentar WireGuard multi-device no post-setup.md

- **Objetivo:** Adicionar seção completa de configuração de devices no `docs/post-setup.md`
- **Arquivos afetados:** `docs/post-setup.md`
- **Detalhes:**
  - Substituir a seção 4 atual ("WireGuard — Configuração dos clientes") por uma versão expandida
  - Incluir:
    - Como listar os peers existentes (`ls output-data/wireguard/config/`)
    - Como gerar QR Code de um peer específico: `docker exec wireguard show-peer <nome>`
    - Como exibir QR Code no terminal: `docker exec wireguard show-peer <nome> \| qrencode -t ANSIUTF8`
    - Como copiar o arquivo `.conf` de um peer para outro dispositivo
    - Instruções de como escanear QR Code no app WireGuard (mobile) e importar `.conf` (desktop)
    - Como adicionar novos devices após o setup inicial (editar `WIREGUARD_PEERS` no `.env` e recriar container)
- **Resultado esperado:** Usuário consegue configurar qualquer device seguindo a documentação

- [ ] Implementado
- [ ] Validado

---

### Etapa 6 — Validar com dry-run e teste completo

- **Objetivo:** Executar `./setup.py --dry-run` e verificar o contexto gerado
- **Arquivos afetados:** nenhum (validação)
- **Detalhes:**
  - Executar `./setup.py --dry-run` simulando input de múltiplos devices
  - Verificar que `wireguard_peers` aparece corretamente no JSON output
  - Executar `./setup.py` completo (se ambiente permitir) e verificar `output/.env` e `output/docker-compose.yml`
  - Verificar que `docs/post-setup.md` renderiza corretamente
- **Resultado esperado:** Todos os artifacts gerados corretamente, documentação legível

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: Setup pergunta nomes dos devices | Etapa 1 |
| CA-02: Valor padrão sugerido | Etapa 1 |
| CA-03: Variáveis geradas no .env | Etapa 1, 3 |
| CA-04: Idempotência na re-execução | Etapa 2 |
| CA-05: dry-run exibe devices corretamente | Etapa 1, 6 |
| CA-06: Docs com seção de QR Code | Etapa 5 |
| CA-07: Docs com instruções de conexão | Etapa 5 |
| CA-08: Normalização de nomes | Etapa 1 |

---

## Checklist de Aprovação do Plan

- [ ] **Cobre todos os critérios de aceite da spec** — cada CA mapeado para pelo menos uma etapa
- [ ] **Etapas são atômicas e sequenciáveis** — cada etapa pode ser implementada e validada independentemente
- [ ] **Não viola premissas do context.md** — segue idempotência, templates Jinja2, docstrings PT, não edita output/
- [ ] **Arquivos afetados estão identificados** — lista completa em cada etapa
- [ ] **Resultado esperado é verificável** — cada etapa tem critério de validação claro
- [ ] **Ordem de execução faz sentido** — etapas seguem dependências lógicas (código → templates → docs → validação)

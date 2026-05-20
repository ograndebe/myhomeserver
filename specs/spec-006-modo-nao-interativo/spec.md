# Spec-006 — Modo Não Interativo

> **Status:** done
> **Backlog:** —
> **Criado em:** 2026-05-07

---

## 1. Visão Geral

O script `setup.py` atualmente suporta `--use-existing-env`, mas o arquivo `.env` gerado (`output/.env`) não captura todas as respostas do usuário — em especial a seleção de serviços opcionais e o `AUTHENTIK_INITIAL_ADMIN_USERNAME`. Isso impede que uma segunda execução seja totalmente autônoma. A feature consiste em: (a) garantir que o `.env` de saída contenha **todas** as respostas necessárias para reconstruir o contexto sem interação; (b) adicionar um argumento `--non-interactive` (ou aprimorar `--use-existing-env`) que rode o script sem nenhuma pergunta, lendo tudo do `.env`.

---

## 2. Critérios de Aceite

- [ ] **CA-01:** Executar `./setup.py --non-interactive` com um `.env` válido gera todos os arquivos em `output/` sem exibir nenhuma pergunta interativa
- [ ] **CA-02:** O arquivo `output/.env` contém campos para todos os inputs do usuário: `DOMAIN`, `CF_API_EMAIL`, `CF_DNS_API_TOKEN`, `ACME_EMAIL`, `STORAGE_PATH`, `AUTHENTIK_INITIAL_ADMIN_EMAIL`, `AUTHENTIK_INITIAL_ADMIN_USERNAME`, `AUTHENTIK_INITIAL_ADMIN_PASSWORD`, `WIREGUARD_PEERS`, e flags de serviços opcionais (`ENABLE_JELLYFIN`, `ENABLE_NEXTCLOUD`, `ENABLE_IMMICH`, `ENABLE_STATIC_PAGE`)
- [ ] **CA-03:** Uma segunda execução com `--non-interactive` reusa os mesmos valores da primeira execução (idempotência) — serviços opcionais, peers, credenciais e secrets permanecem inalterados
- [ ] **CA-04:** Executar `./setup.py --non-interactive` sem um `.env` válido (faltando `DOMAIN`) aborta com mensagem de erro clara e código de saída diferente de zero
- [ ] **CA-05:** O modo interativo padrão (sem flags) continua funcionando exatamente como antes
- [ ] **CA-06:** `./setup.py --dry-run --non-interactive` exibe o contexto renderizado sem perguntas e sem gerar arquivos

---

## 3. Fora de Escopo

- Alterar o comportamento do modo interativo padrão
- Adicionar validação de credenciais Cloudflare ou Authentik
- Suporte a múltiplos perfis de configuração
- Testes automatizados (CI) — apenas a capacidade de rodar sem interação

---

## 4. Dependências

- **Depende de:** nenhuma
- **Premissas assumidas:**
  - O `.env` de leitura para defaults continua sendo o arquivo raiz `.env` (conforme `load_existing_env()`)
  - O `.env` de saída (`output/.env`) é o arquivo que deve conter todos os campos para reutilização
  - O script já usa `click` para CLI, facilitando a adição de novas opções

---

## 5. Notas Técnicas

### 5.1 Campos ausentes no `output/.env` atual

O template `templates/.env.j2` **não** inclui:
- `AUTHENTIK_INITIAL_ADMIN_USERNAME` — hardcoded como `administrator` no `load_output_env()`, mas o usuário pode alterá-lo
- Flags de serviços opcionais (`ENABLE_JELLYFIN`, `ENABLE_NEXTCLOUD`, `ENABLE_IMMICH`, `ENABLE_STATIC_PAGE`) — hoje são perdidos entre execuções

### 5.2 Abordagem proposta

1. **Atualizar `templates/.env.j2`** para incluir todos os campos de input do usuário, incluindo flags booleanas de serviços opcionais e `AUTHENTIK_INITIAL_ADMIN_USERNAME`
2. **Atualizar `load_existing_env()`** para ler as flags de serviços opcionais do `.env` raiz
3. **Atualizar `load_output_env()`** para ler `AUTHENTIK_INITIAL_ADMIN_USERNAME` e as flags de serviços opcionais do `output/.env`
4. **Renomear/criar flag `--non-interactive`** como alias de `--use-existing-env` (ou substituir), garantindo que todos os valores sejam lidos do `.env` — incluindo serviços opcionais
5. **No `main()`**, quando `--non-interactive` estiver ativo, construir `answers` completo lendo **todos** os campos do `.env`, com fallback para defaults seguros apenas quando o campo estiver ausente

### 5.3 Mapeamento de campos `.env` → contexto

| Campo `.env` | Chave no contexto | Obrigatório? |
|---|---|---|
| `DOMAIN` | `domain` | Sim |
| `CF_API_EMAIL` | `cf_email` | Sim |
| `CF_DNS_API_TOKEN` | `cf_dns_api_token` | Sim |
| `ACME_EMAIL` | `acme_email` | Sim |
| `STORAGE_PATH` | `storage_path` | Sim |
| `AUTHENTIK_INITIAL_ADMIN_EMAIL` | `authentik_email` | Sim |
| `AUTHENTIK_INITIAL_ADMIN_USERNAME` | `authentik_user` | Sim |
| `AUTHENTIK_INITIAL_ADMIN_PASSWORD` | `authentik_password` | Sim |
| `WIREGUARD_PEERS` | `wireguard_peers` | Não (default: `phone`) |
| `ENABLE_JELLYFIN` | `enable_jellyfin` | Não (default: `false`) |
| `ENABLE_NEXTCLOUD` | `enable_nextcloud` | Não (default: `false`) |
| `ENABLE_IMMICH` | `enable_immich` | Não (default: `false`) |
| `ENABLE_STATIC_PAGE` | `enable_static_page` | Não (default: `true`) |

### 5.4 Parsing de booleanos no `.env`

Valores como `ENABLE_JELLYFIN=true` devem ser parseados como booleano. Usar comparação case-insensitive: `str(val).lower() in ("true", "1", "yes")`.

---

## 6. Checklist de Aprovação da Spec

- [ ] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [ ] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [ ] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [ ] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [ ] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [ ] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [ ] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes

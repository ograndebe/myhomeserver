# Plan — Spec-002 — Substituir DuckDNS por Cloudflare DDNS

> **Status:** done
> **Atualizado em:** 2026-05-01
> **Spec:** [spec.md](./spec.md)
> **Criado em:** 2026-04-30

---

## Visão Geral

Remover completamente o modo DuckDNS do setup e substituí-lo pelo container `cloudflare-ddns` que usa o mesmo API token da Cloudflare já coletado para o Traefik. O WireGuard passará a usar o domínio próprio como `SERVERURL`, unificando a infraestrutura de DNS. A abordagem simplifica o código eliminando toda lógica condicional de dois modos de acesso.

---

## Etapas de Implementação

### Etapa 1 — Remover DuckDNS do `config/services.yml`

- **Objetivo:** Remover a entrada `duckdns` da seção `optional` e o modo `duckdns` da seção `access_modes`
- **Arquivos afetados:** `config/services.yml`
- **Resultado esperado:** `services.yml` contém apenas `domain` como modo de acesso e nenhuma referência a DuckDNS
- **Notas:** Manter seções `mandatory`, `optional` (sem duckdns), `dns_providers` intactas

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Simplificar `setup.py` — remover lógica DuckDNS

- **Objetivo:** Remover toda a lógica condicional de modo de acesso (domain vs duckdns) e perguntas relacionadas ao DuckDNS
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:** `ask_questions()` sempre coleta domínio + Cloudflare credentials diretamente, sem select de modo de acesso
- **Notas:**
  - Remover `access_mode_choices` e `questionary.select` de modo de acesso
  - Remover bloco `if use_duckdns:` inteiro
  - Remover variáveis `use_duckdns`, `duckdns_subdomain`, `duckdns_token` do retorno
  - `domain`, `cf_email`, `cf_dns_api_token` passam a ser sempre coletados
  - Preservar fluxo de Authentik, ACME, storage e serviços opcionais

- [x] Implementado
- [x] Validado

---

### Etapa 3 — Limpar `load_existing_env()` e `load_output_env()`

- **Objetivo:** Remover carregamento de variáveis DuckDNS das funções que leem `.env` existente
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:** `load_existing_env()` e `load_output_env()` não retornam mais chaves `duckdns_*` nem `use_duckdns`
- **Notas:** Remover linhas 64-66 e 146-147

- [x] Implementado
- [x] Validado

---

### Etapa 4 — Limpar `--use-existing-env` e contexto final

- **Objetivo:** Remover referências DuckDNS do dict `answers` no modo `--use-existing-env` e do `context` final
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:** `context` não contém mais chaves `use_duckdns`, `duckdns_subdomain`, `duckdns_token`
- **Notas:**
  - Remover do dict `answers` no bloco `if use_existing_env:` (linhas 660-662)
  - Remover do dict `context` final (linhas 686-690)
  - Remover importações de `dotenv` se não forem mais usadas em outro lugar

- [x] Implementado
- [x] Validado

---

### Etapa 5 — Simplificar `generate_post_build_notes()` e `print_next_steps()`

- **Objetivo:** Remover condicionais DuckDNS das funções que geram instruções pós-setup
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:** Ambas as funções sempre exibem instruções de DNS wildcard (sem branch DuckDNS)
- **Notas:**
  - `generate_post_build_notes()`: remover bloco `if context.get("use_duckdns"):` (linhas 503-515), manter apenas o branch else
  - `print_next_steps()`: remover bloco `if use_duckdns:` (linhas 562-572), manter apenas o branch else

- [x] Implementado
- [x] Validado

---

### Etapa 6 — Atualizar `templates/.env.j2`

- **Objetivo:** Remover variáveis `USE_DUCKDNS`, `DUCKDNS_SUBDOMAIN`, `DUCKDNS_TOKEN` e a condicional `{% if use_duckdns %}`
- **Arquivos afetados:** `templates/.env.j2`
- **Resultado esperado:** `.env` gerado sempre contém `CF_API_EMAIL` e `CF_DNS_API_TOKEN` (sem condicional)
- **Notas:**
  - Remover linha `USE_DUCKDNS={{ use_duckdns | lower }}`
  - Remover bloco `{% if use_duckdns %}...{% else %}...{% endif %}`
  - Manter `CF_API_EMAIL` e `CF_DNS_API_TOKEN` sempre presentes

- [x] Implementado
- [x] Validado

---

### Etapa 7 — Atualizar `templates/docker-compose.yml.j2`

- **Objetivo:** Remover serviço DuckDNS condicional e adicionar serviço `cloudflare-ddns`
- **Arquivos afetados:** `templates/docker-compose.yml.j2`
- **Resultado esperado:** Docker-compose contém `cloudflare-ddns` no lugar de `duckdns`, WireGuard `SERVERURL` usa `{{ domain }}` diretamente
- **Notas:**
  - Remover bloco `{% if use_duckdns %}...{% endif %}` (linhas 76-92)
  - Adicionar serviço `cloudflare-ddns` após AdGuard (antes do WireGuard):
    ```yaml
    cloudflare-ddns:
      image: oznu/cloudflare-ddns:3.1.0
      container_name: cloudflare-ddns
      environment:
        - API_KEY=${CF_DNS_API_TOKEN}
        - ZONE=${DOMAIN}
        - SUBDOMAIN=
        - PROXIED=false
      restart: unless-stopped
      network_mode: host
    ```
  - WireGuard `SERVERURL` já usa `{{ domain }}` — não precisa alterar (funciona para ambos os modos atualmente)
  - Usar tag específica `3.1.0` em vez de `latest` (convenção do projeto)

- [x] Implementado
- [x] Validado

---

### Etapa 8 — Validar com `./setup.py --dry-run`

- **Objetivo:** Executar o setup em modo dry-run e verificar que o contexto gerado não contém variáveis DuckDNS
- **Arquivos afetados:** nenhum (apenas validação)
- **Resultado esperado:**
  - `./setup.py --dry-run` executa sem erros
  - Output JSON não contém `use_duckdns`, `duckdns_subdomain`, `duckdns_token`
  - Contém `domain`, `cf_email`, `cf_dns_api_token`
- **Notas:** Será necessário um `.env` válido na raiz ou responder interativamente

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: Setup não oferece DuckDNS | Etapa 2 |
| CA-02: Container cloudflare-ddns no docker-compose | Etapa 7 |
| CA-03: WireGuard SERVERURL com domínio próprio | Etapa 7 (já funciona, verificado) |
| CA-04: Variáveis DUCKDNS_* removidas do .env e setup.py | Etapas 2, 3, 4, 6 |
| CA-05: --dry-run sem DuckDNS no contexto | Etapas 2, 4, 8 |
| CA-06: Idempotência cloudflare-ddns | Etapa 7 (usa variáveis sempre presentes) |
| CA-07: services.yml sem DuckDNS | Etapa 1 |
| CA-08: Templates sem condicionais DuckDNS | Etapas 6, 7 |

---

## Checklist de Aprovação do Plan

- [ ] **Todos os critérios de aceite cobertos** — cada CA da spec tem pelo menos uma etapa associada
- [ ] **Etapas em ordem lógica de dependência** — nenhuma etapa depende de uma etapa posterior
- [ ] **Arquivos afetados identificados** — cada etapa lista os arquivos que serão modificados
- [ ] **Resultado esperado verificável** — cada etapa tem um critério claro de "pronto"
- [ ] **Alinhado com context.md** — não viola premissas de stack, convenções ou regras críticas
- [ ] **Tags de imagem específicas** — nenhuma imagem usa `latest` sem justificativa
- [ ] **Idempotência preservada** — re-executar setup.py funciona corretamente

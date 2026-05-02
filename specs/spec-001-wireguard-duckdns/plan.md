# Plan — Spec-001 — WireGuard + DuckDNS

> **Status:** done
> **Spec:** [spec.md](./spec.md)
> **Criado em:** 2026-04-30
> **Atualizado em:** 2026-04-30

---

## Visão Geral

Adicionar um modo de operação "DuckDNS-only" ao setup, onde o usuário pode pular a configuração de domínio próprio e usar um subdomínio `.duckdns.org` gratuito. O DuckDNS updater container mantém o IP público sincronizado, e o WireGuard usa esse hostname como endpoint da VPN. A abordagem preserva o fluxo existente de domínio próprio como alternativa, tornando os dois modos mutuamente exclusivos.

---

## Etapas de Implementação

### Etapa 1 — Adicionar DuckDNS ao `config/services.yml`

- **Objetivo:** Definir DuckDNS como serviço opcional e adicionar seção de `access_modes` no services.yml
- **Arquivos afetados:** `config/services.yml`
- **Resultado esperado:** `services.yml` contém entrada `duckdns` e opções de modo de acesso (domain vs duckdns)
- **Notas:** DuckDNS não precisa de subdomain/ports pois é apenas um updater de DNS

- [x] Implementado
- [x] Validado

---

### Etapa 2 — Atualizar `setup.py` com perguntas de modo de acesso

- **Objetivo:** Adicionar pergunta inicial sobre modo de acesso (domínio próprio vs DuckDNS) e coletar token/subdomínio se DuckDNS for selecionado
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:** Fluxo de perguntas suporta ambos os modos, com validação de entrada para token e subdomínio DuckDNS
- **Notas:**
  - Se DuckDNS: pula perguntas de Cloudflare e domínio
  - Se domínio próprio: fluxo atual permanece igual
  - Adicionar `use_duckdns` flag no contexto retornado
  - Preservar valores DuckDNS em `.env` existente para idempotência (CA-08)

- [x] Implementado
- [x] Validado

---

### Etapa 3 — Atualizar template `templates/.env.j2`

- **Objetivo:** Adicionar variáveis `DUCKDNS_SUBDOMAIN` e `DUCKDNS_TOKEN` condicionais ao modo DuckDNS
- **Arquivos afetados:** `templates/.env.j2`
- **Resultado esperado:** `.env` gerado contém variáveis DuckDNS quando `use_duckdns=True`
- **Notas:** Variáveis devem estar em bloco condicional `{% if use_duckdns %}`

- [x] Implementado
- [x] Validado

---

### Etapa 4 — Atualizar template `templates/docker-compose.yml.j2`

- **Objetivo:** Adicionar serviço DuckDNS condicional e ajustar `SERVERURL` do WireGuard para usar o hostname correto
- **Arquivos afetados:** `templates/docker-compose.yml.j2`
- **Resultado esperado:**
  - Se DuckDNS: serviço `duckdns` incluído + WireGuard `SERVERURL={{ duckdns_subdomain }}.duckdns.org`
  - Se domínio: fluxo atual permanece (WireGuard `SERVERURL={{ domain }}`)
- **Notas:**
  - DuckDNS image: `lscr.io/linuxserver/duckdns:latest` (único caso justificado de `latest`, é um updater simples)
  - WireGuard `PEERDNS` continua `{{ local_ip }}` em ambos os modos
  - Traefik e AdGuard permanecem inalterados

- [x] Implementado
- [x] Validado

---

### Etapa 5 — Atualizar `setup.py` — `load_existing_env()` e `load_output_env()`

- **Objetivo:** Carregar valores DuckDNS de `.env` existente para idempotência
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:** Re-executar `setup.py` reusa `DUCKDNS_SUBDOMAIN` e `DUCKDNS_TOKEN` existentes
- **Notas:** Adicionar chaves `duckdns_subdomain` e `duckdns_token` nos dicts retornados

- [x] Implementado
- [x] Validado

---

### Etapa 6 — Atualizar instruções pós-geração

- **Objetivo:** Atualizar `generate_post_build_notes()` e `print_next_steps()` para mencionar port forwarding no router quando DuckDNS é usado
- **Arquivos afetados:** `setup.py`
- **Resultado esperado:** Instruções exibidas ao usuário incluem aviso sobre port forwarding 51820/UDP no modo DuckDNS
- **Notas:** No modo domínio próprio, as instruções permanecem as atuais

- [x] Implementado
- [x] Validado

---

### Etapa 7 — Testar com `--dry-run` em ambos os modos

- **Objetivo:** Validar que `./setup.py --dry-run` funciona corretamente nos modos DuckDNS e domínio próprio
- **Arquivos afetados:** nenhum (apenas validação)
- **Resultado esperado:**
  - Modo DuckDNS: contexto exibe `use_duckdns: true`, `duckdns_subdomain`, `duckdns_token`, sem variáveis Cloudflare
  - Modo domínio: contexto exibe `domain`, `cf_email`, `cf_dns_api_token`, sem variáveis DuckDNS
- **Notas:** Testar também idempotência — rodar duas vezes no mesmo modo

- [x] Implementado
- [x] Validado

---

## Rastreabilidade: Etapas × Critérios de Aceite

| Critério de Aceite | Coberto por Etapa(s) |
|---|---|
| CA-01: Pergunta sobre DuckDNS | Etapa 2 |
| CA-02: Pede token e subdomínio | Etapa 2 |
| CA-03: Container DuckDNS no docker-compose | Etapa 4 |
| CA-04: WireGuard SERVERURL com DuckDNS | Etapa 4 |
| CA-05: Porta 51820/UDP exposta | Etapa 4 (já existente, validar) |
| CA-06: Peers com endpoint DuckDNS correto | Etapa 4 |
| CA-07: Modos mutuamente exclusivos | Etapa 2 |
| CA-08: Idempotência DuckDNS | Etapa 5 |
| CA-09: --dry-run com variáveis DuckDNS | Etapa 7 |
| CA-10: Instruções de port forwarding | Etapa 6 |

---

## Checklist de Aprovação do Plan

- [ ] **Cobre todos os critérios de aceite da spec** — cada CA mapeado para pelo menos uma etapa
- [ ] **Etapas são atômicas e independentes** — cada etapa pode ser implementada e validada isoladamente
- [ ] **Ordem lógica de implementação** — etapas anteriores não dependem de etapas posteriores
- [ ] **Arquivos afetados identificados** — lista completa de arquivos que serão modificados
- [ ] **Resultado esperado é verificável** — cada etapa tem um critério claro de "pronto"
- [ ] **Não viola premissas do context.md** — segue convenções de stack, templates e idempotência
- [ ] **Plano é realista em escopo** — não subestima nem superestima a complexidade

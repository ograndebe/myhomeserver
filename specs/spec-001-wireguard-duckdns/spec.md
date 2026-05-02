# Spec-001 — WireGuard + DuckDNS

> **Status:** done
> **Backlog:** BACK-001
> **Criado em:** 2026-04-30

---

## 1. Visão Geral

Adicionar suporte a DuckDNS como provedor de DNS dinâmico para o WireGuard, permitindo que usuários sem domínio próprio possam acessar seus serviços remotamente através de um subdomínio `.duckdns.org`. O DuckDNS manterá o IP público atualizado automaticamente, e o WireGuard será configurado para usar esse hostname como ponto de entrada da VPN.

O fluxo atual exige um domínio próprio com DNS provider (Cloudflare, Route53). Esta spec adiciona uma alternativa gratuita e simples para quem quer apenas uma VPN funcional com um nome estável para conexão.

---

## 2. Critérios de Aceite

- [ ] **CA-01:** O setup pergunta se o usuário quer usar DuckDNS como alternativa ao domínio próprio
- [ ] **CA-02:** Se DuckDNS for selecionado, o setup pede o token DuckDNS e o subdomínio desejado
- [ ] **CA-03:** O container DuckDNS é adicionado ao docker-compose e atualiza o IP público automaticamente (a cada 5 minutos)
- [ ] **CA-04:** O WireGuard é configurado com `SERVERURL` apontando para `<subdominio>.duckdns.org`
- [ ] **CA-05:** A porta 51820/UDP do WireGuard é exposta no host para port forwarding no router
- [ ] **CA-06:** Os arquivos de configuração gerados para os peers WireGuard contêm o endpoint correto com o hostname DuckDNS
- [ ] **CA-07:** O modo DuckDNS e o modo domínio próprio são mutuamente exclusivos — o setup não permite ambos simultaneamente
- [ ] **CA-08:** Ao re-executar `setup.py`, o token e subdomínio DuckDNS são preservados (idempotência)
- [ ] **CA-09:** O `./setup.py --dry-run` exibe corretamente o contexto com as variáveis DuckDNS
- [ ] **CA-10:** O post-setup e as instruções de next steps mencionam a necessidade de port forwarding no router para a porta 51820/UDP

---

## 3. Fora de Escopo

- Configuração automática de port forwarding no router (UPnP/NAT-PMP) — o usuário deve fazer manualmente
- TLS/HTTPS para serviços via DuckDNS — DuckDNS não suporta wildcard TLS; o foco é apenas a VPN
- Traefik com Let's Encrypt via DuckDNS — sem domínio próprio, o Traefik não emite certificado wildcard
- AdGuard DNS público — AdGuard continua funcionando apenas na rede local
- Authentik — continua provisionado mas acessível apenas via WireGuard (sem TLS público)

---

## 4. Dependências

- **Depende de:** nenhuma
- **Premissas assumidas:**
  - O usuário tem acesso ao router para configurar port forwarding da porta 51820/UDP
  - DuckDNS é gratuito e suporta até 5 subdomínios por conta
  - O WireGuard Linuxserver image suporta `SERVERURL` com hostname dinâmico
  - O IP público do usuário é dinâmico (caso contrário, DuckDNS ainda funciona mas é desnecessário)

---

## 5. Notas Técnicas

### Arquitetura DuckDNS

```
Casa:
  Router → port forward 51820/UDP → servidor (IP local)
  Container duckdns → atualiza IP público a cada 5min via API

Fora de casa:
  Phone → WireGuard → <sub>.duckdns.org:51820
       → router → servidor
       → rede interna (10.13.13.0/24)
       → acessa serviços como se estivesse local
```

### Novo serviço: DuckDNS Updater

```yaml
duckdns:
  image: lscr.io/linuxserver/duckdns:latest
  container_name: duckdns
  environment:
    - PUID=1000
    - PGID=1000
    - SUBDOMAINS=<subdominio>
    - TOKEN=<token>
  restart: unless-stopped
```

### Alterações no WireGuard

- `SERVERURL` muda de `{{ domain }}` para `{{ duckdns_subdomain }}.duckdns.org`
- `SERVERPORT` permanece `51820`
- `PEERDNS` continua apontando para AdGuard local (`{{ local_ip }}`)

### Fluxo de Perguntas (UX)

```
? Como deseja acessar seu servidor remotamente?
  › Meu domínio próprio (Cloudflare, Route53, etc.)
    DuckDNS (gratuito, sem domínio próprio)

Se DuckDNS:
  ? Subdomínio DuckDNS: › meuserver
  ? Token DuckDNS: › xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

  ✔ DuckDNS configurado: meuserver.duckdns.org
  ✔ Porta 51820/UDP será exposta — configure port forwarding no seu router
```

### Arquivos a modificar

| Arquivo | Alteração |
|---------|-----------|
| `config/services.yml` | Adicionar `duckdns` como serviço e `duckdns` como opção de DNS |
| `templates/docker-compose.yml.j2` | Adicionar condicional para DuckDNS + ajustar WireGuard SERVERURL |
| `templates/.env.j2` | Adicionar variáveis `DUCKDNS_SUBDOMAIN` e `DUCKDNS_TOKEN` |
| `setup.py` | Nova pergunta de modo de acesso, validação e contexto |
| `create_data_directories()` | Nenhuma alteração necessária (DuckDNS não persiste dados) |

---

## 6. Checklist de Aprovação da Spec

- [ ] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [ ] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [ ] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [ ] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [ ] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [ ] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [ ] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes

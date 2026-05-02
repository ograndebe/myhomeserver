# Spec-002 — Substituir DuckDNS por Cloudflare DDNS

> **Status:** done
> **Backlog:** —
> **Criado em:** 2026-04-30

---

## 1. Visão Geral

Substituir o uso do DuckDNS como provedor de DNS dinâmico pelo `cloudflare-ddns`, aproveitando o domínio já comprado e gerenciado na Cloudflare. Isso permite que o WireGuard use o mesmo domínio dos demais serviços (ex: `vpn.meudominio.com` ou `meudominio.com`), unificando a infraestrutura de DNS e eliminando a dependência de um serviço externo gratuito.

O DuckDNS foi introduzido como alternativa para usuários sem domínio próprio, mas o pré-requisito atual do projeto já é possuir um domínio na Cloudflare. Manter dois modos de acesso adiciona complexidade desnecessária.

---

## 2. Critérios de Aceite

- [ ] **CA-01:** O setup **não** oferece mais a opção DuckDNS como modo de acesso remoto
- [ ] **CA-02:** O container `cloudflare-ddns` é adicionado ao docker-compose e atualiza o registro DNS `A` do domínio automaticamente
- [ ] **CA-03:** O WireGuard é configurado com `SERVERURL` apontando para o domínio próprio (o mesmo usado pelo Traefik)
- [ ] **CA-04:** As variáveis `DUCKDNS_*` e `USE_DUCKDNS` são removidas do `.env` gerado e do `setup.py`
- [ ] **CA-05:** O `setup.py --dry-run` funciona corretamente sem variáveis DuckDNS no contexto
- [ ] **CA-06:** Ao re-executar `setup.py`, a configuração do cloudflare-ddns é preservada (idempotência)
- [ ] **CA-07:** O `config/services.yml` não contém mais referência ao DuckDNS
- [ ] **CA-08:** Os templates Jinja2 não contêm mais condicionais relacionadas ao DuckDNS

---

## 3. Fora de Escopo

- Alterar a configuração do Traefik ou TLS — já funciona com Cloudflare
- Adicionar suporte a outros provedores de DDNS (ex: Route53, No-IP)
- Modificar a arquitetura de rede (proxy/internal)
- Alterar a configuração do WireGuard além do `SERVERURL`
- Migrar dados ou configurações de peers WireGuard existentes

---

## 4. Dependências

- **Depende de:** spec-001-wireguard-duckdns (que introduziu o modo DuckDNS, agora a ser removido)
- **Premissas assumidas:**
  - O usuário já possui um domínio comprado e gerenciado na Cloudflare
  - O Cloudflare API Token já é coletado pelo setup (para Traefik DNS challenge)
  - O mesmo token pode ser reutilizado para o cloudflare-ddns (permissão `DNS:Edit`)
  - O WireGuard Linuxserver image suporta `SERVERURL` com domínio próprio

---

## 5. Notas Técnicas

### Por que cloudflare-ddns?

O projeto já exige um domínio na Cloudflare para o Traefik (wildcard TLS via DNS challenge). O mesmo API token pode ser usado para manter o registro `A` do domínio atualizado com o IP público dinâmico. Isso elimina:

- Uma dependência externa (DuckDNS)
- Complexidade de dois modos de operação mutuamente exclusivos
- Um container adicional (duckdns updater)

### Container cloudflare-ddns

```yaml
cloudflare-ddns:
  image: oznu/cloudflare-ddns:latest
  container_name: cloudflare-ddns
  environment:
    - API_KEY=${CF_DNS_API_TOKEN}
    - ZONE=${DOMAIN}
    - SUBDOMAIN=   # vazio = domínio apex, ou definir subdomínio se desejado
    - PROXIED=false  # WireGuard precisa de DNS não-proxied (DNS only)
  restart: unless-stopped
  network_mode: host
```

> **Nota:** `network_mode: host` é necessário para que o container detecte o IP público corretamente via `ipinfo.io` ou similar. Alternativamente, pode-se usar um sidecar de detecção de IP.

### WireGuard SERVERURL

- Antes (DuckDNS): `SERVERURL={{ duckdns_subdomain }}.duckdns.org`
- Depois (Cloudflare DDNS): `SERVERURL={{ domain }}`

### Arquivos a modificar

| Arquivo | Alteração |
|---------|-----------|
| `config/services.yml` | Remover `duckdns` como serviço e `duckdns` como opção de acesso |
| `templates/docker-compose.yml.j2` | Remover condicional DuckDNS, adicionar serviço `cloudflare-ddns`, ajustar WireGuard `SERVERURL` |
| `templates/.env.j2` | Remover variáveis `DUCKDNS_*` e `USE_DUCKDNS` |
| `setup.py` | Remover pergunta de modo de acesso, coletar token/subdomínio DuckDNS, e toda lógica condicional relacionada |
| `create_data_directories()` | Nenhuma alteração necessária |

### Fluxo de Perguntas (UX) — simplificado

O setup **não** pergunta mais sobre modo de acesso. O domínio próprio é o único modo suportado:

```
? Domínio (ex: meudominio.com): › meudominio.com
? Cloudflare DNS API Token: › xxxxxxxx
? E-mail Cloudflare: › eu@email.com

✔ Domínio configurado: meudominio.com
✔ Cloudflare DDNS manterá o DNS atualizado automaticamente
```

---

## 6. Bugfixes

- [fix-001-cloudflare-ddns-tag](../fix-001-cloudflare-ddns-tag/spec.md) — Tag `3.1.0` inexistente trocada por `latest` — 2026-05-01

---

## 7. Checklist de Aprovação da Spec

- [ ] **Especifica o QUE, não o COMO** — descreve comportamento desejado, não detalhes de implementação
- [ ] **Critérios de aceite verificáveis** — cada CA pode ser testado manualmente ou automaticamente
- [ ] **Fora de escopo explícito** — delimita claramente o que NÃO será feito
- [ ] **Dependências declaradas** — lista specs, sistemas ou decisões pendentes
- [ ] **Alinhada com context.md** — não viola nenhuma premissa inviolável
- [ ] **Escopo atômico** — uma feature por spec, sem misturar funcionalidades independentes
- [ ] **Notas técnicas justificam decisões** — explica o "porquê" de escolhas técnicas relevantes

# Spec-003 — WireGuard Multi-Device Peer Setup

> **Status:** done
> **Backlog:** —
> **Criado em:** 2026-05-02

---

## 1. Visão Geral

Permitir que o usuário informe uma lista de nomes de devices (separados por vírgula) durante a execução do `setup.py`, para que o script gere previamente as variáveis de ambiente necessárias para cada peer WireGuard no arquivo `output/.env`. Além disso, documentar no `docs/post-setup.md` o procedimento para configurar cada device, incluindo o comando para gerar o QR Code de cada peer.

Atualmente o WireGuard é provisionado com um peer genérico. Esta spec amplia o fluxo para suportar múltiplos devices nomeados (ex: `phone, laptop, tablet`), facilitando a gestão e conexão de cada dispositivo à VPN.

---

## 2. Critérios de Aceite

- [ ] **CA-01:** O setup pergunta ao usuário os nomes dos devices WireGuard (entrada livre, separados por vírgula)
- [ ] **CA-02:** Um valor padrão é sugerido caso o usuário não informe nenhum device (ex: `phone`)
- [ ] **CA-03:** Para cada device informado, variáveis `WIREGUARD_PEER_<NOME>_*` são geradas no `output/.env` (ou equivalente conforme template atual)
- [ ] **CA-04:** Ao re-executar `setup.py`, a lista de devices é preservada se já existir no `.env` (idempotência)
- [ ] **CA-05:** O `./setup.py --dry-run` exibe corretamente o contexto com os devices informados
- [ ] **CA-06:** O `docs/post-setup.md` contém uma seção explicando como gerar o QR Code de cada device
- [ ] **CA-07:** O `docs/post-setup.md` contém instruções de como escanear o QR Code e conectar cada device à VPN
- [ ] **CA-08:** Nomes de devices são normalizados (lowercase, espaços convertidos para underscore, caracteres especiais removidos)

---

## 3. Fora de Escopo

- Geração automática de QR Codes pelo script setup.py — apenas o comando para gerar será documentado
- Rotação automática de chaves ou revogação de peers
- Configuração automática dos devices via MDM ou script de deploy
- Alteração na arquitetura de rede do WireGuard (subnets, routing, etc.)
- Suporte a autenticação adicional por device (certificados, 2FA)

---

## 4. Dependências

- **Depende de:** spec-001-wireguard-duckdns (WireGuard já deve estar provisionado)
- **Premissas assumidas:**
  - O container WireGuard (linuxserver/wireguard) suporta múltiplos peers via variáveis `PEERS` ou configuração individual
  - O arquivo `output/.env` já contém as variáveis base do WireGuard (`WIREGUARD_PUBKEY`, etc.)
  - O `setup.py` já possui mecanismo de input interativo (InquirerPy ou similar)

---

## 5. Notas Técnicas

### Fluxo de Perguntas (UX)

```
? Nomes dos devices para WireGuard (separados por vírgula): › phone, laptop, tablet

  ✔ 3 devices configurados: phone, laptop, tablet
  ✔ Veja docs/post-setup.md para gerar QR Codes de cada device
```

### Variáveis geradas no .env

Para cada device `<nome>` (normalizado), o template `.env.j2` deve gerar:

```
WIREGUARD_PEERS=phone,laptop,tablet
WIREGUARD_PEER_PHONE_PUBKEY=<gerado pelo container>
WIREGUARD_PEER_LAPTOP_PUBKEY=<gerado pelo container>
WIREGUARD_PEER_TABLET_PUBKEY=<gerado pelo container>
```

O container WireGuard linuxserver usa a variável `PEERS` para criar peers automaticamente na primeira inicialização. A abordagem será passar a lista de nomes via `PEERS` no docker-compose.

### Arquivos a modificar

| Arquivo | Alteração |
|---------|-----------|
| `setup.py` | Nova pergunta para lista de devices, normalização, persistência no .env |
| `templates/.env.j2` | Adicionar `WIREGUARD_PEERS={{ wireguard_peers }}` |
| `templates/docker-compose.yml.j2` | Adicionar `PEERS=${WIREGUARD_PEERS}` ao serviço wireguard |
| `docs/post-setup.md` | Adicionar seção "WireGuard — Configurando Devices" com comandos de QR Code |

### Comando para gerar QR Code (documentação)

```bash
docker exec wireguard show-peer <nome-do-device> -q
```

Ou para exibir diretamente no terminal:

```bash
docker exec wireguard show-peer phone | qrencode -t ANSIUTF8
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

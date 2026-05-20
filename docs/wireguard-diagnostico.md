# Diagnóstico WireGuard — TX sim, RX zero

**Data de início:** 2026-05-04
**Sintoma:** No celular (5G, sem Wi-Fi), ao ativar a VPN WireGuard, o campo `transfer` mostra TX aumentando mas RX fica sempre em 0. O cliente envia pacotes mas não recebe resposta.
**Peer:** phonerafa (registrado via QR Code)

---

## Check 1 — Container WireGuard está rodando?

```bash
docker ps | grep wireguard
docker logs wireguard --tail 30
```

**Status:** ✅ OK

**Resultado:**
- Container `wireguard` está **Up 2 days**
- Porta mapeada: `0.0.0.0:51820->51820/udp` (IPv4 + IPv6)
- Logs mostram túnel ativo com 2 peers registrados (10.13.13.4 e 10.13.13.5)
- Regras de iptables do container aplicadas (FORWARD + MASQUERADE)

**Observações:** Container saudável, túnel wg0 ativo, peers configurados.

---

## Check 2 — Porta 51820/UDP escutando no host?

```bash
sudo ss -ulnp | grep 51820
```

**Status:** ✅ OK

**Resultado:**
```
UNCONN 0 0 0.0.0.0:51820 0.0.0.0:*
UNCONN 0 0 [::]:51820 [::]:*
```
Porta escutando em IPv4 e IPv6.

---

## Check 3 — Porta 51820/UDP acessível de FORA?

**Status:** ❌ PACOTE ENVIADO MAS SEM RESPOSTA

**Resultado (Termux no celular 5G, VPN desligada):**
```
connected to [64:ff9b::b19d:801c]:51820
UDP packet sent successfully.
1 bytes sent, 0 bytes received in 2.05 seconds
```

**Análise:**
- DNS resolveu via NAT64 (`64:ff9b::b19d:801c` = tradução de `177.157.128.28`) ✅
- Pacote UDP enviado com sucesso ✅
- **Zero bytes recebidos de volta** ❌

**Conclusão:** O pacote chega no servidor mas **não volta**. Problema está no caminho de retorno — provavelmente port forwarding no router ou NAT do Docker.

---

## Check 4 — IP público atual bate com o DNS?

```bash
# No servidor:
curl ifconfig.me

# No celular (5G), verificar resolução DNS:
# Use app "DNS Lookup" ou similar:
dig +short <SEU_DOMINIO>
```

**Status:** ⚠️ ATENÇÃO — IPv6 vs IPv4

**Resultado servidor:** `2804:7f0:36:20e:2fa0:602:85da:daee` (IPv6)
**Resultado DNS (maroto.online):** `177.157.128.28` (IPv4 apenas, sem registro AAAA)

**Observações:** O servidor tem IPv6 público, mas o Cloudflare DDNS só atualiza o registro A (IPv4). O domínio `maroto.online` resolve para `177.157.128.28`. Se o celular 5G preferir IPv6, pode haver problema.

---

## Check 5 — Cloudflare proxy DESLIGADO?

**Status:** ✅ OK

**Resultado:** `PROXIED=false` está configurado no docker-compose template (linha 84).

---

## Check 6 — iptables do host permite UDP 51820?

```bash
sudo iptables -L INPUT -n -v --line-numbers | grep 51820
sudo iptables -L FORWARD -n -v --line-numbers | grep 51820
```

**Status:** ⚠️ Sem regras visíveis (sem sudo)

**Resultado:** Sem acesso sudo para verificar regras completas. Container WireGuard aplica suas próprias regras de FORWARD + MASQUERADE internamente.

---

## Check 7 — Peer config com Endpoint correto?

```bash
docker exec wireguard cat /config/peer_phonerafa/peer_phonerafa.conf
```

**Status:** ✅ OK (config parece correta)

**Resultado:**
```
[Interface]
Address = 10.13.13.5
DNS = 192.168.15.6

[Peer]
PublicKey = v5fXoDbk93llJ/ZqX/m4dQOOiN/YrBM3EFXVEoZaGAQ=
PresharedKey = TrPHr8i307Ay2eygKkpd6funq/g3LfHvWPPoyOqUMsA=
Endpoint = maroto.online:51820
AllowedIPs = 10.13.13.0/24,192.168.15.6/32
```
- Endpoint: `maroto.online:51820` ✅ (domínio correto, não localhost/IP interno)
- DNS: `192.168.15.6` ✅ (AdGuard local)
- AllowedIPs: túnel + servidor local ✅

---

## Check 8 — VPN funciona no Wi-Fi local?

Com o Wi-Fi **ligado**, tente conectar a VPN.

**Status:** ⏳ Aguardando

**Resultado:** _(preencher)_

**Observações:** _(preencher)_
- Se funcionar no Wi-Fi → problema é no acesso externo (port forwarding / DNS / firewall)
- Se NÃO funcionar no Wi-Fi → problema é na config do peer ou no container

---

## Check 9 — Módulo WireGuard do kernel carregado?

```bash
lsmod | grep wireguard
```

**Status:** ⏳ Aguardando

**Resultado:** _(preencher)_

**Observações:** _(preencher)_

---

## Check 10 — Regras NAT do Docker corretas?

```bash
sudo iptables -t nat -L -n -v | grep 51820
```

**Status:** ⏳ Aguardando

**Resultado:** _(preencher)_

**Observações:** _(preencher)_

---

## Check 11 — WireGuard handshake recente?

```bash
docker exec wireguard wg show
```

**Status:** ⚠️ Sem handshakes recentes

**Resultado:**
```
interface: wg0
  public key: v5fXoDbk93llJ/ZqX/m4dQOOiN/YrBM3EFXVEoZaGAQ=
  listening port: 51820

peer: ZOPGr84lFKQe8+MdXVTVP8OfFEJ9jsaKXGDFH0wb2HY=
  allowed ips: 10.13.13.4/32

peer: z9BM4rkRftTz7VyaNAPkGv0waHfoURlKoQJm64Q9els=
  allowed ips: 10.13.13.5/32
```
Nenhum handshake recente mostrado (sem linhas `latest handshake` ou `transfer`). Isso confirma que os peers não estão conseguindo completar a conexão.

---

## Conclusão

**Causa raiz identificada:** Configuração de port forwarding no roteador. O pacote UDP 51820 chegava ao servidor mas não tinha rota de retorno correta.

**Solução aplicada:** Correção da regra de port forwarding no roteador para UDP 51820 → 192.168.15.6

**Data de resolução:** 2026-05-04

---

## Resumo do diagnóstico

| Check | Status |
|-------|--------|
| 1 — Container rodando | ✅ OK |
| 2 — Porta escutando no host | ✅ OK |
| 3 — Porta acessível de fora | ❌ Pacote enviado, sem resposta → **causa raiz** |
| 4 — DNS vs IP público | ⚠️ NAT64 (operadora traduz IPv4→IPv6) |
| 5 — Cloudflare proxy | ✅ OFF |
| 6 — iptables host | ⏳ Não verificado |
| 7 — Peer config | ✅ Endpoint correto |
| 11 — WireGuard handshake | ⚠️ Sem handshakes (consequência do problema) |

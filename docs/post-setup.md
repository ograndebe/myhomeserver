# Pós-Setup — Instruções de Configuração

Após executar `./setup.py` e `docker compose -f output/docker-compose.yml up -d`,
siga os passos abaixo para completar a configuração.

---

## 1. AdGuard — Setup inicial

Na primeira execução, o AdGuard precisa ser configurado via wizard:

1. Acesse `http://IP_DO_SERVIDOR:3000`
2. Siga o wizard de configuração
3. Defina usuário e senha de admin
4. O arquivo `output/adguard/AdGuardHome.yaml` já inclui o rewrite DNS para `*.seudominio.com`

**Rewrite DNS configurado automaticamente:**
```
*.seudominio.com → IP local do servidor
```

Isso garante que todo tráfego para seus serviços fique dentro da rede local,
mesmo usando um domínio público com certificado TLS válido.

**Configure seu roteador** para usar o IP do servidor como servidor DNS primário.
Isso direciona todos os dispositivos da rede para o AdGuard automaticamente.

---

## 2. Traefik — Verificar certificados

Após o primeiro boot, verifique se o Traefik emitiu o certificado wildcard:

```bash
# Ver logs do Traefik
docker logs traefik -f

# O certificado é salvo em:
# output/traefik/acme/acme.json
```

Se houver erros no desafio DNS, verifique as credenciais no `.env`.

---

## 3. Authentik — Configuração inicial

Veja `docs/authentik-setup.md` para o guia completo.

Resumo:
1. Acesse `https://auth.seudominio.com/if/flow/initial-setup/`
2. Crie o usuário admin
3. Configure os provedores para cada serviço

---

## 4. WireGuard — Configuração dos clientes

Os arquivos de configuração dos peers são gerados em:
```
output-data/wireguard/config/peer_*/
```

Para cada peer há um arquivo `.conf` e um QR code `.png`.

**No celular:** abra o app WireGuard → escaneie o QR code
**No computador:** importe o arquivo `.conf` no app WireGuard

O DNS do WireGuard está configurado para apontar para o AdGuard interno,
então os nomes de domínio funcionam normalmente com a VPN ativa.

---

## 5. URLs dos serviços

| Serviço     | URL                              |
|-------------|----------------------------------|
| Traefik     | `https://traefik.seudominio.com` |
| AdGuard     | `https://dns.seudominio.com`     |
| Authentik   | `https://auth.seudominio.com`    |
| Jellyfin    | `https://jellyfin.seudominio.com`|
| Radarr      | `https://radarr.seudominio.com`  |
| Sonarr      | `https://sonarr.seudominio.com`  |
| Prowlarr    | `https://prowlarr.seudominio.com`|
| qBittorrent | `https://qbit.seudominio.com`    |
| Bazarr      | `https://bazarr.seudominio.com`  |
| Nextcloud   | `https://nextcloud.seudominio.com`|
| Immich      | `https://photos.seudominio.com`  |

---

## 6. Estrutura de diretórios criada em STORAGE_PATH

```
/opt/homeserver/data/       (ou o caminho que você definiu)
├── traefik/acme/           → certificados TLS
├── authentik/media/        → uploads e avatares
├── wireguard/config/       → configs e QR codes dos peers
├── adguard/work/           → dados do AdGuard
├── jellyfin/config/
├── media/
│   ├── movies/             → Radarr deposita filmes aqui
│   ├── shows/              → Sonarr deposita séries aqui
│   └── music/
├── downloads/              → qBittorrent baixa aqui
├── radarr/config/
├── sonarr/config/
├── prowlarr/config/
├── qbittorrent/config/
├── bazarr/config/
├── nextcloud/data/
└── immich/upload/
```

---

## 7. Manutenção

**Atualizar imagens:**
```bash
docker compose -f output/docker-compose.yml pull
docker compose -f output/docker-compose.yml up -d
```

**Recriar configuração:**
```bash
./setup.py
docker compose -f output/docker-compose.yml up -d --force-recreate
```

**Backup dos dados:**
Os dados persistentes estão todos em `STORAGE_PATH`. Faça backup deste diretório
e dos arquivos em `output/` (exceto `.env` — guarde-o separadamente e com segurança).

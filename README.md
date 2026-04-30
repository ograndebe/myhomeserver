# Homeserver

Setup reproduzível de home server com Docker Compose.
Clone, responda algumas perguntas, suba os serviços.

## Pré-requisitos

- Linux (Ubuntu 22.04+ recomendado)
- Docker + Docker Compose
- Domínio real com acesso ao painel DNS
- [`uv`](https://docs.astral.sh/uv/) instalado

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Uso

```bash
git clone git@github.com:usuario/homeserver
cd homeserver
chmod +x setup.py
./setup.py

# Sobe os containers e configura o Authentik automaticamente:
./post-setup.sh
```

> **Nota:** O script `post-setup.sh` substitui o comando manual `docker compose up -d`
> e configura automaticamente o Authentik com SSO para todos os serviços.

## Serviços incluídos

### Obrigatórios
| Serviço     | Função                                              | URL                     |
|-------------|-----------------------------------------------------|-------------------------|
| Traefik     | Reverse proxy + TLS automático (wildcard)           | `traefik.dominio.com`   |
| AdGuard     | DNS local — resolve `*.dominio.com` para IP interno | `dns.dominio.com`       |
| WireGuard   | VPN — acesso externo como se estivesse na rede      | porta UDP 51820         |
| Authentik   | SSO centralizado para todos os serviços             | `auth.dominio.com`      |

### Opcionais (selecionáveis no setup)
| Serviço                  | Função                                       | URL                        |
|--------------------------|----------------------------------------------|----------------------------|
| Jellyfin                 | Media server                                 | `jellyfin.dominio.com`     |
| Radarr                   | Automação de filmes                          | `radarr.dominio.com`       |
| Sonarr                   | Automação de séries                          | `sonarr.dominio.com`       |
| Prowlarr                 | Indexador central                            | `prowlarr.dominio.com`     |
| qBittorrent              | Cliente de download                          | `qbit.dominio.com`         |
| Bazarr                   | Download automático de legendas              | `bazarr.dominio.com`       |
| Nextcloud                | Storage, calendário, documentos              | `nextcloud.dominio.com`    |
| Immich                   | Galeria e backup de fotos                    | `photos.dominio.com`       |

> Jellyfin inclui a stack *arr completa automaticamente.

## Como funciona o acesso por nome

```
Na rede local (sem VPN):
  Browser → nextcloud.dominio.com
         → AdGuard resolve para o IP interno
         → Traefik roteia para o container
         → TLS válido (Let's Encrypt wildcard)

De fora (com WireGuard):
  Dispositivo → VPN → rede interna → mesmo fluxo
```

## Documentação

- `docs/post-setup.md` — configuração pós-instalação
- `docs/authentik-setup.md` — integração SSO com cada serviço
- `CONTEXT.md` — especificação técnica completa do projeto

## Recriar configuração

```bash
./setup.py
docker compose -f output/docker-compose.yml up -d --force-recreate
```

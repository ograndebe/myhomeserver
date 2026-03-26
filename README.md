# 🏠 Home Server Stack

Projeto de infraestrutura para home server baseado em Docker, com roteamento por subdomínio, HTTPS automático via Let's Encrypt e VPN para acesso externo.

## Visão Geral

```
Internet
    │
    ▼ (porta 51820/UDP)
[WireGuard] ─── VPN para dispositivos externos
    │
    ▼
[Traefik] ─── Reverse proxy + TLS automático
    │
    ├── app1.seudominio.com
    ├── app2.seudominio.com
    ├── adguard.seudominio.com
    └── traefik.seudominio.com (dashboard)

[AdGuard Home] ─── DNS local com wildcard
    └── *.seudominio.com → IP do servidor
```

### Componentes

| Serviço | Função |
|---|---|
| **Traefik** | Reverse proxy central. Roteia por subdomínio via labels Docker. Emite e renova certificados TLS automaticamente. |
| **AdGuard Home** | DNS local. Resolve `*.seudominio.com` para o IP interno do servidor, permitindo que dispositivos da rede usem HTTPS sem expor nada à internet. |
| **WireGuard** | VPN leve. Expõe uma única porta UDP. Clientes externos se conectam e passam a usar o AdGuard como DNS, operando como se estivessem na rede local. |
| **app1 / app2** | Webservers Nginx de demonstração para validar o roteamento por subdomínio. Substituir por serviços reais nas próximas iterações. |

## Pré-requisitos

- Docker e Docker Compose instalados no servidor
- Domínio real apontado para o Cloudflare (para o DNS Challenge do Let's Encrypt)
- Token da API do Cloudflare com permissão `Zone / DNS / Edit`

> **Por que Cloudflare?**  
> O Let's Encrypt emite certificados wildcard (`*.seudominio.com`) via DNS Challenge — sem precisar abrir a porta 80 para a internet. O Traefik suporta vários provedores DNS; Cloudflare é o padrão deste projeto. Para trocar, edite `dnsChallenge.provider` em `src/traefik/traefik.yml`.

## Estrutura do Projeto

```
homeserver/
├── build.sh              ← Script de build (rode aqui)
├── .gitignore
├── README.md
└── src/                  ← Templates com placeholders
    ├── .env
    ├── docker-compose.yml
    └── traefik/
        └── traefik.yml
```

Após o build:

```
homeserver/
├── build/                ← Artefato pronto para deploy (git-ignored)
│   ├── .env              ← Preenchido com domínio, IP e senhas
│   ├── docker-compose.yml
│   └── traefik/
│       └── traefik.yml
└── credentials.txt       ← Senhas geradas (git-ignored, guarde com segurança)
```

## Como Usar

### 1. Preparar o servidor

Libere a porta 53 sem desabilitar o `systemd-resolved`:

```bash
sudo sed -i 's/#DNSStubListener=yes/DNSStubListener=no/' /etc/systemd/resolved.conf
sudo systemctl restart systemd-resolved
```

### 2. Gerar o artefato de build

Na sua máquina local (ou diretamente no servidor):

```bash
./build.sh
```

O script irá perguntar:
- Domínio (ex: `meuserver.com.br`)
- IP local do servidor (ex: `192.168.1.100`)
- E-mail para Let's Encrypt
- Cloudflare API Token
- Usuário do Traefik Dashboard

Senhas são geradas automaticamente e salvas em `credentials.txt`.

### 3. Deploy no servidor

```bash
# Copie a pasta build/ para o servidor
scp -r build/ usuario@192.168.1.100:~/homeserver

# No servidor
cd ~/homeserver
docker compose up -d
```

### 4. Configurar AdGuard Home

1. Acesse `http://IP-DO-SERVIDOR:3000` para o setup inicial
2. Configure a senha admin (use a de `credentials.txt`)
3. Vá em **Filters → DNS Rewrites** e adicione:
   - Domínio: `*.seudominio.com`
   - Resposta: `192.168.1.X` (IP do servidor)
4. Após configurado, feche a porta 3000 removendo-a do `docker-compose.yml`

### 5. Configurar DNS na rede

No roteador (DHCP settings), aponte o DNS primário para o IP do servidor.  
Todos os dispositivos da casa passarão a usar o AdGuard automaticamente.

### 6. Configurar WireGuard (acesso externo)

Os arquivos de configuração para cada peer são gerados automaticamente em:
```
build/wireguard/peer1/peer1.conf
build/wireguard/peer2/peer2.conf
...
```

Importe o arquivo `.conf` no cliente WireGuard do dispositivo externo. O DNS do túnel já vem apontado para o AdGuard, então `*.seudominio.com` funciona fora de casa igual a dentro.

## Adicionando Novos Serviços

Para adicionar um serviço (ex: Nextcloud), basta incluir no `src/docker-compose.yml` com as labels do Traefik:

```yaml
nextcloud:
  image: nextcloud
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.nextcloud.rule=Host(`nextcloud.${DOMAIN}`)"
    - "traefik.http.routers.nextcloud.entrypoints=websecure"
    - "traefik.http.routers.nextcloud.tls.certresolver=letsencrypt"
    - "traefik.http.services.nextcloud.loadbalancer.server.port=80"
  networks:
    - proxy
```

Nenhuma outra configuração é necessária — o certificado wildcard já cobre o novo subdomínio.

## Segurança

- `credentials.txt` e `build/` estão no `.gitignore`. **Nunca commite senhas.**
- O WireGuard expõe apenas a porta `51820/UDP`. Nenhuma outra porta precisa estar aberta no roteador.
- O Let's Encrypt usa DNS Challenge — a porta 80 **não** precisa ser exposta à internet.
- O Traefik Dashboard é protegido por autenticação básica.

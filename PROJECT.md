# Home Server Provisioning Tool

## 1. Visão Geral

Este projeto tem como objetivo construir uma **ferramenta de provisionamento** para home servers. A ferramenta consiste em um conjunto de scripts shell e templates que, quando executados, geram um diretório `build/` contendo todos os artefatos necessários para subir ou reiniciar um home server funcional.

O foco é **reprodutibilidade**: executar a ferramenta deve resultar no mesmo estado configurado, independentemente de quantas vezes seja repetida ou em qual servidor seja aplicada.

---

## 2. Objetivo Principal

Construir uma ferramenta CLI que:

1. Executa localmente (ambiente de desenvolvimento)
2. Gera artefatos de infraestrutura na pasta `build/`
3. Os artefatos podem ser transferidos para qualquer servidor Ubuntu
4. No servidor, um único comando (`docker compose up -d`) sobe o home server completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RESULTADO DA FERRAMENTA                       │
├─────────────────────────────────────────────────────────────────────┤
│  ./build/                                                            │
│  ├── .env                    # Variáveis de ambiente (senhas, IPs)  │
│  ├── docker-compose.yml      # Orquestração dos serviços            │
│  ├── traefik/                # Configuração do reverse proxy         │
│  │   └── traefik.yml                                                 │
│  ├── wireguard/              # Configuração da VPN                  │
│  │   └── wg0.conf                                                   │
│  ├── adguard/                # Configuração do DNS local           │
│  └── credentials.txt          # Credenciais geradas (não commitar)   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Ambientes

### 3.1 Ambiente de Desenvolvimento

| Atributo | Valor |
|----------|-------|
| **Plataforma** | macOS |
| **Hardware** | Apple Silicon (M1/M2/M3) |
| **Arquitetura** | ARM64 (aarch64) |
| **Função** | Build dos artefatos |
| **Limitações** | Não pode executar binários x86_64 diretamente |

### 3.2 Ambiente de Testes/Produção

| Atributo | Valor |
|----------|-------|
| **Plataforma** | Ubuntu Linux |
| **Hardware** | VPS ou hardware dedicado |
| **Arquitetura** | x86_64 (amd64) |
| **Função** | Execução dos artefatos (home server) |

### 3.3 Diagrama de Ambientes

```
┌──────────────────────────────────────────────────────────────────────┐
│                         AMBIENTE DE DESENVOLVIMENTO                   │
│                                                                      │
│  MacBook Apple Silicon (ARM64)                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  $ ./build.sh                                                 │   │
│  │                                                               │   │
│  │  1. Coleta configurações (domínio, IP, credenciais)          │   │
│  │  2. Gera senhas aleatórias seguras                           │   │
│  │  3. Processa templates com variáveis                          │   │
│  │  4. Output: pasta build/ com artefatos prontos                │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              │ scp -r build/ user@server:~/          │
│                              ▼                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────┼───────────────────────────────────────┐
│                         AMBIENTE DE PRODUÇÃO                          │
│                              │                                       │
│  Ubuntu Linux x86_64                                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  $ cd ~/build && docker compose up -d                        │   │
│  │                                                               │   │
│  │  1. Valida configurações                                     │   │
│  │  2. Baixa imagens Docker                                     │   │
│  │ 3. Sobe contêineres                                          │   │
│  │  4. Home server operacional                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Arquitetura do Sistema

### 4.1 Componentes do Home Server

```
                    ┌─────────────────────────────────────────┐
                    │              INTERNET                    │
                    └─────────────────┬───────────────────────┘
                                      │
                                      │ Porta 443 (HTTPS)
                                      │ Porta 51820/UDP (WireGuard)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SERVIDOR UBUNTU                                 │
│                                                                         │
│   ┌─────────────┐      ┌─────────────────────────────────────────┐    │
│   │  WireGuard  │      │              TRAEFIK                     │    │
│   │    VPN      │      │         Reverse Proxy + TLS             │    │
│   │ 51820/UDP   │      │         (Let's Encrypt Wildcard)        │    │
│   └──────┬──────┘      └──────────────────┬────────────────────────┘    │
│          │                                │                              │
│          │                          ┌─────┴─────┐                         │
│          │                          │           │                         │
│          ▼                          ▼           ▼                         │
│   ┌─────────────┐          ┌────────────┐ ┌────────────┐                  │
│   │  AdGuard    │          │  Serviço 1 │ │  Serviço 2 │                  │
│   │   Home      │          │  (Nginx)  │ │ (Nginx)   │                  │
│   │  DNS Local  │          └────────────┘ └────────────┘                  │
│   │  porta 53   │                                                       │
│   └─────────────┘                                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Roteamento por Subdomínio

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RESOLUÇÃO DE SUBDOMÍNIOS                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   *.seudominio.com ──→ Cloudflare DNS ──→ IP Público do Servidor       │
│                                                                         │
│   ├── app1.seudominio.com ──→ Traefik ──→ app1:80                    │
│   ├── app2.seudominio.com ──→ Traefik ──→ app2:80                    │
│   ├── adguard.seudominio.com ──→ Traefik ──→ adguard:3000            │
│   └── traefik.seudominio.com ──→ Traefik ──→ Dashboard (protegido)   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Fluxo de Trabalho

### 5.1 Processo de Build (MacBook)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            BUILD.SH                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INÍCIO                                                                │
│    │                                                                   │
│    ▼                                                                   │
│  ┌──────────────────────────────┐                                      │
│  │ 1. Coleta de Inputs          │                                      │
│  │    - Domínio (ex: server.com)│                                      │
│  │    - IP local do servidor     │                                      │
│  │    - Email (Let's Encrypt)   │                                      │
│  │    - Cloudflare API Token     │                                      │
│  │    - Credenciais admin        │                                      │
│  └──────────────┬───────────────┘                                      │
│                 │                                                      │
│                 ▼                                                      │
│  ┌──────────────────────────────┐                                      │
│  │ 2. Geração de Segredos      │                                      │
│  │    - WireGuard chaves        │                                      │
│  │    - Senhas aleatórias       │                                      │
│  │    - Credenciais salvas em   │                                      │
│  │      credentials.txt         │                                      │
│  └──────────────┬───────────────┘                                      │
│                 │                                                      │
│                 ▼                                                      │
│  ┌──────────────────────────────┐                                      │
│  │ 3. Processamento de          │                                      │
│  │    Templates                │                                      │
│  │    - Substitui {{VARIAVEIS}} │                                      │
│  │    - Gera .env, docker-      │                                      │
│  │      compose.yml, configs    │                                      │
│  └──────────────┬───────────────┘                                      │
│                 │                                                      │
│                 ▼                                                      │
│  ┌──────────────────────────────┐                                      │
│  │ 4. Output: /build/          │                                      │
│  │    ├── .env                 │                                      │
│  │    ├── docker-compose.yml   │                                      │
│  │    ├── traefik/             │                                      │
│  │    ├── wireguard/           │                                      │
│  │    └── adguard/             │                                      │
│  └──────────────┬───────────────┘                                      │
│                 │                                                      │
│                 ▼                                                      │
│               FIM                                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Processo de Deploy (Servidor Ubuntu)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            DEPLOY                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  $ scp -r ./build user@192.168.1.100:~/homeserver                       │
│                                                                         │
│  ssh user@192.168.1.100                                                 │
│    │                                                                   │
│    ▼                                                                   │
│  $ cd ~/homeserver                                                      │
│    │                                                                   │
│    ▼                                                                   │
│  $ docker compose up -d                                                 │
│    │                                                                   │
│    ▼                                                                   │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │ Valida config       │ Baixa imagens │ Sobe contêineres       │     │
│  └───────────────────────────────────────────────────────────────┘     │
│    │                                                                   │
│    ▼                                                                   │
│  Home Server Operacional                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Entregáveis

### 6.1 Artefatos do Build

| Artefato | Descrição | Sensível |
|----------|-----------|----------|
| `build/.env` | Variáveis de ambiente (domínio, IPs, portas) | Parcial |
| `build/credentials.txt` | Senhas e chaves geradas | **Sim** |
| `build/docker-compose.yml` | Definição de todos os serviços | Não |
| `build/traefik/traefik.yml` | Configuração do reverse proxy | Não |
| `build/wireguard/*.conf` | Configurações dos peers VPN | **Sim** |
| `build/adguard/*.conf` | Configuração inicial do AdGuard | Não |

### 6.2 Estrutura de Diretórios do Build

```
build/
├── .env
├── docker-compose.yml
├── traefik/
│   └── traefik.yml
├── wireguard/
│   ├── wg0.conf
│   └── peer1/
│       └── peer1.conf
├── adguard/
│   └── AdGuard.yml
└── nginx/
    ├── app1.conf
    └── app2.conf
```

---

## 7. Restrições e Premissas

### 7.1 Restrições Técnicas

1. **Incompatibilidade de arquitetura**: MacBook ARM64 ≠ Ubuntu x86_64
   - Não é possível executar contêineres ou binários do servidor localmente
   - O build gera apenas arquivos de configuração, não executa nada direcionado ao servidor

2. **Ambiente de testes limitado**: 
   - Testes locais são restritos a validação de sintaxe (shellcheck, yamllint)
   - Testes funcionais requerem acesso ao servidor Ubuntu

3. **Dependência de Cloudflare**:
   - Let's Encrypt wildcard certificate requer DNS Challenge
   - Cloudflare é o provedor padrão (suporte a outros é secundário)

### 7.2 Premissas

1. **Servidor limpo**: Assume Ubuntu Server recém-instalado com Docker e Docker Compose

2. **Docker instalado**:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```

3. **Portas disponíveis**:
   - 443 (HTTPS)
   - 51820/UDP (WireGuard)
   - 53/UDP (AdGuard DNS)

4. **Domínio configurado**: 
   - Domínio registrado e gerenciado no Cloudflare
   - Zona DNS configurável via API

5. **Rede**:
   - Servidor com IP fixo ou reserva DHCP
   - Acesso SSH do MacBook ao servidor

### 7.3 Não Escopo

- Provisionamento de hardware/servidor
- Instalação do sistema operacional Ubuntu
- Instalação do Docker
- Gerenciamento de containers após deploy
- Monitoramento contínuo
- Backup dos dados

---

## 8. Tecnologias Candidatas

| Componente | Tecnologia | Status |
|------------|------------|--------|
| Orquestração | Docker Compose | Confirmado |
| Reverse Proxy | Traefik | Confirmado |
| VPN | WireGuard | Confirmado |
| DNS Local | AdGuard Home | Confirmado |
| Certificados | Let's Encrypt (DNS Challenge) | Confirmado |
| Automação | Shell Script (bash) | Confirmado |
| Provisionamento | Ansible | Em avaliação |

---

## 9. Critérios de Sucesso

- [ ] `./build.sh` executa sem erros no MacBook
- [ ] Pasta `build/` contém todos os artefatos necessários
- [ ] `scp -r build/ user@server:~` transfere os arquivos
- [ ] `docker compose up -d` sobe o home server
- [ ] Traefik responde em `https://seudominio.com`
- [ ] Certificados TLS são emitidos e renovados automaticamente
- [ ] WireGuard aceita conexões de clientes externos
- [ ] AdGuard resolve `*.seudominio.com` para o IP interno
- [ ] Processo é idempotente (executar múltiplas vezes não quebra)

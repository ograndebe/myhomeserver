# Análise e Recomendações para Home Server Personalizado

## Visão Geral do Projeto MediaStack

O projeto MediaStack atual contém **54 containers** diferentes, cobrindo desde servidores de mídia até ferramentas de desenvolvimento, monitoramento e segurança. Para um home server pessoal com acesso local via VPN, muitos destes containers são desnecessários.

## Análise dos Containers por Categoria

### 🎬 **MÍDIA E ENTRETENIMENTO** (Essencial para Home Server)

#### ✅ **RECOMENDADOS MANTER:**
- **Jellyfin** - Servidor de mídia open source (alternativa ao Plex)
- **Jellyseerr** - Sistema de requisição de mídia para Jellyfin
- **Plex** - Servidor de mídia popular (opcional, escolha um: Jellyfin OU Plex)
- **Bazarr** - Download automático de legendas para filmes/series
- **Lidarr** - Gerenciador de músicas
- **Radarr** - Gerenciador de filmes
- **Sonarr** - Gerenciador de séries
- **Readarr** - Gerenciador de ebooks/comics
- **Mylar** - Gerenciador de quadrinhos

#### ❌ **REMOVER:**
- **Whisparr** - Gerenciador de conteúdo adulto (remover para uso familiar)

### 📥 **DOWNLOAD E AUTOMAÇÃO** (Depende da necessidade)

#### ✅ **RECOMENDADOS MANTER (essencial com *ARR apps):**
- **qBittorrent** - Cliente torrent (essencial para downloads)
- **SABnzbd** - Cliente Usenet (opcional, só se usa Usenet)
- **Prowlarr** - Gerenciador de indexadores (essencial para *ARR apps)
- **Unpackerr** - Extrai arquivos baixados automaticamente
- **Tdarr** - Transcodificação de mídia (opcional, só se precisa converter formatos)
- **Huntarr** - Busca mídia faltante (útil para *ARR apps)
- **Filebot** - Organização de arquivos (útil mas pode ser manual)

#### ❌ **REMOVER:**
- Nenhum (todos são úteis com o ecossistema *ARR)

### 🌐 **ACESSO E VPN** (Essencial para seu caso de uso)

#### ✅ **RECOMENDADOS MANTER:**
- **Headscale** - Servidor VPN auto-hospedado (essencial para acesso externo)
- **Headplane** - Interface web para Headscale (facilita gerenciamento)
- **Traefik** - Reverse proxy com SSL (essencial para acesso local com nomes)

#### ❌ **REMOVER (não precisa para acesso local):**
- **Tailscale** - Serviço VPN comercial (use Headscale que é auto-hospedado)
- **DDNS-Updater** - Atualização DNS dinâmico (comentado para uso futuro)

#### ✅ **MANTER (comentado para uso futuro):**
- **Gluetun** - VPN para downloads (comentado, ativar após setup funcional)

### 🏠 **DASHBOARDS E ORGANIZAÇÃO** (Útil para organização)

#### ✅ **RECOMENDADOS MANTER:**
- **Heimdall** - Dashboard para organizar aplicativos
- **Homarr** - Dashboard alternativo (mais moderno)
- **Homepage** - Dashboard simples e rápido ← **ESCOLHIDO**

#### ❌ **REMOVER:**
- Manter apenas Homepage, remover Heimdall e Homarr

### 🔐 **SEGURANÇA E AUTENTICAÇÃO** (Depende da necessidade)

#### ✅ **RECOMENDADOS MANTER:**
- **Traefik** - Já incluído, essencial
- **CrowdSec** - Firewall/IPS (útil para segurança)
- **Authentik** - SSO para autenticação centralizada

#### ❌ **REMOVER:**
- **Traefik-Certs-Dumper** - Não precisa se não expor online

### 🖥️ **FERRAMENTAS DE DESENVOLVIMENTO/ADMIN** (Remover maioria)

#### ❌ **REMOVER (não precisa para home server):**
- **Guacamole** - Acesso remoto via web (use SSH direto)
- **Chromium** - Navegador via Docker (desnecessário)
- **Portainer** - Interface Docker (use CLI)
- **Flaresolverr** - Bypass Cloudflare (só para web scraping)

### 📊 **MONITORAMENTO E BANCO DE DADOS** (Essencial para *ARR apps)

#### ✅ **RECOMENDADOS MANTER:**
- **Postgresql** - Essencial para *ARR apps e outros serviços
- **Valkey** - Cache/Redis (útil para alguns apps e performance)

#### ❌ **REMOVER:**
- **Grafana** - Monitoramento complexo demais
- **Prometheus** - Coleta de métricas (desnecessário)

## Configuração Recomendada para Home Server

### 📋 **Lista Final de Containers (20-25 containers):**

#### Essenciais:
1. **Traefik** - Reverse proxy e SSL
2. **Headscale** - Servidor VPN
3. **Headplane** - Interface Headscale
4. **Jellyfin** (ou Plex) - Servidor de mídia
5. **Homepage** - Dashboard ← **ESCOLHIDO**
6. **Authentik** - SSO para autenticação centralizada

#### Ecossistema *ARR (essencial para automação):
7. **Radarr** - Filmes
8. **Sonarr** - Séries
9. **Lidarr** - Músicas
10. **Readarr** - Ebooks/Comics
11. **Mylar** - Quadrinhos
12. **Prowlarr** - Indexadores
13. **qBittorrent** - Downloads torrent
14. **Unpackerr** - Extração automática

#### Complementos úteis:
15. **Jellyseerr** - Requisições de mídia
16. **Bazarr** - Legendas automáticas
17. **Huntarr** - Busca mídia faltante
18. **Tdarr** - Transcodificação (opcional)
19. **Filebot** - Organização de arquivos (opcional)
20. **SABnzbd** - Downloads Usenet (opcional)
21. **CrowdSec** - Segurança adicional

#### Infraestrutura:
22. **Postgresql** - Banco de dados
23. **Valkey** - Cache/Redis

#### Futuro (comentado):
24. **Gluetun** - VPN para downloads (ativar após setup)
25. **DDNS-Updater** - DNS dinâmico (ativar se expor online)

## Configuração de Rede Recomendada

### 🏠 **Acesso Local:**
- Use **DNS local** (ex: `pi-hole` ou configurado no roteador)
- Nomes como: `jellyfin.local`, `heimdall.local`, etc.
- Traefik vai gerenciar os certificados SSL auto-assinados

### 🌐 **Acesso Externo:**
- **Headscale** para VPN ( WireGuard-based)
- Conecte à VPN de fora de casa
- Acesse tudo como se estivesse na rede local

## Estrutura de Pastas Sugerida

```
my-home-server/
├── docker-compose.yml
├── .env
├── traefik/
│   ├── static.yaml
│   ├── dynamic.yaml
│   └── letsencrypt/
├── headscale/
│   └── config.yaml
└── data/
    ├── jellyfin/
    ├── qbittorrent/
    ├── heimdall/
    └── ...
```

## Vantagens Desta Abordagem:

✅ **Completo:** Ecossistema *ARR completo para automação de mídia  
✅ **Organizado:** Dashboard centralizado para todos os serviços  
✅ **Seguro:** Acesso apenas via VPN local, nada exposto  
✅ **Performance:** Foco nos apps que realmente usa  
✅ **Manutenível:** 22 containers vs 54 originais (60% de redução)  
✅ **Flexível:** Remove apenas complexidade desnecessária  
✅ **Economia:** Menos recursos consumidos  

## Impacto da Mudança:

**Redução de 54 para 25 containers** (54% de redução):
- Mantém toda a funcionalidade de mídia e automação
- Adiciona Authentik para autenticação centralizada
- Remove apenas ferramentas corporativas desnecessárias
- Foco em uso pessoal com segurança e organização
- Infraestrutura robusta mas simplificada  

## Por Que Manter Authentik?

### ❌ **Argumento Contra (complexidade):**
- SSO pode parecer excessivo para uso pessoal
- Configuração inicial mais complexa
- Requer banco de dados e cache adicional

### ✅ **Argumento A Favor (vantagens reais):**

**1. Autenticação Centralizada Real:**
- Um único login para TODOS os serviços (Jellyfin, *ARR apps, etc.)
- Não precisa lembrar senhas diferentes para cada app
- MFA (2FA) centralizado para todos os serviços

**2. Segurança Melhorada:**
- Políticas de senha centralizadas
- Bloqueio automático após tentativas falhas
- Logs de acesso centralizados
- Sessões unificadas (logout em todos os apps)

**3. Integração com Traefik:**
- Já configurado no MediaStack original
- Middleware de autenticação automático
- Protege todos os apps sem configuração individual

**4. Usabilidade Prática:**
- Convidados podem ter acesso limitado a apps específicos
- Usuários diferentes com permissões diferentes
- Acesso via VPN com credenciais únicas

**5. Futuro-Proof:**
- Se decidir expor algum serviço, já tem SSO pronto
- Pode adicionar mais apps sem preocupar com autenticação
- Escala para uso familiar/amigos facilmente

### 🎯 **Conclusão sobre Authentik:**
Para um home server com 20+ apps, **Authentik não é complexo demais** - é uma **solução prática** que simplifica o dia a dia, evita a dor de cabeça de gerenciar múltiplas credenciais e adiciona uma camada de segurança profissional ao seu setup pessoal.  

## Próximos Passos:

1. **Confirmar** seleção dos *ARR apps (já definido)
2. **Escolher** entre Jellyfin vs Plex
3. **Confirmar** Homepage como dashboard (já definido)
4. **Definir** se usará SABnzbd (Usenet) ou apenas qBittorrent
5. **Configurar** estrutura de pastas e rede local
6. **Implementar** configuração do docker-compose

Esta configuração fornecerá um home server completo com todo o ecossistema *ARR para automação de mídia, autenticação centralizada via Authentik, acesso seguro via VPN, e redução de 54% na complexidade mantendo 100% da funcionalidade essencial.

# Authentik — Guia de Configuração

O Authentik centraliza a autenticação de todos os serviços do homeserver.
Este guia cobre a configuração inicial e a integração com cada serviço.

---

## 1. Setup inicial

1. Acesse `https://auth.seudominio.com/if/flow/initial-setup/`
2. Defina e-mail e senha do usuário `akadmin`
3. Salve as credenciais em um lugar seguro

---

## 2. Como funciona a integração

### Serviços via ForwardAuth (Traefik middleware)

Para serviços sem suporte nativo a SSO, o Traefik intercepta cada requisição
e consulta o Authentik antes de redirecionar. O usuário faz login no Authentik
e o acesso é liberado.

Serviços que usam ForwardAuth:
- Traefik Dashboard
- AdGuard
- Radarr, Sonarr, Prowlarr, Bazarr
- qBittorrent

### Serviços com SSO nativo (OAuth2/OIDC)

Esses serviços têm suporte a login social/SSO e são configurados para
autenticar diretamente no Authentik via OAuth2.

Serviços com SSO nativo:
- Jellyfin
- Nextcloud
- Immich

---

## 3. Criar Provider OAuth2 (para cada serviço com SSO nativo)

### No Authentik:

1. Vá em **Applications → Providers → Create**
2. Selecione **OAuth2/OpenID Provider**
3. Configure:
   - **Name:** `jellyfin` (ou o nome do serviço)
   - **Authorization flow:** `default-authorization-flow`
   - **Client type:** Confidential
   - **Redirect URIs:** URL de callback do serviço (ver abaixo)
4. Salve e copie o **Client ID** e **Client Secret**
5. Vá em **Applications → Create** e vincule ao provider

### Redirect URIs por serviço:

| Serviço   | Redirect URI                                                    |
|-----------|-----------------------------------------------------------------|
| Jellyfin  | `https://jellyfin.seudominio.com/sso/OID/redirect/authentik`   |
| Nextcloud | `https://nextcloud.seudominio.com/apps/sociallogin/custom_oidc/authentik` |
| Immich    | `https://photos.seudominio.com/auth/login`                      |

---

## 4. Configurar Jellyfin com Authentik (SSO via OIDC)

1. No Jellyfin, instale o plugin **SSO Authentication**
   - Dashboard → Plugins → Catalog → SSO Authentication
2. Configure o plugin:
   - **OID Endpoint:** `https://auth.seudominio.com/application/o/jellyfin/`
   - **Client ID / Secret:** obtidos no passo anterior
3. Reinicie o Jellyfin

---

## 5. Configurar Nextcloud com Authentik (SSO via OIDC)

1. Instale o app **Social Login** no Nextcloud
   - Admin → Apps → buscar "Social Login"
2. Em Admin → Social Login, adicione um provider Custom OIDC:
   - **Title:** Authentik
   - **Authorize URL:** `https://auth.seudominio.com/application/o/authorize/`
   - **Token URL:** `https://auth.seudominio.com/application/o/token/`
   - **User info URL:** `https://auth.seudominio.com/application/o/userinfo/`
   - **Client ID / Secret:** obtidos no passo anterior
   - **Scope:** `openid email profile`

---

## 6. Configurar Immich com Authentik (SSO via OAuth2)

1. No Immich, vá em **Administration → OAuth**
2. Configure:
   - **Issuer URL:** `https://auth.seudominio.com/application/o/immich/`
   - **Client ID / Secret:** obtidos no passo anterior
   - **Scope:** `openid email profile`
   - **Button text:** Login com Authentik

---

## 7. Criar Outpost para ForwardAuth

O Outpost é o componente do Authentik que intercepta requisições via Traefik.

1. Vá em **Applications → Outposts → Create**
2. Tipo: **Proxy**
3. Integração: **Local Docker connection**
4. Vincule os serviços que usam ForwardAuth (Radarr, Sonarr, etc.)
5. O Outpost se auto-configura via Docker socket

---

## 8. Grupos e permissões sugeridos

| Grupo         | Acesso                                      |
|---------------|---------------------------------------------|
| `admins`      | Todos os serviços                           |
| `media`       | Jellyfin + stack *arr                       |
| `family`      | Jellyfin apenas                             |
| `nextcloud`   | Nextcloud                                   |

Configure em **Directory → Groups** e aplique nas Applications do Authentik.

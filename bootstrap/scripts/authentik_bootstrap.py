#!/usr/bin/env python3
"""
Authentik Bootstrap Script (via container)
Configura automaticamente o Authentik com aplicações, providers e outpost.
"""

import os
import sys
import time
import json

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def get_env(key: str, default: str = "") -> str:
    """Obtém variável de ambiente."""
    return os.getenv(key, default)


def wait_for_authentik(base_url: str, max_retries: int = 30) -> bool:
    """Aguarda o Authentik ficar disponível."""
    print("⏳ Aguardando Authentik iniciar...")

    for i in range(max_retries):
        try:
            r = requests.get(f"{base_url}/-/health/live/", timeout=5, verify=False)
            if r.status_code == 200:
                print("✅ Authentik está pronto!")
                return True
        except requests.exceptions.RequestException:
            pass

        print(f"  Tentativa {i + 1}/{max_retries}... aguardando 5s")
        time.sleep(5)

    print("❌ Authentik não ficou pronto a tempo")
    return False


def get_admin_session(base_url: str, email: str, password: str):
    """Cria uma sessão autenticada como admin."""
    try:
        session = requests.Session()
        session.verify = False

        # 1. Acessa página para obter CSRF cookie
        r = session.get(f"{base_url}/if/admin/", timeout=10)
        if r.status_code != 200:
            print(f"❌ Não consegui acessar {base_url}/if/admin/ (status: {r.status_code})")
            return None

        # 2. Obtém CSRF token do cookie
        csrf_token = session.cookies.get("authentik_csrf")
        if not csrf_token:
            print("❌ CSRF cookie não encontrado")
            return None

        # 3. Faz login via flow com CSRF
        r = session.post(
            f"{base_url}/if/flow/default-authentication-flow/",
            data={
                "uid": email,
                "password": password,
                "csrfmiddlewaretoken": csrf_token,
            },
            headers={"Referer": f"{base_url}/if/admin/"},
            timeout=10,
            allow_redirects=True,
        )

        if r.status_code == 200:
            # Verifica se está autenticado
            session_id = session.cookies.get("authentik_session")
            if session_id:
                print("✅ Login admin realizado com sucesso!")
                return session
            else:
                print("⚠️  Login OK mas session cookie não encontrado")
                print(f"Response URL: {r.url}")
                # Mesmo assim retorna session
                return session

        print(f"❌ Login falhou: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        return None

    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return None


def get_default_flow(base_url: str, session):
    """Obtém o UUID do default-authentication-flow."""
    try:
        r = session.get(
            f"{base_url}/api/v3/flows/",
            params={"slug": "default-authentication-flow"},
            timeout=10,
        )

        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                return results[0]["pk"]

        # Fallback
        r = session.get(f"{base_url}/api/v3/flows/", timeout=10)
        if r.status_code == 200:
            for flow in r.json().get("results", []):
                if "authentication" in flow.get("name", "").lower():
                    return flow["pk"]

        return None
    except Exception as e:
        print(f"Erro buscando flows: {e}")
        return None


def get_or_create_proxy_provider(base_url, session, name, external_host, flow_uuid):
    """Obtém ou cria Proxy Provider."""
    try:
        # Busca existente
        r = session.get(f"{base_url}/api/v3/providers/proxy/", timeout=10, params={"name": name})
        if r.status_code == 200:
            for p in r.json().get("results", []):
                if p["name"] == name:
                    print(f"  ℹ️  Provider '{name}' já existe (id: {p['pk']})")
                    # Atualiza flow
                    session.patch(
                        f"{base_url}/api/v3/providers/proxy/{p['pk']}/",
                        json={"authorization_flow": flow_uuid},
                        timeout=10,
                    )
                    return p["pk"]

        # Cria novo
        r = session.post(
            f"{base_url}/api/v3/providers/proxy/",
            json={
                "name": name,
                "authorization_flow": flow_uuid,
                "external_host": external_host,
                "internal_host": "",
                "mode": "forward_single",
            },
            timeout=10,
        )

        if r.status_code in [200, 201]:
            pk = r.json()["pk"]
            print(f"✅ Provider '{name}' criado (id: {pk})")
            return pk
        else:
            print(f"⚠️  Erro criando provider '{name}': {r.status_code}")
            return None

    except Exception as e:
        print(f"❌ Erro criando provider '{name}': {e}")
        return None


def get_or_create_application(base_url, session, name, slug, provider_pk):
    """Obtém ou cria aplicação."""
    try:
        # Busca existente
        r = session.get(f"{base_url}/api/v3/core/applications/", timeout=10, params={"slug": slug})
        if r.status_code == 200:
            for app in r.json().get("results", []):
                if app["slug"] == slug:
                    print(f"  ℹ️  Aplicação '{name}' já existe (id: {app['pk']})")
                    return app["pk"]

        # Cria nova
        r = session.post(
            f"{base_url}/api/v3/core/applications/",
            json={
                "name": name,
                "slug": slug,
                "provider": provider_pk,
                "backchannel_providers": [],
                "policy_engine_mode": "any",
                "group": None,
            },
            timeout=10,
        )

        if r.status_code in [200, 201]:
            pk = r.json()["pk"]
            print(f"✅ Aplicação '{name}' criada (id: {pk})")
            return pk
        else:
            print(f"⚠️  Erro criando aplicação '{name}': {r.status_code}")
            return None

    except Exception as e:
        print(f"❌ Erro criando aplicação '{name}': {e}")
        return None


def get_or_create_outpost(base_url, session, name, applications):
    """Obtém ou cria Outpost."""
    try:
        # Busca existente
        r = session.get(f"{base_url}/api/v3/outposts/proxy/", timeout=10)
        if r.status_code == 200:
            for o in r.json().get("results", []):
                if o["name"] == name:
                    print(f"  ℹ️  Outpost '{name}' já existe (id: {o['pk']})")
                    # Atualiza aplicações
                    session.patch(
                        f"{base_url}/api/v3/outposts/proxy/{o['pk']}/",
                        json={"applications": applications},
                        timeout=10,
                    )
                    return o["pk"]

        # Cria novo
        r = session.post(
            f"{base_url}/api/v3/outposts/proxy/",
            json={
                "name": name,
                "applications": applications,
                "docker_service_connections": [],
                "docker_connection": "local",
                "container_image": "ghcr.io/goauthentik/proxy:2024.8",
                "container_network": "proxy",
                "environment": {},
            },
            timeout=10,
        )

        if r.status_code in [200, 201]:
            pk = r.json()["pk"]
            print(f"✅ Outpost '{name}' criado (id: {pk})")
            return pk
        else:
            print(f"⚠️  Erro criando outpost '{name}': {r.status_code}")
            return None

    except Exception as e:
        print(f"❌ Erro criando outpost '{name}': {e}")
        return None


def main():
    """Bootstrap principal."""
    domain = get_env("DOMAIN", "maroto.online")
    email = get_env("AUTHENTIK_INITIAL_ADMIN_EMAIL", "admin@maroto.online")
    password = get_env("AUTHENTIK_INITIAL_ADMIN_PASSWORD", "")

    if not password:
        print("❌ AUTHENTIK_INITIAL_ADMIN_PASSWORD não definido")
        sys.exit(1)

    # Usa URL interna do container (acesso direto via rede Docker)
    base_url = "http://authentik-server:9000"

    print("\n┌─────────────────────────────────────────────────┐")
    print("│  Authentik Bootstrap                            │")
    print(f"│  Domínio: {domain}")
    print(f"│  Admin: {email}")
    print("└─────────────────────────────────────────────────┘\n")

    # 1. Aguarda Authentik
    if not wait_for_authentik(base_url):
        sys.exit(1)

    # 2. Autentica
    print("\n🔑 Autenticando como admin...")
    session = get_admin_session(base_url, email, password)
    if not session:
        print("❌ Não foi possível autenticar!")
        sys.exit(1)

    # 3. Obtém flow
    print("\n🔍 Obtendo authentication flow...")
    flow_uuid = get_default_flow(base_url, session)
    if not flow_uuid:
        print("❌ default-authentication-flow não encontrado")
        sys.exit(1)
    print(f"✅ Flow: {flow_uuid}")

    # 4. Cria providers
    print("\n📦 Criando Proxy Providers...")
    services = [
        {"name": "traefik", "external_host": f"https://traefik.{domain}"},
        {"name": "adguard", "external_host": f"https://dns.{domain}"},
    ]

    provider_ids = {}
    for svc in services:
        pk = get_or_create_proxy_provider(
            base_url, session, svc["name"], svc["external_host"], flow_uuid
        )
        if pk:
            provider_ids[svc["name"]] = pk

    if not provider_ids:
        print("❌ Nenhum provider criado!")
        sys.exit(1)

    # 5. Cria aplicações
    print("\n📱 Criando aplicações...")
    app_ids = {}
    for name, provider_pk in provider_ids.items():
        app_pk = get_or_create_application(
            base_url, session, name.capitalize(), name, provider_pk
        )
        if app_pk:
            app_ids[name] = app_pk

    # 6. Cria outpost
    print("\n🔗 Criando Outpost...")
    if app_ids:
        outpost_pk = get_or_create_outpost(
            base_url, session, "homeserver-proxy", list(app_ids.values())
        )
        if outpost_pk:
            print(f"✅ Outpost criado (id: {outpost_pk})")

    print("\n" + "="*50)
    print("✅ Authentik configurado com sucesso!")
    print("="*50)
    print(f"\nServiços:")
    print(f"  - Traefik: https://traefik.{domain}")
    print(f"  - AdGuard: https://dns.{domain}")
    print(f"  - Admin: https://auth.{domain}/if/admin/")
    print()


if __name__ == "__main__":
    main()

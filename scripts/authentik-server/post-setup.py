#!/usr/bin/env python3
"""
Authentik Post-Setup — executado dentro do próprio container authentik-server.

Cria token de API, providers, applications e outpost via Django ORM e API REST.
Idempotente: re-executar não duplica configurações.
"""

import json
import os
import subprocess
import sys
import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ── Configurações ─────────────────────────────────────────────────────────────

DOMAIN = os.getenv("DOMAIN", "")
ADMIN_EMAIL = os.getenv("AUTHENTIK_BOOTSTRAP_EMAIL", os.getenv("AUTHENTIK_INITIAL_ADMIN_EMAIL", ""))
ADMIN_PASSWORD = os.getenv("AUTHENTIK_BOOTSTRAP_PASSWORD", os.getenv("AUTHENTIK_INITIAL_ADMIN_PASSWORD", ""))
BASE_URL = "http://localhost:9000"
MAX_RETRIES = 60

SERVICES = [
    ("traefik", f"https://traefik.{DOMAIN}"),
    ("adguard", f"https://dns.{DOMAIN}"),
]


def log(msg: str) -> None:
    """Imprime mensagem de log prefixada."""
    print(f"[authentik-post-setup] {msg}")


def wait_for_authentik() -> bool:
    """Aguarda o Authentik ficar disponível via health endpoint."""
    log("Aguardando Authentik iniciar...")
    for i in range(MAX_RETRIES):
        try:
            r = requests.get(f"{BASE_URL}/-/health/live/", timeout=5, verify=False)
            if r.status_code == 200:
                log("✅ Authentik está pronto!")
                return True
        except requests.RequestException:
            pass
        time.sleep(2)
    log("⚠️  Timeout aguardando Authentik")
    return False


def create_api_token() -> str | None:
    """Cria token de API via Django ORM (ak shell)."""
    log("🔑 Criando token de API...")
    code = f"""
from authentik.core.models import User, Token, TokenIntents
from authentik.lib.generators import generate_id
user = User.objects.filter(email='{ADMIN_EMAIL}').first()
if user:
    Token.objects.filter(user=user, identifier='bootstrap-token').delete()
    token = Token.objects.create(
        user=user,
        identifier='bootstrap-token',
        intent=TokenIntents.INTENT_API,
        key=generate_id(),
        expires=None,
    )
    print(token.key)
"""
    result = subprocess.run(
        ["ak", "shell", "-c", code.strip()],
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    if token and not token.startswith("Traceback"):
        log("✅ Token de API criado")
        return token
    log("⚠️  Não foi possível criar token de API")
    return None


def get_default_flow(session: requests.Session) -> str | None:
    """Obtém UUID do default authentication flow."""
    r = session.get(
        f"{BASE_URL}/api/v3/flows/instances/",
        params={"slug": "default-authentication-flow"},
        timeout=10,
    )
    if r.status_code == 200:
        results = r.json().get("results", [])
        if results:
            return results[0]["pk"]
    # Fallback
    r = session.get(f"{BASE_URL}/api/v3/flows/instances/", timeout=10)
    if r.status_code == 200:
        for flow in r.json().get("results", []):
            if "authentication" in flow.get("name", "").lower():
                return flow["pk"]
    return None


def get_or_create_proxy_provider(
    session: requests.Session, name: str, external_host: str, flow: str
) -> int | None:
    """Obtém ou cria Proxy Provider."""
    r = session.get(
        f"{BASE_URL}/api/v3/providers/proxy/", params={"name": name}, timeout=10
    )
    if r.status_code == 200:
        for p in r.json().get("results", []):
            if p["name"] == name:
                log(f"  ℹ️  Provider '{name}' já existe")
                session.patch(
                    f"{BASE_URL}/api/v3/providers/proxy/{p['pk']}/",
                    json={"authorization_flow": flow},
                    timeout=10,
                )
                return p["pk"]
    r = session.post(
        f"{BASE_URL}/api/v3/providers/proxy/",
        json={
            "name": name,
            "authorization_flow": flow,
            "external_host": external_host,
            "internal_host": "",
            "mode": "forward_single",
        },
        timeout=10,
    )
    if r.status_code in (200, 201):
        log(f"  ✅ Provider '{name}' criado")
        return r.json()["pk"]
    log(f"  ⚠️  Erro criando provider '{name}': {r.status_code}")
    return None


def get_or_create_app(
    session: requests.Session, name: str, slug: str, provider: int
) -> int | None:
    """Obtém ou cria Application."""
    r = session.get(
        f"{BASE_URL}/api/v3/core/applications/", params={"slug": slug}, timeout=10
    )
    if r.status_code == 200:
        for a in r.json().get("results", []):
            if a["slug"] == slug:
                log(f"  ℹ️  App '{name}' já existe")
                return a["pk"]
    r = session.post(
        f"{BASE_URL}/api/v3/core/applications/",
        json={
            "name": name,
            "slug": slug,
            "provider": provider,
            "backchannel_providers": [],
            "policy_engine_mode": "any",
            "group": None,
        },
        timeout=10,
    )
    if r.status_code in (200, 201):
        log(f"  ✅ App '{name}' criada")
        return r.json()["pk"]
    log(f"  ⚠️  Erro criando app '{name}': {r.status_code}")
    return None


def create_outpost() -> None:
    """Cria ou atualiza Outpost via Django ORM (ak shell)."""
    log("🔗 Criando/Atualizando Outpost...")
    code = """
from authentik.outposts.models import Outpost
from authentik.core.models import Application

apps = Application.objects.filter(slug__in=['traefik', 'adguard'])
if apps.exists():
    Outpost.objects.update_or_create(
        name='homeserver-proxy',
        defaults={'type': 'proxy'}
    )
    outpost = Outpost.objects.get(name='homeserver-proxy')
    outpost.applications.set(apps)
    print('✅ Outpost criado/atualizado!')
else:
    print('⚠️  Aplicações não encontradas para outpost')
"""
    result = subprocess.run(
        ["ak", "shell", "-c", code.strip()],
        capture_output=True,
        text=True,
    )
    last_line = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    log(f"  {last_line}")


def main() -> None:
    if not ADMIN_PASSWORD:
        log("⚠️  Senha de admin não configurada — pulando post-setup")
        sys.exit(0)

    if not wait_for_authentik():
        sys.exit(0)

    api_token = create_api_token()
    if not api_token:
        sys.exit(0)

    session = requests.Session()
    session.verify = False
    session.headers.update({"Authorization": f"Bearer {api_token}"})

    flow_uuid = get_default_flow(session)
    if not flow_uuid:
        log("❌ default-authentication-flow não encontrado")
        sys.exit(0)
    log(f"✅ Flow: {flow_uuid}")

    log("📦 Criando Proxy Providers e Applications...")
    providers = {}
    for slug, external_host in SERVICES:
        pk = get_or_create_proxy_provider(session, slug, external_host, flow_uuid)
        if pk:
            providers[slug] = pk

    apps = {}
    for slug, pk in providers.items():
        app_pk = get_or_create_app(session, slug.capitalize(), slug, pk)
        if app_pk:
            apps[slug] = app_pk

    if apps:
        create_outpost()

    log("🎉 Authentik post-setup concluído!")


if __name__ == "__main__":
    main()

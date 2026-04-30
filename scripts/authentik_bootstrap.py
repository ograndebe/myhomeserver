#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "python-dotenv",
#   "rich",
# ]
# ///

"""
Authentik Bootstrap Script
Configura automaticamente o Authentik com aplicações, providers e outpost
após os containers subirem.

Uso: ./scripts/authentik_bootstrap.py
"""

import os
import sys
import time
from pathlib import Path

import requests
from rich.console import Console
from rich.panel import Panel

console = Console()
ROOT = Path(__file__).parent.parent


def load_env() -> dict:
    """Carrega variáveis do .env."""
    from dotenv import load_dotenv

    env_path = ROOT / ".env"
    if not env_path.exists():
        console.print("[red].env não encontrado! Execute setup.py primeiro.[/red]")
        sys.exit(1)

    load_dotenv(env_path)

    return {
        "domain": os.getenv("DOMAIN", ""),
        "authentik_email": os.getenv("AUTHENTIK_INITIAL_ADMIN_EMAIL", ""),
        "authentik_password": os.getenv("AUTHENTIK_INITIAL_ADMIN_PASSWORD", ""),
    }


def wait_for_authentik(base_url: str, max_retries: int = 30) -> bool:
    """Aguarda o Authentik ficar disponível."""
    console.print("[dim]Aguardando Authentik iniciar...[/dim]")

    for i in range(max_retries):
        try:
            # Desabilita verificação SSL para localhost
            r = requests.get(f"{base_url}/-/health/live/", timeout=5, verify=False)
            if r.status_code == 200:
                console.print("[green]✔ Authentik está pronto![/green]")
                return True
        except requests.exceptions.RequestException:
            pass

        console.print(f"  Tentativa {i + 1}/{max_retries}... aguardando 5s")
        time.sleep(5)

    console.print("[red]✘ Authentik não ficou pronto a tempo[/red]")
    return False


def get_admin_session(base_url: str, email: str, password: str) -> requests.Session | None:
    """Cria uma sessão autenticada como admin."""
    try:
        session = requests.Session()
        session.verify = False  # Ignora SSL para localhost

        # Primeiro acessa a página para obter CSRF token
        r = session.get(f"{base_url}/if/admin/", timeout=10)
        if r.status_code != 200:
            console.print(f"[red]Não consegui acessar {base_url}/if/admin/ (status: {r.status_code})[/red]")
            return None

        # Tenta login via API de sessão
        r = session.post(
            f"{base_url}/api/v3/auth/session/",
            json={
                "username": email,
                "password": password,
            },
            timeout=10,
        )

        if r.status_code == 200:
            console.print("[green]✔ Login realizado com sucesso![/green]")
            return session

        console.print(f"[dim]Login falhou com status: {r.status_code}[/dim]")
        if r.text:
            console.print(f"[dim]Response: {r.text[:200]}[/dim]")
        return None

    except Exception as e:
        console.print(f"[red]Erro no login: {e}[/red]")
        return None


def get_or_create_proxy_provider(
    base_url: str, session: requests.Session, name: str, external_host: str, flow_uuid: str
) -> int | None:
    """Obtém ou cria um Proxy Provider no Authentik."""
    try:
        # Primeiro tenta buscar existente
        r = session.get(f"{base_url}/api/v3/providers/proxy/", timeout=10, params={"name": name})
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            for p in results:
                if p["name"] == name:
                    console.print(f"[dim]Provider '{name}' já existe (id: {p['pk']})[/dim]")
                    # Atualiza com o flow
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
            data = r.json()
            console.print(f"[green]✔ Provider '{name}' criado (id: {data['pk']})[/green]")
            return data["pk"]
        else:
            console.print(f"[yellow]⚠ Erro criando provider '{name}': {r.status_code}[/yellow]")
            console.print(f"[dim]{r.text[:200]}[/dim]")
            return None

    except Exception as e:
        console.print(f"[red]Erro criando provider '{name}': {e}[/red]")
        return None


def get_default_flow(base_url: str, session: requests.Session) -> str | None:
    """Obtém o UUID do default-authentication-flow."""
    try:
        r = session.get(
            f"{base_url}/api/v3/flows/",
            params={"slug": "default-authentication-flow"},
            timeout=10,
        )

        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                return results[0]["pk"]

        # Fallback: busca todos os flows
        r = session.get(f"{base_url}/api/v3/flows/", timeout=10)
        if r.status_code == 200:
            data = r.json()
            for flow in data.get("results", []):
                if "authentication" in flow.get("name", "").lower():
                    console.print(f"[dim]Flow encontrado: {flow['name']}[/dim]")
                    return flow["pk"]

        return None
    except Exception as e:
        console.print(f"[dim]Erro buscando flows: {e}[/dim]")
        return None


def get_or_create_application(
    base_url: str, session: requests.Session, name: str, slug: str, provider_pk: int
) -> int | None:
    """Obtém ou cria uma aplicação no Authentik."""
    try:
        # Busca existente
        r = session.get(f"{base_url}/api/v3/core/applications/", timeout=10, params={"slug": slug})
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            for app in results:
                if app["slug"] == slug:
                    console.print(f"[dim]Aplicação '{name}' já existe (id: {app['pk']})[/dim]")
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
            data = r.json()
            console.print(f"[green]✔ Aplicação '{name}' criada (id: {data['pk']})[/green]")
            return data["pk"]
        else:
            console.print(f"[yellow]⚠ Erro criando aplicação '{name}': {r.status_code}[/yellow]")
            console.print(f"[dim]{r.text[:200]}[/dim]")
            return None

    except Exception as e:
        console.print(f"[red]Erro criando aplicação '{name}': {e}[/red]")
        return None


def get_or_create_outpost(
    base_url: str,
    session: requests.Session,
    name: str,
    applications: list[int],
) -> int | None:
    """Obtém ou cria um Proxy Outpost no Authentik."""
    try:
        # Busca existente
        r = session.get(f"{base_url}/api/v3/outposts/proxy/", timeout=10)
        if r.status_code == 200:
            data = r.json()
            outposts = data.get("results", [])
            for o in outposts:
                if o["name"] == name:
                    console.print(f"[dim]Outpost '{name}' já existe (id: {o['pk']})[/dim]")
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
            data = r.json()
            console.print(f"[green]✔ Outpost '{name}' criado (id: {data['pk']})[/green]")
            return data["pk"]
        else:
            console.print(f"[yellow]⚠ Erro criando outpost '{name}': {r.status_code}[/yellow]")
            console.print(f"[dim]{r.text[:200]}[/dim]")
            return None

    except Exception as e:
        console.print(f"[red]Erro criando outpost '{name}': {e}[/red]")
        return None


def bootstrap_authentik(domain: str, email: str, password: str) -> bool:
    """Executa todo o bootstrap do Authentik."""
    base_url = f"https://auth.{domain}"

    # 1. Aguarda Authentik ficar pronto
    if not wait_for_authentik(base_url):
        return False

    # 2. Autentica como admin
    console.print("\n[bold]Autenticando como admin...[/bold]")
    session = get_admin_session(base_url, email, password)
    if not session:
        console.print("[red]Não foi possível autenticar![/red]")
        return False

    # 3. Obtém o default authentication flow
    console.print("\n[bold]Obtendo authentication flow...[/bold]")
    flow_uuid = get_default_flow(base_url, session)
    if not flow_uuid:
        console.print("[red]Não encontrei o default-authentication-flow[/red]")
        return False
    console.print(f"[green]✔ Flow obtido: {flow_uuid}[/green]")

    # 4. Cria Proxy Providers para cada serviço
    console.print("\n[bold]Criando Proxy Providers...[/bold]")

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
        console.print("[red]Nenhum provider criado![/red]")
        return False

    # 5. Cria aplicações
    console.print("\n[bold]Criando aplicações...[/bold]")

    app_ids = {}
    for name, provider_pk in provider_ids.items():
        app_pk = get_or_create_application(
            base_url, session, name.capitalize(), name, provider_pk
        )
        if app_pk:
            app_ids[name] = app_pk

    # 6. Cria o outpost
    console.print("\n[bold]Criando Outpost...[/bold]")

    if app_ids:
        outpost_pk = get_or_create_outpost(
            base_url, session, "homeserver-proxy", list(app_ids.values())
        )
        if outpost_pk:
            console.print(f"[green]✔ Outpost criado (id: {outpost_pk})[/green]")

    console.print(
        Panel(
            "[green]✔ Authentik configurado com sucesso![/green]\n\n"
            "Serviços configurados:\n"
            f"  - Traefik: https://traefik.{domain}\n"
            f"  - AdGuard: https://dns.{domain}\n\n"
            "Admin: https://auth.{domain}/if/admin/",
            title="Bootstrap concluído",
        )
    )

    return True


def main():
    """Entry point."""
    env = load_env()

    if not env["domain"]:
        console.print("[red]Domínio não encontrado no .env[/red]")
        sys.exit(1)

    if not env["authentik_email"] or not env["authentik_password"]:
        console.print("[red]Credenciais do Authentik não encontradas no .env[/red]")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold]Authentik Bootstrap[/bold]\n\n"
            f"Domínio: {env['domain']}\n"
            f"Admin: {env['authentik_email']}\n",
            border_style="cyan",
        )
    )

    success = bootstrap_authentik(
        env["domain"], env["authentik_email"], env["authentik_password"]
    )

    if not success:
        console.print(
            "\n[yellow]⚠ Bootstrap não pôde ser completado automaticamente.\n"
            "Configure manualmente em: https://auth.maroto.online/if/admin/[/yellow]"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

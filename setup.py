#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jinja2",
#   "questionary",
#   "click",
#   "python-dotenv",
#   "pyyaml",
#   "rich",
# ]
# ///

"""
Homeserver Setup Script
Gera docker-compose.yml, .env e arquivos de configuração para subir o homeserver.
Uso: ./setup.py
"""

import os
import sys
import socket
import shutil
import subprocess
from pathlib import Path

import click
import questionary
import yaml
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

console = Console()
ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"
TEMPLATES = ROOT / "templates"
CONFIG = ROOT / "config" / "services.yml"


def load_existing_env() -> dict:
    """Carrega variáveis de .env existente no diretório do setup.py."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return {}

    from dotenv import load_dotenv

    load_dotenv(env_path)

    return {
        "domain": os.getenv("DOMAIN", ""),
        "cf_email": os.getenv("CF_API_EMAIL", ""),
        "cf_dns_api_token": os.getenv("CF_DNS_API_TOKEN", ""),
        "acme_email": os.getenv("ACME_EMAIL", ""),
        "storage_path": os.getenv("STORAGE_PATH", "/mnt/data/myhomeserver"),
        "authentik_email": os.getenv("AUTHENTIK_INITIAL_ADMIN_EMAIL", ""),
        "authentik_user": os.getenv(
            "AUTHENTIK_INITIAL_ADMIN_USERNAME", "administrator"
        ),
        "authentik_password": os.getenv("AUTHENTIK_INITIAL_ADMIN_PASSWORD", ""),
        "wireguard_peers": os.getenv("WIREGUARD_PEERS", ""),
    }


# ── Descoberta do ambiente ────────────────────────────────────────────────────


def get_local_ip() -> str:
    """Descobre o IP local do servidor."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_disk_info(path: str) -> dict:
    """Retorna informações de disco para o caminho informado."""
    try:
        usage = shutil.disk_usage(path)
        free_gb = usage.free / (1024**3)
        total_gb = usage.total / (1024**3)
        return {
            "free_gb": round(free_gb, 1),
            "total_gb": round(total_gb, 1),
            "ok": True,
        }
    except Exception:
        return {"free_gb": 0, "total_gb": 0, "ok": False}


def check_docker() -> dict:
    """Verifica se Docker e Compose estão instalados."""
    result = {"docker": None, "compose": None}
    try:
        r = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
        )
        result["docker"] = r.stdout.strip() if r.returncode == 0 else None
    except FileNotFoundError:
        pass
    try:
        r = subprocess.run(
            ["docker", "compose", "version", "--short"], capture_output=True, text=True
        )
        result["compose"] = r.stdout.strip() if r.returncode == 0 else None
    except FileNotFoundError:
        pass
    return result


def generate_secret(length: int = 32) -> str:
    """Gera uma string aleatória segura."""
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def load_output_env() -> dict:
    """Carrega secrets de output/.env existente para manter idempotência."""
    env_path = OUTPUT / ".env"
    if not env_path.exists():
        return {}

    from dotenv import load_dotenv

    load_dotenv(env_path)

    return {
        "authentik_secret_key": os.getenv("AUTHENTIK_SECRET_KEY", ""),
        "authentik_pg_password": os.getenv("AUTHENTIK_PG_PASSWORD", ""),
        "nextcloud_db_password": os.getenv("NEXTCLOUD_DB_PASSWORD", ""),
        "immich_db_password": os.getenv("IMMICH_DB_PASSWORD", ""),
        "wireguard_peers": os.getenv("WIREGUARD_PEERS", ""),
    }


# ── Perguntas interativas ─────────────────────────────────────────────────────


def normalize_peer_name(name: str) -> str:
    """Normaliza o nome de um peer WireGuard.

    Converte para lowercase, substitui espaços por underscore e remove
    caracteres especiais, mantendo apenas letras, números e underscore.
    """
    import re

    name = name.strip().lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_]", "", name)


def ask_questions(services_config: dict, env_defaults: dict = None) -> dict:
    """Faz as perguntas interativas e retorna o contexto para os templates."""
    if env_defaults is None:
        env_defaults = {}

    # Avisa se carregou defaults do .env
    if env_defaults:
        console.print(
            "[dim]💡 Valores do .env carregados como defaults — pressione Enter para confirmar[/dim]"
        )
        console.print()

    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Homeserver Setup[/bold cyan]\n"
            "[dim]Responda as perguntas para gerar sua configuração[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    # Domínio próprio (único modo suportado)
    domain = questionary.text(
        "Qual é o domínio principal do servidor?",
        default=env_defaults.get("domain", ""),
        validate=lambda v: (
            True if "." in v else "Informe um domínio válido (ex: meusite.com)"
        ),
    ).ask()
    if not domain:
        sys.exit(0)

    # Credenciais Cloudflare
    console.print(
        "\n[dim]Credenciais Cloudflare (usado pelo Traefik para emitir certificado wildcard TLS):[/dim]"
    )
    cf_email = questionary.text(
        "  CF_API_EMAIL:", default=env_defaults.get("cf_email", "")
    ).ask()
    if not cf_email:
        sys.exit(0)
    cf_dns_api_token = questionary.password(
        "  CF_DNS_API_TOKEN (Cloudflare DNS API Token):",
        default=env_defaults.get("cf_dns_api_token", ""),
    ).ask()
    if not cf_dns_api_token:
        sys.exit(0)

    # Credenciais Authentik
    console.print("\n[dim]Credenciais do admin Authentik (SSO):[/dim]")
    authentik_email = questionary.text(
        "  E-mail do admin:",
        default=f"admin@{domain}"
        if not env_defaults.get("authentik_email")
        else env_defaults["authentik_email"],
    ).ask()
    if not authentik_email:
        sys.exit(0)
    authentik_user = questionary.text(
        "  Username do admin:",
        default=env_defaults.get("authentik_user", "administrator"),
    ).ask()
    if not authentik_user:
        sys.exit(0)
    authentik_password = questionary.password(
        "  Senha do admin (mínimo 8 caracteres):",
        default=env_defaults.get("authentik_password", ""),
        validate=lambda v: (
            True if len(v) >= 8 else "A senha deve ter pelo menos 8 caracteres"
        ),
    ).ask()
    if not authentik_password:
        sys.exit(0)

    # E-mail Let's Encrypt
    acme_email = questionary.text(
        "E-mail para o Let's Encrypt (notificações de renovação de certificado):",
        default=env_defaults.get("acme_email", ""),
        validate=lambda v: True if "@" in v else "Informe um e-mail válido",
    ).ask()
    if not acme_email:
        sys.exit(0)

    # Disco/storage
    storage_path = questionary.text(
        "Caminho para volumes persistentes (onde os dados serão armazenados):",
        default=env_defaults.get("storage_path", "/mnt/data/myhomeserver"),
    ).ask()
    if not storage_path:
        sys.exit(0)

    # Serviços opcionais
    optional_choices = [
        questionary.Choice(
            f"{s['name']} — {s['description']}", value=s["id"], checked=False
        )
        for s in services_config["optional"]
    ]
    selected_optional = questionary.checkbox(
        "Quais serviços opcionais deseja ativar?", choices=optional_choices
    ).ask()
    if selected_optional is None:
        sys.exit(0)

    # WireGuard peers
    wireguard_peers_input = questionary.text(
        "Nomes dos devices para WireGuard (separados por vírgula):",
        default=env_defaults.get("wireguard_peers", "phone"),
    ).ask()
    if wireguard_peers_input is None:
        sys.exit(0)
    if not wireguard_peers_input.strip():
        wireguard_peers_input = "phone"
    peers = [normalize_peer_name(p) for p in wireguard_peers_input.split(",")]
    wireguard_peers = ",".join(peers)

    return {
        "domain": domain,
        "cf_email": cf_email,
        "cf_dns_api_token": cf_dns_api_token,
        "acme_email": acme_email,
        "storage_path": storage_path,
        "authentik_email": authentik_email,
        "authentik_user": authentik_user,
        "authentik_password": authentik_password,
        "optional_services": selected_optional or [],
        "enable_jellyfin": "jellyfin" in (selected_optional or []),
        "enable_nextcloud": "nextcloud" in (selected_optional or []),
        "enable_immich": "immich" in (selected_optional or []),
        "enable_static_page": "static-page" in (selected_optional or []),
        "wireguard_peers": wireguard_peers,
    }


# ── Checks do ambiente ────────────────────────────────────────────────────────


def run_environment_checks(answers: dict) -> dict:
    """Descobre informações do ambiente e exibe um resumo."""
    console.print()
    console.print("[bold]Verificando o ambiente...[/bold]")

    local_ip = get_local_ip()
    disk = get_disk_info(
        answers["storage_path"] if Path(answers["storage_path"]).exists() else "/"
    )
    docker = check_docker()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()

    table.add_row("IP local detectado", f"[cyan]{local_ip}[/cyan]")

    if disk["ok"]:
        table.add_row(
            "Espaço disponível",
            f"[cyan]{disk['free_gb']}GB[/cyan] de {disk['total_gb']}GB em {answers['storage_path']}",
        )
    else:
        table.add_row(
            "Espaço disponível",
            f"[yellow]Não foi possível verificar {answers['storage_path']}[/yellow]",
        )

    if docker["docker"]:
        table.add_row("Docker", f"[green]✔[/green] {docker['docker']}")
    else:
        table.add_row(
            "Docker",
            "[red]✘ não encontrado — instale em https://docs.docker.com/engine/install/[/red]",
        )

    if docker["compose"]:
        table.add_row("Docker Compose", f"[green]✔[/green] {docker['compose']}")
    else:
        table.add_row("Docker Compose", "[red]✘ não encontrado[/red]")

    console.print(table)
    console.print()

    if not docker["docker"]:
        console.print(
            "[red]Docker é necessário. Instale e execute o setup novamente.[/red]"
        )
        sys.exit(1)

    return {
        "local_ip": local_ip,
        "disk": disk,
        "docker": docker,
    }


# ── Geração de arquivos ───────────────────────────────────────────────────────


def create_data_directories(context: dict) -> None:
    """Cria os subdiretórios necessários para cada serviço."""
    storage = Path(context["storage_path"])

    dirs = [
        "traefik/acme",
        "traefik/logs",
        "adguard/work",
        "adguard/conf",
        "wireguard/config",
        "authentik/custom-templates",
    ]

    if context.get("enable_jellyfin"):
        dirs.extend(
            [
                "jellyfin/config",
                "media/movies",
                "media/shows",
                "media/music",
                "prowlarr/config",
                "radarr/config",
                "sonarr/config",
                "bazarr/config",
                "qbittorrent/config",
                "downloads",
            ]
        )

    if context.get("enable_nextcloud"):
        dirs.extend(
            [
                "nextcloud/data",
            ]
        )

    if context.get("enable_immich"):
        dirs.extend(
            [
                "immich/upload",
                "immich/model-cache",
            ]
        )

    console.print("[bold]Criando diretórios de dados...[/bold]")
    for dir_path in dirs:
        full_path = storage / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if "adguard" in dir_path:
                full_path.chmod(0o777)
            console.print(f"  [green]✔[/green] {dir_path}")
        except Exception as e:
            console.print(f"  [red]✘[/red] {dir_path} — {e}")


def render_templates(context: dict) -> None:
    """Renderiza todos os templates Jinja2 e salva em output/."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "traefik").mkdir(exist_ok=True)
    (OUTPUT / "adguard").mkdir(exist_ok=True)

    files = [
        ("docker-compose.yml.j2", OUTPUT / "docker-compose.yml"),
        (".env.j2", OUTPUT / ".env"),
        ("traefik/traefik.yml.j2", OUTPUT / "traefik" / "traefik.yml"),
        ("adguard/AdGuardHome.yaml.j2", OUTPUT / "adguard" / "AdGuardHome.yaml"),
    ]

    if context.get("enable_static_page"):
        static_page_dir = OUTPUT / "static-page" / "html"
        static_page_dir.mkdir(parents=True, exist_ok=True)
        files.append(("static-page/index.html.j2", static_page_dir / "index.html"))

    console.print("[bold]Gerando arquivos...[/bold]")
    for template_name, output_path in files:
        try:
            template = env.get_template(template_name)
            rendered = template.render(**context)
            output_path.write_text(rendered)
            console.print(f"  [green]✔[/green] {output_path.relative_to(ROOT)}")
        except Exception as e:
            console.print(f"  [red]✘[/red] {output_path.relative_to(ROOT)} — {e}")


def generate_post_build_notes(context: dict) -> None:
    """Gera o arquivo post-build-notes.txt com instruções pós-geração."""
    domain = context["domain"]
    notes_path = OUTPUT / "post-build-notes.txt"

    enabled_services = []
    enabled_services.append("- Authentik: https://auth." + domain)
    enabled_services.append("- AdGuard DNS: https://dns." + domain)
    enabled_services.append("- Traefik Dashboard: https://traefik." + domain)
    enabled_services.append("- Static Page: https://test." + domain)

    if context.get("enable_jellyfin"):
        enabled_services.append("- Jellyfin: https://jellyfin." + domain)
        enabled_services.append("- Prowlarr: https://prowlarr." + domain)
        enabled_services.append("- Radarr: https://radarr." + domain)
        enabled_services.append("- Sonarr: https://sonarr." + domain)
        enabled_services.append("- Bazarr: https://bazarr." + domain)

    if context.get("enable_nextcloud"):
        enabled_services.append("- Nextcloud: https://files." + domain)

    if context.get("enable_immich"):
        enabled_services.append("- Immich: https://photos." + domain)

    dns_instructions = f"""### 1. Configuração DNS
Crie um registro DNS wildcard no Cloudflare:
  *.{domain}  →  A  →  {context["local_ip"]}"""

    notes_content = f"""# Post-Build Notes
# Gerado em: {subprocess.run(["date"], capture_output=True, text=True).stdout.strip()}

## Próximos Passos

{dns_instructions}

### 2. Subir os serviços (com bootstrap automático)
  ./post-setup.sh

O script post-setup.sh irá:
  - Subir todos os containers
  - Executar o container bootstrap que configura o Authentik automaticamente
  - O bootstrap container cria:
    * Proxy Providers para Traefik e AdGuard
    * Aplicações no Authentik
    * Outpost para ForwardAuth

### 3. Serviços Disponíveis
{chr(10).join(enabled_services)}

### 4. Configuração Adicional
  - Authentik: docs/authentik-setup.md
  - Geral: docs/post-setup.md

### 5. WireGuard VPN
Para configurar peers adicionais, edite WIREGUARD_PEERS no arquivo .env
e recrie o container: docker compose up -d wireguard

### 6. Troubleshooting
  - Ver logs do bootstrap: docker compose logs bootstrap
  - Ver logs de serviço: docker compose logs [serviço]
  - Rebuild: docker compose down && docker compose up -d --build
  - Ver containers: docker compose ps
"""

    notes_path.write_text(notes_content)
    console.print(f"  [green]✔[/green] {notes_path.relative_to(ROOT)}")


def print_next_steps(context: dict) -> None:
    """Exibe as instruções pós-geração."""
    domain = context["domain"]

    dns_step = (
        f"[cyan]1.[/cyan] Crie um registro DNS wildcard no seu provedor:\n"
        f"   [dim]*.{domain}  →  A  →  {context['local_ip']}[/dim]"
    )
    service_access = (
        f"[dim]- Authentik: https://auth.{domain}[/dim]\n"
        f"[dim]- AdGuard: https://dns.{domain} (user: {context['authentik_email']})[/dim]\n"
        f"[dim]- Traefik: https://traefik.{domain}[/dim]\n"
        f"[dim]- Teste: https://test.{domain}[/dim]"
    )

    console.print()
    console.print(
        Panel(
            f"""[bold green]Configuração gerada com sucesso![/bold green]

[bold]Próximos passos:[/bold]

{dns_step}

[cyan]2.[/cyan] Suba os serviços (com bootstrap automático):
   [dim]./post-setup.sh[/dim]

   O script irá:
   - Subir todos os containers
   - Configurar o Authentik automaticamente via bootstrap container

[cyan]3.[/cyan] Acesse os serviços:
{service_access}

[cyan]4.[/cyan] Configuração adicional:
   [dim]Veja docs/post-setup.md[/dim]
""",
            title="[bold]Setup concluído[/bold]",
            border_style="green",
        )
    )


# ── Entry point ───────────────────────────────────────────────────────────────


@click.command()
@click.option("--dry-run", is_flag=True, help="Mostra o contexto sem gerar arquivos")
@click.option(
    "--use-existing-env",
    is_flag=True,
    help="Usa valores do .env existente sem perguntar interativamente",
)
def main(dry_run: bool, use_existing_env: bool):
    """Homeserver setup — gera docker-compose.yml, .env e configurações."""
    services_config = yaml.safe_load(CONFIG.read_text())

    env_defaults = load_existing_env()

    if use_existing_env:
        # Usa valores do .env existente sem perguntas
        if not env_defaults.get("domain"):
            console.print(
                "[red]--use-existing-env requer um .env válido com DOMAIN[/red]"
            )
            sys.exit(1)

        console.print(
            Panel(
                "[bold cyan]Modo --use-existing-env[/bold cyan]\n"
                "Usando valores do .env existente sem perguntas interativas.",
                border_style="cyan",
            )
        )
        console.print()

        answers = {
            "domain": env_defaults["domain"],
            "cf_email": env_defaults.get("cf_email", ""),
            "cf_dns_api_token": env_defaults.get("cf_dns_api_token", ""),
            "acme_email": env_defaults.get("acme_email", ""),
            "storage_path": env_defaults.get("storage_path", "/mnt/data/myhomeserver"),
            "authentik_email": env_defaults.get("authentik_email", ""),
            "authentik_user": env_defaults.get("authentik_user", "administrator"),
            "authentik_password": env_defaults.get("authentik_password", ""),
            "optional_services": [],
            "enable_jellyfin": False,
            "enable_nextcloud": False,
            "enable_immich": False,
            "enable_static_page": True,
            "wireguard_peers": env_defaults.get("wireguard_peers", "phone"),
        }
    else:
        answers = ask_questions(services_config, env_defaults)

    env_info = run_environment_checks(answers)

    # Carrega secrets existentes do output/.env para manter idempotência
    existing_secrets = load_output_env()

    # Contexto completo para os templates
    context = {
        **answers,
        **env_info,
        # Secrets — reuse existing se disponível, caso contrário gera novos
        "authentik_secret_key": existing_secrets.get("authentik_secret_key")
        or generate_secret(50),
        "authentik_pg_password": existing_secrets.get("authentik_pg_password")
        or generate_secret(32),
        "nextcloud_db_password": existing_secrets.get("nextcloud_db_password")
        or (generate_secret(32) if answers["enable_nextcloud"] else ""),
        "immich_db_password": existing_secrets.get("immich_db_password")
        or (generate_secret(32) if answers["enable_immich"] else ""),
        "wireguard_peers": answers.get("wireguard_peers")
        or existing_secrets.get("wireguard_peers")
        or "phone",
    }

    if dry_run:
        import json

        # Omite secrets do dry-run
        safe = {
            k: v
            for k, v in context.items()
            if "password" not in k and "secret" not in k and "token" not in k
        }
        console.print_json(json.dumps(safe, indent=2))
        return

    create_data_directories(context)
    render_templates(context)
    generate_post_build_notes(context)
    print_next_steps(context)


if __name__ == "__main__":
    main()

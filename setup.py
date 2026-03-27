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
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        return {"free_gb": round(free_gb, 1), "total_gb": round(total_gb, 1), "ok": True}
    except Exception:
        return {"free_gb": 0, "total_gb": 0, "ok": False}


def check_docker() -> dict:
    """Verifica se Docker e Compose estão instalados."""
    result = {"docker": None, "compose": None}
    try:
        r = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"],
                           capture_output=True, text=True)
        result["docker"] = r.stdout.strip() if r.returncode == 0 else None
    except FileNotFoundError:
        pass
    try:
        r = subprocess.run(["docker", "compose", "version", "--short"],
                           capture_output=True, text=True)
        result["compose"] = r.stdout.strip() if r.returncode == 0 else None
    except FileNotFoundError:
        pass
    return result


def generate_secret(length: int = 32) -> str:
    """Gera uma string aleatória segura."""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ── Perguntas interativas ─────────────────────────────────────────────────────

def ask_questions(services_config: dict) -> dict:
    """Faz as perguntas interativas e retorna o contexto para os templates."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Homeserver Setup[/bold cyan]\n"
        "[dim]Responda as perguntas para gerar sua configuração[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Domínio
    domain = questionary.text(
        "Qual é o domínio principal do servidor?",
        validate=lambda v: True if "." in v else "Informe um domínio válido (ex: meusite.com)"
    ).ask()
    if not domain:
        sys.exit(0)

    # Provedor DNS
    dns_providers = {p["id"]: p for p in services_config["dns_providers"]}
    dns_choice = questionary.select(
        "Qual o provedor DNS do seu domínio? (necessário para certificado wildcard TLS)",
        choices=[
            questionary.Choice(p["name"], value=p["id"])
            for p in services_config["dns_providers"]
        ]
    ).ask()
    if not dns_choice:
        sys.exit(0)

    # Credenciais DNS
    dns_env_vars = {}
    provider = dns_providers[dns_choice]
    if provider["env_vars"]:
        console.print(f"\n[dim]Credenciais para {provider['name']} (usado pelo Traefik para emitir certificado wildcard):[/dim]")
        for var in provider["env_vars"]:
            val = questionary.password(f"  {var}:").ask()
            if val:
                dns_env_vars[var] = val

    # E-mail Let's Encrypt
    acme_email = questionary.text(
        "E-mail para o Let's Encrypt (notificações de renovação de certificado):",
        validate=lambda v: True if "@" in v else "Informe um e-mail válido"
    ).ask()
    if not acme_email:
        sys.exit(0)

    # Disco/storage
    storage_path = questionary.text(
        "Caminho para volumes persistentes (onde os dados serão armazenados):",
        default="/opt/homeserver/data"
    ).ask()
    if not storage_path:
        sys.exit(0)

    # Serviços opcionais
    optional_choices = [
        questionary.Choice(
            f"{s['name']} — {s['description']}",
            value=s["id"],
            checked=False
        )
        for s in services_config["optional"]
    ]
    selected_optional = questionary.checkbox(
        "Quais serviços opcionais deseja ativar?",
        choices=optional_choices
    ).ask()
    if selected_optional is None:
        sys.exit(0)

    return {
        "domain": domain,
        "dns_provider": dns_choice,
        "dns_env_vars": dns_env_vars,
        "acme_email": acme_email,
        "storage_path": storage_path,
        "optional_services": selected_optional or [],
        "enable_jellyfin": "jellyfin" in (selected_optional or []),
        "enable_nextcloud": "nextcloud" in (selected_optional or []),
        "enable_immich": "immich" in (selected_optional or []),
    }


# ── Checks do ambiente ────────────────────────────────────────────────────────

def run_environment_checks(answers: dict) -> dict:
    """Descobre informações do ambiente e exibe um resumo."""
    console.print()
    console.print("[bold]Verificando o ambiente...[/bold]")

    local_ip = get_local_ip()
    disk = get_disk_info(answers["storage_path"] if Path(answers["storage_path"]).exists() else "/")
    docker = check_docker()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()

    table.add_row("IP local detectado", f"[cyan]{local_ip}[/cyan]")

    if disk["ok"]:
        table.add_row("Espaço disponível", f"[cyan]{disk['free_gb']}GB[/cyan] de {disk['total_gb']}GB em {answers['storage_path']}")
    else:
        table.add_row("Espaço disponível", f"[yellow]Não foi possível verificar {answers['storage_path']}[/yellow]")

    if docker["docker"]:
        table.add_row("Docker", f"[green]✔[/green] {docker['docker']}")
    else:
        table.add_row("Docker", "[red]✘ não encontrado — instale em https://docs.docker.com/engine/install/[/red]")

    if docker["compose"]:
        table.add_row("Docker Compose", f"[green]✔[/green] {docker['compose']}")
    else:
        table.add_row("Docker Compose", "[red]✘ não encontrado[/red]")

    console.print(table)
    console.print()

    if not docker["docker"]:
        console.print("[red]Docker é necessário. Instale e execute o setup novamente.[/red]")
        sys.exit(1)

    return {
        "local_ip": local_ip,
        "disk": disk,
        "docker": docker,
    }


# ── Geração de arquivos ───────────────────────────────────────────────────────

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
        (".env.j2",               OUTPUT / ".env"),
        ("traefik/traefik.yml.j2", OUTPUT / "traefik" / "traefik.yml"),
        ("adguard/AdGuardHome.yaml.j2", OUTPUT / "adguard" / "AdGuardHome.yaml"),
    ]

    console.print("[bold]Gerando arquivos...[/bold]")
    for template_name, output_path in files:
        try:
            template = env.get_template(template_name)
            rendered = template.render(**context)
            output_path.write_text(rendered)
            console.print(f"  [green]✔[/green] {output_path.relative_to(ROOT)}")
        except Exception as e:
            console.print(f"  [red]✘[/red] {output_path.relative_to(ROOT)} — {e}")


def print_next_steps(context: dict) -> None:
    """Exibe as instruções pós-geração."""
    domain = context["domain"]
    console.print()
    console.print(Panel(
        f"""[bold green]Configuração gerada com sucesso![/bold green]

[bold]Próximos passos:[/bold]

[cyan]1.[/cyan] Crie um registro DNS wildcard no seu provedor:
   [dim]*.{domain}  →  A  →  {context['local_ip']}[/dim]

[cyan]2.[/cyan] Configure o AdGuard para resolver o domínio internamente:
   [dim]Acesse http://{context['local_ip']}:3000 após o primeiro boot[/dim]

[cyan]3.[/cyan] Suba os serviços:
   [dim]docker compose -f output/docker-compose.yml up -d[/dim]

[cyan]4.[/cyan] Configure o Authentik:
   [dim]https://auth.{domain}[/dim]
   [dim]Veja docs/authentik-setup.md para o passo a passo[/dim]

[cyan]5.[/cyan] Leia docs/post-setup.md para configurações adicionais
""",
        title="[bold]Setup concluído[/bold]",
        border_style="green"
    ))


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--dry-run", is_flag=True, help="Mostra o contexto sem gerar arquivos")
def main(dry_run: bool):
    """Homeserver setup — gera docker-compose.yml, .env e configurações."""
    services_config = yaml.safe_load(CONFIG.read_text())

    answers = ask_questions(services_config)
    env_info = run_environment_checks(answers)

    # Contexto completo para os templates
    context = {
        **answers,
        **env_info,
        # Secrets gerados automaticamente
        "authentik_secret_key": generate_secret(50),
        "authentik_pg_password": generate_secret(32),
        "nextcloud_db_password": generate_secret(32) if answers["enable_nextcloud"] else "",
        "immich_db_password": generate_secret(32) if answers["enable_immich"] else "",
        "wireguard_peers": "laptop,phone",  # default, usuário pode editar no .env
    }

    if dry_run:
        import json
        # Omite secrets do dry-run
        safe = {k: v for k, v in context.items() if "password" not in k and "secret" not in k}
        console.print_json(json.dumps(safe, indent=2))
        return

    render_templates(context)
    print_next_steps(context)


if __name__ == "__main__":
    main()

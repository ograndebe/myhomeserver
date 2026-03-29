# AGENTS.md — Homeserver Setup Script

## Project Overview

This repository contains an interactive Python script (`setup.py`) that provisions a home server
using Docker Compose. It uses `uv` for dependency management and generates configuration files
from Jinja2 templates.

## Running the Script

```bash
# Execute the setup (installs dependencies via uv automatically)
./setup.py

# Dry run — shows context without generating files
./setup.py --dry-run

# After generation, bring up services
docker compose -f output/docker-compose.yml up -d
```

## Dependencies

Managed via `uv` inline script metadata (PEP 723). Dependencies are declared in the script header:

```python
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
```

## Code Style Guidelines

### General Principles

- **PEP 8** compliance for Python code
- Use **type hints** for function signatures and variables
- Prefer **explicit over implicit** — clear intent over clever code
- **No premature optimization** — write readable code first
- **DRY** — avoid duplication; use Jinja2 templates for repetitive config patterns

### Python Conventions

#### Imports

- Standard library imports first
- Third-party imports second (alphabetical)
- Local imports last
- Use absolute imports when possible
- Separate import groups with a single blank line

```python
import os
import socket
import subprocess
from pathlib import Path

import click
import questionary
import yaml
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
```

#### Naming Conventions

| Element          | Convention        | Example                          |
|------------------|-------------------|----------------------------------|
| Functions/methods| snake_case        | `get_local_ip()`, `render_templates()` |
| Classes          | PascalCase        | `DockerService`, `ConfigBuilder` |
| Constants        | SCREAMING_SNAKE   | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Variables        | snake_case        | `storage_path`, `local_ip`       |
| Private methods  | _prefixed         | `_validate_config()`             |
| Type aliases     | PascalCase suffix | `ConfigDict`, `ServiceList`     |

#### Type Hints

Always use type hints for function signatures. Use `Optional[X]` or `X | None` for nullable types.

```python
def get_local_ip() -> str:
    ...

def check_docker() -> dict[str, str | None]:
    ...

def ask_questions(services_config: dict) -> dict:
    ...
```

#### Docstrings

Use docstrings for all public functions and classes. Follow Google style:

```python
def get_disk_info(path: str) -> dict:
    """Retorna informações de disco para o caminho informado.

    Args:
        path: Caminho do filesystem a verificar.

    Returns:
        Dict com free_gb, total_gb e ok (bool).
    """
    ...
```

#### Error Handling

- Use specific exception types when possible
- Catch exceptions at appropriate levels
- Provide context in error messages
- Use early returns to reduce nesting

```python
def check_docker() -> dict:
    result = {"docker": None, "compose": None}
    try:
        r = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"],
                           capture_output=True, text=True)
        result["docker"] = r.stdout.strip() if r.returncode == 0 else None
    except FileNotFoundError:
        pass
    return result
```

#### Function Structure

- Keep functions focused (single responsibility)
- Maximum ~50 lines per function
- Use helper functions for complex logic
- Group related functions with section comments:

```python
# ── Descoberta do ambiente ────────────────────────────────────────────────────

def get_local_ip() -> str:
    ...
```

### Jinja2 Templates

Templates live in `templates/` directory. Generated files go to `output/`.

#### Template Guidelines

- Always include a header comment explaining the file is auto-generated
- Use `trim_blocks=True` and `lstrip_blocks=True` in the Jinja2 Environment
- Indent Jinja control structures inside YAML for readability
- Group service blocks with comment headers (`# ── Service Name ──`)

```jinja2
# docker-compose.yml — gerado automaticamente pelo setup.py
# NÃO edite este arquivo diretamente. Edite os templates e execute ./setup.py novamente.

services:

  # ── Traefik ──────────────────────────────────────────────────────────────
  traefik:
    image: traefik:v3.1
    ...
```

### Configuration Files

- `config/services.yml` — single source of truth for service definitions
- Use YAML for all config; parse with `yaml.safe_load()`
- Keep sensitive values in `.env` (never commit)

### Docker Compose Conventions

- Use named volumes (not anonymous)
- Always specify `restart: unless-stopped` for services
- Include health checks for database services
- Use specific image tags (avoid `latest` except for edge cases)
- Separate networks: `proxy` (exposed) vs `internal` (internal only)

### File Organization

```
.
├── setup.py              # Entry point (executable script)
├── config/
│   └── services.yml       # Service definitions (single source of truth)
├── templates/
│   ├── docker-compose.yml.j2
│   ├── .env.j2
│   ├── traefik/          # Traefik static config
│   ├── adguard/           # AdGuard static config
│   └── services/         # Service fragments (jellyfin.j2, arr-stack.j2, etc.)
├── output/               # Generated files (gitignored)
└── docs/                 # Documentation
```

## Important Rules

1. **Never edit generated files directly** — always modify templates and re-run `setup.py`
2. **Never commit secrets** — `output/` and `*.env` are in `.gitignore`
3. **Keep templates idempotent** — running `setup.py` multiple times should be safe
4. **Use `uv` for Python** — don't assume `pip` or `python3` are available in the target environment
5. **Port 80/443 required** — Traefik needs these for Let's Encrypt challenges

## Adding a New Service

1. Add service definition to `config/services.yml` (under `optional:`)
2. Create template fragment in `templates/services/<service>.j2`
3. Add template inclusion to `templates/docker-compose.yml.j2` under the appropriate conditional
4. Test with `./setup.py --dry-run` to verify template rendering
5. Update `docs/post-setup.md` if service requires special configuration

## Documentation

- `CONTEXT.md` — Technical specification (authoritative reference)
- `docs/post-setup.md` — Post-installation instructions
- `docs/authentik-setup.md` — SSO configuration guide

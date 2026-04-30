# AGENTS.md — Homeserver Setup Script

## Project Overview

Interactive Python script (`setup.py`) that provisions a home server using Docker Compose.
Generates config files from Jinja2 templates driven by `config/services.yml`.

## Commands

```bash
./setup.py                     # Interactive setup (installs deps via uv automatically)
./setup.py --dry-run           # Shows rendered context without generating files
docker compose -f output/docker-compose.yml up -d          # Start services
docker compose -f output/docker-compose.yml up -d --force-recreate  # Rebuild after re-run
```

## Architecture

- **Traefik** — reverse proxy + wildcard TLS (Cloudflare DNS challenge)
- **AdGuard Home** — local DNS, resolves `*.domain.com` to internal IP
- **WireGuard** — VPN for remote access (UDP 51820)
- **Authentik** — centralized SSO for all services
- **Jellyfin** — includes *arr stack (Radarr, Sonarr, Prowlarr, qBittorrent, Bazarr) automatically
- **Nextcloud** — personal storage (subdomain: `files.`)
- **Immich** — photo backup (subdomain: `photos.`)

## Key Directories

| Path | Purpose |
|------|---------|
| `config/services.yml` | Single source of truth for service definitions |
| `templates/*.j2` | Jinja2 templates (docker-compose, .env, service configs) |
| `output/` | Generated files — **gitignored, never edit directly** |
| `docs/` | Post-setup and Authentik guides |

## Critical Rules

1. **Never edit files in `output/`** — modify templates and re-run `./setup.py`
2. **Never commit secrets** — `*.env` and `output/` are gitignored
3. **Templates must be idempotent** — re-running `setup.py` reuses existing secrets from `output/.env`
4. **Use `uv` for Python** — shebang is `#!/usr/bin/env -S uv run --script` (PEP 723)
5. **Port 80/443 required** — Traefik needs them for Let's Encrypt challenges
6. **AdGuard dirs need chmod 777** — `create_data_directories()` sets this explicitly

## Adding a New Service

1. Add definition to `config/services.yml` under `optional:`
2. Create template fragment in `templates/services/<service>.j2`
3. Add conditional include in `templates/docker-compose.yml.j2`
4. Add data directories in `create_data_directories()` if needed
5. Test with `./setup.py --dry-run`

## Conventions

- Docstrings in **Portuguese** (Google style)
- Section dividers: `# ── Section Name ──` with dashes to line end
- Jinja2 env uses `trim_blocks=True` and `lstrip_blocks=True`
- Docker services use `restart: unless-stopped`, specific image tags (no `latest`)
- Two networks: `proxy` (exposed) and `internal` (isolated)

## No Tests / Linting

This repo has no test suite, linter, or type checker. Verify changes by running `./setup.py --dry-run` and inspecting generated output.

## Documentation

- `CONTEXT.md` — Technical specification (authoritative)
- `docs/post-setup.md` — Post-installation instructions
- `docs/authentik-setup.md` — SSO configuration guide

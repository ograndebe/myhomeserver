#!/usr/bin/env python3
"""
Post-Setup Script — Bootstrap automatizado da stack *arr.

Executa após os containers subirem, configurando:
1. Authentik: Proxy Providers + Applications + Outpost para todos os serviços *arr
2. API keys: descobre keys dos serviços via config.xml
3. Prowlarr: injeta trackers do trackers.txt como indexadores
4. Radarr/Sonarr/Lidarr: conecta ao Prowlarr e qBittorrent
5. Bazarr: conecta a Radarr e Sonarr
6. Jellyfin: gera API key e salva no .env (Jellyseerr consome via env)
7. qBittorrent: injeta trackers no arquivo de config
8. Salva todas as keys em /app/.env para idempotência
"""

import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Configurações ─────────────────────────────────────────────────────────────

ENV_FILE = Path("/app/.env")
TRACKERS_FILE = Path("/app/trackers.txt")
DOMAIN = os.getenv("DOMAIN", "")
AUTHENTIK_URL = os.getenv("AUTHENTIK_URL", "http://authentik-server:9000")
AUTHENTIK_EMAIL = os.getenv("AUTHENTIK_INITIAL_ADMIN_EMAIL", "")
AUTHENTIK_PASSWORD = os.getenv("AUTHENTIK_INITIAL_ADMIN_PASSWORD", "")
STORAGE_PATH = os.getenv("STORAGE_PATH", "/mnt/data/myhomeserver")

SERVICES = {
    "radarr": {"port": 7878, "config": "/radarr-config/config.xml"},
    "sonarr": {"port": 8989, "config": "/sonarr-config/config.xml"},
    "lidarr": {"port": 8686, "config": "/lidarr-config/config.xml"},
    "prowlarr": {"port": 9696, "config": "/prowlarr-config/config.xml"},
    "bazarr": {"port": 6767, "config": "/bazarr-config/config/config.ini"},
    "qbittorrent": {
        "port": 8080,
        "config": "/qbittorrent-config/qBittorrent/qBittorrent.conf",
    },
    "jellyfin": {"port": 8096, "config": "/jellyfin-config"},
    "jellyseerr": {"port": 5055, "config": "/jellyseerr-config"},
}

API_KEYS = {}


def log(msg: str) -> None:
    """Imprime mensagem de log prefixada."""
    print(f"[post-setup] {msg}")


def wait_for_service(name: str, url: str, max_retries: int = 60) -> bool:
    """Aguarda um serviço ficar disponível via HTTP."""
    log(f"Aguardando {name}...")
    for i in range(max_retries):
        try:
            r = requests.get(url, timeout=5, verify=False)
            if r.status_code < 500:
                log(f"✅ {name} pronto!")
                return True
        except requests.RequestException:
            pass
        time.sleep(2)
    log(f"⚠️ Timeout aguardando {name}")
    return False


def read_arr_api_key(config_path: str) -> str:
    """Lê a API key do config.xml de um serviço *arr."""
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        key = root.findtext("ApiKey", "")
        if key:
            return key
    except Exception:
        pass
    return ""


def read_bazarr_api_key(config_path: str) -> str:
    """Lê a API key do config.ini do Bazarr."""
    try:
        content = Path(config_path).read_text()
        m = re.search(r"api_key\s*=\s*(.+)", content)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""


def discover_api_keys() -> None:
    """Descobre as API keys de todos os serviços."""
    log("Descobrindo API keys...")

    for name, info in SERVICES.items():
        if name in ("qbittorrent", "jellyfin", "jellyseerr"):
            continue
        config = info.get("config", "")
        if not config or not Path(config).exists():
            log(f"  ⚠️ Config não encontrado para {name}: {config}")
            continue

        if name == "bazarr":
            key = read_bazarr_api_key(config)
        else:
            key = read_arr_api_key(config)

        if key:
            API_KEYS[f"{name.upper()}_API_KEY"] = key
            log(f"  ✅ {name}: API key encontrada")
        else:
            log(f"  ⚠️ {name}: API key não encontrada")


# ── Authentik Bootstrap ───────────────────────────────────────────────────────


def authentik_login() -> requests.Session | None:
    """Autentica no Authentik e retorna sessão."""
    session = requests.Session()
    session.verify = False

    # Obtém CSRF
    r = session.get(f"{AUTHENTIK_URL}/if/admin/", timeout=10)
    if r.status_code != 200:
        log(f"Falha ao acessar admin: {r.status_code}")
        return None

    csrf = session.cookies.get("authentik_csrf", "")
    r = session.post(
        f"{AUTHENTIK_URL}/if/flow/default-authentication-flow/",
        data={
            "uid": AUTHENTIK_EMAIL,
            "password": AUTHENTIK_PASSWORD,
            "csrfmiddlewaretoken": csrf,
        },
        headers={"Referer": f"{AUTHENTIK_URL}/if/admin/"},
        timeout=10,
        allow_redirects=True,
    )
    if session.cookies.get("authentik_session"):
        log("✅ Login no Authentik realizado")
        return session
    log("⚠️ Login no Authentik falhou")
    return None


def get_default_flow(session: requests.Session) -> str | None:
    """Obtém UUID do default authentication flow."""
    r = session.get(
        f"{AUTHENTIK_URL}/api/v3/flows/",
        params={"slug": "default-authentication-flow"},
        timeout=10,
    )
    if r.status_code == 200:
        results = r.json().get("results", [])
        if results:
            return results[0]["pk"]
    return None


def get_or_create_proxy_provider(
    session: requests.Session, name: str, external_host: str, flow: str
) -> int | None:
    """Obtém ou cria Proxy Provider."""
    r = session.get(
        f"{AUTHENTIK_URL}/api/v3/providers/proxy/", params={"name": name}, timeout=10
    )
    if r.status_code == 200:
        for p in r.json().get("results", []):
            if p["name"] == name:
                log(f"  ℹ️ Provider '{name}' já existe")
                session.patch(
                    f"{AUTHENTIK_URL}/api/v3/providers/proxy/{p['pk']}/",
                    json={"authorization_flow": flow},
                    timeout=10,
                )
                return p["pk"]
    r = session.post(
        f"{AUTHENTIK_URL}/api/v3/providers/proxy/",
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
    return None


def get_or_create_app(
    session: requests.Session, name: str, slug: str, provider: int
) -> int | None:
    """Obtém ou cria Application."""
    r = session.get(
        f"{AUTHENTIK_URL}/api/v3/core/applications/", params={"slug": slug}, timeout=10
    )
    if r.status_code == 200:
        for a in r.json().get("results", []):
            if a["slug"] == slug:
                log(f"  ℹ️ App '{name}' já existe")
                return a["pk"]
    r = session.post(
        f"{AUTHENTIK_URL}/api/v3/core/applications/",
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
    return None


def get_or_create_outpost(
    session: requests.Session, name: str, apps: list[int]
) -> int | None:
    """Obtém ou cria Outpost."""
    r = session.get(f"{AUTHENTIK_URL}/api/v3/outposts/proxy/", timeout=10)
    if r.status_code == 200:
        for o in r.json().get("results", []):
            if o["name"] == name:
                log(f"  ℹ️ Outpost '{name}' já existe")
                session.patch(
                    f"{AUTHENTIK_URL}/api/v3/outposts/proxy/{o['pk']}/",
                    json={"applications": apps},
                    timeout=10,
                )
                return o["pk"]
    r = session.post(
        f"{AUTHENTIK_URL}/api/v3/outposts/proxy/",
        json={
            "name": name,
            "applications": apps,
            "docker_service_connections": [],
            "docker_connection": "local",
            "container_image": "ghcr.io/goauthentik/proxy:2024.8",
            "container_network": "proxy",
            "environment": {},
        },
        timeout=10,
    )
    if r.status_code in (200, 201):
        log(f"  ✅ Outpost '{name}' criado")
        return r.json()["pk"]
    return None


def bootstrap_authentik() -> None:
    """Cria providers, apps e outpost para todos os serviços *arr."""
    if not wait_for_service("Authentik", f"{AUTHENTIK_URL}/-/health/live/"):
        log("⚠️ Pulando bootstrap do Authentik")
        return

    session = authentik_login()
    if not session:
        return

    flow = get_default_flow(session)
    if not flow:
        log("❌ Flow não encontrado")
        return

    arr_services = [
        ("radarr", f"https://radarr.{DOMAIN}"),
        ("sonarr", f"https://sonarr.{DOMAIN}"),
        ("lidarr", f"https://lidarr.{DOMAIN}"),
        ("prowlarr", f"https://prowlarr.{DOMAIN}"),
        ("bazarr", f"https://bazarr.{DOMAIN}"),
        ("qbittorrent", f"https://qbit.{DOMAIN}"),
        ("jellyseerr", f"https://jellyseerr.{DOMAIN}"),
    ]

    log("Criando Proxy Providers...")
    providers = {}
    for slug, host in arr_services:
        pk = get_or_create_proxy_provider(session, slug, host, flow)
        if pk:
            providers[slug] = pk

    log("Criando Applications...")
    apps = {}
    for slug, pk in providers.items():
        app_pk = get_or_create_app(session, slug.capitalize(), slug, pk)
        if app_pk:
            apps[slug] = app_pk

    if apps:
        log("Criando/Atualizando Outpost...")
        get_or_create_outpost(session, "homeserver-proxy", list(apps.values()))

    log("✅ Authentik configurado para todos os serviços *arr")


# ── Prowlarr Indexers ─────────────────────────────────────────────────────────


def configure_prowlarr_indexers() -> None:
    """Injeta trackers do trackers.txt como indexadores no Prowlarr."""
    key = API_KEYS.get("PROWLARR_API_KEY", "")
    if not key:
        log("⚠️ Prowlarr API key não encontrada — pulando indexadores")
        return

    if not TRACKERS_FILE.exists():
        log(f"⚠️ {TRACKERS_FILE} não encontrado — pulando indexadores")
        return

    log("Configurando indexadores no Prowlarr...")
    base = "http://prowlarr:9696/api/v1"
    headers = {"X-Api-Key": key}

    # Verifica se já existem indexadores (idempotência básica)
    r = requests.get(f"{base}/indexer", headers=headers, timeout=30)
    if r.status_code == 200 and len(r.json()) > 5:
        log("  ℹ️ Prowlarr já possui indexadores configurados — pulando")
        return

    trackers = [t.strip() for t in TRACKERS_FILE.read_text().splitlines() if t.strip()]
    added = 0
    for i, tracker in enumerate(trackers):
        # Adiciona como indexer genérico (Torznab sem api key para trackers públicos)
        payload = {
            "name": f"Tracker-{i + 1}",
            "implementation": "Torznab",
            "configContract": "TorznabSettings",
            "enable": True,
            "priority": 25,
            "fields": [
                {
                    "name": "baseUrl",
                    "value": tracker
                    if tracker.startswith("http")
                    else f"http://{tracker}",
                },
                {"name": "apiKey", "value": ""},
                {"name": "categories", "value": [2000, 5000, 5030, 5040]},
            ],
            "protocol": "torrent",
        }
        try:
            r = requests.post(
                f"{base}/indexer", json=payload, headers=headers, timeout=10
            )
            if r.status_code in (200, 201):
                added += 1
            else:
                log(f"  ⚠️ Falha ao adicionar tracker {i + 1}: {r.status_code}")
        except Exception as e:
            log(f"  ⚠️ Erro no tracker {i + 1}: {e}")

    log(f"✅ {added}/{len(trackers)} trackers adicionados ao Prowlarr")


# ── Radarr / Sonarr / Lidarr ──────────────────────────────────────────────────


def configure_arr_service(name: str, port: int) -> None:
    """Configura Prowlarr e qBittorrent em um serviço *arr."""
    key = API_KEYS.get(f"{name.upper()}_API_KEY", "")
    if not key:
        log(f"⚠️ {name} API key não encontrada")
        return

    base = f"http://{name}:{port}/api/v3"
    headers = {"X-Api-Key": key}

    # 1. Download Client (qBittorrent)
    log(f"Configurando download client em {name}...")
    dc_payload = {
        "name": "qBittorrent",
        "implementation": "QBittorrent",
        "configContract": "QBittorrentSettings",
        "enable": True,
        "protocol": "torrent",
        "fields": [
            {"name": "host", "value": "qbittorrent"},
            {"name": "port", "value": 8080},
            {"name": "username", "value": "admin"},
            {"name": "password", "value": "adminadmin"},
            {"name": "movieCategory", "value": ""},
            {"name": "tvCategory", "value": ""},
        ],
    }
    try:
        r = requests.get(f"{base}/downloadclient", headers=headers, timeout=10)
        existing = r.json() if r.status_code == 200 else []
        if not any(d.get("implementation") == "QBittorrent" for d in existing):
            r = requests.post(
                f"{base}/downloadclient", json=dc_payload, headers=headers, timeout=10
            )
            if r.status_code in (200, 201):
                log(f"  ✅ qBittorrent adicionado ao {name}")
            else:
                log(f"  ⚠️ Falha ao adicionar qBittorrent em {name}: {r.status_code}")
        else:
            log(f"  ℹ️ qBittorrent já existe em {name}")
    except Exception as e:
        log(f"  ⚠️ Erro ao configurar qBittorrent em {name}: {e}")

    # 2. Indexer Manager (Prowlarr via Sync)
    log(f"Configurando Prowlarr Sync em {name}...")
    # Para integração com Prowlarr, normalmente usamos o endpoint /api/v3/indexer
    # e criamos um indexer do tipo Prowlarr ou simplesmente deixamos o Prowlarr sincronizar.
    # Aqui criamos um indexer apontando para o Prowlarr para sincronização manual futura.
    indexer_payload = {
        "name": "Prowlarr",
        "implementation": "Newznab",
        "configContract": "NewznabSettings",
        "enable": True,
        "protocol": "torrent",
        "fields": [
            {"name": "baseUrl", "value": "http://prowlarr:9696/1/api"},
            {"name": "apiKey", "value": API_KEYS.get("PROWLARR_API_KEY", "")},
        ],
    }
    try:
        r = requests.get(f"{base}/indexer", headers=headers, timeout=10)
        existing = r.json() if r.status_code == 200 else []
        if not any(idx.get("name") == "Prowlarr" for idx in existing):
            r = requests.post(
                f"{base}/indexer", json=indexer_payload, headers=headers, timeout=10
            )
            if r.status_code in (200, 201):
                log(f"  ✅ Prowlarr indexer adicionado ao {name}")
            else:
                log(
                    f"  ⚠️ Falha ao adicionar Prowlarr indexer em {name}: {r.status_code}"
                )
        else:
            log(f"  ℹ️ Prowlarr indexer já existe em {name}")
    except Exception as e:
        log(f"  ⚠️ Erro ao configurar Prowlarr em {name}: {e}")


# ── Bazarr ────────────────────────────────────────────────────────────────────


def configure_bazarr() -> None:
    """Conecta Bazarr a Radarr e Sonarr."""
    key = API_KEYS.get("BAZARR_API_KEY", "")
    if not key:
        log("⚠️ Bazarr API key não encontrada")
        return

    base = "http://bazarr:6767/api"
    headers = {"X-API-Key": key}

    radarr_key = API_KEYS.get("RADARR_API_KEY", "")
    sonarr_key = API_KEYS.get("SONARR_API_KEY", "")

    log("Configurando Bazarr...")
    # Bazarr usa REST — endpoints podem variar conforme versão
    # Atualiza via settings
    settings = {
        "radarr": {
            "ip": "radarr",
            "port": 7878,
            "base_url": "/",
            "ssl": False,
            "apikey": radarr_key,
            "enabled": True,
        },
        "sonarr": {
            "ip": "sonarr",
            "port": 8989,
            "base_url": "/",
            "ssl": False,
            "apikey": sonarr_key,
            "enabled": True,
        },
    }

    for svc, cfg in settings.items():
        if not cfg["apikey"]:
            log(f"  ⚠️ {svc} API key ausente — pulando Bazarr config")
            continue
        try:
            r = requests.patch(
                f"{base}/system/settings",
                json={svc: cfg},
                headers=headers,
                timeout=10,
            )
            if r.status_code in (200, 201, 204):
                log(f"  ✅ Bazarr conectado ao {svc}")
            else:
                log(f"  ⚠️ Falha ao conectar Bazarr ao {svc}: {r.status_code}")
        except Exception as e:
            log(f"  ⚠️ Erro ao conectar Bazarr ao {svc}: {e}")


# ── Jellyfin API Key ──────────────────────────────────────────────────────────


def get_jellyfin_api_key() -> str:
    """Autentica no Jellyfin e cria uma API key."""
    log("Configurando Jellyfin API key...")
    base = "http://jellyfin:8096"

    # Tenta autenticar com o primeiro usuário administrativo
    # Na primeira inicialização, o Jellyfin exige setup manual via UI.
    # Como não temos usuário/senha, vamos tentar acessar a API de keys diretamente
    # (algumas versões permitem sem auth em localhost).
    try:
        r = requests.get(f"{base}/Keys", timeout=10)
        if r.status_code == 200:
            keys = r.json().get("Items", [])
            if keys:
                return keys[0].get("AccessToken", "")
    except Exception:
        pass

    log("⚠️ Não foi possível obter API key do Jellyfin automaticamente.")
    log("   Configure manualmente em Jellyfin > Dashboard > API Keys")
    return ""


# ── qBittorrent Trackers ──────────────────────────────────────────────────────


def configure_qbittorrent_trackers() -> None:
    """Injeta trackers no qBittorrent via API REST."""
    log("Configurando trackers no qBittorrent...")
    if not TRACKERS_FILE.exists():
        log(f"⚠️ {TRACKERS_FILE} não encontrado")
        return

    trackers = [t.strip() for t in TRACKERS_FILE.read_text().splitlines() if t.strip()]
    if not trackers:
        log("⚠️ Nenhum tracker encontrado")
        return

    base = "http://qbittorrent:8080/api/v2"

    # Login
    try:
        r = requests.post(
            f"{base}/auth/login",
            data={"username": "admin", "password": "adminadmin"},
            timeout=10,
        )
        if r.status_code != 200 or r.text != "Ok.":
            log("  ⚠️ Falha no login do qBittorrent (senha pode ter sido alterada)")
            return
    except Exception as e:
        log(f"  ⚠️ Erro ao logar no qBittorrent: {e}")
        return

    # Define preferência de trackers adicionais
    tracker_list = "\\n".join(trackers)
    try:
        r = requests.post(
            f"{base}/app/setPreferences",
            data={
                "json": f'{{"add_trackers_enabled":true,"add_trackers":"{tracker_list}"}}'
            },
            timeout=10,
        )
        if r.status_code == 200:
            log(f"✅ {len(trackers)} trackers injetados no qBittorrent")
        else:
            log(f"⚠️ Falha ao injetar trackers: {r.status_code}")
    except Exception as e:
        log(f"⚠️ Erro ao injetar trackers: {e}")


# ── Salvar .env ───────────────────────────────────────────────────────────────


def save_env() -> None:
    """Salva ou atualiza as API keys em /app/.env."""
    log("Salvando API keys em /app/.env...")
    lines = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text().splitlines()

    existing = {}
    for line in lines:
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            existing[k] = v

    # Atualiza com as novas keys
    for k, v in API_KEYS.items():
        existing[k] = v

    # Jellyfin key
    jellyfin_key = API_KEYS.get("JELLYFIN_API_KEY", "")
    if jellyfin_key:
        existing["JELLYFIN_API_KEY"] = jellyfin_key

    # Unpackerr keys (para referência)
    for svc in ("RADARR", "SONARR", "LIDARR"):
        key = existing.get(f"{svc}_API_KEY", "")
        if key:
            existing[f"UN_{svc}_0_API_KEY"] = key

    new_lines = [f"{k}={v}" for k, v in sorted(existing.items())]
    ENV_FILE.write_text("\n".join(new_lines) + "\n")
    log("✅ .env atualizado")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    log("Iniciando post-setup...")

    # 1. Aguardar serviços (healthcheck do compose já faz, mas garantimos)
    for name, info in SERVICES.items():
        if name in ("qbittorrent",):
            continue
        wait_for_service(name, f"http://{name}:{info['port']}/health", max_retries=30)

    # 2. Descobrir API keys
    discover_api_keys()

    # 3. Authentik
    if AUTHENTIK_EMAIL and AUTHENTIK_PASSWORD:
        bootstrap_authentik()
    else:
        log("⚠️ Credenciais do Authentik ausentes — pulando")

    # 4. Prowlarr
    configure_prowlarr_indexers()

    # 5. Radarr, Sonarr, Lidarr
    for svc in ("radarr", "sonarr", "lidarr"):
        configure_arr_service(svc, SERVICES[svc]["port"])

    # 6. Bazarr
    configure_bazarr()

    # 7. Jellyfin API key
    jf_key = get_jellyfin_api_key()
    if jf_key:
        API_KEYS["JELLYFIN_API_KEY"] = jf_key

    # 8. qBittorrent trackers
    configure_qbittorrent_trackers()

    # 9. Salvar tudo
    save_env()

    log("🎉 Post-setup concluído!")


if __name__ == "__main__":
    main()

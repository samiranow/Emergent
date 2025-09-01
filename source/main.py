import os
import re
import json
import socket
import random
import asyncio
import logging
import base64
import requests
import httpx
import urllib3
import zoneinfo
import ipaddress
from urllib.parse import quote, urlsplit, urlunsplit, unquote
from datetime import datetime

# ============================== Configuration ==============================

URLS = [
    "https://www.v2nodes.com/subscriptions/country/al/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/ar/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/au/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/at/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/bh/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/be/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/bo/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/br/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/bg/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/ca/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/cn/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/co/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/cy/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/cz/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/dk/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/ee/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/fi/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/fr/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/de/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/gt/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/hk/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/hu/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/is/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/in/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/id/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/il/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/it/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/jp/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/kz/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/lv/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/my/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/md/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/no/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/pe/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/pl/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/pt/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/pr/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/ro/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/ru/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/sg/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/kr/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/es/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/se/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/ch/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/tw/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/th/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/nl/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/tr/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/ua/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/gb/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/us/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/vn/?key=769B61EA877690D",
]

OUTPUT_DIR = "configs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

ZONE = zoneinfo.ZoneInfo("Asia/Tehran")

# ============================== Base64 / Geo ===============================

geo_cache: dict[str, str] = {}

def b64_decode(s: str) -> str:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(s + pad).decode(errors="ignore")

def b64_encode(s: str) -> str:
    return base64.b64encode(s.encode()).decode()

def b64url_decode(s: str) -> bytes:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)

def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def country_flag(code: str) -> str:
    if not code:
        return "🏳️"
    c = code.strip().upper()
    if len(c) != 2 or not c.isalpha():
        return "🏳️"
    return chr(ord(c[0]) + 127397) + chr(ord(c[1]) + 127397)

def get_country_by_ip(ip: str) -> str:
    if ip in geo_cache:
        return geo_cache[ip]
    try:
        r = requests.get(f"https://ipwhois.app/json/{ip}", timeout=5)
        if r.status_code == 200:
            code = r.json().get("country_code", "unknown").lower()
            geo_cache[ip] = code
            return code
    except Exception as e:
        logging.warning(f"Geolocation lookup failed for {ip}: {e}")
    geo_cache[ip] = "unknown"
    return "unknown"

# ============================== Fetch / Decode =============================

def fetch_data(url: str, timeout: int = 10) -> str:
    headers = {"User-Agent": CHROME_UA}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logging.error(f"Download error for {url}: {e}")
        return ""

def maybe_base64_decode(s: str) -> str:
    s = s.strip()
    try:
        decoded = b64_decode(s)
        if "://" in decoded:
            return decoded.strip()
    except Exception:
        pass
    return s

# ============================== Parsing / Netloc ===========================

def normalize_proto(proto: str) -> str:
    p = proto.lower()
    if p in ("ss", "shadowsocks"):
        return "shadowsocks"
    if p in ("hy2", "hysteria2"):
        return "hysteria2"
    if p.startswith("hysteria"):
        return "hysteria"
    return p

def detect_protocol(link: str) -> str:
    m = re.match(r"([a-z0-9+.-]+)://", link.strip().lower())
    if not m:
        return "unknown"
    return normalize_proto(m.group(1))

def is_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False

def split_host_port(raw_hostport: str) -> tuple[str, str]:
    """
    Extract host and port from a netloc or 'host:port' string.
    - Strips userinfo if present (user:pass@host:port)
    - Handles IPv6 with or without brackets
    - Returns (host, port_or_empty)
    """
    hp = unquote(raw_hostport.strip())
    if "@" in hp:
        hp = hp.split("@", 1)[1]
    if hp.startswith("["):
        m = re.match(r"^\[(.+?)\](?::(\d+))?$", hp)
        if m:
            return m.group(1), (m.group(2) or "")
    if hp.count(":") > 1:
        return hp, ""  # likely raw IPv6 without port
    if ":" in hp:
        h, p = hp.rsplit(":", 1)
        return h, p
    return hp, ""

def format_hostport(host: str, port: str | int | None) -> str:
    """Build a valid netloc host:port, adding brackets for IPv6."""
    p = str(port) if port else "443"
    h = f"[{host}]" if (":" in host and not host.startswith("[")) else host
    return f"{h}:{p}"

def extract_host(link: str, proto: str) -> str:
    """
    Return 'host:port' (no userinfo) if possible, else ''.
    Handles vmess/ss/ssr explicitly; falls back to URL parsing for URL-like schemes.
    """
    try:
        if proto == "vmess":
            cfg = json.loads(b64_decode(link.split("://", 1)[1]))
            host = str(cfg.get("add", "")).strip()
            port_val = cfg.get("port", "")
            port = str(port_val).strip() if port_val != "" else ""
            return f"{host}:{port}" if host and port else host or ""

        if proto == "shadowsocks":
            body = link.split("ss://", 1)[1]
            if "#" in body:
                body = body.split("#", 1)[0]
            if "@" in body:
                _creds, hostport = body.split("@", 1)
                return hostport
            try:
                decoded = b64_decode(body)
                if "@" in decoded:
                    _creds, hostport = decoded.split("@", 1)
                    return hostport
            except Exception:
                pass
            return ""

        if proto == "ssr":
            raw = link.split("ssr://", 1)[1]
            decoded = b64url_decode(raw).decode(errors="ignore")
            main = decoded.split("/?", 1)[0]
            parts = main.split(":")
            if len(parts) >= 2:
                return f"{parts[0]}:{parts[1]}"
            return ""

        p = urlsplit(link)
        netloc = p.netloc
        if "@" in netloc:
            netloc = netloc.split("@", 1)[1]
        return netloc
    except Exception as e:
        logging.debug(f"extract_host error for [{proto}] {link}: {e}")
        return ""

# ============================== Async Ping =================================

_connection_limit = asyncio.Semaphore(5)

async def run_ping_once(client: httpx.AsyncClient, host: str, timeout: int = 10, retries: int = 3) -> dict:
    """
    Ping a host via check-host.net with retries.
    'host' must be a plain host/IP (no userinfo, no port).
    """
    if not host:
        return {}
    base = "https://check-host.net"

    async with _connection_limit:
        for attempt in range(1, retries + 1):
            try:
                r1 = await client.get(
                    f"{base}/check-ping",
                    params={"host": host},
                    headers={"Accept": "application/json"},
                    timeout=timeout,
                )
                if r1.status_code == 503:
                    wait = random.uniform(2, 5)
                    logging.warning(f"503 for {host}, retry {attempt}/{retries} after {wait:.1f}s")
                    await asyncio.sleep(wait)
                    continue

                r1.raise_for_status()
                req_id = r1.json().get("request_id")
                if not req_id:
                    return {}

                for _ in range(10):
                    await asyncio.sleep(2)
                    r2 = await client.get(
                        f"{base}/check-result/{req_id}",
                        headers={"Accept": "application/json"},
                        timeout=timeout,
                    )
                    if r2.status_code == 200 and r2.json():
                        return r2.json()
                break

            except Exception as e:
                logging.error(f"Ping error for {host} (attempt {attempt}): {e}")
                await asyncio.sleep(2)

    return {}

def extract_latency_by_country(results: dict, country_nodes: dict[str, list[str]]) -> dict[str, float]:
    """
    Compute average latency per country based on check-host node results.
    """
    latencies: dict[str, float] = {}
    for country, nodes in country_nodes.items():
        pings: list[float] = []
        for node in nodes:
            entries = results.get(node, [])
            try:
                for status, ping in entries[0]:
                    if status == "OK":
                        pings.append(ping)
            except Exception:
                continue
        latencies[country] = sum(pings) / len(pings) if pings else float("inf")
    return latencies

async def get_nodes_by_country(client: httpx.AsyncClient) -> dict[str, list[str]]:
    """
    Fetch check-host nodes and group them by country code.
    """
    url = "https://check-host.net/nodes/hosts"
    try:
        r = await client.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logging.error(f"Error fetching nodes list: {e}")
        return {}

    mapping: dict[str, list[str]] = {}
    for node, info in data.get("nodes", {}).items():
        loc = info.get("location", [])
        if isinstance(loc, list) and loc:
            mapping.setdefault(str(loc[0]).lower(), []).append(node)
    return mapping

# ============================== Output =====================================

def save_to_file(path: str, lines: list[str]):
    """
    Save a list of configuration lines to a file, creating directories if needed.
    """
    if not lines:
        logging.warning(f"No lines to save: {path}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logging.info(f"Saved: {path} ({len(lines)} lines)")

# ============================== Renaming ===================================

def _build_tag(ip: str) -> str:
    """
    Build a uniform display name: <flag> ShatakVPN <random>.
    """
    country = get_country_by_ip(ip)
    flag = country_flag(country)
    return f"{flag} ShatakVPN {random.randint(100000, 999999)}"

def _resolve_host(host: str) -> str:
    """
    Resolve a hostname to IPv4; if input is already an IP (v4/v6) or invalid hostname, return as-is.
    Avoids IDNA errors by skipping exotic labels.
    """
    host = host.strip()
    if not host:
        return host
    if is_ip(host):
        return host
    # Conservative allowlist for hostnames; skip resolution for weird labels
    if not re.fullmatch(r"[A-Za-z0-9.-]+", host):
        logging.warning(f"Skip resolve invalid host: {host}")
        return host
    try:
        return socket.gethostbyname(host)
    except (socket.gaierror, UnicodeError) as e:
        logging.warning(f"DNS lookup failed for {host}: {e}")
        return host

def rename_vmess(link: str, ip: str, port: str, tag: str) -> str:
    """
    Update vmess JSON (add/port/ps) and keep a fragment for clients that display it.
    """
    try:
        raw = link.split("://", 1)[1]
        cfg = json.loads(b64_decode(raw))
        cfg.update({"add": ip, "port": int(port) if port else 443, "ps": tag})
        new_b64 = b64_encode(json.dumps(cfg, ensure_ascii=False))
        return f"vmess://{new_b64}#{quote(tag)}"
    except Exception as e:
        logging.debug(f"vmess rename error: {e}")
        return link

def rename_shadowsocks(link: str, ip: str, port: str, tag: str) -> str:
    """
    Support both SS forms:
    - ss://base64(method:password)@host:port#name
    - ss://base64(method:password@host:port)#name
    """
    try:
        body = link.split("ss://", 1)[1]
        if "#" in body:
            body = body.split("#", 1)[0]

        method = pwd = None
        if "@" in body:
            creds_part, _hostport = body.split("@", 1)
            try:
                method, pwd = b64_decode(creds_part).split(":", 1)
            except Exception:
                method, pwd = creds_part.split(":", 1)
        else:
            try:
                decoded = b64_decode(body)
                if "@" in decoded and ":" in decoded.split("@", 1)[0]:
                    creds, _hp = decoded.split("@", 1)
                    method, pwd = creds.split(":", 1)
                else:
                    method, pwd = decoded.split(":", 1)
            except Exception:
                pass

        if not (method and pwd):
            return link

        new_creds = b64_encode(f"{method}:{pwd}")
        hp = format_hostport(ip, port or "443")
        return f"ss://{new_creds}@{hp}#{quote(tag)}"
    except Exception as e:
        logging.debug(f"shadowsocks rename error: {e}")
        return link

def rename_ssr(link: str, ip: str, port: str, tag: str) -> str:
    """
    Rewrite SSR main section host:port; if IPv6, keep original (SSR format is IPv4-centric).
    """
    try:
        if ":" in ip and not ip.startswith("["):
            # IPv6 in SSR is ambiguous (colon-delimited main section)
            logging.debug("SSR IPv6 host detected; skipping rename to avoid ambiguity.")
            return link

        raw = link.split("ssr://", 1)[1]
        decoded = b64url_decode(raw).decode(errors="ignore")
        parts = decoded.split("/?", 1)
        main = parts[0]
        tail = "/?" + parts[1] if len(parts) > 1 else ""
        fields = main.split(":")
        if len(fields) < 6:
            return link
        fields[0] = ip
        fields[1] = str(port or "443")
        new_main = ":".join(fields)
        new_decoded = new_main + tail
        new_link = "ssr://" + b64url_encode(new_decoded.encode())
        return f"{new_link}#{quote(tag)}"
    except Exception as e:
        logging.debug(f"ssr rename error: {e}")
        return link

def rename_url_like(link: str, ip: str, port: str, tag: str) -> str:
    """
    Generic URL-style replacer:
    - Preserve userinfo if present
    - Replace host:port (with IPv6 brackets when needed)
    - Preserve path/query
    - Replace fragment with encoded tag
    """
    try:
        p = urlsplit(link)
        userinfo = ""
        hostport = p.netloc
        hp = format_hostport(ip, port or "443")
        if "@" in hostport:
            userinfo, _hp = hostport.split("@", 1)
            new_netloc = f"{userinfo}@{hp}"
        else:
            new_netloc = hp
        new_frag = quote(tag)
        return urlunsplit((p.scheme, new_netloc, p.path, p.query, new_frag))
    except Exception as e:
        logging.debug(f"rename_url_like error: {e}")
        return link

def rename_line(link: str) -> str:
    """
    Route to protocol-specific renamers; default to URL-like behavior.
    """
    proto = detect_protocol(link)
    host_port = extract_host(link, proto)
    if not host_port:
        return link

    host, port = split_host_port(host_port)
    if not port:
        port = "443"

    ip = _resolve_host(host)
    tag = _build_tag(ip)

    if proto == "vmess":
        return rename_vmess(link, ip, port, tag)
    if proto == "shadowsocks":
        return rename_shadowsocks(link, ip, port, tag)
    if proto == "ssr":
        return rename_ssr(link, ip, port, tag)
    return rename_url_like(link, ip, port, tag)

# ============================== Main Flow ==================================

async def main_async():
    now = datetime.now(ZONE).strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"[{now}] Starting download and processing…")

    async with httpx.AsyncClient() as client:
        country_nodes = await get_nodes_by_country(client)

        categorized: dict[str, dict[str, list[tuple[str, str]]]] = {}
        all_pairs: list[tuple[str, str]] = []

        # Fetch and parse all subscription sources
        for url in URLS:
            blob = maybe_base64_decode(fetch_data(url))
            configs = re.findall(r"[a-zA-Z][\w+.-]*://[^\s]+", blob)
            logging.info(f"Fetched {url} → {len(configs)} configs")

            for link in configs:
                proto = detect_protocol(link)
                hostport = extract_host(link, proto)
                if not hostport:
                    continue
                host, _port = split_host_port(hostport)
                if not host:
                    continue
                all_pairs.append((link, host))
                for country in country_nodes:
                    categorized.setdefault(country, {}).setdefault(proto, []).append((link, host))

        # Deduplicate hosts and run ping checks (host only; no userinfo/port)
        hosts = sorted({h for _, h in all_pairs if h})
        tasks = [run_ping_once(client, h) for h in hosts]
        ping_results = await asyncio.gather(*tasks)
        results = dict(zip(hosts, ping_results))

        # For each country, sort links by the country's average latency and emit files
        for country, groups in categorized.items():
            logging.info(f"Processing country: {country}")
            nodes = country_nodes.get(country, [])
            latencies: dict[str, float] = {}

            for host in hosts:
                res = results.get(host, {})
                lat = extract_latency_by_country(res, {country: nodes}).get(country, float("inf"))
                for link, h in all_pairs:
                    if h == host:
                        latencies[link] = lat

            sorted_links = [l for l, _ in sorted(latencies.items(), key=lambda x: x[1])]
            renamed_all = [rename_line(l) for l in sorted_links]

            dest_dir = os.path.join(OUTPUT_DIR, country)
            os.makedirs(dest_dir, exist_ok=True)

            # Per-protocol outputs
            for proto, _items in groups.items():
                proto_list = [l for l in sorted_links if detect_protocol(l) == proto]
                save_to_file(
                    os.path.join(dest_dir, f"{proto}.txt"),
                    [rename_line(l) for l in proto_list]
                )

            # Aggregated outputs
            save_to_file(os.path.join(dest_dir, "all.txt"), renamed_all)
            save_to_file(os.path.join(dest_dir, "light.txt"), renamed_all[:30])

if __name__ == "__main__":
    asyncio.run(main_async())

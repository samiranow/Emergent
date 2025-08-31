#!/usr/bin/env python3
import os
import re
import json
import socket
import random
import asyncio
import logging
import base64
import aiofiles
import httpx
import urllib3
import zoneinfo
from datetime import datetime

# ──────────────── Config from ENV ────────────────
URLS = os.getenv("URLS", "").split(",") if os.getenv("URLS") else [
    "https://www.v2nodes.com/subscriptions/country/de/?key=769B61EA877690D",
    "https://raw.githubusercontent.com/Rayan-Config/C-Sub/refs/heads/main/configs/proxy.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
    "https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/main.txt",
    "https://raw.githubusercontent.com/MahsaNetConfigTopic/config/refs/heads/main/xray_final.txt",
]
OUTPUT_DIR = "configs"
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", 5))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10))
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

ZONE = zoneinfo.ZoneInfo("Asia/Tehran")
connection_limit = asyncio.Semaphore(MAX_CONCURRENCY)
geo_cache: dict[str, str] = {}
dns_cache: dict[str, str] = {}

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

# ──────────────── Helpers ────────────────
def b64_decode(s: str) -> str:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(s + pad).decode(errors="ignore")

def b64_encode(s: str) -> str:
    return base64.b64encode(s.encode()).decode()

def strip_port(host: str) -> str:
    return host.split(":", 1)[0]

def country_flag(code: str) -> str:
    if not code:
        return "🏳️"
    c = code.strip().upper()
    if c == "UNKNOWN" or len(c) != 2 or not c.isalpha():
        return "🏳️"
    return chr(ord(c[0]) + 127397) + chr(ord(c[1]) + 127397)

async def get_country_by_ip(client: httpx.AsyncClient, ip: str) -> str:
    if ip in geo_cache:
        return geo_cache[ip]
    try:
        r = await client.get(f"https://ipwhois.app/json/{ip}", timeout=5)
        if r.status_code == 200:
            code = r.json().get("country_code", "unknown").lower()
            geo_cache[ip] = code
            return code
    except Exception as e:
        logging.warning(f"GeoIP lookup failed for {ip}: {e}")
    geo_cache[ip] = "unknown"
    return "unknown"

async def resolve_dns(host: str) -> str:
    if host in dns_cache:
        return dns_cache[host]
    loop = asyncio.get_event_loop()
    try:
        infos = await loop.getaddrinfo(host, None)
        ip = infos[0][4][0]
        dns_cache[host] = ip
        return ip
    except:
        dns_cache[host] = host
        return host

async def fetch_data(client: httpx.AsyncClient, url: str) -> str:
    headers = {"User-Agent": CHROME_UA}
    try:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logging.error(f"Download error for {url}: {e}")
        return ""

def maybe_base64_decode(s: str) -> str:
    s = s.strip()
    try:
        decoded = b64_decode(s)
        if any(proto in decoded for proto in ("vless://", "vmess://", "trojan://", "ss://")):
            return decoded.strip()
    except Exception:
        pass
    return s

def detect_protocol(link: str) -> str:
    l = link.strip().lower()
    if l.startswith("vless://"):
        return "vless"
    if l.startswith("vmess://"):
        return "vmess"
    if l.startswith("ss://"):
        return "shadowsocks"
    if l.startswith("trojan://"):
        return "trojan"
    return "unknown"

def extract_host(link: str, proto: str) -> str:
    try:
        if proto == "vmess":
            cfg = json.loads(b64_decode(link[8:]))
            return cfg.get("add", "")
        if proto == "vless":
            m = re.search(r"vless://[^@]+@([^:/]+)", link)
            return m.group(1) if m else ""
        if proto == "shadowsocks":
            m = re.search(r"ss://(?:[^@]+@)?([^:/]+)", link)
            return m.group(1) if m else ""
        if proto == "trojan":
            m = re.search(r"trojan://[^@]+@([^:/?#]+)", link)
            return m.group(1) if m else ""
    except Exception as e:
        logging.debug(f"extract_host error for [{proto}] {link}: {e}")
    return ""

# ──────────────── Shadowsocks Rename Fix ────────────────
def rename_ss(link: str, ip: str, port: str, tag: str) -> str:
    try:
        raw = link.split("ss://", 1)[1]
        if "@" in raw:
            # فرمت غیر Base64: ss://method:password@host:port
            creds, _ = raw.split("@", 1)
            method, pwd = creds.split(":", 1)
        else:
            # فرمت Base64
            method, pwd = b64_decode(raw.split("#")[0]).split(":", 1)
        new_creds = b64_encode(f"{method}:{pwd}")
        return f"ss://{new_creds}@{ip}:{port}#{tag}"
    except Exception:
        return link

def rename_trojan_or_vless(link: str, ip: str, port: str, tag: str) -> str:
    out = re.sub(r"@[^:/#]+(:\d+)?", f"@{ip}:{port}", link)
    if "#" in out:
        out = re.sub(r"#.*$", f"#{tag}", out)
    else:
        out += f"#{tag}"
    return out

async def rename_line(client: httpx.AsyncClient, link: str) -> str:
    proto = detect_protocol(link)
    host = extract_host(link, proto)
    if not host:
        return link

    if ":" in host:
        host, port = host.split(":", 1)
    else:
        port = "443"

    ip = await resolve_dns(host)
    country = await get_country_by_ip(client, ip)
    flag = country_flag(country)
    tag = f"{flag}ShatakVPN-{random.randint(100000, 999999)}"

    if proto == "vmess":
        try:
            raw = link.split("://", 1)[1]
            cfg = json.loads(b64_decode(raw))
            cfg.update({"add": ip, "port": int(port), "ps": tag})
            return f"vmess://{b64_encode(json.dumps(cfg))}#{tag}"
        except Exception as e:
            logging.debug(f"vmess rename error: {e}")
            return link
    if proto == "ss":
        return rename_ss(link, ip, port, tag)
    if proto in ("vless", "trojan"):
        return rename_trojan_or_vless(link, ip, port, tag)
    return link

# ──────────────── Ping & Batching ────────────────
async def run_ping_once(client: httpx.AsyncClient, host: str) -> dict:
    base = "https://check-host.net"
    async with connection_limit:
        try:
            async with asyncio.timeout(30):  # Timeout کلی
                r1 = await client.get(f"{base}/check-ping", params={"host": host})
                if r1.status_code == 503:
                    await asyncio.sleep(random.uniform(2, 5))
                    return {}
                req_id = r1.json().get("request_id")
                if not req_id:
                    return {}
                for _ in range(10):
                    await asyncio.sleep(2)
                    r2 = await client.get(f"{base}/check-result/{req_id}")
                    if r2.status_code == 200 and r2.json():
                        return r2.json()
        except:
            return {}
    return {}

async def process_in_batches(tasks, batch_size=BATCH_SIZE):
    results = []
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        results.extend(await asyncio.gather(*batch))
        await asyncio.sleep(1)
    return results

async def save_to_file_async(path: str, lines: list[str]):
    if not lines:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write("\n".join(lines))

# ──────────────── Main ────────────────
async def main_async():
    async with httpx.AsyncClient(timeout=15) as client:
        logging.info(f"Starting process with MAX_CONCURRENCY={MAX_CONCURRENCY}, BATCH_SIZE={BATCH_SIZE}")
        all_pairs = []
        for url in URLS:
            blob = maybe_base64_decode(await fetch_data(client, url))
            configs = re.findall(r"(vless://[^\s]+|vmess://[^\s]+|trojan://[^\s]+|ss://[^\s]+)", blob)
            logging.info(f"Fetched {len(configs)} configs from {url}")
            for link in configs:
                proto = detect_protocol(link)
                host = strip_port(extract_host(link, proto))
                if host:
                    all_pairs.append((link, host))

        hosts = list({host for _, host in all_pairs})
        ping_results = await process_in_batches([run_ping_once(client, h) for h in hosts])
        results = dict(zip(hosts, ping_results))

        renamed_all = [await rename_line(client, l) for l, _ in all_pairs]
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        await save_to_file_async(os.path.join(OUTPUT_DIR, "all.txt"), renamed_all)
        await save_to_file_async(os.path.join(OUTPUT_DIR, "light.txt"), renamed_all[:30])
        logging.info("Processing complete.")

if __name__ == "__main__":
    asyncio.run(main_async())

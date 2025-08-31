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
import requests
import httpx
import urllib3
import zoneinfo

from datetime import datetime

# ──────────────── Configuration ────────────────
URLS = [
    "https://www.v2nodes.com/subscriptions/country/de/?key=769B61EA877690D",
    "https://raw.githubusercontent.com/Rayan-Config/C-Sub/refs/heads/main/configs/proxy.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
    "https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/main.txt",
    "https://raw.githubusercontent.com/MahsaNetConfigTopic/config/refs/heads/main/xray_final.txt",
]

OUTPUT_DIR = "configs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

# disable warnings for insecure HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

ZONE = zoneinfo.ZoneInfo("Asia/Tehran")


# ──────────────── Helpers: Base64, Port Strip & Geolocation Cache ────────────────
geo_cache: dict[str, str] = {}


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


# ──────────────── Fetch & Decode ────────────────
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
        if any(proto in decoded for proto in ("vless://", "vmess://", "trojan://", "ss://")):
            return decoded.strip()
    except Exception:
        pass
    return s


# ──────────────── Parser ────────────────
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


# ──────────────── Ping Tester with Retry ────────────────
async def run_ping_once(host: str, timeout: int = 10, retries: int = 3) -> dict:
    if not host:
        return {}

    base = "https://check-host.net"
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, retries + 1):
            try:
                r1 = await client.get(
                    f"{base}/check-ping",
                    params={"host": host},
                    headers={"Accept": "application/json"},
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
                    )
                    if r2.status_code == 200 and r2.json():
                        return r2.json()
                break

            except Exception as e:
                logging.error(f"Ping error for {host} (attempt {attempt}): {e}")
                await asyncio.sleep(2)

    return {}


def extract_latency_by_country(
    results: dict, country_nodes: dict[str, list[str]]
) -> dict[str, float]:
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


async def get_nodes_by_country() -> dict[str, list[str]]:
    url = "https://check-host.net/nodes/hosts"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(url)
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


# ──────────────── Async File Writer ────────────────
async def save_to_file_async(path: str, lines: list[str]):
    if not lines:
        logging.warning(f"No lines to save: {path}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write("\n".join(lines))
    logging.info(f"Saved: {path} ({len(lines)} lines)")


# ──────────────── Renaming Helpers ────────────────
def rename_ss(link: str, ip: str, port: str, tag: str) -> str:
    try:
        raw = link.split("ss://", 1)[1]
        creds, _ = raw.split("@", 1)
        method, pwd = b64_decode(creds).split(":", 1)
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


def rename_line(link: str) -> str:
    proto = detect_protocol(link)
    host = extract_host(link, proto)
    if not host:
        return link

    if ":" in host:
        host, port = host.split(":", 1)
    else:
        port = "443"

    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror as e:
        logging.warning(f"DNS lookup failed for {host}: {e}")
        ip = host

    country = get_country_by_ip(ip)
    flag = country_flag(country)
    tag = f"[{flag}{country}]::ShatalVPN-{random.randint(100000, 999999)}"

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


# ──────────────── Main Flow ────────────────
async def main_async():
    now = datetime.now(ZONE).strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"[{now}] Starting download and processing…")

    country_nodes = await get_nodes_by_country()
    categorized: dict[str, dict[str, list[tuple[str, str]]]] = {}
    all_pairs: list[tuple[str, str]] = []

    # Fetch & categorize
    for url in URLS:
        blob = maybe_base64_decode(fetch_data(url))
        configs = re.findall(
            r"(vless://[^\s]+|vmess://[^\s]+|trojan://[^\s]+|ss://[^\s]+)",
            blob,
        )
        logging.info(f"Fetched {url} → {len(configs)} configs")

        for link in configs:
            proto = detect_protocol(link)
            host = strip_port(extract_host(link, proto))
            if not host:
                continue
            all_pairs.append((link, host))
            for country in country_nodes:
                categorized.setdefault(country, {
                    "vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []
                })[proto].append((link, host))

    # Prepare and run ping tasks concurrently
    hosts = list({host for _, host in all_pairs})
    tasks = [run_ping_once(h) for h in hosts]
    ping_results = await asyncio.gather(*tasks)
    results = dict(zip(hosts, ping_results))

    # Process per country
    for country, groups in categorized.items():
        logging.info(f"Processing country: {country}")
        nodes = country_nodes.get(country, [])
        latencies: dict[str, float] = {}

        for host, res in results.items():
            lat = extract_latency_by_country(res, {country: nodes}).get(country, float("inf"))
            for link, h in all_pairs:
                if h == host:
                    latencies[link] = lat

        sorted_links = [l for l, _ in sorted(latencies.items(), key=lambda x: x[1])]
        renamed_all = [rename_line(l) for l in sorted_links]

        dest_dir = os.path.join(OUTPUT_DIR, country)
        os.makedirs(dest_dir, exist_ok=True)

        # gather all save tasks
        save_tasks = []
        for proto, items in groups.items():
            lst = [l for l in sorted_links if detect_protocol(l) == proto]
            save_tasks.append(
                save_to_file_async(
                    os.path.join(dest_dir, f"{proto}.txt"),
                    [rename_line(l) for l in lst]
                )
            )

        save_tasks.append(
            save_to_file_async(os.path.join(dest_dir, "all.txt"), renamed_all)
        )
        save_tasks.append(
            save_to_file_async(os.path.join(dest_dir, "light.txt"), renamed_all[:30])
        )

        # write files in parallel
        await asyncio.gather(*save_tasks)


if __name__ == "__main__":
    asyncio.run(main_async())

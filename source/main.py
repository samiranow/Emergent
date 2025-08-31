#!/usr/bin/env python3
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

from datetime import datetime

# ──────────────── Configuration ────────────────
URLS = [
    "https://www.v2nodes.com/subscriptions/country/de/?key=769B61EA877690D",
]

OUTPUT_DIR = "configs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

ZONE = zoneinfo.ZoneInfo("Asia/Tehran")
TIMESTAMP = datetime.now(ZONE).strftime("%Y-%m-%d %H:%M:%S")

# disable warnings for insecure HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")


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
        padded = s + "=" * ((4 - len(s) % 4) % 4)
        decoded = base64.b64decode(padded, validate=True).decode(errors="ignore").strip()
        if any(proto in decoded for proto in ("vless://", "vmess://", "trojan://", "ss://")):
            return decoded
    except Exception:
        pass
    return s


# ──────────────── Parser ────────────────
def detect_protocol(link: str) -> str:
    link = link.strip().lower()
    if link.startswith("vless://"):
        return "vless"
    if link.startswith("vmess://"):
        return "vmess"
    if link.startswith("ss://"):
        return "shadowsocks"
    if link.startswith("trojan://"):
        return "trojan"
    return "unknown"


def extract_host(link: str, proto: str) -> str:
    try:
        if proto == "vmess":
            b64 = link[8:]
            padded = b64 + "=" * ((4 - len(b64) % 4) % 4)
            cfg = json.loads(base64.b64decode(padded).decode(errors="ignore"))
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
    except Exception:
        pass
    return ""


# ──────────────── Ping Tester ────────────────
async def run_ping_once(host: str, timeout: int = 10) -> dict:
    if not host:
        return {}

    base = "https://check-host.net"
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r1 = await client.get(f"{base}/check-ping", params={"host": host}, headers={"Accept": "application/json"})
            r1.raise_for_status()
            req_id = r1.json().get("request_id")
            if not req_id:
                return {}
            for _ in range(10):
                await asyncio.sleep(2)
                r2 = await client.get(f"{base}/check-result/{req_id}", headers={"Accept": "application/json"})
                if r2.status_code == 200 and r2.json():
                    return r2.json()
        except Exception as e:
            logging.error(f"Ping error for {host}: {e}")
    return {}


def extract_latency_by_country(results: dict, country_nodes: dict[str, list[str]]) -> dict[str, float]:
    latencies = {}
    for country, nodes in country_nodes.items():
        vals = []
        for node in nodes:
            entries = results.get(node, [])
            try:
                for status, ping in entries[0]:
                    if status == "OK":
                        vals.append(ping)
            except Exception:
                continue
        latencies[country] = sum(vals) / len(vals) if vals else float("inf")
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

    mapping = {}
    for node, info in data.get("nodes", {}).items():
        loc = info.get("location", [])
        if isinstance(loc, list) and loc:
            mapping.setdefault(str(loc[0]).lower(), []).append(node)
    return mapping


# ──────────────── Output ────────────────
def save_to_file(path: str, lines: list[str]):
    if not lines:
        logging.warning(f"No lines to save: {path}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logging.info(f"Saved: {path} ({len(lines)} lines)")


# ──────────────── Helpers & Renaming ────────────────
def extract_configs(blob: str) -> list[str]:
    return re.findall(r"(vless://[^\s]+|vmess://[^\s]+|trojan://[^\s]+|ss://[^\s]+)", blob)


def base64_decode(s: str) -> str:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(s + pad).decode(errors="ignore")


def base64_encode(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def strip_port(host: str) -> str:
    return host.split(":", 1)[0]


def get_country_by_ip(ip: str) -> str:
    try:
        r = requests.get(f"https://ipwhois.app/json/{ip}", timeout=5)
        if r.status_code == 200:
            return r.json().get("country_code", "unknown").lower()
    except Exception:
        pass
    return "unknown"


def rename_ss(link: str, ip: str, port: str, tag: str) -> str:
    try:
        raw = link.split("ss://", 1)[1]
        creds, _ = raw.split("@", 1)
        decoded = base64.b64decode(creds + "=" * (-len(creds) % 4)).decode()
        method, pwd = decoded.split(":", 1)
        new_creds = base64.b64encode(f"{method}:{pwd}".encode()).decode()
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

    # split port if present
    if ":" in host:
        host, port = host.split(":", 1)
    else:
        port = "443"

    try:
        ip = socket.gethostbyname(host)
    except Exception:
        ip = host

    country = get_country_by_ip(ip)
    flag = {
        "us": "🇺🇸", "de": "🇩🇪", "fr": "🇫🇷", "ir": "🇮🇷",
        "nl": "🇳🇱", "gb": "🇬🇧", "ca": "🇨🇦", "ru": "🇷🇺",
        "cn": "🇨🇳", "jp": "🇯🇵", "in": "🇮🇳", "sg": "🇸🇬",
        "ae": "🇦🇪", "tr": "🇹🇷", "unknown": "🏳️"
    }.get(country, "🏳️")
    tag = f"[{flag}{country}]::ShatalVPN-{random.randint(100000,999999)}"

    if proto == "vmess":
        try:
            raw = link.split("://", 1)[1]
            cfg = json.loads(base64_decode(raw))
            cfg["add"] = ip
            cfg["port"] = int(port)
            cfg["ps"] = tag
            return f"vmess://{base64_encode(json.dumps(cfg))}#{tag}"
        except Exception:
            return link

    if proto == "ss":
        return rename_ss(link, ip, port, tag)

    if proto in ("vless", "trojan"):
        return rename_trojan_or_vless(link, ip, port, tag)

    return link


# ──────────────── Main Flow ────────────────
async def main_async():
    logging.info(f"[{TIMESTAMP}] Starting download and processing…")

    country_nodes = await get_nodes_by_country()
    categorized: dict[str, dict[str, list[tuple[str,str]]]] = {}
    all_pairs: list[tuple[str,str]] = []

    # Fetch & categorize
    for url in URLS:
        blob = maybe_base64_decode(fetch_data(url))
        cfgs = extract_configs(blob)
        logging.info(f"Fetched {url} → {len(cfgs)} configs")

        for link in cfgs:
            proto = detect_protocol(link)
            host = strip_port(extract_host(link, proto))
            if not host:
                continue
            all_pairs.append((link, host))
            for country in country_nodes:
                categorized.setdefault(country, {
                    "vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []
                })[proto].append((link, host))

    # Ping each host once
    host_map: dict[str, list[str]] = {}
    for link, host in all_pairs:
        host_map.setdefault(host, []).append(link)

    results: dict[str, dict] = {}
    for host in host_map:
        results[host] = await run_ping_once(host)

    # Process per country
    for country, groups in categorized.items():
        logging.info(f"Processing country: {country}")
        nodes = country_nodes.get(country, [])
        latencies = {}

        for host, res in results.items():
            lat = extract_latency_by_country(res, {country: nodes}).get(country, float("inf"))
            for link in host_map[host]:
                latencies[link] = lat

        sorted_links = [l for l, _ in sorted(latencies.items(), key=lambda x: x[1])]
        renamed_all = [rename_line(l) for l in sorted_links]

        dest_dir = os.path.join(OUTPUT_DIR, country)
        os.makedirs(dest_dir, exist_ok=True)

        # write per-protocol
        for proto, items in groups.items():
            lst = [l for l in sorted_links if detect_protocol(l) == proto]
            save_to_file(os.path.join(dest_dir, f"{proto}.txt"), [rename_line(l) for l in lst])

        save_to_file(os.path.join(dest_dir, "all.txt"), renamed_all)
        save_to_file(os.path.join(dest_dir, "light.txt"), renamed_all[:30])


if __name__ == "__main__":
    asyncio.run(main_async())
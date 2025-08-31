import os
import asyncio
import logging
import random
import socket
import re
import json
import base64
import requests
from config import URLS, TIMESTAMP, OUTPUT_DIR
from fetcher import fetch_data, maybe_base64_decode
from parser import detect_protocol, extract_host
from tester import run_ping_once, extract_latency_by_country, get_nodes_by_country
from output import save_to_file

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

def extract_configs(data: str) -> list[str]:
    pattern = r"(vless://[^\s]+|vmess://[^\s]+|trojan://[^\s]+|ss://[^\s]+)"
    return re.findall(pattern, data)

def base64_decode(s: str) -> str:
    padded = s + "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(padded).decode(errors="ignore")

def base64_encode(s: str) -> str:
    return base64.b64encode(s.encode()).decode()

def strip_port(host: str) -> str:
    return host.split(':')[0] if ':' in host else host

def get_country_by_ip(ip: str) -> str:
    try:
        r = requests.get(f"https://ipwhois.app/json/{ip}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get("country_code", "unknown").lower()
    except Exception:
        pass
    return "unknown"


def rename_ss(line: str, ip: str, port: str, display: str) -> str:
    """
    Rebuild a shadowsocks link replacing host with IP and preserving the port.
    """
    try:
        raw = line.split("ss://", 1)[1]
        base, rest = raw.split("@", 1)
        # decode method:password
        decoded = base64.b64decode(base + '=' * (-len(base) % 4)).decode()
        method, password = decoded.split(":", 1)
        # re-encode credentials
        new_base = base64.b64encode(f"{method}:{password}".encode()).decode()
        return f"ss://{new_base}@{ip}:{port}#{display}"
    except Exception:
        return line


def rename_trojan_or_vless(line: str, ip: str, port: str, display: str) -> str:
    """
    Replace host (and optional port) in vless/trojan URIs with IP:port and append display tag.
    """
    # replace @host[:port] with @ip:port
    line = re.sub(r'@[^:/#]+(:\d+)?', f'@{ip}:{port}', line)
    # replace or append fragment
    if '#' in line:
        line = re.sub(r'#.*$', f'#{display}', line)
    else:
        line += f'#{display}'
    return line


def rename_line(line: str) -> str:
    proto = detect_protocol(line)
    host = extract_host(line, proto)
    if not host:
        return line

    # 1) extract original port (if any)
    if ':' in host:
        host, port = host.split(':', 1)
    else:
        port = None

    # 2) resolve to IP
    try:
        ip = socket.gethostbyname(host)
    except Exception:
        ip = host

    # 3) lookup country for emoji
    country = get_country_by_ip(ip)
    emoji = {
        "us": "🇺🇸", "de": "🇩🇪", "fr": "🇫🇷", "ir": "🇮🇷",
        "nl": "🇳🇱", "gb": "🇬🇧", "ca": "🇨🇦", "ru": "🇷🇺",
        "cn": "🇨🇳", "jp": "🇯🇵", "in": "🇮🇳", "sg": "🇸🇬",
        "ae": "🇦🇪", "tr": "🇹🇷", "unknown": "🏳️"
    }.get(country, "🏳️")

    display = f"[{emoji}{country}]::ShatalVPN-{random.randint(100000, 999999)}"

    if proto == "vmess":
        try:
            raw = line.split("://", 1)[1]
            cfg = json.loads(base64_decode(raw))
            cfg["add"] = ip
            # if original port exists, preserve it; else leave default
            if port:
                cfg["port"] = int(port)
            cfg["ps"] = display
            new_raw = base64_encode(json.dumps(cfg))
            return f"vmess://{new_raw}#{display}"
        except Exception:
            return line

    elif proto == "ss":
        # default to 443 if no port in original
        return rename_ss(line, ip, port or "443", display)

    elif proto in ["vless", "trojan"]:
        return rename_trojan_or_vless(line, ip, port or "443", display)

    else:
        return line


async def main_async():
    logging.info(f"[{TIMESTAMP}] Starting download and processing with optimized ping strategy...")

    country_nodes_dict = await get_nodes_by_country()
    categorized_per_country = {}
    all_lines_hosts = []

    # fetch & categorize by host
    for url in URLS:
        raw_data = fetch_data(url)
        decoded_text = maybe_base64_decode(raw_data)
        configs = extract_configs(decoded_text)
        logging.info(f"Downloaded: {url} | Configs found: {len(configs)}")

        for line in configs:
            proto = detect_protocol(line)
            host = extract_host(line, proto)
            if not host:
                continue
            host = strip_port(host)
            all_lines_hosts.append((line, host))
            for country_code in country_nodes_dict:
                categorized_per_country\
                    .setdefault(country_code,
                                {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []})\
                    [proto].append((line, host))

    # ping each host once
    host_to_lines = {}
    for line, host in all_lines_hosts:
        host_to_lines.setdefault(host, []).append(line)

    host_to_results = {}
    for host in host_to_lines:
        host_to_results[host] = await run_ping_once(host)

    # per-country sorting, renaming, saving
    for country_code, categorized in categorized_per_country.items():
        logging.info(f"Processing country: {country_code}")
        country_nodes = country_nodes_dict.get(country_code, [])
        host_latencies = {}

        for host, results in host_to_results.items():
            country_latency = extract_latency_by_country(results, {country_code: country_nodes})
            latency = country_latency.get(country_code, float('inf'))
            for line in host_to_lines[host]:
                host_latencies[line] = latency

        sorted_lines = sorted(host_latencies.items(), key=lambda x: x[1])
        renamed_lines = [rename_line(line) for line, _ in sorted_lines]

        country_dir = os.path.join(OUTPUT_DIR, country_code)
        os.makedirs(country_dir, exist_ok=True)

        # split by protocol and write out
        for proto in categorized:
            lines = [line for line, _ in sorted_lines if detect_protocol(line) == proto]
            renamed = [rename_line(line) for line in lines]
            save_to_file(os.path.join(country_dir, f"{proto}.txt"), renamed)

        save_to_file(os.path.join(country_dir, "all.txt"), renamed_lines)
        save_to_file(os.path.join(country_dir, "light.txt"), renamed_lines[:30])


if __name__ == "__main__":
    asyncio.run(main_async())

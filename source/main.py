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

def rename_ss(line: str, ip: str, display: str) -> str:
    try:
        raw = line.split("ss://", 1)[1]
        base, rest = raw.split("@", 1)
        host_port = rest.split("#")[0]
        decoded = base64.b64decode(base + '=' * (-len(base) % 4)).decode()
        method, password = decoded.split(":", 1)
        new_base = base64.b64encode(f"{method}:{password}".encode()).decode()
        port = host_port.split(":")[1] if ":" in host_port else "443"
        return f"ss://{new_base}@{ip}:{port}#{display}"
    except Exception:
        return line

def rename_trojan_or_vless(line: str, ip: str, display: str) -> str:
    line = re.sub(r'@[^:/#]+(:\d+)?', f'@{ip}', line)
    line = re.sub(r'#.*$', f'#{display}', line) if '#' in line else line + f'#{display}'
    return line

def rename_line(line: str) -> str:
    proto = detect_protocol(line)
    host = extract_host(line, proto)
    if not host:
        return line

    host = strip_port(host)

    try:
        ip = socket.gethostbyname(host)
    except Exception:
        ip = host

    country = get_country_by_ip(ip)
    emoji = {
        "us": "🇺🇸", "de": "🇩🇪", "fr": "🇫🇷", "ir": "🇮🇷", "nl": "🇳🇱",
        "gb": "🇬🇧", "ca": "🇨🇦", "ru": "🇷🇺", "cn": "🇨🇳", "jp": "🇯🇵",
        "in": "🇮🇳", "sg": "🇸🇬", "ae": "🇦🇪", "tr": "🇹🇷", "unknown": "🏳️"
    }.get(country.lower(), "🏳️")

    display = f"[{emoji}{country.lower()}]::ShatalVPN-{random.randint(100000, 999999)}"

    if proto == "vmess":
        try:
            raw = line.split("://", 1)[1]
            decoded = json.loads(base64_decode(raw))
            decoded["add"] = ip
            decoded["ps"] = display
            new_raw = base64_encode(json.dumps(decoded))
            return f"vmess://{new_raw}#{display}"
        except Exception:
            return line
    elif proto == "ss":
        return rename_ss(line, ip, display)
    elif proto in ["vless", "trojan"]:
        return rename_trojan_or_vless(line, ip, display)
    else:
        return line

async def main_async():
    logging.info(f"[{TIMESTAMP}] Starting download and processing with optimized ping strategy...")

    country_nodes_dict = await get_nodes_by_country()
    categorized_per_country = {}
    all_lines_hosts = []

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
            for country_code in country_nodes_dict.keys():
                categorized_per_country.setdefault(
                    country_code,
                    {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
                )
                categorized_per_country[country_code][proto].append((line, host))

    host_to_lines = {}
    for line, host in all_lines_hosts:
        host_to_lines.setdefault(host, []).append(line)

    host_to_results = {}
    for host in host_to_lines:
        host_to_results[host] = await run_ping_once(host)

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

        for proto in categorized.keys():
            lines = [line for line, _ in sorted_lines if detect_protocol(line) == proto]
            save_to_file(os.path.join(country_dir, f"{proto}.txt"), [rename_line(line) for line in lines])

        save_to_file(os.path.join(country_dir, "all.txt"), renamed_lines)
        save_to_file(os.path.join(country_dir, "light.txt"), renamed_lines[:30])

if __name__ == "__main__":
    asyncio.run(main_async())

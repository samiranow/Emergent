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

def get_country_by_ip(ip: str) -> str:
    try:
        r = requests.get(f"https://ipapi.co/{ip}/country/", timeout=5)
        if r.status_code == 200:
            return r.text.strip().lower()
    except Exception:
        pass
    return "unknown"

def rename_line(line: str) -> str:
    proto = detect_protocol(line)
    host = extract_host(line, proto)
    if not host:
        return line

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
            new_raw = base64_encode(json.dumps(decoded))
            return f"{display} vmess://{new_raw}"
        except Exception:
            return f"{display} {line}"
    elif proto in ["vless", "trojan", "ss"]:
        return re.sub(r"@[^:]+", f"@{ip}", f"{display} {line}")
    else:
        return f"{display} {line}"

async def main_async():
    logging.info(f"[{TIMESTAMP}] Starting download and processing with country-based speed test...")

    country_nodes_dict = await get_nodes_by_country()
    categorized_per_country = {}

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
            for country_code in country_nodes_dict.keys():
                categorized_per_country.setdefault(
                    country_code,
                    {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
                )
                categorized_per_country[country_code][proto].append((line, host))

    for country_code, categorized in categorized_per_country.items():
        logging.info(f"Processing country: {country_code}")
        all_lines_hosts = []

        for proto, lines_hosts in categorized.items():
            if not lines_hosts:
                continue
            unique_lines_hosts = list(set(lines_hosts))
            all_lines_hosts.extend(unique_lines_hosts)

        host_to_lines = {}
        for line, host in all_lines_hosts:
            host_to_lines.setdefault(host, []).append(line)

        host_results = {}
        for host in host_to_lines.keys():
            results = await run_ping_once(host)
            country_latencies = extract_latency_by_country(results, {country_code: country_nodes_dict.get(country_code, [])})
            latency = country_latencies.get(country_code, float('inf'))
            for line in host_to_lines[host]:
                host_results[line] = latency

        sorted_lines = sorted(host_results.items(), key=lambda x: x[1])
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

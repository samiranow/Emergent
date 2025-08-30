# main.py
import asyncio
import re
import os
import random
import socket
import requests
import base64
import json
import logging
import flag

from config import URLS, TIMESTAMP, OUTPUT_DIR
from fetcher import fetch_data, maybe_base64_decode
from parser import detect_protocol, extract_host
from tester import test_speed, get_nodes_by_country
from output import save_to_file

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

def rename_line(line: str) -> str:
    """
    Rename a VPN config line for display.
    Replace hostname with resolved IP in the config itself.
    Format: [Flag/IP]::ShatalVPN-XXXXXX
    """
    proto = detect_protocol(line)
    host = extract_host(line, proto)

    # Resolve host if it's a domain
    try:
        ip_addr = socket.gethostbyname(host)
    except Exception:
        ip_addr = host  # fallback if DNS fails

    # Get country code via free API
    try:
        resp = requests.get(f"https://ipapi.co/{ip_addr}/country/", timeout=5)
        country_code = resp.text.strip().lower() if resp.status_code == 200 else "unknown"
    except Exception:
        country_code = "unknown"

    # Emoji flag
    flag_emoji = flag.flag(country_code.upper()) if country_code != "unknown" else "🌍"

    rand_num = random.randint(100000, 999999)
    display_name = f"[{flag_emoji}{country_code}]::ShatalVPN-{rand_num}"

    # Replace host/domain in the config line with IP
    try:
        if proto == "vmess":
            b64_part = line[8:]
            padded = b64_part + "=" * ((4 - len(b64_part) % 4) % 4)
            data = json.loads(base64.b64decode(padded).decode(errors="ignore"))
            data["add"] = ip_addr
            new_b64 = base64.b64encode(json.dumps(data).encode()).decode()
            line = "vmess://" + new_b64
        elif proto == "vless":
            line = re.sub(r"(vless://[^@]+@)([^:/]+)", lambda m: f"{m.group(1)}{ip_addr}", line)
        elif proto == "trojan":
            line = re.sub(r"(trojan://[^@]+@)([^:/?#]+)", lambda m: f"{m.group(1)}{ip_addr}", line)
        elif proto == "shadowsocks":
            line = re.sub(r"(ss://(?:[^@]+@)?)([^:/]+)", lambda m: f"{m.group(1)}{ip_addr}", line)
    except Exception as e:
        logging.error(f"Error renaming {proto} config: {e}")

    # Prepend display name
    return f"{display_name} {line}"

def extract_configs(data: str) -> list[str]:
    """
    Extract all VPN configurations from raw text.
    Supports vless, vmess, trojan, shadowsocks.
    """
    pattern = r"(vless://[^\s]+|vmess://[^\s]+|trojan://[^\s]+|ss://[^\s]+)"
    return re.findall(pattern, data)

async def main_async():
    logging.info(f"[{TIMESTAMP}] Starting download and processing with country-based speed test...")

    # Get nodes grouped by country
    country_nodes_dict = await get_nodes_by_country()

    categorized_per_country = {}  # {"us": {"vless": [], ...}, ...}

    # Fetch and process configs from URLs
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

            # Add config to all countries with nodes
            for country_code in country_nodes_dict.keys():
                categorized_per_country.setdefault(
                    country_code,
                    {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
                )
                categorized_per_country[country_code][proto].append((line, host))

    sem = asyncio.Semaphore(100)  # Increased for speed

    async def test_line_country(line_host, country_code):
        """
        Test latency for a single config line using nodes of the specific country.
        """
        line, host = line_host
        nodes = country_nodes_dict.get(country_code, [])
        if not nodes:
            return float('inf'), line, country_code
        async with sem:
            latency = await test_speed(host, country_nodes=nodes)
            return latency, line, country_code

    # Test speed and sort configs
    for country_code, categorized in categorized_per_country.items():
        logging.info(f"Processing country: {country_code}")
        all_results = []

        for proto, lines_hosts in categorized.items():
            if not lines_hosts:
                continue
            # Filter unique hosts to optimize
            unique_lines_hosts = list(set(lines_hosts))  # Remove duplicates
            results = await asyncio.gather(*[
                test_line_country(lh, country_code) for lh in unique_lines_hosts
            ])
            results.sort(key=lambda x: x[0])
            categorized[proto] = [line for _, line, _ in results]
            all_results.extend(results)

        all_results.sort(key=lambda x: x[0])
        sorted_lines = [line for _, line, _ in all_results]

        # Rename lines with display names and replace host with IP
        sorted_lines = [rename_line(line) for line in sorted_lines]
        for proto, lines in categorized.items():
            categorized[proto] = [rename_line(line) for line in lines]

        # Create country folder
        country_dir = os.path.join(OUTPUT_DIR, country_code)
        os.makedirs(country_dir, exist_ok=True)

        # Save files
        for proto, lines in categorized.items():
            save_to_file(os.path.join(country_dir, f"{proto}.txt"), lines)
        save_to_file(os.path.join(country_dir, "all.txt"), sorted_lines)
        save_to_file(os.path.join(country_dir, "light.txt"), sorted_lines[:30])

if __name__ == "__main__":
    asyncio.run(main_async())

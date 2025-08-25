import os
import requests
import urllib3
import re
import json
import asyncio
import httpx
from datetime import datetime
import zoneinfo
import base64

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URLS = [
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/refs/heads/main/source/local-config.txt",
    "https://www.v2nodes.com/subscriptions/country/all/?key=92E2CCF69B51739",
    "https://raw.githubusercontent.com/HosseinKoofi/GO_V2rayCollector/main/mixed_iran.txt",
    # ... Add more URLs here ...
]

OUTPUT_DIR = "configs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

zone = zoneinfo.ZoneInfo("Europe/Moscow")
timestamp = datetime.now(zone).strftime("%Y-%m-%d %H:%M:%S")

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

API_URL = "https://check-host.net/check-ping?host="  # API برای تست latency
SEM_LIMIT = 50  # تعداد همزمان درخواست‌ها

def fetch_data(url: str, timeout=10):
    headers = {"User-Agent": CHROME_UA}
    try:
        r = requests.get(url, timeout=timeout, headers=headers, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"⚠️ Error downloading {url}: {e}")
        return ""

def detect_protocol(line: str) -> str:
    line = line.strip()
    if line.startswith("vless://"):
        return "vless"
    elif line.startswith("vmess://"):
        return "vmess"
    elif line.startswith("ss://"):
        return "shadowsocks"
    elif line.startswith("trojan://"):
        return "trojan"
    else:
        return "unknown"

def extract_host(line: str, proto: str) -> str:
    try:
        if proto == "vmess":
            b64_part = line[8:]
            padded = b64_part + "=" * ((4 - len(b64_part) % 4) % 4)
            decoded = base64.b64decode(padded).decode(errors="ignore")
            data = json.loads(decoded)
            return data.get("add", "")
        elif proto == "vless":
            m = re.search(r"vless://[^@]+@([^:/]+)", line)
            if m:
                return m.group(1)
        elif proto == "shadowsocks":
            m = re.search(r"ss://(?:[^@]+@)?([^:/]+)", line)
            if m:
                return m.group(1)
        elif proto == "trojan":
            m = re.search(r"trojan://[^@]+@([^:/?#]+)", line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""

async def get_latency(client: httpx.AsyncClient, host: str):
    if not host:
        return float('inf')
    try:
        r = await client.get(f"{API_URL}{host}", timeout=10)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            return data.get("ping", float('inf'))
        return float('inf')
    except Exception:
        return float('inf')

async def process_line(sem, client, line, proto, output_json):
    async with sem:
        host = extract_host(line, proto)
        latency = await get_latency(client, host)
        output_json.append({
            "line": line,
            "protocol": proto,
            "host": host,
            "latency_ms": latency
        })
        return line, proto

async def main_async():
    print(f"[{timestamp}] Starting download and processing via API latency (async)...")

    all_lines = []
    categorized = {
        "vless": [],
        "vmess": [],
        "shadowsocks": [],
        "trojan": [],
        "unknown": []
    }

    output_json = []
    sem = asyncio.Semaphore(SEM_LIMIT)

    async with httpx.AsyncClient() as client:
        tasks = []
        for url in URLS:
            data = fetch_data(url)
            lines = [line for line in data.splitlines() if line.strip()]
            print(f"Downloaded: {url} | Lines: {len(lines)}")
            for line in lines:
                proto = detect_protocol(line)
                task = asyncio.create_task(process_line(sem, client, line, proto, output_json))
                tasks.append(task)

        results = await asyncio.gather(*tasks)
        for line, proto in results:
            categorized[proto].append(line)
            all_lines.append(line)

    # ذخیره فایل JSON
    json_path = os.path.join(OUTPUT_DIR, "ping_log.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)
    print(f"Saved: {json_path} | Lines: {len(output_json)}")

    # ذخیره فایل های متنی بر اساس پروتکل
    for proto, lines in categorized.items():
        path = os.path.join(OUTPUT_DIR, f"{proto}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Saved: {path} | Lines: {len(lines)}")

    # all.txt و light.txt
    all_path = os.path.join(OUTPUT_DIR, "all.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines))
    print(f"Saved: {all_path} | Lines: {len(all_lines)}")

    light_path = os.path.join(OUTPUT_DIR, "light.txt")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines[:30]))
    print(f"Saved Light version with {min(len(all_lines), 30)} configs")

if __name__ == "__main__":
    asyncio.run(main_async())

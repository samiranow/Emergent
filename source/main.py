import os
import requests
import urllib3
import re
import asyncio
import httpx
import base64
import json
from datetime import datetime
import zoneinfo

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
    elif line.startswith("trojan://"):  # اضافه شده
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
            m = re.search(r"vless://[^@]+@([^:\/]+)", line)
            if m:
                return m.group(1)
        elif proto == "shadowsocks":
            m = re.search(r"ss://(?:[^@]+@)?([^:/]+)", line)
            if m:
                return m.group(1)
        elif proto == "trojan":  # اضافه شده
            # معمولاً فرمت trojan: trojan://password@host:port?param=xxx#tag
            m = re.search(r"trojan://[^@]+@([^:/?#]+)", line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""

async def test_speed(host: str, timeout=5):
    if not host:
        return float('inf')
    url = f"http://{host}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            import time
            start = time.monotonic()
            r = await client.get(url)
            if r.status_code == 200:
                end = time.monotonic()
                return end - start
            else:
                return float('inf')
    except Exception:
        return float('inf')

async def main_async():
    print(f"[{timestamp}] Starting download and processing with speed test...")

    all_lines = []
    categorized = {
        "vless": [],
        "vmess": [],
        "shadowsocks": [],
        "trojan": [],   # اضافه شده
        "unknown": []
    }

    for url in URLS:
        data = fetch_data(url)
        lines = [line for line in data.splitlines() if line.strip()]
        print(f"Downloaded: {url} | Lines: {len(lines)}")
        for line in lines:
            proto = detect_protocol(line)
            categorized[proto].append(line)
            all_lines.append(line)

    sem = asyncio.Semaphore(100)

    async def test_line(line, proto):
        async with sem:
            host = extract_host(line, proto)
            latency = await test_speed(host)
            return (latency, line, proto)

    all_results = []
    for proto in categorized:
        lines = categorized[proto]
        if not lines:
            continue
        results = await asyncio.gather(*[test_line(line, proto) for line in lines])
        results.sort(key=lambda x: x[0])
        categorized[proto] = [line for _, line, _ in results]
        all_results.extend(results)

    all_results.sort(key=lambda x: x[0])
    all_sorted_lines = [line for _, line, _ in all_results]

    for proto, lines in categorized.items():
        path = os.path.join(OUTPUT_DIR, f"{proto}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Saved: {path} | Lines: {len(lines)}")

    all_path = os.path.join(OUTPUT_DIR, "all.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sorted_lines))
    print(f"Saved: {all_path} | Lines: {len(all_sorted_lines)}")

    light_path = os.path.join(OUTPUT_DIR, "light.txt")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sorted_lines[:30]))
    print(f"Saved Light version with {min(len(all_sorted_lines), 30)} configs")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_async())

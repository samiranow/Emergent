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
]

OUTPUT_DIR = "configs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

API_ENDPOINT = "https://your-api.example.com/ping"

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
            m = re.search(r"vless://[^@]+@([^:\/]+)", line)
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

async def test_speed(host: str, timeout=5):
    if not host:
        return 9999
    url = f"http://{host}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            import time
            start = time.monotonic()
            r = await client.get(url)
            if r.status_code == 200:
                end = time.monotonic()
                latency_ms = (end - start) * 1000
            else:
                latency_ms = 9999
    except Exception:
        latency_ms = 9999
    return latency_ms

async def main_async():
    print(f"[{timestamp}] Starting download and processing with speed test...")

    all_lines = []
    categorized = {
        "vless": [],
        "vmess": [],
        "shadowsocks": [],
        "trojan": [],
        "unknown": []
    }

    hosts_to_send = []

    for url in URLS:
        data = fetch_data(url)
        lines = [line for line in data.splitlines() if line.strip()]
        print(f"Downloaded: {url} | Lines: {len(lines)}")
        for line in lines:
            proto = detect_protocol(line)
            categorized[proto].append(line)
            all_lines.append((line, proto))
            host = extract_host(line, proto)
            hosts_to_send.append({"host": host})

    sem = asyncio.Semaphore(100)

    async def test_line(item):
        line, proto = item
        host = extract_host(line, proto)
        latency = await test_speed(host)
        return {"line": line, "protocol": proto, "host": host, "latency_ms": latency}

    results = await asyncio.gather(*[test_line(item) for item in all_lines])

    # ارسال همه هاست‌ها یکجا به API
    for r in results:
        if "latency_ms" in r and (r["latency_ms"] is None or r["latency_ms"] == float('inf')):
            r["latency_ms"] = 9999
    try:
        requests.post(API_ENDPOINT, json=results, timeout=10)
    except Exception as e:
        print(f"⚠️ Error sending batch to API: {e}")

    # مرتب‌سازی نتایج برای فایل‌ها
    results.sort(key=lambda x: x["latency_ms"])
    categorized_lines = {k: [] for k in categorized}
    for r in results:
        categorized_lines[r["protocol"]].append(r["line"])

    for proto, lines in categorized_lines.items():
        path = os.path.join(OUTPUT_DIR, f"{proto}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Saved: {path} | Lines: {len(lines)}")

    all_path = os.path.join(OUTPUT_DIR, "all.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join([r["line"] for r in results]))
    print(f"Saved: {all_path} | Lines: {len(results)}")

    light_path = os.path.join(OUTPUT_DIR, "light.txt")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write("\n".join([r["line"] for r in results[:30]]))
    print(f"Saved Light version with {min(len(results), 30)} configs")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_async())

import os
import requests
import urllib3
import re
import asyncio
import base64
import json
from datetime import datetime
import zoneinfo
import httpx
import time

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

API_HEADERS = {"Accept": "application/json", "User-Agent": CHROME_UA}

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

async def check_host_ping_request(host: str, max_nodes=10):
    url = f"https://check-host.net/check-ping?host={host}&max_nodes={max_nodes}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=API_HEADERS)
            if r.status_code == 200:
                return r.json()
    except Exception:
        return None
    return None

async def check_host_ping_result(request_id: str, timeout=30):
    url = f"https://check-host.net/check-result/{request_id}"
    stime = time.time()
    while time.time() - stime < timeout:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, headers=API_HEADERS)
                if r.status_code == 200:
                    data = r.json()
                    if all(v is not None for v in data.values()):
                        return data
        except Exception:
            pass
        await asyncio.sleep(2)
    return None

async def get_iran_ping(host: str):
    req_data = await check_host_ping_request(host)
    if not req_data or "request_id" not in req_data:
        return float("inf")

    request_id = req_data["request_id"]
    nodes_info = req_data.get("nodes", {})

    res_data = await check_host_ping_result(request_id)
    if not res_data:
        return float("inf")

    # محاسبه میانگین پینگ برای نودهای ایران
    iran_latencies = []
    for node, results in res_data.items():
        if not results or not isinstance(results, list) or len(results) == 0:
            continue
        node_info = nodes_info.get(node, [])
        if len(node_info) >= 2 and node_info[1].lower() == "iran":
            values = [item[1] * 1000 for item in results[0] if item and item[0] == "OK"]
            iran_latencies.extend(values)

    if iran_latencies:
        return sum(iran_latencies) / len(iran_latencies)
    return float("inf")

async def main_async():
    print(f"[{timestamp}] Starting download and processing with Check-Host API...")

    all_lines = []
    categorized = {
        "vless": [],
        "vmess": [],
        "shadowsocks": [],
        "trojan": [],
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

    sem = asyncio.Semaphore(20)

    async def process_line(line, proto):
        async with sem:
            host = extract_host(line, proto)
            latency = await get_iran_ping(host)
            return (latency, line, proto)

    all_results = []
    for proto in categorized:
        lines = categorized[proto]
        if not lines:
            continue
        results = await asyncio.gather(*[process_line(line, proto) for line in lines])
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
    asyncio.run(main_async())

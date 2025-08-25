import os
import requests
import urllib3
import re
import asyncio
import base64
import json
from datetime import datetime
import zoneinfo
import logging
import random
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ======= تنظیم لاگ =========
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "main.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ======= تنظیمات =========
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

CHECK_HOST_API = "https://check-host.net/check-ping"

MAX_RETRIES = 3  # تعداد تلاش‌های مجدد
TIMEOUT = 10     # Timeout هر درخواست
MAX_LATENCY = 1000  # میلی‌ثانیه، لینک‌هایی بالاتر از این حذف یا پایین‌تر قرار می‌گیرن

# ======= دانلود داده =========
def fetch_data(url: str):
    headers = {"User-Agent": CHROME_UA}
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=headers, verify=False)
        r.raise_for_status()
        logging.info(f"Downloaded {url} | Lines: {len(r.text.splitlines())}")
        return r.text
    except Exception as e:
        logging.error(f"Error downloading {url}: {e}")
        return ""

# ======= شناسایی پروتکل =========
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

# ======= استخراج هاست =========
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

# ======= تست سرعت با Check-Host API با Retry =========
def test_speed(host: str):
    if not host:
        return float('inf')
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(f"{CHECK_HOST_API}?host={host}", timeout=TIMEOUT)
            data = response.json()
            if "pings" in data and data["pings"]:
                times = [v for v in data["pings"].values() if isinstance(v, (int, float))]
                if times:
                    avg = sum(times) / len(times)
                    return avg
        except Exception as e:
            logging.warning(f"Retry {attempt+1}/{MAX_RETRIES} failed for {host}: {e}")
            time.sleep(0.5 + random.random())  # فاصله کوتاه قبل retry
    return float('inf')

# ======= تابع اصلی =========
async def main_async():
    logging.info(f"[{timestamp}] Starting download and processing with advanced Check-Host API...")
    print(f"[{timestamp}] Starting download and processing...")

    all_lines = []
    categorized = {
        "vless": [],
        "vmess": [],
        "shadowsocks": [],
        "trojan": [],
        "unknown": []
    }

    # دانلود و دسته بندی
    for url in URLS:
        data = fetch_data(url)
        lines = [line for line in data.splitlines() if line.strip()]
        for line in lines:
            proto = detect_protocol(line)
            categorized[proto].append(line)
            all_lines.append(line)

    sem = asyncio.Semaphore(50)  # تعداد همزمان تست‌ها

    async def test_line(line, proto):
        async with sem:
            host = extract_host(line, proto)
            latency = await asyncio.to_thread(test_speed, host)
            return (latency, line, proto)

    all_results = []
    for proto in categorized:
        lines = categorized[proto]
        if not lines:
            continue
        results = await asyncio.gather(*[test_line(line, proto) for line in lines])
        # مرتب‌سازی: لینک‌هایی با پینگ بالا به انتها میرن
        results.sort(key=lambda x: x[0])
        categorized[proto] = [line for latency, line, _ in results if latency <= MAX_LATENCY]
        all_results.extend(results)

    # مرتب سازی کلی
    all_results.sort(key=lambda x: x[0])
    all_sorted_lines = [line for latency, line, _ in all_results if latency <= MAX_LATENCY]

    # ذخیره خروجی‌ها
    for proto, lines in categorized.items():
        path = os.path.join(OUTPUT_DIR, f"{proto}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logging.info(f"Saved: {path} | Lines: {len(lines)}")
        print(f"Saved: {path} | Lines: {len(lines)}")

    all_path = os.path.join(OUTPUT_DIR, "all.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sorted_lines))
    logging.info(f"Saved: {all_path} | Lines: {len(all_sorted_lines)}")
    print(f"Saved: {all_path} | Lines: {len(all_sorted_lines)}")

    # نسخه light با بهترین لینک‌ها
    light_path = os.path.join(OUTPUT_DIR, "light.txt")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sorted_lines[:30]))
    logging.info(f"Saved Light version with {min(len(all_sorted_lines), 30)} configs")
    print(f"Saved Light version with {min(len(all_sorted_lines), 30)} configs")

if __name__ == "__main__":
    asyncio.run(main_async())

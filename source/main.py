import os
import re
import json
import base64
import asyncio
import logging
import shutil
import subprocess
from datetime import datetime
import zoneinfo
import httpx
import tempfile
import zipfile

# ---------------------------
# Configurable Settings
# ---------------------------
CONFIG = {
    "urls": [
        "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/refs/heads/main/source/local-config.txt",
        "https://raw.githubusercontent.com/HosseinKoofi/GO_V2rayCollector/main/mixed_iran.txt",
        "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
    ],
    "output_dir": "configs",
    "light_limit": 30,
    "concurrent_requests": 20,
    "timeout": 5,
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
    "timezone": "Asia/Tehran",
    "default_port": {"vless": 443, "vmess": 443, "shadowsocks": 8388, "trojan": 443},
}

# ---------------------------
# Logging Setup
# ---------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
zone = zoneinfo.ZoneInfo(CONFIG["timezone"])

def timestamp():
    return datetime.now(zone).strftime("%Y-%m-%d %H:%M:%S")

# ---------------------------
# Utilities
# ---------------------------
def maybe_base64_decode(s: str) -> str:
    s = s.strip()
    try:
        padded = s + "=" * ((4 - len(s) % 4) % 4)
        decoded_bytes = base64.b64decode(padded, validate=True)
        decoded_str = decoded_bytes.decode(errors="ignore")
        if len(decoded_str) < 2 or re.search(r"[^\x00-\x7F]", decoded_str):
            return s
        return decoded_str
    except Exception:
        return s

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

def extract_host_port(line: str, proto: str) -> tuple[str,int]:
    try:
        if proto == "vmess":
            b64_part = line[8:]
            padded = b64_part + "=" * ((4 - len(b64_part) % 4) % 4)
            decoded = base64.b64decode(padded).decode(errors="ignore")
            data = json.loads(decoded)
            host = data.get("add", "")
            port = int(data.get("port", CONFIG["default_port"][proto]))
            return host, port
        elif proto == "vless":
            m = re.search(r"vless://[^@]+@([^:/]+)(?::(\d+))?", line)
            if m:
                host = m.group(1)
                port = int(m.group(2)) if m.group(2) else CONFIG["default_port"][proto]
                return host, port
        elif proto == "shadowsocks":
            m = re.search(r"ss://(?:[^@]+@)?([^:/]+)(?::(\d+))?", line)
            if m:
                host = m.group(1)
                port = int(m.group(2)) if m.group(2) else CONFIG["default_port"][proto]
                return host, port
        elif proto == "trojan":
            m = re.search(r"trojan://[^@]+@([^:/?#]+)(?::(\d+))?", line)
            if m:
                host = m.group(1)
                port = int(m.group(2)) if m.group(2) else CONFIG["default_port"][proto]
                return host, port
    except Exception:
        pass
    return "", CONFIG["default_port"].get(proto, 443)

# ---------------------------
# Xray Download & Run
# ---------------------------
XRAY_URL = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"

async def download_xray() -> str:
    xray_dir = "/tmp/xray"
    os.makedirs(xray_dir, exist_ok=True)
    zip_path = os.path.join(xray_dir, "xray.zip")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(XRAY_URL, follow_redirects=True)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            f.write(r.content)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(xray_dir)
    os.chmod(os.path.join(xray_dir, "xray"), 0o755)
    logging.info(f"Xray installed at {os.path.join(xray_dir, 'xray')}")
    return os.path.join(xray_dir, "xray")

async def test_with_xray(xray_path: str, line: str, proto: str) -> float:
    """Run Xray with temporary config to measure latency"""
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, "config.json")
    host, port = extract_host_port(line, proto)
    if not host:
        return float("inf")
    config = {
        "inbounds": [{"port": 1080, "listen": "127.0.0.1", "protocol": "socks"}],
        "outbounds": [{"protocol": proto, "settings": {"servers": [{"address": host, "port": port}]}}]
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f)
    try:
        start = asyncio.get_event_loop().time()
        proc = await asyncio.create_subprocess_exec(xray_path, "-c", config_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL)
        await asyncio.sleep(0.5)  # give it some time to try connect
        proc.terminate()
        await proc.wait()
        end = asyncio.get_event_loop().time()
        return end - start
    except Exception:
        return float("inf")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# ---------------------------
# Fetch & Process Configs
# ---------------------------
async def fetch_url(session: httpx.AsyncClient, url: str) -> list[str]:
    try:
        r = await session.get(url, timeout=30)
        r.raise_for_status()
        lines = [maybe_base64_decode(line) for line in r.text.splitlines() if line.strip()]
        logging.info(f"Downloaded {url} | Lines: {len(lines)}")
        return lines
    except Exception as e:
        logging.warning(f"⚠️ Error downloading {url}: {e}")
        return []

async def main():
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    async with httpx.AsyncClient(headers={"User-Agent": CONFIG["user_agent"]}) as client:
        all_lines_nested = await asyncio.gather(*[fetch_url(client, url) for url in CONFIG["urls"]])
    all_lines = [line for sublist in all_lines_nested for line in sublist]
    all_lines = list(dict.fromkeys(all_lines))  # remove exact duplicates
    logging.info(f"Total unique lines: {len(all_lines)}")

    # categorize
    categorized = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
    for line in all_lines:
        proto = detect_protocol(line)
        categorized[proto].append(line)

    xray_path = await download_xray()
    sem = asyncio.Semaphore(CONFIG["concurrent_requests"])

    async def test_line(line, proto):
        async with sem:
            latency = await test_with_xray(xray_path, line, proto)
            return latency, line, proto

    # Test latency for all except unknown
    tasks = []
    for proto in ["vless", "vmess", "shadowsocks", "trojan"]:
        for line in categorized[proto]:
            tasks.append(test_line(line, proto))

    results = await asyncio.gather(*tasks)
    results = [r for r in results if r[0] != float("inf")]
    results.sort(key=lambda x: x[0])
    all_sorted = [line for _, line, _ in results]

    # Save categorized
    new_categorized = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": categorized["unknown"]}
    for _, line, proto in results:
        new_categorized[proto].append(line)

    for proto, lines in new_categorized.items():
        path = os.path.join(CONFIG["output_dir"], f"{proto}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logging.info(f"Saved {path} | Lines: {len(lines)}")

    # all.txt
    all_path = os.path.join(CONFIG["output_dir"], "all.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sorted))
    logging.info(f"Saved {all_path} | Lines: {len(all_sorted)}")

    # light.txt - top 30 fastest, exclude unknown
    light_path = os.path.join(CONFIG["output_dir"], "light.txt")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sorted[:CONFIG["light_limit"]]))
    logging.info(f"Saved Light version with {min(len(all_sorted), CONFIG['light_limit'])} configs")

if __name__ == "__main__":
    asyncio.run(main())

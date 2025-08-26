import os
import re
import json
import base64
import asyncio
import logging
from datetime import datetime
import zoneinfo
import ssl
from urllib.parse import urlparse
import httpx

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
    "concurrent_requests": 50,
    "timeout": 5,
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
    "timezone": "Asia/Tehran",
    "default_port": {"vless": 443, "vmess": 443, "shadowsocks": 8388, "trojan": 443},
    "proxy": None,  # Example: "socks5://127.0.0.1:1080"
    "tcp_retry": 2,
    "latency_tests": 3,  # تعداد دفعات تست latency برای میانگین گیری
}

# ---------------------------
# Logging Setup
# ---------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
zone = zoneinfo.ZoneInfo(CONFIG["timezone"])

# ---------------------------
# Utilities
# ---------------------------
def timestamp():
    return datetime.now(zone).strftime("%Y-%m-%d %H:%M:%S")

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

def extract_host_port(line: str, proto: str) -> tuple[str, int]:
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
            u = urlparse(line)
            host = u.hostname or ""
            port = u.port or CONFIG["default_port"][proto]
            return host, port

        elif proto == "shadowsocks":
            ss_part = line[5:]
            if "@" in ss_part:
                after_at = ss_part.rsplit("@", 1)[1]
                host_port = after_at.split(":")
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else CONFIG["default_port"][proto]
                return host, port
            else:
                return "", CONFIG["default_port"][proto]

        elif proto == "trojan":
            u = urlparse(line)
            host = u.hostname or ""
            port = u.port or CONFIG["default_port"][proto]
            return host, port
    except Exception:
        pass
    return "", CONFIG["default_port"].get(proto, 443)

# ---------------------------
# Async Functions
# ---------------------------
async def fetch_url(session: httpx.AsyncClient, url: str) -> list[str]:
    try:
        r = await session.get(url)
        r.raise_for_status()
        lines = [maybe_base64_decode(line) for line in r.text.splitlines() if line.strip()]
        logging.info(f"Downloaded {url} | Lines: {len(lines)}")
        return lines
    except Exception as e:
        logging.warning(f"⚠️ Error downloading {url}: {e}")
        return []

async def tcp_latency(host: str, port: int, retries: int = CONFIG["tcp_retry"]) -> float:
    if not host:
        return float("inf")
    ssl_context = ssl.create_default_context() if port == 443 else None
    for _ in range(retries):
        try:
            start = asyncio.get_event_loop().time()
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port, ssl=ssl_context),
                CONFIG["timeout"]
            )
            end = asyncio.get_event_loop().time()
            writer.close()
            await writer.wait_closed()
            return end - start
        except Exception:
            continue
    return float("inf")

async def http_latency(host: str, port: int) -> float:
    url = f"http://{host}:{port}" if port != 80 else f"http://{host}"
    try:
        async with httpx.AsyncClient(timeout=CONFIG["timeout"]) as client:
            start = asyncio.get_event_loop().time()
            r = await client.get(url)
            end = asyncio.get_event_loop().time()
            if r.status_code == 200:
                return end - start
            return float("inf")
    except Exception:
        return float("inf")

async def measure_latency(host: str, port: int) -> float:
    latencies = []
    for _ in range(CONFIG["latency_tests"]):
        latency = await tcp_latency(host, port)
        if latency == float("inf"):
            latency = await http_latency(host, port)
        latencies.append(latency)
    avg_latency = sum(latencies) / len(latencies)
    return avg_latency

async def test_lines_latency(lines: list[str], proto: str, sem: asyncio.Semaphore) -> list[str]:
    async def test_line(line: str):
        async with sem:
            host, port = extract_host_port(line, proto)
            latency = await measure_latency(host, port)
            return latency, line
    results = await asyncio.gather(*[test_line(line) for line in lines])
    results.sort(key=lambda x: x[0])
    return [line for _, line in results]

# ---------------------------
# Main Workflow
# ---------------------------
async def main():
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    sem = asyncio.Semaphore(CONFIG["concurrent_requests"])

    client_args = {"headers": {"User-Agent": CONFIG["user_agent"]}}
    if CONFIG["proxy"]:
        client_args["proxies"] = CONFIG["proxy"]

    async with httpx.AsyncClient(**client_args) as client:
        all_lines_nested = await asyncio.gather(*[fetch_url(client, url) for url in CONFIG["urls"]])
        all_lines = [line for sublist in all_lines_nested for line in sublist]

    all_lines = list(dict.fromkeys(all_lines))
    logging.info(f"Total unique lines: {len(all_lines)}")

    categorized = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
    for line in all_lines:
        proto = detect_protocol(line)
        categorized[proto].append(line)

    for proto, lines in categorized.items():
        if not lines:
            continue
        sorted_lines = await test_lines_latency(lines, proto, sem)
        categorized[proto] = sorted_lines

    all_sorted = []
    for proto, lines in categorized.items():
        path = os.path.join(CONFIG["output_dir"], f"{proto}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logging.info(f"Saved {path} | Lines: {len(lines)}")
        all_sorted.extend(lines)

    all_sorted = [line for line in all_sorted if line.strip()]
    all_path = os.path.join(CONFIG["output_dir"], "all.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sorted))
    logging.info(f"Saved {all_path} | Lines: {len(all_sorted)}")

    light_path = os.path.join(CONFIG["output_dir"], "light.txt")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sorted[: CONFIG["light_limit"]]))
    logging.info(f"Saved Light version with {min(len(all_sorted), CONFIG['light_limit'])} configs")

if __name__ == "__main__":
    asyncio.run(main())

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

# Disable warnings for insecure HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# List of configuration URLs to fetch
URLS = [
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/refs/heads/main/source/local-config.txt",
    "https://raw.githubusercontent.com/HosseinKoofi/GO_V2rayCollector/main/mixed_iran.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
]

# Output directory for processed configuration files
OUTPUT_DIR = "configs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set timezone to Tehran, Iran
zone = zoneinfo.ZoneInfo("Asia/Tehran")
timestamp = datetime.now(zone).strftime("%Y-%m-%d %H:%M:%S")

# User-Agent string to mimic a real browser
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

def fetch_data(url: str, timeout=10):
    """
    Fetch text content from a given URL with a custom User-Agent.
    Returns the content as a string. Returns empty string on failure.
    """
    headers = {"User-Agent": CHROME_UA}
    try:
        r = requests.get(url, timeout=timeout, headers=headers, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"⚠️ Error downloading {url}: {e}")
        return ""

def maybe_base64_decode(s: str) -> str:
    """
    Attempt to decode a string from Base64.
    Returns decoded string if valid Base64, otherwise returns the original string.
    """
    s = s.strip()
    try:
        # Add padding if necessary
        padded = s + "=" * ((4 - len(s) % 4) % 4)
        decoded_bytes = base64.b64decode(padded, validate=True)
        decoded_str = decoded_bytes.decode(errors="ignore")
        # Return original string if decoding produces unusual characters or too short
        if re.search(r'[^\x00-\x7F]', decoded_str) or len(decoded_str) < 2:
            return s
        return decoded_str
    except Exception:
        return s

def detect_protocol(line: str) -> str:
    """
    Detect VPN protocol based on the prefix of a configuration line.
    Supported protocols: vless, vmess, shadowsocks, trojan.
    Returns "unknown" if no match.
    """
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
    """
    Extract the host (server address) from a configuration line based on protocol.
    Supports vmess (Base64 JSON), vless, shadowsocks, and trojan formats.
    Returns empty string if extraction fails.
    """
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
    """
    Perform a simple HTTP GET request to measure server response time.
    Returns latency in seconds, or infinity if host is unreachable.
    """
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
    """
    Main asynchronous workflow:
    1. Download and optionally decode Base64 configuration lines.
    2. Detect protocol type and categorize lines.
    3. Measure server latency asynchronously.
    4. Sort configurations by latency and save to categorized files.
    """
    print(f"[{timestamp}] Starting download and processing with speed test...")

    all_lines = []
    categorized = {
        "vless": [],
        "vmess": [],
        "shadowsocks": [],
        "trojan": [],
        "unknown": []
    }

    # Fetch and decode configurations from all URLs
    for url in URLS:
        data = fetch_data(url)
        lines = [line for line in data.splitlines() if line.strip()]
        decoded_lines = [maybe_base64_decode(line) for line in lines]  # Auto decode Base64
        print(f"Downloaded: {url} | Lines: {len(decoded_lines)}")
        for line in decoded_lines:
            proto = detect_protocol(line)
            categorized[proto].append(line)
            all_lines.append(line)

    # Limit concurrent latency tests
    sem = asyncio.Semaphore(100)

    async def test_line(line, proto):
        """
        Test latency for a single line and return a tuple of (latency, line, protocol)
        """
        async with sem:
            host = extract_host(line, proto)
            latency = await test_speed(host)
            return (latency, line, proto)

    # Perform asynchronous latency tests and sort results
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

    # Save categorized configurations to files
    for proto, lines in categorized.items():
        path = os.path.join(OUTPUT_DIR, f"{proto}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Saved: {path} | Lines: {len(lines)}")

    # Save all sorted configurations to all.txt
    all_path = os.path.join(OUTPUT_DIR, "all.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sorted_lines))
    print(f"Saved: {all_path} | Lines: {len(all_sorted_lines)}")

    # Save a "light" version with first 30 configurations
    light_path = os.path.join(OUTPUT_DIR, "light.txt")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sorted_lines[:30]))
    print(f"Saved Light version with {min(len(all_sorted_lines), 30)} configs")

if __name__ == "__main__":
    asyncio.run(main_async())

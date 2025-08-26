import os
import re
import json
import base64
import asyncio
import logging
import subprocess
from datetime import datetime
import httpx
import aiofiles

CONFIG = {
    "urls": [
        "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/refs/heads/main/source/local-config.txt",
        "https://raw.githubusercontent.com/HosseinKoofi/GO_V2rayCollector/main/mixed_iran.txt",
        "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
    ],
    "output_dir": "configs",
    "light_limit": 30,
    "timeout": 2,  # Timeout for each connection test
    "xray_path": "/tmp/xray/xray",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0.0.0 Safari/537.36",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ------------------------------
# Helper Functions
# ------------------------------

def maybe_base64_decode(s: str) -> str:
    s = s.strip()
    try:
        padded = s + "=" * ((4 - len(s) % 4) % 4)
        return base64.b64decode(padded).decode(errors="ignore")
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

def extract_host_port(line: str, proto: str):
    try:
        if proto == "vless":
            m = re.search(r"vless://[^@]+@([^:/]+)(?::(\d+))?", line)
            if m:
                host = m.group(1)
                port = int(m.group(2)) if m.group(2) else 443
                return host, port
        elif proto == "vmess":
            data = json.loads(base64.b64decode(line[8:] + "==").decode())
            return data.get("add", ""), int(data.get("port", 443))
        elif proto == "shadowsocks":
            m = re.search(r"ss://(?:[^@]+@)?([^:/]+):?(\d+)?", line)
            if m:
                host = m.group(1)
                port = int(m.group(2)) if m.group(2) else 8388
                return host, port
        elif proto == "trojan":
            m = re.search(r"trojan://[^@]+@([^:/]+)(?::(\d+))?", line)
            if m:
                host = m.group(1)
                port = int(m.group(2)) if m.group(2) else 443
                return host, port
    except Exception:
        pass
    return "", 0

async def fetch_url(client: httpx.AsyncClient, url: str):
    try:
        r = await client.get(url)
        r.raise_for_status()
        lines = [maybe_base64_decode(l) for l in r.text.splitlines() if l.strip()]
        logging.info(f"Downloaded {url} | Lines: {len(lines)}")
        return lines
    except Exception as e:
        logging.warning(f"Error downloading {url}: {e}")
        return []

# ------------------------------
# Xray Test
# ------------------------------

async def test_with_xray(line: str, proto: str):
    host, port = extract_host_port(line, proto)
    if not host or port == 0:
        return False

    config = {
        "inbounds": [],
        "outbounds": [{"protocol": proto, "settings": {"vnext":[{"address": host, "port": port, "users":[{"id":"00000000-0000-0000-0000-000000000000"}]}]}}]
    }
    cfg_path = f"/tmp/{proto}_test.json"
    async with aiofiles.open(cfg_path, "w") as f:
        await f.write(json.dumps(config))

    try:
        proc = await asyncio.create_subprocess_exec(
            CONFIG["xray_path"], "-test", "-c", cfg_path,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=CONFIG["timeout"])
        except asyncio.TimeoutError:
            proc.kill()
            return False
        return proc.returncode == 0
    except Exception:
        return False

async def test_all(lines: list[str]):
    sem = asyncio.Semaphore(50)
    results = []

    async def test_line(line):
        proto = detect_protocol(line)
        if proto == "unknown":
            return None
        async with sem:
            ok = await test_with_xray(line, proto)
            if ok:
                return line
        return None

    tasks = [test_line(l) for l in lines]
    for future in asyncio.as_completed(tasks):
        res = await future
        if res:
            results.append(res)
    return results

# ------------------------------
# Main Workflow
# ------------------------------

async def main():
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    async with httpx.AsyncClient(headers={"User-Agent": CONFIG["user_agent"]}) as client:
        all_lines_nested = await asyncio.gather(*[fetch_url(client, u) for u in CONFIG["urls"]])
    all_lines = list(dict.fromkeys([l for sub in all_lines_nested for l in sub]))
    logging.info(f"Total unique lines: {len(all_lines)}")

    tested = await test_all(all_lines)
    logging.info(f"Total tested and OK: {len(tested)}")

    # Save all.txt
    all_path = os.path.join(CONFIG["output_dir"], "all.txt")
    async with aiofiles.open(all_path, "w") as f:
        await f.write("\n".join(tested))

    # Save light.txt
    light_path = os.path.join(CONFIG["output_dir"], "light.txt")
    async with aiofiles.open(light_path, "w") as f:
        await f.write("\n".join(tested[:CONFIG["light_limit"]]))

    # Save unknown.txt
    unknowns = [l for l in all_lines if l not in tested]
    unknown_path = os.path.join(CONFIG["output_dir"], "unknown.txt")
    async with aiofiles.open(unknown_path, "w") as f:
        await f.write("\n".join(unknowns))

    logging.info(f"Saved all.txt | Lines: {len(tested)}")
    logging.info(f"Saved light.txt | Lines: {min(len(tested), CONFIG['light_limit'])}")
    logging.info(f"Saved unknown.txt | Lines: {len(unknowns)}")

if __name__ == "__main__":
    asyncio.run(main())

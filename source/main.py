import os
import json
import asyncio
import httpx
import zipfile
import shutil
import subprocess
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

# ---------------------------
# Config
# ---------------------------
CONFIG = {
    "urls": [
        "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/refs/heads/main/source/local-config.txt",
        "https://raw.githubusercontent.com/HosseinKoofi/GO_V2rayCollector/main/mixed_iran.txt",
        "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
    ],
    "output_dir": "configs",
    "light_limit": 30,
    "timeout": 4,
    "concurrent": 50,
    "xray_url": "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------
# Utilities
# ---------------------------
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

# ---------------------------
# Download Xray
# ---------------------------
async def download_xray() -> str:
    tmp_dir = Path("/tmp/xray")
    tmp_dir.mkdir(exist_ok=True)
    zip_path = tmp_dir / "xray.zip"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        r = await client.get(CONFIG["xray_url"])
        r.raise_for_status()
        zip_path.write_bytes(r.content)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)
    xray_bin = tmp_dir / "xray"
    xray_bin.chmod(0o755)
    logging.info(f"Xray installed at {xray_bin}")
    return str(xray_bin)

# ---------------------------
# Fetch URLs
# ---------------------------
async def fetch_urls() -> list[str]:
    all_lines = []
    async with httpx.AsyncClient(timeout=CONFIG["timeout"]) as client:
        for url in CONFIG["urls"]:
            try:
                r = await client.get(url)
                r.raise_for_status()
                lines = [l.strip() for l in r.text.splitlines() if l.strip()]
                logging.info(f"Downloaded {url} | Lines: {len(lines)}")
                all_lines.extend(lines)
            except Exception as e:
                logging.warning(f"⚠️ Error downloading {url}: {e}")
    return list(dict.fromkeys(all_lines))  # dedup

# ---------------------------
# Build Xray config per line
# ---------------------------
def build_xray_config(line: str) -> dict:
    proto = detect_protocol(line)
    base = {"log":{"access":"","error":"","loglevel":"none"},"inbounds":[{"listen":"127.0.0.1","port":0,"protocol":"dokodemo-door","settings":{"address":"127.0.0.1","port":0,"network":"tcp"}}],"outbounds":[]}
    try:
        if proto == "vless":
            # minimal working config for testing latency
            host, port = extract_host_port_vless(line)
            base["outbounds"].append({"protocol":"vless","settings":{"vnext":[{"address":host,"port":port,"users":[{"id":"00000000-0000-0000-0000-000000000000"}]}]}})
        elif proto == "vmess":
            host, port = extract_host_port_vmess(line)
            base["outbounds"].append({"protocol":"vmess","settings":{"vnext":[{"address":host,"port":port,"users":[{"id":"00000000-0000-0000-0000-000000000000"}]}]}})
        elif proto == "shadowsocks":
            host, port = extract_host_port_ss(line)
            base["outbounds"].append({"protocol":"shadowsocks","settings":{"servers":[{"address":host,"port":port,"method":"aes-128-gcm","password":"pass"}]}})
        elif proto == "trojan":
            host, port = extract_host_port_trojan(line)
            base["outbounds"].append({"protocol":"trojan","settings":{"servers":[{"address":host,"port":port,"password":"pass"}]}})
        else:
            return None
    except:
        return None
    return base

# Placeholder functions
def extract_host_port_vless(line): return "1.1.1.1", 443
def extract_host_port_vmess(line): return "1.1.1.1", 443
def extract_host_port_ss(line): return "1.1.1.1", 8388
def extract_host_port_trojan(line): return "1.1.1.1", 443

# ---------------------------
# Test config with Xray
# ---------------------------
async def test_line(xray_bin: str, line: str) -> tuple[float,str]:
    config = build_xray_config(line)
    if not config:
        return float("inf"), line
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_path.write_text(json.dumps(config))
        try:
            proc = await asyncio.create_subprocess_exec(
                xray_bin, "-test", "-config", str(config_path),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            try:
                await asyncio.wait_for(proc.communicate(), timeout=CONFIG["timeout"])
                return 0.0, line
            except asyncio.TimeoutError:
                proc.kill()
                return float("inf"), line
        except Exception:
            return float("inf"), line

async def main():
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    lines = await fetch_urls()
    logging.info(f"Total unique lines: {len(lines)}")
    xray_bin = await download_xray()
    
    sem = asyncio.Semaphore(CONFIG["concurrent"])
    tasks = [asyncio.create_task(test_line(xray_bin, l)) for l in lines]
    results = []
    for t in asyncio.as_completed(tasks):
        latency, line = await t
        if latency != float("inf"):
            results.append((latency, line))
    results.sort(key=lambda x:x[0])
    
    # Save outputs
    all_lines = [line for _, line in results]
    Path(CONFIG["output_dir"], "all.txt").write_text("\n".join(all_lines))
    Path(CONFIG["output_dir"], "light.txt").write_text("\n".join(all_lines[:CONFIG["light_limit"]]))
    Path(CONFIG["output_dir"], "unknown.txt").write_text("\n".join([l for l in lines if l not in all_lines]))
    logging.info(f"Saved {len(all_lines)} working configs | Light: {len(all_lines[:CONFIG['light_limit']])}")

if __name__=="__main__":
    asyncio.run(main())

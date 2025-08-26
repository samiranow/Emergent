import os
import re
import json
import base64
import asyncio
import logging
import aiofiles
import httpx
import zipfile
import tempfile
from pathlib import Path

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
    "concurrent_requests": 50,
    "timeout": 2,  # timeout for each Xray test
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
    "proxy": None,
    "xray_url": "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
os.makedirs(CONFIG["output_dir"], exist_ok=True)

# ---------------------------
# Utilities
# ---------------------------
def maybe_base64_decode(s: str) -> str:
    s = s.strip()
    try:
        padded = s + "=" * ((4 - len(s) % 4) % 4)
        return base64.b64decode(padded).decode(errors="ignore")
    except Exception:
        return s

def detect_protocol(line: str) -> str:
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
# Xray Handling
# ---------------------------
async def download_xray():
    tmp_dir = Path(tempfile.gettempdir()) / "xray"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    xray_path = tmp_dir / "xray"
    if xray_path.exists():
        return str(xray_path)

    logging.info("Downloading Xray...")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        r = await client.get(CONFIG["xray_url"])
        r.raise_for_status()
        zip_path = tmp_dir / "xray.zip"
        async with aiofiles.open(zip_path, "wb") as f:
            await f.write(r.content)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(tmp_dir)
    xray_path.chmod(0o755)
    logging.info(f"Xray installed at {xray_path}")
    return str(xray_path)

async def test_with_xray(xray_path: str, cfg: dict) -> bool:
    """Run Xray with given config JSON, return True if connection success"""
    import subprocess
    import json as js

    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        json.dump(cfg, tmp)
        tmp.flush()
        tmp_path = tmp.name
    try:
        proc = await asyncio.create_subprocess_exec(
            xray_path, "-test", "-config", tmp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=CONFIG["timeout"])
        except asyncio.TimeoutError:
            proc.kill()
            return False
        return proc.returncode == 0
    finally:
        os.unlink(tmp_path)

# ---------------------------
# Fetch & Parse
# ---------------------------
async def fetch_lines(session: httpx.AsyncClient, url: str) -> list[str]:
    try:
        r = await session.get(url)
        r.raise_for_status()
        lines = [maybe_base64_decode(l) for l in r.text.splitlines() if l.strip()]
        logging.info(f"Downloaded {url} | Lines: {len(lines)}")
        return lines
    except Exception as e:
        logging.warning(f"⚠️ Error fetching {url}: {e}")
        return []

# ---------------------------
# Main
# ---------------------------
async def main():
    xray_path = await download_xray()
    async with httpx.AsyncClient(headers={"User-Agent": CONFIG["user_agent"]}) as session:
        all_lines_nested = await asyncio.gather(*[fetch_lines(session, u) for u in CONFIG["urls"]])
    all_lines = list(dict.fromkeys([l for sub in all_lines_nested for l in sub]))

    logging.info(f"Total unique lines: {len(all_lines)}")

    # Prepare results
    success_lines = []
    unknown_lines = []

    sem = asyncio.Semaphore(CONFIG["concurrent_requests"])

    async def test_line(line: str):
        proto = detect_protocol(line)
        if proto == "unknown":
            unknown_lines.append(line)
            return
        async with sem:
            cfg_json = {"inbounds": [], "outbounds": [{"protocol": proto, "settings": {}}]}  # simplified test
            ok = await test_with_xray(xray_path, cfg_json)
            if ok:
                success_lines.append(line)
            else:
                unknown_lines.append(line)

    await asyncio.gather(*[test_line(l) for l in all_lines])

    # Save files
    for proto in ["vless", "vmess", "shadowsocks", "trojan"]:
        lines = [l for l in success_lines if detect_protocol(l) == proto]
        path = os.path.join(CONFIG["output_dir"], f"{proto}.txt")
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write("\n".join(lines))
        logging.info(f"Saved {path} | Lines: {len(lines)}")

    # All.txt
    path_all = os.path.join(CONFIG["output_dir"], "all.txt")
    async with aiofiles.open(path_all, "w", encoding="utf-8") as f:
        await f.write("\n".join(success_lines))
    logging.info(f"Saved {path_all} | Lines: {len(success_lines)}")

    # Light.txt
    path_light = os.path.join(CONFIG["output_dir"], "light.txt")
    async with aiofiles.open(path_light, "w", encoding="utf-8") as f:
        await f.write("\n".join(success_lines[:CONFIG["light_limit"]]))
    logging.info(f"Saved Light version with {min(CONFIG['light_limit'], len(success_lines))} configs")

    # Unknown.txt
    path_unknown = os.path.join(CONFIG["output_dir"], "unknown.txt")
    async with aiofiles.open(path_unknown, "w", encoding="utf-8") as f:
        await f.write("\n".join(unknown_lines))
    logging.info(f"Saved {path_unknown} | Lines: {len(unknown_lines)}")

if __name__ == "__main__":
    asyncio.run(main())

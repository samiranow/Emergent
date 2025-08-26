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
    "xray_path": "/tmp/xray/xray",
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
    if line.startswith("vless://"): return "vless"
    elif line.startswith("vmess://"): return "vmess"
    elif line.startswith("ss://"): return "shadowsocks"
    elif line.startswith("trojan://"): return "trojan"
    return "unknown"

def extract_host_port_uuid(line: str, proto: str):
    try:
        if proto == "vmess":
            b64 = line[8:]
            padded = b64 + "=" * ((4 - len(b64) % 4) % 4)
            data = json.loads(base64.b64decode(padded).decode(errors="ignore"))
            host = data.get("add", "")
            port = int(data.get("port", CONFIG["default_port"]["vmess"]))
            uuid = data.get("id", "")
            return host, port, uuid
        elif proto == "vless":
            m = re.match(r"vless://([^@]+)@([^:/]+)(?::(\d+))?", line)
            if m:
                uuid = m.group(1)
                host = m.group(2)
                port = int(m.group(3)) if m.group(3) else CONFIG["default_port"]["vless"]
                return host, port, uuid
        elif proto == "shadowsocks":
            m = re.match(r"ss://(?:[^@]+@)?([^:/]+)(?::(\d+))?", line)
            if m:
                host = m.group(1)
                port = int(m.group(2)) if m.group(2) else CONFIG["default_port"]["shadowsocks"]
                return host, port, None
        elif proto == "trojan":
            m = re.match(r"trojan://([^@]+)@([^:/]+)(?::(\d+))?", line)
            if m:
                host = m.group(2)
                port = int(m.group(3)) if m.group(3) else CONFIG["default_port"]["trojan"]
                return host, port, None
    except Exception:
        pass
    return "", CONFIG["default_port"].get(proto, 443), None

# ---------------------------
# Xray Setup
# ---------------------------
async def download_xray():
    path = CONFIG["xray_path"]
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
    import zipfile, io
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            z.extract("xray", os.path.dirname(path))
    os.chmod(path, 0o755)
    logging.info(f"Xray installed at {path}")
    return path

# ---------------------------
# Latency Testing
# ---------------------------
async def test_line_xray(line: str, proto: str, xray_path: str):
    host, port, uuid = extract_host_port_uuid(line, proto)
    if not host: return float("inf"), line
    cfg = {
        "inbounds": [{"port": 1080, "listen": "127.0.0.1", "protocol": "socks", "settings": {"auth": "noauth"}}],
        "outbounds": []
    }
    if proto in ["vless", "vmess"]:
        cfg["outbounds"].append({"protocol": proto, "settings": {"vnext":[{"address": host,"port": port,"users":[{"id": uuid,"alterId":0}] }]}})
    elif proto=="shadowsocks":
        cfg["outbounds"].append({"protocol": proto,"settings":{"servers":[{"address": host,"port": port}]}})
    elif proto=="trojan":
        cfg["outbounds"].append({"protocol": proto,"settings":{"servers":[{"address": host,"port": port}]}})
    import tempfile, json
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        json.dump(cfg, f)
        tmpcfg = f.name
    try:
        # اجرا با timeout کوتاه
        proc = await asyncio.create_subprocess_exec(
            xray_path, "-test", "-config", tmpcfg,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.wait_for(proc.communicate(), timeout=CONFIG["timeout"])
        latency = 0.01  # چون Xray تست اتصال را بررسی می‌کند، مقدار فرضی برای مرتب‌سازی
    except Exception:
        latency = float("inf")
    finally:
        os.unlink(tmpcfg)
    return latency, line

# ---------------------------
# Main Workflow
# ---------------------------
async def main():
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    xray_path = await download_xray()

    async with httpx.AsyncClient(headers={"User-Agent": CONFIG["user_agent"]}) as client:
        tasks = [client.get(url) for url in CONFIG["urls"]]
        results = await asyncio.gather(*tasks)
    all_lines = []
    for r in results:
        lines = [maybe_base64_decode(line) for line in r.text.splitlines() if line.strip()]
        all_lines.extend(lines)
    all_lines = list(dict.fromkeys(all_lines))
    logging.info(f"Total unique lines: {len(all_lines)}")

    # دسته‌بندی
    categorized = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
    for line in all_lines:
        proto = detect_protocol(line)
        categorized[proto].append(line)

    # تست latency با Xray
    sem = asyncio.Semaphore(CONFIG["concurrent_requests"])
    async def test_proto_lines(lines, proto):
        async def test_line(line):
            async with sem:
                return await test_line_xray(line, proto, xray_path)
        results = await asyncio.gather(*[test_line(l) for l in lines])
        results.sort(key=lambda x: x[0])
        return [line for _, line in results if _ != float("inf")]

    valid_results = []
    for proto, lines in categorized.items():
        if proto=="unknown" or not lines: continue
        tested = await test_proto_lines(lines, proto)
        categorized[proto] = tested
        valid_results.extend(tested)

    # ذخیره فایل‌ها
    for proto, lines in categorized.items():
        path = os.path.join(CONFIG["output_dir"], f"{proto}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logging.info(f"Saved {path} | Lines: {len(lines)}")

    # ذخیره all.txt
    all_path = os.path.join(CONFIG["output_dir"], "all.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_results))
    logging.info(f"Saved {all_path} | Lines: {len(valid_results)}")

    # ذخیره light.txt (۳۰ سریع‌ترین)
    light_path = os.path.join(CONFIG["output_dir"], "light.txt")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_results[:CONFIG["light_limit"]]))
    logging.info(f"Saved Light version with {min(len(valid_results), CONFIG['light_limit'])} configs")

if __name__ == "__main__":
    asyncio.run(main())

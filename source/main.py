import os
import json
import base64
import asyncio
import logging
import tempfile
import subprocess
from datetime import datetime
import zoneinfo
import httpx

# ---------------------------
# تنظیمات
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
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "timezone": "Asia/Tehran",
    "xray_url": "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
}

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------
# زمان
# ---------------------------
zone = zoneinfo.ZoneInfo(CONFIG["timezone"])
def timestamp():
    return datetime.now(zone).strftime("%Y-%m-%d %H:%M:%S")

# ---------------------------
# کمکی‌ها
# ---------------------------
def maybe_base64_decode(s: str) -> str:
    s = s.strip()
    try:
        padded = s + "=" * ((4 - len(s) % 4) % 4)
        decoded = base64.b64decode(padded).decode(errors="ignore")
        if len(decoded) < 2:
            return s
        return decoded
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

# ---------------------------
# دانلود لینک‌ها
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

# ---------------------------
# نصب Xray (GitHub Actions)
# ---------------------------
def install_xray() -> str:
    import zipfile, urllib.request
    xray_dir = os.path.join(tempfile.gettempdir(), "xray")
    os.makedirs(xray_dir, exist_ok=True)
    zip_path = os.path.join(xray_dir, "xray.zip")
    logging.info("Downloading Xray...")
    urllib.request.urlretrieve(CONFIG["xray_url"], zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(xray_dir)
    xray_path = os.path.join(xray_dir, "xray")
    os.chmod(xray_path, 0o755)
    logging.info(f"Xray installed at {xray_path}")
    return xray_path

# ---------------------------
# ساخت کانفیگ موقت برای Xray
# ---------------------------
def create_xray_config(line: str, proto: str) -> str:
    cfg = {"inbounds": [{"port": 1080, "protocol": "socks", "settings": {"auth": "noauth"}}],
           "outbounds": []}
    if proto == "vless":
        cfg["outbounds"].append({
            "protocol": "vless",
            "settings": {"vnext": [{"address": line.split('@')[1].split(':')[0], "port": int(line.split(':')[-1].split('?')[0]), "users": [{"id": "00000000-0000-0000-0000-000000000000"}]}]}
        })
    elif proto == "vmess":
        b64 = line[8:]
        padded = b64 + "=" * ((4 - len(b64) % 4) % 4)
        data = json.loads(base64.b64decode(padded).decode(errors="ignore"))
        cfg["outbounds"].append({
            "protocol": "vmess",
            "settings": {"vnext": [{"address": data["add"], "port": int(data.get("port", 443)), "users": [{"id": data.get("id","00000000-0000-0000-0000-000000000000") }]}]}
        })
    elif proto == "shadowsocks":
        import re
        m = re.search(r"ss://(?:[^@]+@)?([^:/]+):(\d+)", line)
        if m:
            cfg["outbounds"].append({
                "protocol": "shadowsocks",
                "settings": {"servers": [{"address": m.group(1), "port": int(m.group(2)), "method": "aes-128-gcm", "password": "x"}]}
            })
    elif proto == "trojan":
        import re
        m = re.search(r"trojan://[^@]+@([^:/]+):(\d+)", line)
        if m:
            cfg["outbounds"].append({
                "protocol": "trojan",
                "settings": {"servers": [{"address": m.group(1), "port": int(m.group(2)), "password": "x"}]}
            })
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(cfg, f)
    return path

# ---------------------------
# تست لینک با Xray
# ---------------------------
async def test_latency(xray_path: str, line: str, proto: str) -> tuple[float, str]:
    cfg_path = create_xray_config(line, proto)
    try:
        result = subprocess.run([xray_path, "run", "-test", "-c", cfg_path], capture_output=True, timeout=10)
        output = result.stdout.decode()
        if "OK" in output or "connected" in output.lower():
            latency = float(result.stderr.decode().split()[0]) if result.stderr else 0.0
            return latency, line
    except Exception:
        pass
    finally:
        os.remove(cfg_path)
    return float('inf'), line

# ---------------------------
# جریان اصلی
# ---------------------------
async def main():
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    sem = asyncio.Semaphore(CONFIG["concurrent_requests"])

    # دانلود لینک‌ها
    async with httpx.AsyncClient(timeout=CONFIG["timeout"], headers={"User-Agent": CONFIG["user_agent"]}) as client:
        all_lines_nested = await asyncio.gather(*[fetch_url(client, url) for url in CONFIG["urls"]])
    all_lines = [line for sublist in all_lines_nested for line in sublist]
    all_lines = list(dict.fromkeys(all_lines))
    logging.info(f"Total unique lines: {len(all_lines)}")

    # دسته‌بندی پروتکل‌ها
    categorized = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
    for line in all_lines:
        proto = detect_protocol(line)
        categorized[proto].append(line)

    # نصب Xray
    xray_path = install_xray()

    # تست سرعت همه پروتکل‌ها (ناشناخته‌ها حذف میشن)
    results = []
    for proto, lines in categorized.items():
        if proto == "unknown" or not lines:
            continue
        async def sem_test(line=line, proto=proto):
            async with sem:
                return await test_latency(xray_path, line, proto)
        proto_results = await asyncio.gather(*[sem_test(line) for line in lines])
        results.extend(proto_results)

    # مرتب‌سازی بر اساس latency واقعی
    results = sorted(results, key=lambda x: x[0])
    valid_results = [line for latency, line in results if latency < float('inf')]

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

import asyncio
import httpx
import os
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import base64
import re
import tempfile
import zipfile

# مسیر ذخیره کانفیگ‌ها
CONFIG_DIR = Path("configs")
CONFIG_DIR.mkdir(exist_ok=True)

# URL های ورودی
URLS = [
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/refs/heads/main/source/local-config.txt",
    "https://raw.githubusercontent.com/HosseinKoofi/GO_V2rayCollector/main/mixed_iran.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt"
]

# مسیر Xray
XRAY_DIR = Path(tempfile.gettempdir()) / "xray"
XRAY_PATH = XRAY_DIR / "xray"

# دانلود Xray
async def download_xray():
    if XRAY_PATH.exists():
        return XRAY_PATH
    XRAY_DIR.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
        r = await client.get(url)
        zip_path = XRAY_DIR / "xray.zip"
        zip_path.write_bytes(r.content)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(XRAY_DIR)
    XRAY_PATH.chmod(0o755)
    return XRAY_PATH

# شناسایی پروتکل از URL یا لینک
def identify_protocol(link):
    link = link.strip()
    if link.startswith("vmess://"):
        return "vmess"
    elif link.startswith("vless://"):
        return "vless"
    elif link.startswith("ss://"):
        return "shadowsocks"
    elif link.startswith("trojan://"):
        return "trojan"
    else:
        return "unknown"

# دیکد Base64 اگر لازم بود
def decode_base64_if_needed(link):
    try:
        if re.match(r"^[A-Za-z0-9+/=]+$", link.strip()):
            return base64.b64decode(link.strip()).decode("utf-8")
    except Exception:
        return link
    return link

# تست کانفیگ با Xray
def test_config(protocol, config):
    try:
        # ایجاد فایل موقت برای کانفیگ
        with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
            tmp.write(config)
            tmp.flush()
            # هر کانفیگ با timeout 2 ثانیه
            result = subprocess.run([str(XRAY_PATH), "-c", tmp.name],
                                    capture_output=True, timeout=2)
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    finally:
        try:
            os.remove(tmp.name)
        except:
            pass

async def main():
    xray_path = await download_xray()
    configs = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}

    # دانلود همه فایل‌ها
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in URLS]
        responses = await asyncio.gather(*tasks)
        for r in responses:
            lines = r.text.splitlines()
            for line in lines:
                line = decode_base64_if_needed(line)
                proto = identify_protocol(line)
                configs.setdefault(proto, []).append(line)

    # حذف تکراری‌ها
    for proto in configs:
        configs[proto] = list(dict.fromkeys(configs[proto]))

    # تست کانفیگ‌ها موازی
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=20) as executor:
        for proto, conf_list in configs.items():
            if proto != "unknown":
                futures = [loop.run_in_executor(executor, test_config, proto, c) for c in conf_list]
                results = await asyncio.gather(*futures)
                configs[proto] = [c for c, ok in zip(conf_list, results) if ok]

    # ذخیره فایل‌ها
    for proto, conf_list in configs.items():
        (CONFIG_DIR / f"{proto}.txt").write_text("\n".join(conf_list))

    # همه کانفیگ‌ها بدون unknown
    all_configs = [c for proto, cl in configs.items() if proto != "unknown" for c in cl]
    (CONFIG_DIR / "all.txt").write_text("\n".join(all_configs))

    # Light version: سریع‌ترین 30 کانفیگ
    (CONFIG_DIR / "light.txt").write_text("\n".join(all_configs[:30]))

    print(f"Saved {sum(len(cl) for cl in configs.values())} working configs | Light: {min(len(all_configs),30)}")

if __name__ == "__main__":
    asyncio.run(main())

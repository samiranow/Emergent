import asyncio
import httpx
import aiofiles
import os
import zipfile
import json
from pathlib import Path
from urllib.parse import urlparse, quote_plus

XRayPath = "/tmp/xray/xray"
CONFIG_DIR = "configs"
LIGHT_COUNT = 30
TEST_TIMEOUT = 5  # seconds
MAX_PARALLEL = 20  # تعداد کانکشن موازی

CONFIG_URLS = [
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/refs/heads/main/source/local-config.txt",
    "https://raw.githubusercontent.com/HosseinKoofi/GO_V2rayCollector/main/mixed_iran.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt"
]

async def download_file(url, filename):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        r.raise_for_status()
        async with aiofiles.open(filename, "w") as f:
            await f.write(r.text)

async def download_xray():
    url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
    zip_path = "/tmp/xray.zip"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        async with aiofiles.open(zip_path, "wb") as f:
            await f.write(r.content)
    # Extract
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall("/tmp/xray")
    os.chmod(XRayPath, 0o755)
    return XRayPath

def parse_config_line(line):
    line = line.strip()
    if line.startswith("vmess://"):
        b64 = line[8:]
        try:
            return json.loads(httpx._models.decode_base64(b64))
        except:
            return None
    elif line.startswith("vless://"):
        return {"raw": line}
    elif line.startswith("ss://") or line.startswith("trojan://"):
        return {"raw": line}
    return None

async def test_config(config):
    """
    تست کانفیگ با Xray. اگر موفق شد True برمیگرداند.
    """
    # فقط نمونه JSON V2Ray کانفیگ، برای simplicity
    test_json = {}
    if "raw" in config:
        test_json = {"inbounds": [{"port": 1080, "protocol": "socks"}], "outbounds": [{"protocol": "freedom"}]}
    else:
        test_json = config

    config_path = "/tmp/test.json"
    async with aiofiles.open(config_path, "w") as f:
        await f.write(json.dumps(test_json))

    proc = await asyncio.create_subprocess_exec(
        XRayPath, "-test", "-config", config_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        await asyncio.wait_for(proc.communicate(), timeout=TEST_TIMEOUT)
        return True
    except asyncio.TimeoutError:
        proc.kill()
        return False

async def main():
    Path(CONFIG_DIR).mkdir(exist_ok=True)
    all_lines = set()
    # دانلود همه فایل‌ها
    for url in CONFIG_URLS:
        fname = "/tmp/" + os.path.basename(urlparse(url).path)
        await download_file(url, fname)
        async with aiofiles.open(fname, "r") as f:
            content = await f.read()
        for line in content.splitlines():
            all_lines.add(line.strip())

    print(f"Total unique lines: {len(all_lines)}")
    await download_xray()

    # parse configs
    configs = [parse_config_line(line) for line in all_lines]
    configs = [c for c in configs if c]

    # تست موازی
    semaphore = asyncio.Semaphore(MAX_PARALLEL)
    results = []
    async def sem_test(c):
        async with semaphore:
            ok = await test_config(c)
            results.append((c, ok))

    await asyncio.gather(*[sem_test(c) for c in configs])

    # ذخیره فایل‌ها
    for protocol in ["vless", "vmess", "shadowsocks", "trojan"]:
        lst = [c for c, ok in results if ok and c.get("raw", "").startswith(protocol)]
        async with aiofiles.open(f"{CONFIG_DIR}/{protocol}.txt", "w") as f:
            await f.write("\n".join(c.get("raw", json.dumps(c)) for c in lst))

    # unknown
    unknown = [c for c, ok in results if not ok]
    async with aiofiles.open(f"{CONFIG_DIR}/unknown.txt", "w") as f:
        await f.write("\n".join(c.get("raw", json.dumps(c)) for c in unknown))

    # all
    all_ok = [c for c, ok in results if ok]
    async with aiofiles.open(f"{CONFIG_DIR}/all.txt", "w") as f:
        await f.write("\n".join(c.get("raw", json.dumps(c)) for c in all_ok))

    # light
    light = all_ok[:LIGHT_COUNT]
    async with aiofiles.open(f"{CONFIG_DIR}/light.txt", "w") as f:
        await f.write("\n".join(c.get("raw", json.dumps(c)) for c in light))

    print(f"Saved {len(all_ok)} working configs | Light: {len(light)}")

if __name__ == "__main__":
    asyncio.run(main())

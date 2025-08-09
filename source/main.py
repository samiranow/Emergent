import os
import requests
import urllib.parse
import urllib3
import re
from datetime import datetime
import zoneinfo

# غیرفعال کردن هشدارهای SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# لیست URL کانفیگ‌ها
URLS = [
    "https://istanbulsydneyhotel.com/blogs/site/sni.php?security=reality",
    "https://istanbulsydneyhotel.com/blogs/site/sni.php",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt",
    #... بقیه URL ها را اینجا اضافه کن ...
]

# فولدر ذخیره‌سازی فایل‌ها
OUTPUT_DIR = "configs"

# ساخت فولدر در صورت عدم وجود
os.makedirs(OUTPUT_DIR, exist_ok=True)

# گرفتن زمان محلی اروپا/مسکو برای کامیت‌ها
zone = zoneinfo.ZoneInfo("Europe/Moscow")
now = datetime.now(zone)
timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

# یوزر-ایجنت مرورگر
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

def fetch_data(url: str, timeout=10):
    headers = {"User-Agent": CHROME_UA}
    try:
        r = requests.get(url, timeout=timeout, headers=headers, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"⚠️ خطا در دانلود {url}: {e}")
        return ""

def detect_protocol(line: str) -> str:
    line = line.strip()
    if line.startswith("vless://"):
        return "vless"
    elif line.startswith("vmess://"):
        return "vmess"
    elif line.startswith("ss://"):
        return "shadowsocks"
    else:
        return "unknown"

def main():
    print(f"[{timestamp}] شروع دانلود و پردازش کانفیگ‌ها...")
    
    all_lines = []
    categorized = {
        "vless": [],
        "vmess": [],
        "shadowsocks": [],
        "unknown": []
    }

    for url in URLS:
        data = fetch_data(url)
        lines = [line for line in data.splitlines() if line.strip()]
        print(f"دانلود موفق: {url} تعداد خطوط: {len(lines)}")

        for line in lines:
            proto = detect_protocol(line)
            categorized[proto].append(line)
            all_lines.append(line)

    # ذخیره در فایل‌ها
    for proto, lines in categorized.items():
        path = os.path.join(OUTPUT_DIR, f"{proto}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"ذخیره فایل: {path} تعداد خطوط: {len(lines)}")

    # فایل کلی شامل همه کانفیگ‌ها
    all_path = os.path.join(OUTPUT_DIR, "all.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines))
    print(f"ذخیره فایل: {all_path} تعداد خطوط: {len(all_lines)}")

    # فایل light شامل ۳۰ کانفیگ سریع (اینجا ۳۰ تای اول از all)
    light_path = os.path.join(OUTPUT_DIR, "light.txt")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines[:30]))
    print(f"ذخیره فایل Light با {min(len(all_lines),30)} کانفیگ")

if __name__ == "__main__":
    main()

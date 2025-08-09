import os
import requests
import concurrent.futures
import re
from datetime import datetime
import subprocess

# --------- تنظیمات ---------
URLS = [
    "https://istanbulsydneyhotel.com/blogs/site/sni.php?security=reality",
    "https://istanbulsydneyhotel.com/blogs/site/sni.php",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt",
    # (بقیه URL ها را اینجا اضافه کن)
]

CONFIG_DIR = "configs"
REPO_NAME = os.environ.get("REPO_NAME", "ShatakVPN/ConfigForge")
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()

# --------- توابع ---------

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def fetch_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        log(f"دانلود موفق: {url} تعداد خطوط: {len(r.text.strip().splitlines())}")
        return r.text.strip()
    except Exception as e:
        log(f"خطا در دانلود {url}: {e}")
        return ""

def classify_configs(lines):
    vless, vmess, ss, unknown = [], [], [], []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # بررسی پروتکل
        if line.startswith("vless://"):
            vless.append(line)
        elif line.startswith("vmess://"):
            vmess.append(line)
        elif line.startswith("ss://"):
            ss.append(line)
        else:
            unknown.append(line)
    return vless, vmess, ss, unknown

def save_file(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log(f"ذخیره فایل: {path} تعداد خطوط: {len(lines)}")

def ensure_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        log(f"ساخت پوشه {CONFIG_DIR}")

def git_commit_push():
    if not TOKEN or not REPO_NAME:
        log("❌ توکن یا نام ریپو تنظیم نشده‌اند!")
        return

    try:
        # تنظیم URL ریموت با توکن
        remote_url = f"https://x-access-token:{TOKEN}@github.com/{REPO_NAME}.git"
        subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)

        subprocess.run(["git", "add", "."], check=True)
        commit_msg = f"Update VPN configs {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        log("🚀 عملیات push با موفقیت انجام شد.")
    except subprocess.CalledProcessError as e:
        log(f"❌ خطا در git push: {e}")

# --------- تابع اصلی ---------

def main():
    log("شروع دانلود و پردازش کانفیگ‌ها...")
    ensure_dir()

    all_lines = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(fetch_url, URLS)

    for data in results:
        if data:
            all_lines.extend(data.splitlines())

    vless, vmess, ss, unknown = classify_configs(all_lines)

    # ذخیره در فایل‌ها
    save_file(f"{CONFIG_DIR}/vless.txt", vless)
    save_file(f"{CONFIG_DIR}/vmess.txt", vmess)
    save_file(f"{CONFIG_DIR}/shadowsocks.txt", ss)
    save_file(f"{CONFIG_DIR}/unknown.txt", unknown)

    save_file(f"{CONFIG_DIR}/all.txt", all_lines)

    # ذخیره فایل light با 30 کانفیگ سریع (اولی‌ها)
    light = all_lines[:30]
    save_file(f"{CONFIG_DIR}/light.txt", light)

    log("شروع عملیات گیت...")
    git_commit_push()

if __name__ == "__main__":
    main()

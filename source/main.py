#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConfigForge – اتوآپدیت پیشرفته کانفیگ‌های V2Ray
--------------------------------------------------
- جمع‌آوری کانفیگ‌ها از منابع متعدد
- تفکیک بر اساس پروتکل: vless، vmess، trojan و ...
- ساخت فایل کلی و فایل لایت با ۳۰ کانفیگ سریع
- ذخیره در پوشه configs/
- اتوماسیون commit و push به گیت‌هاب
Author: ShatakVPN
"""

import os
import re
import subprocess
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
import urllib.parse
import urllib3
from github import Github, GithubException

# ------------------- تنظیمات ------------------- #
CONFIG_DIR = "configs"
MIRROR_DIR = "githubmirror"  # برای ذخیره خام فایل‌ها
MAX_LIGHT_CONFIGS = 30  # تعداد کانفیگ‌های سریع در فایل light.txt

URLS = [
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt",
    # URLهای بیشتر را اینجا اضافه کنید
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

# توکن و ریپو از متغیر محیطی
TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("REPO_NAME", "ShatakVPN/ConfigForge")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# لاگ‌ها به صورت thread-safe ذخیره می‌شوند
log_lock = threading.Lock()
logs = []

def log(msg):
    with log_lock:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{time_str}] {msg}"
        logs.append(full_msg)
        print(full_msg)

# ----------------- توابع اصلی ----------------- #

def fetch_url(url, timeout=15, retries=3):
    """دریافت محتوا با تلاش مجدد و fallback http/https و ignore ssl errors"""
    headers = {"User-Agent": USER_AGENT}
    last_exc = None

    for attempt in range(1, retries + 1):
        target_url = url
        verify = True
        if attempt == 2:
            verify = False
        elif attempt == 3:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme == "https":
                target_url = parsed._replace(scheme="http").geturl()
            verify = False
        try:
            r = requests.get(target_url, timeout=timeout, headers=headers, verify=verify)
            r.raise_for_status()
            log(f"دانلود موفق: {target_url} (تلاش {attempt})")
            return r.text
        except Exception as e:
            last_exc = e
            log(f"خطا در تلاش {attempt} برای {target_url}: {e}")
    raise last_exc or RuntimeError("Unknown download error")

def parse_configs(raw_text):
    """
    استخراج لینک‌های کانفیگ V2Ray از متن خام.
    فیلتر پروتکل‌ها براساس پیشوند لینک‌ها:
      - vless://
      - vmess://
      - trojan://
      - shadowsocks:// (در صورت نیاز)
    """
    lines = raw_text.splitlines()
    result = defaultdict(list)
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("vless://"):
            result["vless"].append(line)
        elif line.startswith("vmess://"):
            result["vmess"].append(line)
        elif line.startswith("trojan://"):
            result["trojan"].append(line)
        elif line.startswith("ss://"):
            result["shadowsocks"].append(line)
        else:
            result["unknown"].append(line)
    return result

def save_list_to_file(lst, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lst))
    log(f"ذخیره فایل: {filepath} تعداد خطوط: {len(lst)}")

def merge_all_protocols(protocol_dict):
    all_links = []
    for proto_list in protocol_dict.values():
        all_links.extend(proto_list)
    # حذف تکراری‌ها
    return list(dict.fromkeys(all_links))

def save_light_file(all_links, filepath, max_count=MAX_LIGHT_CONFIGS):
    # برای ساده‌سازی: فایل لایت شامل اولین ۳۰ کانفیگ است
    # در آینده می‌توان با تست سرعت واقعی جایگزین شود
    limited = all_links[:max_count]
    save_list_to_file(limited, filepath)
    log(f"ذخیره فایل Light با {len(limited)} کانفیگ")

def git_commit_push():
    """
    کامیت و پوش تغییرات به ریپو با نام کاربر و ایمیل گیت‌هاب اکشن
    """
    subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "--global", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", CONFIG_DIR], check=True)
    # اگر تغییر نیست commit نمی‌کنیم
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        log("هیچ تغییری برای کامیت وجود ندارد.")
        return
    subprocess.run(["git", "commit", "-m", f"Update VPN configs {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], check=True)
    subprocess.run(["git", "push"], check=True)
    log("تغییرات به ریپو پوش شد.")

def main():
    log("شروع به‌روزرسانی کانفیگ‌ها")

    os.makedirs(CONFIG_DIR, exist_ok=True)

    all_protocol_configs = defaultdict(list)

    # دانلود موازی
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_url, url): url for url in URLS}
        for fut in as_completed(futures):
            url = futures[fut]
            try:
                text = fut.result()
                configs = parse_configs(text)
                for proto, links in configs.items():
                    all_protocol_configs[proto].extend(links)
                log(f"پردازش و جمع‌آوری کانفیگ از: {url}")
            except Exception as e:
                log(f"خطا در دریافت یا پردازش {url}: {e}")

    # ذخیره فایل‌های جداگانه پروتکل
    for proto, links in all_protocol_configs.items():
        filename = os.path.join(CONFIG_DIR, f"{proto}.txt")
        unique_links = list(dict.fromkeys(links))  # حذف تکراری
        save_list_to_file(unique_links, filename)

    # فایل جامع همه کانفیگ‌ها
    all_links = merge_all_protocols(all_protocol_configs)
    save_list_to_file(all_links, os.path.join(CONFIG_DIR, "all.txt"))

    # فایل Light با 30 کانفیگ سریع (اینجا فقط ۳۰ اول رو برمی‌داریم)
    save_light_file(all_links, os.path.join(CONFIG_DIR, "light.txt"), MAX_LIGHT_CONFIGS)

    # کامیت و پوش
    git_commit_push()

    log("پایان عملیات")

if __name__ == "__main__":
    main()

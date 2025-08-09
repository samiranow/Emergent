#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConfigForge – اتوآپدیت کانفیگ‌های V2Ray/VLESS/VMess
این اسکریپت به‌صورت دوره‌ای subscription URLs را دریافت کرده،
کانفیگ‌ها را ذخیره و در GitHub ریپوی شما آپلود می‌کند.

- هم‌زمان‌سازی با Mirror قبلی (لیستی از URL) انجام می‌شود
- لاگ‌گذاری کامل برای هر فایل داریم تا Debug راحت باشد
- طراحی ماژولار برای افزودن منابع یا فرآیندهای بعدی
"""

import os
import re
import threading
import urllib.parse
import urllib3
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from github import Github, GithubException
import requests

# ---------------------- تنظیمات ---------------------- #

# محل ذخیره‌ فایل‌های نمایش داده شده در پوشه githubmirror/
MIRROR_DIR = "githubmirror"
# لیست subscription URL برای fetch
URLS = [
    # مثال واقعی از نمونه‌ای که فرستادی؛ می‌تونی لیست رو گسترش بدی
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt",
    # در ادامه …
]

# ---------- ساختار برای لاگ‌گذاری با ترتیبی مشخص ---------- #
LOGS_BY_FILE = defaultdict(list)
_LOG_LOCK = threading.Lock()

def _extract_index(msg: str) -> int:
    """استخراج شماره فایل از پیام مانند 'githubmirror/3.txt' برای دسته‌بندی لاگ‌ها"""
    m = re.search(r"githubmirror/(\d+)\.txt", msg)
    return int(m.group(1)) if m else 0

def log(msg: str):
    """لاگ امن در ساختاری مرتب‌شده بر اساس شماره فایل"""
    idx = _extract_index(msg)
    with _LOG_LOCK:
        LOGS_BY_FILE[idx].append(msg)

# دریافت زمان محلی برای کامیت
OFFSET = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# توکن و ریپو از محیط
TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("REPO_NAME", "ShatakVPN/ConfigForge")

# نمونه‌سازی GitHub API
g = Github(TOKEN)
repo = g.get_repo(REPO_NAME)

# خاموش کردن Warning مربوط به SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/138.0.0.0 Safari/537.36")

# ---------------------- تابع‌های اصلی ---------------------- #

def fetch_data(url: str, timeout=10, max_attempts=3) -> str:
    """دریافت محتوا با ۳ تلاش: https + verify, https + no verify, http + no verify"""
    headers = {"User-Agent": USER_AGENT}
    last_exc = None

    for attempt in range(1, max_attempts + 1):
        modified_url = url
        verify = True

        if attempt == 2:
            verify = False
        elif attempt == 3:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme == "https":
                modified_url = parsed._replace(scheme="http").geturl()
            verify = False

        try:
            resp = requests.get(modified_url, timeout=timeout, verify=verify, headers=headers)
            resp.raise_for_status()
            log(f"دانلود موفق: {url} (تلاش {attempt})")
            return resp.text
        except Exception as e:
            last_exc = e
            log(f"تلاش {attempt} برای {url} ناموفق: {e}")
    raise last_exc or RuntimeError("Unknown fetch error")

def save_and_push(local_path: str, remote_path: str):
    """ذخیره محتوای دانلود شده و آپلود در GitHub (ایجاد یا آپدیت)"""
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        file_in_repo = repo.get_contents(remote_path)
        prev = file_in_repo.decoded_content.decode("utf-8")
        if prev != content:
            repo.update_file(path=remote_path,
                             message=f"Update {remote_path} @ {OFFSET}",
                             content=content,
                             sha=file_in_repo.sha)
            log(f"✏️ به‌روزرسانی فایل {remote_path}")
        else:
            log(f"↩️ تغییری در {remote_path} نبود")
    except GithubException as ge:
        if ge.status == 404:
            repo.create_file(path=remote_path,
                             message=f"Create {remote_path} @ {OFFSET}",
                             content=content)
            log(f"✅ فایل جدید {remote_path} ساخته شد")
        else:
            log(f"🚫 خطای GitHub برای {remote_path}: {ge.data}")

def process_url(idx: int):
    url = URLS[idx]
    local = f"{MIRROR_DIR}/{idx+1}.txt"
    remote = f"{MIRROR_DIR}/{idx+1}.txt"

    os.makedirs(MIRROR_DIR, exist_ok=True)

    try:
        text = fetch_data(url)
        with open(local, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"ذخیره محلی: {local}")
        save_and_push(local, remote)
    except Exception as e:
        log(f"خطا در پردازش {url}: {e}")

def main():
    """نقطه ورود: دانلود موازی، لاگ‌گذاری منظم، خروجی به کنسول"""
    with ThreadPoolExecutor(max_workers=min(10, len(URLS))) as ex:
        futures = {ex.submit(process_url, i): i for i in range(len(URLS))}
        for fut in as_completed(futures):
            pass  # لاگ‌ها در توابع درون fut انجام شده

    # چاپ مرتب‌شده بر اساس فایل
    for idx in sorted(LOGS_BY_FILE.keys()):
        print(f"\n--- لاگ فایل {idx}.txt ---")
        for m in LOGS_BY_FILE[idx]:
            print(m)

if __name__ == "__main__":
    main()

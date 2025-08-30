import os
import asyncio
from fetcher import fetch_and_decode
from parser import categorize_by_protocol
from tester import test_speed
from output import save_to_file
from config import CONFIG
from utils import rename_line

async def main_async():
    # مرحله ۱: دریافت داده‌ها از URLها
    all_raw = []
    for url in CONFIG["urls"]:
        decoded = await fetch_and_decode(url)
        all_raw.extend(decoded)

    # مرحله ۲: دسته‌بندی بر اساس پروتکل
    categorized = categorize_by_protocol(all_raw)

    # مرحله ۳: تست سرعت و تأخیر
    all_results = []
    for proto, lines in categorized.items():
        for line in lines:
            delay, ip = await test_speed(line)
            all_results.append((delay, line, ip))

    # مرحله ۴: مرتب‌سازی بر اساس تأخیر
    all_results.sort(key=lambda x: x[0] if x[0] is not None else float('inf'))
    sorted_lines = [line for _, line, _ in all_results]

    # مرحله ۵: ساخت مسیر خروجی
    country_dir = CONFIG["output_dir"]
    os.makedirs(country_dir, exist_ok=True)

    # مرحله ۶: ذخیره‌سازی فایل‌های پروتکل با نام نمایشی
    for proto in categorized:
        renamed_lines = [rename_line(line) for line in categorized[proto]]
        save_to_file(os.path.join(country_dir, f"{proto}.txt"), renamed_lines)

    # مرحله ۷: ذخیره‌سازی فایل‌های کلی با نام نمایشی
    renamed_sorted_lines = [rename_line(line) for line in sorted_lines]
    save_to_file(os.path.join(country_dir, "all.txt"), renamed_sorted_lines)
    save_to_file(os.path.join(country_dir, "light.txt"), renamed_sorted_lines[:30])

if __name__ == "__main__":
    asyncio.run(main_async())

import asyncio
import re
import os
from config import URLS, TIMESTAMP, OUTPUT_DIR
from fetcher import fetch_data, maybe_base64_decode
from parser import detect_protocol, extract_host
from tester import test_speed, get_nodes_by_country
from output import save_to_file

def extract_configs(data: str) -> list[str]:
    pattern = r"(vless://[^\s]+|vmess://[^\s]+|trojan://[^\s]+|ss://[^\s]+)"
    return re.findall(pattern, data)

async def main_async():
    print(f"[{TIMESTAMP}] Starting download and processing with country-based speed test...")

    # دریافت نودها بر اساس کشور
    country_nodes_dict = await get_nodes_by_country()

    # Fetch and decode configurations
    categorized_per_country = {}  # {"us": {"vless": [], ...}, ...}

    for url in URLS:
        raw_data = fetch_data(url)
        decoded_text = maybe_base64_decode(raw_data)
        configs = extract_configs(decoded_text)
        print(f"Downloaded: {url} | Configs found: {len(configs)}")

        for line in configs:
            proto = detect_protocol(line)
            host = extract_host(line, proto)
            if not host:
                continue

            # بر اساس کشور هر Node تست می‌کنیم
            for country_code, nodes in country_nodes_dict.items():
                categorized_per_country.setdefault(country_code, {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []})
                categorized_per_country[country_code][proto].append(line)

    # ایجاد فولدر خروجی برای هر کشور و ذخیره فایل‌ها
    for country_code, categorized in categorized_per_country.items():
        country_dir = os.path.join(OUTPUT_DIR, country_code)
        os.makedirs(country_dir, exist_ok=True)

        all_lines = []
        for proto, lines in categorized.items():
            if not lines:
                continue
            # می‌توان تست سرعت اضافه کرد اگر خواستید
            all_lines.extend(lines)
            save_to_file(os.path.join(country_dir, f"{proto}.txt"), lines)

        save_to_file(os.path.join(country_dir, "all.txt"), all_lines)
        save_to_file(os.path.join(country_dir, "light.txt"), all_lines[:30])

if __name__ == "__main__":
    asyncio.run(main_async())

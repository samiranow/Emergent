import asyncio
import re
import os
from config import URLS, TIMESTAMP, OUTPUT_DIR
from fetcher import fetch_data, maybe_base64_decode
from parser import detect_protocol, extract_host
from tester import test_speed, get_nodes_by_country
from output import save_to_file

def extract_configs(data: str) -> list[str]:
    """
    Extract VPN configurations from raw text.
    Supports vless, vmess, trojan, and ss.
    """
    pattern = r"(vless://[^\s]+|vmess://[^\s]+|trojan://[^\s]+|ss://[^\s]+)"
    return re.findall(pattern, data)

async def main_async():
    print(f"[{TIMESTAMP}] Starting download and processing with country-based speed test...")

    # دریافت نودها بر اساس کشور
    country_nodes_dict = await get_nodes_by_country()

    # دیکشنری برای ذخیره کانفیگ‌ها بر اساس کشور
    categorized_per_country = {}  # {"us": {"vless": [], ...}, ...}

    # دریافت و پردازش کانفیگ‌ها از URL‌ها
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

            # اضافه کردن کانفیگ به کشورهایی که نود دارند
            for country_code in country_nodes_dict.keys():
                categorized_per_country.setdefault(
                    country_code,
                    {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
                )
                categorized_per_country[country_code][proto].append((line, host))

    # محدودیت همزمانی تست‌ها
    sem = asyncio.Semaphore(50)

    async def test_line_country(line_host, country_code):
        """
        Test latency for a single config line using nodes of the specific country.
        """
        line, host = line_host
        nodes = country_nodes_dict.get(country_code, [])
        if not nodes:
            return float('inf'), line, country_code
        async with sem:
            latency = await test_speed(host, country_nodes=nodes)
            return latency, line, country_code

    # تست سرعت و مرتب‌سازی کانفیگ‌ها
    for country_code, categorized in categorized_per_country.items():
        print(f"Processing country: {country_code}")
        all_results = []

        for proto, lines_hosts in categorized.items():
            if not lines_hosts:
                continue
            results = await asyncio.gather(*[
                test_line_country(lh, country_code) for lh in lines_hosts
            ])
            results.sort(key=lambda x: x[0])
            categorized[proto] = [line for _, line, _ in results]
            all_results.extend(results)

        all_results.sort(key=lambda x: x[0])
        sorted_lines = [line for _, line, _ in all_results]

        # ساخت فولدر کشور
        country_dir = os.path.join(OUTPUT_DIR, country_code)
        os.makedirs(country_dir, exist_ok=True)

        # ذخیره فایل‌ها
        for proto, lines in categorized.items():
            save_to_file(os.path.join(country_dir, f"{proto}.txt"), lines)
        save_to_file(os.path.join(country_dir, "all.txt"), sorted_lines)
        save_to_file(os.path.join(country_dir, "light.txt"), sorted_lines[:30])

if __name__ == "__main__":
    asyncio.run(main_async())

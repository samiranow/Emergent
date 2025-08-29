import asyncio
from pathlib import Path
from config import URLS, TIMESTAMP, OUTPUT_DIR
from fetcher import fetch_data, maybe_base64_decode
from parser import detect_protocol, extract_host
from tester import test_speed_country, get_nodes_by_country
from output import save_to_file
import re

def extract_configs(data: str) -> list[str]:
    pattern = r"(vless://[^\s]+|vmess://[^\s]+|trojan://[^\s]+|ss://[^\s]+)"
    return re.findall(pattern, data)

async def main_async():
    print(f"[{TIMESTAMP}] Starting download and processing with country-based speed test...")
    
    country_nodes = await get_nodes_by_country()
    countries = country_nodes.keys()

    # Fetch all configs
    all_configs = []
    for url in URLS:
        raw_data = fetch_data(url)
        decoded_text = maybe_base64_decode(raw_data)
        configs = extract_configs(decoded_text)
        print(f"Downloaded: {url} | Configs found: {len(configs)}")
        all_configs.extend(configs)

    sem = asyncio.Semaphore(50)

    async def test_line(line, country_code):
        async with sem:
            proto = detect_protocol(line)
            host = extract_host(line, proto)
            latency = await test_speed_country(host, country_code, country_nodes)
            return latency, line, proto

    for country_code in countries:
        print(f"Processing country: {country_code.upper()}")
        categorized = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
        all_results = []

        results = await asyncio.gather(*[test_line(line, country_code) for line in all_configs])
        results.sort(key=lambda x: x[0])
        for latency, line, proto in results:
            if latency == float('inf'):
                continue
            categorized[proto].append(line)
            all_results.append((latency, line, proto))

        all_results.sort(key=lambda x: x[0])
        sorted_lines = [line for _, line, _ in all_results]

        # Country folder
        country_dir = Path(OUTPUT_DIR) / country_code.upper()
        country_dir.mkdir(parents=True, exist_ok=True)

        # Save files
        for proto, lines in categorized.items():
            save_to_file(str(country_dir / f"{proto}.txt"), lines)
        save_to_file(str(country_dir / "all.txt"), sorted_lines)
        save_to_file(str(country_dir / "light.txt"), sorted_lines[:30])

if __name__ == "__main__":
    asyncio.run(main_async())

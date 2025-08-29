import asyncio
import re
from config import URLS, TIMESTAMP
from fetcher import fetch_data, maybe_base64_decode
from parser import detect_protocol, extract_host
from tester import test_speed
from output import save_to_file

async def main_async():
    print(f"[{TIMESTAMP}] Starting download and processing with speed test...")
    
def extract_configs(data: str) -> list[str]:
    pattern = r"(vless://[^\s]+|vmess://[^\s]+|trojan://[^\s]+|ss://[^\s]+)"
    return re.findall(pattern, data)
    
    categorized = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
    all_lines = []

# Fetch and decode configurations
for url in URLS:
    raw_data = fetch_data(url)
    
    # Decode Base64 اگر لازم بود
    decoded_text = maybe_base64_decode(raw_data)
    
    # استخراج همه کانفیگ‌ها از متن
    configs = extract_configs(decoded_text)
    
    print(f"Downloaded: {url} | Configs found: {len(configs)}")
    
    for line in configs:
        proto = detect_protocol(line)
        categorized[proto].append(line)
        all_lines.append(line)
    

    # Speed test
    sem = asyncio.Semaphore(100)

    async def test_line(line, proto):
        async with sem:
            host = extract_host(line, proto)
            latency = await test_speed(host)
            return latency, line, proto

    all_results = []
    for proto, lines in categorized.items():
        if not lines:
            continue
        results = await asyncio.gather(*[test_line(line, proto) for line in lines])
        results.sort(key=lambda x: x[0])
        categorized[proto] = [line for _, line, _ in results]
        all_results.extend(results)

    all_results.sort(key=lambda x: x[0])
    sorted_lines = [line for _, line, _ in all_results]

    # Save files
    for proto, lines in categorized.items():
        save_to_file(f"{proto}.txt", lines)
    save_to_file("all.txt", sorted_lines)
    save_to_file("light.txt", sorted_lines[:30])

if __name__ == "__main__":
    asyncio.run(main_async())

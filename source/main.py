import asyncio
from config import URLS, TIMESTAMP
from fetcher import fetch_data, maybe_base64_decode
from parser import detect_protocol, extract_host
from tester import test_speed
from output import save_to_file

async def main_async():
    print(f"[{TIMESTAMP}] Starting download and processing with speed test...")

    categorized = {"vless": [], "vmess": [], "shadowsocks": [], "trojan": [], "unknown": []}
    all_lines = []

    # Fetch and decode configurations
    for url in URLS:
        data = fetch_data(url)
        lines = [line.strip() for line in data.splitlines() if line.strip()]
        decoded = [maybe_base64_decode(line) for line in lines]
        print(f"Downloaded: {url} | Lines: {len(decoded)}")
        for line in decoded:
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

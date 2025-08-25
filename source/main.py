import asyncio
import aiohttp
import base64
import re
from urllib.parse import urlparse
import json
import time

CHECK_HOST_API_BASE = "https://check-host.net/check-ping"

async def get_ping_result_from_checkhost(session, link, country_code="ir"):
    try:
        # استخراج آدرس سرور از لینک VPN
        parsed = urlparse(link)
        hostname = parsed.hostname

        if not hostname:
            return float('inf')  # اگر نتوانست hostname پیدا کند

        # ارسال درخواست پینگ به API
        params = {"host": hostname}
        async with session.get(CHECK_HOST_API_BASE, params=params) as resp:
            data = await resp.json()
            request_id = data.get("request_id")
            if not request_id:
                print(f"[ERROR] No request_id for {hostname}")
                return float('inf')

        # منتظر ماندن برای نتیجه (API async)
        await asyncio.sleep(2)  # کمی صبر برای پردازش

        # گرفتن نتیجه پینگ
        result_url = f"https://check-host.net/check-result/{request_id}"
        async with session.get(result_url) as resp:
            result_data = await resp.json()

        if not result_data:
            print(f"[WARNING] No result for {hostname}")
            return float('inf')

        # پیدا کردن نودهای ایران
        latencies = []
        for node, checks in result_data.items():
            if node.startswith(country_code):  # فقط IR
                for check in checks:
                    if check and isinstance(check, list) and check[0] is not None:
                        latencies.append(check[0])

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            print(f"[PING] {hostname} -> {avg_latency:.2f} ms (IR nodes)")
            return avg_latency
        else:
            print(f"[PING] {hostname} -> No IR nodes found")
            return float('inf')

    except Exception as e:
        print(f"[ERROR] {hostname}: {e}")
        return float('inf')


async def process_links(links, country_code="ir"):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for link in links:
            tasks.append(get_ping_result_from_checkhost(session, link, country_code))
            await asyncio.sleep(3)  # برای جلوگیری از بلاک شدن API

        results = await asyncio.gather(*tasks)

    # ترکیب لینک با پینگ و مرتب‌سازی
    combined = list(zip(links, results))
    combined.sort(key=lambda x: x[1])

    print("\n--- Sorted by IR Ping ---")
    for link, latency in combined:
        status = f"{latency:.2f} ms" if latency != float('inf') else "No Data"
        print(f"{status} | {link}")

    return combined


if __name__ == "__main__":
    # تست با چند لینک VPN
    sample_links = [
        "vmess://Y29uZmlnMQ==",
        "vless://example.com:443",
        "trojan://node.ir:443"
    ]
    asyncio.run(process_links(sample_links, "ir"))

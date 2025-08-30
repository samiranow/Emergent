# config.py
import os
import zoneinfo
from datetime import datetime

# URLs to fetch VPN configurations from
URLS = [
    "https://raw.githubusercontent.com/HosseinKoofi/GO_V2rayCollector/main/mixed_iran.txt",
    "https://www.v2nodes.com/subscriptions/country/all/?key=769B61EA877690D",
    "https://www.v2nodes.com/subscriptions/country/de/?key=769B61EA877690D",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
    "https://raw.githubusercontent.com/hamedp-71/Sub_Checker_Creator/refs/heads/main/final.txt",
    "https://gh-proxy.com/raw.githubusercontent.com/ssrsub/ssr/master/v2ray",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/refs/heads/main/subscriptions/v2ray/super-sub.txt",
    "https://raw.githubusercontent.com/aqayerez/MatnOfficial-VPN/refs/heads/main/MatnOfficial",
]

# Directory where processed configuration files will be saved
OUTPUT_DIR = "configs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# User-Agent string to mimic a real Chrome browser
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

# Timezone for timestamp
ZONE = zoneinfo.ZoneInfo("Asia/Tehran")
TIMESTAMP = datetime.now(ZONE).strftime("%Y-%m-%d %H:%M:%S")

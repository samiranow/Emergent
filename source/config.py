# config.py
import os
import zoneinfo
from datetime import datetime

# URLs to fetch VPN configurations from
URLS = [
    "https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet.txt",
    "https://www.v2nodes.com/subscriptions/country/de/?key=769B61EA877690D",
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

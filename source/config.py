import os
import zoneinfo
from datetime import datetime

# URLs to fetch VPN configurations from
URLS = [
    "https://raw.githubusercontent.com/HosseinKoofi/GO_V2rayCollector/main/mixed_iran.txt",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
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

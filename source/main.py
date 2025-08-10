import os
import requests
import urllib.parse
import urllib3
import re
from datetime import datetime
import zoneinfo

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# List of configuration URLs
URLS = [
    "https://raw.githubusercontent.com/MahsaNetConfigTopic/config/refs/heads/main/xray_final.txt",
    "https://istanbulsydneyhotel.com/blogs/site/sni.php?security=reality",
    "https://istanbulsydneyhotel.com/blogs/site/sni.php",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt",
    # ... Add more URLs here ...
]

# Folder for saving configuration files
OUTPUT_DIR = "configs"

# Create folder if it does not exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Get local time in Europe/Moscow timezone for commits
zone = zoneinfo.ZoneInfo("Europe/Moscow")
now = datetime.now(zone)
timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

# Chrome browser User-Agent
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

def fetch_data(url: str, timeout=10):
    """Download configuration data from a given URL."""
    headers = {"User-Agent": CHROME_UA}
    try:
        r = requests.get(url, timeout=timeout, headers=headers, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"⚠️ Error downloading {url}: {e}")
        return ""

def detect_protocol(line: str) -> str:
    """Detect the VPN protocol type from a config line."""
    line = line.strip()
    if line.startswith("vless://"):
        return "vless"
    elif line.startswith("vmess://"):
        return "vmess"
    elif line.startswith("ss://"):
        return "shadowsocks"
    else:
        return "unknown"

def main():
    print(f"[{timestamp}] Starting configuration download and processing...")
    
    all_lines = []
    categorized = {
        "vless": [],
        "vmess": [],
        "shadowsocks": [],
        "unknown": []
    }

    # Download and categorize configs
    for url in URLS:
        data = fetch_data(url)
        lines = [line for line in data.splitlines() if line.strip()]
        print(f"Downloaded: {url} | Lines: {len(lines)}")

        for line in lines:
            proto = detect_protocol(line)
            categorized[proto].append(line)
            all_lines.append(line)

    # Save categorized configs to separate files
    for proto, lines in categorized.items():
        path = os.path.join(OUTPUT_DIR, f"{proto}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Saved: {path} | Lines: {len(lines)}")

    # Save all configs into one file
    all_path = os.path.join(OUTPUT_DIR, "all.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines))
    print(f"Saved: {all_path} | Lines: {len(all_lines)}")

    # Save a light version with the first 30 configs
    light_path = os.path.join(OUTPUT_DIR, "light.txt")
    with open(light_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines[:30]))
    print(f"Saved Light version with {min(len(all_lines), 30)} configs")

if __name__ == "__main__":
    main()

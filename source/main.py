import os
import re
import json
import socket
import random
import asyncio
import logging
import base64
import requests
import httpx
import urllib3
import zoneinfo

from datetime import datetime

# ──────────────── Configuration ────────────────
URLS = [
    "https://www.v2nodes.com/subscriptions/country/de/?key=769B61EA877690D",
]

OUTPUT_DIR = "configs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)

# disable warnings for insecure HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

ZONE = zoneinfo.ZoneInfo("Asia/Tehran")

# ──────────────── Helpers: Base64, Port Strip & Geolocation Cache ────────────────
geo_cache: dict[str, str] = {}

def b64_decode(s: str) -> str:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(s + pad).decode(errors="ignore")

def b64_encode(s: str) -> str:
    return base64.b64encode(s.encode()).decode()

def strip_port(host: str) -> str:
    return host.split(":", 1)[0]

def country_flag(code: str) -> str:
    if not code:
        return "🏳️"
    c = code.strip().upper()
    if c == "UNKNOWN" or len(c) != 2 or not c.isalpha():
        return "🏳️"
    return chr(ord(c[0]) + 127397) + chr(ord(c[1]) + 127397)

def get_country_by_ip(ip: str) -> str:
    if ip in geo_cache:
        return geo_cache[ip]
    try:
        r = requests.get(f"https://ipwhois.app/json/{ip}", timeout=5)
        if r.status_code == 200:
            code = r.json().get("country_code", "unknown").lower()
            geo_cache[ip] = code
            return code
    except Except

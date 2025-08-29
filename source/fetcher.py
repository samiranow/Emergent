import requests
import base64
import re
import urllib3
from config import CHROME_UA

# Disable warnings for insecure HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_data(url: str, timeout=10) -> str:
    """
    Fetch text content from a given URL using a custom User-Agent header.
    Returns the content as a string or an empty string on failure.
    """
    headers = {"User-Agent": CHROME_UA}
    try:
        response = requests.get(url, timeout=timeout, headers=headers, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"⚠️ Error downloading {url}: {e}")
        return ""

def maybe_base64_decode(s: str) -> str:
    """
    Attempt to decode a string from Base64.
    Returns decoded string if it looks like a valid config, otherwise returns the original string.
    """
    s = s.strip()
    try:
        # padding
        padded = s + "=" * ((4 - len(s) % 4) % 4)
        decoded_bytes = base64.b64decode(padded, validate=True)
        decoded_str = decoded_bytes.decode(errors="ignore").strip()
        # check if it contains at least one config protocol keyword
        if any(proto in decoded_str for proto in ["vless://", "vmess://", "trojan://", "ss://"]):
            return decoded_str
        return s
    except Exception:
        return s

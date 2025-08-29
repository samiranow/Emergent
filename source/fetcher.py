import requests
import base64
import urllib3
from config import CHROME_UA

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_data(url: str, timeout=10) -> str:
    headers = {"User-Agent": CHROME_UA}
    try:
        response = requests.get(url, timeout=timeout, headers=headers, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"⚠️ Error downloading {url}: {e}")
        return ""

def maybe_base64_decode(s: str) -> str:
    s = s.strip()
    try:
        padded = s + "=" * ((4 - len(s) % 4) % 4)
        decoded_bytes = base64.b64decode(padded, validate=True)
        decoded_str = decoded_bytes.decode(errors="ignore").strip()
        if any(proto in decoded_str for proto in ["vless://", "vmess://", "trojan://", "ss://"]):
            return decoded_str
        return s
    except Exception:
        return s

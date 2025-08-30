# parser.py
import base64
import json
import re

def detect_protocol(line: str) -> str:
    line = line.strip().lower()
    if line.startswith("vless://"):
        return "vless"
    elif line.startswith("vmess://"):
        return "vmess"
    elif line.startswith("ss://"):
        return "shadowsocks"
    elif line.startswith("trojan://"):
        return "trojan"
    return "unknown"

def extract_host(line: str, proto: str) -> str:
    try:
        if proto == "vmess":
            b64_part = line[8:]
            padded = b64_part + "=" * ((4 - len(b64_part) % 4) % 4)
            decoded = base64.b64decode(padded).decode(errors="ignore")
            data = json.loads(decoded)
            return data.get("add", "")
        elif proto == "vless":
            m = re.search(r"vless://[^@]+@([^:/]+)", line)
            if m:
                return m.group(1)
        elif proto == "shadowsocks":
            m = re.search(r"ss://(?:[^@]+@)?([^:/]+)", line)
            if m:
                return m.group(1)
        elif proto == "trojan":
            m = re.search(r"trojan://[^@]+@([^:/?#]+)", line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""

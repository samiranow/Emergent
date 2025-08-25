<h1>ConfigForge 🚀</h1>
<p>
  <b>VPN Config Collector & Organizer</b>
</p>

## 📂 Available Subscription Files

| File            | Description                   | Direct Link                                                                                                          |
| -------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **all.txt**    | All combined configs         | [Link Sub](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/all.txt)                 |
| **light.txt**  | Lightweight top 30 configs   | [Link Sub](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/light.txt)             |
| **vless.txt**  | VLESS protocol configs       | [Link Sub](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/vless.txt)             |
| **vmess.txt**  | VMess protocol configs       | [Link Sub](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/vmess.txt)             |
| **shadowsocks.txt** | Shadowsocks configs        | [Link Sub](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/shadowsocks.txt) |
| **trojan.txt** | Trojan configs               | [Link Sub](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/trojan.txt)           |
| **unknown.txt**| Unknown or unsupported configs| [Link Sub](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/unknown.txt)         |

✅ Files are updated automatically via **GitHub Actions** every 6 hours.

---

**Features:**
- Download VPN config lists from multiple sources
- Parse and categorize configs by protocol
- Generate aggregated and lightweight subscription files
- Auto commit and push updates to GitHub
- Easy to customize and extend

**Usage:**
1. Clone this repository:  
   `git clone https://github.com/ShatakVPN/ConfigForge.git`  
   `cd ConfigForge`
2. Set your GitHub Personal Access Token (PAT) as a secret `PAT_TOKEN` in GitHub Actions for push access.
3. Install dependencies:  
   `pip install -r source/requirements.txt`
4. Run the main script:  
   `python source/main.py`
5. Or use the included GitHub Actions workflow for scheduled updates.

**Requirements:**
- Python 3.1+
- `requests` package (from requirements.txt)

**License:** GPL-3.0 License
</details>

---
<p align="center">
  <img src="https://img.shields.io/github/stars/ShatakVPN/ConfigForge?style=for-the-badge&color=yellow" alt="Stars" />
  <img src="https://img.shields.io/github/forks/ShatakVPN/ConfigForge?style=for-the-badge&color=blue" alt="Forks" />
  <img src="https://img.shields.io/github/last-commit/ShatakVPN/ConfigForge?style=for-the-badge&color=brightgreen" alt="Last Commit" />
  <img src="https://img.shields.io/github/license/ShatakVPN/ConfigForge?style=for-the-badge&color=orange" alt="License" />
  <img src="https://img.shields.io/github/languages/top/ShatakVPN/ConfigForge?style=for-the-badge&color=purple" alt="Top Language" />
</p>

---

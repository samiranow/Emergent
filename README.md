<h1>ConfigForge V2Ray 🚀</h1>
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

✅ Files are updated automatically via **GitHub Actions** every 30 minutes.

---

## Features:
- Download VPN config lists from multiple sources
- Parse and categorize configs by protocol
- Generate aggregated and lightweight subscription files
- Auto commit and push updates to GitHub
- Easy to customize and extend

## How to Use

**✅ Option 1: Run Locally**

Clone the repository:
```bash
git clone https://github.com/ShatakVPN/ConfigForge.git
cd ConfigForge
```

Install dependencies:
```bash
pip install -r source/requirements.txt
```

Run the main script:
```bash
python source/main.py
```

---

**✅ Option 2: Run Automatically on GitHub (No Server Needed)**

You can **fork this repository** and let **GitHub Actions** handle everything for you!  

1. **Fork this repository** to your own GitHub account.  
2. **Create a Personal Access Token (PAT)** and add it as a secret:  
   - Go to **Settings → Secrets → Actions**  
   - Add a new secret named **`PAT_TOKEN`** with your token value.  
3. **Enable the included workflow**:
```bash
.github/workflows/update.yml
```
4. Done! The workflow will automatically:  
   - Download and update VPN configs  
   - Commit changes to your forked repo  
   - Run on a schedule — completely serverless!  

---

<p align="center">
  <img src="https://img.shields.io/github/stars/ShatakVPN/ConfigForge?style=for-the-badge&color=yellow" alt="Stars" />
  <img src="https://img.shields.io/github/forks/ShatakVPN/ConfigForge?style=for-the-badge&color=blue" alt="Forks" />
  <img src="https://img.shields.io/github/last-commit/ShatakVPN/ConfigForge?style=for-the-badge&color=brightgreen" alt="Last Commit" />
  <img src="https://img.shields.io/github/license/ShatakVPN/ConfigForge?style=for-the-badge&color=orange" alt="License" />
  <img src="https://img.shields.io/github/languages/top/ShatakVPN/ConfigForge?style=for-the-badge&color=purple" alt="Top Language" />
</p>

---

**License:** GPL-3.0 License


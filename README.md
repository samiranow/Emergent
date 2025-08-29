
# ConfigForge V2Ray 🌍

**ConfigForge V2Ray** is an advanced open-source platform that aggregates and optimizes V2Ray VPN configurations from multiple sources.  
It automatically detects your country and suggests the **fastest configurations**, verified through **Check-Host API latency testing**, to ensure the best connection speed and reliability.

---

## 🌐 Access the Web Interface
For the easiest experience, use our **modern multi-language web interface**:  
➡️ **[https://shatakvpn.github.io/ConfigForge-V2Ray/](https://shatakvpn.github.io/ConfigForge-V2Ray/)**

---

## 🚀 Why ConfigForge?
Unlike basic config repositories, **ConfigForge V2Ray**:
- ✅ Continuously fetches configs from **multiple sources**
- ✅ **Tests latency for each country** using [Check-Host API](https://check-host.net/)
- ✅ Suggests **the fastest servers** for your location
- ✅ Provides **aggregated, lightweight, and categorized configs** (VLESS, VMess, Shadowsocks, Trojan)
- ✅ Runs **automatically with GitHub Actions** – no server required!

---

## ✨ Features
- 🌍 **Country-based selection** – Automatically detect your location or choose manually  
- 🔍 **Latency-tested recommendations** – Get only the **fastest working configs** for your country  
- 🌐 **Multi-language support** – Dynamic translation of the entire interface  
- 📂 **Subscription files available**:
  - `all.txt` → Full list of configs
  - `light.txt` → Top 30 fastest configs
  - Individual files for each protocol (VLESS, VMess, Shadowsocks, Trojan)
- 🔄 **Auto-updates via GitHub Actions**
- ⚡ **Optimized for speed and simplicity**
- 🛠 **Easy to extend** for new protocols or sources

---

## ✅ Additional Features:
- Download VPN config lists from multiple sources  
- Parse and categorize configs by protocol  
- Generate aggregated and lightweight subscription files  
- Auto commit and push updates to GitHub  
- Fully customizable structure for advanced users  

---

## 🛠 How to Use

### ✅ Option 1: Run Locally
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

### ✅ Option 2: Run Automatically on GitHub (Serverless)
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
   - Run on a schedule — completely **serverless**!  

---

## 📂 Folder Structure
```
ConfigForge-V2Ray/
│
├── configs/
│   ├── us/
│   │   ├── all.txt
│   │   ├── light.txt
│   │   ├── vless.txt
│   │   ├── vmess.txt
│   │   ├── shadowsocks.txt
│   │   └── trojan.txt
│   ├── ir/
│   └── ...
│
└── docs/
    └── index.html  (Modern Web Interface)
```

---

## 🔗 Important Links
- **Live Website**: [https://shatakvpn.github.io/ConfigForge-V2Ray/](https://shatakvpn.github.io/ConfigForge-V2Ray/)
- **GitHub Repository**: [https://github.com/ShatakVPN/ConfigForge-V2Ray](https://github.com/ShatakVPN/ConfigForge-V2Ray)

---

<p align="center">
  <img src="https://img.shields.io/github/stars/ShatakVPN/ConfigForge?style=for-the-badge&color=yellow" alt="Stars" />
  <img src="https://img.shields.io/github/forks/ShatakVPN/ConfigForge?style=for-the-badge&color=blue" alt="Forks" />
  <img src="https://img.shields.io/github/last-commit/ShatakVPN/ConfigForge?style=for-the-badge&color=brightgreen" alt="Last Commit" />
  <img src="https://img.shields.io/github/license/ShatakVPN/ConfigForge?style=for-the-badge&color=orange" alt="License" />
  <img src="https://img.shields.io/github/languages/top/ShatakVPN/ConfigForge?style=for-the-badge&color=purple" alt="Top Language" />
</p>

---

## 📜 License
This project is licensed under the **GPL-3.0 License**.  
See the [LICENSE](LICENSE) file for details.

---

### ❤️ Built with love by [ShatakVPN](https://github.com/ShatakVPN)

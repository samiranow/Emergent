# ConfigForge 🚀

**A Powerful VPN Configuration Collector & Organizer**

<p align="center">
  <img src="https://img.shields.io/github/stars/ShatakVPN/ConfigForge?style=for-the-badge&color=yellow" alt="Stars" />
  <img src="https://img.shields.io/github/forks/ShatakVPN/ConfigForge?style=for-the-badge&color=blue" alt="Forks" />
  <img src="https://img.shields.io/github/last-commit/ShatakVPN/ConfigForge?style=for-the-badge&color=brightgreen" alt="Last Commit" />
  <img src="https://img.shields.io/github/license/ShatakVPN/ConfigForge?style=for-the-badge&color=orange" alt="License" />
  <img src="https://img.shields.io/github/languages/top/ShatakVPN/ConfigForge?style=for-the-badge&color=purple" alt="Top Language" />
</p>

---

<style>
  .tabs {
    display: flex;
    flex-wrap: wrap;
    margin-bottom: 10px;
    border-bottom: 2px solid #ddd;
  }
  .tabs label {
    padding: 10px 20px;
    cursor: pointer;
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-bottom: none;
    margin-right: 5px;
    font-weight: bold;
  }
  .tabs label:hover {
    background: #eaeaea;
  }
  .tabs input {
    display: none;
  }
  .tab-content {
    display: none;
    padding: 20px;
    border: 1px solid #ddd;
    background: #fff;
  }
  .tabs input:checked + label {
    background: #fff;
    border-bottom: 1px solid #fff;
  }
  .tabs input:checked + label + .tab-content {
    display: block;
  }
</style>

<div class="tabs">
  <input type="radio" id="tab-english" name="tabs" checked>
  <label for="tab-english">English</label>
  <div class="tab-content">
    ## Overview

    ConfigForge is a versatile and robust tool designed for downloading, parsing, organizing, and managing VPN configurations such as **VLESS**, **VMess**, **Shadowsocks**, and **Trojan**. With its automated features, it ensures your VPN configurations are always up-to-date with minimal effort.

    ## Features

    - **Multi-source Downloading**: Automatically fetch VPN configuration lists from multiple sources.
    - **Protocol-based Categorization**: Organize configurations by protocol (VLESS, VMess, Shadowsocks, Trojan, etc.).
    - **Subscription File Generation**:
      - Aggregate configurations into a single file.
      - Generate lightweight top-tier configuration files for quick use.
    - **Automation**:
      - Auto-commit and push updates to GitHub using GitHub Actions.
    - **Customization**:
      - Highly customizable and extendable for different use cases.

    ## Configuration Files

    | Name              | Description                | Link                                                                                                                |
    | ----------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------- |
    | **All**             | Combined configurations       | [all.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/all.txt)                 |
    | **Light**           | Top 30 lightweight configurations | [light.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/light.txt)             |
    | **VLESS**           | VLESS protocol configurations     | [vless.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/vless.txt)             |
    | **VMess**           | VMess protocol configurations     | [vmess.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/vmess.txt)             |
    | **Shadowsocks**     | Shadowsocks configurations        | [shadowsocks.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/shadowsocks.txt) |
    | **Trojan**          | Trojan protocol configurations             | [trojan.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/trojan.txt)           |
    | **Unknown**         | Other or unidentified configurations   | [unknown.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/unknown.txt)         |

    ## Getting Started

    1. **Clone the Repository**:
       ```bash
       git clone https://github.com/ShatakVPN/ConfigForge.git
       cd ConfigForge
       ```

    2. **Install Dependencies**:
       ```bash
       pip install -r source/requirements.txt
       ```

    3. **Run the Main Script**:
       ```bash
       python source/main.py
       ```
  </div>

  <input type="radio" id="tab-persian" name="tabs">
  <label for="tab-persian">فارسی</label>
  <div class="tab-content" dir="rtl" align="right">
    ## معرفی

    **ConfigForge** یک ابزار قدرتمند است که برای دانلود، تجزیه، سازماندهی و مدیریت تنظیمات وی‌پی‌ان‌هایی مانند **VLESS**، **VMess**، **Shadowsocks** و **Trojan** طراحی شده است. این ابزار به صورت خودکار به‌روزرسانی‌ها را انجام می‌دهد و تجربه‌ای ساده و سریع را ارائه می‌دهد.

    ## ویژگی‌ها

    - **دانلود از منابع متعدد**: به‌صورت خودکار لیست‌های تنظیمات VPN را از منابع مختلف دریافت می‌کند.
    - **دسته‌بندی بر اساس پروتکل**: تنظیمات را بر اساس پروتکل (VLESS، VMess، Shadowsocks و Trojan) سازماندهی می‌کند.
    - **ایجاد فایل اشتراک**:
      - تجمع تنظیمات در یک فایل واحد.
      - تولید فایل‌های سبک و با اولویت بالا برای استفاده سریع.
    - **خودکارسازی**:
      - به‌روزرسانی خودکار و ارسال تغییرات به GitHub با استفاده از GitHub Actions.
    - **قابلیت شخصی‌سازی**:
      - کاملاً قابل تنظیم و گسترش برای استفاده‌های مختلف.

    ## فایل‌های تنظیمات

    | نام              | توضیحات                | لینک                                                                                                                |
    | ----------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------- |
    | **All**             | ترکیب همه تنظیمات       | [all.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/all.txt)                 |
    | **Light**           | 30 تنظیم برتر و سبک | [light.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/light.txt)             |
    | **VLESS**           | تنظیمات پروتکل VLESS     | [vless.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/vless.txt)             |
    | **VMess**           | تنظیمات پروتکل VMess     | [vmess.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/vmess.txt)             |
    | **Shadowsocks**     | تنظیمات Shadowsocks        | [shadowsocks.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/shadowsocks.txt) |
    | **Trojan**          | تنظیمات پروتکل Trojan             | [trojan.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/trojan.txt)           |
    | **Unknown**         | سایر تنظیمات یا نامشخص   | [unknown.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/unknown.txt)         |

    ## شروع به کار

    1. **کلون کردن مخزن**:
       ```bash
       git clone https://github.com/ShatakVPN/ConfigForge.git
       cd ConfigForge
       ```

    2. **نصب وابستگی‌ها**:
       ```bash
       pip install -r source/requirements.txt
       ```

    3. **اجرای اسکریپت اصلی**:
       ```bash
       python source/main.py
       ```
  </div>
</div>

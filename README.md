
markdown
Copy
Edit
# ConfigForge - VPN Config Collector

[English](#english) | [فارسی](#%D9%81%D8%A7%D8%B1%D8%B3%DB%8C) | [中文](#%E4%B8%AD%E6%96%87)

---

## English

A powerful tool to automatically download, parse, and organize VPN configurations (VLESS, VMess, Shadowsocks, etc.) and push updates to GitHub.

### Features

- Download VPN config lists from multiple sources  
- Parse and categorize configs by protocol  
- Generate aggregated and lightweight subscription files  
- Auto commit and push updates to GitHub  
- Easy to customize and extend  

### Usage

1. Clone this repository:  
   ```bash
   git clone https://github.com/ShatakVPN/ConfigForge.git
   cd ConfigForge
Set your GitHub Personal Access Token (PAT) as a secret PAT_TOKEN in GitHub Actions for push access.

Install dependencies:

bash
Copy
Edit
pip install -r source/requirements.txt
Run the main script:

bash
Copy
Edit
python source/main.py
Or use the included GitHub Actions workflow for scheduled updates.

Requirements
Python 3.8+

requests package (from requirements.txt)

License
MIT License

فارسی
ابزاری قدرتمند برای دانلود، پردازش و دسته‌بندی خودکار کانفیگ‌های VPN (VLESS، VMess، Shadowsocks و ...) و به‌روزرسانی خودکار مخزن گیت‌هاب.

ویژگی‌ها
دانلود لیست کانفیگ از منابع مختلف

دسته‌بندی کانفیگ‌ها بر اساس پروتکل

تولید فایل‌های اشتراک کلی و سبک

ارسال خودکار تغییرات به گیت‌هاب

قابل سفارشی‌سازی و توسعه آسان

نحوه استفاده
کلون کردن مخزن:

bash
Copy
Edit
git clone https://github.com/ShatakVPN/ConfigForge.git
cd ConfigForge
تنظیم توکن دسترسی شخصی گیت‌هاب (PAT) به عنوان متغیر مخفی PAT_TOKEN در GitHub Actions جهت دسترسی به ارسال تغییرات.

نصب وابستگی‌ها:

bash
Copy
Edit
pip install -r source/requirements.txt
اجرای اسکریپت اصلی:

bash
Copy
Edit
python source/main.py
یا استفاده از Workflow گیت‌هاب برای به‌روزرسانی زمان‌بندی شده.

پیش‌نیازها
پایتون نسخه ۳.۸ و بالاتر

بسته requests (از فایل requirements.txt)

مجوز
مجوز MIT

中文
一个强大的工具，用于自动下载、解析和整理VPN配置（VLESS、VMess、Shadowsocks等），并自动推送更新到GitHub。

功能
从多个来源下载VPN配置列表

按协议解析和分类配置

生成汇总和轻量级订阅文件

自动提交并推送更新到GitHub

易于定制和扩展

使用方法
克隆仓库：

bash
Copy
Edit
git clone https://github.com/ShatakVPN/ConfigForge.git
cd ConfigForge
在GitHub Actions中设置个人访问令牌（PAT）为PAT_TOKEN秘密变量，以获得推送权限。

安装依赖：

bash
Copy
Edit
pip install -r source/requirements.txt
运行主脚本：

bash
Copy
Edit
python source/main.py
或使用内置的GitHub Actions工作流进行定时更新。

需求
Python 3.8及以上版本

requests包（通过requirements.txt安装）

许可
MIT 许可

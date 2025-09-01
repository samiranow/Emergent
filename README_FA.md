# 🌍 ConfigForge V2Ray 

یک پلتفرم متن‌باز برای جمع‌آوری و بهینه‌سازی کانفیگ‌های V2Ray از چندین منبع است.
این ابزار به‌طور خودکار کشور شما را تشخیص می‌دهد و با استفاده از **آزمایش تأخیر (Latency) از طریق Check-Host** سریع‌ترین کانفیگ‌ها را پیشنهاد می‌کند تا به بهترین سرعت و پایداری برسید.

---

## 🌐 دسترسی به رابط وب

### لینک‌های سریع گلوبالِ ایران (Direct Links)
این URLها مربوط به پوشه‌ی **ایران (`configs/ir/`)** هستند و در اکثر کلاینت‌های سازگار با V2Ray (مثل v2rayNG، V2RayN، Shadowrocket و …) قابل استفاده‌اند.  
روی لینک کلیک کنید و URL را در بخش **Subscriptions** کلاینت خود پیست کنید.

| فایل | توضیح | لینک مستقیم |
|---|---|---|
| `all.txt` | فهرست کامل ایران (مرتب‌شده بر اساس میانگین تأخیر) | [Open](https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/all.txt) · [Mirror](https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/all.txt) |
| `light.txt` | ۳۰ کانفیگ سریع‌تر ایران | [Open](https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/light.txt) · [Mirror](https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/light.txt) |
| `vless.txt` | فقط VLESS (ایران) | [Open](https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/vless.txt) · [Mirror](https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/vless.txt) |
| `vmess.txt` | فقط VMess (ایران) | [Open](https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/vmess.txt) · [Mirror](https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/vmess.txt) |
| `shadowsocks.txt` | فقط Shadowsocks (ایران) | [Open](https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/shadowsocks.txt) · [Mirror](https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/shadowsocks.txt) |
| `trojan.txt` | فقط Trojan (ایران) | [Open](https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/trojan.txt) · [Mirror](https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/trojan.txt) |
| `unknown.txt` | سایر/نامشخص (ایران) | [Open](https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/unknown.txt) · [Mirror](https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/unknown.txt) |

<details>
<summary><strong>نمایش URLهای خام (Copy/Paste)</strong></summary>

```
https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/all.txt
https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/light.txt
https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/vless.txt
https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/vmess.txt
https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/shadowsocks.txt
https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/trojan.txt
https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ir/unknown.txt
```

_میرورها (jsDelivr):_

```
https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/all.txt
https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/light.txt
https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/vless.txt
https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/vmess.txt
https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/shadowsocks.txt
https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/trojan.txt
https://cdn.jsdelivr.net/gh/ShatakVPN/ConfigForge-V2Ray@main/configs/ir/unknown.txt
```
</details>

برای تجربه‌ی سریع و چندزبانه از **رابط وب مدرن** استفاده کنید:  
➡️ **[https://shatakvpn.github.io/ConfigForge-V2Ray/](https://shatakvpn.github.io/ConfigForge-V2Ray/)**

---

## 🚀 چرا ConfigForge؟
برخلاف مخازن ساده‌ی کانفیگ، **ConfigForge V2Ray**:
- ✅ به‌صورت مداوم از **چندین منبع** کانفیگ دریافت می‌کند
- ✅ برای هر کشور **تأخیر را با Check-Host** می‌سنجد
- ✅ **سریع‌ترین سرورها** را برای موقعیت شما پیشنهاد می‌کند
- ✅ **فایل‌های تجمیعی و سبک** و همچنین دسته‌بندی بر اساس پروتکل (VLESS, VMess, Shadowsocks, Trojan) را ارائه می‌دهد
- ✅ به‌طور **خودکار با GitHub Actions** اجرا می‌شود — بدون نیاز به سرور

---

## ✨ امکانات
- 🌍 **انتخاب بر اساس کشور** — تشخیص خودکار کشور یا انتخاب دستی  
- 🔍 **پیشنهادهای تست‌شده با تأخیر کم** — فقط **سریع‌ترین کانفیگ‌های کارکرده** را دریافت کنید  
- 🌐 **پشتیبانی چندزبانه** — ترجمه‌ی پویا برای کل رابط  
- 📂 **فایل‌های اشتراک موجود**:
  - `all.txt` → فهرست کامل
  - `light.txt` → ۳۰ مورد سریع‌تر
  - فایل‌های مجزا برای هر پروتکل (VLESS, VMess, Shadowsocks, Trojan)
- 🔄 **به‌روزرسانی خودکار با GitHub Actions**
- ⚡ **بهینه برای سرعت و سادگی**
- 🛠 **قابل‌گسترش برای منابع/پروتکل‌های جدید**

---

## ✅ قابلیت‌های بیشتر
- دانلود لیست کانفیگ از چند منبع  
- پارس و دسته‌بندی بر اساس پروتکل  
- تولید فایل‌های تجمیعی و سبک  
- کامیت و پوش خودکار به گیت‌هاب  
- ساختار قابل‌سفارشی‌سازی برای کاربران حرفه‌ای  

---

## 🛠 روش استفاده

### ✅ روش ۱: اجرای محلی
مخزن را کلون کنید:
```bash
git clone https://github.com/ShatakVPN/ConfigForge.git
cd ConfigForge
```

پیش‌نیازها را نصب کنید:
```bash
pip install -r source/requirements.txt
```

اسکریپت اصلی را اجرا کنید:
```bash
python source/main.py
```

---

### ✅ روش ۲: اجرای خودکار روی GitHub (Serverless)
می‌توانید این مخزن را **Fork** کنید و اجازه دهید **GitHub Actions** همه‌چیز را مدیریت کند!

1. مخزن را به حساب خود **Fork** کنید.  
2. یک **Personal Access Token (PAT)** بسازید و به‌عنوان Secret اضافه کنید:  
   - مسیر: **Settings → Secrets → Actions**  
   - Secret جدید با نام **`PAT_TOKEN`** اضافه کنید.  
3. ورک‌فلو موجود را فعال کنید:
```bash
.github/workflows/update.yml
```
4. تمام! ورک‌فلو به‌صورت خودکار:  
   - کانفیگ‌ها را دانلود و به‌روزرسانی می‌کند  
   - تغییرات را کامیت و پوش می‌کند  
   - طبق زمان‌بندی اجرا می‌شود — کاملاً **بدون سرور**!  

---

<p align="center">
  <img src="https://img.shields.io/github/stars/ShatakVPN/ConfigForge?style=for-the-badge&color=yellow" alt="Stars" />
  <img src="https://img.shields.io/github/forks/ShatakVPN/ConfigForge?style=for-the-badge&color=blue" alt="Forks" />
  <img src="https://img.shields.io/github/last-commit/ShatakVPN/ConfigForge?style=for-the-badge&color=brightgreen" alt="Last Commit" />
  <img src="https://img.shields.io/github/license/ShatakVPN/ConfigForge?style=for-the-badge&color=orange" alt="License" />
  <img src="https://img.shields.io/github/languages/top/ShatakVPN/ConfigForge?style=for-the-badge&color=purple" alt="Top Language" />
</p>

---
این پروژه تحت **GPL-3.0 License** منتشر شده است.  

### ❤️ ساخته‌شده با عشق توسط [ShatakVPN](https://github.com/ShatakVPN)

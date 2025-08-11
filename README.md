<h1>ConfigForge 🚀</h1>
<p><b>Powerful VPN Config Collector & Organizer</b></p>

<p align="center">
  <img src="https://img.shields.io/github/stars/ShatakVPN/ConfigForge?style=for-the-badge&color=yellow" alt="Stars" />
  <img src="https://img.shields.io/github/forks/ShatakVPN/ConfigForge?style=for-the-badge&color=blue" alt="Forks" />
  <img src="https://img.shields.io/github/last-commit/ShatakVPN/ConfigForge?style=for-the-badge&color=brightgreen" alt="Last Commit" />
  <img src="https://img.shields.io/github/license/ShatakVPN/ConfigForge?style=for-the-badge&color=orange" alt="License" />
  <img src="https://img.shields.io/github/languages/top/ShatakVPN/ConfigForge?style=for-the-badge&color=purple" alt="Top Language" />
</p>

| Name | Description | Link |
|------|-------------|------|
| `All` | All combined configs | [all.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/all.txt) |
| `Light` | Lightweight top 30 configs | [light.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/light.txt) |
| `Vless` | VLESS protocol configs | [vless.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/vless.txt) |
| `Vmess` | VMess protocol configs | [vmess.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/vmess.txt) |
| `Shadowsocks` | Shadowsocks configs | [shadowsocks.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/shadowsocks.txt) |
| `Trojan` | Trojan configs | [trojan.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/trojan.txt) |
| `Unknown` | Unknown or other configs | [unknown.txt](https://raw.githubusercontent.com/ShatakVPN/ConfigForge/main/configs/unknown.txt) |

---

<!-- Language Tabs -->
<div>
  <input type="radio" id="tab-en" name="lang" checked>
  <label for="tab-en">English</label>

  <input type="radio" id="tab-fa" name="lang">
  <label for="tab-fa">فارسی</label>

  <input type="radio" id="tab-zh" name="lang">
  <label for="tab-zh">中文</label>

  <input type="radio" id="tab-ru" name="lang">
  <label for="tab-ru">Русский</label>

  <input type="radio" id="tab-ar" name="lang">
  <label for="tab-ar">العربية</label>

  <!-- English -->
  <div class="tab-content" id="content-en">
    <p>A powerful tool to automatically download, parse, and organize VPN configurations (VLESS, VMess, Shadowsocks, etc.) and push updates to GitHub.</p>
    <b>Features:</b>
    <ul>
      <li>Download VPN config lists from multiple sources</li>
      <li>Parse and categorize configs by protocol</li>
      <li>Generate aggregated and lightweight subscription files</li>
      <li>Auto commit and push updates to GitHub</li>
      <li>Easy to customize and extend</li>
    </ul>
    <b>Usage:</b>
    <ol>
      <li>Clone this repository:<br>`git clone https://github.com/ShatakVPN/ConfigForge.git`<br>`cd ConfigForge`</li>
      <li>Set your GitHub Personal Access Token (PAT) as a secret <code>PAT_TOKEN</code> in GitHub Actions for push access.</li>
      <li>Install dependencies:<br>`pip install -r source/requirements.txt`</li>
      <li>Run the main script:<br>`python source/main.py`</li>
      <li>Or use the included GitHub Actions workflow for scheduled updates.</li>
    </ol>
    <b>Requirements:</b> Python 3.8+, `requests` package.<br>
    <b>License:</b> GPL-3.0 License.
  </div>

  <!-- Persian -->
  <div class="tab-content" id="content-fa">
    <p>ابزاری قدرتمند برای دانلود، پردازش و دسته‌بندی خودکار کانفیگ‌های VPN (VLESS، VMess، Shadowsocks و ...) و به‌روزرسانی خودکار مخزن گیت‌هاب.</p>
    <b>ویژگی‌ها:</b>
    <ul>
      <li>دانلود لیست کانفیگ از منابع مختلف</li>
      <li>دسته‌بندی کانفیگ‌ها بر اساس پروتکل</li>
      <li>تولید فایل‌های اشتراک کلی و سبک</li>
      <li>ارسال خودکار تغییرات به گیت‌هاب</li>
      <li>قابل سفارشی‌سازی و توسعه آسان</li>
    </ul>
    <b>نحوه استفاده:</b>
    <ol>
      <li>کلون کردن مخزن:<br>`git clone https://github.com/ShatakVPN/ConfigForge.git`<br>`cd ConfigForge`</li>
      <li>تنظیم توکن دسترسی شخصی گیت‌هاب (PAT) به عنوان متغیر مخفی <code>PAT_TOKEN</code> در GitHub Actions.</li>
      <li>نصب وابستگی‌ها:<br>`pip install -r source/requirements.txt`</li>
      <li>اجرای اسکریپت اصلی:<br>`python source/main.py`</li>
      <li>یا استفاده از Workflow گیت‌هاب برای به‌روزرسانی زمان‌بندی شده.</li>
    </ol>
    <b>پیش‌نیازها:</b> Python 3.8+، بسته `requests`.<br>
    <b>مجوز:</b> GPL-3.0.
  </div>

  <!-- Chinese -->
  <div class="tab-content" id="content-zh">
    <p>一个强大的工具，用于自动下载、解析和整理VPN配置（VLESS、VMess、Shadowsocks等），并自动推送更新到GitHub。</p>
    <b>功能:</b>
    <ul>
      <li>从多个来源下载VPN配置列表</li>
      <li>按协议解析和分类配置</li>
      <li>生成汇总和轻量级订阅文件</li>
      <li>自动提交并推送更新到GitHub</li>
      <li>易于定制和扩展</li>
    </ul>
    <b>使用方法:</b>
    <ol>
      <li>克隆仓库:<br>`git clone https://github.com/ShatakVPN/ConfigForge.git`<br>`cd ConfigForge`</li>
      <li>在GitHub Actions中设置个人访问令牌（PAT）为`PAT_TOKEN`秘密变量。</li>
      <li>安装依赖:<br>`pip install -r source/requirements.txt`</li>
      <li>运行主脚本:<br>`python source/main.py`</li>
      <li>或使用内置的GitHub Actions工作流进行定时更新。</li>
    </ol>
    <b>需求:</b> Python 3.8+，`requests`包.<br>
    <b>许可:</b> GPL-3.0.
  </div>

  <!-- Russian -->
  <div class="tab-content" id="content-ru">
    <p>Мощный инструмент для автоматической загрузки, разбора и организации VPN-конфигураций (VLESS, VMess, Shadowsocks и др.) с автоматической отправкой обновлений на GitHub.</p>
    <b>Возможности:</b>
    <ul>
      <li>Загрузка списков VPN-конфигураций из нескольких источников</li>
      <li>Парсинг и категоризация по протоколам</li>
      <li>Генерация агрегированных и облегчённых подписочных файлов</li>
      <li>Автоматические коммиты и пуш обновлений на GitHub</li>
      <li>Лёгкая настройка и расширение</li>
    </ul>
    <b>Использование:</b>
    <ol>
      <li>Клонируйте репозиторий:<br>`git clone https://github.com/ShatakVPN/ConfigForge.git`<br>`cd ConfigForge`</li>
      <li>Установите персональный токен доступа GitHub (PAT) как секрет <code>PAT_TOKEN</code> в GitHub Actions.</li>
      <li>Установите зависимости:<br>`pip install -r source/requirements.txt`</li>
      <li>Запустите основной скрипт:<br>`python source/main.py`</li>
      <li>Или используйте включённый workflow GitHub Actions для плановых обновлений.</li>
    </ol>
    <b>Требования:</b> Python 3.8+，`requests`.<br>
    <b>Лицензия:</b> GPL-3.0.
  </div>

  <!-- Arabic -->
  <div class="tab-content" id="content-ar">
    <p>أداة قوية لتحميل، وتحليل، وتنظيم إعدادات VPN (مثل VLESS وVMess وShadowsocks) تلقائياً مع دفع التحديثات إلى GitHub.</p>
    <b>الميزات:</b>
    <ul>
      <li>تحميل قوائم إعدادات VPN من مصادر متعددة</li>
      <li>تحليل وتصنيف الإعدادات حسب البروتوكول</li>
      <li>إنشاء ملفات اشتراك مجمعة وخفيفة الوزن</li>
      <li>الالتزام التلقائي ودفع التحديثات إلى GitHub</li>
      <li>سهل التخصيص والتوسيع</li>
    </ul>
    <b>الاستخدام:</b>
    <ol>
      <li>استنساخ المستودع:<br>`git clone https://github.com/ShatakVPN/ConfigForge.git`<br>`cd ConfigForge`</li>
      <li>تعيين رمز الوصول الشخصي (PAT) كسر في GitHub Actions باسم <code>PAT_TOKEN</code>.</li>
      <li>تثبيت المتطلبات:<br>`pip install -r source/requirements.txt`</li>
      <li>تشغيل السكربت الرئيسي:<br>`python source/main.py`</li>
      <li>أو استخدام سير العمل المضمّن لـ GitHub Actions للتحديثات المجدولة.</li>
    </ol>
    <b>المتطلبات:</b> Python 3.8+، حزمة `requests`.<br>
    <b>الرخصة:</b> GPL-3.0.
  </div>
</div>

<style>
  input[type="radio"] { display: none; }
  label { padding: 8px 15px; background: #ddd; cursor: pointer; margin-right: 5px; border-radius: 5px; }
  .tab-content { display: none; padding: 15px; background: #f9f9f9; border: 1px solid #ccc; margin-top: 10px; }
  #tab-en:checked ~ #content-en,
  #tab-fa:checked ~ #content-fa,
  #tab-zh:checked ~ #content-zh,
  #tab-ru:checked ~ #content-ru,
  #tab-ar:checked ~ #content-ar {
    display: block;
  }
</style>

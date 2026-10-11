<div lang="fa" dir="rtl" align="right">

# معماری و جریان داده سیستم (System Architecture) 🏛️

[English Version](Architecture.en.md) | **نسخه فارسی**

این مستند تشریح‌کننده معماری ماژولار، چرخه حیات درخواست‌ها، نحوه هماهنگی بین رابط کاربری PyQt6، موتور هوش مصنوعی Gemini 2.5 Flash و ابزارهای سیستم‌عامل در پروژه دستیار هوشمند نوا است.

---

## ۱. نمای کلی لایه‌های سیستم (Layered Architecture)

سیستم به ۴ لایه اصلی و مستقل تفکیک شده است:

```mermaid
graph TD
    subgraph UI_Layer [لایه رابط کاربری - PyQt6]
        Mascot[DesktopMascot - شکلک ۳بعدی دسکتاپ]
        Bubble[SpeechBubble - حباب گفتار شناور]
        Chat[ChatWindow - مرکز فرمان و چت شیشه‌ای]
        Settings[SettingsWindow - پنجره تنظیمات]
        Tray[SystemTray - آیکون کنار ساعت ویندوز]
    end

    subgraph Coordination_Layer [لایه هماهنگی و پس‌زمینه]
        Worker[AgentWorkerThread - ترد پس‌زمینه]
        VoiceRec[AudioRecorder - ضبط صدا از میکروفون]
        TTS[TTSEngine - گوینده صوتی SAPI]
    end

    subgraph Core_Agent_Layer [لایه هسته هوش مصنوعی]
        Engine[AgentEngine - مدیریت نشست جمینای]
        KeyMgr[KeyManager - استخر کلیدها و چرخش خودکار]
        MemMgr[MemoryManager - پایگاه حافظه بلندمدت]
        LearnEng[LearningEngine - موتور خودآموزی از خطاها]
        PersonaMgr[PersonaManager - مدیریت تم و شخصیت]
    end

    subgraph System_Tools_Layer [لایه ابزارهای سیستم‌عامل]
        Tools[PowerShell / Python / Files / Webcam / Vision / Diagnostics]
        OS[(Windows 10/11 & Hardware)]
    end

    Chat --> Worker
    Worker --> Engine
    Engine --> KeyMgr
    Engine --> MemMgr
    Engine --> LearnEng
    Engine --> PersonaMgr
    Engine --> Tools
    Tools --> OS
    Worker --> Mascot
    Worker --> Bubble
    Worker --> TTS
    VoiceRec --> Chat
```

---

## ۲. چرخه حیات ارسال پیام و فراخوانی ابزار (Interaction Flow)

هنگامی که کاربر پیامی صوتی، تصویری یا متنی ارسال می‌کند، گردش کار مطابق دیاگرام توالی زیر اجرا می‌گردد:

```mermaid
sequenceDiagram
    autonumber
    actor User as کاربر
    participant Chat as پنجره چت (ChatWindow)
    participant Worker as ترد پردازش (WorkerThread)
    participant Mascot as شکلک دسکتاپ (Mascot)
    participant Engine as موتور هوش مصنوعی (AgentEngine)
    participant Gemini as سرور Google Gemini 2.5
    participant Tools as ابزارهای سیستم (Tools)
    participant TTS as سیستم صوتی (TTSEngine)

    User->>Chat: ارسال پیام / صوت میکروفون / عکس وب‌کم
    Chat->>Mascot: تغییر وضعیت به "Thinking" (رادار چرخشی بنفش)
    Chat->>Worker: اجرای ناهمگام در پس‌زمینه (Non-blocking)
    Worker->>Engine: ارسال پیام و فایل‌های چندرسانه‌ای
    Engine->>Gemini: فراخوانی API با سابقه و ابزارها
    
    opt فراخوانی ابزار سیستمی (Function Calling)
        Gemini-->>Engine: درخواست اجرای ابزار (مثلا execute_powershell یا capture_webcam)
        Engine->>Mascot: تغییر وضعیت به "Working" (اکولایزر نارنجی/داده جریانی)
        Engine->>Tools: اجرای دستور در ویندوز با انکودینگ UTF-8
        Tools-->>Engine: بازگرداندن خروجی استاندارد
        Engine->>Gemini: ارسال نتیجه به مدل برای ادامه تحلیل
    end

    Gemini-->>Engine: پاسخ نهایی هوش مصنوعی
    Engine-->>Worker: متن نهایی پاسخ
    Worker->>Mascot: تغییر وضعیت به "Speaking" / "Success"
    Worker->>Chat: نمایش کارت پاسخ در تاریخچه چت
    Worker->>TTS: پخش صوتی پاسخ از اسپیکر
    TTS-->>User: پخش صدا (با لحن متناسب با جنسیت فعال)
```

---

## ۳. تفکیک مسئولیت‌های ماژول‌ها (Module Matrix)

- **`main.py`**: نقطه ورود برنامه، اتصال سیگنال‌های PyQt6، تنظیم موقعیت اولیه پنجره‌ها و مدیریت Tray Icon.
- **`agent/engine.py`**: مدیریت سشن چت جمینای، تلفیق پرامپت‌ها، مدیریت چرخش کلیدها و دیکشنری ابزارها.
- **`agent/tools.py`**: پیاده‌سازی امن توابع پاورشل، اجرای کد پایتون، عملیات دیسک، وب‌کم OpenCV، اسکرین‌شات Pillow و سلامت سیستم.
- **`agent/key_manager.py`**: استخر کلیدهای API، مدیریت سهمیه، نرخ مصرف و چرخش بدون فراموشی تاریخچه.
- **`agent/memory.py`**: مدیریت پایگاه دانش بلندمدت محلی در قالب JSON، جستجوی کلیدواژه‌ای و تزریق پویا به سیستم‌پرامپت.
- **`agent/learning.py`**: موتور بازتاب بر خطاهای اجرا، استخراج قوانین اصلاحی و تضمین عدم تکرار اشتباهات گذشته.
- **`agent/audio_recorder.py`**: رکورد صوت بافر بدون افت فشرده‌سازی با فرمت Wave از طریق `QMediaCaptureSession`.
- **`agent/tts.py`**: سنتز گفتار محلی با رابط `win32com` و پشتیبانی از گوینده‌های David و Zira.
- **`ui/mascot.py`**: رندر برداری سه‌بعدی بدون استفاده از تصاویر سنگین، پشتیبانی از ۴ سبک کاراکتر، شناوری و حالات حسی.
- **`ui/chat_window.py`**: مرکز کنترل شیشه‌ای دارک، چیپ‌های دسترسی سریع، ویجت‌های کارت پاسخ و ابزارهای مالتی‌مدیا.
- **`ui/settings_window.py`**: مدیریت تنظیمات کلیدها، ویرایش حافظه، پایش خودآموزی و انتخاب استایل کاراکتر.

</div>

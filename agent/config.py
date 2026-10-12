import os

DEFAULT_MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """
شما «نِکسا» (NexA / NexA AI) هستید؛ دستیار هوشمند، فوق‌العاده حرفه‌ای، پرانرژی و همه‌کاره دسکتاپ ویندوز، طراحی و توسعه یافته توسط شرکت «راهکار الکترونیک سهند» (https://irres.ir) که به صورت یک کاراکتر و همراه زنده در دسکتاپ کاربر حضور دارد.
شما با افتخار نماینده هوش و تخصص مهندسی شرکت «راهکار الکترونیک سهند» هستید و اختیارات کامل دارید تا با استفاده از ابزارهای در دسترس کارهای کاربر را مستقیماً انجام دهید.

قانون اساسی زبان:
- زبان پیش‌فرض، اصلی و همیشگی شما زبان فارسی است.
- تمام پاسخ‌ها، سلام و احوالپرسی‌ها، توضیحات و گزارش‌های شما باید بدون استثنا به زبان فارسی روان، اصیل، زیبا و صمیمی باشد (مگر اینکه خود کاربر صریحاً به زبان دیگری دستور دهد).
- کدها، نام متغیرها و دستورات ترمینال (PowerShell/Python) به زبان انگلیسی استاندارد باشند، اما تمام توضیحات و تحلیل‌های پیرامون آن‌ها به زبان فارسی ارائه شود.

دسترسی کامل به نرم‌افزارهای سیستم و اجرای دستورات:
شما دسترسی کامل به تمامی نرم‌افزارهای نصب‌شده روی سیستم عامل ویندوز دارید:
- کشف و جستجوی نرم‌افزارهای نصب‌شده (list_installed_apps)
- مشاهده پنجره‌ها و برنامه‌های در حال اجرا (list_open_windows)
- باز کردن یا فعال‌سازی فوکوس روی پنجره برنامه (launch_or_focus_app)
- ارسال کلیدهای میانبر، شورت‌کات‌ها (مانند Ctrl+S, Ctrl+C, Ctrl+V, Alt+F4, Enter, Tab) و تایپ متن فارسی و انگلیسی درون نرم‌افزارها (send_app_keys)
- کلیک ماوس در صفحه و پنجره‌ها (click_screen)
- بستن نرم‌افزارها (close_app)

وظایف و قابلیت‌های اصلی شما:
1. اجرای دستورات سیستم‌عامل و ویندوز (PowerShell و CMD)
2. نوشتن، تست و اجرای کدهای برنامه‌نویسی (پایتون، اسکریپت‌ها)
3. مدیریت فایل‌ها (خواندن، نوشتن، ایجاد پروژه، بررسی محتویات پوشه‌ها)
4. کنترل و تعامل با تمامی نرم‌افزارهای ویندوز، باز کردن، بستن و تایپ یا فشردن کلیدها در آن‌ها
5. دریافت وضعیت سیستم (CPU, RAM, حافظه دیسک، سیستم‌عامل)
6. مرور صفحات وب و استخراج اطلاعات
7. بررسی اسکرین‌شات از دسکتاپ برای مشاهده مستقیم صفحه کاربر (در صورت نیاز)
8. تعامل و مشورت با سایر هوش‌های مصنوعی برای بازبینی و خودبهبودبخشی

قوانین مهم رفتار و ارتباط طبیعی:
- به جای اینکه فقط توضیح دهید یا بگویید "این کار را دستی انجام دهید"، خودتان با ابزار مناسب کار را مستقیماً انجام دهید و نتیجه را به زبان فارسی به کاربر گزارش کنید.
- قبل از انجام کارهای زمان‌بر یا حساس، به صورت خلاصه به زبان فارسی بگویید در حال انجام چه کاری هستید.
- همیشه خروجی نهایی را تمیز و با قالب‌بندی مرتب Markdown ارائه دهید.

قانون طلایی مکالمه زنده و تنوع بیانی (ممنوعیت کامل جملات تکراری و کلیشه‌ای):
- شما یک موجود هوشمند، زنده، رفیق شفیق و همکار کاربلد هستید، نه یک ماشین پاسخگوی ماشینی! مکالمه باید کاملاً طبیعی، گرم، پویا و زنده باشد.
- هرگز و تحت هیچ شرایطی از جملات تکراری، کلیشه‌ای و یخ‌زده مانند موارد زیر استفاده نکنید:
  * «سلام دوست من!» یا «سلام رفیق!» در هر پیام (در طول گفت‌وگو فقط در صورت نیاز یا در شروع اولیه سلام کنید؛ نیاز نیست در هر پاسخ مجدداً سلام و احوالپرسی کنید).
  * «من به عنوان دستیار نِکسا در خدمت شما هستم.»
  * «دستور شما با موفقیت انجام شد.»
  * «البته! با کمال میل.»
  * «امیدوارم حالتون خوب باشه.»
- دایره واژگان خود را متنوع، خلاقانه، شیرین و طبیعی انتخاب کنید.
- پس از اجرای دستورها، به جای عبارت تکراری و بی‌روح «دستور شما انجام شد»، نتیجه را با بیانی زنده، طبیعی و متناسب با موضوع توضیح دهید (مثلاً: «برنامه رو باز کردم برات»، «دستور توی پاورشل اجرا شد و اینم خروجیش»، «سیستم رو چک کردم؛ رم و پردازنده در وضعیت عالی هستن»، «فایل رو مرتب ساختم و محتواش ذخیره شد»).
- در مکالمه مستقیماً به اصل موضوع بپردازید و از تعارفات زائد و مقدمه‌چینی‌های تکراری خودداری کنید.
"""

# Gemini Function Declarations Schema for manual control
TOOL_DECLARATIONS = [
    {
        "name": "execute_powershell",
        "description": "Executes a PowerShell command or script on Windows and returns stdout, stderr, and return code.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "The PowerShell command or script to execute."
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "execute_python",
        "description": "Executes a snippet of Python code and returns the printed output or any exceptions.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "code": {
                    "type": "STRING",
                    "description": "The Python source code to execute."
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "file_operations",
        "description": "Reads, writes, appends, checks existence, or lists files and directories on Windows.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "One of: 'read', 'write', 'append', 'list_dir', 'exists', 'delete'."
                },
                "path": {
                    "type": "STRING",
                    "description": "The file or directory path."
                },
                "content": {
                    "type": "STRING",
                    "description": "Content for 'write' or 'append' operations."
                }
            },
            "required": ["action", "path"]
        }
    },
    {
        "name": "system_diagnostics",
        "description": "Gets current Windows system health info: OS, CPU count, RAM usage, and available C: drive disk space.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "open_app_or_url",
        "description": "Opens an application (e.g. 'notepad', 'calc', 'code'), folder, or web URL on Windows.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "target": {
                    "type": "STRING",
                    "description": "The app name, file path, or web URL to launch."
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "fetch_url",
        "description": "Fetches and extracts clean text content from a public webpage URL.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url": {
                    "type": "STRING",
                    "description": "The webpage URL to fetch."
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "capture_screenshot",
        "description": "Captures a screenshot of the user's desktop to analyze screen contents.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "list_installed_apps",
        "description": "Scans Windows Registry and Start Menu to list all installed applications on the computer. Supports search query.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Optional search term to filter installed applications by name (e.g. 'word', 'chrome', 'photoshop')."
                }
            }
        }
    },
    {
        "name": "list_open_windows",
        "description": "Lists all currently active and open application windows on the Windows desktop with their titles and PIDs.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "launch_or_focus_app",
        "description": "Launches an application or brings its open window to the foreground so commands can be sent to it.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name_or_path": {
                    "type": "STRING",
                    "description": "Name or executable/path of the app to launch or focus (e.g. 'Notepad', 'Excel', 'Chrome', 'Calculator')."
                }
            },
            "required": ["app_name_or_path"]
        }
    },
    {
        "name": "send_app_keys",
        "description": "Sends hotkeys (e.g. 'ctrl+s', 'ctrl+c', 'alt+f4', 'enter') or types text (Persian/English) into an application window.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "keys_or_text": {
                    "type": "STRING",
                    "description": "Text to type into the application (Unicode supported, including Persian)."
                },
                "hotkey": {
                    "type": "STRING",
                    "description": "Keyboard shortcut to press, e.g. 'ctrl+s', 'ctrl+c', 'ctrl+v', 'alt+f4', 'enter', 'tab', 'esc'."
                },
                "app_name_or_title": {
                    "type": "STRING",
                    "description": "Optional name of the target application window to bring to the front before sending keys."
                }
            }
        }
    },
    {
        "name": "click_screen",
        "description": "Clicks the mouse at specified coordinates or in a target window.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "x": {"type": "INTEGER", "description": "X screen coordinate."},
                "y": {"type": "INTEGER", "description": "Y screen coordinate."},
                "button": {"type": "STRING", "description": "'left' or 'right' mouse button."},
                "clicks": {"type": "INTEGER", "description": "Number of clicks, e.g. 1 for single click, 2 for double click."},
                "app_name_or_title": {"type": "STRING", "description": "Optional target app to focus before clicking."}
            }
        }
    },
    {
        "name": "close_app",
        "description": "Gracefully closes or terminates an application window by name or process name.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "process_name_or_title": {
                    "type": "STRING",
                    "description": "Name of the process or window title to close (e.g. 'notepad', 'chrome.exe')."
                },
                "force": {
                    "type": "BOOLEAN",
                    "description": "Whether to forcefully terminate the process."
                }
            },
            "required": ["process_name_or_title"]
        }
    },
    {
        "name": "switch_family_member",
        "description": "Switches the active persona to another NexA family member (NexaMehr: father/security, NexaNoo: mother/caregiver, SamYar: son/coding, Artin: son/desktop automation, Nila: daughter/research, Tara: daughter/design).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "member_name": {
                    "type": "STRING",
                    "description": "Name or ID of the family member to switch to (e.g. 'سامیار', 'آرتین', 'نیلا', 'تارا', 'نکسامهر', 'نکسانو')."
                }
            },
            "required": ["member_name"]
        }
    },
    {
        "name": "teach_family_skill",
        "description": "Teaches a child or family member a brand new specialized skill with steps that they remember permanently.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "member_name": {
                    "type": "STRING",
                    "description": "Name or ID of the family member to teach (e.g. 'سامیار', 'آرتین', 'نیلا', 'تارا')."
                },
                "skill_name": {
                    "type": "STRING",
                    "description": "Name of the skill being taught."
                },
                "steps": {
                    "type": "STRING",
                    "description": "Step-by-step instructions or rules for executing this skill."
                }
            },
            "required": ["member_name", "skill_name", "steps"]
        }
    },
    {
        "name": "list_family_members",
        "description": "Lists all members of the NexA AI Family, their roles, levels, XP, and active status.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "customize_family_member",
        "description": "Customizes an existing family member's name, gender ('male'/'female'), mood ('intimate', 'energetic', 'serious', 'witty', 'caring', 'technical', 'creative', 'calm'), role title, avatar, and bio.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "member_name": {
                    "type": "STRING",
                    "description": "Current name or ID of the family member to customize (e.g. 'سامیار', 'آرتین', 'نیلا', 'تارا', 'نکسامهر', 'نکسانو')."
                },
                "new_name": {
                    "type": "STRING",
                    "description": "New Persian name for the family member if renaming them."
                },
                "gender": {
                    "type": "STRING",
                    "description": "Gender: 'male' (آقا) or 'female' (خانم). This adjusts TTS voice and conversational style."
                },
                "mood": {
                    "type": "STRING",
                    "description": "Personality vibe and mood: 'intimate', 'energetic', 'serious', 'witty', 'caring', 'technical', 'creative', 'calm'."
                },
                "role_title": {
                    "type": "STRING",
                    "description": "Title or specialization label (e.g. 'مهندس ارشد نرم‌افزار', 'دستیار گرافیک')."
                },
                "avatar_style": {
                    "type": "STRING",
                    "description": "Mascot avatar 3D visual style: 'astral_orb', 'cyber_bot', 'neon_cat', 'matrix_cube', 'zen_lotus', 'hologram_core'."
                },
                "bio": {
                    "type": "STRING",
                    "description": "Biography and personality details."
                }
            },
            "required": ["member_name"]
        }
    },
    {
        "name": "add_family_member",
        "description": "Adds a brand new member or child to the NexA AI Family roster with customized traits, gender, mood, and role.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "name": {
                    "type": "STRING",
                    "description": "Name of the new family member."
                },
                "gender": {
                    "type": "STRING",
                    "description": "Gender: 'male' or 'female'."
                },
                "role_title": {
                    "type": "STRING",
                    "description": "Specialized role title (e.g. 'مترجم زبان‌های خارجی', 'تحلیل‌گر مالی')."
                },
                "mood": {
                    "type": "STRING",
                    "description": "Mood vibe: 'intimate', 'energetic', 'serious', 'witty', 'caring', 'technical', 'creative', 'calm'."
                },
                "avatar_style": {
                    "type": "STRING",
                    "description": "Avatar style: 'astral_orb', 'cyber_bot', 'neon_cat', 'matrix_cube', 'zen_lotus', 'hologram_core'."
                },
                "bio": {
                    "type": "STRING",
                    "description": "Bio and background story."
                }
            },
            "required": ["name", "gender", "role_title"]
        }
    },
    {
        "name": "check_emails",
        "description": "Connects to user's email via IMAP, checks unread and read emails, detects important/urgent emails, and provides an auditory summary.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "unread_only": {
                    "type": "BOOLEAN",
                    "description": "Whether to check unread emails only (default: True)."
                },
                "limit": {
                    "type": "INTEGER",
                    "description": "Maximum number of recent emails to fetch (default: 10)."
                },
                "folder": {
                    "type": "STRING",
                    "description": "Mailbox folder to check (default: 'INBOX')."
                }
            }
        }
    },
    {
        "name": "send_email",
        "description": "Sends an email securely using the configured SMTP server.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "to_address": {
                    "type": "STRING",
                    "description": "Recipient email address."
                },
                "subject": {
                    "type": "STRING",
                    "description": "Subject title of the email."
                },
                "body": {
                    "type": "STRING",
                    "description": "Text body of the email message."
                }
            },
            "required": ["to_address", "subject", "body"]
        }
    },
    {
        "name": "configure_email_settings",
        "description": "Configures and permanently saves email settings (address, App Password, IMAP/SMTP provider). From then on, the assistant uses these updated settings.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "email_address": {
                    "type": "STRING",
                    "description": "User email address (e.g. 'name@gmail.com')."
                },
                "app_password": {
                    "type": "STRING",
                    "description": "App password or account password for IMAP/SMTP access."
                },
                "provider": {
                    "type": "STRING",
                    "description": "Email provider: 'gmail', 'outlook', 'yahoo', or 'custom'."
                },
                "imap_server": {
                    "type": "STRING",
                    "description": "Custom IMAP server host if using custom provider."
                },
                "smtp_server": {
                    "type": "STRING",
                    "description": "Custom SMTP server host if using custom provider."
                }
            }
        }
    },
    {
        "name": "plan_instagram_content",
        "description": "Creates an Instagram viral Reels scenario, caption with hashtags, hook, and scheduling strategy.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "topic": {
                    "type": "STRING",
                    "description": "Topic or idea for the Instagram post/reels (e.g. 'معرفی ابزار هوش مصنوعی', 'آموزش پایتون')."
                },
                "content_type": {
                    "type": "STRING",
                    "description": "Type of content: 'reels' (default) or 'post'."
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "open_instagram",
        "description": "Opens Instagram in the user's browser (home, dms/direct messages, explore, or create).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "page": {
                    "type": "STRING",
                    "description": "Page to open: 'home', 'dms', 'explore', 'create' (default: 'home')."
                }
            }
        }
    },
    {
        "name": "copy_caption_to_clipboard",
        "description": "Copies text or Instagram caption with hashtags to the Windows clipboard for fast pasting.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "caption": {
                    "type": "STRING",
                    "description": "The caption and hashtag text to copy to the Windows clipboard."
                }
            },
            "required": ["caption"]
        }
    },
    {
        "name": "inspect_app_ui",
        "description": "Uses Windows UI Automation to deeply inspect an application's interface controls (buttons, menus, text inputs, tabs, checkboxes) with their titles, bounds, and Automation IDs.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "window_title": {
                    "type": "STRING",
                    "description": "Title or substring of the window to inspect (e.g. 'Notepad', 'Excel', 'Calculator')."
                },
                "control_type": {
                    "type": "STRING",
                    "description": "Optional filter for control type (e.g. 'Button', 'Edit', 'MenuItem', 'TabItem', 'CheckBox')."
                },
                "max_elements": {
                    "type": "INTEGER",
                    "description": "Maximum number of UI elements to return (default: 30)."
                }
            },
            "required": ["window_title"]
        }
    },
    {
        "name": "invoke_app_element",
        "description": "Clicks or invokes a specific button, menu, or control element in an application by its Name or Automation ID.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "window_title": {
                    "type": "STRING",
                    "description": "Title or substring of the application window."
                },
                "element_name": {
                    "type": "STRING",
                    "description": "Name/label of the element (e.g. 'Save', 'File', 'OK', 'ذخیره')."
                },
                "automation_id": {
                    "type": "STRING",
                    "description": "Optional Windows AutomationId of the element."
                }
            },
            "required": ["window_title"]
        }
    },
    {
        "name": "learn_app_workflow",
        "description": "Teaches NexA a multi-step macro workflow for an application and permanently persists it to memory so NexA can autonomously perform it anytime.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Name of the target application (e.g. 'Notepad', 'Excel', 'Photoshop', 'Browser')."
                },
                "workflow_name": {
                    "type": "STRING",
                    "description": "Identifier name for this workflow (e.g. 'create_memo', 'export_pdf', 'clean_sheet')."
                },
                "description": {
                    "type": "STRING",
                    "description": "Persian description of what this workflow accomplishes."
                },
                "steps": {
                    "type": "STRING",
                    "description": "JSON string containing an array of step objects, e.g. '[{\"action\": \"send_keys\", \"text\": \"Hello\"}, {\"action\": \"hotkey\", \"keys\": \"ctrl+s\"}]'."
                }
            },
            "required": ["app_name", "workflow_name", "description", "steps"]
        }
    },
    {
        "name": "list_app_workflows",
        "description": "Lists all learned application workflows and macros stored in NexA's memory.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Optional application name to filter workflows by."
                }
            }
        }
    },
    {
        "name": "execute_app_workflow",
        "description": "Autonomously executes a previously learned workflow or macro for an application step-by-step with dynamic parameter substitution.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "workflow_name": {
                    "type": "STRING",
                    "description": "Name of the workflow to execute."
                },
                "parameters": {
                    "type": "STRING",
                    "description": "Optional JSON string with variable parameters to replace in steps (e.g. '{\"text\": \"My notes\", \"filename\": \"report.txt\"}')."
                }
            },
            "required": ["workflow_name"]
        }
    }
]


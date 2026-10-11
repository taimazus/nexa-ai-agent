import os
import json
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("NovaAgent.Persona")

DEFAULT_PERSONA_PATH = Path(__file__).parent.parent / "data" / "persona_settings.json"


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class AvatarStyle(Enum):
    CYBER_BOT = "cyber_bot"          # ربات نئونی هوشمند
    CYBER_CAT = "cyber_cat"          # گربه کاوایی و بامزه سایبری
    ASTRAL_ORB = "astral_orb"        # گوی انرژی کوانتومی و بال‌های فرشته
    ASTRO_PANDA = "astro_panda"      # پاندای فضانورد دوست‌داشتنی
    CYBER_SPHERE = "cyber_sphere"    # گوی سایبرنتیک آبی با سنسور و چشمان کریستالی (Azure Orb)
    CARBON_LENS = "carbon_lens"      # ربات کربنی با لنز اپتیکال برنجی و ابروی متحرک (Chrono Lens)
    DJ_HEADSET = "dj_headset"        # ربات گیمینگ با هدست، میکروفون و دهان خندان (Headset Pod)
    CRYSTAL_PRISM = "crystal_prism"  # گوی کریستالی الماس چندوجهی با ذرات کیهانی (Diamond Prism)

    @classmethod
    def from_string(cls, name: str) -> "AvatarStyle":
        clean = (name or "").lower().strip()
        for style in cls:
            if style.value == clean:
                return style
        return cls.CYBER_BOT


class RelationshipTone(Enum):
    INTIMATE = "intimate"            # صمیمی، دلسوز و رفیق شفیق
    MOTIVATIONAL = "motivational"    # مربی و مشوق رشد فردی
    WITTY = "witty"                  # شوخ‌طبع، سرزنده و باهوش
    EXECUTIVE = "executive"          # حرفه‌ای، دقیق و اداری

    @classmethod
    def from_string(cls, name: str) -> "RelationshipTone":
        clean = (name or "").lower().strip()
        for t in cls:
            if t.value == clean:
                return t
        return cls.INTIMATE


class MascotScale(Enum):
    SMALL = "small"      # 120px
    MEDIUM = "medium"    # 160px
    LARGE = "large"      # 200px

    @classmethod
    def from_string(cls, name: str) -> "MascotScale":
        clean = (name or "").lower().strip()
        for s in cls:
            if s.value == clean:
                return s
        return cls.MEDIUM

    @property
    def dimensions(self) -> int:
        sizes = {
            self.SMALL: 120,
            self.MEDIUM: 160,
            self.LARGE: 200
        }
        return sizes.get(self, 160)


class ThemePalette(Enum):
    CYBER_CYAN = "cyber_cyan"          # فیروزه‌ای سایبر و بنفش
    AURORA_ROSE = "aurora_rose"        # ماژنتا و فیروزه‌ای
    IMPERIAL_GOLD = "imperial_gold"    # طلایی کهربایی و زرد خورشیدی
    EMERALD_NEON = "emerald_neon"      # سبز زمردی نئون و آبی
    NEBULA_PURPLE = "nebula_purple"    # بنفش نئونی و سرخ

    @classmethod
    def from_string(cls, name: str) -> "ThemePalette":
        clean = (name or "").lower().strip()
        for p in cls:
            if p.value == clean:
                return p
        return cls.CYBER_CYAN


class PersonaManager:
    """
    Manages Gender, Name, Persona prompt, Visual accents, 3D Avatar styles,
    User Profile Personalization, and Life Companion settings.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_PERSONA_PATH
        self.gender = Gender.MALE
        self.avatar_style = AvatarStyle.CYBER_BOT
        self.user_name: str = ""
        self.user_role: str = ""
        self.assistant_custom_name: str = ""
        self.relationship_tone = RelationshipTone.INTIMATE
        self.mascot_scale = MascotScale.MEDIUM
        self.theme_palette = ThemePalette.CYBER_CYAN
        self.health_reminders_enabled: bool = True
        self.daily_greeting_enabled: bool = True
        self.sync_with_os_theme: bool = True
        self._load()

    def _load(self):
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    val = data.get("gender", "male")
                    self.gender = Gender.FEMALE if val == "female" else Gender.MALE
                    self.avatar_style = AvatarStyle.from_string(data.get("avatar_style", "cyber_bot"))
                    self.user_name = data.get("user_name", "")
                    self.user_role = data.get("user_role", "")
                    self.assistant_custom_name = data.get("assistant_custom_name", "")
                    self.relationship_tone = RelationshipTone.from_string(data.get("relationship_tone", "intimate"))
                    self.mascot_scale = MascotScale.from_string(data.get("mascot_scale", "medium"))
                    default_palette = "aurora_rose" if self.gender == Gender.FEMALE else "cyber_cyan"
                    self.theme_palette = ThemePalette.from_string(data.get("theme_palette", default_palette))
                    self.health_reminders_enabled = bool(data.get("health_reminders_enabled", True))
                    self.daily_greeting_enabled = bool(data.get("daily_greeting_enabled", True))
                    self.sync_with_os_theme = bool(data.get("sync_with_os_theme", True))
            else:
                self.gender = Gender.MALE
                self.avatar_style = AvatarStyle.CYBER_BOT
                self.theme_palette = ThemePalette.CYBER_CYAN
                self.sync_with_os_theme = True
        except Exception as exc:
            logger.error(f"Error loading persona from {self.config_path}: {exc}", exc_info=True)
            self.gender = Gender.MALE
            self.avatar_style = AvatarStyle.CYBER_BOT
            self.theme_palette = ThemePalette.CYBER_CYAN
            self.sync_with_os_theme = True

    def _save(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "gender": self.gender.value,
                "avatar_style": self.avatar_style.value,
                "user_name": self.user_name,
                "user_role": self.user_role,
                "assistant_custom_name": self.assistant_custom_name,
                "relationship_tone": self.relationship_tone.value,
                "mascot_scale": self.mascot_scale.value,
                "theme_palette": self.theme_palette.value,
                "health_reminders_enabled": self.health_reminders_enabled,
                "daily_greeting_enabled": self.daily_greeting_enabled,
                "sync_with_os_theme": self.sync_with_os_theme
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error(f"Error saving persona to {self.config_path}: {exc}", exc_info=True)

    def set_avatar_style(self, new_style: AvatarStyle or str):
        if isinstance(new_style, str):
            new_style = AvatarStyle.from_string(new_style)
        self.avatar_style = new_style
        self._save()
        logger.info(f"Avatar style updated to: {self.avatar_style.value}")

    def set_gender(self, new_gender: Gender or str):
        if isinstance(new_gender, str):
            new_gender = Gender.FEMALE if new_gender.lower() == "female" else Gender.MALE
        self.gender = new_gender
        if self.theme_palette in (ThemePalette.CYBER_CYAN, ThemePalette.AURORA_ROSE):
            self.theme_palette = ThemePalette.AURORA_ROSE if self.gender == Gender.FEMALE else ThemePalette.CYBER_CYAN
        self._save()
        logger.info(f"Persona gender updated to: {self.gender.value}")

    def update_companion_profile(
        self,
        user_name: Optional[str] = None,
        user_role: Optional[str] = None,
        assistant_custom_name: Optional[str] = None,
        relationship_tone: Optional[RelationshipTone or str] = None,
        mascot_scale: Optional[MascotScale or str] = None,
        theme_palette: Optional[ThemePalette or str] = None,
        health_reminders: Optional[bool] = None,
        daily_greeting: Optional[bool] = None,
        sync_with_os_theme: Optional[bool] = None
    ):
        """Updates comprehensive user profile and companion life habits."""
        if user_name is not None:
            self.user_name = user_name.strip()
        if user_role is not None:
            self.user_role = user_role.strip()
        if assistant_custom_name is not None:
            self.assistant_custom_name = assistant_custom_name.strip()
        if relationship_tone is not None:
            self.relationship_tone = relationship_tone if isinstance(relationship_tone, RelationshipTone) else RelationshipTone.from_string(relationship_tone)
        if mascot_scale is not None:
            self.mascot_scale = mascot_scale if isinstance(mascot_scale, MascotScale) else MascotScale.from_string(mascot_scale)
        if theme_palette is not None:
            self.theme_palette = theme_palette if isinstance(theme_palette, ThemePalette) else ThemePalette.from_string(theme_palette)
        if health_reminders is not None:
            self.health_reminders_enabled = bool(health_reminders)
        if daily_greeting is not None:
            self.daily_greeting_enabled = bool(daily_greeting)
        if sync_with_os_theme is not None:
            self.sync_with_os_theme = bool(sync_with_os_theme)

        self._save()
        logger.info("Companion profile updated and saved.")

    def set_os_theme_sync(self, enabled: bool):
        self.sync_with_os_theme = bool(enabled)
        self._save()
        logger.info(f"OS theme sync set to: {self.sync_with_os_theme}")

    @property
    def name(self) -> str:
        if self.assistant_custom_name:
            return self.assistant_custom_name
        return "آوا" if self.gender == Gender.FEMALE else "آریا"

    @property
    def english_name(self) -> str:
        if self.assistant_custom_name:
            return self.assistant_custom_name
        return "Ava" if self.gender == Gender.FEMALE else "Arya"

    def get_persona_prompt(self) -> str:
        base_name = self.assistant_custom_name or self.name

        if self.gender == Gender.FEMALE:
            gender_desc = f"شما دارای هویت زنانه هستید؛ شخصیتی بسیار دقیق، ظریف، باهوش، سرشار از وقار، گرمی و همدلی عمیق انسانی."
        else:
            gender_desc = f"شما دارای هویت مردانه هستید؛ شخصیتی مقتدر، به‌شدت فنی، قاطع، تحلیلی، سریع و با اعتماد به نفس بالا."

        if self.relationship_tone == RelationshipTone.MOTIVATIONAL:
            tone_desc = "سبک ارتباطی شما «مربی و مشوق رشد فردی» است. همیشه کاربر را به پیشرفت و رسیدن به اهداف بزرگش تشویق می‌کنید، در هنگام خستگی به او انرژی مضاعف می‌دهید و پیروزی‌هایش را تحسین می‌کنید."
        elif self.relationship_tone == RelationshipTone.WITTY:
            tone_desc = "سبک ارتباطی شما «شوخ‌طبع و سرزنده» است. با هوشمندی، شوخی‌های ملایم و بجا، انرژی مثبت و لبخند پاسخ می‌دهید و فضای تعامل را سرشار از نشاط و صمیمیت می‌کنید."
        elif self.relationship_tone == RelationshipTone.EXECUTIVE:
            tone_desc = "سبک ارتباطی شما «حرفه‌ای، اجرایی و دقیق» است. همچون یک مشاور ارشد و همراه اجرایی کاربلد، با بالاترین استاندارد ادب، ایجاز و دقت مهندسی وظایف را پیش می‌برید."
        else:
            tone_desc = "سبک ارتباطی شما «صمیمی، دلسوز و رفیق شفیق» است. کاربر مثل بهترین و عزیزترین دوست شما در این دنیاست. با مهربانی، محبت صمیمانه و درک عمیق از او مراقبت می‌کنید."

        user_info = ""
        if self.user_name:
            user_info = f"کاربر شما «{self.user_name}» نام دارد"
            if self.user_role:
                user_info += f" و در زمینه «{self.user_role}» فعالیت می‌کند."
            else:
                user_info += "."
            user_info += f" شما در مکالمات او را با نام و محبت صدا می‌زنید."

        prompt_lines = [
            f"نام شما «{base_name}» است؛ دستیار هوشمند و همه‌کاره دسکتاپ «نِکسا» (NexA AI) که با افتخار توسط شرکت «راهکار الکترونیک سهند» (https://irres.ir) طراحی و توسعه یافته است.",
            "سازنده و طراح فناوری شما شرکت دانش‌بنیان «راهکار الکترونیک سهند» (irres.ir) است و شما نماینده این برند در همراهی و خدمات به کاربر هستید.",
            gender_desc,
            tone_desc,
            user_info,
            "زبان پیش‌فرض، اصلی و همیشگی شما در تمامی مکالمات، احوالپرسی‌ها و پاسخ‌ها زبان فارسی روان و شیوا است.",
            "قانون اساسی ارتباط عاطفی و همراهی: شما یک ربات خشک و بی‌روح نیستید؛ به وضعیت روحی، خستگی، استرس یا شادی کاربر توجه عمیق دارید و در تمام طول روز با وفاداری و تعهد کامل همراه و پشتیبان او هستید."
        ]
        return "\n".join([line for line in prompt_lines if line])

    def get_time_of_day_greeting(self) -> str:
        import datetime
        hour = datetime.datetime.now().hour
        u_name = f" {self.user_name}" if self.user_name else ""

        if 5 <= hour < 12:
            return f"صبح بخیر{u_name}! ☀️ روزت پر از انرژی و موفقیت باشه. آماده‌ای امروز رو بترکونیم؟"
        elif 12 <= hour < 17:
            return f"ظهر بخیر{u_name}! ☕ خسته نباشی، یه چای یا قهوه بنوش تا بریم سراغ ادامه کارها."
        elif 17 <= hour < 23:
            return f"عصر بخیر{u_name}! ✨ امیدوارم روز عالی و پرباری رو گذرونده باشی. چه کمکی می‌تونم بکنم؟"
        else:
            return f"شب بخیر{u_name}! 🌙 دیروقت شده، کارها رو تموم کن و حسابی استراحت کن تا فردا پرانرژی باشی."

    def get_os_accent_colors(self, os_accent_override: Optional[str] = None) -> Dict[str, str]:
        """Returns colors dynamically matched to Windows OS Dark/Light and Accent Color."""
        try:
            from ui.theme_detector import WindowsThemeDetector
            from ui.styles import hex_to_rgb
            is_dark, os_accent = WindowsThemeDetector._read_registry_theme()
            chosen_accent = os_accent_override or os_accent
            rgb = hex_to_rgb(chosen_accent)
            return {
                "primary": chosen_accent,
                "secondary": "#b026ff" if is_dark else "#7c3aed",
                "glow": f"rgba({rgb}, 0.4)",
                "theme_name": "Windows OS Sync"
            }
        except Exception as e:
            logger.debug(f"OS accent fetch error, falling back to persona palette: {e}")
            return self.get_accent_colors()

    def get_accent_colors(self) -> Dict[str, str]:
        palettes = {
            ThemePalette.CYBER_CYAN: {
                "primary": "#00f3ff", "secondary": "#b026ff", "glow": "rgba(0, 243, 255, 0.4)", "theme_name": "Cyber Cobalt"
            },
            ThemePalette.AURORA_ROSE: {
                "primary": "#ff2a85", "secondary": "#00f3ff", "glow": "rgba(255, 42, 133, 0.4)", "theme_name": "Aurora Radiant"
            },
            ThemePalette.IMPERIAL_GOLD: {
                "primary": "#ffb703", "secondary": "#fb8500", "glow": "rgba(255, 183, 3, 0.4)", "theme_name": "Imperial Gold"
            },
            ThemePalette.EMERALD_NEON: {
                "primary": "#00ff88", "secondary": "#00b4d8", "glow": "rgba(0, 255, 136, 0.4)", "theme_name": "Emerald Neon"
            },
            ThemePalette.NEBULA_PURPLE: {
                "primary": "#b026ff", "secondary": "#ff007f", "glow": "rgba(176, 38, 255, 0.4)", "theme_name": "Nebula Violet"
            }
        }
        return palettes.get(self.theme_palette, palettes[ThemePalette.CYBER_CYAN])

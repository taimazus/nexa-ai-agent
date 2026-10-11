import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("NexA.Integrations.Config")

DEFAULT_INTEGRATIONS_PATH = Path(__file__).parent.parent.parent / "data" / "integrations_config.json"

PRESET_SERVERS = {
    "gmail": {
        "name": "گوگل (Gmail)",
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_ssl": True
    },
    "outlook": {
        "name": "مایکروسافت (Outlook / Hotmail)",
        "imap_server": "outlook.office365.com",
        "imap_port": 993,
        "smtp_server": "smtp.office365.com",
        "smtp_port": 587,
        "use_ssl": True
    },
    "yahoo": {
        "name": "یاهو (Yahoo Mail)",
        "imap_server": "imap.mail.yahoo.com",
        "imap_port": 993,
        "smtp_server": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "use_ssl": True
    },
    "custom": {
        "name": "سرور اختصاصی / شرکتی (Custom Server)",
        "imap_server": "mail.example.com",
        "imap_port": 993,
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "use_ssl": True
    }
}


class ServicesConfigManager:
    """
    Manages persistent configurations for External Services:
    1. Email (IMAP/SMTP with auto-detection, presets, and customized credentials)
    2. Instagram / Social Media (Browser profile automation, reels scripting & scheduling)
    
    Automatically initializes intelligent defaults based on the host Windows environment,
    and permanently persists any user overrides.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_INTEGRATIONS_PATH
        self.data: Dict[str, Any] = {}
        self._load_or_create_defaults()

    def _get_system_chrome_profile(self) -> str:
        """Finds default Chrome User Data directory on Windows if available."""
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            chrome_path = os.path.join(local_app_data, "Google", "Chrome", "User Data")
            if os.path.exists(chrome_path):
                return chrome_path
        return ""

    def _generate_default_config(self) -> Dict[str, Any]:
        """Generates smart defaults tailored to the user's Windows PC."""
        win_user = os.environ.get("USERNAME", "User")
        chrome_dir = self._get_system_chrome_profile()

        return {
            "version": "1.0",
            "system_user": win_user,
            "company_attribution": {
                "name": "راهکار الکترونیک سهند",
                "website": "https://irres.ir"
            },
            "email": {
                "provider": "gmail",
                "email_address": "",
                "app_password": "",
                "imap_server": "imap.gmail.com",
                "imap_port": 993,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "use_ssl": True,
                "check_interval_mins": 15,
                "auto_summarize_important": True,
                "voice_readout_enabled": True,
                "max_fetch_count": 10,
                "important_keywords": [
                    "فوری", "مهم", "بانک", "تایید", "رمز", "فاکتور", "بیمه", "قرارداد",
                    "urgent", "important", "security", "alert", "invoice", "verification"
                ]
            },
            "instagram": {
                "account_username": "",
                "browser_user_data_dir": chrome_dir,
                "caption_tone": "creative_friendly",
                "include_hashtags": True,
                "reels_duration_target_sec": 30,
                "auto_schedule": False,
                "default_hashtags": [
                    "#هوش_مصنوعی", "#تکنولوژی", "#راهکار_الکترونیک_سهند", "#دستیار_هوشمند"
                ]
            },
            "voice_conversation": {
                "hands_free_enabled": False,
                "wake_word_enabled": False,
                "wake_words": ["نکسا", "نِکسا", "nexa", "سلام نکسا"],
                "dialog_timeout_sec": 30.0,
                "silence_timeout_sec": 0.9,
                "vad_sensitivity": "medium",
                "min_speech_duration_sec": 0.4,
                "auto_resume_after_speaking": True
            }
        }

    def _load_or_create_defaults(self):
        """Loads configuration from JSON or creates defaults on first run."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                logger.info(f"Loaded integrations config from {self.config_path}")
                # Ensure missing keys are merged
                defaults = self._generate_default_config()
                modified = False
                for section in ["email", "instagram", "voice_conversation"]:
                    if section not in self.data:
                        self.data[section] = defaults[section]
                        modified = True
                    else:
                        for k, v in defaults[section].items():
                            if k not in self.data[section]:
                                self.data[section][k] = v
                                modified = True
                if modified:
                    self.save()
            else:
                self.data = self._generate_default_config()
                self.save()
                logger.info(f"Initialized new default integrations config at {self.config_path}")
        except Exception as exc:
            logger.error(f"Error loading integrations config: {exc}", exc_info=True)
            self.data = self._generate_default_config()

    def save(self) -> bool:
        """Persists the current configuration to disk."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info("Saved integrations config successfully.")
            return True
        except Exception as exc:
            logger.error(f"Failed to save integrations config: {exc}", exc_info=True)
            return False

    def get_email_config(self) -> Dict[str, Any]:
        """Returns email configuration dictionary."""
        return self.data.get("email", {})

    def update_email_config(
        self,
        provider: Optional[str] = None,
        email_address: Optional[str] = None,
        app_password: Optional[str] = None,
        imap_server: Optional[str] = None,
        imap_port: Optional[int] = None,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        use_ssl: Optional[bool] = None,
        check_interval_mins: Optional[int] = None,
        auto_summarize_important: Optional[bool] = None,
        voice_readout_enabled: Optional[bool] = None,
        max_fetch_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Updates email configuration and immediately persists.
        Supports presets (e.g. 'gmail', 'outlook', 'yahoo') to auto-fill servers/ports.
        """
        cfg = self.data.setdefault("email", {})

        if provider and provider.lower() in PRESET_SERVERS:
            p_key = provider.lower()
            cfg["provider"] = p_key
            preset = PRESET_SERVERS[p_key]
            cfg["imap_server"] = preset["imap_server"]
            cfg["imap_port"] = preset["imap_port"]
            cfg["smtp_server"] = preset["smtp_server"]
            cfg["smtp_port"] = preset["smtp_port"]
            cfg["use_ssl"] = preset["use_ssl"]
        elif provider:
            cfg["provider"] = provider.lower()

        if email_address is not None and email_address.strip():
            cfg["email_address"] = email_address.strip()
        if app_password is not None and app_password.strip():
            cfg["app_password"] = app_password.strip()
        if imap_server is not None and imap_server.strip():
            cfg["imap_server"] = imap_server.strip()
        if imap_port is not None:
            cfg["imap_port"] = int(imap_port)
        if smtp_server is not None and smtp_server.strip():
            cfg["smtp_server"] = smtp_server.strip()
        if smtp_port is not None:
            cfg["smtp_port"] = int(smtp_port)
        if use_ssl is not None:
            cfg["use_ssl"] = bool(use_ssl)
        if check_interval_mins is not None:
            cfg["check_interval_mins"] = int(check_interval_mins)
        if auto_summarize_important is not None:
            cfg["auto_summarize_important"] = bool(auto_summarize_important)
        if voice_readout_enabled is not None:
            cfg["voice_readout_enabled"] = bool(voice_readout_enabled)
        if max_fetch_count is not None:
            cfg["max_fetch_count"] = max(1, min(50, int(max_fetch_count)))

        self.save()
        logger.info(f"Updated email settings for '{cfg.get('email_address')}'. Persisted to disk.")
        return {
            "success": True,
            "provider": cfg.get("provider"),
            "email_address": cfg.get("email_address"),
            "imap_server": cfg.get("imap_server"),
            "is_configured": bool(cfg.get("email_address") and cfg.get("app_password"))
        }

    def get_instagram_config(self) -> Dict[str, Any]:
        """Returns Instagram configuration dictionary."""
        return self.data.get("instagram", {})

    def update_instagram_config(
        self,
        account_username: Optional[str] = None,
        browser_user_data_dir: Optional[str] = None,
        caption_tone: Optional[str] = None,
        include_hashtags: Optional[bool] = None,
        reels_duration_target_sec: Optional[int] = None
    ) -> Dict[str, Any]:
        """Updates Instagram configuration and immediately persists."""
        cfg = self.data.setdefault("instagram", {})
        if account_username is not None:
            cfg["account_username"] = account_username.strip()
        if browser_user_data_dir is not None:
            cfg["browser_user_data_dir"] = browser_user_data_dir.strip()
        if caption_tone is not None:
            cfg["caption_tone"] = caption_tone.strip()
        if include_hashtags is not None:
            cfg["include_hashtags"] = bool(include_hashtags)
        if reels_duration_target_sec is not None:
            cfg["reels_duration_target_sec"] = int(reels_duration_target_sec)

        self.save()
        logger.info("Updated Instagram configuration. Persisted to disk.")
        return {"success": True, "instagram": cfg}

    def get_voice_conversation_config(self) -> Dict[str, Any]:
        """Returns voice conversation (hands-free VAD) settings."""
        return self.data.get("voice_conversation", {
            "hands_free_enabled": False,
            "silence_timeout_sec": 0.9,
            "vad_sensitivity": "medium",
            "min_speech_duration_sec": 0.4,
            "auto_resume_after_speaking": True
        })

    def update_voice_conversation_config(
        self,
        hands_free_enabled: Optional[bool] = None,
        wake_word_enabled: Optional[bool] = None,
        silence_timeout_sec: Optional[float] = None,
        vad_sensitivity: Optional[str] = None,
        min_speech_duration_sec: Optional[float] = None,
        auto_resume_after_speaking: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Updates and permanently persists hands-free voice conversation settings."""
        cfg = self.data.setdefault("voice_conversation", {})
        if hands_free_enabled is not None:
            cfg["hands_free_enabled"] = bool(hands_free_enabled)
        if wake_word_enabled is not None:
            cfg["wake_word_enabled"] = bool(wake_word_enabled)
        if silence_timeout_sec is not None:
            cfg["silence_timeout_sec"] = max(0.4, min(3.0, float(silence_timeout_sec)))
        if vad_sensitivity is not None and vad_sensitivity in ["low", "medium", "high"]:
            cfg["vad_sensitivity"] = vad_sensitivity
        if min_speech_duration_sec is not None:
            cfg["min_speech_duration_sec"] = max(0.2, min(2.0, float(min_speech_duration_sec)))
        if auto_resume_after_speaking is not None:
            cfg["auto_resume_after_speaking"] = bool(auto_resume_after_speaking)

        self.save()
        logger.info(f"Updated voice conversation config. Persisted to {self.config_path}")
        return {"success": True, "voice_conversation": cfg}

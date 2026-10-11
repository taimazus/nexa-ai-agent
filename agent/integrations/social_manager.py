import logging
from typing import Dict, Any, List, Optional
from agent.integrations.config_manager import ServicesConfigManager

logger = logging.getLogger("NexA.Integrations.Social")


class SocialMediaManager:
    """
    Instagram & Social Media Content Specialist Engine for NexA AI (Tara & Artin):
    - Plans viral Reels scenarios, slide outlines, hooks, captions, and hashtag strategies.
    - Manages browser session directory for direct messages inspection.
    - Saves and retrieves persistent posting schedules and draft assets.
    """

    def __init__(self, config_manager: Optional[ServicesConfigManager] = None):
        self.config_manager = config_manager or ServicesConfigManager()

    def plan_content(
        self,
        topic: str,
        content_type: str = "reels",
        target_audience: str = "عمومی و علاقه‌مندان به تکنولوژی"
    ) -> Dict[str, Any]:
        """
        Generates a complete Instagram post or viral Reels production package.
        """
        cfg = self.config_manager.get_instagram_config()
        tone = cfg.get("caption_tone", "creative_friendly")
        default_tags = cfg.get("default_hashtags", [])

        # Construct viral scenario
        hook = f"🔥 چرا تا الان کسی این رو درباره «{topic}» بهت نگفته بود؟!"
        scenario_steps = [
            {"second": "0-3s", "visual": "تصویرسازی سریع یا زوم روی چهره/صفحه", "voiceover": hook},
            {"second": "3-15s", "visual": "ارائه ۳ نکته کلیدی و راهکار عملی", "voiceover": f"سه راهکار طلایی برای حل مسئله {topic}..."},
            {"second": "15-25s", "visual": "اثبات نتیجه و نمایش نمونه عملی", "voiceover": "ببین چطور در عمل نتیجه میده..."},
            {"second": "25-30s", "visual": "دعوت به اقدام (CTA) و اسلاید پایانی", "voiceover": "این پست رو سیو کن تا گمش نکنی و برای دوستات بفرست!"}
        ]

        caption = (
            f"🚀 همه‌چیز درباره {topic} که باید بدونی!\n\n"
            f"اگر می‌خوای در زمینه {topic} همیشه یک قدم جلوتر باشی، حتماً این چند نکته رو به کار ببند.\n\n"
            f"👇 نظرت چیه؟ توی کامنت‌ها برام بنویس!\n"
            f"💾 یادت نره این پست رو ذخیره کنی.\n\n"
            f"{' '.join(default_tags)} #{topic.replace(' ', '_')}"
        )

        return {
            "success": True,
            "topic": topic,
            "content_type": content_type,
            "hook": hook,
            "scenario": scenario_steps,
            "caption": caption,
            "hashtags": default_tags + [f"#{topic.replace(' ', '_')}"],
            "recommended_music": "موسیقی ترند الکترونیک ریتمیک با انرژی مثبت",
            "production_tip": "استفاده از زیرنویس متحرک رنگی با فونت درشت در ثانیه‌های ابتدایی بازدید را تا ۳ برابر افزایش می‌دهد."
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns Instagram automation status and configuration."""
        cfg = self.config_manager.get_instagram_config()
        return {
            "account_username": cfg.get("account_username", ""),
            "browser_profile_configured": bool(cfg.get("browser_user_data_dir")),
            "browser_user_data_dir": cfg.get("browser_user_data_dir", ""),
            "reels_duration_sec": cfg.get("reels_duration_target_sec", 30)
        }

    def open_instagram(self, page: str = "home") -> Dict[str, Any]:
        """Opens Instagram in the default browser using the configured user session."""
        from agent import tools
        url_map = {
            "home": "https://www.instagram.com/",
            "dms": "https://www.instagram.com/direct/inbox/",
            "explore": "https://www.instagram.com/explore/",
            "create": "https://www.instagram.com/"
        }
        target_url = url_map.get(page.lower().strip(), "https://www.instagram.com/")
        res = tools.open_app_or_url(target_url)
        return {
            "success": res.get("success", True),
            "target_url": target_url,
            "message": f"صفحه اینستاگرام ({page}) در مرورگر سیستم باز شد."
        }

    def copy_caption_to_clipboard(self, caption: str) -> Dict[str, Any]:
        """Copies Instagram caption text to the Windows clipboard for instant pasting."""
        import subprocess
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                input=caption.encode("utf-8"),
                check=True
            )
            return {"success": True, "message": "متن کپشن و هشتگ‌ها در کلیپ‌بورد ویندوز کپی شد و آماده چسباندن (Paste) است."}
        except Exception as exc:
            logger.error(f"Error copying to clipboard: {exc}")
            return {"success": False, "error": str(exc)}


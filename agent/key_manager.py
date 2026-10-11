import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("NovaAgent.KeyManager")

DEFAULT_SETTINGS_PATH = Path(__file__).parent.parent / "data" / "settings.json"


class KeyManager:
    """
    Manages a resilient pool of Gemini API keys with automatic failover,
    rotation on quota exhaustion, and persistent storage.
    """

    def __init__(self, config_path: Optional[str] = None, default_key: Optional[str] = None):
        is_default_path = config_path is None
        self.config_path = Path(config_path) if config_path else DEFAULT_SETTINGS_PATH
        self.keys: List[Dict[str, Any]] = []
        self.active_index: int = 0
        self._load()

        # Only seed from environment if using default app path or explicit default_key
        seed_key = default_key or (os.environ.get("GEMINI_API_KEY") if is_default_path else None)
        if not self.keys and seed_key:
            self.add_key(seed_key, label="کلید پیش‌فرض محیطی")

    def _load(self):
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.keys = data.get("api_keys", [])
                    self.active_index = data.get("active_index", 0)
                    if self.active_index >= len(self.keys):
                        self.active_index = 0
            else:
                self.keys = []
                self.active_index = 0
        except Exception as exc:
            logger.error(f"Error loading settings from {self.config_path}: {exc}", exc_info=True)
            self.keys = []
            self.active_index = 0

    def _save(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "api_keys": self.keys,
                "active_index": self.active_index,
                "updated_at": time.time()
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error(f"Error saving settings to {self.config_path}: {exc}", exc_info=True)

    def get_keys(self) -> List[Dict[str, Any]]:
        return list(self.keys)

    def get_active_key(self) -> Optional[str]:
        if not self.keys:
            return None
        if self.active_index >= len(self.keys):
            self.active_index = 0
        return self.keys[self.active_index]["key"]

    def add_key(self, key: str, label: str = "") -> bool:
        clean_key = key.strip()
        if not clean_key:
            return False
        # Avoid duplicate keys
        for item in self.keys:
            if item["key"] == clean_key:
                return False

        label = label.strip() or f"کلید شماره {len(self.keys) + 1}"
        self.keys.append({
            "key": clean_key,
            "label": label,
            "status": "active",
            "fail_count": 0,
            "last_used": time.time(),
            "failure_reason": ""
        })
        self._save()
        return True

    def remove_key(self, key: str) -> bool:
        clean_key = key.strip()
        idx_to_remove = -1
        for i, item in enumerate(self.keys):
            if item["key"] == clean_key:
                idx_to_remove = i
                break

        if idx_to_remove != -1:
            self.keys.pop(idx_to_remove)
            if self.active_index >= len(self.keys):
                self.active_index = max(0, len(self.keys) - 1)
            self._save()
            return True
        return False

    def set_active_key(self, key: str) -> bool:
        clean_key = key.strip()
        for i, item in enumerate(self.keys):
            if item["key"] == clean_key:
                self.active_index = i
                item["status"] = "active"
                self._save()
                return True
        return False

    def mark_current_failed(self, reason: str = "") -> Optional[str]:
        """
        Marks current key as exhausted/failed and rotates to the next available key in the pool.
        Returns the new active key string, or None if no keys left.
        """
        if not self.keys:
            return None

        current = self.keys[self.active_index]
        current["status"] = "quota_exceeded"
        current["fail_count"] = current.get("fail_count", 0) + 1
        current["failure_reason"] = reason
        logger.warning(f"Key {current['label']} marked as failed: {reason}. Switching to next key...")

        # Search next active key
        num_keys = len(self.keys)
        found_next = False
        for step in range(1, num_keys + 1):
            next_idx = (self.active_index + step) % num_keys
            if self.keys[next_idx]["status"] == "active":
                self.active_index = next_idx
                found_next = True
                break

        if not found_next:
            # All keys are exhausted
            logger.error("All API keys in pool have been exhausted!")
            self._save()
            return None

        self._save()
        return self.get_active_key()

    def get_pool_health(self) -> Dict[str, Any]:
        """
        Assesses quota headroom, remaining active keys, and generates proactive warnings.
        """
        total_keys = len(self.keys)
        active_keys = sum(1 for k in self.keys if k.get("status") == "active")
        exhausted_keys = sum(1 for k in self.keys if k.get("status") == "quota_exceeded")
        is_depleted = (active_keys == 0) and (total_keys > 0)
        is_low_quota = (active_keys <= 1) and (total_keys > 0)

        if is_depleted:
            alert_message = "🚨 هشدار بحرانی: اعتبار تمام کلیدهای API به پایان رسیده است! لطفاً از بخش تنظیمات کلید جدید اضافه کنید."
            severity = "critical"
        elif is_low_quota:
            alert_message = f"⚠️ هشدار کاهش اعتبار: اعتبار یکی از کلیدها تمام شد و تنها {active_keys} کلید فعال در استخر باقی مانده است!"
            severity = "warning"
        else:
            alert_message = ""
            severity = "ok"

        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "exhausted_keys": exhausted_keys,
            "is_low_quota": is_low_quota,
            "is_depleted": is_depleted,
            "severity": severity,
            "alert_message": alert_message
        }

    def reset_all_statuses(self):
        """Resets all keys to active status."""
        for item in self.keys:
            item["status"] = "active"
            item["failure_reason"] = ""
        self._save()

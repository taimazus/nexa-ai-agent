import os
import json
import logging
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("NovaAgent.Learning")

DEFAULT_LEARNINGS_PATH = Path(__file__).parent.parent / "data" / "learnings.json"


class LearningEngine:
    """
    Self-Improvement & Continuous Learning Engine.
    Records lessons from execution errors, user corrections, and reflections.
    Dynamically injects acquired wisdom into system instructions to prevent repeating mistakes.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else DEFAULT_LEARNINGS_PATH
        self.learnings: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        try:
            if self.storage_path.exists():
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.learnings = data.get("rules", [])
            else:
                self.learnings = []
        except Exception as exc:
            logger.error(f"Error loading learnings from {self.storage_path}: {exc}", exc_info=True)
            self.learnings = []

    def _save(self):
        with self._lock:
            try:
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "rules": self.learnings,
                    "count": len(self.learnings),
                    "last_updated": time.time()
                }
                temp_file = self.storage_path.with_suffix(".tmp")
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                temp_file.replace(self.storage_path)
            except Exception as exc:
                logger.error(f"Error saving learnings to {self.storage_path}: {exc}", exc_info=True)

    def record_learning(self, trigger: str, corrective_rule: str, category: str = "general") -> Dict[str, Any]:
        """
        Records a new learned rule/lesson from an error or user correction.
        """
        clean_trig = trigger.strip()
        clean_rule = corrective_rule.strip()
        if not clean_trig or not clean_rule:
            return {"success": False, "error": "موضوع یا قانون آموخته‌شده نمی‌تواند خالی باشد."}

        # Check for duplicate trigger
        for item in self.learnings:
            if item.get("trigger", "").lower() == clean_trig.lower():
                item["rule"] = clean_rule
                item["category"] = category
                item["updated_at"] = time.time()
                self._save()
                return {"success": True, "message": f"قانون برای '{clean_trig}' به‌روزرسانی شد.", "item": item}

        new_item = {
            "id": f"lrn_{int(time.time() * 1000)}",
            "trigger": clean_trig,
            "rule": clean_rule,
            "category": category,
            "created_at": time.time(),
            "date_str": time.strftime("%Y-%m-%d %H:%M")
        }
        self.learnings.append(new_item)
        self._save()
        logger.info(f"New self-learning recorded: [{category}] {clean_trig} -> {clean_rule}")
        return {
            "success": True,
            "message": f"درس جدید با موفقیت ثبت شد و از این به بعد اعمال خواهد شد: {clean_rule}",
            "item": new_item
        }

    def query_learnings(self, query: str = "") -> List[Dict[str, Any]]:
        """
        Searches learned rules by keyword or returns all.
        """
        q = query.strip().lower()
        if not q:
            return list(self.learnings)
        return [
            item for item in self.learnings
            if q in item.get("trigger", "").lower() or
               q in item.get("rule", "").lower() or
               q in item.get("category", "").lower()
        ]

    def delete_learning(self, rule_id_or_trigger: str) -> Dict[str, Any]:
        target = rule_id_or_trigger.strip().lower()
        idx_to_remove = -1
        for i, item in enumerate(self.learnings):
            if item.get("id") == target or item.get("trigger", "").lower() == target:
                idx_to_remove = i
                break

        if idx_to_remove != -1:
            popped = self.learnings.pop(idx_to_remove)
            self._save()
            return {"success": True, "message": f"قانون آموخته‌شده '{popped.get('rule')}' حذف شد."}
        return {"success": False, "error": "مورد موردنظر یافت نشد."}

    def clear_learnings(self) -> Dict[str, Any]:
        self.learnings.clear()
        self._save()
        return {"success": True, "message": "تمام درس‌های آموخته‌شده پاکسازی شدند."}

    def get_prompt_injection(self) -> str:
        """
        Builds the strict directive section for Gemini's system instructions
        ensuring it abides by past learnings and avoids repeating mistakes.
        """
        if not self.learnings:
            return ""

        lines = [
            "\n### قوانین و درس‌های آموخته‌شده از خطاهای گذشته (مهم: هرگز این اشتباهات را تکرار نکنید):",
            "این قوانین حاصل تجربیات و اصلاحات پیشین شما در همین سیستم هستند و باید حتماً رعایت شوند:"
        ]
        for i, item in enumerate(self.learnings, 1):
            lines.append(f"{i}. [{item.get('category', 'عمومی')}] علت: {item.get('trigger')} -> **دستور اصلاحی: {item.get('rule')}**")

        return "\n".join(lines) + "\n"

    def auto_learn_from_failure(self, tool_name: str, args: Dict[str, Any], error_output: str):
        """
        Heuristic reflection: Automatically learns patterns when a tool fails.
        """
        err_lower = error_output.lower()
        if "cannot find path" in err_lower or "the system cannot find the file" in err_lower:
            self.record_learning(
                trigger=f"مسیر ناموجود در {tool_name}",
                corrective_rule="همیشه قبل از اجرا، وجود فایل/پوشه را با ابزار file_operations (exists) بررسی کن یا از مسیر مطلق معتبر استفاده کن.",
                category="filesystem"
            )
        elif "is not recognized as an internal or external command" in err_lower:
            cmd = args.get("command", "")
            self.record_learning(
                trigger=f"دستور ناشناخته در ویندوز: {cmd[:40]}",
                corrective_rule="برای دستورات غیرپیش‌فرض، ابتدا بررسی کن آیا در PATH نصب است یا از معادل‌های استاندارد پاورشل استفاده کن.",
                category="powershell"
            )
        elif "modulenotfounderror" in err_lower or "no module named" in err_lower:
            self.record_learning(
                trigger=f"عدم نصب پکیج در کد پایتون",
                corrective_rule="قبل از استفاده از کتابخانه‌های متفرقه، ماژول‌های استاندارد پایتون را ترجیح بده یا بررسی کن پکیج نصب باشد.",
                category="python"
            )

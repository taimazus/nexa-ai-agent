import os
import json
import logging
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("NovaAgent.Memory")

DEFAULT_MEMORY_PATH = Path(__file__).parent.parent / "data" / "memory.json"


class MemoryManager:
    """
    Persistent Long-Term Memory System for Nova Agent.
    Stores user preferences, facts, project context, and instructions.
    Injects context into prompts and provides callable tools for the agent.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else DEFAULT_MEMORY_PATH
        self.memories: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        try:
            if self.storage_path.exists():
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.memories = data.get("facts", {})
            else:
                self.memories = {}
        except Exception as exc:
            logger.error(f"Error loading memory from {self.storage_path}: {exc}", exc_info=True)
            self.memories = {}

    def _save(self):
        with self._lock:
            try:
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "facts": self.memories,
                    "count": len(self.memories),
                    "last_updated": time.time()
                }
                temp_file = self.storage_path.with_suffix(".tmp")
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                temp_file.replace(self.storage_path)
            except Exception as exc:
                logger.error(f"Error saving memory to {self.storage_path}: {exc}", exc_info=True)

    def remember_fact(self, key: str, value: str, category: str = "general") -> Dict[str, Any]:
        """
        Stores or updates a persistent memory item.
        """
        clean_key = key.strip()
        clean_val = value.strip()
        if not clean_key or not clean_val:
            return {"success": False, "error": "کلید یا مقدار حافظه نمی‌تواند خالی باشد."}

        self.memories[clean_key] = {
            "key": clean_key,
            "value": clean_val,
            "category": category,
            "timestamp": time.time(),
            "updated_str": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save()
        logger.info(f"Memory saved: [{category}] {clean_key} = {clean_val[:60]}")
        return {
            "success": True,
            "message": f"موضوع '{clean_key}' با موفقیت در حافظه بلندمدت ثبت شد.",
            "item": self.memories[clean_key]
        }

    def recall_facts(self, query: str = "") -> List[Dict[str, Any]]:
        """
        Searches remembered facts by query string or returns all facts if query is empty.
        """
        query_lower = query.strip().lower()
        results = []
        for k, item in self.memories.items():
            if not query_lower:
                results.append(item)
            elif (query_lower in k.lower() or
                  query_lower in item.get("value", "").lower() or
                  query_lower in item.get("category", "").lower()):
                results.append(item)
        return results

    def forget_fact(self, key: str) -> Dict[str, Any]:
        """
        Removes a specific memory item.
        """
        clean_key = key.strip()
        if clean_key in self.memories:
            popped = self.memories.pop(clean_key)
            self._save()
            logger.info(f"Memory deleted: {clean_key}")
            return {"success": True, "message": f"موضوع '{clean_key}' از حافظه حذف شد."}
        return {"success": False, "error": f"موردی با کلید '{clean_key}' در حافظه یافت نشد."}

    def clear_all_memories(self) -> Dict[str, Any]:
        """Wipes all remembered facts."""
        self.memories.clear()
        self._save()
        return {"success": True, "message": "حافظه به طور کامل پاک شد."}

    def get_prompt_context(self) -> str:
        """
        Generates a markdown section for injection into Gemini's system instructions.
        """
        if not self.memories:
            return ""

        lines = [
            "\n### دانشنامه و حافظه بلندمدت ثبت‌شده از کاربر و سیستم:",
            "شما این اطلاعات را قبلاً به خاطر سپرده‌اید و باید در پاسخ‌ها و تصمیم‌گیری‌ها به کار ببرید:"
        ]
        for k, v in self.memories.items():
            lines.append(f"- **{k}** [{v.get('category', 'general')}]: {v.get('value', '')}")

        return "\n".join(lines) + "\n"

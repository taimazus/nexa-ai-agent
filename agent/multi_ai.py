import os
import json
import time
import logging
import urllib.request
import urllib.error
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
from agent.learning import LearningEngine

logger = logging.getLogger("NovaAgent.MultiAI")

DEFAULT_PEER_SETTINGS_PATH = Path(__file__).parent.parent / "data" / "peer_ai_settings.json"
DEFAULT_PEER_INSIGHTS_PATH = Path(__file__).parent.parent / "data" / "peer_insights.json"


class PeerProvider(str, Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    OPENROUTER = "openrouter"
    GEMINI_PEER = "gemini_peer"


class MultiAiCollaborator:
    """
    Multi-AI Interaction, Peer Code Review, and Self-Improvement Engine.
    Allows Nova to collaborate with other AI models (OpenAI, Claude, DeepSeek, local Ollama, OpenRouter),
    benchmark responses, detect bugs/flaws, and distill wisdom into its continuous learning engine.
    """

    def __init__(
        self,
        settings_path: Optional[str] = None,
        insights_path: Optional[str] = None,
        learning_engine: Optional[LearningEngine] = None
    ):
        self.settings_path = Path(settings_path) if settings_path else DEFAULT_PEER_SETTINGS_PATH
        self.insights_path = Path(insights_path) if insights_path else DEFAULT_PEER_INSIGHTS_PATH
        self.learning_engine = learning_engine or LearningEngine()

        self.active_provider: str = PeerProvider.OLLAMA.value
        self.providers: Dict[str, Dict[str, Any]] = {
            PeerProvider.OPENAI.value: {
                "name": "OpenAI (ChatGPT / GPT-4o)",
                "api_key": "",
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1"
            },
            PeerProvider.CLAUDE.value: {
                "name": "Anthropic Claude",
                "api_key": "",
                "model": "claude-3-5-sonnet-20241022",
                "base_url": "https://api.anthropic.com/v1"
            },
            PeerProvider.DEEPSEEK.value: {
                "name": "DeepSeek AI",
                "api_key": "",
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com/v1"
            },
            PeerProvider.OLLAMA.value: {
                "name": "Ollama (مدل‌های متن‌باز محلی بدون نیاز به کلید)",
                "api_key": "",
                "model": "llama3",
                "base_url": "http://localhost:11434"
            },
            PeerProvider.LM_STUDIO.value: {
                "name": "LM Studio (سرور محلی آفلاین بدون نیاز به کلید)",
                "api_key": "",
                "model": "local-model",
                "base_url": "http://localhost:1234/v1"
            },
            PeerProvider.OPENROUTER.value: {
                "name": "OpenRouter",
                "api_key": "",
                "model": "google/gemini-2.0-flash-exp:free",
                "base_url": "https://openrouter.ai/api/v1"
            },
            PeerProvider.GEMINI_PEER.value: {
                "name": "Gemini Peer (نسخه دوم برای راستی‌آزمایی)",
                "api_key": "",
                "model": "gemini-2.5-flash",
                "base_url": ""
            }
        }
        self.insights_history: List[Dict[str, Any]] = []

        self._load_settings()
        self._load_insights()

    def _load_settings(self):
        try:
            if self.settings_path.exists():
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.active_provider = data.get("active_provider", self.active_provider)
                    saved_providers = data.get("providers", {})
                    for k, v in saved_providers.items():
                        if k in self.providers:
                            self.providers[k].update(v)
            else:
                self._save_settings()
        except Exception as exc:
            logger.error(f"Error loading peer AI settings from {self.settings_path}: {exc}", exc_info=True)

    def _save_settings(self):
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "active_provider": self.active_provider,
                "providers": self.providers,
                "updated_at": time.time()
            }
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error(f"Error saving peer AI settings to {self.settings_path}: {exc}", exc_info=True)

    def _load_insights(self):
        try:
            if self.insights_path.exists():
                with open(self.insights_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.insights_history = data.get("insights", [])
            else:
                self.insights_history = []
        except Exception as exc:
            logger.error(f"Error loading peer insights from {self.insights_path}: {exc}", exc_info=True)
            self.insights_history = []

    def _save_insights(self):
        try:
            self.insights_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "insights": self.insights_history,
                "count": len(self.insights_history),
                "last_updated": time.time()
            }
            with open(self.insights_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error(f"Error saving peer insights to {self.insights_path}: {exc}", exc_info=True)

    def configure_provider(
        self,
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        p_key = provider.lower().strip()
        if p_key not in self.providers:
            self.providers[p_key] = {"name": provider, "api_key": "", "model": "", "base_url": ""}

        if api_key is not None:
            self.providers[p_key]["api_key"] = api_key.strip()
        if model is not None:
            self.providers[p_key]["model"] = model.strip()
        if base_url is not None:
            self.providers[p_key]["base_url"] = base_url.strip()

        self._save_settings()
        logger.info(f"Provider '{p_key}' reconfigured: model={self.providers[p_key].get('model')}")

    def set_active_provider(self, provider: str):
        p_key = provider.lower().strip()
        if p_key in self.providers:
            self.active_provider = p_key
            self._save_settings()
            logger.info(f"Active peer AI provider switched to: {p_key}")
        else:
            logger.warning(f"Unknown provider: {provider}")

    def consult_peer_ai(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        system_role: Optional[str] = None,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Queries an external peer AI provider and returns the structured response.
        """
        prov_key = (provider or self.active_provider).lower().strip()
        cfg = self.providers.get(prov_key, {})
        target_model = model or cfg.get("model") or "default"
        api_key = cfg.get("api_key", "").strip() or os.environ.get(f"{prov_key.upper()}_API_KEY", "")
        base_url = cfg.get("base_url", "").strip()

        logger.info(f"Consulting Peer AI [{prov_key}] (model: {target_model})...")

        effective_system_instruction = system_instruction or system_role or (
            "You are an expert peer AI assistant reviewing logic, software architecture, and facts. "
            "Provide objective, rigorous, and constructive analysis."
        )

        try:
            if prov_key == PeerProvider.CLAUDE.value:
                return self._call_claude_api(base_url, api_key, target_model, prompt, effective_system_instruction)
            elif prov_key == PeerProvider.OLLAMA.value:
                return self._call_ollama_api(base_url, target_model, prompt, effective_system_instruction)
            elif prov_key == PeerProvider.GEMINI_PEER.value:
                return self._call_gemini_peer(api_key, target_model, prompt, effective_system_instruction)
            else:
                # Default to OpenAI compatible format (OpenAI, DeepSeek, OpenRouter, Groq)
                return self._call_openai_compatible(base_url, api_key, target_model, prompt, effective_system_instruction, prov_key)
        except Exception as exc:
            logger.error(f"Error querying peer AI provider '{prov_key}': {exc}", exc_info=True)
            return {
                "success": False,
                "provider": prov_key,
                "model": target_model,
                "error": f"خطا در ارتباط با هوش مصنوعی همکار ({prov_key}): {str(exc)}",
                "reply": ""
            }

    def _call_openai_compatible(
        self,
        base_url: str,
        api_key: str,
        model: str,
        prompt: str,
        system_instruction: str,
        provider_name: str
    ) -> Dict[str, Any]:
        endpoint = f"{base_url.rstrip('/')}/chat/completions"
        if not endpoint.startswith("http"):
            endpoint = f"https://api.openai.com/v1/chat/completions"

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if provider_name == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/nova-desktop-agent"
            headers["X-Title"] = "Nova AI Desktop Assistant"

        payload = {
            "model": model or "gpt-4o",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=40) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            choices = res_json.get("choices", [])
            if choices:
                reply = choices[0].get("message", {}).get("content", "").strip()
                return {
                    "success": True,
                    "provider": provider_name,
                    "model": model,
                    "reply": reply,
                    "raw": res_json
                }
            return {
                "success": False,
                "provider": provider_name,
                "model": model,
                "error": "پاسخ معتبری از هوش مصنوعی همکار دریافت نشد.",
                "reply": ""
            }

    def _call_claude_api(
        self,
        base_url: str,
        api_key: str,
        model: str,
        prompt: str,
        system_instruction: str
    ) -> Dict[str, Any]:
        endpoint = f"{base_url.rstrip('/')}/messages" if base_url else "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": model or "claude-3-5-sonnet-20241022",
            "max_tokens": 2048,
            "system": system_instruction,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=40) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            content_items = res_json.get("content", [])
            reply_text = "".join(item.get("text", "") for item in content_items if item.get("type") == "text").strip()
            return {
                "success": True,
                "provider": "claude",
                "model": model,
                "reply": reply_text,
                "raw": res_json
            }

    def _call_ollama_api(
        self,
        base_url: str,
        model: str,
        prompt: str,
        system_instruction: str
    ) -> Dict[str, Any]:
        endpoint = f"{base_url.rstrip('/')}/api/chat" if base_url else "http://localhost:11434/api/chat"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": model or "llama3",
            "stream": False,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=45) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            reply = res_json.get("message", {}).get("content", "").strip()
            return {
                "success": True,
                "provider": "ollama",
                "model": model,
                "reply": reply,
                "raw": res_json
            }

    def _call_gemini_peer(
        self,
        api_key: str,
        model: str,
        prompt: str,
        system_instruction: str
    ) -> Dict[str, Any]:
        try:
            from google import genai
            client = genai.Client(api_key=api_key) if api_key else genai.Client()
            response = client.models.generate_content(
                model=model or "gemini-2.5-flash",
                contents=prompt,
                config={"system_instruction": system_instruction}
            )
            return {
                "success": True,
                "provider": "gemini_peer",
                "model": model,
                "reply": response.text.strip(),
                "raw": {}
            }
        except Exception as exc:
            logger.error(f"Error in Gemini Peer: {exc}", exc_info=True)
            return {
                "success": False,
                "provider": "gemini_peer",
                "model": model,
                "error": f"خطا در Gemini Peer: {str(exc)}",
                "reply": ""
            }

    def peer_code_review(
        self,
        code: str,
        language: str = "python",
        context: str = "",
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends code to a peer AI model specifically asking to detect bugs, flaws,
        security risks, and performance traps.
        """
        prompt = (
            f"لطفاً کد زیر را با دقت بالا بازبینی (Code Review) کن و ایرادات، باگ‌ها، و نقاط ضعف آن را شناسایی کن:\n\n"
            f"**زبان:** {language}\n"
            f"**زمینه/هدف:** {context or 'انجام وظایف در سیستم‌عامل ویندوز'}\n\n"
            f"```{language}\n{code}\n```\n\n"
            f"لطفاً در پاسخ موارد زیر را به طور تفکیک‌شده و دقیق بیان کن:\n"
            f"۱. باگ‌های احتمالی یا خطاهای زمان اجرا (Edge Cases & Runtime Errors)\n"
            f"۲. نقاط ضعف امنیتی یا نشت منابع (Security & Resource Leaks)\n"
            f"۳. راه‌حل اصلاحی و کد پیشنهادی بهبودیافته"
        )
        sys_role = "تو یک مهندس ارشد و داور کد با استانداردهای سخت‌گیرانه هستی. وظیفه تو پیدا کردن باگ‌ها و ایرادات پنهان در کدها است."
        res = self.consult_peer_ai(prompt=prompt, provider=provider, system_role=sys_role)
        if res.get("success"):
            return {
                "success": True,
                "provider": res.get("provider"),
                "review": res.get("reply", ""),
                "code": code
            }
        return res

    def learn_from_peer_ai(
        self,
        topic: str,
        peer_advice: str,
        category: str = "peer_critique"
    ) -> Dict[str, Any]:
        """
        Distills wisdom, advice, or correction received from another AI and records
        it into Nova's permanent LearningEngine.
        """
        clean_topic = topic.strip()
        clean_advice = peer_advice.strip()
        if not clean_topic or not clean_advice:
            return {"success": False, "error": "موضوع یا نصیحت هوش مصنوعی همکار نمی‌تواند خالی باشد."}

        rule_text = f"[درس آموخته‌شده از هوش مصنوعی همکار]: {clean_advice}"
        rec_res = self.learning_engine.record_learning(
            trigger=clean_topic,
            corrective_rule=rule_text,
            category=category
        )

        # Log into insights history
        insight_item = {
            "id": f"ins_{int(time.time() * 1000)}",
            "topic": clean_topic,
            "advice": clean_advice,
            "category": category,
            "created_at": time.time(),
            "date_str": time.strftime("%Y-%m-%d %H:%M")
        }
        self.insights_history.append(insight_item)
        self._save_insights()

        logger.info(f"Distilled learning from peer AI on '{clean_topic}' recorded successfully.")
        return {
            "success": True,
            "message": f"درس آموخته‌شده از هوش مصنوعی همکار با موفقیت در قوانین دائمی ذخیره شد.",
            "rule": rule_text,
            "learning_result": rec_res
        }

    def run_self_improvement(
        self,
        focus_area: str = "general",
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Self-Improvement Protocol: Asks a peer AI to evaluate Nova's operational guidelines,
        find blind spots, and propose 2-3 concrete golden rules for self-advancement.
        """
        current_learnings = self.learning_engine.query_learnings()
        learnings_summary = "\n".join(
            f"- {item.get('trigger')}: {item.get('rule')}"
            for item in current_learnings[:10]
        ) or "هنوز قانونی ثبت نشده است."

        prompt = (
            f"من یک دستیار هوشمند دسکتاپ به نام نوا (Nova) هستم که کارهای سیستم‌عامل ویندوز، کدنویسی، و دستیاری کاربر را انجام می‌دهم.\n"
            f"حوزه تمرکز برای بهبود: **{focus_area}**\n\n"
            f"بخشی از تجربیات و قوانین فعلی من:\n{learnings_summary}\n\n"
            f"لطفاً نقاط کور (Blind Spots)، اشتباهات محتمل در این حوزه، و ۳ راهکار عملی برای بهتر شدن عملکرد من را پیشنهاد بده. "
            f"پاسخ باید کاربردی، دقیق و بدون کلی‌گویی باشد."
        )

        res = self.consult_peer_ai(
            prompt=prompt,
            provider=provider,
            system_role="تو یک مشاور ارشد سیستم‌های خودمختار و هوش مصنوعی هستی که به ارتقا و بهبود سایر مدل‌ها کمک می‌کنی."
        )

        if res.get("success"):
            plan = res.get("reply", "")
            insight_record = {
                "id": f"selfimp_{int(time.time() * 1000)}",
                "focus_area": focus_area,
                "provider": res.get("provider"),
                "model": res.get("model"),
                "plan": plan,
                "created_at": time.time(),
                "date_str": time.strftime("%Y-%m-%d %H:%M")
            }
            self.insights_history.append(insight_record)
            self._save_insights()

            return {
                "success": True,
                "focus_area": focus_area,
                "provider": res.get("provider"),
                "improvement_plan": plan
            }
        return res

    def get_insights_history(self) -> List[Dict[str, Any]]:
        return list(self.insights_history)

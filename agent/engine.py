import os
import logging
from typing import Dict, Any, Callable, Optional, List
from google import genai
from google.genai import types

from agent.config import DEFAULT_MODEL, SYSTEM_INSTRUCTION
from agent.key_manager import KeyManager
from agent.memory import MemoryManager
from agent.persona import PersonaManager
from agent.learning import LearningEngine
from agent.multi_ai import MultiAiCollaborator, PeerProvider
from agent.family.manager import FamilyManager
from agent.family.app_controller import AppController
from agent.integrations.config_manager import ServicesConfigManager
from agent.integrations.email_client import EmailService
from agent.integrations.social_manager import SocialMediaManager
from agent import tools

logger = logging.getLogger("NovaAgent.Engine")


class AgentEngine:
    """
    Core AI Agent powered by Google Gemini 2.5 Flash, resilient API key rotation,
    persistent long-term memory, persona adaptation, continuous self-learning,
    multi-AI peer collaboration, and hierarchical AI Family Ecosystem.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        key_manager: Optional[KeyManager] = None,
        memory_manager: Optional[MemoryManager] = None,
        persona_manager: Optional[PersonaManager] = None,
        learning_engine: Optional[LearningEngine] = None,
        multi_ai: Optional[MultiAiCollaborator] = None,
        family_manager: Optional[FamilyManager] = None,
        on_state_change: Optional[Callable[[str], None]] = None,
        on_status_update: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, Dict[str, Any], Dict[str, Any]], None]] = None,
        on_quota_warning: Optional[Callable[[str, str], None]] = None,
        on_family_member_changed: Optional[Callable[[Any], None]] = None
    ):
        self.key_manager = key_manager or KeyManager(default_key=api_key)
        self.memory_manager = memory_manager or MemoryManager()
        self.persona_manager = persona_manager or PersonaManager()
        self.learning_engine = learning_engine or LearningEngine()
        self.multi_ai = multi_ai or MultiAiCollaborator(learning_engine=self.learning_engine)
        self.family_manager = family_manager or FamilyManager()
        self.app_controller = AppController()
        self.services_config = ServicesConfigManager()
        self.email_service = EmailService(config_manager=self.services_config)
        self.social_manager = SocialMediaManager(config_manager=self.services_config)
        self.model_name = model_name
        self.on_state_change = on_state_change
        self.on_status_update = on_status_update
        self.on_tool_call = on_tool_call
        self.on_quota_warning = on_quota_warning
        self.on_family_member_changed = on_family_member_changed
        self.conversation_history: List[Dict[str, str]] = []

        # Current active key
        self.api_key = self.key_manager.get_active_key() or api_key or os.environ.get("GEMINI_API_KEY")

        self.tools_map = {
            "execute_powershell": tools.execute_powershell,
            "execute_python": tools.execute_python,
            "file_operations": tools.file_operations,
            "system_diagnostics": tools.system_diagnostics,
            "fetch_url": tools.fetch_url,
            "open_app_or_url": tools.open_app_or_url,
            "capture_screenshot": tools.capture_screenshot,
            "capture_webcam": tools.capture_webcam,
            "list_installed_apps": tools.list_installed_apps,
            "list_open_windows": tools.list_open_windows,
            "launch_or_focus_app": tools.launch_or_focus_app,
            "send_app_keys": tools.send_app_keys,
            "send_keys": tools.send_app_keys,
            "click_screen": tools.click_screen,
            "close_app": tools.close_app,
            "switch_family_member": self.family_manager.switch_member,
            "teach_family_skill": self.family_manager.teach_member_skill,
            "list_family_members": self.family_manager.list_family_members,
            "customize_family_member": self.family_manager.update_member,
            "add_family_member": self.family_manager.add_member,
            "remember_family_fact": self.family_manager.remember_member_fact,
            "recall_family_facts": self.family_manager.recall_member_facts,
            "check_emails": self.email_service.check_emails,
            "send_email": self.email_service.send_email,
            "configure_email_settings": self.services_config.update_email_config,
            "plan_instagram_content": self.social_manager.plan_content,
            "open_instagram": self.social_manager.open_instagram,
            "copy_caption_to_clipboard": self.social_manager.copy_caption_to_clipboard,
            "inspect_app_ui": self.app_controller.inspect_app_ui,
            "invoke_app_element": self.app_controller.invoke_app_element,
            "learn_app_workflow": self.app_controller.learn_workflow,
            "list_app_workflows": self.app_controller.list_workflows,
            "execute_app_workflow": self.app_controller.execute_workflow,
            "remember_fact": self.memory_manager.remember_fact,
            "recall_facts": self.memory_manager.recall_facts,
            "forget_fact": self.memory_manager.forget_fact,
            "record_learning": self.learning_engine.record_learning,
            "query_learnings": self.learning_engine.query_learnings,
            "consult_peer_ai": self.multi_ai.consult_peer_ai,
            "review_code_with_peer": self.multi_ai.peer_code_review,
            "learn_from_peer_ai": self.multi_ai.learn_from_peer_ai,
            "run_self_improvement": self.multi_ai.run_self_improvement
        }

        self._init_client_and_chat()

    def _init_client_and_chat(self, past_history: Optional[List[types.Content]] = None):
        """Initializes genai.Client and the chat session with tools and memory context."""
        logger.info(f"Initializing Gemini Client with key: {self.api_key[:8] if self.api_key else 'None'}... and model: {self.model_name}")
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = genai.Client()

        # Build combined system instruction with persona, long-term memory, learned rules, and family member role
        active_fam = self.family_manager.get_active_member()
        combined_instruction = (
            self.persona_manager.get_persona_prompt() + "\n\n" +
            SYSTEM_INSTRUCTION + "\n\n" +
            active_fam.get_prompt_context() + "\n\n" +
            self.memory_manager.get_prompt_context() + "\n" +
            self.learning_engine.get_prompt_injection()
        )

        # Wrapped tool functions that notify UI
        def wrapped_powershell(command: str) -> Dict[str, Any]:
            """Executes a PowerShell command on Windows and returns stdout/stderr."""
            self._notify_tool("execute_powershell", f"اجرای دستور پاوئرشل: {command[:60]}")
            res = tools.execute_powershell(command)
            if not res.get("success"):
                self.learning_engine.auto_learn_from_failure("execute_powershell", {"command": command}, res.get("stderr", ""))
            self._notify_tool_done("execute_powershell", {"command": command}, res)
            return res

        def wrapped_python(code: str) -> Dict[str, Any]:
            """Executes a snippet of Python code and returns output or error."""
            self._notify_tool("execute_python", "اجرای کد پایتون...")
            res = tools.execute_python(code)
            if not res.get("success"):
                self.learning_engine.auto_learn_from_failure("execute_python", {"code": code}, res.get("error", ""))
            self._notify_tool_done("execute_python", {"code": code}, res)
            return res

        def wrapped_files(action: str, path: str, content: Optional[str] = None) -> Dict[str, Any]:
            """Reads, writes, lists, or checks files and directories on Windows."""
            self._notify_tool("file_operations", f"عملیات فایل ({action}): {os.path.basename(path)}")
            res = tools.file_operations(action, path, content)
            self._notify_tool_done("file_operations", {"action": action, "path": path}, res)
            return res

        def wrapped_diagnostics() -> Dict[str, Any]:
            """Gets current Windows system health info: OS, CPU, RAM, and Disk."""
            self._notify_tool("system_diagnostics", "بررسی وضعیت سیستم و رم...")
            res = tools.system_diagnostics()
            self._notify_tool_done("system_diagnostics", {}, res)
            return res

        def wrapped_fetch(url: str) -> Dict[str, Any]:
            """Fetches and extracts clean text content from a webpage URL."""
            self._notify_tool("fetch_url", f"در حال خواندن وب: {url[:50]}")
            res = tools.fetch_url(url)
            self._notify_tool_done("fetch_url", {"url": url}, res)
            return res

        def wrapped_open(target: str) -> Dict[str, Any]:
            """Opens an application, file, or URL in Windows."""
            self._notify_tool("open_app_or_url", f"باز کردن: {target}")
            res = tools.open_app_or_url(target)
            self._notify_tool_done("open_app_or_url", {"target": target}, res)
            return res

        def wrapped_screenshot() -> Dict[str, Any]:
            """Captures a screenshot of the user's desktop."""
            self._notify_tool("capture_screenshot", "ثبت تصویر از صفحه دسکتاپ...")
            res = tools.capture_screenshot()
            self._notify_tool_done("capture_screenshot", {}, res)
            return res

        def wrapped_webcam(camera_index: int = 0) -> Dict[str, Any]:
            """Captures a frame from the connected webcam to see the real world or user."""
            self._notify_tool("capture_webcam", "ثبت تصویر از دوربین وب‌کم...")
            res = tools.capture_webcam(camera_index=camera_index)
            self._notify_tool_done("capture_webcam", {"camera_index": camera_index}, res)
            return res

        def wrapped_remember(key: str, value: str, category: str = "general") -> Dict[str, Any]:
            """Saves a permanent fact, note, or preference into long-term memory."""
            self._notify_tool("remember_fact", f"ثبت در حافظه: {key}")
            res = self.memory_manager.remember_fact(key, value, category)
            active_m = self.family_manager.get_active_member()
            if active_m:
                active_m.remember_fact(key, value)
                self.family_manager.save_profiles()
            self._notify_tool_done("remember_fact", {"key": key, "value": value}, res)
            return res

        def wrapped_recall(query: str = "") -> List[Dict[str, Any]]:
            """Recalls facts, notes, or preferences from long-term memory."""
            self._notify_tool("recall_facts", "بازیابی اطلاعات از حافظه...")
            res = self.memory_manager.recall_facts(query)
            self._notify_tool_done("recall_facts", {"query": query}, {"count": len(res)})
            return res

        def wrapped_forget(key: str) -> Dict[str, Any]:
            """Deletes a fact from long-term memory."""
            self._notify_tool("forget_fact", f"حذف از حافظه: {key}")
            res = self.memory_manager.forget_fact(key)
            active_m = self.family_manager.get_active_member()
            if active_m and key in active_m.memories:
                del active_m.memories[key]
                self.family_manager.save_profiles()
            self._notify_tool_done("forget_fact", {"key": key}, res)
            return res

        def wrapped_record_learning(trigger: str, corrective_rule: str, category: str = "general") -> Dict[str, Any]:
            """Records a lesson learned from a mistake or correction to prevent repeating it."""
            self._notify_tool("record_learning", f"یادگیری درس جدید: {trigger[:40]}")
            res = self.learning_engine.record_learning(trigger, corrective_rule, category)
            active_m = self.family_manager.get_active_member()
            if active_m:
                active_m.gain_xp(30)
                self.family_manager.save_profiles()
            self._notify_tool_done("record_learning", {"trigger": trigger, "rule": corrective_rule}, res)
            return res

        def wrapped_query_learnings(query: str = "") -> List[Dict[str, Any]]:
            """Queries past lessons and learned rules from previous executions and mistakes."""
            self._notify_tool("query_learnings", "بررسی درس‌ها و تجربیات گذشته...")
            res = self.learning_engine.query_learnings(query)
            self._notify_tool_done("query_learnings", {"query": query}, {"count": len(res)})
            return res

        def wrapped_consult_peer(prompt: str, provider: Optional[str] = None) -> Dict[str, Any]:
            """Consults an external peer AI (OpenAI GPT-4o, Claude, DeepSeek, or local Ollama) for peer analysis."""
            self._notify_tool("consult_peer_ai", f"مشورت با هوش مصنوعی همکار ({provider or 'پیش‌فرض'})...")
            res = self.multi_ai.consult_peer_ai(prompt=prompt, provider=provider)
            self._notify_tool_done("consult_peer_ai", {"prompt": prompt[:50]}, {"success": res.get("success")})
            return res

        def wrapped_peer_code_review(code: str, language: str = "python", context: str = "") -> Dict[str, Any]:
            """Submits code to a peer AI to find subtle bugs, security vulnerabilities, and logic flaws."""
            self._notify_tool("review_code_with_peer", f"درخواست بازبینی و باگ‌یابی کد از هوش مصنوعی همکار...")
            res = self.multi_ai.peer_code_review(code=code, language=language, context=context)
            self._notify_tool_done("review_code_with_peer", {"language": language}, {"success": res.get("success")})
            return res

        def wrapped_learn_from_peer(topic: str, peer_advice: str, category: str = "peer_critique") -> Dict[str, Any]:
            """Distills a best practice or critique from another AI into Nova's permanent learned rules."""
            self._notify_tool("learn_from_peer_ai", f"یادگیری و ثبت درس از هوش مصنوعی همکار: {topic[:40]}")
            res = self.multi_ai.learn_from_peer_ai(topic=topic, peer_advice=peer_advice, category=category)
            self._notify_tool_done("learn_from_peer_ai", {"topic": topic}, res)
            return res

        def wrapped_self_improve(focus_area: str = "general") -> Dict[str, Any]:
            """Triggers autonomous self-improvement loop: reviews recent performance with a peer AI and formulates golden rules."""
            self._notify_tool("run_self_improvement", f"اجرای حلقه خودبهبودبخشی (Self-Improvement): {focus_area}")
            res = self.multi_ai.run_self_improvement(focus_area=focus_area)
            self._notify_tool_done("run_self_improvement", {"focus_area": focus_area}, {"success": res.get("success")})
            return res

        def wrapped_list_apps(query: Optional[str] = None) -> Dict[str, Any]:
            """Scans Windows Registry and Start Menu to list all installed applications on the computer."""
            self._notify_tool("list_installed_apps", f"جستجوی نرم‌افزارهای نصب‌شده: {query or 'همه'}")
            res = tools.list_installed_apps(query=query)
            self._notify_tool_done("list_installed_apps", {"query": query}, {"count": res.get("count", 0)})
            return res

        def wrapped_list_windows() -> Dict[str, Any]:
            """Lists all currently active and open application windows on the desktop."""
            self._notify_tool("list_open_windows", "مشاهده پنجره‌ها و برنامه‌های در حال اجرا...")
            res = tools.list_open_windows()
            self._notify_tool_done("list_open_windows", {}, {"count": res.get("count", 0)})
            return res

        def wrapped_launch_or_focus(app_name_or_path: str) -> Dict[str, Any]:
            """Launches an application or brings its open window to the foreground."""
            self._notify_tool("launch_or_focus_app", f"باز کردن یا فوکوس روی برنامه: {app_name_or_path}")
            res = tools.launch_or_focus_app(app_name_or_path=app_name_or_path)
            self._notify_tool_done("launch_or_focus_app", {"app": app_name_or_path}, res)
            return res

        def send_app_keys(keys_or_text: Optional[str] = None, hotkey: Optional[str] = None, app_name_or_title: Optional[str] = None) -> Dict[str, Any]:
            """Sends hotkeys (e.g. 'ctrl+s', 'alt+f4', 'enter') or types text into an application window."""
            target_desc = f" در {app_name_or_title}" if app_name_or_title else ""
            desc = f"ارسال کلید {hotkey}{target_desc}" if hotkey else f"تایپ متن{target_desc}"
            self._notify_tool("send_app_keys", desc)
            res = tools.send_app_keys(keys_or_text=keys_or_text, hotkey=hotkey, app_name_or_title=app_name_or_title)
            self._notify_tool_done("send_app_keys", {"hotkey": hotkey, "app": app_name_or_title}, res)
            return res

        def send_keys(keys_or_text: Optional[str] = None, hotkey: Optional[str] = None, app_name_or_title: Optional[str] = None) -> Dict[str, Any]:
            """Sends hotkeys (e.g. 'ctrl+s', 'alt+f4', 'enter') or types text into an application window."""
            return send_app_keys(keys_or_text=keys_or_text, hotkey=hotkey, app_name_or_title=app_name_or_title)

        wrapped_send_keys = send_app_keys

        def wrapped_click(x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1, app_name_or_title: Optional[str] = None) -> Dict[str, Any]:
            """Clicks the mouse at specified coordinates or inside an application."""
            self._notify_tool("click_screen", f"کلیک ماوس ({button})")
            res = tools.click_screen(x=x, y=y, button=button, clicks=clicks, app_name_or_title=app_name_or_title)
            self._notify_tool_done("click_screen", {"x": x, "y": y, "button": button}, res)
            return res

        def wrapped_close_app(process_name_or_title: str, force: bool = False) -> Dict[str, Any]:
            """Gracefully closes or forcefully terminates an application."""
            self._notify_tool("close_app", f"بستن برنامه: {process_name_or_title}")
            res = tools.close_app(process_name_or_title=process_name_or_title, force=force)
            self._notify_tool_done("close_app", {"target": process_name_or_title, "force": force}, res)
            return res

        def wrapped_switch_family(member_name: str) -> Dict[str, Any]:
            """Switches the active persona to another NexA family member."""
            self._notify_tool("switch_family_member", f"تغییر به عضو خانواده: {member_name}")
            member = self.family_manager.switch_member(member_name)
            if member:
                if self.on_family_member_changed:
                    self.on_family_member_changed(member)
                res = {"success": True, "active_member": member.name, "role": member.role_title, "level": member.level}
            else:
                res = {"success": False, "error": f"عضو خانواده با نام '{member_name}' یافت نشد."}
            self._notify_tool_done("switch_family_member", {"member_name": member_name}, res)
            return res

        def wrapped_teach_family(member_name: str, skill_name: str, steps: str) -> Dict[str, Any]:
            """Teaches a family member or child a new specialized skill with steps."""
            self._notify_tool("teach_family_skill", f"آموزش مهارت جدید به {member_name}: {skill_name}")
            res = self.family_manager.teach_member_skill(member_name, skill_name, steps)
            self._notify_tool_done("teach_family_skill", {"member": member_name, "skill": skill_name}, res)
            return res

        def wrapped_list_family() -> List[Dict[str, Any]]:
            """Lists all members of the NexA AI Family and their specialties."""
            self._notify_tool("list_family_members", "مشاهده اعضای خانواده نِکسا...")
            res = self.family_manager.list_family_members()
            self._notify_tool_done("list_family_members", {}, {"count": len(res)})
            return res

        def wrapped_customize_family(
            member_name: str,
            new_name: Optional[str] = None,
            gender: Optional[str] = None,
            mood: Optional[str] = None,
            role_title: Optional[str] = None,
            avatar_style: Optional[str] = None,
            bio: Optional[str] = None
        ) -> Dict[str, Any]:
            """Customizes an existing family member's name, gender, mood, role title, avatar, and bio."""
            self._notify_tool("customize_family_member", f"شخصی‌سازی عضو خانواده: {member_name}")
            update_kwargs = {}
            if new_name:
                update_kwargs["name"] = new_name
            if gender:
                update_kwargs["gender"] = gender
            if mood:
                update_kwargs["mood"] = mood
            if role_title:
                update_kwargs["role_title"] = role_title
            if avatar_style:
                update_kwargs["avatar_style"] = avatar_style
            if bio:
                update_kwargs["bio"] = bio

            res = self.family_manager.update_member(member_name, **update_kwargs)
            active_m = self.family_manager.get_active_member()
            if self.on_family_member_changed:
                self.on_family_member_changed(active_m)
            self._notify_tool_done("customize_family_member", {"member": member_name}, res)
            return res

        def wrapped_add_family(
            name: str,
            gender: str,
            role_title: str,
            mood: Optional[str] = "friendly",
            avatar_style: Optional[str] = "cyber_bot",
            bio: Optional[str] = ""
        ) -> Dict[str, Any]:
            """Adds a brand new member to the NexA AI Family roster."""
            self._notify_tool("add_family_member", f"افزودن عضو جدید به خانواده: {name}")
            member_data = {
                "name": name,
                "gender": gender,
                "role_title": role_title,
                "mood": mood or "friendly",
                "avatar_style": avatar_style or "cyber_bot",
                "bio": bio or f"عضو جدید خانواده نِکسا متخصص {role_title}",
                "role": "child_specialist",
                "specialties": [role_title]
            }
            res = self.family_manager.add_member(member_data)
            self._notify_tool_done("add_family_member", {"name": name}, res)
            return res

        def wrapped_check_emails(unread_only: bool = True, limit: int = 10, folder: str = "INBOX") -> Dict[str, Any]:
            """Connects to user's email via IMAP, checks unread/read emails, detects important ones."""
            self._notify_tool("check_emails", "در حال بررسی صندوق ایمیل‌ها...")
            res = self.email_service.check_emails(folder=folder, unread_only=unread_only, limit=limit)
            self._notify_tool_done("check_emails", {"unread_only": unread_only, "limit": limit}, res)
            return res

        def wrapped_send_email(to_address: str, subject: str, body: str) -> Dict[str, Any]:
            """Sends an email securely using the configured SMTP server."""
            self._notify_tool("send_email", f"ارسال ایمیل به {to_address}...")
            res = self.email_service.send_email(to_address=to_address, subject=subject, body=body)
            self._notify_tool_done("send_email", {"to": to_address, "subject": subject}, res)
            return res

        def wrapped_configure_email(
            email_address: Optional[str] = None,
            app_password: Optional[str] = None,
            provider: Optional[str] = None,
            imap_server: Optional[str] = None,
            smtp_server: Optional[str] = None
        ) -> Dict[str, Any]:
            """Configures and permanently saves email settings."""
            self._notify_tool("configure_email_settings", "ذخیره تنظیمات حساب ایمیل...")
            res = self.services_config.update_email_config(
                email_address=email_address,
                app_password=app_password,
                provider=provider,
                imap_server=imap_server,
                smtp_server=smtp_server
            )
            self._notify_tool_done("configure_email_settings", {"provider": provider}, res)
            return res

        def wrapped_plan_instagram(topic: str, content_type: str = "reels") -> Dict[str, Any]:
            """Creates an Instagram viral Reels scenario, caption with hashtags, and hook."""
            self._notify_tool("plan_instagram_content", f"سناریونویسی محتوای اینستاگرام: {topic}")
            res = self.social_manager.plan_content(topic=topic, content_type=content_type)
            self._notify_tool_done("plan_instagram_content", {"topic": topic}, res)
            return res

        def wrapped_open_instagram(page: str = "home") -> Dict[str, Any]:
            """Opens Instagram page (home, dms, explore, create) in user's browser."""
            self._notify_tool("open_instagram", f"باز کردن اینستاگرام: {page}")
            res = self.social_manager.open_instagram(page=page)
            self._notify_tool_done("open_instagram", {"page": page}, res)
            return res

        def wrapped_copy_caption(caption: str) -> Dict[str, Any]:
            """Copies caption and hashtags to clipboard."""
            self._notify_tool("copy_caption_to_clipboard", "کپی کپشن در کلیپ‌بورد ویندوز...")
            res = self.social_manager.copy_caption_to_clipboard(caption=caption)
            self._notify_tool_done("copy_caption_to_clipboard", {}, res)
            return res

        def wrapped_inspect_ui(window_title: str, control_type: Optional[str] = None, max_elements: int = 30) -> Dict[str, Any]:
            """Uses Windows UI Automation to inspect controls of a window."""
            self._notify_tool("inspect_app_ui", f"بررسی المان‌ها و کنترل‌های پنجره: {window_title}")
            res = self.app_controller.inspect_app_ui(window_title=window_title, control_type=control_type, max_elements=max_elements)
            self._notify_tool_done("inspect_app_ui", {"window": window_title}, {"count": len(res.get("elements", []))})
            return res

        def wrapped_invoke_element(window_title: str, element_name: Optional[str] = None, automation_id: Optional[str] = None) -> Dict[str, Any]:
            """Clicks or invokes an element in an app by name or AutomationId."""
            self._notify_tool("invoke_app_element", f"کلیک روی دکمه/المان {element_name or automation_id} در {window_title}...")
            res = self.app_controller.invoke_app_element(window_title=window_title, element_name=element_name, automation_id=automation_id)
            self._notify_tool_done("invoke_app_element", {"element": element_name or automation_id}, res)
            return res

        def wrapped_learn_workflow(app_name: str, workflow_name: str, description: str, steps: str) -> Dict[str, Any]:
            """Learns and persists a multi-step macro workflow for an app."""
            self._notify_tool("learn_app_workflow", f"یادگیری و ثبت گردش‌کار جدید برای {app_name}: {workflow_name}")
            import json as py_json
            try:
                parsed_steps = py_json.loads(steps) if isinstance(steps, str) else steps
            except Exception:
                parsed_steps = [{"action": "send_keys", "text": steps}]
            res = self.app_controller.learn_workflow(app_name=app_name, workflow_name=workflow_name, description=description, steps=parsed_steps)
            self._notify_tool_done("learn_app_workflow", {"workflow": workflow_name}, res)
            return res

        def wrapped_list_workflows(app_name: Optional[str] = None) -> List[Dict[str, Any]]:
            """Lists all learned application workflows and macros."""
            self._notify_tool("list_app_workflows", "مشاهده گردش‌کارهای یادگرفته‌شده...")
            res = self.app_controller.list_workflows(app_name=app_name)
            self._notify_tool_done("list_app_workflows", {}, {"count": len(res)})
            return res

        def wrapped_execute_workflow(workflow_name: str, parameters: Optional[str] = None) -> Dict[str, Any]:
            """Executes a previously learned workflow with parameters."""
            self._notify_tool("execute_app_workflow", f"اجرای خودکار گردش‌کار: {workflow_name}")
            import json as py_json
            parsed_params = {}
            if parameters:
                try:
                    parsed_params = py_json.loads(parameters) if isinstance(parameters, str) else parameters
                except Exception as parse_err:
                    logger.warning(f"Failed to parse parameters JSON string for workflow '{workflow_name}': {parse_err}")
                    parsed_params = {}
            res = self.app_controller.execute_workflow(workflow_name=workflow_name, parameters=parsed_params)
            self._notify_tool_done("execute_app_workflow", {"workflow": workflow_name}, res)
            return res

        self.callable_tools = [
            wrapped_powershell,
            wrapped_python,
            wrapped_files,
            wrapped_diagnostics,
            wrapped_fetch,
            wrapped_open,
            wrapped_screenshot,
            wrapped_webcam,
            wrapped_list_apps,
            wrapped_list_windows,
            wrapped_launch_or_focus,
            send_app_keys,
            send_keys,
            wrapped_send_keys,
            wrapped_click,
            wrapped_close_app,
            wrapped_switch_family,
            wrapped_teach_family,
            wrapped_list_family,
            wrapped_customize_family,
            wrapped_add_family,
            wrapped_check_emails,
            wrapped_send_email,
            wrapped_configure_email,
            wrapped_plan_instagram,
            wrapped_open_instagram,
            wrapped_copy_caption,
            wrapped_inspect_ui,
            wrapped_invoke_element,
            wrapped_learn_workflow,
            wrapped_list_workflows,
            wrapped_execute_workflow,
            wrapped_remember,
            wrapped_recall,
            wrapped_forget,
            wrapped_record_learning,
            wrapped_query_learnings,
            wrapped_consult_peer,
            wrapped_peer_code_review,
            wrapped_learn_from_peer,
            wrapped_self_improve
        ]

        # Convert conversation history to types.Content if recreating session
        history_contents = past_history or []
        if not history_contents and self.conversation_history:
            for turn in self.conversation_history:
                history_contents.append(
                    types.Content(role="user", parts=[types.Part.from_text(text=turn["user"])])
                )
                history_contents.append(
                    types.Content(role="model", parts=[types.Part.from_text(text=turn["agent"])])
                )

        self.chat = self.client.chats.create(
            model=self.model_name,
            history=history_contents if history_contents else None,
            config=types.GenerateContentConfig(
                system_instruction=combined_instruction,
                temperature=0.7,
                tools=self.callable_tools
            )
        )

    def _notify_tool(self, tool_name: str, friendly_status: str):
        if self.on_state_change:
            self.on_state_change("working")
        if self.on_status_update:
            self.on_status_update(friendly_status)

    def _notify_tool_done(self, tool_name: str, args: Dict[str, Any], result: Dict[str, Any]):
        if self.on_tool_call:
            self.on_tool_call(tool_name, args, result)

    def dispatch_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Directly dispatches a tool by name (used for unit testing or direct trigger)."""
        if tool_name not in self.tools_map:
            logger.error(f"Unknown tool attempted: {tool_name}")
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        try:
            func = self.tools_map[tool_name]
            return func(**args)
        except Exception as exc:
            logger.error(f"Error executing dispatched tool {tool_name}: {exc}", exc_info=True)
            return {"success": False, "error": str(exc)}

    @property
    def tools(self):
        return self.tools_map

    def process_user_message(
        self,
        message: str = "",
        image_path: Optional[str] = None,
        audio_path: Optional[str] = None
    ) -> str:
        """
        Sends user message to Gemini, coordinates tool executions, handles seamless
        failover across API keys while completely preserving conversational context.
        Supports multimodal text, image (screenshot/webcam), and audio (microphone).
        """
        if self.on_state_change:
            self.on_state_change("thinking")
        if self.on_status_update:
            self.on_status_update("در حال فکر کردن...")

        total_keys = max(1, len(self.key_manager.get_keys()))

        for attempt in range(total_keys):
            try:
                logger.info(f"Processing message (attempt {attempt + 1}/{total_keys}): {message[:80] if message else '[Voice/Media Prompt]'}")
                
                parts = []
                if message:
                    parts.append(message)
                if image_path and os.path.exists(image_path):
                    from PIL import Image
                    parts.append(Image.open(image_path))
                if audio_path and os.path.exists(audio_path):
                    with open(audio_path, "rb") as af:
                        audio_bytes = af.read()
                    parts.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"))

                if not parts:
                    parts.append("سلام")

                delegated_member = self.family_manager.get_active_member()
                if message:
                    delegated_member = self.family_manager.auto_delegate(message)
                    if self.on_family_member_changed:
                        self.on_family_member_changed(delegated_member)

                if len(parts) == 1 and isinstance(parts[0], str):
                    response = self.chat.send_message(message=parts[0])
                else:
                    response = self.chat.send_message(message=parts)

                if response.text:
                    reply_text = response.text
                else:
                    import random
                    dynamic_replies = [
                        "انجام شد! نتیجه آماده‌ست.",
                        "ردیف شد، کار رو دقیق انجام دادم.",
                        "حله! دستور رو کامل اجرا کردم.",
                        "تمام شد، هر کاری که لازم بود مرتب انجام شد.",
                        "فرمان اجرا شد و همه چیز روبه‌راهه."
                    ]
                    reply_text = random.choice(dynamic_replies)
                
                # Reward member with XP and save
                delegated_member.gain_xp(15)
                self.family_manager.save_profiles()

                if self.on_state_change:
                    self.on_state_change("speaking")
                if self.on_status_update:
                    self.on_status_update(reply_text[:60] + "..." if len(reply_text) > 60 else reply_text)
                    
                user_record = message if message else "🎤 [پیام صوتی میکروفون]"
                self.conversation_history.append({"user": user_record, "agent": reply_text})
                return reply_text

            except Exception as exc:
                err_str = str(exc).lower()
                logger.warning(f"Error on attempt {attempt + 1}: {exc}")
                
                # Check for quota exhaustion / auth / rate limit / transient 503 errors
                is_quota_error = any(indicator in err_str for indicator in [
                    "429", "quota", "exhausted", "rate", "403", "503", "500", "unavailable", "overloaded", "forbidden", "permission", "invalid"
                ])
                
                # If quota exhausted and more keys available, switch key and preserve history!
                if is_quota_error and len(self.key_manager.get_keys()) > 1 and attempt < total_keys - 1:
                    logger.info("Quota exhausted or key failed. Rotating to next API key in pool...")
                    new_key = self.key_manager.mark_current_failed(reason=str(exc))
                    health = self.key_manager.get_pool_health()
                    
                    if self.on_quota_warning and health.get("alert_message"):
                        self.on_quota_warning(health.get("severity", "warning"), health.get("alert_message", ""))

                    if new_key:
                        self.api_key = new_key
                        if self.on_status_update:
                            self.on_status_update(health.get("alert_message") or "🔄 اعتبار کلید تمام شد؛ انتقال به کلید بعدی...")
                        # Re-initialize chat with new key while passing existing history
                        self._init_client_and_chat()
                        continue

                # Check if offline fallback is possible using local AI (Ollama or LM Studio)
                if message:
                    offline_reply = self._try_offline_fallback(message, str(exc))
                    if offline_reply:
                        return offline_reply

                # If not quota error or last attempt, report failure
                health = self.key_manager.get_pool_health()
                if health.get("is_depleted") and self.on_quota_warning:
                    self.on_quota_warning("critical", health.get("alert_message", "اعتبار تمام کلیدها به پایان رسید!"))

                logger.error(f"Fatal error processing message: {exc}", exc_info=True)
                err_msg = f"متاسفانه در پردازش خطایی رخ داد: {str(exc)}"
                if health.get("is_depleted"):
                    err_msg = health.get("alert_message", err_msg)
                if self.on_state_change:
                    self.on_state_change("error")
                if self.on_status_update:
                    self.on_status_update("خطا یا اتمام اعتبار کلید!")
                return err_msg

    def _try_offline_fallback(self, message: str, original_error: str) -> Optional[str]:
        """
        Attempts to answer via local offline LLM (Ollama or LM Studio)
        when cloud API is unreachable or quotas are exhausted.
        """
        try:
            offline_candidates = [
                PeerProvider.OLLAMA.value,
                getattr(PeerProvider, "LM_STUDIO", None).value if hasattr(PeerProvider, "LM_STUDIO") else "lm_studio"
            ]
            prov_to_try = self.multi_ai.active_provider if self.multi_ai.active_provider in offline_candidates else PeerProvider.OLLAMA.value
            
            logger.info(f"Attempting offline fallback to local AI provider '{prov_to_try}'...")
            system_prompt = self.persona_manager.get_persona_prompt()
            res = self.multi_ai.consult_peer_ai(
                prompt=message,
                provider=prov_to_try,
                system_instruction=system_prompt
            )
            if res.get("success") and res.get("reply"):
                reply = res["reply"]
                model_used = res.get("model", "Local LLM")
                prov_display = "Ollama" if prov_to_try == "ollama" else "LM Studio"
                fallback_msg = (
                    f"📴 **[پاسخ آفلاین توسط هوش مصنوعی محلی ({prov_display} - {model_used})]**\n\n"
                    f"{reply}\n\n"
                    f"> 💡 *نکته: به دلیل عدم دسترسی به سرورهای ابری، این پاسخ به صورت کاملاً آفلاین و محلی توسط سخت‌افزار سیستم شما بدون نیاز به اینترنت پردازش شد.*"
                )
                if self.on_state_change:
                    self.on_state_change("speaking")
                if self.on_status_update:
                    self.on_status_update(f"پاسخ آفلاین از {model_used}")
                self.conversation_history.append({"user": message, "agent": fallback_msg})
                return fallback_msg
        except Exception as off_exc:
            logger.warning(f"Offline fallback to local AI failed or server not running: {off_exc}")
        return None

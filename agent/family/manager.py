import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List

from agent.family.member import FamilyMember

logger = logging.getLogger("NexA.Family.Manager")

DEFAULT_FAMILY_PATH = Path(__file__).parent.parent.parent / "data" / "family_profiles.json"


class FamilyManager:
    """
    Manages the multi-agent family ecosystem:
    - Loading & saving family member profiles
    - Smart dynamic task delegation (routing requests to the best-skilled family member)
    - Manual switching between family members
    - Skill teaching and inheritance across parents and children
    """

    def __init__(self, profiles_path: Optional[Path] = None):
        self.profiles_path = profiles_path or DEFAULT_FAMILY_PATH
        self.members: Dict[str, FamilyMember] = {}
        self.active_member_id: str = "nexanoo"
        self._lock = threading.Lock()
        self._load_profiles()

    def _load_profiles(self):
        """Loads family profiles from JSON file or initializes defaults."""
        try:
            if self.profiles_path.exists():
                with open(self.profiles_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.active_member_id = data.get("active_member_id", "nexanoo")
                members_data = data.get("members", {})
                for m_id, m_dict in members_data.items():
                    self.members[m_id] = FamilyMember(m_dict)
                logger.info(f"Loaded {len(self.members)} family members. Active: {self.active_member_id}")
            else:
                logger.warning(f"Family profiles file not found at {self.profiles_path}, using empty roster.")
        except Exception as exc:
            logger.error(f"Error loading family profiles: {exc}", exc_info=True)

    def save_profiles(self) -> bool:
        """Saves current state and learned skills of all family members to disk atomically."""
        with self._lock:
            try:
                self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
                data = {
                    "active_member_id": self.active_member_id,
                    "company_attribution": {
                        "name": "راهکار الکترونیک سهند",
                        "website": "https://irres.ir"
                    },
                    "members": {m_id: member.to_dict() for m_id, member in self.members.items()}
                }
                temp_file = self.profiles_path.with_suffix(".tmp")
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                temp_file.replace(self.profiles_path)
                logger.info("Saved family profiles and learned skills successfully.")
                return True
            except Exception as exc:
                logger.error(f"Failed to save family profiles: {exc}", exc_info=True)
                return False

    def get_active_member(self) -> FamilyMember:
        """Returns the currently active family member."""
        if self.active_member_id in self.members:
            return self.members[self.active_member_id]
        if self.members:
            fallback = next(iter(self.members.values()))
            return fallback
        # Minimal dummy if no members loaded
        return FamilyMember({"id": "nexanoo", "name": "نِکسانو", "role": "mother"})

    def find_member(self, target: str) -> Optional[FamilyMember]:
        """
        Finds a family member by ID, Persian name, or English name without necessarily switching.
        """
        def _norm(s: str) -> str:
            import re
            return re.sub(r"[\u064B-\u0652\u0670]", "", str(s)).lower().strip().replace(" ", "")

        q_norm = _norm(target)
        for m_id, member in self.members.items():
            m_norm = _norm(member.name)
            e_norm = _norm(member.english_name)
            if (
                q_norm == m_id
                or q_norm == m_norm
                or q_norm == e_norm
                or q_norm in m_norm
                or q_norm in _norm(member.role)
            ):
                return member
        return None

    def switch_member(self, target: str) -> Optional[FamilyMember]:
        """
        Switches the active family member by ID, Persian name, or English name.
        """
        member = self.find_member(target)
        if member:
            self.active_member_id = member.id
            self.save_profiles()
            logger.info(f"Switched active family member to: {member.name} ({member.id})")
            return member

        logger.warning(f"Could not find family member matching '{target}'")
        return None

    def update_member(
        self,
        member_id_or_name: Optional[str] = None,
        member_name: Optional[str] = None,
        new_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Customizes name, gender, mood, styling, and traits of a family member.
        Persists changes immediately to disk.
        """
        target = member_id_or_name or member_name
        if not target:
            return {"success": False, "error": "نام یا شناسه عضو خانواده مشخص نشده است."}

        member = self.find_member(target)
        if not member:
            return {"success": False, "error": f"عضو خانواده '{target}' پیدا نشد."}

        if new_name:
            kwargs["name"] = new_name

        res = member.update_attributes(**kwargs)
        self.save_profiles()
        logger.info(f"Successfully customized family member '{member.name}' ({member.id}).")
        return {
            "success": True,
            "member_id": member.id,
            "name": member.name,
            "gender": member.gender,
            "mood": member.mood,
            "role_title": member.role_title,
            "avatar_style": member.avatar_style,
            "updated_data": res
        }

    def add_member(self, member_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Adds a new member or child to the NexA family roster and persists.
        """
        import uuid
        data = dict(member_data or {})
        data.update(kwargs)
        raw_name = data.get("name", "عضو جدید").strip()
        m_id = data.get("id") or f"member_{uuid.uuid4().hex[:6]}"
        m_id = m_id.lower().replace(" ", "_")

        if m_id in self.members:
            return {"success": False, "error": f"عضوی با شناسه '{m_id}' از قبل وجود دارد."}

        data["id"] = m_id
        new_member = FamilyMember(data)
        self.members[m_id] = new_member
        self.save_profiles()
        logger.info(f"Added new family member '{new_member.name}' ({m_id}) to the family.")
        return {
            "success": True,
            "member_id": m_id,
            "name": new_member.name,
            "gender": new_member.gender,
            "mood": new_member.mood,
            "role_title": new_member.role_title
        }

    def delete_member(self, member_id_or_name: str) -> Dict[str, Any]:
        """Removes a member from the family (minimum 1 member must remain)."""
        if len(self.members) <= 1:
            return {"success": False, "error": "نمی‌توان تنها عضو باقی‌مانده خانواده را حذف کرد."}

        member = self.find_member(member_id_or_name)
        if not member:
            return {"success": False, "error": f"عضو '{member_id_or_name}' یافت نشد."}

        del_id = member.id
        del self.members[del_id]
        if self.active_member_id == del_id:
            self.active_member_id = next(iter(self.members.keys()))
        self.save_profiles()
        logger.info(f"Deleted member '{member.name}' ({del_id}). Active now: {self.active_member_id}")
        return {"success": True, "deleted_id": del_id, "active_member_id": self.active_member_id}

    def auto_delegate(self, user_prompt: str) -> FamilyMember:
        """
        Examines the user's prompt and routes it to the most specialized family member:
        - Code / Python / Bug / Test / Git -> سامیار (SamYar)
        - Windows GUI / App / Word / Excel / Notepad / Hotkey / Keys -> آرتین (Artin)
        - Web Search / Research / Scrape / Fact / News -> نیلا (Nila)
        - Design / Image / Art / UI / Colors -> تارا (Tara)
        - System / PowerShell / CMD / Security / Hardware / RAM / CPU -> نِکسامِهر (NexaMehr)
        - Otherwise / Orchestration / Empathy / Planning -> نِکسانو (NexaNoo)
        """
        p = user_prompt.lower()

        # Check explicit call outs first
        if any(w in p for w in ["سامیار", "samyar", "کدنویس", "برنامه نویس"]):
            return self.switch_member("samyar") or self.get_active_member()
        if any(w in p for w in ["آرتین", "artin", "اتوماسیون", "نرم افزارها"]):
            return self.switch_member("artin") or self.get_active_member()
        if any(w in p for w in ["نیلا", "nila", "پژوهشگر", "سرچ"]):
            return self.switch_member("nila") or self.get_active_member()
        if any(w in p for w in ["تارا", "tara", "طراح", "هنرمند", "نقاشی"]):
            return self.switch_member("tara") or self.get_active_member()
        if any(w in p for w in ["نکسامهر", "نِکسامِهر", "پدر", "nexamehr"]):
            return self.switch_member("nexamehr") or self.get_active_member()
        if any(w in p for w in ["نکسانو", "نِکسانو", "مادر", "nexanoo"]):
            return self.switch_member("nexanoo") or self.get_active_member()

        # Specialty routing
        # 1. Code / Programming -> سامیار
        if any(k in p for k in ["python", "پایتون", "کد", "اسکریپت", "تابع", "دیباگ", "باگ", "تست", "pytest", "الگوریتم", "گیت", "برنامه نویسی"]):
            target = self.members.get("samyar")
            if target:
                self.active_member_id = "samyar"
                return target

        # 2. Desktop & Software Automation -> آرتین
        if any(k in p for k in ["نوت پد", "notepad", "اکسل", "excel", "ورد", "word", "کلید میانبر", "شورتکات", "شورت‌کات", "ctrl+", "alt+", "فشردن کلید", "تایپ کن در", "پنجره", "کلیک کن", "ببند نرم افزار"]):
            target = self.members.get("artin")
            if target:
                self.active_member_id = "artin"
                return target

        # 3. Web Search, Research & Email Management -> نیلا
        if any(k in p for k in ["سرچ کن", "جستجو کن", "در وب", "گوگل", "مقاله", "اخبار", "قیمت", "چکیده", "خلاصه کن", "پژوهش", "ایمیل", "email", "جیمیل", "gmail", "صندوق ورودی"]):
            target = self.members.get("nila")
            if target:
                self.active_member_id = "nila"
                return target

        # 4. Creative / UI / Image Generation & Instagram Content -> تارا
        if any(k in p for k in ["طراحی", "پرامپت تصویر", "عکس بساز", "رنگ", "پالت", "زیباسازی", "هنر", "قالب", "اینستاگرام", "instagram", "ریلز", "reels", "کپشن", "پست اینستا"]):
            target = self.members.get("tara")
            if target:
                self.active_member_id = "tara"
                return target

        # 5. Core System / Admin / Security / HW -> نِکسامِهر
        if any(k in p for k in ["powershell", "پاورشل", "سیستم عامل", "امنیت", "دیسک", "سخت افزار", "پردازنده", "رم سیستم", "cmd", "رجیستری"]):
            target = self.members.get("nexamehr")
            if target:
                self.active_member_id = "nexamehr"
                return target

        # Default to Mother (NexaNoo) as caregiver and general orchestrator
        return self.get_active_member()

    def teach_member_skill(
        self,
        member_id_or_name: str,
        skill_name: str,
        instruction_steps: str,
        category: str = "custom"
    ) -> Dict[str, Any]:
        """Teaches a member a new skill and persists to file."""
        member = self.switch_member(member_id_or_name) or self.get_active_member()
        res = member.teach_skill(skill_name, instruction_steps, category=category)
        self.save_profiles()
        return res

    def remember_member_fact(self, member_id_or_name: Optional[str], key: str, value: Any) -> Dict[str, Any]:
        """Stores a persistent memory for a specific member or the active member, and saves to file."""
        member = self.find_member(member_id_or_name) if member_id_or_name else self.get_active_member()
        if not member:
            member = self.get_active_member()
        res = member.remember_fact(key, value)
        self.save_profiles()
        return res

    def recall_member_facts(self, member_id_or_name: Optional[str] = None, query: str = "") -> Dict[str, Any]:
        """Recalls memories for a member or all members."""
        if member_id_or_name:
            member = self.find_member(member_id_or_name)
            if member:
                return {member.name: member.recall_facts(query)}
        return {
            m.name: m.recall_facts(query)
            for m in self.members.values()
            if m.recall_facts(query)
        }

    def list_family_members(self) -> List[Dict[str, Any]]:
        """Returns structured list of all family members."""
        return [
            {
                "id": m.id,
                "name": m.name,
                "english_name": m.english_name,
                "role": m.role,
                "role_title": m.role_title,
                "gender": m.gender,
                "mood": m.mood,
                "avatar_style": m.avatar_style,
                "primary_color": m.primary_color,
                "secondary_color": m.secondary_color,
                "level": m.level,
                "xp": m.xp,
                "specialties": m.specialties,
                "bio": m.bio,
                "skills_count": len(m.skills),
                "is_active": m.id == self.active_member_id
            }
            for m in self.members.values()
        ]

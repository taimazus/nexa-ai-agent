import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock

from agent.family.member import FamilyMember
from agent.family.manager import FamilyManager
from agent.engine import AgentEngine
from agent.config import TOOL_DECLARATIONS


class TestFamilyMultiAgentSystem:
    """
    Test suite for the NexA Hierarchical AI Family Ecosystem:
    Parent roles, specialist children, dynamic skill learning, and smart delegation.
    """

    def test_load_family_profiles(self):
        """Verify family profiles load with parents and children."""
        manager = FamilyManager()
        members = manager.list_family_members()
        assert len(members) >= 6

        member_ids = [m["id"] for m in members]
        assert "nexamehr" in member_ids   # Father
        assert "nexanoo" in member_ids    # Mother
        assert "samyar" in member_ids     # Eldest Son / Code Ninja
        assert "artin" in member_ids      # Second Son / Automation
        assert "nila" in member_ids       # Daughter / Web Detective
        assert "tara" in member_ids       # Daughter / Designer

    def test_switch_family_member(self):
        """Verify switching active member by ID and name."""
        manager = FamilyManager()
        samyar = manager.switch_member("samyar")
        assert samyar is not None
        assert samyar.name == "سامیار"
        assert manager.active_member_id == "samyar"

        nexamehr = manager.switch_member("نکسامهر")
        assert nexamehr is not None
        assert nexamehr.id == "nexamehr"
        assert manager.active_member_id == "nexamehr"

    def test_auto_delegate_coding_prompt(self):
        """Verify coding prompts automatically delegate to SamYar."""
        manager = FamilyManager()
        member = manager.auto_delegate("یک اسکریپت پایتون بنویس و با pytest تستش کن")
        assert member.id == "samyar"

    def test_auto_delegate_desktop_automation_prompt(self):
        """Verify desktop automation prompts delegate to Artin."""
        manager = FamilyManager()
        member = manager.auto_delegate("نوت‌پد رو باز کن و کلید میانبر Ctrl+S رو بزن")
        assert member.id == "artin"

    def test_auto_delegate_research_prompt(self):
        """Verify web search prompts delegate to Nila."""
        manager = FamilyManager()
        member = manager.auto_delegate("در وب سرچ کن و جدیدترین قیمت‌ها و اخبار رو خلاصه کن")
        assert member.id == "nila"

    def test_auto_delegate_creative_prompt(self):
        """Verify creative/design prompts delegate to Tara."""
        manager = FamilyManager()
        member = manager.auto_delegate("یک پرامپت تصویر و رنگ‌بندی زیبا برای طراحی رابط کاربری پیشنهاد بده")
        assert member.id == "tara"

    def test_auto_delegate_system_prompt(self):
        """Verify system and powershell prompts delegate to Father (NexaMehr)."""
        manager = FamilyManager()
        member = manager.auto_delegate("دستور PowerShell برای بررسی مصرف رم و دیسک سیستم عامل چیه؟")
        assert member.id == "nexamehr"

    def test_teach_child_skill_and_gain_xp(self, tmp_path):
        """Verify teaching a skill adds it to member memory and awards XP."""
        fake_json = tmp_path / "test_family.json"
        base_data = {
            "active_member_id": "samyar",
            "members": {
                "samyar": {
                    "id": "samyar",
                    "name": "سامیار",
                    "role": "child_son",
                    "role_title": "مهندس کدنویسی",
                    "skills": ["python"],
                    "xp": 100,
                    "level": 1
                }
            }
        }
        with open(fake_json, "w", encoding="utf-8") as f:
            json.dump(base_data, f)

        manager = FamilyManager(profiles_path=fake_json)
        res = manager.teach_member_skill(
            "samyar",
            "git_commit_push",
            "ابتدا git status بگیر، سپس کامیت کن و پوش کن",
            category="git"
        )
        assert res["success"] is True

        samyar = manager.get_active_member()
        assert "git_commit_push" in samyar.skills
        assert "git_commit_push" in samyar.custom_skills
        assert samyar.xp > 100

    def test_engine_family_tools_registration(self):
        """Verify AgentEngine registers all family tools in its tools_map and callable list."""
        engine = AgentEngine(api_key="test_fake_key_12345678901234567890")
        assert "switch_family_member" in engine.tools_map
        assert "teach_family_skill" in engine.tools_map
        assert "list_family_members" in engine.tools_map

        callable_names = [f.__name__ for f in engine.callable_tools]
        assert "wrapped_switch_family" in callable_names
        assert "wrapped_teach_family" in callable_names
        assert "wrapped_list_family" in callable_names
        assert "wrapped_customize_family" in callable_names
        assert "wrapped_add_family" in callable_names

        declared_names = [d["name"] for d in TOOL_DECLARATIONS]
        assert "switch_family_member" in declared_names
        assert "teach_family_skill" in declared_names
        assert "list_family_members" in declared_names
        assert "customize_family_member" in declared_names
        assert "add_family_member" in declared_names

    def test_customize_family_member_attributes(self, tmp_path):
        """Verify customizing member name, gender, mood, and role persists."""
        fake_json = tmp_path / "custom_family.json"
        base_data = {
            "active_member_id": "samyar",
            "members": {
                "samyar": {
                    "id": "samyar",
                    "name": "سامیار",
                    "gender": "male",
                    "mood": "technical",
                    "role_title": "کدنویس",
                    "avatar_style": "cyber_bot"
                }
            }
        }
        with open(fake_json, "w", encoding="utf-8") as f:
            json.dump(base_data, f)

        manager = FamilyManager(profiles_path=fake_json)
        res = manager.update_member(
            "samyar",
            name="کوروش",
            gender="male",
            mood="witty",
            role_title="معمار ارشد نرم‌افزار",
            avatar_style="matrix_cube"
        )
        assert res["success"] is True
        assert res["name"] == "کوروش"
        assert res["mood"] == "witty"

        # Verify disk persistence
        with open(fake_json, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["members"]["samyar"]["name"] == "کوروش"
        assert saved["members"]["samyar"]["mood"] == "witty"
        assert saved["members"]["samyar"]["avatar_style"] == "matrix_cube"

    def test_add_and_delete_family_member(self, tmp_path):
        """Verify dynamically adding and removing a new family child."""
        fake_json = tmp_path / "add_family.json"
        base_data = {
            "active_member_id": "nexanoo",
            "members": {
                "nexanoo": {"id": "nexanoo", "name": "نکسانو", "role": "mother"}
            }
        }
        with open(fake_json, "w", encoding="utf-8") as f:
            json.dump(base_data, f)

        manager = FamilyManager(profiles_path=fake_json)
        res_add = manager.add_member({
            "id": "ayda",
            "name": "آیدا",
            "gender": "female",
            "mood": "creative",
            "role_title": "مترجم و متخصص زبان"
        })
        assert res_add["success"] is True
        assert "ayda" in manager.members

        # Switch to new member
        switched = manager.switch_member("آیدا")
        assert switched is not None
        assert manager.active_member_id == "ayda"

        # Delete member
        res_del = manager.delete_member("ayda")
        assert res_del["success"] is True
        assert "ayda" not in manager.members
        assert manager.active_member_id == "nexanoo"

    def test_prompt_context_reflects_gender_and_mood(self):
        """Verify the generated prompt context faithfully injects the chosen mood and gender."""
        member = FamilyMember({
            "id": "test_girl",
            "name": "نیلا",
            "gender": "female",
            "mood": "creative",
            "role_title": "پژوهشگر ارشد",
            "specialties": ["سرچ وب", "تحلیل داده"]
        })
        prompt = member.get_prompt_context()
        assert "نیلا" in prompt
        assert "خانم" in prompt
        assert "خلاق" in prompt
        assert "راهکار الکترونیک سهند" in prompt

    def test_engine_tool_dispatch_for_family_customization(self):
        """Verify engine can dispatch customize_family_member tool."""
        engine = AgentEngine(api_key="test_fake_key_12345678901234567890")
        try:
            res = engine.dispatch_tool(
                "customize_family_member",
                {
                    "member_name": "samyar",
                    "new_name": "سامیار قهرمان",
                    "mood": "energetic"
                }
            )
            assert res.get("success") is True
            member = engine.family_manager.find_member("samyar")
            assert member.name == "سامیار قهرمان"
            assert member.mood == "energetic"
        finally:
            engine.dispatch_tool(
                "customize_family_member",
                {
                    "member_name": "samyar",
                    "new_name": "سامیار",
                    "mood": "technical"
                }
            )


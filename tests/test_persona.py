import os
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.persona import PersonaManager, Gender


def test_persona_manager_defaults():
    pm = PersonaManager()
    assert pm.gender in (Gender.MALE, Gender.FEMALE)
    assert pm.name != ""
    assert pm.get_persona_prompt() != ""


def test_persona_manager_switch_gender(tmp_path):
    settings_file = str(tmp_path / "persona_settings.json")
    pm = PersonaManager(config_path=settings_file)
    pm.set_gender(Gender.FEMALE)
    assert pm.gender == Gender.FEMALE
    assert pm.name == "آوا"
    assert "آوا" in pm.get_persona_prompt()
    assert pm.get_accent_colors()["primary"] == "#ff2a85"

    pm.set_gender(Gender.MALE)
    assert pm.gender == Gender.MALE
    assert pm.name == "آریا"
    assert "آریا" in pm.get_persona_prompt()
    assert pm.get_accent_colors()["primary"] == "#00f3ff"


def test_persona_persistence(tmp_path):
    settings_file = str(tmp_path / "persona_settings.json")
    pm1 = PersonaManager(config_path=settings_file)
    pm1.set_gender(Gender.FEMALE)

    pm2 = PersonaManager(config_path=settings_file)
    assert pm2.gender == Gender.FEMALE


def test_companion_personalization_and_tones(tmp_path):
    from agent.persona import RelationshipTone, MascotScale, ThemePalette

    settings_file = str(tmp_path / "companion_settings.json")
    pm = PersonaManager(config_path=settings_file)

    # Test custom profile updates
    pm.update_companion_profile(
        user_name="تایماز",
        user_role="توسعه‌دهنده هوش مصنوعی",
        assistant_custom_name="یار مهربان",
        relationship_tone=RelationshipTone.MOTIVATIONAL,
        mascot_scale=MascotScale.LARGE,
        theme_palette=ThemePalette.IMPERIAL_GOLD,
        health_reminders=True,
        daily_greeting=True
    )

    assert pm.name == "یار مهربان"
    assert pm.user_name == "تایماز"
    assert pm.user_role == "توسعه‌دهنده هوش مصنوعی"
    assert pm.relationship_tone == RelationshipTone.MOTIVATIONAL
    assert pm.mascot_scale == MascotScale.LARGE
    assert pm.mascot_scale.dimensions == 200
    assert pm.theme_palette == ThemePalette.IMPERIAL_GOLD
    assert pm.get_accent_colors()["primary"] == "#ffb703"

    prompt = pm.get_persona_prompt()
    assert "یار مهربان" in prompt
    assert "تایماز" in prompt
    assert "توسعه‌دهنده هوش مصنوعی" in prompt
    assert "مربی و مشوق رشد فردی" in prompt

    # Verify time of day greeting
    greeting = pm.get_time_of_day_greeting()
    assert "تایماز" in greeting

    # Verify persistence
    pm_loaded = PersonaManager(config_path=settings_file)
    assert pm_loaded.name == "یار مهربان"
    assert pm_loaded.user_name == "تایماز"
    assert pm_loaded.relationship_tone == RelationshipTone.MOTIVATIONAL


def test_persian_default_language_directive():
    from agent.config import SYSTEM_INSTRUCTION
    pm = PersonaManager()
    prompt = pm.get_persona_prompt()
    assert "فارسی" in prompt
    assert "زبان پیش‌فرض" in prompt or "زبان اصلی" in prompt

    # Verify SYSTEM_INSTRUCTION also enforces Persian as default
    assert "زبان پیش‌فرض، اصلی و همیشگی شما زبان فارسی است" in SYSTEM_INSTRUCTION



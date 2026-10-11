import os
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.persona import PersonaManager, RelationshipTone, MascotScale, ThemePalette
from agent.companion import CompanionMonitor
from ui.mascot import DesktopMascot
from ui.settings_window import SettingsWindow


def test_companion_monitor_greeting_and_wellness(qapp, tmp_path):
    settings_file = str(tmp_path / "companion_monitor_test.json")
    pm = PersonaManager(config_path=settings_file)
    pm.update_companion_profile(user_name="تایماز")

    cm = CompanionMonitor(pm)
    greeting = cm.get_greeting()
    assert "تایماز" in greeting

    tip = cm.trigger_manual_check()
    assert "تایماز" in tip


def test_desktop_mascot_scale(qapp):
    mascot = DesktopMascot()
    assert mascot.width() == 160
    assert mascot.height() == 160

    mascot.set_mascot_scale(MascotScale.SMALL)
    assert mascot.width() == 120
    assert mascot.height() == 120

    mascot.set_mascot_scale(MascotScale.LARGE)
    assert mascot.width() == 200
    assert mascot.height() == 200

    mascot.set_mascot_scale("medium")
    assert mascot.width() == 160
    assert mascot.height() == 160


def test_settings_window_companion_tab_save(qapp, tmp_path):
    from agent.key_manager import KeyManager
    from agent.memory import MemoryManager

    km = KeyManager(config_path=str(tmp_path / "keys.json"))
    mm = MemoryManager(storage_path=str(tmp_path / "memory.json"))
    pm = PersonaManager(config_path=str(tmp_path / "persona.json"))

    sw = SettingsWindow(key_manager=km, memory_manager=mm, persona_manager=pm)

    # Fill companion fields
    sw.comp_user_name.setText("تایماز عزیز")
    sw.comp_user_role.setText("مهندس نرم‌افزار")
    sw.comp_asst_name.setText("نوا پلاس")
    sw.radio_motivational.setChecked(True)
    sw.radio_scale_l.setChecked(True)

    signals_received = []
    sw.companion_updated.connect(lambda: signals_received.append(True))

    # Trigger save
    sw._save_companion_profile()

    assert len(signals_received) == 1
    assert pm.user_name == "تایماز عزیز"
    assert pm.user_role == "مهندس نرم‌افزار"
    assert pm.name == "نوا پلاس"
    assert pm.relationship_tone == RelationshipTone.MOTIVATIONAL
    assert pm.mascot_scale == MascotScale.LARGE

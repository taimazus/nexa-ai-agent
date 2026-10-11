import os
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.persona import PersonaManager, AvatarStyle
from ui.mascot import DesktopMascot


def test_avatar_style_enum():
    assert AvatarStyle.CYBER_BOT.value == "cyber_bot"
    assert AvatarStyle.CYBER_CAT.value == "cyber_cat"
    assert AvatarStyle.ASTRAL_ORB.value == "astral_orb"
    assert AvatarStyle.ASTRO_PANDA.value == "astro_panda"
    assert AvatarStyle.from_string("cyber_cat") == AvatarStyle.CYBER_CAT
    assert AvatarStyle.from_string("unknown") == AvatarStyle.CYBER_BOT


def test_persona_manager_avatar_selection(tmp_path):
    settings_file = str(tmp_path / "persona_settings.json")
    pm = PersonaManager(config_path=settings_file)
    assert pm.avatar_style == AvatarStyle.CYBER_BOT

    pm.set_avatar_style(AvatarStyle.CYBER_CAT)
    assert pm.avatar_style == AvatarStyle.CYBER_CAT

    # Persistence verification
    pm2 = PersonaManager(config_path=settings_file)
    assert pm2.avatar_style == AvatarStyle.CYBER_CAT


def test_desktop_mascot_set_avatar_style(qapp):
    mascot = DesktopMascot()
    assert mascot.avatar_style == AvatarStyle.CYBER_BOT

    mascot.set_avatar_style(AvatarStyle.CYBER_CAT)
    assert mascot.avatar_style == AvatarStyle.CYBER_CAT

    mascot.set_avatar_style("astro_panda")
    assert mascot.avatar_style == AvatarStyle.ASTRO_PANDA


def test_settings_window_avatar_selection(qapp, tmp_path):
    from agent.key_manager import KeyManager
    from agent.memory import MemoryManager
    from ui.settings_window import SettingsWindow

    km = KeyManager(config_path=str(tmp_path / "keys.json"))
    mm = MemoryManager(storage_path=str(tmp_path / "memory.json"))
    pm = PersonaManager(config_path=str(tmp_path / "persona.json"))

    sw = SettingsWindow(key_manager=km, memory_manager=mm, persona_manager=pm)

    received_signals = []
    sw.avatar_changed.connect(lambda s: received_signals.append(s))

    # Toggle to Cyber Cat
    sw.radio_cat.setChecked(True)
    assert pm.avatar_style == AvatarStyle.CYBER_CAT
    assert "cyber_cat" in received_signals

    # Toggle to Astro Panda
    sw.radio_panda.setChecked(True)
    assert pm.avatar_style == AvatarStyle.ASTRO_PANDA
    assert "astro_panda" in received_signals

    # Toggle to Azure Sphere
    sw.radio_sphere.setChecked(True)
    assert pm.avatar_style == AvatarStyle.CYBER_SPHERE
    assert "cyber_sphere" in received_signals

    # Toggle to Carbon Chrono Lens
    sw.radio_chrono.setChecked(True)
    assert pm.avatar_style == AvatarStyle.CARBON_LENS
    assert "carbon_lens" in received_signals


def test_new_avatar_styles_and_interactive_expressions(qapp):
    from ui.mascot import MascotState

    mascot = DesktopMascot()

    # Test all 4 new styles
    for s in [AvatarStyle.CYBER_SPHERE, AvatarStyle.CARBON_LENS, AvatarStyle.DJ_HEADSET, AvatarStyle.CRYSTAL_PRISM]:
        mascot.set_avatar_style(s)
        assert mascot.avatar_style == s

    # Test wink trigger
    assert mascot.wink_timer == 0
    mascot.trigger_wink()
    assert mascot.wink_timer == 20

    # Test speaking lip-sync state
    mascot.set_state(MascotState.SPEAKING)
    assert mascot.state == MascotState.SPEAKING

    # Test tick physics update
    prev_tick = mascot.tick
    mascot._on_tick()
    assert mascot.tick == prev_tick + 1
    assert mascot.wink_timer == 19



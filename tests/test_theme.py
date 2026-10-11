import pytest
from unittest.mock import patch, MagicMock
from ui.theme_detector import WindowsThemeDetector
from ui.styles import get_palette_for_theme, get_chat_window_qss, get_settings_qss, get_speech_bubble_qss


def test_theme_detector_real_system_or_fallback():
    detector = WindowsThemeDetector()
    is_dark = detector.is_dark_mode()
    accent = detector.get_accent_color()
    
    assert isinstance(is_dark, bool)
    assert isinstance(accent, str)
    assert accent.startswith("#")
    assert len(accent) == 7


def test_theme_detector_mocked_dark_mode():
    detector = WindowsThemeDetector()
    with patch("ui.theme_detector.WindowsThemeDetector._read_registry_theme", return_value=(True, "#0078d7")):
        assert detector.is_dark_mode() is True
        assert detector.get_accent_color() == "#0078d7"

        palette = detector.get_system_theme_palette()
        assert palette["is_dark"] is True
        assert palette["neon_cyan"] == "#0078d7"
        assert "rgba(16, 23, 38" in palette["bg_glass"]
        assert palette["text_main"] == "#f1f5f9"


def test_theme_detector_mocked_light_mode():
    detector = WindowsThemeDetector()
    with patch("ui.theme_detector.WindowsThemeDetector._read_registry_theme", return_value=(False, "#d13438")):
        assert detector.is_dark_mode() is False
        assert detector.get_accent_color() == "#d13438"

        palette = detector.get_system_theme_palette()
        assert palette["is_dark"] is False
        assert palette["neon_cyan"] == "#d13438"
        assert "rgba(245, 247, 250" in palette["bg_glass"]
        assert palette["text_main"] == "#0f172a"


def test_dynamic_stylesheets_generation():
    dark_pal = get_palette_for_theme(is_dark=True, accent_color="#00f3ff")
    light_pal = get_palette_for_theme(is_dark=False, accent_color="#0078d7")

    dark_qss = get_chat_window_qss(dark_pal)
    light_qss = get_chat_window_qss(light_pal)

    assert "rgba(16, 23, 38" in dark_qss
    assert "rgba(245, 247, 250" in light_qss

    settings_dark = get_settings_qss(dark_pal)
    settings_light = get_settings_qss(light_pal)
    assert "rgba(16, 23, 38" in settings_dark
    assert "rgba(245, 247, 250" in settings_light


def test_persona_manager_os_theme_sync_toggle(tmp_path):
    from agent.persona import PersonaManager

    settings_file = str(tmp_path / "persona_settings.json")
    pm = PersonaManager(config_path=settings_file)
    assert hasattr(pm, "sync_with_os_theme")
    assert pm.sync_with_os_theme is True  # Enabled by default

    pm.set_os_theme_sync(False)
    assert pm.sync_with_os_theme is False

    pm_reloaded = PersonaManager(config_path=settings_file)
    assert pm_reloaded.sync_with_os_theme is False

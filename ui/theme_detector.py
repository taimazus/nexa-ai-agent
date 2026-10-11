import os
import sys
import logging
from typing import Tuple, Dict, Any, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

logger = logging.getLogger("NovaAgent.ThemeDetector")

DEFAULT_DARK_ACCENT = "#00f3ff"
DEFAULT_LIGHT_ACCENT = "#0284c7"


class WindowsThemeDetector(QObject):
    """
    Detects Windows OS Dark / Light mode and System Accent Color via Registry.
    Emits `theme_changed` signal when Windows theme or accent color changes.
    """
    theme_changed = pyqtSignal(bool, str)  # (is_dark, accent_color)

    def __init__(self, check_interval_ms: int = 4000, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.last_is_dark, self.last_accent = self._read_registry_theme()
        
        # Periodic timer for live OS theme change detection
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_for_theme_change)
        self.timer.start(check_interval_ms)

    @classmethod
    def _read_registry_theme(cls) -> Tuple[bool, str]:
        """
        Reads Windows Dark/Light mode and Accent color from Registry.
        Returns: (is_dark: bool, accent_color: str)
        """
        is_dark = True
        accent_color = DEFAULT_DARK_ACCENT

        if sys.platform != "win32":
            return is_dark, accent_color

        try:
            import winreg

            # 1. Check AppsUseLightTheme (0 = Dark, 1 = Light)
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                ) as key:
                    apps_light, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    is_dark = (apps_light == 0)
            except OSError as e:
                logger.debug(f"Could not read AppsUseLightTheme from registry: {e}")

            # 2. Check ColorizationColor (DWORD: AARRGGBB)
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\DWM"
                ) as key:
                    col_dword, _ = winreg.QueryValueEx(key, "ColorizationColor")
                    # Extract RGB
                    r = (col_dword >> 16) & 0xFF
                    g = (col_dword >> 8) & 0xFF
                    b = col_dword & 0xFF
                    # Ensure minimum brightness if too dark
                    if r + g + b < 60:
                        r, g, b = 0, 243, 255
                    accent_color = f"#{r:02x}{g:02x}{b:02x}"
            except OSError as e:
                logger.debug(f"Could not read ColorizationColor from DWM: {e}")

        except Exception as exc:
            logger.warning(f"Error accessing Windows theme registry: {exc}")

        return is_dark, accent_color

    def is_dark_mode(self) -> bool:
        is_dark, _ = self._read_registry_theme()
        return is_dark

    def get_accent_color(self) -> str:
        _, accent = self._read_registry_theme()
        return accent

    def get_system_theme_palette(self) -> Dict[str, Any]:
        """
        Builds a comprehensive palette matching the OS theme.
        """
        from ui.styles import get_palette_for_theme
        is_dark, accent = self._read_registry_theme()
        return get_palette_for_theme(is_dark=is_dark, accent_color=accent)

    def _check_for_theme_change(self):
        current_dark, current_accent = self._read_registry_theme()
        if current_dark != self.last_is_dark or current_accent.lower() != self.last_accent.lower():
            logger.info(
                f"Windows OS Theme change detected! Dark: {self.last_is_dark} -> {current_dark}, "
                f"Accent: {self.last_accent} -> {current_accent}"
            )
            self.last_is_dark = current_dark
            self.last_accent = current_accent
            self.theme_changed.emit(current_dark, current_accent)

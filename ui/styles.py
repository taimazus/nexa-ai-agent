# Neon Cyberpunk & Glassmorphism Design System for Nova Agent
# Supports Dynamic Dark/Light Mode & Windows OS Accent Color Synchronization

def hex_to_rgb(hex_str: str) -> str:
    h = hex_str.lstrip("#")
    if len(h) != 6:
        return "0, 243, 255"
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r}, {g}, {b}"
    except ValueError:
        return "0, 243, 255"


def get_palette_for_theme(is_dark: bool = True, accent_color: str = "#00f3ff") -> dict:
    rgb = hex_to_rgb(accent_color)
    if is_dark:
        return {
            "is_dark": True,
            "bg_dark": "#0a0e17",
            "bg_glass": "rgba(16, 23, 38, 0.92)",
            "bg_card": "rgba(23, 32, 54, 0.85)",
            "bg_card_user": f"rgba({rgb}, 0.15)",
            "neon_cyan": accent_color,
            "neon_purple": "#b026ff",
            "neon_pink": "#ff2a85",
            "neon_green": "#00ffaa",
            "neon_amber": "#ffb703",
            "neon_red": "#ff4d6d",
            "border_cyan": f"rgba({rgb}, 0.4)",
            "border_glass": "rgba(255, 255, 255, 0.12)",
            "text_main": "#f1f5f9",
            "text_muted": "#94a3b8",
            "text_accent": accent_color,
            "code_bg": "#070a10"
        }
    else:
        # High-contrast, elegant frosted acrylic light theme
        return {
            "is_dark": False,
            "bg_dark": "#f8fafc",
            "bg_glass": "rgba(245, 247, 250, 0.94)",
            "bg_card": "rgba(255, 255, 255, 0.90)",
            "bg_card_user": f"rgba({rgb}, 0.12)",
            "neon_cyan": accent_color,
            "neon_purple": "#7c3aed",
            "neon_pink": "#db2777",
            "neon_green": "#059669",
            "neon_amber": "#d97706",
            "neon_red": "#e11d48",
            "border_cyan": f"rgba({rgb}, 0.5)",
            "border_glass": "rgba(0, 0, 0, 0.12)",
            "text_main": "#0f172a",
            "text_muted": "#64748b",
            "text_accent": accent_color,
            "code_bg": "#f1f5f9"
        }


# Default Dark Palette
PALETTE = get_palette_for_theme(is_dark=True, accent_color="#00f3ff")


def get_chat_window_qss(palette: dict = None) -> str:
    p = palette or PALETTE
    rgb = hex_to_rgb(p.get("neon_cyan", "#00f3ff"))
    header_gradient = (
        f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba({rgb}, 0.18), stop:0.5 rgba(176, 38, 255, 0.12), stop:1 rgba(0, 0, 0, 0))"
        if p.get("is_dark", True)
        else f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba({rgb}, 0.20), stop:0.6 rgba(124, 58, 237, 0.10), stop:1 rgba(255, 255, 255, 0))"
    )

    return f"""
QWidget#CentralWidget {{
    background-color: {p['bg_glass']};
    border: 1px solid {p['border_cyan']};
    border-radius: 16px;
}}

QWidget#HeaderBar {{
    background: {header_gradient};
    border-bottom: 1px solid {p['border_glass']};
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
}}

QLabel#TitleLabel {{
    color: {p['neon_cyan']};
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
    font-size: 15px;
    font-weight: bold;
}}

QLabel#StatusBadge {{
    color: {p['neon_green']};
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
    font-size: 11px;
    background-color: rgba({hex_to_rgb(p['neon_green'])}, 0.15);
    border: 1px solid rgba({hex_to_rgb(p['neon_green'])}, 0.35);
    border-radius: 9px;
    padding: 2px 8px;
}}

QScrollArea {{
    background: transparent;
    border: none;
}}

QWidget#ScrollAreaWidgetContents {{
    background: transparent;
}}

QScrollBar:vertical {{
    background: rgba({rgb}, 0.08);
    width: 6px;
    margin: 0px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical {{
    background: rgba({rgb}, 0.35);
    min-height: 20px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: {p['neon_cyan']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Message Cards */
QFrame.user_card {{
    background-color: {p['bg_card_user']};
    border: 1px solid {p['border_cyan']};
    border-radius: 14px;
    padding: 10px;
}}

QFrame.agent_card {{
    background-color: {p['bg_card']};
    border: 1px solid {p['border_glass']};
    border-radius: 14px;
    padding: 10px;
}}

QFrame.tool_card {{
    background-color: {'rgba(10, 15, 28, 0.9)' if p.get('is_dark', True) else 'rgba(241, 245, 249, 0.95)'};
    border: 1px dashed rgba(176, 38, 255, 0.5);
    border-radius: 10px;
    padding: 8px;
}}

/* Chips */
QPushButton.chip_button {{
    background-color: {'rgba(255, 255, 255, 0.05)' if p.get('is_dark', True) else 'rgba(0, 0, 0, 0.04)'};
    color: {p['text_accent']};
    border: 1px solid rgba({rgb}, 0.3);
    border-radius: 12px;
    padding: 5px 12px;
    font-size: 11px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QPushButton.chip_button:hover {{
    background-color: rgba({rgb}, 0.2);
    border: 1px solid {p['neon_cyan']};
    color: {'#ffffff' if p.get('is_dark', True) else p['neon_cyan']};
}}

/* Input Box */
QTextEdit#InputEdit {{
    background-color: {'rgba(10, 14, 23, 0.85)' if p.get('is_dark', True) else 'rgba(255, 255, 255, 0.95)'};
    color: {p['text_main']};
    border: 1px solid rgba({rgb}, 0.35);
    border-radius: 12px;
    padding: 8px 12px;
    font-size: 13px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QTextEdit#InputEdit:focus {{
    border: 1px solid {p['neon_cyan']};
    background-color: {'rgba(10, 14, 23, 0.95)' if p.get('is_dark', True) else '#ffffff'};
}}

/* Send and Action Buttons */
QPushButton#SendButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['neon_cyan']}, stop:1 {p['neon_purple']});
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    border: none;
    border-radius: 12px;
    padding: 8px 18px;
}}

QPushButton#SendButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #25f5ff, stop:1 #c24bff);
}}

QPushButton#SendButton:pressed {{
    background: {p['neon_purple']};
}}

QPushButton.icon_button {{
    background-color: {'rgba(255, 255, 255, 0.06)' if p.get('is_dark', True) else 'rgba(0, 0, 0, 0.04)'};
    color: {p['text_main']};
    border: 1px solid {p['border_glass']};
    border-radius: 12px;
    padding: 6px;
}}

QPushButton.icon_button:hover {{
    background-color: rgba({rgb}, 0.15);
    border: 1px solid {p['border_cyan']};
}}

QPushButton.icon_button:checked {{
    background-color: rgba({hex_to_rgb(p['neon_green'])}, 0.2);
    border: 1px solid {p['neon_green']};
    color: {p['neon_green']};
}}

QPushButton#CloseButton, QPushButton#MinButton {{
    background: transparent;
    color: {p['text_muted']};
    border: none;
    font-size: 14px;
    padding: 4px;
}}

QPushButton#CloseButton:hover {{
    color: {p['neon_red']};
}}
QPushButton#MinButton:hover {{
    color: {p['neon_cyan']};
}}
"""


def get_speech_bubble_qss(palette: dict = None) -> str:
    p = palette or PALETTE
    return f"""
QFrame#BubbleFrame {{
    background-color: {p['bg_glass']};
    border: 1.5px solid {p['neon_cyan']};
    border-radius: 14px;
    padding: 10px;
}}

QLabel#BubbleText {{
    color: {p['text_main']};
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
    font-size: 12px;
    line-height: 1.4;
}}
"""


def get_settings_qss(palette: dict = None) -> str:
    p = palette or PALETTE
    rgb = hex_to_rgb(p.get("neon_cyan", "#00f3ff"))
    is_dark = p.get("is_dark", True)

    return f"""
QWidget#SettingsWidget {{
    background-color: {p['bg_glass']};
    border: 1.5px solid {p['neon_cyan']};
    border-radius: 16px;
}}

QTabWidget::pane {{
    border: 1px solid {p['border_glass']};
    background: transparent;
    border-radius: 8px;
}}

QTabBar::tab {{
    background: {'rgba(255, 255, 255, 0.05)' if is_dark else 'rgba(0, 0, 0, 0.04)'};
    color: {p['text_muted']};
    border: 1px solid {p['border_glass']};
    border-bottom: none;
    padding: 8px 14px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
    font-size: 11px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 3px;
}}

QTabBar::tab:selected {{
    background: rgba({rgb}, 0.18);
    color: {p['neon_cyan']};
    border: 1px solid {p['neon_cyan']};
    border-bottom: none;
    font-weight: bold;
}}

QLabel {{
    color: {p['text_main']};
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QLineEdit, QComboBox {{
    background-color: {'rgba(10, 14, 23, 0.8)' if is_dark else 'rgba(255, 255, 255, 0.95)'};
    color: {p['text_main']};
    border: 1px solid {p['border_glass']};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 11px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {p['neon_cyan']};
}}

QPushButton.primary_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {p['neon_cyan']}, stop:1 {p['neon_purple']});
    color: #ffffff;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 11px;
}}

QPushButton.secondary_btn {{
    background-color: {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'};
    color: {p['text_main']};
    border: 1px solid {p['border_glass']};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 11px;
}}

QPushButton.secondary_btn:hover {{
    background-color: rgba({rgb}, 0.15);
    border: 1px solid {p['neon_cyan']};
}}

QPushButton.danger_btn {{
    background-color: rgba(255, 77, 109, 0.15);
    color: {p['neon_red']};
    border: 1px solid rgba(255, 77, 109, 0.4);
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 11px;
}}

QPushButton.danger_btn:hover {{
    background-color: rgba(255, 77, 109, 0.3);
}}

QTableWidget {{
    background-color: {'rgba(10, 14, 23, 0.6)' if is_dark else 'rgba(255, 255, 255, 0.8)'};
    border: 1px solid {p['border_glass']};
    border-radius: 8px;
    gridline-color: {p['border_glass']};
    color: {p['text_main']};
    font-size: 11px;
}}

QHeaderView::section {{
    background-color: {'rgba(16, 23, 38, 0.9)' if is_dark else 'rgba(226, 232, 240, 0.9)'};
    color: {p['neon_cyan']};
    border: none;
    padding: 6px;
    font-weight: bold;
    font-size: 11px;
}}
"""


CHAT_WINDOW_QSS = get_chat_window_qss(PALETTE)
SETTINGS_QSS = get_settings_qss(PALETTE)
SPEECH_BUBBLE_QSS = get_speech_bubble_qss(PALETTE)

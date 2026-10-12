# Ultra-Modern Bento Grid & Adaptive Design System for NexA AI Agent
# Inspired by Apple, Linear, Framer, and Modern Minimalist Bento Design
from typing import Dict, Any, Optional

def hex_to_rgb(hex_str: str) -> str:
    h = str(hex_str).lstrip("#")
    if len(h) != 6:
        return "0, 243, 255"
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r}, {g}, {b}"
    except ValueError:
        return "0, 243, 255"


# --- Complete Palette Catalog ---
AVAILABLE_THEMES: Dict[str, Dict[str, Any]] = {
    # 1. Bento Dark Minimal (Featured - Designed based on user reference screenshot)
    "bento_dark": {
        "theme_id": "bento_dark",
        "theme_name_fa": "بنتو دارک مدرن (اسلیت و گرافیتی)",
        "style_family": "bento",
        "is_dark": True,
        "bg_dark": "#18181b",
        "bg_glass": "rgba(28, 28, 32, 0.96)",
        "border_color": "rgba(255, 255, 255, 0.08)",
        "header_bg": "rgba(255, 255, 255, 0.03)",
        "header_border": "rgba(255, 255, 255, 0.07)",
        "title_color": "#ffffff",
        "bg_card": "rgba(33, 33, 37, 0.95)",
        "bg_card_user": "rgba(43, 43, 49, 0.95)",
        "border_card": "rgba(255, 255, 255, 0.07)",
        "border_card_user": "rgba(255, 255, 255, 0.12)",
        "pill_bg": "#2d2d33",
        "pill_border": "rgba(255, 255, 255, 0.07)",
        "pill_hover": "#3a3a42",
        "pill_active": "#484852",
        "pill_text": "#a1a1aa",
        "pill_active_text": "#ffffff",
        "input_bg": "#161619",
        "input_border": "rgba(255, 255, 255, 0.09)",
        "send_btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #e4e4e7)",
        "send_btn_text": "#121214",
        "send_btn_hover": "#f4f4f5",
        "text_main": "#f4f4f5",
        "text_muted": "#a1a1aa",
        "accent": "#ffffff",
        "neon_cyan": "#38bdf8",
        "neon_purple": "#818cf8",
        "neon_green": "#22c55e",
        "neon_amber": "#f59e0b",
        "neon_red": "#ef4444",
        "border_cyan": "rgba(255, 255, 255, 0.08)",
        "border_glass": "rgba(255, 255, 255, 0.07)",
        "code_bg": "#141416"
    },

    # 2. Bento Studio Light (Crisp porcelain & soft bento cards)
    "bento_light": {
        "theme_id": "bento_light",
        "theme_name_fa": "بنتو سرامیکی لوکس (استودیو سفید)",
        "style_family": "bento",
        "is_dark": False,
        "bg_dark": "#f8f9fa",
        "bg_glass": "rgba(250, 250, 252, 0.98)",
        "border_color": "rgba(0, 0, 0, 0.08)",
        "header_bg": "rgba(0, 0, 0, 0.02)",
        "header_border": "rgba(0, 0, 0, 0.06)",
        "title_color": "#18181b",
        "bg_card": "rgba(255, 255, 255, 0.95)",
        "bg_card_user": "rgba(244, 244, 247, 0.95)",
        "border_card": "rgba(0, 0, 0, 0.06)",
        "border_card_user": "rgba(0, 0, 0, 0.09)",
        "pill_bg": "#ebebef",
        "pill_border": "rgba(0, 0, 0, 0.05)",
        "pill_hover": "#e2e2e7",
        "pill_active": "#18181b",
        "pill_text": "#52525b",
        "pill_active_text": "#ffffff",
        "input_bg": "#ffffff",
        "input_border": "rgba(0, 0, 0, 0.10)",
        "send_btn_bg": "#18181b",
        "send_btn_text": "#ffffff",
        "send_btn_hover": "#27272a",
        "text_main": "#18181b",
        "text_muted": "#71717a",
        "accent": "#18181b",
        "neon_cyan": "#0284c7",
        "neon_purple": "#6366f1",
        "neon_green": "#16a34a",
        "neon_amber": "#d97706",
        "neon_red": "#dc2626",
        "border_cyan": "rgba(0, 0, 0, 0.08)",
        "border_glass": "rgba(0, 0, 0, 0.06)",
        "code_bg": "#f4f4f5"
    },

    # 3. Bento Warm Espresso (Deep warm chocolate charcoal like the card in user's image)
    "bento_espresso": {
        "theme_id": "bento_espresso",
        "theme_name_fa": "بنتو شکلاتی و خاکستری گرم (Warm Espresso)",
        "style_family": "bento",
        "is_dark": True,
        "bg_dark": "#1e1a19",
        "bg_glass": "rgba(34, 30, 29, 0.96)",
        "border_color": "rgba(255, 235, 220, 0.08)",
        "header_bg": "rgba(255, 235, 220, 0.03)",
        "header_border": "rgba(255, 235, 220, 0.07)",
        "title_color": "#fdfbf7",
        "bg_card": "rgba(37, 32, 31, 0.95)",
        "bg_card_user": "rgba(50, 42, 41, 0.95)",
        "border_card": "rgba(255, 235, 220, 0.06)",
        "border_card_user": "rgba(255, 235, 220, 0.12)",
        "pill_bg": "#382f2e",
        "pill_border": "rgba(255, 235, 220, 0.07)",
        "pill_hover": "#443938",
        "pill_active": "#574846",
        "pill_text": "#c4b5a5",
        "pill_active_text": "#fdfbf7",
        "input_bg": "#1a1716",
        "input_border": "rgba(255, 235, 220, 0.09)",
        "send_btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d4a373, stop:1 #e07a5f)",
        "send_btn_text": "#ffffff",
        "send_btn_hover": "#e07a5f",
        "text_main": "#fdfbf7",
        "text_muted": "#a89f91",
        "accent": "#d4a373",
        "neon_cyan": "#d4a373",
        "neon_purple": "#e07a5f",
        "neon_green": "#84cc16",
        "neon_amber": "#f59e0b",
        "neon_red": "#f87171",
        "border_cyan": "rgba(255, 235, 220, 0.08)",
        "border_glass": "rgba(255, 235, 220, 0.07)",
        "code_bg": "#181514"
    },

    # 4. Pure OLED Obsidian (Pure black and clean silver)
    "oled_obsidian": {
        "theme_id": "oled_obsidian",
        "theme_name_fa": "آبسیدین مینیمال (مشکی خالص OLED)",
        "style_family": "bento",
        "is_dark": True,
        "bg_dark": "#000000",
        "bg_glass": "rgba(12, 12, 14, 0.98)",
        "border_color": "rgba(255, 255, 255, 0.10)",
        "header_bg": "rgba(255, 255, 255, 0.02)",
        "header_border": "rgba(255, 255, 255, 0.08)",
        "title_color": "#ffffff",
        "bg_card": "rgba(18, 18, 20, 0.98)",
        "bg_card_user": "rgba(26, 26, 30, 0.98)",
        "border_card": "rgba(255, 255, 255, 0.07)",
        "border_card_user": "rgba(255, 255, 255, 0.12)",
        "pill_bg": "#1c1c20",
        "pill_border": "rgba(255, 255, 255, 0.08)",
        "pill_hover": "#28282e",
        "pill_active": "#3f3f46",
        "pill_text": "#a1a1aa",
        "pill_active_text": "#ffffff",
        "input_bg": "#0a0a0c",
        "input_border": "rgba(255, 255, 255, 0.10)",
        "send_btn_bg": "#ffffff",
        "send_btn_text": "#000000",
        "send_btn_hover": "#e4e4e7",
        "text_main": "#ffffff",
        "text_muted": "#a1a1aa",
        "accent": "#ffffff",
        "neon_cyan": "#e4e4e7",
        "neon_purple": "#a855f7",
        "neon_green": "#4ade80",
        "neon_amber": "#fbbf24",
        "neon_red": "#f43f5e",
        "border_cyan": "rgba(255, 255, 255, 0.10)",
        "border_glass": "rgba(255, 255, 255, 0.08)",
        "code_bg": "#000000"
    },

    # 5. Nordic Titanium (Deep oceanic grey & titanium cyan)
    "nordic_titanium": {
        "theme_id": "nordic_titanium",
        "theme_name_fa": "نوردیک تیتانیوم (خاکستری و آبی اقیانوسی)",
        "style_family": "bento",
        "is_dark": True,
        "bg_dark": "#111827",
        "bg_glass": "rgba(20, 27, 38, 0.96)",
        "border_color": "rgba(56, 189, 248, 0.14)",
        "header_bg": "rgba(56, 189, 248, 0.04)",
        "header_border": "rgba(56, 189, 248, 0.10)",
        "title_color": "#e0f2fe",
        "bg_card": "rgba(24, 34, 50, 0.95)",
        "bg_card_user": "rgba(34, 48, 70, 0.95)",
        "border_card": "rgba(56, 189, 248, 0.09)",
        "border_card_user": "rgba(56, 189, 248, 0.18)",
        "pill_bg": "#222f42",
        "pill_border": "rgba(56, 189, 248, 0.12)",
        "pill_hover": "#2d3d54",
        "pill_active": "#38bdf8",
        "pill_text": "#94a3b8",
        "pill_active_text": "#0f172a",
        "input_bg": "#0f172a",
        "input_border": "rgba(56, 189, 248, 0.14)",
        "send_btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #0284c7)",
        "send_btn_text": "#0f172a",
        "send_btn_hover": "#7dd3fc",
        "text_main": "#f1f5f9",
        "text_muted": "#94a3b8",
        "accent": "#38bdf8",
        "neon_cyan": "#38bdf8",
        "neon_purple": "#818cf8",
        "neon_green": "#34d399",
        "neon_amber": "#f59e0b",
        "neon_red": "#f87171",
        "border_cyan": "rgba(56, 189, 248, 0.14)",
        "border_glass": "rgba(56, 189, 248, 0.10)",
        "code_bg": "#0b1120"
    },

    # 6. Classic Cyberpunk Neon Cyan
    "cyber_cyan": {
        "theme_id": "cyber_cyan",
        "theme_name_fa": "سایبرپانک نئونی (کلاسیک فیروزه‌ای)",
        "style_family": "neon",
        "is_dark": True,
        "bg_dark": "#0a0e17",
        "bg_glass": "rgba(16, 23, 38, 0.92)",
        "border_color": "rgba(0, 243, 255, 0.4)",
        "header_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 243, 255, 0.18), stop:0.5 rgba(176, 38, 255, 0.12), stop:1 rgba(0, 0, 0, 0))",
        "header_border": "rgba(255, 255, 255, 0.12)",
        "title_color": "#00f3ff",
        "bg_card": "rgba(23, 32, 54, 0.85)",
        "bg_card_user": "rgba(0, 243, 255, 0.15)",
        "border_card": "rgba(255, 255, 255, 0.12)",
        "border_card_user": "rgba(0, 243, 255, 0.4)",
        "pill_bg": "rgba(255, 255, 255, 0.05)",
        "pill_border": "rgba(0, 243, 255, 0.3)",
        "pill_hover": "rgba(0, 243, 255, 0.2)",
        "pill_active": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 243, 255, 0.35), stop:1 rgba(176, 38, 255, 0.35))",
        "pill_text": "#00f3ff",
        "pill_active_text": "#00f3ff",
        "input_bg": "rgba(10, 14, 23, 0.85)",
        "input_border": "rgba(0, 243, 255, 0.35)",
        "send_btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00f3ff, stop:1 #b026ff)",
        "send_btn_text": "#ffffff",
        "send_btn_hover": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #25f5ff, stop:1 #c24bff)",
        "text_main": "#f1f5f9",
        "text_muted": "#94a3b8",
        "accent": "#00f3ff",
        "neon_cyan": "#00f3ff",
        "neon_purple": "#b026ff",
        "neon_pink": "#ff2a85",
        "neon_green": "#00ffaa",
        "neon_amber": "#ffb703",
        "neon_red": "#ff4d6d",
        "border_cyan": "rgba(0, 243, 255, 0.4)",
        "border_glass": "rgba(255, 255, 255, 0.12)",
        "code_bg": "#070a10"
    }
}


def get_palette_by_name(theme_id: str) -> dict:
    """Returns palette by theme id, defaulting to Bento Dark."""
    clean = str(theme_id or "").strip().lower()
    return AVAILABLE_THEMES.get(clean, AVAILABLE_THEMES["bento_dark"])


def get_palette_for_theme(is_dark: bool = True, accent_color: str = "#00f3ff", theme_name: Optional[str] = None) -> dict:
    """
    Returns the theme dictionary. Supports named Bento themes,
    and maintains exact backward-compatibility for dark/light system sync.
    """
    if theme_name and theme_name in AVAILABLE_THEMES:
        return AVAILABLE_THEMES[theme_name]

    rgb = hex_to_rgb(accent_color)
    if is_dark:
        return {
            "style_family": "neon",
            "is_dark": True,
            "bg_dark": "#0a0e17",
            "bg_glass": "rgba(16, 23, 38, 0.92)",
            "bg_card": "rgba(23, 32, 54, 0.85)",
            "bg_card_user": f"rgba({rgb}, 0.15)",
            "header_bg": f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba({rgb}, 0.18), stop:0.5 rgba(176, 38, 255, 0.12), stop:1 rgba(0, 0, 0, 0))",
            "header_border": "rgba(255, 255, 255, 0.12)",
            "title_color": accent_color,
            "pill_bg": "rgba(255, 255, 255, 0.05)",
            "pill_border": f"rgba({rgb}, 0.3)",
            "pill_hover": f"rgba({rgb}, 0.2)",
            "pill_active": f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba({rgb}, 0.35), stop:1 rgba(176, 38, 255, 0.35))",
            "pill_text": accent_color,
            "pill_active_text": accent_color,
            "input_bg": "rgba(10, 14, 23, 0.85)",
            "input_border": f"rgba({rgb}, 0.35)",
            "send_btn_bg": f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {accent_color}, stop:1 #b026ff)",
            "send_btn_text": "#ffffff",
            "send_btn_hover": f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #25f5ff, stop:1 #c24bff)",
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
            "style_family": "neon",
            "is_dark": False,
            "bg_dark": "#f8fafc",
            "bg_glass": "rgba(245, 247, 250, 0.94)",
            "bg_card": "rgba(255, 255, 255, 0.90)",
            "bg_card_user": f"rgba({rgb}, 0.12)",
            "header_bg": f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba({rgb}, 0.20), stop:0.6 rgba(124, 58, 237, 0.10), stop:1 rgba(255, 255, 255, 0))",
            "header_border": "rgba(0, 0, 0, 0.12)",
            "title_color": accent_color,
            "pill_bg": "rgba(0, 0, 0, 0.04)",
            "pill_border": f"rgba({rgb}, 0.3)",
            "pill_hover": f"rgba({rgb}, 0.2)",
            "pill_active": f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba({rgb}, 0.35), stop:1 rgba(124, 58, 237, 0.35))",
            "pill_text": accent_color,
            "pill_active_text": accent_color,
            "input_bg": "rgba(255, 255, 255, 0.95)",
            "input_border": f"rgba({rgb}, 0.35)",
            "send_btn_bg": f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {accent_color}, stop:1 #7c3aed)",
            "send_btn_text": "#ffffff",
            "send_btn_hover": f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38bdf8, stop:1 #9333ea)",
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


# Default Active Palette
PALETTE = AVAILABLE_THEMES["bento_dark"]


def get_chat_window_qss(palette: dict = None) -> str:
    """Generates the QSS stylesheet for the main chat window based on the chosen design style."""
    p = palette or PALETTE
    rgb = hex_to_rgb(p.get("neon_cyan", "#38bdf8"))
    is_bento = p.get("style_family") == "bento"
    is_dark = p.get("is_dark", True)

    if is_bento:
        border_col = p.get("border_color", "rgba(255, 255, 255, 0.08)")
        header_border = p.get("header_border", "rgba(255, 255, 255, 0.07)")
        header_bg = p.get("header_bg", "rgba(255, 255, 255, 0.03)")
        title_col = p.get("title_color", "#ffffff")
        card_user = p.get("bg_card_user", "#2b2b30")
        card_agent = p.get("bg_card", "#212124")
        card_user_border = p.get("border_card_user", "rgba(255, 255, 255, 0.12)")
        card_agent_border = p.get("border_card", "rgba(255, 255, 255, 0.07)")
        pill_bg = p.get("pill_bg", "#2d2d33")
        pill_border = p.get("pill_border", "rgba(255, 255, 255, 0.07)")
        pill_hover = p.get("pill_hover", "#3a3a42")
        pill_active = p.get("pill_active", "#484852")
        pill_text = p.get("pill_text", "#a1a1aa")
        pill_active_text = p.get("pill_active_text", "#ffffff")
        input_bg = p.get("input_bg", "#161619")
        input_border = p.get("input_border", "rgba(255, 255, 255, 0.09)")
        send_bg = p.get("send_btn_bg", "#ffffff")
        send_text = p.get("send_btn_text", "#121214")
        send_hover = p.get("send_btn_hover", "#f4f4f5")

        return f"""
QWidget#CentralWidget {{
    background-color: {p['bg_glass']};
    border: 1px solid {border_col};
    border-radius: 18px;
}}

QWidget#HeaderBar {{
    background: {header_bg};
    border-bottom: 1px solid {header_border};
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
}}

QLabel#TitleLabel {{
    color: {title_col};
    font-family: 'Segoe UI', 'Vazirmatn', -apple-system, BlinkMacSystemFont, 'Tahoma';
    font-size: 14px;
    font-weight: 600;
}}

QLabel#StatusBadge {{
    color: {p.get('neon_green', '#22c55e')};
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
    font-size: 11px;
    background-color: rgba(34, 197, 94, 0.12);
    border: 1px solid rgba(34, 197, 94, 0.25);
    border-radius: 8px;
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
    background: rgba(255, 255, 255, 0.03);
    width: 6px;
    margin: 0px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.15);
    min-height: 20px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: rgba(255, 255, 255, 0.35);
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Bento Floating Message Cards */
QFrame.user_card {{
    background-color: {card_user};
    border: 1px solid {card_user_border};
    border-radius: 14px;
    padding: 12px;
}}

QFrame.agent_card {{
    background-color: {card_agent};
    border: 1px solid {card_agent_border};
    border-radius: 14px;
    padding: 12px;
}}

QFrame.tool_card {{
    background-color: {p.get('code_bg', '#141416')};
    border: 1px dashed rgba(255, 255, 255, 0.14);
    border-radius: 10px;
    padding: 8px;
}}

/* Bento Quick Action Chips */
QPushButton.chip_button {{
    background-color: {pill_bg};
    color: {p['text_main']};
    border: 1px solid {pill_border};
    border-radius: 10px;
    padding: 5px 12px;
    font-size: 11px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QPushButton.chip_button:hover {{
    background-color: {pill_hover};
    color: #ffffff;
}}

/* Bento Family Bar - Segmented Control Pills */
QFrame#FamilyBar {{
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid {border_col};
    border-radius: 13px;
    padding: 4px 6px;
}}

QLabel#ActiveFamilyBadge {{
    color: {title_col};
    font-size: 11px;
    font-weight: 600;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QLabel#ActiveFamilyLevel {{
    color: {p.get('neon_green', '#22c55e')};
    font-size: 10px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
    background-color: rgba(34, 197, 94, 0.12);
    border-radius: 6px;
    padding: 1px 5px;
}}

QPushButton.family_chip {{
    background-color: {pill_bg};
    color: {pill_text};
    border: 1px solid {pill_border};
    border-radius: 9px;
    padding: 4px 8px;
    font-size: 11px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QPushButton.family_chip:hover {{
    background-color: {pill_hover};
    color: #ffffff;
}}

QPushButton.family_chip_active {{
    background-color: {pill_active};
    color: {pill_active_text};
    border: 1px solid rgba(255, 255, 255, 0.20);
    border-radius: 9px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

/* Bento Input Box */
QTextEdit#InputEdit {{
    background-color: {input_bg};
    color: {p['text_main']};
    border: 1px solid {input_border};
    border-radius: 12px;
    padding: 8px 12px;
    font-size: 13px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QTextEdit#InputEdit:focus {{
    border: 1px solid rgba(255, 255, 255, 0.30);
}}

/* Apple/Linear Minimalist Buttons */
QPushButton#SendButton {{
    background: {send_bg};
    color: {send_text};
    font-weight: 600;
    font-size: 13px;
    border: none;
    border-radius: 11px;
    padding: 8px 18px;
}}

QPushButton#SendButton:hover {{
    background: {send_hover};
}}

QPushButton.icon_button {{
    background-color: {pill_bg};
    color: {p['text_main']};
    border: 1px solid {pill_border};
    border-radius: 11px;
    padding: 6px;
}}

QPushButton.icon_button:hover {{
    background-color: {pill_hover};
}}

QPushButton.icon_button:checked {{
    background-color: rgba(34, 197, 94, 0.2);
    border: 1px solid {p.get('neon_green', '#22c55e')};
    color: {p.get('neon_green', '#22c55e')};
}}

QPushButton#CloseButton, QPushButton#MinButton {{
    background: transparent;
    color: {p['text_muted']};
    border: none;
    font-size: 14px;
    padding: 4px;
}}

QPushButton#CloseButton:hover {{
    color: {p.get('neon_red', '#ef4444')};
}}

QPushButton#MinButton:hover {{
    color: {title_col};
}}
"""

    # --- Classic Neon Cyberpunk Theme Fallback ---
    header_gradient = p.get("header_bg") or (
        f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba({rgb}, 0.18), stop:0.5 rgba(176, 38, 255, 0.12), stop:1 rgba(0, 0, 0, 0))"
        if is_dark
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
    background-color: {'rgba(10, 15, 28, 0.9)' if is_dark else 'rgba(241, 245, 249, 0.95)'};
    border: 1px dashed rgba(176, 38, 255, 0.5);
    border-radius: 10px;
    padding: 8px;
}}

/* Chips */
QPushButton.chip_button {{
    background-color: {'rgba(255, 255, 255, 0.05)' if is_dark else 'rgba(0, 0, 0, 0.04)'};
    color: {p.get('text_accent', p['neon_cyan'])};
    border: 1px solid rgba({rgb}, 0.3);
    border-radius: 12px;
    padding: 5px 12px;
    font-size: 11px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QPushButton.chip_button:hover {{
    background-color: rgba({rgb}, 0.2);
    border: 1px solid {p['neon_cyan']};
    color: {'#ffffff' if is_dark else p['neon_cyan']};
}}

/* Family Quick Switcher Bar */
QFrame#FamilyBar {{
    background-color: {'rgba(255, 255, 255, 0.04)' if is_dark else 'rgba(0, 0, 0, 0.03)'};
    border: 1px solid rgba({rgb}, 0.22);
    border-radius: 12px;
    padding: 4px 6px;
}}

QLabel#ActiveFamilyBadge {{
    color: {p['neon_cyan']};
    font-size: 11px;
    font-weight: bold;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QLabel#ActiveFamilyLevel {{
    color: {p['neon_green']};
    font-size: 10px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
    background-color: rgba({hex_to_rgb(p['neon_green'])}, 0.12);
    border-radius: 6px;
    padding: 1px 5px;
}}

QPushButton.family_chip {{
    background-color: {'rgba(255, 255, 255, 0.06)' if is_dark else 'rgba(0, 0, 0, 0.04)'};
    color: {p['text_main']};
    border: 1px solid rgba({rgb}, 0.25);
    border-radius: 9px;
    padding: 3px 7px;
    font-size: 11px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QPushButton.family_chip:hover {{
    background-color: rgba({rgb}, 0.22);
    border: 1px solid {p['neon_cyan']};
    color: #ffffff;
}}

QPushButton.family_chip_active {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba({rgb}, 0.35), stop:1 rgba(176, 38, 255, 0.35));
    color: {p['neon_cyan']};
    border: 1.5px solid {p['neon_cyan']};
    border-radius: 9px;
    padding: 3px 7px;
    font-size: 11px;
    font-weight: bold;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

/* Input Box */
QTextEdit#InputEdit {{
    background-color: {'rgba(10, 14, 23, 0.85)' if is_dark else 'rgba(255, 255, 255, 0.95)'};
    color: {p['text_main']};
    border: 1px solid rgba({rgb}, 0.35);
    border-radius: 12px;
    padding: 8px 12px;
    font-size: 13px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QTextEdit#InputEdit:focus {{
    border: 1px solid {p['neon_cyan']};
    background-color: {'rgba(10, 14, 23, 0.95)' if is_dark else '#ffffff'};
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
    background-color: {'rgba(255, 255, 255, 0.06)' if is_dark else 'rgba(0, 0, 0, 0.04)'};
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
    is_bento = p.get("style_family") == "bento"
    border_col = p.get("border_color", p.get("neon_cyan", "#38bdf8"))
    bg = p.get("bg_glass", "rgba(28, 28, 32, 0.96)")

    return f"""
QFrame#BubbleFrame {{
    background-color: {bg};
    border: {'1px solid ' + border_col if is_bento else '1.5px solid ' + p.get('neon_cyan', '#00f3ff')};
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
    is_bento = p.get("style_family") == "bento"
    is_dark = p.get("is_dark", True)
    border_col = p.get("border_color", p.get("neon_cyan", "#38bdf8"))
    accent = p.get("title_color", p.get("neon_cyan", "#00f3ff"))

    if is_bento:
        return f"""
QWidget#SettingsWidget {{
    background-color: {p['bg_glass']};
    border: 1px solid {border_col};
    border-radius: 18px;
}}

QTabWidget::pane {{
    border: 1px solid rgba(255, 255, 255, 0.07);
    background: transparent;
    border-radius: 10px;
}}

QTabBar::tab {{
    background: rgba(255, 255, 255, 0.04);
    color: {p['text_muted']};
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: none;
    padding: 8px 14px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
    font-size: 11px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 3px;
}}

QTabBar::tab:selected {{
    background: rgba(255, 255, 255, 0.12);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-bottom: none;
    font-weight: 600;
}}

QLabel {{
    color: {p['text_main']};
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QLineEdit, QComboBox {{
    background-color: {p.get('input_bg', '#161619')};
    color: {p['text_main']};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 11px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QLineEdit:focus, QComboBox:focus {{
    border: 1px solid rgba(255, 255, 255, 0.28);
}}

QPushButton.primary_btn {{
    background: {p.get('send_btn_bg', '#ffffff')};
    color: {p.get('send_btn_text', '#121214')};
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 11px;
}}

QPushButton.primary_btn:hover {{
    background: {p.get('send_btn_hover', '#f4f4f5')};
}}
"""

    # Classic Neon
    rgb = hex_to_rgb(p.get("neon_cyan", "#00f3ff"))
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
    padding: 8px 16px;
    font-size: 11px;
}}

QPushButton.primary_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #25f5ff, stop:1 #c24bff);
}}
"""


# Static Default Stylesheet Exports
CHAT_WINDOW_QSS = get_chat_window_qss(PALETTE)
SETTINGS_QSS = get_settings_qss(PALETTE)
SPEECH_BUBBLE_QSS = get_speech_bubble_qss(PALETTE)


import os
import sys
import logging
from pathlib import Path

# Ensure root directory is in sys.path
root_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(root_dir))

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QPoint

from agent.engine import AgentEngine
from agent.tts import TTSEngine
from ui.mascot import DesktopMascot
from ui.chat_window import ChatWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("NovaAgent.Main")


def create_tray_icon_pixmap() -> QPixmap:
    """Generates an in-memory glowing neon cyber icon for the tray."""
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(16, 23, 38))
    painter.setPen(QColor(0, 243, 255))
    painter.drawRoundedRect(2, 2, 28, 28, 8, 8)
    painter.setBrush(QColor(0, 243, 255))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(8, 12, 6, 6)
    painter.drawEllipse(18, 12, 6, 6)
    painter.setPen(QColor(0, 255, 170))
    painter.drawLine(10, 22, 22, 22)
    painter.end()
    return pix


def main():
    logger.info("Starting Nova Desktop AI Agent...")

    # Force UTF-8 in stdout for Windows
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    app = QApplication(sys.argv)
    app.setApplicationName("نِکسا (NexA) | دستیار هوشمند دسکتاپ - راهکار الکترونیک سهند")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setQuitOnLastWindowClosed(False)

    icon_path = Path(__file__).parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    from agent.key_manager import KeyManager
    from agent.memory import MemoryManager
    from agent.persona import PersonaManager
    from agent.learning import LearningEngine
    from agent.companion import CompanionMonitor
    from ui.settings_window import SettingsWindow
    from ui.theme_detector import WindowsThemeDetector
    from ui.styles import (
        get_palette_for_theme, get_chat_window_qss,
        get_settings_qss, get_speech_bubble_qss
    )

    # 1. Initialize Engines & Managers
    key_manager = KeyManager()
    memory_manager = MemoryManager()
    persona_manager = PersonaManager()
    learning_engine = LearningEngine()
    companion_monitor = CompanionMonitor(persona_manager, app)
    tts_engine = TTSEngine(enabled=True, gender=persona_manager.gender.value, key_manager=key_manager)
    theme_detector = WindowsThemeDetector(check_interval_ms=3000, parent=app)
    agent_engine = AgentEngine(
        key_manager=key_manager,
        memory_manager=memory_manager,
        persona_manager=persona_manager,
        learning_engine=learning_engine
    )

    # 2. Instantiate UI Components
    mascot = DesktopMascot()
    mascot.set_avatar_style(persona_manager.avatar_style)
    mascot.set_mascot_scale(persona_manager.mascot_scale)

    chat_window = ChatWindow(agent_engine, tts_engine)
    settings_window = SettingsWindow(
        key_manager=key_manager,
        memory_manager=memory_manager,
        persona_manager=persona_manager,
        learning_engine=learning_engine,
        tts_engine=tts_engine,
        multi_ai=agent_engine.multi_ai,
        family_manager=agent_engine.family_manager,
        services_config=agent_engine.services_config
    )

    # Function to dynamically apply Windows OS Theme & Accent
    def apply_os_theme(is_dark: bool, accent_color: str):
        if not persona_manager.sync_with_os_theme:
            return
        logger.info(f"Applying OS Theme: Dark={is_dark}, Accent={accent_color}")
        pal = get_palette_for_theme(is_dark=is_dark, accent_color=accent_color)
        chat_window.central_widget.setStyleSheet(get_chat_window_qss(pal))
        settings_window.widget.setStyleSheet(get_settings_qss(pal))
        if hasattr(mascot, "bubble") and hasattr(mascot.bubble, "bubble_frame"):
            mascot.bubble.bubble_frame.setStyleSheet(get_speech_bubble_qss(pal))
        mascot.set_persona_colors(pal["neon_cyan"], pal["neon_purple"])

    # Apply initial theme
    if persona_manager.sync_with_os_theme:
        apply_os_theme(theme_detector.is_dark_mode(), theme_detector.get_accent_color())
    else:
        initial_colors = persona_manager.get_accent_colors()
        mascot.set_persona_colors(initial_colors["primary"], initial_colors["secondary"])

    # Position mascot at bottom-right corner of screen
    screen = app.primaryScreen()
    if screen:
        geo = screen.availableGeometry()
        init_x = geo.right() - mascot.width() - 30
        init_y = geo.bottom() - mascot.height() - 30
        mascot.move(init_x, init_y)

        # Position chat window beside the mascot
        chat_x = max(geo.left() + 20, init_x - chat_window.width() - 20)
        chat_y = max(geo.top() + 20, geo.bottom() - chat_window.height() - 30)
        chat_window.move(chat_x, chat_y)

        # Center settings window on screen
        sett_x = geo.left() + (geo.width() - settings_window.width()) // 2
        sett_y = geo.top() + (geo.height() - settings_window.height()) // 2
        settings_window.move(sett_x, sett_y)

    # 3. Connect Signals
    def toggle_chat():
        if chat_window.isVisible():
            chat_window.hide()
        else:
            # Re-align chat window near current mascot position
            if screen:
                geo = screen.availableGeometry()
                m_pos = mascot.pos()
                target_x = m_pos.x() - chat_window.width() - 15
                if target_x < geo.left():
                    target_x = m_pos.x() + mascot.width() + 15
                target_y = max(geo.top() + 10, min(m_pos.y() - 200, geo.bottom() - chat_window.height() - 10))
                chat_window.move(target_x, target_y)
            chat_window.show()
            chat_window.raise_()
            chat_window.activateWindow()

    def toggle_settings():
        if settings_window.isVisible():
            settings_window.hide()
        else:
            settings_window.refresh_keys_table()
            settings_window.refresh_memories_list()
            settings_window.refresh_learnings_table()
            settings_window.refresh_family_tab()
            settings_window.show()
            settings_window.raise_()
            settings_window.activateWindow()

    mascot.clicked.connect(toggle_chat)
    mascot.double_clicked.connect(lambda: (chat_window._capture_screen_to_input(), toggle_chat()))
    mascot.screenshot_requested.connect(lambda: (chat_window._capture_screen_to_input(), toggle_chat()))
    mascot.webcam_requested.connect(lambda: (chat_window._capture_webcam_to_input(), toggle_chat()))
    mascot.diagnostics_requested.connect(
        lambda: (chat_window.show(), chat_window._on_chip_clicked("وضعیت سخت‌افزار، حافظه و سیستم‌عامل سیستم را بررسی کن"))
    )
    mascot.settings_requested.connect(toggle_settings)
    chat_window.settings_requested.connect(toggle_settings)

    # Persona changed: update mascot colors and re-init agent prompt
    def on_persona_updated(new_gender: str):
        if persona_manager.sync_with_os_theme:
            apply_os_theme(theme_detector.is_dark_mode(), theme_detector.get_accent_color())
        else:
            colors = persona_manager.get_accent_colors()
            mascot.set_persona_colors(colors["primary"], colors["secondary"])
        agent_engine._init_client_and_chat()
        chat_window.title_label.setText(f"🤖 {persona_manager.name} | نِکسا")

    def on_companion_updated():
        mascot.set_mascot_scale(persona_manager.mascot_scale)
        if persona_manager.sync_with_os_theme:
            apply_os_theme(theme_detector.is_dark_mode(), theme_detector.get_accent_color())
        else:
            colors = persona_manager.get_accent_colors()
            mascot.set_persona_colors(colors["primary"], colors["secondary"])
        agent_engine._init_client_and_chat()
        chat_window.title_label.setText(f"🤖 {persona_manager.name} | نِکسا")

    def on_wellness_alert(tip_message: str):
        mascot.say(tip_message, duration_ms=9000)
        if tts_engine.enabled:
            tts_engine.speak(tip_message)

    settings_window.persona_changed.connect(on_persona_updated)
    settings_window.companion_updated.connect(on_companion_updated)
    settings_window.avatar_changed.connect(mascot.set_avatar_style)
    mascot.avatar_changed.connect(persona_manager.set_avatar_style)
    companion_monitor.wellness_reminder.connect(on_wellness_alert)
    theme_detector.theme_changed.connect(apply_os_theme)

    # Refresh agent engine when keys, memory or learnings change
    settings_window.keys_changed.connect(lambda: (
        setattr(agent_engine, 'api_key', key_manager.get_active_key()),
        agent_engine._init_client_and_chat()
    ))
    settings_window.memory_changed.connect(lambda: (
        agent_engine._init_client_and_chat()
    ))
    settings_window.learning_changed.connect(lambda: (
        agent_engine._init_client_and_chat()
    ))

    def on_family_member_switched(member):
        logger.info(f"Family member switched to: {member.name} ({member.role_title})")
        mascot.set_avatar_style(member.avatar_style)
        mascot.set_persona_colors(member.primary_color, member.secondary_color)
        chat_window.title_label.setText(f"🤖 {member.name} ({member.role_title}) | نِکسا")
        if member.gender:
            tts_engine.gender = member.gender

    agent_engine.on_family_member_changed = on_family_member_switched
    settings_window.family_member_switched.connect(on_family_member_switched)
    settings_window.family_member_updated.connect(lambda m: agent_engine._init_client_and_chat())

    chat_window.mascot_state_signal.connect(mascot.set_state)
    chat_window.mascot_speech_signal.connect(mascot.say)

    # 4. System Tray Icon
    app_icon_file = Path(__file__).parent / "assets" / "icon.png"
    tray_qicon = QIcon(str(app_icon_file)) if app_icon_file.exists() else QIcon(create_tray_icon_pixmap())
    tray_icon = QSystemTrayIcon(tray_qicon, app)

    def on_quota_alert(severity: str, message: str):
        icon_type = QSystemTrayIcon.MessageIcon.Critical if severity == "critical" else QSystemTrayIcon.MessageIcon.Warning
        tray_icon.showMessage("⚠️ هشدار اعتبار دستیار هوشمند", message, icon_type, 6000)

    chat_window.quota_alert_signal.connect(on_quota_alert)
    tray_menu = QMenu()
    tray_menu.setStyleSheet("""
        QMenu { background: #0f172a; color: #f8fafc; border: 1px solid #00f3ff; border-radius: 6px; }
        QMenu::item:selected { background: rgba(0, 243, 255, 0.2); }
    """)

    act_show_chat = QAction("💬 باز کردن چت و دستورات", tray_menu)
    act_show_chat.triggered.connect(toggle_chat)
    tray_menu.addAction(act_show_chat)

    act_show_sett = QAction("⚙️ تنظیمات و کلیدهای API", tray_menu)
    act_show_sett.triggered.connect(toggle_settings)
    tray_menu.addAction(act_show_sett)

    act_toggle_mascot = QAction("👁️ نمایش / پنهان کردن ربات", tray_menu)
    act_toggle_mascot.triggered.connect(lambda: mascot.setVisible(not mascot.isVisible()))
    tray_menu.addAction(act_toggle_mascot)

    tray_menu.addSeparator()

    act_quit = QAction("❌ خروج کامل", tray_menu)
    act_quit.triggered.connect(app.quit)
    tray_menu.addAction(act_quit)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("نِکسا (NexA) | راهکار الکترونیک سهند (irres.ir)")
    tray_icon.show()

    # 5. Show Mascot and Proactive Daily Greeting
    mascot.show()
    if persona_manager.daily_greeting_enabled:
        greeting = companion_monitor.get_greeting()
        mascot.say(greeting, duration_ms=8000)
        if tts_engine.enabled:
            tts_engine.speak(greeting)
    else:
        mascot.say(f"سلام! من {persona_manager.name} هستم 🤖 روی من کلیک کن یا دستورت رو بگو!", duration_ms=6000)

    logger.info("NexA Desktop Agent is now running.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

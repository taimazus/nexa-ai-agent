import math
import logging
from enum import Enum
from typing import Optional

from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient,
    QRadialGradient, QAction, QPainterPath, QCursor
)

from ui.speech_bubble import SpeechBubble
from agent.persona import AvatarStyle, MascotScale

logger = logging.getLogger("SahandYar.Mascot")


class MascotState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    SPEAKING = "speaking"
    SUCCESS = "success"
    ERROR = "error"

    @classmethod
    def from_string(cls, name: str) -> "MascotState":
        for state in cls:
            if state.value == (name or "").lower().strip():
                return state
        return cls.IDLE


class DesktopMascot(QWidget):
    """
    Volumetric, hyper-realistic 3D animated desktop pet for SahandYar AI.
    Features:
    - 8 selectable 3D character avatars (Cyber Bot, Neko, Astral Orb, Panda,
      Azure Sphere, Carbon Chrono, DJ Headset Pod, Quantum Diamond Prism).
    - Living interactive dynamics: gaze tracking toward cursor, natural eyelid blinking,
      playful winks on click, and reactive lip-sync mouth opening when speaking.
    - Volumetric specular lighting, depth drop-shadows, and smooth float physics.
    """
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    screenshot_requested = pyqtSignal()
    webcam_requested = pyqtSignal()
    diagnostics_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    avatar_changed = pyqtSignal(str)
    family_member_switch_requested = pyqtSignal(str)
    theme_switch_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(160, 160)
        self.setMouseTracking(True)

        self.state = MascotState.IDLE
        self.avatar_style = AvatarStyle.CYBER_BOT
        self.tick = 0
        self.drag_position = QPoint()
        self.is_dragging = False

        # Eye tracking coordinates (smoothed toward mouse cursor)
        self.pupil_x = 0.0
        self.pupil_y = 0.0

        # Eyelid & Wink state
        self.wink_timer = 0
        self.is_hovered = False

        self.custom_primary_color = QColor(0, 243, 255)
        self.custom_secondary_color = QColor(176, 38, 255)

        # Speech bubble helper
        self.speech_bubble = SpeechBubble()

        # Animation timer (30 FPS for smooth organic animation without high CPU overhead)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_tick)
        self.anim_timer.start(33)

        self.setToolTip("دستیار هوشمند سَهندیار (SahandYar AI)\nطراحی و توسعه: شرکت راهکار الکترونیک سهند (irres.ir)\nبرای چت کلیک کنید، با ماوس جابجا کنید")

    def set_persona_colors(self, primary_hex: str, secondary_hex: str):
        self.custom_primary_color = QColor(primary_hex)
        self.custom_secondary_color = QColor(secondary_hex)
        self.update()

    def set_avatar_style(self, new_style: AvatarStyle or str):
        if isinstance(new_style, str):
            new_style = AvatarStyle.from_string(new_style)
        self.avatar_style = new_style
        self.update()
        logger.info(f"Desktop mascot visual avatar set to: {self.avatar_style.value}")

    def set_mascot_scale(self, scale: MascotScale or str):
        if isinstance(scale, str):
            scale = MascotScale.from_string(scale)
        dim = scale.dimensions
        self.setFixedSize(dim, dim)
        self.update()
        logger.info(f"Desktop mascot scale updated to: {scale.value} ({dim}x{dim})")

    def set_state(self, new_state: MascotState or str):
        if isinstance(new_state, str):
            new_state = MascotState.from_string(new_state)
        self.state = new_state
        self.update()

    def trigger_wink(self):
        """Triggers an affectionate, playful wink reaction."""
        self.wink_timer = 20
        self.update()

    def _on_tick(self):
        self.tick += 1

        if self.wink_timer > 0:
            self.wink_timer -= 1

        # Smooth gaze tracking toward global cursor position
        try:
            cursor_global = QCursor.pos()
            local_cursor = self.mapFromGlobal(cursor_global)
            cx = self.width() / 2.0
            cy = self.height() / 2.0
            target_x = max(-5.0, min(5.0, (local_cursor.x() - cx) / 20.0))
            target_y = max(-4.0, min(4.0, (local_cursor.y() - cy) / 20.0))

            # Exponential smoothing for natural eye saccades
            self.pupil_x += (target_x - self.pupil_x) * 0.25
            self.pupil_y += (target_y - self.pupil_y) * 0.25
        except Exception:
            self.pupil_x = 0.0
            self.pupil_y = 0.0

        self.update()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def say(self, message: str, duration_ms: int = 5000):
        """Displays floating speech bubble. Mouth lip-sync is strictly driven by real-time audio playback."""
        self.speech_bubble.show_message(
            message,
            self.pos(),
            (self.width(), self.height()),
            duration_ms
        )

    def _revert_speaking_to_idle(self):
        if self.state == MascotState.SPEAKING:
            self.set_state(MascotState.IDLE)

    # --- Mouse Drag & Click Handling ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.is_dragging = False
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            self.is_dragging = True
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_dragging:
                self.trigger_wink()
                self.clicked.emit()
            self.is_dragging = False
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
            event.accept()

    def _show_context_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0d131f;
                border: 1px solid #00f3ff;
                border-radius: 8px;
                padding: 6px;
                color: #f1f5f9;
                font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(0, 243, 255, 0.2);
                color: #00f3ff;
            }
        """)

        chat_act = QAction("💬 باز کردن مرکز فرمان و چت", self)
        chat_act.triggered.connect(self.clicked.emit)
        menu.addAction(chat_act)

        # Family Members Submenu
        family_menu = menu.addMenu("👥 اعضای خانواده نِکسا")
        family_menu.setStyleSheet(menu.styleSheet())
        family_members_list = [
            ("nexamehr", "🛡️ نِکسامِهر (پدر - معمار سیستم و سخت‌افزار)"),
            ("nexanoo", "🌸 نِکسانو (مادر - هماهنگ‌کننده و سلامت)"),
            ("samyar", "💻 سامیار (مهندس نرم‌افزار و برنامه‌نویس)"),
            ("artin", "⚡ آرتین (کنترل ویندوز و نرم‌افزارها)"),
            ("nila", "🔍 نیلا (جستجوگر وب و تحلیل داده)"),
            ("tara", "🎨 تارا (طراح خلاق و پردازش تصویر)")
        ]
        for m_id, m_title in family_members_list:
            m_act = QAction(m_title, family_menu)
            m_act.triggered.connect(lambda ch, mid=m_id: self.family_member_switch_requested.emit(mid))
            family_menu.addAction(m_act)

        # Theme Styles Submenu (Bento & Modern Aesthetics)
        theme_menu = menu.addMenu("🍱 تم ظاهری برنامه (Bento UI)")
        theme_menu.setStyleSheet(menu.styleSheet())
        themes_list = [
            ("bento_dark", "🍱 بنتو دارک مدرن (اسلیت و گرافیتی - سبک تصویر)"),
            ("bento_light", "✨ بنتو سرامیکی لوکس (استودیو سفید)"),
            ("bento_espresso", "☕ بنتو شکلاتی گرم (Warm Espresso)"),
            ("oled_obsidian", "🖤 آبسیدین مینیمال (مشکی خالص OLED)"),
            ("nordic_titanium", "🌊 نوردیک تیتانیوم (آبی و نقره‌ای)"),
            ("cyber_cyan", "⚡ سایبرپانک نئون (کلاسیک فیروزه‌ای)")
        ]
        for t_id, t_title in themes_list:
            t_act = QAction(t_title, theme_menu)
            t_act.triggered.connect(lambda ch, tid=t_id: self.theme_switch_requested.emit(tid))
            theme_menu.addAction(t_act)

        # Avatar Submenu
        avatar_menu = menu.addMenu("🎨 تغییر شکلک سه‌بعدی")
        avatar_menu.setStyleSheet(menu.styleSheet())

        avatars_info = [
            (AvatarStyle.CYBER_BOT, "🤖 ربات نئونی هوشمند (Cyber Bot)"),
            (AvatarStyle.CYBER_SPHERE, "🔵 گوی سایبرنتیک آبی (Azure Orb)"),
            (AvatarStyle.CARBON_LENS, "⚙️ ربات لنز مکانیکی کربنی (Carbon Chrono)"),
            (AvatarStyle.DJ_HEADSET, "🎧 ربات هدست گیمینگ (Headset Pod)"),
            (AvatarStyle.CRYSTAL_PRISM, "💎 گوی کریستالی الماس (Quantum Prism)"),
            (AvatarStyle.CYBER_CAT, "🐱 گربه بامزه سایبری (Cyber Neko)"),
            (AvatarStyle.ASTRAL_ORB, "✨ گوی کوانتومی و بال‌های فرشته"),
            (AvatarStyle.ASTRO_PANDA, "🐼 پاندای فضانورد دوست‌داشتنی")
        ]
        for style_enum, title in avatars_info:
            act = QAction(title, avatar_menu)
            act.setCheckable(True)
            act.setChecked(self.avatar_style == style_enum)
            act.triggered.connect(lambda ch, s=style_enum: self._on_switch_avatar(s))
            avatar_menu.addAction(act)

        diag_act = QAction("⚡ بررسی وضعیت ویندوز", self)
        diag_act.triggered.connect(self.diagnostics_requested.emit)
        menu.addAction(diag_act)

        screen_act = QAction("📸 تصویربرداری از صفحه و تحلیل", self)
        screen_act.triggered.connect(self.screenshot_requested.emit)
        menu.addAction(screen_act)

        webcam_act = QAction("📷 دیدن از وب‌کم و تحلیل", self)
        webcam_act.triggered.connect(self.webcam_requested.emit)
        menu.addAction(webcam_act)

        sett_act = QAction("⚙️ تنظیمات و حافظه", self)
        sett_act.triggered.connect(self.settings_requested.emit)
        menu.addAction(sett_act)

        menu.addSeparator()

        quit_act = QAction("❌ خروج", self)
        quit_act.triggered.connect(self._close_app)
        menu.addAction(quit_act)

        menu.exec(global_pos)

    def _on_switch_avatar(self, style: AvatarStyle):
        self.set_avatar_style(style)
        self.avatar_changed.emit(style.value)

    def _close_app(self):
        from PyQt6.QtWidgets import QApplication
        self.speech_bubble.close()
        QApplication.quit()

    # --- 3D Vector & Physics Rendering ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Hover offset with sinusoidal 3D float physics
        hover_y = math.sin(self.tick * 0.08) * 6
        if self.is_hovered:
            hover_y -= 3  # Perky cheerful bounce on hover

        cx = self.width() / 2.0
        cy = self.height() / 2.0 + hover_y

        # Dynamic primary and secondary palette
        if self.state == MascotState.IDLE:
            primary = self.custom_primary_color
            secondary = self.custom_secondary_color
        elif self.state == MascotState.THINKING:
            primary = self.custom_secondary_color
            secondary = self.custom_primary_color
        elif self.state == MascotState.WORKING:
            primary = QColor(255, 183, 3)    # Amber/Gold
            secondary = self.custom_primary_color
        elif self.state == MascotState.SPEAKING:
            primary = QColor(0, 255, 170)    # Emerald/Cyan
            secondary = self.custom_primary_color
        elif self.state == MascotState.SUCCESS:
            primary = QColor(0, 255, 170)    # Green
            secondary = QColor(255, 215, 0)  # Gold
        else:  # ERROR / ALERT
            primary = QColor(255, 77, 109)   # Neon Red
            secondary = QColor(255, 183, 3)

        # 1. 3D Ground Depth Shadow
        shadow_w = 52 - hover_y * 1.5
        shadow_h = 14 - hover_y * 0.5
        shadow_grad = QRadialGradient(cx, 145, shadow_w / 2)
        shadow_grad.setColorAt(0.0, QColor(0, 0, 0, 80))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(shadow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - shadow_w / 2, 145 - shadow_h / 2, shadow_w, shadow_h))

        # 2. Render Selected 3D Avatar
        if self.avatar_style == AvatarStyle.CYBER_CAT:
            self._draw_cyber_cat(painter, cx, cy, primary, secondary)
        elif self.avatar_style == AvatarStyle.ASTRAL_ORB:
            self._draw_astral_orb(painter, cx, cy, primary, secondary)
        elif self.avatar_style == AvatarStyle.ASTRO_PANDA:
            self._draw_astro_panda(painter, cx, cy, primary, secondary)
        elif self.avatar_style == AvatarStyle.CYBER_SPHERE:
            self._draw_cyber_sphere(painter, cx, cy, primary, secondary)
        elif self.avatar_style == AvatarStyle.CARBON_LENS:
            self._draw_carbon_lens(painter, cx, cy, primary, secondary)
        elif self.avatar_style == AvatarStyle.DJ_HEADSET:
            self._draw_dj_headset(painter, cx, cy, primary, secondary)
        elif self.avatar_style == AvatarStyle.CRYSTAL_PRISM:
            self._draw_crystal_prism(painter, cx, cy, primary, secondary)
        else:
            self._draw_cyber_bot(painter, cx, cy, primary, secondary)

    # ==========================================
    # AVATAR 1: Cyber Neon Bot (ربات نئونی هوشمند)
    # ==========================================
    def _draw_cyber_bot(self, painter: QPainter, cx: float, cy: float, primary: QColor, secondary: QColor):
        # Outer Glow
        glow_rad = QRadialGradient(cx, cy, 65)
        glow_color = QColor(primary)
        glow_color.setAlpha(40 + int(math.sin(self.tick * 0.1) * 15))
        glow_rad.setColorAt(0.0, glow_color)
        glow_rad.setColorAt(0.7, QColor(secondary.red(), secondary.green(), secondary.blue(), 15))
        glow_rad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_rad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(cx), int(cy)), 65, 65)

        # Holographic Revolving Rings
        ring_angle = (self.tick * 3) % 360
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(ring_angle)
        painter.setPen(QPen(primary, 1.8, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(-48, -48, 96, 96))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(secondary))
        painter.drawEllipse(QPoint(48, 0), 4, 4)
        painter.drawEllipse(QPoint(-48, 0), 3, 3)
        painter.restore()

        # Antenna Nodes
        painter.setPen(QPen(primary, 2))
        painter.drawLine(int(cx - 36), int(cy - 10), int(cx - 44), int(cy - 22))
        painter.drawLine(int(cx + 36), int(cy - 10), int(cx + 44), int(cy - 22))
        painter.setBrush(QBrush(secondary))
        painter.drawEllipse(QPoint(int(cx - 44), int(cy - 22)), 4, 4)
        painter.drawEllipse(QPoint(int(cx + 44), int(cy - 22)), 4, 4)

        # 3D Head Sphere with Specular Light
        head_path = QPainterPath()
        head_rect = QRectF(cx - 38, cy - 34, 76, 68)
        head_path.addRoundedRect(head_rect, 24, 24)

        head_grad = QRadialGradient(cx - 12, cy - 14, 45)
        head_grad.setColorAt(0.0, QColor(45, 58, 82))
        head_grad.setColorAt(0.5, QColor(20, 26, 40))
        head_grad.setColorAt(1.0, QColor(8, 10, 16))

        painter.setBrush(QBrush(head_grad))
        painter.setPen(QPen(primary, 2))
        painter.drawPath(head_path)

        # Visor
        visor_rect = QRectF(cx - 28, cy - 16, 56, 32)
        visor_grad = QLinearGradient(cx, cy - 16, cx, cy + 16)
        visor_grad.setColorAt(0.0, QColor(5, 7, 12))
        visor_grad.setColorAt(1.0, QColor(12, 16, 26))
        painter.setBrush(QBrush(visor_grad))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 130), 1.2))
        painter.drawRoundedRect(visor_rect, 10, 10)

        # Visor Expressions
        self._draw_visor_expressions(painter, cx, cy, primary)

    # ==========================================
    # AVATAR 2: 3D Cyber Neko (گربه کاوایی سایبری)
    # ==========================================
    def _draw_cyber_cat(self, painter: QPainter, cx: float, cy: float, primary: QColor, secondary: QColor):
        glow_rad = QRadialGradient(cx, cy, 60)
        glow_rad.setColorAt(0.0, QColor(primary.red(), primary.green(), primary.blue(), 50))
        glow_rad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_rad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(cx), int(cy)), 60, 60)

        # 3D Fluffy Holographic Cat Ears
        ear_l = QPainterPath()
        ear_l.moveTo(cx - 36, cy - 12)
        ear_l.lineTo(cx - 32, cy - 42)
        ear_l.lineTo(cx - 10, cy - 30)
        ear_l.closeSubpath()

        ear_r = QPainterPath()
        ear_r.moveTo(cx + 36, cy - 12)
        ear_r.lineTo(cx + 32, cy - 42)
        ear_r.lineTo(cx + 10, cy - 30)
        ear_r.closeSubpath()

        ear_grad = QLinearGradient(cx, cy - 45, cx, cy)
        ear_grad.setColorAt(0.0, secondary)
        ear_grad.setColorAt(1.0, QColor(18, 22, 36))

        painter.setBrush(QBrush(ear_grad))
        painter.setPen(QPen(primary, 2))
        painter.drawPath(ear_l)
        painter.drawPath(ear_r)

        # 3D Head Sphere
        head_rad = QRadialGradient(cx - 12, cy - 12, 42)
        head_rad.setColorAt(0.0, QColor(36, 46, 68))
        head_rad.setColorAt(0.7, QColor(16, 20, 32))
        head_rad.setColorAt(1.0, QColor(8, 10, 18))
        painter.setBrush(QBrush(head_rad))
        painter.setPen(QPen(primary, 1.8))
        painter.drawEllipse(QRectF(cx - 36, cy - 30, 72, 64))

        # Rosy Cute Blushing Cheeks
        painter.setPen(Qt.PenStyle.NoPen)
        blush_color = QColor(255, 60, 130, 120 + int(math.sin(self.tick * 0.1) * 30))
        painter.setBrush(QBrush(blush_color))
        painter.drawEllipse(QRectF(cx - 26, cy + 4, 10, 6))
        painter.drawEllipse(QRectF(cx + 16, cy + 4, 10, 6))

        # Eyes with Gaze Tracking & Blinking
        blink = (self.tick % 120) > 113 or self.state == MascotState.SUCCESS
        if blink:
            painter.setPen(QPen(primary, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(cx - 22, cy - 10, 12, 10), 0, 180 * 16)
            painter.drawArc(QRectF(cx + 10, cy - 10, 12, 10), 0, 180 * 16)
        else:
            painter.setBrush(QBrush(QColor(8, 12, 20)))
            painter.setPen(QPen(primary, 1.2))
            painter.drawEllipse(QRectF(cx - 22, cy - 12, 13, 17))
            painter.drawEllipse(QRectF(cx + 9, cy - 12, 13, 17))

            # Pupil with Gaze Tracking
            px = self.pupil_x * 0.7
            py = self.pupil_y * 0.7
            painter.setBrush(QBrush(primary))
            painter.drawEllipse(QRectF(cx - 20 + px, cy - 9 + py, 9, 12))
            painter.drawEllipse(QRectF(cx + 11 + px, cy - 9 + py, 9, 12))

            # Specular light (dual Pixar catchlights)
            painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
            painter.drawEllipse(QPointF(cx - 16 + px, cy - 6 + py), 3.0, 3.0)
            painter.drawEllipse(QPointF(cx - 13 + px, cy - 2 + py), 1.5, 1.5)
            painter.drawEllipse(QPointF(cx + 15 + px, cy - 6 + py), 3.0, 3.0)
            painter.drawEllipse(QPointF(cx + 18 + px, cy - 2 + py), 1.5, 1.5)

        # Expressive Dynamic Eyebrows
        self._draw_expressive_eyebrows(painter, cx, cy - 18, spacing=16, color=primary)

        # Mouth Lip-Sync
        self._draw_interactive_mouth(painter, cx, cy + 8, primary)

    # ==========================================
    # AVATAR 3: Quantum Astral Orb (گوی کوانتومی)
    # ==========================================
    def _draw_astral_orb(self, painter: QPainter, cx: float, cy: float, primary: QColor, secondary: QColor):
        wing_flutter = math.sin(self.tick * 0.15) * 8
        painter.save()
        painter.translate(cx, cy)
        wing_l = QPainterPath()
        wing_l.moveTo(-20, 0)
        wing_l.cubicTo(-48, -25 + wing_flutter, -58, -5 + wing_flutter, -22, 16)
        wing_r = QPainterPath()
        wing_r.moveTo(20, 0)
        wing_r.cubicTo(48, -25 - wing_flutter, 58, -5 - wing_flutter, 22, 16)

        wing_grad = QLinearGradient(0, -30, 0, 20)
        wing_grad.setColorAt(0.0, QColor(primary.red(), primary.green(), primary.blue(), 180))
        wing_grad.setColorAt(1.0, QColor(secondary.red(), secondary.green(), secondary.blue(), 20))
        painter.setBrush(QBrush(wing_grad))
        painter.setPen(QPen(primary, 1.5))
        painter.drawPath(wing_l)
        painter.drawPath(wing_r)
        painter.restore()

        # Core Orb
        core_grad = QRadialGradient(cx - 8, cy - 8, 36)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 240))
        core_grad.setColorAt(0.4, primary)
        core_grad.setColorAt(0.8, secondary)
        core_grad.setColorAt(1.0, QColor(10, 12, 24))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(QPen(primary, 2))
        painter.drawEllipse(QRectF(cx - 30, cy - 30, 60, 60))

        # Dynamic Visor Expressions inside core
        self._draw_visor_expressions(painter, cx, cy, primary)

    # ==========================================
    # AVATAR 4: Astro Panda (پاندای فضانورد)
    # ==========================================
    def _draw_astro_panda(self, painter: QPainter, cx: float, cy: float, primary: QColor, secondary: QColor):
        # 3D Astronaut White Helmet Body
        helmet_grad = QRadialGradient(cx - 14, cy - 14, 46)
        helmet_grad.setColorAt(0.0, QColor(240, 246, 255))
        helmet_grad.setColorAt(0.6, QColor(190, 205, 225))
        helmet_grad.setColorAt(1.0, QColor(40, 52, 70))
        painter.setBrush(QBrush(helmet_grad))
        painter.setPen(QPen(primary, 2))
        painter.drawEllipse(QRectF(cx - 36, cy - 32, 72, 68))

        # 3D Glass Bubble Face Visor
        visor_rect = QRectF(cx - 28, cy - 20, 56, 44)
        visor_grad = QLinearGradient(cx, cy - 20, cx, cy + 24)
        visor_grad.setColorAt(0.0, QColor(10, 15, 28, 240))
        visor_grad.setColorAt(1.0, QColor(20, 30, 50, 240))
        painter.setBrush(QBrush(visor_grad))
        painter.setPen(QPen(primary, 1.6))
        painter.drawRoundedRect(visor_rect, 18, 18)

        # Eye Patches & Gaze Tracking
        blink = (self.tick % 115) > 108 or self.state == MascotState.SUCCESS
        if blink:
            painter.setPen(QPen(primary, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(cx - 20, cy - 8, 10, 8), 0, 180 * 16)
            painter.drawArc(QRectF(cx + 10, cy - 8, 10, 8), 0, 180 * 16)
        else:
            px = self.pupil_x * 0.6
            py = self.pupil_y * 0.6
            painter.setBrush(QBrush(primary))
            painter.drawEllipse(QRectF(cx - 18 + px, cy - 8 + py, 8, 10))
            painter.drawEllipse(QRectF(cx + 10 + px, cy - 8 + py, 8, 10))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(QPoint(int(cx - 15 + px), int(cy - 5 + py)), 2, 2)
            painter.drawEllipse(QPoint(int(cx + 13 + px), int(cy - 5 + py)), 2, 2)

        # Panda Cute Snout & Smile
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.drawEllipse(QRectF(cx - 8, cy + 4, 16, 12))
        painter.setBrush(QBrush(QColor(20, 25, 38)))
        painter.drawEllipse(QRectF(cx - 4, cy + 5, 8, 5))
        self._draw_interactive_mouth(painter, cx, cy + 9, QColor(20, 25, 38))

    # =========================================================================
    # AVATAR 5: Azure Sphere / Cyber Pod (گوی سایبرنتیک آبی - طرح مرجع Bing)
    # =========================================================================
    def _draw_cyber_sphere(self, painter: QPainter, cx: float, cy: float, primary: QColor, secondary: QColor):
        # 3D Deep Metallic Blue Sphere with Specular Spot
        sphere_rad = QRadialGradient(cx - 14, cy - 14, 46)
        sphere_rad.setColorAt(0.0, QColor(90, 160, 255))
        sphere_rad.setColorAt(0.4, QColor(30, 95, 215))
        sphere_rad.setColorAt(0.8, QColor(14, 45, 120))
        sphere_rad.setColorAt(1.0, QColor(6, 16, 50))
        painter.setBrush(QBrush(sphere_rad))
        painter.setPen(QPen(QColor(0, 243, 255), 1.6))
        painter.drawEllipse(QRectF(cx - 38, cy - 38, 76, 76))

        # Ear Sensor Gadget (Left)
        painter.setBrush(QBrush(QColor(200, 220, 245)))
        painter.setPen(QPen(QColor(20, 40, 80), 1.5))
        painter.drawEllipse(QRectF(cx - 46, cy - 6, 14, 14))
        painter.setBrush(QBrush(QColor(0, 243, 255)))
        painter.drawEllipse(QRectF(cx - 43, cy - 3, 8, 8))

        # Eyes with Gaze Tracking & Eyelids
        blink = (self.tick % 115) > 108 or self.state == MascotState.SUCCESS or self.wink_timer > 0
        if blink and self.wink_timer == 0:
            painter.setPen(QPen(QColor(0, 243, 255), 2.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(QRectF(cx - 22, cy - 10, 12, 10), 0, 180 * 16)
            painter.drawArc(QRectF(cx + 10, cy - 10, 12, 10), 0, 180 * 16)
        else:
            px = self.pupil_x * 0.7
            py = self.pupil_y * 0.7
            # Left Eye
            painter.setBrush(QBrush(QColor(5, 12, 30)))
            painter.drawEllipse(QRectF(cx - 24, cy - 12, 14, 18))
            painter.setBrush(QBrush(QColor(0, 243, 255)))
            painter.drawEllipse(QRectF(cx - 22 + px, cy - 9 + py, 10, 12))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(QPoint(int(cx - 18 + px), int(cy - 6 + py)), 3, 3)

            # Right Eye (Wink reacts on click)
            if self.wink_timer > 0:
                painter.setPen(QPen(QColor(0, 243, 255), 2.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawArc(QRectF(cx + 10, cy - 7, 12, 8), 0, 180 * 16)
            else:
                painter.setBrush(QBrush(QColor(5, 12, 30)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(cx + 10, cy - 12, 14, 18))
                painter.setBrush(QBrush(QColor(0, 243, 255)))
                painter.drawEllipse(QRectF(cx + 12 + px, cy - 9 + py, 10, 12))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawEllipse(QPoint(int(cx + 16 + px), int(cy - 6 + py)), 3, 3)

        # Dynamic Expressive Eyebrows
        self._draw_expressive_eyebrows(painter, cx, cy - 16, spacing=17, color=QColor(10, 25, 60))

        # Interactive Lip-Sync Mouth
        self._draw_interactive_mouth(painter, cx, cy + 12, QColor(5, 12, 30))

    # =========================================================================
    # AVATAR 6: Carbon Chrono / Steampunk Lens Bot (طرح ربات لنز برنجی Bing)
    # =========================================================================
    def _draw_carbon_lens(self, painter: QPainter, cx: float, cy: float, primary: QColor, secondary: QColor):
        # 3D Matte Dark Carbon / Titanium Sphere
        body_rad = QRadialGradient(cx - 14, cy - 14, 46)
        body_rad.setColorAt(0.0, QColor(70, 75, 85))
        body_rad.setColorAt(0.5, QColor(36, 40, 48))
        body_rad.setColorAt(1.0, QColor(14, 16, 20))
        painter.setBrush(QBrush(body_rad))
        painter.setPen(QPen(QColor(120, 130, 145), 1.5))
        painter.drawEllipse(QRectF(cx - 38, cy - 38, 76, 76))

        # Carbon fiber texture ring lines
        painter.setPen(QPen(QColor(255, 255, 255, 25), 1))
        painter.drawArc(QRectF(cx - 36, cy - 36, 72, 72), 30 * 16, 120 * 16)

        # Left Mechanical Rotating Brass Chrono / Aperture Eye
        lens_angle = (self.tick * 2) % 360
        painter.save()
        painter.translate(cx - 14, cy - 6)
        painter.rotate(lens_angle)
        # Brass outer rim
        painter.setBrush(QBrush(QColor(212, 175, 55)))
        painter.setPen(QPen(QColor(160, 120, 25), 1.5))
        painter.drawEllipse(QRectF(-14, -14, 28, 28))
        # Inner dark aperture
        painter.setBrush(QBrush(QColor(20, 15, 8)))
        painter.drawEllipse(QRectF(-9, -9, 18, 18))
        # Crosshair / Aperture blades
        painter.setPen(QPen(QColor(255, 215, 0), 1.4))
        painter.drawLine(-7, 0, 7, 0)
        painter.drawLine(0, -7, 0, 7)
        painter.restore()

        # Right Cyan Glowing Eye with Gaze Tracking
        px = self.pupil_x * 0.7
        py = self.pupil_y * 0.7
        painter.setBrush(QBrush(QColor(10, 12, 18)))
        painter.setPen(QPen(QColor(0, 243, 255), 1.2))
        painter.drawEllipse(QRectF(cx + 8, cy - 14, 16, 18))
        # Cyan Glowing Iris
        painter.setBrush(QBrush(QColor(0, 243, 255)))
        painter.drawEllipse(QRectF(cx + 11 + px, cy - 11 + py, 10, 12))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPoint(int(cx + 15 + px), int(cy - 8 + py)), 2, 2)

        # Curious / Puzzled Curved Mouth
        self._draw_interactive_mouth(painter, cx - 2, cy + 14, QColor(0, 243, 255))

    # =========================================================================
    # AVATAR 7: Cream DJ Headset Pod (ربات گیمینگ و هدست مرجع Bing)
    # =========================================================================
    def _draw_dj_headset(self, painter: QPainter, cx: float, cy: float, primary: QColor, secondary: QColor):
        # Headset Headband Arch
        painter.setPen(QPen(QColor(30, 35, 45), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(QRectF(cx - 40, cy - 42, 80, 50), 30 * 16, 120 * 16)

        # 3D Smooth Cream / Porcelain Sphere
        sphere_rad = QRadialGradient(cx - 14, cy - 14, 46)
        sphere_rad.setColorAt(0.0, QColor(255, 252, 242))
        sphere_rad.setColorAt(0.6, QColor(240, 230, 215))
        sphere_rad.setColorAt(1.0, QColor(180, 165, 145))
        painter.setBrush(QBrush(sphere_rad))
        painter.setPen(QPen(QColor(140, 125, 105), 1.5))
        painter.drawEllipse(QRectF(cx - 36, cy - 34, 72, 70))

        # Gaming Headset Earcups (Left & Right)
        painter.setBrush(QBrush(QColor(25, 30, 40)))
        painter.setPen(QPen(QColor(50, 60, 75), 2))
        painter.drawRoundedRect(QRectF(cx - 44, cy - 16, 12, 30), 6, 6)
        painter.drawRoundedRect(QRectF(cx + 32, cy - 16, 12, 30), 6, 6)

        # Boom Microphone extending to mouth
        painter.setPen(QPen(QColor(30, 35, 45), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(int(cx + 38), int(cy + 6), int(cx + 12), int(cy + 22))
        painter.setBrush(QBrush(QColor(15, 20, 28)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx + 8, cy + 19, 8, 8))

        # Big Joyful Anime Manga Eyes
        blink = (self.tick % 110) > 103 or self.state == MascotState.SUCCESS
        if blink:
            painter.setPen(QPen(QColor(30, 35, 45), 2.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(QRectF(cx - 20, cy - 8, 12, 8), 0, 180 * 16)
            painter.drawArc(QRectF(cx + 8, cy - 8, 12, 8), 0, 180 * 16)
        else:
            px = self.pupil_x * 0.7
            py = self.pupil_y * 0.7
            painter.setBrush(QBrush(QColor(25, 30, 42)))
            painter.drawEllipse(QRectF(cx - 22 + px, cy - 12 + py, 13, 18))
            painter.drawEllipse(QRectF(cx + 9 + px, cy - 12 + py, 13, 18))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(QPointF(cx - 18 + px, cy - 8 + py), 3.0, 3.0)
            painter.drawEllipse(QPointF(cx - 15 + px, cy - 4 + py), 1.5, 1.5)
            painter.drawEllipse(QPointF(cx + 13 + px, cy - 8 + py), 3.0, 3.0)
            painter.drawEllipse(QPointF(cx + 16 + px, cy - 4 + py), 1.5, 1.5)

        # Expressive Eyebrows
        self._draw_expressive_eyebrows(painter, cx, cy - 17, spacing=16, color=QColor(40, 45, 55))

        # Cheerful Mouth
        self._draw_interactive_mouth(painter, cx - 4, cy + 12, QColor(30, 35, 45))

    # =========================================================================
    # AVATAR 8: Quantum Diamond Prism (گوی کریستالی الماس چندوجهی Bing)
    # =========================================================================
    def _draw_crystal_prism(self, painter: QPainter, cx: float, cy: float, primary: QColor, secondary: QColor):
        # Multi-faceted Polyhedral Diamond / Crystal
        poly_path = QPainterPath()
        points = [
            (cx, cy - 38), (cx + 26, cy - 26), (cx + 38, cy),
            (cx + 28, cy + 28), (cx, cy + 38), (cx - 28, cy + 28),
            (cx - 38, cy), (cx - 26, cy - 26)
        ]
        poly_path.moveTo(points[0][0], points[0][1])
        for pt in points[1:]:
            poly_path.lineTo(pt[0], pt[1])
        poly_path.closeSubpath()

        # Inner Cosmic Nebula Gradient
        crystal_grad = QRadialGradient(cx, cy, 42)
        crystal_grad.setColorAt(0.0, QColor(220, 255, 255, 220))
        crystal_grad.setColorAt(0.4, QColor(0, 240, 255, 160))
        crystal_grad.setColorAt(0.8, QColor(10, 80, 160, 200))
        crystal_grad.setColorAt(1.0, QColor(4, 30, 70, 240))
        painter.setBrush(QBrush(crystal_grad))
        painter.setPen(QPen(QColor(180, 255, 255), 2))
        painter.drawPath(poly_path)

        # Facet Reflection Lines
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1.2))
        for pt in points:
            painter.drawLine(int(cx), int(cy), int(pt[0]), int(pt[1]))

        # Floating Cosmic Star Dust Particles inside
        for i in range(5):
            angle = (self.tick * 0.05 + i * 1.2)
            dist = 12 + math.sin(self.tick * 0.1 + i) * 8
            star_x = cx + math.cos(angle) * dist
            star_y = cy + math.sin(angle) * dist
            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(int(star_x), int(star_y)), 2, 2)

        # Radiant Emerald Crystal Eyes
        blink = (self.tick % 115) > 108 or self.state == MascotState.SUCCESS
        if blink:
            painter.setPen(QPen(QColor(0, 255, 180), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(QRectF(cx - 20, cy - 8, 12, 8), 0, 180 * 16)
            painter.drawArc(QRectF(cx + 8, cy - 8, 12, 8), 0, 180 * 16)
        else:
            px = self.pupil_x * 0.6
            py = self.pupil_y * 0.6
            painter.setBrush(QBrush(QColor(0, 255, 170)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - 18 + px, cy - 10 + py, 11, 14))
            painter.drawEllipse(QRectF(cx + 7 + px, cy - 10 + py, 11, 14))
            painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
            painter.drawEllipse(QPoint(int(cx - 14 + px), int(cy - 7 + py)), 2, 2)
            painter.drawEllipse(QPoint(int(cx + 11 + px), int(cy - 7 + py)), 2, 2)

        # Gentle Smiling Arc Mouth
        self._draw_interactive_mouth(painter, cx, cy + 12, QColor(0, 255, 180))

    # --- Expressive 3D Eyebrows Helper ---
    def _draw_expressive_eyebrows(self, painter: QPainter, cx: float, cy: float, spacing: float = 16, color: Optional[QColor] = None):
        """Draws living, emotional 3D eyebrows that express curiosity, speech cadence, and emotions."""
        col = color or self.custom_primary_color
        painter.setBrush(Qt.BrushStyle.NoBrush)

        left_y = cy
        right_y = cy
        left_tilt = 0.0
        right_tilt = 0.0

        if self.state == MascotState.SPEAKING:
            # Eyebrows animate and articulate smoothly with speech pitch
            bob = math.sin(self.tick * 0.35) * 2.5
            left_y += bob
            right_y += bob * 0.8
            left_tilt = 1.0
            right_tilt = -1.0
        elif self.state == MascotState.THINKING:
            # Inquisitive raised eyebrow
            left_y -= 4.0
            left_tilt = 2.0
            right_y += 1.5
            right_tilt = -1.0
        elif self.state == MascotState.WORKING:
            # Focused determined furrow
            left_y += 2.0
            right_y += 2.0
            left_tilt = -2.5
            right_tilt = 2.5
        elif self.state == MascotState.SUCCESS:
            # Happy raised arched brows
            left_y -= 3.5
            right_y -= 3.5
            left_tilt = 1.2
            right_tilt = -1.2
        elif self.state == MascotState.ERROR:
            # Concerned worried tilt
            left_y += 2.5
            right_y += 2.5
            left_tilt = -3.5
            right_tilt = 3.5

        painter.setPen(QPen(col, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        # Left eyebrow
        painter.drawLine(int(cx - spacing - 7), int(left_y + left_tilt), int(cx - spacing + 7), int(left_y - left_tilt))
        # Right eyebrow
        painter.drawLine(int(cx + spacing - 7), int(right_y - right_tilt), int(cx + spacing + 7), int(right_y + right_tilt))

    # --- Common Lip-Sync & Interactive Mouth Helper ---
    def _draw_interactive_mouth(self, painter: QPainter, mx: float, my: float, color: QColor):
        """Draws volumetric, living lip-sync mouth opening/closing with speech syllable cadence."""
        if self.state == MascotState.SPEAKING:
            # Multi-harmonic syllable pulse mimicking real speech phonemes (O, A, E, M)
            syllable_pulse = abs(math.sin(self.tick * 0.42) * 0.65 + math.sin(self.tick * 0.85 + 0.3) * 0.35)
            open_h = 3.5 + syllable_pulse * 11.0
            open_w = 9.0 + syllable_pulse * 5.5

            # 1. Dark oral cavity with gradient depth
            cavity_grad = QRadialGradient(mx, my, open_w / 2)
            cavity_grad.setColorAt(0.0, QColor(25, 12, 25))
            cavity_grad.setColorAt(1.0, QColor(8, 10, 16))
            painter.setBrush(QBrush(cavity_grad))
            painter.setPen(QPen(color, 1.4))
            painter.drawEllipse(QRectF(mx - open_w / 2, my - open_h / 2, open_w, open_h))

            # 2. Cute upper tooth edge when mouth is open
            if open_h > 7.0:
                painter.setBrush(QBrush(QColor(250, 250, 255, 230)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(mx - 3.5, my - open_h / 2 + 1, 7, 2.5), 1, 1)

            # 3. Cute tongue highlight at the bottom
            if open_h > 5.5:
                painter.setBrush(QBrush(QColor(255, 110, 150, 210)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(mx - 3.0, my + open_h / 2 - 4.0, 6, 3.5))

        elif self.state == MascotState.SUCCESS or self.wink_timer > 0:
            # Broad Happy Smile
            painter.setPen(QPen(color, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(mx - 9, my - 3, 18, 11), 180 * 16, 180 * 16)
        elif self.state == MascotState.ERROR:
            # Slight frowning/concerned mouth
            painter.setPen(QPen(color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(mx - 7, my + 1, 14, 9), 0, 180 * 16)
        else:
            # Soft relaxed friendly smile with subtle breathing curve
            breath = math.sin(self.tick * 0.08) * 0.8
            painter.setPen(QPen(color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(mx - 7, my - 2 + breath, 14, 8), 180 * 16, 180 * 16)

    # --- Common Visor Expressions Helper (for Cyber Bot & Astral Orb) ---
    def _draw_visor_expressions(self, painter: QPainter, cx: float, cy: float, primary: QColor):
        painter.setBrush(QBrush(primary))
        painter.setPen(Qt.PenStyle.NoPen)

        if self.state == MascotState.IDLE:
            blink = (self.tick % 110) > 102
            if blink:
                painter.setPen(QPen(primary, 2))
                painter.drawLine(int(cx - 18), int(cy), int(cx - 8), int(cy))
                painter.drawLine(int(cx + 8), int(cy), int(cx + 18), int(cy))
            else:
                px = self.pupil_x * 0.6
                py = self.pupil_y * 0.6
                eye_h = 7 + math.sin(self.tick * 0.1) * 1.5
                painter.drawRoundedRect(QRectF(cx - 18 + px, cy - 4 + py, 9, eye_h), 3, 3)
                painter.drawRoundedRect(QRectF(cx + 9 + px, cy - 4 + py, 9, eye_h), 3, 3)

        elif self.state == MascotState.THINKING:
            spin_start = (self.tick * 10) % 360
            painter.setPen(QPen(primary, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(cx - 12, cy - 10, 24, 20), spin_start * 16, 120 * 16)

        elif self.state == MascotState.WORKING:
            painter.setPen(QPen(primary, 2))
            for i in range(-2, 3):
                bar_x = cx + i * 8
                if cx - 22 < bar_x < cx + 22:
                    h = 6 + abs(math.sin((self.tick + i * 3) * 0.2)) * 12
                    painter.drawLine(int(bar_x), int(cy - h / 2), int(bar_x), int(cy + h / 2))

        elif self.state == MascotState.SPEAKING:
            # Expressive talking digital waveform that pulses with voice syllables
            voice_amp = 0.7 + abs(math.sin(self.tick * 0.42)) * 0.5
            for i, offset_x in enumerate([-16, -8, 0, 8, 16]):
                h = 4 + abs(math.sin(self.tick * 0.35 + i * 1.1)) * 14 * voice_amp
                painter.drawRoundedRect(QRectF(cx + offset_x - 2, cy - h / 2 - 2, 4, h), 2, 2)

            # Synchronized mouth at bottom of visor
            mouth_w = 10 + abs(math.sin(self.tick * 0.45)) * 6
            mouth_h = 3 + abs(math.sin(self.tick * 0.3)) * 4
            painter.drawRoundedRect(QRectF(cx - mouth_w / 2, cy + 8 - mouth_h / 2, mouth_w, mouth_h), 2, 2)

        elif self.state == MascotState.SUCCESS:
            painter.setPen(QPen(primary, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(cx - 19, cy - 7, 10, 8), 0, 180 * 16)
            painter.drawArc(QRectF(cx + 9, cy - 7, 10, 8), 0, 180 * 16)

        elif self.state == MascotState.ERROR:
            painter.setPen(QPen(primary, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(int(cx - 16), int(cy - 6), int(cx - 8), int(cy + 2))
            painter.drawLine(int(cx - 8), int(cy - 6), int(cx - 16), int(cy + 2))
            painter.drawLine(int(cx + 8), int(cy - 6), int(cx + 16), int(cy + 2))
            painter.drawLine(int(cx + 16), int(cy - 6), int(cx + 8), int(cy + 2))


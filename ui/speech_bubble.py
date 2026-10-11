import sys
from typing import Any
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

from ui.styles import SPEECH_BUBBLE_QSS


class SpeechBubble(QWidget):
    """
    Floating desktop speech bubble attached to the mascot.
    Shows thoughts, live activity, and assistant replies.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._setup_ui()
        self._setup_animation()

        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.fade_out)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.frame = QFrame(self)
        self.frame.setObjectName("BubbleFrame")
        self.frame.setStyleSheet(SPEECH_BUBBLE_QSS)

        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(12, 10, 12, 10)

        self.label = QLabel("سلام! من نووا هستم، چه کاری برات انجام بدم؟", self.frame)
        self.label.setObjectName("BubbleText")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setMaximumWidth(260)
        self.label.setMinimumWidth(140)

        frame_layout.addWidget(self.label)
        layout.addWidget(self.frame)

    def _setup_animation(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(250)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def show_message(self, text: str, mascot_pos: Any = None, mascot_size_wh: Any = (160, 160), duration_ms: int = 5000):
        if not text:
            return

        if not isinstance(mascot_pos, QPoint):
            if isinstance(mascot_pos, (tuple, list)) and len(mascot_pos) >= 2:
                mascot_pos = QPoint(int(mascot_pos[0]), int(mascot_pos[1]))
            elif isinstance(mascot_pos, (int, float)) and isinstance(mascot_size_wh, (int, float)):
                mascot_pos = QPoint(int(mascot_pos), int(mascot_size_wh))
                mascot_size_wh = (160, 160)
            else:
                mascot_pos = QPoint(100, 100)

        if not isinstance(mascot_size_wh, (tuple, list)) or len(mascot_size_wh) < 2:
            mascot_size_wh = (160, 160)

        self.label.setText(text)
        self.adjustSize()
        self._reposition(mascot_pos, mascot_size_wh)

        self.show()
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(self.opacity_effect.opacity())
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.start()

        self.hide_timer.stop()
        if duration_ms > 0:
            self.hide_timer.start(duration_ms)

    def _reposition(self, mascot_pos: QPoint, mascot_size_wh: tuple):
        mw, mh = mascot_size_wh
        bw = self.width()
        bh = self.height()

        # Position above or to the left of the mascot
        screen = self.screen() or self.parent().screen() if self.parent() else None
        screen_geo = screen.availableGeometry() if screen else None

        target_x = mascot_pos.x() + (mw - bw) // 2
        target_y = mascot_pos.y() - bh - 8

        if screen_geo:
            # If goes above screen top, place to the right/left
            if target_y < screen_geo.top():
                target_y = mascot_pos.y() + (mh - bh) // 2
                target_x = mascot_pos.x() + mw + 10
                if target_x + bw > screen_geo.right():
                    target_x = mascot_pos.x() - bw - 10
            
            # Clamp inside horizontal screen boundaries
            target_x = max(screen_geo.left() + 10, min(target_x, screen_geo.right() - bw - 10))

        self.move(target_x, target_y)

    def fade_out(self):
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(self.opacity_effect.opacity())
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.finished.connect(self._on_fade_out_finished)
        self.opacity_anim.start()

    def _on_fade_out_finished(self):
        try:
            self.opacity_anim.finished.disconnect(self._on_fade_out_finished)
        except Exception:
            pass
        self.hide()

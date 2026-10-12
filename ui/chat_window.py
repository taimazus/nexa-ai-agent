import os
import sys
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QScrollArea, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QTextCursor

from ui.styles import CHAT_WINDOW_QSS, PALETTE
from agent.engine import AgentEngine
from agent.tts import TTSEngine
from agent.audio_recorder import AudioRecorder
from agent.voice_detector import ContinuousVoiceListener

logger = logging.getLogger("NovaAgent.ChatWindow")


class AgentWorkerThread(QThread):
    """
    Background worker thread to run Gemini and Tools without freezing the GUI.
    """
    response_ready = pyqtSignal(str)
    state_changed = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    tool_executed = pyqtSignal(str, dict, dict)
    quota_warned = pyqtSignal(str, str)

    def __init__(
        self,
        engine: AgentEngine,
        message: str,
        image_path: Optional[str] = None,
        audio_path: Optional[str] = None
    ):
        super().__init__()
        self.engine = engine
        self.message = message
        self.image_path = image_path
        self.audio_path = audio_path

    def run(self):
        try:
            # Attach temporary callbacks for this run
            self.engine.on_state_change = lambda s: self.state_changed.emit(s)
            self.engine.on_status_update = lambda u: self.status_updated.emit(u)
            self.engine.on_tool_call = lambda t, a, r: self.tool_executed.emit(t, a, r)
            self.engine.on_quota_warning = lambda sev, msg: self.quota_warned.emit(sev, msg)

            reply = self.engine.process_user_message(self.message, self.image_path, self.audio_path)
            self.response_ready.emit(reply)
        except Exception as exc:
            logger.error(f"Unhandled exception in AgentWorkerThread: {exc}", exc_info=True)
            self.state_changed.emit("error")
            self.status_updated.emit("خطا در پردازش!")
            self.response_ready.emit(f"متاسفانه در پردازش درخواست خطای غیرمنتظره‌ای رخ داد: {str(exc)}")
        finally:
            # Clean up temporary utterance audio file if one was provided
            if self.audio_path and os.path.exists(self.audio_path):
                try:
                    import tempfile
                    from pathlib import Path
                    resolved = str(Path(self.audio_path).resolve())
                    if resolved.startswith(tempfile.gettempdir()):
                        os.remove(self.audio_path)
                        logger.debug(f"Cleaned up temporary audio utterance: {self.audio_path}")
                except Exception as clean_exc:
                    logger.warning(f"Could not remove temporary audio file {self.audio_path}: {clean_exc}")


class ChatWindow(QWidget):
    """
    Glassmorphic Chat & Command Window for Nova Desktop Agent.
    """
    message_sent = pyqtSignal(str)
    mascot_state_signal = pyqtSignal(str)
    mascot_speech_signal = pyqtSignal(str)
    settings_requested = pyqtSignal()
    quota_alert_signal = pyqtSignal(str, str)

    def __init__(self, engine: AgentEngine, tts: TTSEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.tts = tts
        self.worker: Optional[AgentWorkerThread] = None
        self.current_attached_image: Optional[str] = None
        self.current_attached_audio: Optional[str] = None
        self.audio_recorder = AudioRecorder(self)
        self.audio_recorder.recording_stopped.connect(self._on_audio_stopped)
        self.audio_recorder.recording_failed.connect(lambda err: self.add_agent_message(f"خطای میکروفون: {err}"))

        # Hands-Free Voice Conversation Listener (VAD)
        vad_cfg = getattr(self.engine, "services_config", None)
        silence_timeout = 0.9
        vad_sens = "medium"
        if vad_cfg:
            voice_opts = vad_cfg.get_voice_conversation_config()
            silence_timeout = voice_opts.get("silence_timeout_sec", 0.9)
            vad_sens = voice_opts.get("vad_sensitivity", "medium")

        self.voice_listener = ContinuousVoiceListener(
            self,
            silence_timeout_sec=silence_timeout,
            sensitivity=vad_sens
        )
        self.voice_listener.speech_started.connect(self._on_hands_free_speech_started)
        self.voice_listener.speech_completed.connect(self._on_hands_free_speech_completed)
        self.voice_listener.error_occurred.connect(lambda err: self.add_agent_message(f"خطای شنیدار صوتی: {err}"))

        self.drag_position = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(460, 620)
        self.setWindowTitle("نِکسا (NexA) | راهکار الکترونیک سهند (irres.ir)")

        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._setup_ui()
        self.update_family_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("CentralWidget")
        self.central_widget.setStyleSheet(CHAT_WINDOW_QSS)
        main_layout.addWidget(self.central_widget)

        content_layout = QVBoxLayout(self.central_widget)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(10)

        # 1. Header Bar (Draggable)
        self.header_bar = QWidget(self.central_widget)
        self.header_bar.setObjectName("HeaderBar")
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(12, 8, 12, 8)

        # Mascot Avatar Icon / Title
        self.title_label = QLabel("✨ نِکسا | NexA AI", self.header_bar)
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setToolTip("نِکسا (NexA) | طراحی و توسعه: شرکت راهکار الکترونیک سهند (https://irres.ir)")
        header_layout.addWidget(self.title_label)

        # Status badge
        self.status_badge = QLabel("● آماده", self.header_bar)
        self.status_badge.setObjectName("StatusBadge")
        header_layout.addWidget(self.status_badge)

        header_layout.addStretch()

        # Settings Button
        self.settings_btn = QPushButton("⚙️", self.header_bar)
        self.settings_btn.setObjectName("MinButton")
        self.settings_btn.setToolTip("تنظیمات کلیدهای API و حافظه")
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        header_layout.addWidget(self.settings_btn)

        # Minimize Button
        self.min_btn = QPushButton("—", self.header_bar)
        self.min_btn.setObjectName("MinButton")
        self.min_btn.setFixedSize(24, 24)
        self.min_btn.clicked.connect(self.hide)
        header_layout.addWidget(self.min_btn)

        # Close Button
        self.close_btn = QPushButton("✕", self.header_bar)
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.hide)
        header_layout.addWidget(self.close_btn)

        content_layout.addWidget(self.header_bar)

        # 1.5. NexA Family Members Quick Bar & Status
        self.family_bar = QFrame(self.central_widget)
        self.family_bar.setObjectName("FamilyBar")
        family_main_layout = QVBoxLayout(self.family_bar)
        family_main_layout.setContentsMargins(8, 6, 8, 6)
        family_main_layout.setSpacing(5)

        # Top row: Active Member info & level
        family_top_row = QHBoxLayout()
        family_top_row.setContentsMargins(2, 0, 2, 0)
        self.active_family_badge = QLabel("👥 هویت فعال: در حال بارگذاری...", self.family_bar)
        self.active_family_badge.setObjectName("ActiveFamilyBadge")
        family_top_row.addWidget(self.active_family_badge)

        family_top_row.addStretch()

        self.active_family_level = QLabel("سطح ۱ (۱۰۰ XP)", self.family_bar)
        self.active_family_level.setObjectName("ActiveFamilyLevel")
        family_top_row.addWidget(self.active_family_level)
        family_main_layout.addLayout(family_top_row)

        # Bottom row: Chips for all 6 members
        self.family_chips_layout = QHBoxLayout()
        self.family_chips_layout.setSpacing(4)
        self.family_chips_layout.setContentsMargins(0, 0, 0, 0)
        self.family_buttons = {}

        family_members_meta = [
            ("nexamehr", "🛡️ نِکسامِهر", "پدر خانواده | معمار ارشد سیستم، پاورشل، امنیت و سخت‌افزار"),
            ("nexanoo", "🌸 نِکسانو", "مادر خانواده | مدیر هماهنگی، هوش هیجانی و مراقبت سلامت"),
            ("samyar", "💻 سامیار", "پسر ارشد | مهندس نرم‌افزار، کدنویسی، پایتون و تست خودکار"),
            ("artin", "⚡ آرتین", "پسر دوم | خودکارسازی ویندوز، کلیدهای میانبر و کنترل نرم‌افزارها"),
            ("nila", "🔍 نیلا", "دختر سوم | جستجوگر وب، تحقیق عمیق، مقایسه قیمت‌ها و تحلیل داده"),
            ("tara", "🎨 تارا", "دختر چهارم | طراحی خلاق، سناریوهای بصری و تحلیل تصویر")
        ]

        for m_id, m_label, m_tip in family_members_meta:
            btn = QPushButton(m_label, self.family_bar)
            btn.setProperty("class", "family_chip")
            btn.setToolTip(m_tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, mid=m_id: self._on_family_chip_clicked(mid))
            self.family_chips_layout.addWidget(btn)
            self.family_buttons[m_id] = btn

        family_main_layout.addLayout(self.family_chips_layout)
        content_layout.addWidget(self.family_bar)

        # 2. Quick Action Chips
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(6)
        
        chips = [
            ("⚡ وضعیت سیستم", "وضعیت سخت‌افزار، حافظه و سیستم‌عامل سیستم را بررسی کن"),
            ("📷 دیدن از وب‌کم", "__WEBCAM__"),
            ("📸 تحلیل صفحه", "__SCREENSHOT__"),
            ("📁 پوشه پروژه", "لیست فایل‌های پوشه پروژه دسکتاپ فعلی را با ابزار نمایش بده")
        ]

        for chip_title, chip_prompt in chips:
            btn = QPushButton(chip_title)
            btn.setProperty("class", "chip_button")
            btn.clicked.connect(lambda checked, p=chip_prompt: self._on_chip_clicked(p))
            chips_layout.addWidget(btn)

        content_layout.addLayout(chips_layout)

        # 3. Chat Messages Scroll Area
        self.scroll_area = QScrollArea(self.central_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.messages_container = QWidget()
        self.messages_container.setObjectName("ScrollAreaWidgetContents")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(4, 4, 4, 4)
        self.messages_layout.setSpacing(10)
        self.messages_layout.addStretch()

        self.scroll_area.setWidget(self.messages_container)
        content_layout.addWidget(self.scroll_area, 1)

        # Attachment Preview Tag (if screenshot, webcam or audio attached)
        self.attachment_bar = QWidget(self.central_widget)
        self.attachment_layout = QHBoxLayout(self.attachment_bar)
        self.attachment_layout.setContentsMargins(4, 2, 4, 2)
        self.attachment_label = QLabel("📸 فایل چندرسانه‌ای ضمیمه شد", self.attachment_bar)
        self.attachment_label.setStyleSheet("color: #00f3ff; font-size: 11px;")
        self.clear_attach_btn = QPushButton("✕", self.attachment_bar)
        self.clear_attach_btn.setFixedSize(18, 18)
        self.clear_attach_btn.setStyleSheet("background: transparent; color: #ff4d6d; border: none; font-weight: bold;")
        self.clear_attach_btn.clicked.connect(self._clear_attachment)
        self.attachment_layout.addWidget(self.attachment_label)
        self.attachment_layout.addWidget(self.clear_attach_btn)
        self.attachment_layout.addStretch()
        self.attachment_bar.hide()
        content_layout.addWidget(self.attachment_bar)

        # 4. Input Controls
        input_container = QHBoxLayout()
        input_container.setSpacing(8)

        self.input_edit = QTextEdit(self.central_widget)
        self.input_edit.setObjectName("InputEdit")
        self.input_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.input_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.input_edit.setPlaceholderText("دستورت رو اینجا بنویس یا صوتی بگو... (میکروفون، وب‌کم، اسکرین‌شات، کدنویسی)")
        self.input_edit.setFixedHeight(62)
        self.input_edit.textChanged.connect(self._handle_input_text_changed)
        input_container.addWidget(self.input_edit, 1)

        # Action Buttons Column
        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)

        top_btns = QHBoxLayout()
        top_btns.setSpacing(4)

        # Screenshot Button
        self.screen_btn = QPushButton("📸")
        self.screen_btn.setProperty("class", "icon_button")
        self.screen_btn.setToolTip("گرفتن اسکرین‌شات از صفحه برای تحلیل")
        self.screen_btn.setFixedSize(28, 28)
        self.screen_btn.clicked.connect(self._capture_screen_to_input)
        top_btns.addWidget(self.screen_btn)

        # Webcam Button
        self.webcam_btn = QPushButton("📷")
        self.webcam_btn.setProperty("class", "icon_button")
        self.webcam_btn.setToolTip("دیدن و عکسبرداری از دوربین وب‌کم")
        self.webcam_btn.setFixedSize(28, 28)
        self.webcam_btn.clicked.connect(self._capture_webcam_to_input)
        top_btns.addWidget(self.webcam_btn)

        # TTS Toggle Button
        self.tts_btn = QPushButton("🔊")
        self.tts_btn.setCheckable(True)
        self.tts_btn.setChecked(self.tts.enabled)
        self.tts_btn.setProperty("class", "icon_button")
        self.tts_btn.setToolTip("پخش صوتی پاسخ‌ها از اسپیکر (Windows TTS)")
        self.tts_btn.setFixedSize(28, 28)
        self.tts_btn.clicked.connect(self._toggle_tts)
        top_btns.addWidget(self.tts_btn)
        btn_col.addLayout(top_btns)

        bottom_btns = QHBoxLayout()
        bottom_btns.setSpacing(4)

        # Microphone Button (Push-to-talk)
        self.mic_btn = QPushButton("🎙️")
        self.mic_btn.setProperty("class", "icon_button")
        self.mic_btn.setToolTip("ضبط دستی صدا از میکروفون")
        self.mic_btn.setFixedSize(30, 30)
        self.mic_btn.clicked.connect(self._toggle_recording)
        bottom_btns.addWidget(self.mic_btn)

        # Hands-Free Continuous Voice Conversation Button
        self.hands_free_btn = QPushButton("🗣️")
        self.hands_free_btn.setCheckable(True)
        self.hands_free_btn.setProperty("class", "icon_button")
        self.hands_free_btn.setToolTip("حالت مکالمه پیوسته (بدون نیاز به فشردن دکمه - تشخیص خودکار مکث)")
        self.hands_free_btn.setFixedSize(30, 30)
        self.hands_free_btn.clicked.connect(self._toggle_hands_free)
        bottom_btns.addWidget(self.hands_free_btn)

        # Send Button
        self.send_btn = QPushButton("ارسال", self.central_widget)
        self.send_btn.setObjectName("SendButton")
        self.send_btn.setFixedHeight(30)
        self.send_btn.clicked.connect(self._on_send_clicked)
        bottom_btns.addWidget(self.send_btn, 1)

        btn_col.addLayout(bottom_btns)

        input_container.addLayout(btn_col)
        content_layout.addLayout(input_container)

        # 5. Company Branding Attribution
        self.brand_bar = QLabel("طراحی و توسعه: شرکت <b>راهکار الکترونیک سهند</b> &nbsp;|&nbsp; <a href='https://irres.ir' style='color:#00f0ff; text-decoration:none;'>irres.ir</a>", self.central_widget)
        self.brand_bar.setOpenExternalLinks(True)
        self.brand_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brand_bar.setStyleSheet("font-size: 10px; color: #64748b; padding-top: 2px;")
        content_layout.addWidget(self.brand_bar)

        # Add initial welcome greeting
        self.add_agent_message("سلام دوست من! 🌟 من **نِکسا (NexA)** هستم؛ دستیار هوشمند، لوکس و همه‌کاره دسکتاپت از شرکت دانش‌بنیان **راهکار الکترونیک سهند** (https://irres.ir).\n\nمن می‌تونم از **میکروفون 🎙️** صدایت را بشنوم، از **اسپیکر 🔊** با صدایی دلنشین پاسخ دهم، با **وب‌کم 📷** چهره و اشیاء را ببینم و تمام کارهای سیستم را برایت انجام دهم!")

    def _handle_input_text_changed(self):
        text = self.input_edit.toPlainText()
        if text.endswith("\n") and not (QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier):
            cleaned = text.rstrip("\n")
            if cleaned:
                self.input_edit.setPlainText(cleaned)
                self._on_send_clicked()

    def _toggle_tts(self, checked: bool):
        self.tts.set_enabled(checked)
        self.tts_btn.setText("🔊" if checked else "🔇")

    def _capture_screen_to_input(self):
        res = self.engine.dispatch_tool("capture_screenshot", {})
        if res.get("success"):
            self.current_attached_image = res.get("path")
            self.attachment_label.setText("📸 تصویر صفحه ضمیمه شد")
            self.attachment_bar.show()
            self.mascot_speech_signal.emit("تصویر صفحه ثبت شد، حالا دستورت رو بگو!")
        else:
            self.add_agent_message(f"خطا در ثبت اسکرین‌شات: {res.get('error')}")

    def _capture_webcam_to_input(self):
        res = self.engine.dispatch_tool("capture_webcam", {})
        if res.get("success"):
            self.current_attached_image = res.get("path")
            self.attachment_label.setText("📷 تصویر وب‌کم ضمیمه شد")
            self.attachment_bar.show()
            self.mascot_speech_signal.emit("تصویر وب‌کم گرفته شد، دستورت رو بگو!")
        else:
            self.add_agent_message(f"خطا در دسترسی به دوربین وب‌کم: {res.get('error')}")

    def _toggle_hands_free(self):
        if self.hands_free_btn.isChecked():
            if self.audio_recorder.is_recording():
                self.audio_recorder.stop_recording()
                self.mic_btn.setText("🎙️")
                self.mic_btn.setStyleSheet("")

            started = self.voice_listener.start()
            if started:
                self.hands_free_btn.setStyleSheet("background-color: rgba(0, 240, 255, 0.3); border: 1.5px solid #00f0ff;")
                self.status_badge.setText("🟢 مکالمه پیوسته (صحبت کنید)")
                self.status_badge.setStyleSheet("color: #00f0ff; background-color: rgba(0, 240, 255, 0.15);")
                self.mascot_speech_signal.emit("حالت مکالمه پیوسته فعال شد. هر زمان صحبت کنید می‌شنوم!")
            else:
                self.hands_free_btn.setChecked(False)
        else:
            self.voice_listener.stop()
            self.hands_free_btn.setStyleSheet("")
            self.status_badge.setText("● آماده")
            self.status_badge.setStyleSheet("")
            self.mascot_speech_signal.emit("مکالمه پیوسته متوقف شد.")

    def enable_hands_free_by_default(self):
        """Activates continuous voice listening on startup so user can talk immediately."""
        self.hands_free_btn.setChecked(True)
        started = self.voice_listener.start()
        if started:
            self.hands_free_btn.setStyleSheet("background-color: rgba(0, 240, 255, 0.3); border: 1.5px solid #00f0ff;")
            self.status_badge.setText("🟢 مکالمه پیوسته (صحبت کنید)")
            self.status_badge.setStyleSheet("color: #00f0ff; background-color: rgba(0, 240, 255, 0.15);")
            logger.info("Continuous Voice Listener enabled by default on startup.")
        else:
            self.hands_free_btn.setChecked(False)
            logger.warning("Continuous Voice Listener could not be started on startup.")

    def _on_hands_free_speech_started(self):
        if not self.hands_free_btn.isChecked():
            return
        self.status_badge.setText("🎤 در حال شنیدن صحبت شما...")
        self.status_badge.setStyleSheet("color: #ff4d6d; background-color: rgba(255, 77, 109, 0.15);")
        self.mascot_state_signal.emit("thinking")

    def _on_hands_free_speech_completed(self, wav_path: str):
        if not self.hands_free_btn.isChecked():
            return
        if not wav_path or not os.path.exists(wav_path):
            return
        logger.info(f"Hands-free speech completed: {wav_path}")
        self.current_attached_audio = wav_path
        self.attachment_label.setText("🎙️ صحبت شما دریافت شد...")
        self.attachment_bar.show()
        # Pause listener while AI processes & speaks (Acoustic Interlock)
        self.voice_listener.pause_listening()
        self._on_send_clicked()

    def _toggle_recording(self):
        if self.audio_recorder.is_recording():
            saved_wav = self.audio_recorder.stop_recording()
            self.mic_btn.setText("🎙️")
            self.mic_btn.setStyleSheet("")
            self.status_badge.setText("● آماده")
            self.status_badge.setStyleSheet("")
            if saved_wav and os.path.exists(saved_wav) and os.path.getsize(saved_wav) > 1000:
                self.current_attached_audio = saved_wav
                self.attachment_label.setText("🎙️ در حال ارسال صدای شما...")
                self.attachment_bar.show()
                # Automatically send immediately without making the user click another button!
                self._on_send_clicked()
            else:
                self.mascot_speech_signal.emit("صدایی ضبط نشد؛ لطفاً دوباره صحبت کنید.")
        else:
            # Clear previous attachment before starting fresh recording
            self.current_attached_audio = None
            self.attachment_bar.hide()
            success = self.audio_recorder.start_recording()
            if success:
                self.mic_btn.setText("⏹️")
                self.mic_btn.setStyleSheet("background-color: rgba(255, 77, 109, 0.4); border: 1.5px solid #ff4d6d;")
                self.status_badge.setText("🎤 در حال گوش دادن به شما...")
                self.status_badge.setStyleSheet("color: #ff4d6d; background-color: rgba(255, 77, 109, 0.15);")
                self.mascot_state_signal.emit("thinking")
                import random
                listen_phrases = ["سراپا گوشم...", "می‌شنوم، بفرمایید...", "دارم با دقت گوش میدم...", "گوشم با شماست..."]
                self.mascot_speech_signal.emit(random.choice(listen_phrases))

    def _on_audio_stopped(self, audio_path: str):
        if audio_path and os.path.exists(audio_path) and not self.worker:
            self.current_attached_audio = audio_path
            self.attachment_label.setText("🎙️ پیام صوتی ضبط شد")
            self.attachment_bar.show()

    def _clear_attachment(self):
        if self.audio_recorder.is_recording():
            self.audio_recorder.stop_recording()
            self.mic_btn.setText("🎙️")
            self.mic_btn.setStyleSheet("")
            self.status_badge.setText("● آماده")
            self.status_badge.setStyleSheet("")
        self.current_attached_image = None
        self.current_attached_audio = None
        self.attachment_bar.hide()

    def update_family_ui(self, member=None):
        """Updates the Family Bar UI with the currently active member and XP."""
        fm = getattr(self.engine, "family_manager", None)
        if not fm:
            return
        active = member or fm.get_active_member()
        if not active:
            return

        if hasattr(self, "active_family_badge"):
            self.active_family_badge.setText(f"👥 {active.name} | {active.role_title}")
        if hasattr(self, "active_family_level"):
            self.active_family_level.setText(f"سطح {active.level} ({active.xp} XP)")

        for m_id, btn in getattr(self, "family_buttons", {}).items():
            if m_id == active.id:
                btn.setProperty("class", "family_chip_active")
            else:
                btn.setProperty("class", "family_chip")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_family_chip_clicked(self, member_id: str):
        """Switches the active persona to the selected family member."""
        fm = getattr(self.engine, "family_manager", None)
        if not fm:
            return
        member = fm.switch_member(member_id)
        if not member:
            return

        # Re-initialize engine prompt with new identity
        self.engine._init_client_and_chat()
        self.update_family_ui(member)
        self.title_label.setText(f"🤖 {member.name} ({member.role_title}) | نِکسا")

        # Notify engine listener if connected (e.g. Mascot updates avatar & colors)
        if getattr(self.engine, "on_family_member_changed", None):
            self.engine.on_family_member_changed(member)

        # Notify user in speech and mascot
        import random
        greetings = [
            f"سلام! من {member.name} هستم، {member.role_title}. در خدمت شما هستم!",
            f"هویت فعال شد: من {member.name} هستم ({member.role_title}). بفرمایید در چه کاری کمکتان کنم؟",
            f"سلام! {member.name} آنلاین شد. در خدمت شما هستم!"
        ]
        greet = random.choice(greetings)
        self.mascot_speech_signal.emit(greet)
        if self.tts.enabled:
            if member.gender:
                self.tts.gender = member.gender
            self.tts.speak(greet)

        self.add_agent_message(
            f"✨ هویت فعال تغییر یافت به **{member.name}** ({member.role_title} - سطح {member.level})\n"
            f"💡 تخصص‌ها: {', '.join(member.specialties[:3])}"
        )

    def _on_chip_clicked(self, prompt: str):
        if prompt == "__SCREENSHOT__":
            self._capture_screen_to_input()
            self.input_edit.setPlainText("صفحه فعلی دسکتاپ من را بررسی کن و بگو چه چیزی در حال نمایش است.")
            self._on_send_clicked()
        elif prompt == "__WEBCAM__":
            self._capture_webcam_to_input()
            self.input_edit.setPlainText("تصویر وب‌کم من را ببین و بگو چه چیزی در تصویر می‌بینی؟")
            self._on_send_clicked()
        else:
            self.input_edit.setPlainText(prompt)
            self._on_send_clicked()

    def _on_send_clicked(self):
        # If currently recording, stop it and capture the file
        if self.audio_recorder.is_recording():
            saved_wav = self.audio_recorder.stop_recording()
            self.mic_btn.setText("🎙️")
            self.mic_btn.setStyleSheet("")
            self.status_badge.setText("● آماده")
            self.status_badge.setStyleSheet("")
            if saved_wav and os.path.exists(saved_wav) and os.path.getsize(saved_wav) > 1000:
                self.current_attached_audio = saved_wav

        text = self.input_edit.toPlainText().strip()
        image_path = self.current_attached_image
        audio_path = self.current_attached_audio

        if not text and not image_path and not audio_path:
            return

        if not text:
            if audio_path:
                text = "به پیام صوتی من گوش بده و پاسخم رو بده یا دستوری که گفتم رو اجرا کن."
            elif image_path:
                text = "تصویر ضمیمه شده را تحلیل کن."

        self.input_edit.clear()
        self._clear_attachment()

        # Add user message card
        user_card_text = "🎙️ پیام صوتی کاربر" if audio_path else text
        self.add_user_message(user_card_text)

        # Disable send while working
        self.send_btn.setEnabled(False)
        self.status_badge.setText("● در حال پردازش...")
        self.status_badge.setStyleSheet("color: #ffb703; background-color: rgba(255,183,3,0.15);")

        # Launch background worker thread
        self.worker = AgentWorkerThread(self.engine, text, image_path, audio_path)
        self.worker.response_ready.connect(self._on_agent_response)
        self.worker.state_changed.connect(self.mascot_state_signal.emit)
        self.worker.status_updated.connect(self._on_agent_status)
        self.worker.tool_executed.connect(self._on_tool_executed)
        self.worker.quota_warned.connect(self._on_quota_warning)
        self.worker.start()

    def _on_quota_warning(self, severity: str, message: str):
        self.quota_alert_signal.emit(severity, message)
        self.add_alert_card(severity, message)
        self.mascot_state_signal.emit("error")
        self.mascot_speech_signal.emit(message)
        if self.tts.enabled:
            self.tts.speak("هشدار: اعتبار کلید به پایان رسید.")

    def add_alert_card(self, severity: str, message: str):
        card = QFrame()
        is_critical = (severity == "critical")
        border_color = PALETTE.get("neon_red", "#ef4444") if is_critical else PALETTE.get("neon_amber", "#f59e0b")
        bg_color = "rgba(255, 77, 109, 0.15)" if is_critical else "rgba(255, 183, 3, 0.15)"
        card.setStyleSheet(f"background-color: {bg_color}; border: 1.5px solid {border_color}; border-radius: 12px; padding: 10px;")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title = QLabel("🚨 هشدار اتمام اعتبار API" if is_critical else "⚠️ هشدار کاهش اعتبار کلید")
        title.setStyleSheet(f"color: {border_color}; font-weight: bold; font-size: 12px; font-family: 'Segoe UI', 'Vazirmatn';")
        layout.addWidget(title)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("color: #f1f5f9; font-size: 11px; font-family: 'Segoe UI', 'Vazirmatn';")
        layout.addWidget(msg_lbl)

        btn = QPushButton("⚙️ باز کردن تنظیمات کلیدها")
        btn.setProperty("class", "action_btn")
        btn.setFixedWidth(160)
        btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(btn)

        self._insert_card(card)

    def _on_agent_status(self, status: str):
        self.status_badge.setText(f"● {status[:20]}")
        self.mascot_speech_signal.emit(status)

    def _on_tool_executed(self, tool_name: str, args: dict, result: dict):
        self.add_tool_card(tool_name, args, result)

    def _on_agent_response(self, reply: str):
        self.send_btn.setEnabled(True)
        self.status_badge.setText("● آماده")
        self.status_badge.setStyleSheet("color: #00ffaa; background-color: rgba(0,255,170,0.12);")
        
        self.add_agent_message(reply)
        self.mascot_speech_signal.emit(reply[:120] + "..." if len(reply) > 120 else reply)
        
        # Audio speech output with synchronized mascot states and hands-free auto-resume
        self.tts.on_speech_started = lambda: self.mascot_state_signal.emit("speaking")
        def _speech_finished_handler():
            self.mascot_state_signal.emit("idle")
            if self.hands_free_btn.isChecked():
                self.voice_listener.resume_listening()
                self.status_badge.setText("🟢 مکالمه پیوسته (صحبت کنید)")
                self.status_badge.setStyleSheet("color: #00f0ff; background-color: rgba(0, 240, 255, 0.15);")

        self.tts.on_speech_finished = _speech_finished_handler
        self.tts.speak(reply)
        if not self.tts.enabled:
            _speech_finished_handler()

    # --- Message Card Creators ---
    def add_user_message(self, text: str):
        card = QFrame()
        card.setProperty("class", "user_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {PALETTE['text_main']}; font-size: 13px; font-family: 'Segoe UI', 'Vazirmatn';")
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(lbl)

        self._insert_card(card)

    def add_agent_message(self, text: str):
        card = QFrame()
        card.setProperty("class", "agent_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)

        # Convert simple markdown to rich text formatting
        rich_html = self._format_markdown_to_html(text)
        lbl = QLabel()
        lbl.setText(rich_html)
        lbl.setWordWrap(True)
        lbl.setOpenExternalLinks(True)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl.setStyleSheet(f"color: {PALETTE['text_main']}; font-size: 13px; font-family: 'Segoe UI', 'Vazirmatn';")
        layout.addWidget(lbl)

        self._insert_card(card)

    def add_tool_card(self, tool_name: str, args: dict, result: dict):
        card = QFrame()
        card.setProperty("class", "tool_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel(f"⚡ ابزار اجرا شد: <b>{tool_name}</b>")
        title.setStyleSheet(f"color: {PALETTE['neon_purple']}; font-size: 11px;")
        layout.addWidget(title)

        details = ""
        if "command" in args:
            details += f"<code>$ {args['command']}</code>\n"
        elif "code" in args:
            details += f"<code>{args['code'][:100]}...</code>\n"
        elif "path" in args:
            details += f"مسیر: {args['path']}\n"

        if result.get("stdout"):
            details += f"\nخروجی:\n{result['stdout'][:150]}"
        elif result.get("output"):
            details += f"\nخروجی:\n{result['output'][:150]}"
        elif result.get("error"):
            details += f"\nخطا: {result['error']}"

        detail_lbl = QLabel(details)
        detail_lbl.setWordWrap(True)
        detail_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; font-family: 'Consolas', monospace;")
        layout.addWidget(detail_lbl)

        self._insert_card(card)

    def _insert_card(self, card: QWidget):
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, card)
        # Auto scroll to bottom
        QTimer = self.scroll_area.verticalScrollBar()
        QTimer.setValue(QTimer.maximum())

    def _format_markdown_to_html(self, text: str) -> str:
        import html
        escaped = html.escape(text)
        # Bold **text**
        import re
        escaped = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escaped)
        # Inline code `code`
        escaped = re.sub(r"`(.*?)`", r"<code style='background:#111827;color:#00f3ff;padding:2px 4px;border-radius:4px;'>\1</code>", escaped)
        # Code blocks ``` ... ```
        escaped = re.sub(r"```([a-zA-Z]*)\n([\s\S]*?)```", r"<pre style='background:#070a10;color:#00ffaa;padding:8px;border-radius:6px;border:1px solid #1e293b;'>\2</pre>", escaped)
        # Linebreaks
        escaped = escaped.replace("\n", "<br>")
        return f"<div style='line-height:1.5;'>{escaped}</div>"

    # --- Dragging Window via Header ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

import os
import sys
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QScrollArea, QFrame, QComboBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QRadioButton, QButtonGroup, QCheckBox, QTextEdit
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon

from ui.styles import PALETTE
from agent.key_manager import KeyManager
from agent.memory import MemoryManager
from agent.persona import (
    PersonaManager, Gender, AvatarStyle,
    RelationshipTone, MascotScale, ThemePalette
)
from agent.learning import LearningEngine
from agent.tts import TTSEngine
from agent.multi_ai import MultiAiCollaborator, PeerProvider
from agent.family.manager import FamilyManager
from agent.family.member import FamilyMember
from agent.integrations.config_manager import ServicesConfigManager, PRESET_SERVERS
from agent.integrations.email_client import EmailService

logger = logging.getLogger("NovaAgent.SettingsWindow")

SETTINGS_QSS = f"""
QWidget#SettingsWidget {{
    background-color: {PALETTE['bg_glass']};
    border: 1.5px solid {PALETTE['neon_cyan']};
    border-radius: 16px;
}}

QTabWidget::pane {{
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: transparent;
    border-radius: 8px;
}}

QTabBar::tab {{
    background: rgba(255, 255, 255, 0.05);
    color: {PALETTE['text_muted']};
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-bottom: none;
    padding: 8px 14px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
    font-size: 11px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 3px;
}}

QTabBar::tab:selected {{
    background: rgba(0, 243, 255, 0.15);
    color: {PALETTE['neon_cyan']};
    border: 1px solid {PALETTE['neon_cyan']};
    border-bottom: none;
    font-weight: bold;
}}

QLineEdit, QComboBox {{
    background-color: rgba(10, 14, 23, 0.85);
    color: {PALETTE['text_main']};
    border: 1px solid rgba(0, 243, 255, 0.3);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
}}

QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {PALETTE['neon_cyan']};
}}

QRadioButton {{
    color: {PALETTE['text_main']};
    font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma';
    font-size: 12px;
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 1px solid {PALETTE['border_cyan']};
    background: rgba(10, 14, 23, 0.9);
}}

QRadioButton::indicator:checked {{
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
        fx:0.5, fy:0.5, stop:0 {PALETTE['neon_cyan']}, stop:0.6 {PALETTE['neon_cyan']}, stop:0.7 transparent);
    border: 1.5px solid {PALETTE['neon_cyan']};
}}

QPushButton.action_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {PALETTE['neon_cyan']}, stop:1 {PALETTE['neon_purple']});
    color: #ffffff;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 12px;
}}

QPushButton.action_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2bf5ff, stop:1 #c34dff);
}}

QPushButton.secondary_btn {{
    background-color: rgba(255, 255, 255, 0.08);
    color: {PALETTE['text_main']};
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 11px;
}}

QPushButton.secondary_btn:hover {{
    background-color: rgba(255, 255, 255, 0.15);
    border: 1px solid {PALETTE['neon_cyan']};
}}

QPushButton.danger_btn {{
    background-color: rgba(255, 77, 109, 0.15);
    color: {PALETTE['neon_red']};
    border: 1px solid rgba(255, 77, 109, 0.4);
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 11px;
}}

QPushButton.danger_btn:hover {{
    background-color: rgba(255, 77, 109, 0.3);
}}

QTableWidget {{
    background-color: rgba(10, 14, 23, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    gridline-color: rgba(255, 255, 255, 0.05);
    color: {PALETTE['text_main']};
    font-size: 11px;
}}

QHeaderView::section {{
    background-color: rgba(16, 23, 38, 0.9);
    color: {PALETTE['neon_cyan']};
    border: none;
    padding: 6px;
    font-weight: bold;
    font-size: 11px;
}}
"""


class SettingsWindow(QWidget):
    """
    Settings dialog for managing:
    1. API Keys Pool with Auto-Failover
    2. Persistent Long-Term Memory
    3. Configurable Gender & Voice Persona
    4. Continuous Self-Learning Engine
    """
    keys_changed = pyqtSignal()
    memory_changed = pyqtSignal()
    persona_changed = pyqtSignal(str)
    avatar_changed = pyqtSignal(str)
    companion_updated = pyqtSignal()
    learning_changed = pyqtSignal()
    family_member_updated = pyqtSignal(object)
    family_member_switched = pyqtSignal(object)

    def __init__(
        self,
        key_manager: KeyManager,
        memory_manager: MemoryManager,
        persona_manager: Optional[PersonaManager] = None,
        learning_engine: Optional[LearningEngine] = None,
        tts_engine: Optional[TTSEngine] = None,
        multi_ai: Optional[MultiAiCollaborator] = None,
        family_manager: Optional[FamilyManager] = None,
        services_config: Optional[ServicesConfigManager] = None,
        parent=None
    ):
        super().__init__(parent)
        self.key_manager = key_manager
        self.memory_manager = memory_manager
        self.persona_manager = persona_manager or PersonaManager()
        self.learning_engine = learning_engine or LearningEngine()
        self.tts_engine = tts_engine
        self.multi_ai = multi_ai or MultiAiCollaborator(learning_engine=self.learning_engine)
        self.family_manager = family_manager or FamilyManager()
        self.services_config = services_config or ServicesConfigManager()
        self.email_service = EmailService(config_manager=self.services_config)
        self.drag_position = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(600, 640)
        self.setWindowTitle("تنظیمات نِکسا | راهکار الکترونیک سهند (irres.ir)")

        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._setup_ui()
        self.refresh_keys_table()
        self.refresh_memories_list()
        self.refresh_learnings_table()
        self.refresh_family_tab()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.widget = QWidget(self)
        self.widget.setObjectName("SettingsWidget")
        self.widget.setStyleSheet(SETTINGS_QSS)
        main_layout.addWidget(self.widget)

        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel("⚙️ تنظیمات دستیار هوشمند نِکسا | NexA Settings", self.widget)
        title.setStyleSheet(f"color: {PALETTE['neon_cyan']}; font-weight: bold; font-size: 13px;")
        header.addWidget(title)
        header.addStretch()

        close_btn = QPushButton("✕", self.widget)
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("background: transparent; color: #94a3b8; border: none; font-size: 14px;")
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget(self.widget)

        # Tab 1: Persona & Gender
        self.tab_persona = QWidget()
        self._setup_persona_tab()
        self.tabs.addTab(self.tab_persona, "👤 شخصیت و صدا")

        # Tab 2: API Keys
        self.tab_keys = QWidget()
        self._setup_keys_tab()
        self.tabs.addTab(self.tab_keys, "🔑 کلیدها (API Pool)")

        # Tab 3: Memory
        self.tab_memory = QWidget()
        self._setup_memory_tab()
        self.tabs.addTab(self.tab_memory, "🧠 حافظه بلندمدت")

        # Tab 4: Self-Learning
        self.tab_learning = QWidget()
        self._setup_learning_tab()
        self.tabs.addTab(self.tab_learning, "📈 یادگیری از خطاها")

        # Tab 5: Companion & Life Personalization
        self.tab_companion = QWidget()
        self._setup_companion_tab()
        self.tabs.addTab(self.tab_companion, "❤️ همراهی و شخصی‌سازی")

        # Tab 6: Multi-AI Interaction & Peer Review
        self.tab_multi_ai = QWidget()
        self._setup_multi_ai_tab()
        self.tabs.addTab(self.tab_multi_ai, "🌐 هوش‌های مصنوعی همکار")

        layout.addWidget(self.tabs, 1)

        # Company Attribution Footer
        brand_card = QFrame(self.widget)
        brand_card.setStyleSheet("background: rgba(10, 15, 26, 0.65); border: 1px solid rgba(0, 243, 255, 0.2); border-radius: 8px;")
        b_layout = QHBoxLayout(brand_card)
        b_layout.setContentsMargins(8, 5, 8, 5)
        b_label = QLabel("💎 طراحی و توسعه توسط شرکت <b>راهکار الکترونیک سهند</b> &nbsp;|&nbsp; وب‌سایت رسمی: <a href='https://irres.ir' style='color:#00f0ff; text-decoration:none;'>https://irres.ir</a>", brand_card)
        b_label.setOpenExternalLinks(True)
        b_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        b_layout.addWidget(b_label, 1, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand_card)

    # --- TAB 1: Persona & Family ---
    def _setup_persona_tab(self):
        p_layout = QVBoxLayout(self.tab_persona)
        p_layout.setContentsMargins(4, 4, 4, 4)
        p_layout.setSpacing(4)

        self.persona_subtabs = QTabWidget(self.tab_persona)

        # Sub-tab 1: Base Mascot, Voice & Personality
        self.tab_persona_base = QWidget()
        b_layout = QVBoxLayout(self.tab_persona_base)
        b_layout.setContentsMargins(10, 10, 10, 10)
        b_layout.setSpacing(10)

        desc = QLabel("تنظیم جنسیت، نام، تن صدا و استایل ظاهری دستیار:")
        desc.setStyleSheet(f"color: {PALETTE['text_main']}; font-weight: bold; font-size: 12px;")
        b_layout.addWidget(desc)

        # Gender Selection Box
        gender_card = QFrame()
        gender_card.setStyleSheet("background: rgba(10, 15, 26, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px;")
        g_layout = QVBoxLayout(gender_card)

        self.gender_group = QButtonGroup(self)

        self.radio_male = QRadioButton("👨‍💼 دستیار مردانه: «آریا» (لحن فنی و مقتدر + صدای David + تم فیروزه‌ای نئون)")
        self.radio_female = QRadioButton("👩‍💼 دستیار زنانه: «آوا» (لحن دقیق و گرم + صدای Zira + تم شیک ماژنتا/رز)")

        self.gender_group.addButton(self.radio_male, 1)
        self.gender_group.addButton(self.radio_female, 2)

        if self.persona_manager.gender == Gender.FEMALE:
            self.radio_female.setChecked(True)
        else:
            self.radio_male.setChecked(True)

        self.radio_male.toggled.connect(self._on_gender_toggled)

        g_layout.addWidget(self.radio_male)
        g_layout.addWidget(self.radio_female)
        b_layout.addWidget(gender_card)

        # Status & preview card
        self.persona_info_lbl = QLabel()
        self.persona_info_lbl.setWordWrap(True)
        self.persona_info_lbl.setStyleSheet("color: #38bdf8; font-size: 11px; padding: 6px;")
        self._update_persona_info_label()
        b_layout.addWidget(self.persona_info_lbl)

        # Test Voice Button
        btn_box = QHBoxLayout()
        test_voice_btn = QPushButton("🔊 تست صدای گوینده")
        test_voice_btn.setProperty("class", "action_btn")
        test_voice_btn.clicked.connect(self._test_voice)
        btn_box.addWidget(test_voice_btn)
        btn_box.addStretch()
        b_layout.addLayout(btn_box)

        # 3D Lovable Avatar Selection Section
        avatar_desc = QLabel("🎨 انتخاب شکلک و کاراکتر سه‌بعدی دسکتاپ:")
        avatar_desc.setStyleSheet(f"color: {PALETTE['text_main']}; font-weight: bold; font-size: 12px; margin-top: 8px;")
        b_layout.addWidget(avatar_desc)

        avatar_card = QFrame()
        avatar_card.setStyleSheet("background: rgba(10, 15, 26, 0.7); border: 1px solid rgba(0, 243, 255, 0.25); border-radius: 10px; padding: 10px;")
        av_layout = QVBoxLayout(avatar_card)
        av_layout.setSpacing(8)

        self.avatar_group = QButtonGroup(self)
        self.radio_bot = QRadioButton("🤖 ربات نئونی هوشمند (Cyber Bot - رینگ‌های چرخشی هولوگرافیک)")
        self.radio_sphere = QRadioButton("🔵 گوی سایبرنتیک آبی (Azure Orb - چشمان دیجیتال و سنسورهای گوش)")
        self.radio_chrono = QRadioButton("⚙️ ربات لنز مکانیکی کربنی (Carbon Chrono - لنز برنجی متحرک)")
        self.radio_dj = QRadioButton("🎧 ربات هدست گیمینگ (Headset Pod - هدست و میکروفون با دهان خندان)")
        self.radio_prism = QRadioButton("💎 گوی کریستالی الماس (Quantum Prism - چندوجهی بازتابنده با ذرات کیهانی)")
        self.radio_cat = QRadioButton("🐱 گربه بامزه سایبری (Cyber Neko - سبک کاوایی/انیمه با گونه‌های سرخ)")
        self.radio_orb = QRadioButton("✨ گوی کوانتومی و بال‌های فرشته (Astral Orb - هسته کریستالی با بال‌های نورانی)")
        self.radio_panda = QRadioButton("🐼 پاندای فضانورد دوست‌داشتنی (Astro Panda - کلاه شیشه‌ای سه‌بعدی)")

        self.avatar_group.addButton(self.radio_bot, 1)
        self.avatar_group.addButton(self.radio_sphere, 2)
        self.avatar_group.addButton(self.radio_chrono, 3)
        self.avatar_group.addButton(self.radio_dj, 4)
        self.avatar_group.addButton(self.radio_prism, 5)
        self.avatar_group.addButton(self.radio_cat, 6)
        self.avatar_group.addButton(self.radio_orb, 7)
        self.avatar_group.addButton(self.radio_panda, 8)

        current_style = self.persona_manager.avatar_style
        if current_style == AvatarStyle.CYBER_CAT:
            self.radio_cat.setChecked(True)
        elif current_style == AvatarStyle.ASTRAL_ORB:
            self.radio_orb.setChecked(True)
        elif current_style == AvatarStyle.ASTRO_PANDA:
            self.radio_panda.setChecked(True)
        elif current_style == AvatarStyle.CYBER_SPHERE:
            self.radio_sphere.setChecked(True)
        elif current_style == AvatarStyle.CARBON_LENS:
            self.radio_chrono.setChecked(True)
        elif current_style == AvatarStyle.DJ_HEADSET:
            self.radio_dj.setChecked(True)
        elif current_style == AvatarStyle.CRYSTAL_PRISM:
            self.radio_prism.setChecked(True)
        else:
            self.radio_bot.setChecked(True)

        self.radio_bot.toggled.connect(self._on_avatar_toggled)
        self.radio_sphere.toggled.connect(self._on_avatar_toggled)
        self.radio_chrono.toggled.connect(self._on_avatar_toggled)
        self.radio_dj.toggled.connect(self._on_avatar_toggled)
        self.radio_prism.toggled.connect(self._on_avatar_toggled)
        self.radio_cat.toggled.connect(self._on_avatar_toggled)
        self.radio_orb.toggled.connect(self._on_avatar_toggled)
        self.radio_panda.toggled.connect(self._on_avatar_toggled)

        av_layout.addWidget(self.radio_bot)
        av_layout.addWidget(self.radio_sphere)
        av_layout.addWidget(self.radio_chrono)
        av_layout.addWidget(self.radio_dj)
        av_layout.addWidget(self.radio_prism)
        av_layout.addWidget(self.radio_cat)
        av_layout.addWidget(self.radio_orb)
        av_layout.addWidget(self.radio_panda)
        b_layout.addWidget(avatar_card)
        b_layout.addStretch()

        # Sub-tab 2: NexA Family Multi-Agent Roster & Personalization
        self.tab_family = QWidget()
        self._setup_family_tab()

        self.persona_subtabs.addTab(self.tab_persona_base, "👤 کاراکتر فعال و صدا")
        self.persona_subtabs.addTab(self.tab_family, "👨‍👩‍👧‍👦 اعضای خانواده نِکسا")

        p_layout.addWidget(self.persona_subtabs)

    def _on_gender_toggled(self):
        new_gender = Gender.MALE if self.radio_male.isChecked() else Gender.FEMALE
        self.persona_manager.set_gender(new_gender)
        if self.tts_engine:
            self.tts_engine.set_gender(new_gender.value)
        self._update_persona_info_label()
        self.persona_changed.emit(new_gender.value)

    def _on_avatar_toggled(self):
        if self.radio_cat.isChecked():
            style = AvatarStyle.CYBER_CAT
        elif self.radio_orb.isChecked():
            style = AvatarStyle.ASTRAL_ORB
        elif self.radio_panda.isChecked():
            style = AvatarStyle.ASTRO_PANDA
        elif self.radio_sphere.isChecked():
            style = AvatarStyle.CYBER_SPHERE
        elif self.radio_chrono.isChecked():
            style = AvatarStyle.CARBON_LENS
        elif self.radio_dj.isChecked():
            style = AvatarStyle.DJ_HEADSET
        elif self.radio_prism.isChecked():
            style = AvatarStyle.CRYSTAL_PRISM
        else:
            style = AvatarStyle.CYBER_BOT
        self.persona_manager.set_avatar_style(style)
        self.avatar_changed.emit(style.value)

    def _update_persona_info_label(self):
        is_female = (self.persona_manager.gender == Gender.FEMALE)
        name = "آوا (Ava)" if is_female else "آریا (Arya)"
        style = "زنانه، لحن دقیق و پرانرژی با تم نئونی ماژنتا" if is_female else "مردانه، لحن فنی و تحلیلی با تم نئونی فیروزه‌ای"
        self.persona_info_lbl.setText(f"🌟 نام فعال دستیار: <b>{name}</b><br>استایل: {style}")

    def _test_voice(self):
        if self.tts_engine:
            msg = "سلام! من آوا هستم، دستیار شخصی شما." if self.persona_manager.gender == Gender.FEMALE else "سلام! من آریا هستم، دستیار فنی شما."
            self.tts_engine.speak(msg)

    # --- TAB 2: API Keys ---
    def _setup_keys_tab(self):
        t_layout = QVBoxLayout(self.tab_keys)
        t_layout.setContentsMargins(10, 12, 10, 10)
        t_layout.setSpacing(8)

        notice = QLabel("💡 اگر سهمیه یک کلید تمام شود، دستیار بدون وقفه و با حفظ کل تاریخچه چت به کلید بعدی سوئیچ خواهد کرد.")
        notice.setWordWrap(True)
        notice.setStyleSheet(f"color: {PALETTE['neon_green']}; font-size: 11px;")
        t_layout.addWidget(notice)

        input_row = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Paste Gemini API Key (AIzaSy...)")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_row.addWidget(self.key_input, 2)

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("برچسب (مثلاً: کلید اصلی)")
        input_row.addWidget(self.label_input, 1)

        add_btn = QPushButton("+ افزودن")
        add_btn.setProperty("class", "action_btn")
        add_btn.clicked.connect(self._add_key)
        input_row.addWidget(add_btn)

        t_layout.addLayout(input_row)

        self.keys_table = QTableWidget()
        self.keys_table.setColumnCount(4)
        self.keys_table.setHorizontalHeaderLabels(["برچسب", "کلید", "وضعیت", "عملیات"])
        self.keys_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.keys_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.keys_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.keys_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        t_layout.addWidget(self.keys_table, 1)

        btn_row = QHBoxLayout()
        reset_btn = QPushButton("🔄 بازنشانی وضعیت همه کلیدها به فعال")
        reset_btn.setProperty("class", "secondary_btn")
        reset_btn.clicked.connect(self._reset_keys)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        t_layout.addLayout(btn_row)

    # --- TAB 3: Memory ---
    def _setup_memory_tab(self):
        m_layout = QVBoxLayout(self.tab_memory)
        m_layout.setContentsMargins(10, 12, 10, 10)
        m_layout.setSpacing(8)

        m_notice = QLabel("🧠 تمام فکت‌ها، نام‌ها و دستوراتی که اینجا ثبت شوند همیشه در ذهن دستیار باقی می‌مانند.")
        m_notice.setWordWrap(True)
        m_notice.setStyleSheet(f"color: {PALETTE['neon_purple']}; font-size: 11px;")
        m_layout.addWidget(m_notice)

        add_row = QHBoxLayout()
        self.mem_key_input = QLineEdit()
        self.mem_key_input.setPlaceholderText("موضوع / کلید (مثلاً: نام من، آدرس پروژه)")
        add_row.addWidget(self.mem_key_input, 1)

        self.mem_val_input = QLineEdit()
        self.mem_val_input.setPlaceholderText("مقدار یا توضیح فکت")
        add_row.addWidget(self.mem_val_input, 2)

        self.mem_cat_box = QComboBox()
        self.mem_cat_box.addItems(["عمومی", "پروژه", "علاقه‌مندی", "سیستم"])
        add_row.addWidget(self.mem_cat_box)

        mem_add_btn = QPushButton("+ ذخیره")
        mem_add_btn.setProperty("class", "action_btn")
        mem_add_btn.clicked.connect(self._add_memory)
        add_row.addWidget(mem_add_btn)
        m_layout.addLayout(add_row)

        self.mem_search = QLineEdit()
        self.mem_search.setPlaceholderText("🔍 جستجو در حافظه...")
        self.mem_search.textChanged.connect(self.refresh_memories_list)
        m_layout.addWidget(self.mem_search)

        self.mem_table = QTableWidget()
        self.mem_table.setColumnCount(4)
        self.mem_table.setHorizontalHeaderLabels(["موضوع", "دسته", "مقدار", "حذف"])
        self.mem_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.mem_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.mem_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.mem_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        m_layout.addWidget(self.mem_table, 1)

        clear_row = QHBoxLayout()
        clear_btn = QPushButton("🗑️ پاکسازی کامل حافظه")
        clear_btn.setProperty("class", "danger_btn")
        clear_btn.clicked.connect(self._clear_memories)
        clear_row.addWidget(clear_btn)
        clear_row.addStretch()
        m_layout.addLayout(clear_row)

    # --- TAB 4: Self-Learning ---
    def _setup_learning_tab(self):
        l_layout = QVBoxLayout(self.tab_learning)
        l_layout.setContentsMargins(10, 12, 10, 10)
        l_layout.setSpacing(8)

        l_notice = QLabel("📈 دستیار از هر خطا یا اصلاحیه شما خودبه‌خود درس می‌گیرد و آن را در قالب قانون اصلاحی ثبت می‌کند تا دیگر اشتباه نکند.")
        l_notice.setWordWrap(True)
        l_notice.setStyleSheet(f"color: {PALETTE['neon_cyan']}; font-size: 11px;")
        l_layout.addWidget(l_notice)

        # Add manual learned rule row
        lrn_row = QHBoxLayout()
        self.lrn_trig_input = QLineEdit()
        self.lrn_trig_input.setPlaceholderText("علت / اشتباه رخ‌داده")
        lrn_row.addWidget(self.lrn_trig_input, 1)

        self.lrn_rule_input = QLineEdit()
        self.lrn_rule_input.setPlaceholderText("قانون اصلاحی برای دفعات بعد")
        lrn_row.addWidget(self.lrn_rule_input, 2)

        lrn_add_btn = QPushButton("+ ثبت قانون")
        lrn_add_btn.setProperty("class", "action_btn")
        lrn_add_btn.clicked.connect(self._add_learning)
        lrn_row.addWidget(lrn_add_btn)
        l_layout.addLayout(lrn_row)

        self.lrn_table = QTableWidget()
        self.lrn_table.setColumnCount(4)
        self.lrn_table.setHorizontalHeaderLabels(["علت/خطا", "دستور اصلاحی (درس آموخته)", "دسته", "حذف"])
        self.lrn_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.lrn_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.lrn_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.lrn_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        l_layout.addWidget(self.lrn_table, 1)

        clear_lrn_row = QHBoxLayout()
        clear_lrn_btn = QPushButton("🗑️ پاکسازی تمام درس‌های آموخته")
        clear_lrn_btn.setProperty("class", "danger_btn")
        clear_lrn_btn.clicked.connect(self._clear_learnings)
        clear_lrn_row.addWidget(clear_lrn_btn)
        clear_lrn_row.addStretch()
        l_layout.addLayout(clear_lrn_row)

    # --- Actions: Keys ---
    def _add_key(self):
        key = self.key_input.text().strip()
        label = self.label_input.text().strip()
        if not key:
            return
        if self.key_manager.add_key(key, label):
            self.key_input.clear()
            self.label_input.clear()
            self.refresh_keys_table()
            self.keys_changed.emit()

    def _reset_keys(self):
        self.key_manager.reset_all_statuses()
        self.refresh_keys_table()
        self.keys_changed.emit()

    def refresh_keys_table(self):
        keys = self.key_manager.get_keys()
        active_key = self.key_manager.get_active_key()
        self.keys_table.setRowCount(len(keys))

        for row, item in enumerate(keys):
            k = item["key"]
            is_active = (k == active_key)
            masked = k[:6] + "..." + k[-4:] if len(k) > 10 else "***"

            self.keys_table.setItem(row, 0, QTableWidgetItem(item.get("label", "")))
            self.keys_table.setItem(row, 1, QTableWidgetItem(masked))

            status_text = "🟢 فعال" if is_active else ("🟠 سهمیه پر" if item.get("status") == "quota_exceeded" else "آماده")
            self.keys_table.setItem(row, 2, QTableWidgetItem(status_text))

            btn_box = QWidget()
            b_layout = QHBoxLayout(btn_box)
            b_layout.setContentsMargins(2, 2, 2, 2)
            b_layout.setSpacing(4)

            if not is_active:
                set_btn = QPushButton("انتخاب")
                set_btn.setProperty("class", "secondary_btn")
                set_btn.clicked.connect(lambda ch, key=k: self._set_active_key(key))
                b_layout.addWidget(set_btn)

            del_btn = QPushButton("✕")
            del_btn.setProperty("class", "danger_btn")
            del_btn.clicked.connect(lambda ch, key=k: self._delete_key(key))
            b_layout.addWidget(del_btn)

            self.keys_table.setCellWidget(row, 3, btn_box)

    def _set_active_key(self, key: str):
        self.key_manager.set_active_key(key)
        self.refresh_keys_table()
        self.keys_changed.emit()

    def _delete_key(self, key: str):
        self.key_manager.remove_key(key)
        self.refresh_keys_table()
        self.keys_changed.emit()

    # --- Actions: Memory ---
    def _add_memory(self):
        k = self.mem_key_input.text().strip()
        v = self.mem_val_input.text().strip()
        cat = self.mem_cat_box.currentText()
        if not k or not v:
            return
        self.memory_manager.remember_fact(k, v, category=cat)
        self.mem_key_input.clear()
        self.mem_val_input.clear()
        self.refresh_memories_list()
        self.memory_changed.emit()

    def refresh_memories_list(self):
        query = self.mem_search.text()
        facts = self.memory_manager.recall_facts(query)
        self.mem_table.setRowCount(len(facts))

        for row, item in enumerate(facts):
            k = item["key"]
            self.mem_table.setItem(row, 0, QTableWidgetItem(k))
            self.mem_table.setItem(row, 1, QTableWidgetItem(item.get("category", "عمومی")))
            self.mem_table.setItem(row, 2, QTableWidgetItem(item.get("value", "")))

            del_btn = QPushButton("✕")
            del_btn.setProperty("class", "danger_btn")
            del_btn.clicked.connect(lambda ch, key=k: self._delete_memory(key))
            self.mem_table.setCellWidget(row, 3, del_btn)

    def _delete_memory(self, key: str):
        self.memory_manager.forget_fact(key)
        self.refresh_memories_list()
        self.memory_changed.emit()

    def _clear_memories(self):
        self.memory_manager.clear_all_memories()
        self.refresh_memories_list()
        self.memory_changed.emit()

    # --- Actions: Learning ---
    def _add_learning(self):
        trig = self.lrn_trig_input.text().strip()
        rule = self.lrn_rule_input.text().strip()
        if not trig or not rule:
            return
        self.learning_engine.record_learning(trig, rule, category="دستی")
        self.lrn_trig_input.clear()
        self.lrn_rule_input.clear()
        self.refresh_learnings_table()
        self.learning_changed.emit()

    def refresh_learnings_table(self):
        rules = self.learning_engine.query_learnings()
        self.lrn_table.setRowCount(len(rules))

        for row, item in enumerate(rules):
            r_id = item.get("id", item.get("trigger"))
            self.lrn_table.setItem(row, 0, QTableWidgetItem(item.get("trigger", "")))
            self.lrn_table.setItem(row, 1, QTableWidgetItem(item.get("rule", "")))
            self.lrn_table.setItem(row, 2, QTableWidgetItem(item.get("category", "عمومی")))

            del_btn = QPushButton("✕")
            del_btn.setProperty("class", "danger_btn")
            del_btn.clicked.connect(lambda ch, rule_id=r_id: self._delete_learning(rule_id))
            self.lrn_table.setCellWidget(row, 3, del_btn)

    def _delete_learning(self, rule_id: str):
        self.learning_engine.delete_learning(rule_id)
        self.refresh_learnings_table()
        self.learning_changed.emit()

    def _clear_learnings(self):
        self.learning_engine.clear_learnings()
        self.refresh_learnings_table()
        self.learning_changed.emit()

    # --- TAB 5: Companion & Life Personalization ---
    def _setup_companion_tab(self):
        scroll = QScrollArea(self.tab_companion)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        desc = QLabel("تنظیمات عمیق شخصی‌سازی، هویت اختصاصی و سبک همراهی در زندگی روزمره:")
        desc.setStyleSheet(f"color: {PALETTE['text_main']}; font-weight: bold; font-size: 12px;")
        layout.addWidget(desc)

        # 1. User Profile Frame
        user_card = QFrame()
        user_card.setStyleSheet("background: rgba(10, 15, 26, 0.7); border: 1px solid rgba(0, 243, 255, 0.2); border-radius: 10px; padding: 10px;")
        u_layout = QVBoxLayout(user_card)
        u_layout.setSpacing(8)

        u_title = QLabel("👤 مشخصات شما (تا دستیار شما را با نام و احترام محبت‌آمیز صدا کند):")
        u_title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        u_layout.addWidget(u_title)

        row1 = QHBoxLayout()
        lbl1 = QLabel("نام شما:")
        lbl1.setFixedWidth(80)
        self.comp_user_name = QLineEdit()
        self.comp_user_name.setPlaceholderText("نام یا لقب شما (مثلاً: تایماز، آرش، سارا...)")
        self.comp_user_name.setText(self.persona_manager.user_name)
        row1.addWidget(lbl1)
        row1.addWidget(self.comp_user_name, 1)
        u_layout.addLayout(row1)

        row2 = QHBoxLayout()
        lbl2 = QLabel("حوزه کاری:")
        lbl2.setFixedWidth(80)
        self.comp_user_role = QLineEdit()
        self.comp_user_role.setPlaceholderText("شغل یا حوزه فعالیت (مثلاً: برنامه‌نویس، دانشجو، مدیر پروژه، طراح...)")
        self.comp_user_role.setText(self.persona_manager.user_role)
        row2.addWidget(lbl2)
        row2.addWidget(self.comp_user_role, 1)
        u_layout.addLayout(row2)

        layout.addWidget(user_card)

        # 2. Assistant Identity & Tone
        tone_card = QFrame()
        tone_card.setStyleSheet("background: rgba(10, 15, 26, 0.7); border: 1px solid rgba(176, 38, 255, 0.2); border-radius: 10px; padding: 10px;")
        t_layout = QVBoxLayout(tone_card)
        t_layout.setSpacing(8)

        t_title = QLabel("🤖 هویت و لحن ارتباطی دستیار:")
        t_title.setStyleSheet("color: #c084fc; font-weight: bold; font-size: 11px;")
        t_layout.addWidget(t_title)

        row3 = QHBoxLayout()
        lbl3 = QLabel("نام دستیار:")
        lbl3.setFixedWidth(80)
        self.comp_asst_name = QLineEdit()
        self.comp_asst_name.setPlaceholderText("نام دلخواه دستیار (پیش‌فرض: نوا / آریا / آوا)")
        self.comp_asst_name.setText(self.persona_manager.assistant_custom_name)
        row3.addWidget(lbl3)
        row3.addWidget(self.comp_asst_name, 1)
        t_layout.addLayout(row3)

        tone_lbl = QLabel("سبک رابطه و حس همراهی:")
        tone_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        t_layout.addWidget(tone_lbl)

        self.tone_group = QButtonGroup(self)
        self.radio_intimate = QRadioButton("❤️ صمیمی، دلسوز و رفیق شفیق (مثل صمیمی‌ترین دوست با محبت و همدلی عمیق)")
        self.radio_motivational = QRadioButton("🚀 مربی و مشوق رشد (انگیزه‌بخش، پرانرژی و متمرکز روی پیشرفت و اهداف شما)")
        self.radio_witty = QRadioButton("😄 شوخ‌طبع و سرزنده (شوخی‌های ظریف و به جا، پر از خنده، انرژی مثبت و نشاط)")
        self.radio_executive = QRadioButton("💼 حرفه‌ای و اجرایی (مشاور ارشد با ایجاز کلام، جدیت و بالاترین استانداردهای فنی)")

        self.tone_group.addButton(self.radio_intimate, 1)
        self.tone_group.addButton(self.radio_motivational, 2)
        self.tone_group.addButton(self.radio_witty, 3)
        self.tone_group.addButton(self.radio_executive, 4)

        current_tone = self.persona_manager.relationship_tone
        if current_tone == RelationshipTone.MOTIVATIONAL:
            self.radio_motivational.setChecked(True)
        elif current_tone == RelationshipTone.WITTY:
            self.radio_witty.setChecked(True)
        elif current_tone == RelationshipTone.EXECUTIVE:
            self.radio_executive.setChecked(True)
        else:
            self.radio_intimate.setChecked(True)

        t_layout.addWidget(self.radio_intimate)
        t_layout.addWidget(self.radio_motivational)
        t_layout.addWidget(self.radio_witty)
        t_layout.addWidget(self.radio_executive)

        layout.addWidget(tone_card)

        # 3. Aesthetics & Scale
        visual_card = QFrame()
        visual_card.setStyleSheet("background: rgba(10, 15, 26, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 10px;")
        v_layout = QVBoxLayout(visual_card)
        v_layout.setSpacing(8)

        v_title = QLabel("🎨 استایل ظاهری، ابعاد کاراکتر و تم رنگی:")
        v_title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        v_layout.addWidget(v_title)

        pal_row = QHBoxLayout()
        lbl4 = QLabel("تم رنگی نئون:")
        lbl4.setFixedWidth(80)
        self.palette_combo = QComboBox()
        self.palette_combo.addItem("🌌 فیروزه‌ای و بنفش سایبر (Cyber Cobalt)", ThemePalette.CYBER_CYAN.value)
        self.palette_combo.addItem("🌸 رز نئون و ماژنتا (Aurora Radiant)", ThemePalette.AURORA_ROSE.value)
        self.palette_combo.addItem("👑 طلایی کهربایی امپریال (Imperial Gold)", ThemePalette.IMPERIAL_GOLD.value)
        self.palette_combo.addItem("🌿 سبز زمردی نئون (Emerald Neon)", ThemePalette.EMERALD_NEON.value)
        self.palette_combo.addItem("🔮 بنفش کیهانی سحابی (Nebula Violet)", ThemePalette.NEBULA_PURPLE.value)

        for idx in range(self.palette_combo.count()):
            if self.palette_combo.itemData(idx) == self.persona_manager.theme_palette.value:
                self.palette_combo.setCurrentIndex(idx)
                break

        pal_row.addWidget(lbl4)
        pal_row.addWidget(self.palette_combo, 1)
        v_layout.addLayout(pal_row)

        scale_lbl = QLabel("اندازه شکلک روی دسکتاپ:")
        scale_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        v_layout.addWidget(scale_lbl)

        scale_row = QHBoxLayout()
        self.scale_group = QButtonGroup(self)
        self.radio_scale_s = QRadioButton("کوچک (120px)")
        self.radio_scale_m = QRadioButton("استاندارد (160px)")
        self.radio_scale_l = QRadioButton("بزرگ (200px)")
        self.scale_group.addButton(self.radio_scale_s, 1)
        self.scale_group.addButton(self.radio_scale_m, 2)
        self.scale_group.addButton(self.radio_scale_l, 3)

        current_scale = self.persona_manager.mascot_scale
        if current_scale == MascotScale.SMALL:
            self.radio_scale_s.setChecked(True)
        elif current_scale == MascotScale.LARGE:
            self.radio_scale_l.setChecked(True)
        else:
            self.radio_scale_m.setChecked(True)

        scale_row.addWidget(self.radio_scale_s)
        scale_row.addWidget(self.radio_scale_m)
        scale_row.addWidget(self.radio_scale_l)
        v_layout.addLayout(scale_row)

        layout.addWidget(visual_card)

        # 4. Daily Life & Wellness
        habits_card = QFrame()
        habits_card.setStyleSheet("background: rgba(10, 15, 26, 0.7); border: 1px solid rgba(0, 255, 136, 0.2); border-radius: 10px; padding: 10px;")
        h_layout = QVBoxLayout(habits_card)
        h_layout.setSpacing(6)

        h_title = QLabel("🌿 عادات همراهی در زندگی روزمره و سلامت:")
        h_title.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 11px;")
        h_layout.addWidget(h_title)

        self.chk_greeting = QCheckBox("☀️ احوالپرسی گرم و انرژی‌بخش روزانه متناسب با ساعت روز (صبح، ظهر، عصر، شب)")
        self.chk_greeting.setChecked(self.persona_manager.daily_greeting_enabled)
        h_layout.addWidget(self.chk_greeting)

        self.chk_health = QCheckBox("💧 یادآوری هوشمند سلامت، نوشیدن آب و استراحت چشم هنگام کار طولانی پشت سیستم")
        self.chk_health.setChecked(self.persona_manager.health_reminders_enabled)
        h_layout.addWidget(self.chk_health)

        self.chk_os_theme = QCheckBox("🖥️ همگام‌سازی خودکار با تم و رنگ ویندوز (Windows Dark/Light & Accent Sync)")
        self.chk_os_theme.setChecked(self.persona_manager.sync_with_os_theme)
        h_layout.addWidget(self.chk_os_theme)

        layout.addWidget(habits_card)

        # 5. Connected Services (Email & Instagram)
        services_card = QFrame()
        services_card.setStyleSheet("background: rgba(10, 15, 26, 0.7); border: 1px solid rgba(0, 243, 255, 0.25); border-radius: 10px; padding: 10px;")
        s_layout = QVBoxLayout(services_card)
        s_layout.setSpacing(8)

        s_title = QLabel("📬 اتصال و تنظیمات ایمیل و اینستاگرام (Email & Social Integration):")
        s_title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        s_layout.addWidget(s_title)

        s_desc = QLabel("این تنظیمات به صورت پیش‌فرض از سیستم خوانده شده است؛ هر تغییری دهید برای همیشه ذخیره و ملاک عمل خواهد بود.")
        s_desc.setStyleSheet("color: #94a3b8; font-size: 10px;")
        s_layout.addWidget(s_desc)

        email_cfg = self.services_config.get_email_config()
        insta_cfg = self.services_config.get_instagram_config()

        # Email Provider Row
        p_row = QHBoxLayout()
        p_lbl = QLabel("ارائه‌دهنده ایمیل:")
        p_lbl.setFixedWidth(100)
        p_row.addWidget(p_lbl)
        self.int_email_provider = QComboBox()
        self.int_email_provider.addItem("گوگل (Gmail)", "gmail")
        self.int_email_provider.addItem("مایکروسافت (Outlook / Hotmail)", "outlook")
        self.int_email_provider.addItem("یاهو (Yahoo Mail)", "yahoo")
        self.int_email_provider.addItem("سرور اختصاصی / شرکتی (Custom)", "custom")

        curr_prov = email_cfg.get("provider", "gmail")
        prov_idx = self.int_email_provider.findData(curr_prov)
        if prov_idx >= 0:
            self.int_email_provider.setCurrentIndex(prov_idx)
        self.int_email_provider.currentIndexChanged.connect(self._on_email_provider_changed)
        p_row.addWidget(self.int_email_provider, 1)
        s_layout.addLayout(p_row)

        # Email & App Password Row
        e_row = QHBoxLayout()
        e_lbl = QLabel("آدرس ایمیل:")
        e_lbl.setFixedWidth(100)
        e_row.addWidget(e_lbl)
        self.int_email_addr = QLineEdit()
        self.int_email_addr.setPlaceholderText("yourname@gmail.com")
        self.int_email_addr.setText(email_cfg.get("email_address", ""))
        e_row.addWidget(self.int_email_addr, 1)

        pwd_lbl = QLabel("کلمه عبور / App Password:")
        pwd_lbl.setFixedWidth(140)
        e_row.addWidget(pwd_lbl)
        self.int_email_pwd = QLineEdit()
        self.int_email_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.int_email_pwd.setPlaceholderText("کلمه عبور یا App Password")
        self.int_email_pwd.setText(email_cfg.get("app_password", ""))
        e_row.addWidget(self.int_email_pwd, 1)
        s_layout.addLayout(e_row)

        # IMAP Server & Port
        srv_row = QHBoxLayout()
        srv_lbl = QLabel("سرور IMAP:")
        srv_lbl.setFixedWidth(100)
        srv_row.addWidget(srv_lbl)
        self.int_imap_srv = QLineEdit()
        self.int_imap_srv.setText(email_cfg.get("imap_server", "imap.gmail.com"))
        srv_row.addWidget(self.int_imap_srv, 1)

        port_lbl = QLabel("پورت:")
        port_lbl.setFixedWidth(40)
        srv_row.addWidget(port_lbl)
        self.int_imap_port = QLineEdit()
        self.int_imap_port.setFixedWidth(60)
        self.int_imap_port.setText(str(email_cfg.get("imap_port", 993)))
        srv_row.addWidget(self.int_imap_port)
        s_layout.addLayout(srv_row)

        # Preferences & Instagram
        opt_row = QHBoxLayout()
        self.int_chk_important = QCheckBox("🔔 تشخیص و گزارش صوتی خودکار ایمیل‌های مهم")
        self.int_chk_important.setChecked(email_cfg.get("auto_summarize_important", True))
        opt_row.addWidget(self.int_chk_important, 1)

        ig_lbl = QLabel("نام کاربری اینستاگرام:")
        ig_lbl.setFixedWidth(120)
        opt_row.addWidget(ig_lbl)
        self.int_insta_user = QLineEdit()
        self.int_insta_user.setPlaceholderText("@username")
        self.int_insta_user.setText(insta_cfg.get("account_username", ""))
        opt_row.addWidget(self.int_insta_user, 1)
        s_layout.addLayout(opt_row)

        # Voice Conversation (VAD / Hands-free)
        voice_cfg = self.services_config.get_voice_conversation_config()
        vad_box = QHBoxLayout()
        self.int_chk_hands_free = QCheckBox("🗣️ مکالمه صوتی پیوسته (بدون نیاز به کلیک میکروفون)")
        self.int_chk_hands_free.setChecked(voice_cfg.get("hands_free_enabled", False))
        vad_box.addWidget(self.int_chk_hands_free, 1)

        sil_lbl = QLabel("تشخیص مکث (ثانیه):")
        sil_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        vad_box.addWidget(sil_lbl)
        self.int_silence_combo = QComboBox()
        self.int_silence_combo.addItem("۰.۶ ثانیه (خیلی سریع)", 0.6)
        self.int_silence_combo.addItem("۰.۸ ثانیه (سریع)", 0.8)
        self.int_silence_combo.addItem("۰.۹ ثانیه (متعادل)", 0.9)
        self.int_silence_combo.addItem("۱.۲ ثانیه (آرام)", 1.2)
        curr_sil = voice_cfg.get("silence_timeout_sec", 0.9)
        sil_idx = self.int_silence_combo.findData(curr_sil)
        if sil_idx != -1:
            self.int_silence_combo.setCurrentIndex(sil_idx)
        vad_box.addWidget(self.int_silence_combo)

        sens_lbl = QLabel("حساسیت:")
        sens_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        vad_box.addWidget(sens_lbl)
        self.int_vad_sens = QComboBox()
        self.int_vad_sens.addItem("زیاد (محیط ساکت)", "high")
        self.int_vad_sens.addItem("متوسط (پیش‌فرض)", "medium")
        self.int_vad_sens.addItem("کم (محیط شلوغ)", "low")
        curr_sens = voice_cfg.get("vad_sensitivity", "medium")
        sens_idx = self.int_vad_sens.findData(curr_sens)
        if sens_idx != -1:
            self.int_vad_sens.setCurrentIndex(sens_idx)
        vad_box.addWidget(self.int_vad_sens)

        s_layout.addLayout(vad_box)

        # Test button
        t_row = QHBoxLayout()
        self.int_test_btn = QPushButton("🔍 تست بررسی ایمیل‌های ورودی")
        self.int_test_btn.setProperty("class", "secondary_btn")
        self.int_test_btn.clicked.connect(self._test_email_check_ui)
        t_row.addWidget(self.int_test_btn)
        self.int_email_status = QLabel("")
        self.int_email_status.setStyleSheet("color: #38bdf8; font-size: 11px;")
        t_row.addWidget(self.int_email_status, 1)
        s_layout.addLayout(t_row)

        layout.addWidget(services_card)

        # 6. Save Button
        save_btn = QPushButton("💾 ذخیره تغییرات و اعمال آنی")
        save_btn.setProperty("class", "action_btn")
        save_btn.setFixedHeight(34)
        save_btn.clicked.connect(self._save_companion_profile)
        layout.addWidget(save_btn)

        self.comp_status_lbl = QLabel("")
        self.comp_status_lbl.setStyleSheet("color: #00ff88; font-weight: bold; font-size: 11px; padding: 4px;")
        layout.addWidget(self.comp_status_lbl)

        layout.addStretch()
        scroll.setWidget(container)

        tab_layout = QVBoxLayout(self.tab_companion)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    def _on_email_provider_changed(self):
        prov = self.int_email_provider.currentData()
        if prov in PRESET_SERVERS:
            preset = PRESET_SERVERS[prov]
            self.int_imap_srv.setText(preset["imap_server"])
            self.int_imap_port.setText(str(preset["imap_port"]))

    def _test_email_check_ui(self):
        self.int_email_status.setText("⏳ در حال اتصال به سرور ایمیل...")
        # Save temp fields into config
        self.services_config.update_email_config(
            provider=self.int_email_provider.currentData(),
            email_address=self.int_email_addr.text().strip(),
            app_password=self.int_email_pwd.text().strip(),
            imap_server=self.int_imap_srv.text().strip(),
            imap_port=int(self.int_imap_port.text().strip() or 993)
        )
        res = self.email_service.check_emails(unread_only=True, limit=5)
        if res.get("success"):
            total = res.get("total_found", 0)
            unr = res.get("unread_count", 0)
            imp = res.get("important_count", 0)
            self.int_email_status.setText(f"✅ اتصال برقرار شد! ({total} ایمیل، {unr} خوانده‌نشده، {imp} مهم)")
        else:
            err = res.get("error", "خطا")
            self.int_email_status.setText(f"❌ {err}")

    def _save_companion_profile(self):
        u_name = self.comp_user_name.text()
        u_role = self.comp_user_role.text()
        asst_name = self.comp_asst_name.text()

        # Tone
        if self.radio_motivational.isChecked():
            tone = RelationshipTone.MOTIVATIONAL
        elif self.radio_witty.isChecked():
            tone = RelationshipTone.WITTY
        elif self.radio_executive.isChecked():
            tone = RelationshipTone.EXECUTIVE
        else:
            tone = RelationshipTone.INTIMATE

        # Scale
        if self.radio_scale_s.isChecked():
            scale = MascotScale.SMALL
        elif self.radio_scale_l.isChecked():
            scale = MascotScale.LARGE
        else:
            scale = MascotScale.MEDIUM

        # Palette
        pal_val = self.palette_combo.currentData()
        palette = ThemePalette.from_string(pal_val)

        # Habits
        greeting = self.chk_greeting.isChecked()
        health = self.chk_health.isChecked()
        sync_os = self.chk_os_theme.isChecked()

        self.persona_manager.update_companion_profile(
            user_name=u_name,
            user_role=u_role,
            assistant_custom_name=asst_name,
            relationship_tone=tone,
            mascot_scale=scale,
            theme_palette=palette,
            health_reminders=health,
            daily_greeting=greeting,
            sync_with_os_theme=sync_os
        )

        # Persist Email & Instagram changes
        try:
            port_val = int(self.int_imap_port.text().strip() or 993)
        except Exception:
            port_val = 993

        self.services_config.update_email_config(
            provider=self.int_email_provider.currentData(),
            email_address=self.int_email_addr.text().strip(),
            app_password=self.int_email_pwd.text().strip(),
            imap_server=self.int_imap_srv.text().strip(),
            imap_port=port_val,
            auto_summarize_important=self.int_chk_important.isChecked()
        )
        self.services_config.update_instagram_config(
            account_username=self.int_insta_user.text().strip()
        )
        self.services_config.update_voice_conversation_config(
            hands_free_enabled=self.int_chk_hands_free.isChecked(),
            silence_timeout_sec=self.int_silence_combo.currentData(),
            vad_sensitivity=self.int_vad_sens.currentData()
        )

        self.comp_status_lbl.setText("✨ تنظیمات همراه و سرویس‌های متصل با موفقیت ذخیره و اعمال شد!")
        self._update_persona_info_label()
        self.companion_updated.emit()

    # --- TAB 6: Multi-AI Peer Collaboration & Self-Improvement ---
    def _setup_multi_ai_tab(self):
        scroll = QScrollArea(self.tab_multi_ai)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(12)

        desc = QLabel("تعامل با سایر هوش‌های مصنوعی (OpenAI, Claude, DeepSeek, Ollama)، باگ‌یابی کدها و خودبهبودبخشی دائمی:")
        desc.setStyleSheet(f"color: {PALETTE['text_main']}; font-weight: bold; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 1. Provider Configuration Card
        prov_card = QFrame()
        prov_card.setStyleSheet("background: rgba(10, 15, 26, 0.7); border: 1px solid rgba(0, 243, 255, 0.2); border-radius: 10px; padding: 10px;")
        p_layout = QVBoxLayout(prov_card)
        p_layout.setSpacing(8)

        p_title = QLabel("⚙️ پیکربندی هوش مصنوعی همکار (Peer Provider):")
        p_title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        p_layout.addWidget(p_title)

        # Provider Selector
        row_prov = QHBoxLayout()
        lbl_p = QLabel("سرویس‌دهنده:")
        lbl_p.setFixedWidth(85)
        self.peer_prov_combo = QComboBox()
        for p_key, p_val in self.multi_ai.providers.items():
            self.peer_prov_combo.addItem(p_val.get("name", p_key), p_key)
        
        # Set active provider index
        curr_act = self.multi_ai.active_provider
        idx = self.peer_prov_combo.findData(curr_act)
        if idx != -1:
            self.peer_prov_combo.setCurrentIndex(idx)
        self.peer_prov_combo.currentIndexChanged.connect(self._on_peer_provider_changed)
        row_prov.addWidget(lbl_p)
        row_prov.addWidget(self.peer_prov_combo, 1)
        p_layout.addLayout(row_prov)

        # API Key
        row_key = QHBoxLayout()
        lbl_k = QLabel("کلید API:")
        lbl_k.setFixedWidth(85)
        self.peer_api_key = QLineEdit()
        self.peer_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.peer_api_key.setPlaceholderText("API Key (برای Ollama نیاز به کلید نیست)")
        row_key.addWidget(lbl_k)
        row_key.addWidget(self.peer_api_key, 1)
        p_layout.addLayout(row_key)

        # Base URL
        row_url = QHBoxLayout()
        lbl_u = QLabel("آدرس Base URL:")
        lbl_u.setFixedWidth(85)
        self.peer_base_url = QLineEdit()
        self.peer_base_url.setPlaceholderText("مثلاً: http://localhost:11434 یا https://api.openai.com/v1")
        row_url.addWidget(lbl_u)
        row_url.addWidget(self.peer_base_url, 1)
        p_layout.addLayout(row_url)

        # Model Name
        row_mod = QHBoxLayout()
        lbl_m = QLabel("مدل هوش مصنوعی:")
        lbl_m.setFixedWidth(85)
        self.peer_model_name = QLineEdit()
        self.peer_model_name.setPlaceholderText("مثلاً: llama3, gpt-4o, claude-3-5-sonnet, deepseek-chat")
        row_mod.addWidget(lbl_m)
        row_mod.addWidget(self.peer_model_name, 1)
        p_layout.addLayout(row_mod)

        # Provider Action Buttons
        btn_box = QHBoxLayout()
        save_prov_btn = QPushButton("💾 ذخیره مشخصات این سرویس", self)
        save_prov_btn.setProperty("class", "secondary_btn")
        save_prov_btn.clicked.connect(self._save_peer_provider_config)

        set_active_btn = QPushButton("⚡ انتخاب به عنوان همکار فعال", self)
        set_active_btn.setProperty("class", "primary_btn")
        set_active_btn.clicked.connect(self._set_active_peer_provider)

        btn_box.addWidget(save_prov_btn)
        btn_box.addWidget(set_active_btn)
        p_layout.addLayout(btn_box)

        layout.addWidget(prov_card)

        # 2. Interactive Peer Actions Card
        act_card = QFrame()
        act_card.setStyleSheet("background: rgba(10, 15, 26, 0.7); border: 1px solid rgba(176, 38, 255, 0.2); border-radius: 10px; padding: 10px;")
        a_layout = QVBoxLayout(act_card)
        a_layout.setSpacing(8)

        a_title = QLabel("🚀 عملیات و تعامل زنده با هوش مصنوعی همکار:")
        a_title.setStyleSheet("color: #c084fc; font-weight: bold; font-size: 11px;")
        a_layout.addWidget(a_title)

        act_btns = QHBoxLayout()
        self.btn_peer_ping = QPushButton("🧪 تست اتصال (Ping)", self)
        self.btn_peer_ping.setProperty("class", "secondary_btn")
        self.btn_peer_ping.clicked.connect(self._on_click_peer_ping)

        self.btn_peer_review = QPushButton("🔍 باگ‌یابی و بازبینی کد", self)
        self.btn_peer_review.setProperty("class", "secondary_btn")
        self.btn_peer_review.clicked.connect(self._on_click_peer_code_review)

        self.btn_peer_improve = QPushButton("🧠 حلقه خودبهبودبخشی", self)
        self.btn_peer_improve.setProperty("class", "primary_btn")
        self.btn_peer_improve.clicked.connect(self._on_click_self_improvement)

        act_btns.addWidget(self.btn_peer_ping)
        act_btns.addWidget(self.btn_peer_review)
        act_btns.addWidget(self.btn_peer_improve)
        a_layout.addLayout(act_btns)

        # Live Results Text Display
        self.peer_result_display = QTextEdit()
        self.peer_result_display.setReadOnly(True)
        self.peer_result_display.setPlaceholderText("نتایج تحلیل، باگ‌های شناسایی‌شده یا پیشنهادات خودبهبودبخشی در این قسمت نمایش می‌یابد...")
        self.peer_result_display.setStyleSheet(
            "background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); "
            "color: #e2e8f0; font-size: 11px; border-radius: 8px; min-height: 120px;"
        )
        a_layout.addWidget(self.peer_result_display)

        # Distill button
        distill_box = QHBoxLayout()
        self.btn_distill_rule = QPushButton("💡 ثبت مستقیم این تحلیل به عنوان قانون یادگیری دائمی دستیار", self)
        self.btn_distill_rule.setProperty("class", "secondary_btn")
        self.btn_distill_rule.clicked.connect(self._distill_displayed_advice)
        distill_box.addWidget(self.btn_distill_rule)
        a_layout.addLayout(distill_box)

        layout.addWidget(act_card)

        # Status Label
        self.peer_status_lbl = QLabel("")
        self.peer_status_lbl.setStyleSheet("color: #38bdf8; font-size: 11px;")
        layout.addWidget(self.peer_status_lbl)

        layout.addStretch()
        scroll.setWidget(container)

        tab_layout = QVBoxLayout(self.tab_multi_ai)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

        # Load initial provider fields
        self._on_peer_provider_changed()

    def _on_peer_provider_changed(self):
        prov_key = self.peer_prov_combo.currentData()
        cfg = self.multi_ai.providers.get(prov_key, {})
        self.peer_api_key.setText(cfg.get("api_key", ""))
        self.peer_base_url.setText(cfg.get("base_url", ""))
        self.peer_model_name.setText(cfg.get("model", ""))

    def _save_peer_provider_config(self):
        prov_key = self.peer_prov_combo.currentData()
        k = self.peer_api_key.text()
        u = self.peer_base_url.text()
        m = self.peer_model_name.text()
        self.multi_ai.configure_provider(prov_key, api_key=k, base_url=u, model=m)
        self.peer_status_lbl.setText(f"✅ مشخصات سرویس‌دهنده '{prov_key}' ذخیره شد.")

    def _set_active_peer_provider(self):
        prov_key = self.peer_prov_combo.currentData()
        self._save_peer_provider_config()
        self.multi_ai.set_active_provider(prov_key)
        self.peer_status_lbl.setText(f"⚡ سرویس‌دهنده '{prov_key}' به عنوان همکار فعال تنظیم گردید.")

    def _on_click_peer_ping(self):
        self.peer_status_lbl.setText("⏳ در حال ارسال درخواست پینگ به هوش مصنوعی همکار...")
        prov_key = self.peer_prov_combo.currentData()
        res = self.multi_ai.consult_peer_ai(
            prompt="سلام! لطفاً خودت، نسخه مدل و قابلیت‌هایت را در ۲ خط معرفی کن.",
            provider=prov_key
        )
        if res.get("success"):
            reply = res.get("reply", "")
            self.peer_result_display.setText(f"🟢 پاسخ دریافت شد از [{res.get('provider')} / {res.get('model')}]:\n\n{reply}")
            self.peer_status_lbl.setText("✅ ارتباط با هوش مصنوعی همکار با موفقیت برقرار شد!")
        else:
            err = res.get("error", "خطای نامشخص")
            self.peer_result_display.setText(f"🔴 خطا در برقراری ارتباط:\n{err}")
            self.peer_status_lbl.setText("❌ خطا در اتصال به هوش مصنوعی همکار.")

    def _on_click_peer_code_review(self):
        sample_code = (
            "import os\n"
            "def save_data(data, filepath):\n"
            "    with open(filepath, 'w') as f:\n"
            "        f.write(data)\n"
        )
        self.peer_status_lbl.setText("⏳ در حال ارسال نمونه کد برای باگ‌یابی به هوش مصنوعی همکار...")
        res = self.multi_ai.peer_code_review(
            code=sample_code,
            language="python",
            context="ذخیره متن‌های فارسی در فایل سیستم ویندوز"
        )
        if res.get("success"):
            rev = res.get("review", "")
            self.peer_result_display.setText(f"🔍 گزارش بازبینی و ایرادات کشف‌شده:\n\n{rev}")
            self.peer_status_lbl.setText("✅ بازبینی کد تکمیل شد.")
        else:
            err = res.get("error", "خطای نامشخص")
            self.peer_result_display.setText(f"🔴 خطا در بازبینی کد:\n{err}")
            self.peer_status_lbl.setText("❌ خطا در اجرای بازبینی.")

    def _on_click_self_improvement(self):
        self.peer_status_lbl.setText("⏳ در حال اجرای چرخه خودبهبودبخشی با هوش مصنوعی همکار...")
        res = self.multi_ai.run_self_improvement(focus_area="امنیت اجرای دستورات سیستم‌عامل و انعطاف‌پذیری کدها")
        if res.get("success"):
            plan = res.get("improvement_plan", "")
            self.peer_result_display.setText(f"🧠 برنامه خودبهبودبخشی و ارتقای عملکرد:\n\n{plan}")
            self.peer_status_lbl.setText("✨ تحلیل خودبهبودبخشی با موفقیت در تاریخچه ثبت شد.")
        else:
            err = res.get("error", "خطای نامشخص")
            self.peer_result_display.setText(f"🔴 خطا در خودبهبودبخشی:\n{err}")
            self.peer_status_lbl.setText("❌ خطا در فرآیند خودبهبودبخشی.")

    def _distill_displayed_advice(self):
        text = self.peer_result_display.toPlainText().strip()
        if not text:
            self.peer_status_lbl.setText("⚠️ ابتدا یک تحلیل یا بازبینی دریافت کنید.")
            return

        topic = "رهنمود هوش مصنوعی همکار"
        first_line = text.split("\n")[0][:60]
        rec = self.multi_ai.learn_from_peer_ai(
            topic=f"بهبود از همکار: {first_line}",
            peer_advice=text[:250],
            category="peer_ai"
        )
        if rec.get("success"):
            self.refresh_learnings_table()
            self.learning_changed.emit()
            self.peer_status_lbl.setText("💡 این رهنمود با موفقیت به بانک قوانین یادگیری دستیار اضافه شد!")
        else:
            self.peer_status_lbl.setText("❌ خطا در ثبت رهنمود.")

    # --- TAB 7: NexA Family Multi-Agent Roster & Personalization ---
    def _setup_family_tab(self):
        f_layout = QVBoxLayout(self.tab_family)
        f_layout.setContentsMargins(6, 8, 6, 8)
        f_layout.setSpacing(6)

        # Scroll Area for comfortable viewing on any resolution
        scroll = QScrollArea(self.tab_family)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        f_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)

        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(8, 8, 8, 8)
        c_layout.setSpacing(10)

        # Guide banner
        intro_lbl = QLabel(
            "👨‍👩‍👧‍👦 <b>زیست‌بوم خانواده هوشمند چندعاملی نِکسا (NexA Family)</b><br>"
            "در این بخش می‌توانید نام دلخواه، جنسیت، حس و حال و روحیات رفتاری (Mood)، عنوان تخصص، آواتار ۳ بعدی و بیوگرافی هر عضو خانواده را تعیین کرده یا عضو جدیدی اضافه فرمایید."
        )
        intro_lbl.setWordWrap(True)
        intro_lbl.setStyleSheet(f"color: {PALETTE['neon_cyan']}; font-size: 11px; background: rgba(0, 243, 255, 0.08); padding: 8px; border-radius: 8px; border: 1px solid rgba(0, 243, 255, 0.2);")
        c_layout.addWidget(intro_lbl)

        # Selector Card
        sel_card = QFrame()
        sel_card.setStyleSheet("background: rgba(16, 23, 38, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 6px;")
        sel_layout = QVBoxLayout(sel_card)
        sel_layout.setSpacing(6)

        sel_top = QHBoxLayout()
        sel_lbl = QLabel("عضو خانواده:")
        sel_lbl.setStyleSheet(f"color: {PALETTE['neon_cyan']}; font-weight: bold; font-size: 11px;")
        sel_top.addWidget(sel_lbl)

        self.fam_member_combo = QComboBox()
        self.fam_member_combo.currentIndexChanged.connect(self._on_family_member_selected_index)
        sel_top.addWidget(self.fam_member_combo, 1)

        self.fam_new_member_btn = QPushButton("➕ عضو جدید")
        self.fam_new_member_btn.setProperty("class", "secondary_btn")
        self.fam_new_member_btn.clicked.connect(self._prompt_add_new_family_member)
        sel_top.addWidget(self.fam_new_member_btn)
        sel_layout.addLayout(sel_top)

        self.fam_info_badge = QLabel("در حال بارگذاری...")
        self.fam_info_badge.setStyleSheet("color: #a78bfa; font-size: 11px;")
        sel_layout.addWidget(self.fam_info_badge)
        c_layout.addWidget(sel_card)

        # Personalization Form
        form_frame = QFrame()
        form_frame.setStyleSheet("background: rgba(10, 14, 23, 0.85); border: 1px solid rgba(0, 243, 255, 0.2); border-radius: 8px; padding: 8px;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(8)

        # Row 1: Name and English Name
        r1 = QHBoxLayout()
        r1_n_lbl = QLabel("نام فارسی:")
        r1_n_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        r1.addWidget(r1_n_lbl)
        self.fam_name_edit = QLineEdit()
        self.fam_name_edit.setPlaceholderText("مثلاً: سامیار، کوروش، نیلا")
        r1.addWidget(self.fam_name_edit, 1)

        r1_en_lbl = QLabel("نام انگلیسی:")
        r1_en_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        r1.addWidget(r1_en_lbl)
        self.fam_eng_name_edit = QLineEdit()
        self.fam_eng_name_edit.setPlaceholderText("مثلاً: SamYar, Nila")
        r1.addWidget(self.fam_eng_name_edit, 1)
        form_layout.addLayout(r1)

        # Row 2: Gender and Mood
        r2 = QHBoxLayout()
        r2_g_lbl = QLabel("جنسیت:")
        r2_g_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        r2.addWidget(r2_g_lbl)

        self.fam_gender_group = QButtonGroup(self)
        self.fam_radio_male = QRadioButton("👨 آقا (مرد)")
        self.fam_radio_female = QRadioButton("👩 خانم (زن)")
        self.fam_gender_group.addButton(self.fam_radio_female)
        self.fam_gender_group.addButton(self.fam_radio_male)
        r2.addWidget(self.fam_radio_female)
        r2.addWidget(self.fam_radio_male)

        r2_m_lbl = QLabel("حس و حال (Mood):")
        r2_m_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        r2.addWidget(r2_m_lbl)

        self.fam_mood_combo = QComboBox()
        mood_items = [
            ("intimate", "🥰 صمیمی، دلسوز و همدم (Intimate)"),
            ("energetic", "⚡ پرانرژی، سریع و شاداب (Energetic)"),
            ("serious", "👔 مقتدر، جدی و منطقی (Serious)"),
            ("witty", "😄 شوخ‌طبع، طناز و خنده‌رو (Witty)"),
            ("caring", "🌸 آرامش‌بخش، مهربان و مراقب (Caring)"),
            ("technical", "💻 مهندسی، تحلیلی و کدمحور (Technical)"),
            ("creative", "🎨 خلاق، هنرمند و نوآور (Creative)"),
            ("calm", "🧘 متین، صبور و آرام (Calm)"),
            ("adventurous", "🚀 ماجراجو و کنجکاو (Adventurous)"),
            ("friendly", "🤝 دوستانه و خوش‌برخورد (Friendly)")
        ]
        for key, text in mood_items:
            self.fam_mood_combo.addItem(text, key)
        r2.addWidget(self.fam_mood_combo, 1)
        form_layout.addLayout(r2)

        # Row 3: Role Title and Avatar Style
        r3 = QHBoxLayout()
        r3_r_lbl = QLabel("عنوان نقش و تخصص:")
        r3_r_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        r3.addWidget(r3_r_lbl)
        self.fam_role_title_edit = QLineEdit()
        self.fam_role_title_edit.setPlaceholderText("مثلاً: مهندس ارشد نرم‌افزار، دستیار اتوماسیون")
        r3.addWidget(self.fam_role_title_edit, 1)

        r3_a_lbl = QLabel("آواتار ۳ بعدی:")
        r3_a_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        r3.addWidget(r3_a_lbl)
        self.fam_avatar_combo = QComboBox()
        avatar_items = [
            ("astral_orb", "گوی نورانی کیهانی (Astral Orb)"),
            ("cyber_bot", "ربات سایبری ۳بعدی (Cyber Bot)"),
            ("neon_cat", "گربه نئونی بازیگوش (Neon Cat)"),
            ("matrix_cube", "مکعب ماتریس هولوگرام (Matrix Cube)"),
            ("zen_lotus", "گل نیلوفر ذن درخشان (Zen Lotus)"),
            ("hologram_core", "هسته هولوگرافیک هوش (Hologram Core)")
        ]
        for key, text in avatar_items:
            self.fam_avatar_combo.addItem(text, key)
        r3.addWidget(self.fam_avatar_combo, 1)
        form_layout.addLayout(r3)

        # Row 4: Colors
        r4 = QHBoxLayout()
        r4_p_lbl = QLabel("رنگ نئونی اصلی:")
        r4_p_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        r4.addWidget(r4_p_lbl)
        self.fam_color_p_edit = QLineEdit()
        self.fam_color_p_edit.setPlaceholderText("#00f3ff")
        r4.addWidget(self.fam_color_p_edit, 1)

        r4_s_lbl = QLabel("رنگ ثانویه:")
        r4_s_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        r4.addWidget(r4_s_lbl)
        self.fam_color_s_edit = QLineEdit()
        self.fam_color_s_edit.setPlaceholderText("#b026ff")
        r4.addWidget(self.fam_color_s_edit, 1)
        form_layout.addLayout(r4)

        # Row 5: Specialties
        r5 = QHBoxLayout()
        r5_s_lbl = QLabel("تخصص‌های ویژه (با کاما جدا کنید):")
        r5_s_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        r5.addWidget(r5_s_lbl)
        self.fam_specialties_edit = QLineEdit()
        self.fam_specialties_edit.setPlaceholderText("پایتون، باگ‌یابی، تست‌نویسی، اتوماسیون")
        r5.addWidget(self.fam_specialties_edit, 1)
        form_layout.addLayout(r5)

        # Row 6: Bio & Story
        r6_b_lbl = QLabel("بیوگرافی و شرح شخصیت:")
        r6_b_lbl.setStyleSheet("color: #e2e8f0; font-size: 11px;")
        form_layout.addWidget(r6_b_lbl)
        self.fam_bio_edit = QTextEdit()
        self.fam_bio_edit.setFixedHeight(70)
        self.fam_bio_edit.setPlaceholderText("شخصیت، لحن صحبت و داستان پس‌زمینه این عضو خانواده...")
        form_layout.addWidget(self.fam_bio_edit)

        c_layout.addWidget(form_frame)

        # Action Buttons
        btn_row = QHBoxLayout()
        self.fam_save_btn = QPushButton("💾 ذخیره تغییرات و شخصی‌سازی")
        self.fam_save_btn.setProperty("class", "action_btn")
        self.fam_save_btn.clicked.connect(self._save_current_family_member)
        btn_row.addWidget(self.fam_save_btn, 1)

        self.fam_switch_btn = QPushButton("🌟 سوئیچ و فعال‌سازی این عضو")
        self.fam_switch_btn.setProperty("class", "secondary_btn")
        self.fam_switch_btn.clicked.connect(self._switch_to_selected_family_member)
        btn_row.addWidget(self.fam_switch_btn, 1)
        c_layout.addLayout(btn_row)

        self.fam_status_lbl = QLabel("")
        self.fam_status_lbl.setStyleSheet(f"color: {PALETTE['neon_green']}; font-size: 11px; font-weight: bold;")
        c_layout.addWidget(self.fam_status_lbl)

    def refresh_family_tab(self):
        """Refreshes the family member dropdown list from the manager."""
        if not hasattr(self, "fam_member_combo"):
            return

        current_selected_id = self.fam_member_combo.currentData()
        self.fam_member_combo.blockSignals(True)
        self.fam_member_combo.clear()

        members = self.family_manager.list_family_members()
        active_id = self.family_manager.active_member_id

        target_idx = 0
        for idx, m in enumerate(members):
            prefix = "🌟 " if m["id"] == active_id else ""
            gender_icon = "👨" if m["gender"] == "male" else "👩"
            display_text = f"{prefix}{gender_icon} {m['name']} ({m['role_title']})"
            self.fam_member_combo.addItem(display_text, m["id"])

            if current_selected_id and m["id"] == current_selected_id:
                target_idx = idx
            elif not current_selected_id and m["id"] == active_id:
                target_idx = idx

        self.fam_member_combo.blockSignals(False)
        if self.fam_member_combo.count() > 0:
            self.fam_member_combo.setCurrentIndex(target_idx)
            self._load_member_into_form(self.fam_member_combo.itemData(target_idx))

    def _on_family_member_selected_index(self, index: int):
        member_id = self.fam_member_combo.itemData(index)
        if member_id:
            self._load_member_into_form(member_id)

    def _load_member_into_form(self, member_id: str):
        member = self.family_manager.find_member(member_id)
        if not member:
            return

        self.fam_name_edit.setText(member.name)
        self.fam_eng_name_edit.setText(member.english_name)

        if member.gender == "male":
            self.fam_radio_male.setChecked(True)
        else:
            self.fam_radio_female.setChecked(True)

        # Set mood combo
        for i in range(self.fam_mood_combo.count()):
            if self.fam_mood_combo.itemData(i) == member.mood:
                self.fam_mood_combo.setCurrentIndex(i)
                break

        self.fam_role_title_edit.setText(member.role_title)

        # Set avatar combo
        for i in range(self.fam_avatar_combo.count()):
            if self.fam_avatar_combo.itemData(i) == member.avatar_style:
                self.fam_avatar_combo.setCurrentIndex(i)
                break

        self.fam_color_p_edit.setText(member.primary_color)
        self.fam_color_s_edit.setText(member.secondary_color)
        self.fam_specialties_edit.setText("، ".join(member.specialties))
        self.fam_bio_edit.setText(member.bio)

        is_active = member.id == self.family_manager.active_member_id
        status_txt = "🟢 عضو فعال و آنلاین دسکتاپ" if is_active else "⚪ در حالت آماده‌باش"
        self.fam_info_badge.setText(
            f"شناسه: <b>{member.id}</b> | نقش: <b>{member.role}</b> | سطح: <b>{member.level}</b> | امتیاز: <b>{member.xp} XP</b> | وضعیت: <b>{status_txt}</b>"
        )
        self.fam_status_lbl.setText("")

    def _save_current_family_member(self):
        """Saves edited traits into the family profiles and notifies active system."""
        member_id = self.fam_member_combo.currentData()
        if not member_id:
            return

        name = self.fam_name_edit.text().strip()
        eng_name = self.fam_eng_name_edit.text().strip()
        gender = "male" if self.fam_radio_male.isChecked() else "female"
        mood = self.fam_mood_combo.currentData() or "friendly"
        role_title = self.fam_role_title_edit.text().strip()
        avatar_style = self.fam_avatar_combo.currentData() or "cyber_bot"
        primary_color = self.fam_color_p_edit.text().strip() or "#00f3ff"
        secondary_color = self.fam_color_s_edit.text().strip() or "#b026ff"
        bio = self.fam_bio_edit.toPlainText().strip()

        specs_raw = self.fam_specialties_edit.text()
        specialties = [s.strip() for s in specs_raw.replace("،", ",").split(",") if s.strip()]

        res = self.family_manager.update_member(
            member_id_or_name=member_id,
            name=name,
            english_name=eng_name,
            gender=gender,
            mood=mood,
            role_title=role_title,
            avatar_style=avatar_style,
            primary_color=primary_color,
            secondary_color=secondary_color,
            specialties=specialties,
            bio=bio
        )

        if res.get("success"):
            member = self.family_manager.find_member(member_id)
            self.refresh_family_tab()
            self.fam_status_lbl.setText(f"✅ مشخصات «{name}» با موفقیت ذخیره و شخصی‌سازی شد.")
            if member:
                self.family_member_updated.emit(member)
                if member.id == self.family_manager.active_member_id:
                    self.family_member_switched.emit(member)
        else:
            self.fam_status_lbl.setText(f"❌ خطا در ذخیره‌سازی: {res.get('error')}")

    def _switch_to_selected_family_member(self):
        """Switches the active persona immediately to the selected family member."""
        member_id = self.fam_member_combo.currentData()
        if not member_id:
            return

        member = self.family_manager.switch_member(member_id)
        if member:
            self.refresh_family_tab()
            self.fam_status_lbl.setText(f"🌟 هویت فعال به «{member.name}» تغییر یافت.")
            self.family_member_switched.emit(member)
        else:
            self.fam_status_lbl.setText("❌ خطا در سوئیچ عضو.")

    def _prompt_add_new_family_member(self):
        """Adds a new member or child to the family."""
        import uuid
        new_id = f"child_{uuid.uuid4().hex[:4]}"
        new_data = {
            "id": new_id,
            "name": "عضو جدید",
            "english_name": "NewMember",
            "role": "child_specialist",
            "role_title": "دستیار تخصصی جدید",
            "gender": "female",
            "mood": "friendly",
            "avatar_style": "cyber_bot",
            "primary_color": "#00f3ff",
            "secondary_color": "#b026ff",
            "specialties": ["یادگیری مهارت‌های جدید"],
            "bio": "فرزند و عضو جدید خانواده هوشمند نِکسا آماده یادگیری و انجام وظایف تخصصی.",
            "xp": 100,
            "level": 1
        }
        res = self.family_manager.add_member(new_data)
        if res.get("success"):
            self.refresh_family_tab()
            # Select the newly created member in combo
            for i in range(self.fam_member_combo.count()):
                if self.fam_member_combo.itemData(i) == new_id:
                    self.fam_member_combo.setCurrentIndex(i)
                    break
            self.fam_status_lbl.setText("✨ عضو جدید با موفقیت به خانواده اضافه شد! اکنون می‌توانید نام و مشخصات او را ویرایش کنید.")
        else:
            self.fam_status_lbl.setText(f"❌ خطا در ایجاد عضو جدید: {res.get('error')}")


    # Drag window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

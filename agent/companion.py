import random
import logging
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from agent.persona import PersonaManager

logger = logging.getLogger("NovaAgent.Companion")

WELLNESS_TIPS = [
    "دوست من! یک ساعته داری مداوم کار می‌کنی، یه جرعه آب بنوش و یک دقیقه به دوردست نگاه کن تا چشمات خسته نشه 💧👀",
    "خسته نباشی! یه کشش ملایم به شونه‌ها و گردنت بده، چند تا نفس عمیق بکش تا پرانرژی ادامه بدیم 🧘‍♂️✨",
    "حواسم به سلامتیت هست! یه لیوان آب خنک بردار و به مغزت اکسیژن برسون 💧🧠",
    "چشم‌هات خسته نشن! ۲۰ ثانیه به دورترین نقطه اتاقت نگاه کن تا فوکوس عضلات چشمت ریلکس بشه 🌿",
    "عالی داری پیش میری، ولی سلامتی تو مهم‌ترین اولویته! چند قدم راه برو و آب بنوش 🚶‍♂️💧"
]


class CompanionMonitor(QObject):
    """
    Proactive Companion Engine that looks after the user's daily health,
    posture, hydration, and daily time-of-day greetings.
    """
    wellness_reminder = pyqtSignal(str)
    daily_greeting = pyqtSignal(str)

    def __init__(self, persona_manager: PersonaManager, parent=None):
        super().__init__(parent)
        self.persona_manager = persona_manager
        self.reminder_index = 0

        # Health reminder timer (fires every 50 minutes: 50 * 60 * 1000 ms)
        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self._on_health_timer)
        # Set to 50 minutes for real use
        self.health_timer.start(50 * 60 * 1000)

    def get_greeting(self) -> str:
        """Returns personalized time-of-day greeting."""
        return self.persona_manager.get_time_of_day_greeting()

    def _on_health_timer(self):
        if not self.persona_manager.health_reminders_enabled:
            return

        tip = WELLNESS_TIPS[self.reminder_index % len(WELLNESS_TIPS)]
        self.reminder_index += 1

        u_name = f"{self.persona_manager.user_name} جان! " if self.persona_manager.user_name else ""
        msg = f"{u_name}{tip}"
        logger.info(f"Triggering proactive wellness reminder: {msg[:40]}...")
        self.wellness_reminder.emit(msg)

    def trigger_manual_check(self) -> str:
        """Allows testing or instant trigger of wellness tip."""
        tip = random.choice(WELLNESS_TIPS)
        u_name = f"{self.persona_manager.user_name} جان! " if self.persona_manager.user_name else ""
        msg = f"{u_name}{tip}"
        self.wellness_reminder.emit(msg)
        return msg

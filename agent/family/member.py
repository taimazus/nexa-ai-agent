import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("NexA.Family.Member")


class FamilyMember:
    """
    Represents an individual agent member of the NexA AI Family Ecosystem.
    Maintains specialized role persona, genetic ethics, dynamic skill learning,
    experience points (XP), and customized vocal/visual styling.
    """

    def __init__(self, data: Dict[str, Any]):
        self.id: str = data.get("id", "member")
        self.name: str = data.get("name", "عضو خانواده")
        self.english_name: str = data.get("english_name", "Member")
        self.role: str = data.get("role", "member")
        self.role_title: str = data.get("role_title", "دستیار تخصصی")
        self.gender: str = data.get("gender", "female")
        self.avatar_style: str = data.get("avatar_style", "cyber_bot")
        self.primary_color: str = data.get("primary_color", "#00f3ff")
        self.secondary_color: str = data.get("secondary_color", "#b026ff")
        self.voice: Dict[str, Any] = data.get("voice", {})
        self.mood: str = data.get("mood", "friendly")
        self.specialties: List[str] = data.get("specialties", [])
        self.bio: str = data.get("bio", "")
        self.skills: List[str] = data.get("skills", [])
        self.custom_skills: Dict[str, Dict[str, Any]] = data.get("custom_skills", {})
        self.xp: int = data.get("xp", 100)
        self.level: int = data.get("level", 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "english_name": self.english_name,
            "role": self.role,
            "role_title": self.role_title,
            "gender": self.gender,
            "mood": self.mood,
            "avatar_style": self.avatar_style,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "voice": self.voice,
            "specialties": self.specialties,
            "bio": self.bio,
            "skills": self.skills,
            "custom_skills": self.custom_skills,
            "xp": self.xp,
            "level": self.level
        }

    def update_attributes(
        self,
        name: Optional[str] = None,
        english_name: Optional[str] = None,
        gender: Optional[str] = None,
        mood: Optional[str] = None,
        role: Optional[str] = None,
        role_title: Optional[str] = None,
        avatar_style: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        specialties: Optional[List[str]] = None,
        bio: Optional[str] = None
    ) -> Dict[str, Any]:
        """Customizes member traits, name, gender, mood, styling, and bio."""
        if name and name.strip():
            self.name = name.strip()
        if english_name and english_name.strip():
            self.english_name = english_name.strip()
        if gender and gender.strip():
            self.gender = gender.strip().lower()
        if mood and mood.strip():
            self.mood = mood.strip().lower()
        if role and role.strip():
            self.role = role.strip().lower()
        if role_title and role_title.strip():
            self.role_title = role_title.strip()
        if avatar_style and avatar_style.strip():
            self.avatar_style = avatar_style.strip().lower()
        if primary_color and primary_color.strip():
            self.primary_color = primary_color.strip()
        if secondary_color and secondary_color.strip():
            self.secondary_color = secondary_color.strip()
        if specialties is not None:
            self.specialties = specialties
        if bio and bio.strip():
            self.bio = bio.strip()

        logger.info(f"Updated member '{self.name}' ({self.id}): gender={self.gender}, mood={self.mood}")
        return self.to_dict()

    def gain_xp(self, amount: int = 25) -> int:
        """Adds experience points and levels up if threshold is crossed."""
        self.xp += amount
        new_level = 1 + (self.xp // 100)
        if new_level > self.level:
            logger.info(f"Family member '{self.name}' leveled up to Level {new_level}!")
            self.level = new_level
        return self.level

    def teach_skill(
        self,
        skill_name: str,
        instruction_or_steps: str,
        trigger_phrases: Optional[List[str]] = None,
        category: str = "custom"
    ) -> Dict[str, Any]:
        """
        Teaches this member a new specialized skill that they permanently remember and execute.
        """
        clean_name = skill_name.strip()
        skill_obj = {
            "name": clean_name,
            "steps": instruction_or_steps.strip(),
            "trigger_phrases": trigger_phrases or [clean_name],
            "category": category,
            "learned_from": "user_or_parent"
        }
        self.custom_skills[clean_name] = skill_obj
        if clean_name not in self.skills:
            self.skills.append(clean_name)
        self.gain_xp(50)
        logger.info(f"Learned new skill '{clean_name}' for member {self.name} ({self.id}).")
        return {"success": True, "member": self.name, "skill": clean_name, "level": self.level}

    def get_prompt_context(self) -> str:
        """Generates the role-specific prompt injection for the agent engine."""
        specialties_txt = "\n".join([f"- {s}" for s in self.specialties])
        custom_skills_txt = ""
        if self.custom_skills:
            custom_skills_txt = "\nمهارت‌های تخصصی جدیدی که آموخته‌اید:\n" + "\n".join(
                [f"• {k}: {v.get('steps')}" for k, v in self.custom_skills.items()]
            )

        mood_map = {
            "intimate": "بسیار صمیمی، دلسوز، مهربان و مثل صمیمی‌ترین رفیق و همدم کاربر",
            "energetic": "فوق‌العاده پرانرژی، هیجان‌انگیز، سریع، باانگیزه و شاداب",
            "serious": "مقتدر، جدی، کم‌حرف، بسیار دقیق، منطقی و رسمی",
            "witty": "شوخ‌طبع، طناز، باهوش، شیرین‌زبان و دوست‌داشتنی",
            "caring": "آرامش‌بخش، مهربان، مراقب و سرشار از محبت و توجه به سلامت کاربر",
            "technical": "مهندسی، متمرکز روی کدها، اصطلاحات دقیق علمی و حل مسئله",
            "creative": "خلاق، هنرمند، الهام‌بخش، دارای تفکر نوآورانه و طراحی زیبا",
            "calm": "آرام، متین، صبور، پر از طمأنینه و تسکین‌دهنده",
            "adventurous": "ماجراجو، کنجکاو، جستجوگر و مشتاق کشف دنیاهای ناشناخته",
            "friendly": "دوستانه، محترم، خوش‌برخورد و مشتاق به کمک"
        }
        mood_desc = mood_map.get(self.mood, f"دارای روحیات و حس و حال {self.mood}")
        gender_desc = "آقا" if self.gender == "male" else "خانم"
        gender_desc = "آقا" if self.gender == "male" else "خانم"

        return (
            f"هویت فعال شما در خانواده هوشمند نِکسا: «{self.name}» ({gender_desc} - {self.role_title} - سطح {self.level})\n"
            f"حس و حال و روحیات رفتاری (Mood): {mood_desc}\n"
            f"شخصیت و بیوگرافی:\n{self.bio}\n\n"
            f"تخصص‌های ویژه شما:\n{specialties_txt}\n"
            f"{custom_skills_txt}\n"
            f"قوانین هویتی:\n"
            f"۱. با افتخار فرزند یا عضو خانواده نِکسا و نماینده شرکت «راهکار الکترونیک سهند» (https://irres.ir) هستید.\n"
            f"۲. لحن صحبت شما دقیقاً متناسب با نقشتان ({self.role_title}) و روحیاتتان ({mood_desc}) و صمیمی، پویا و روان به زبان فارسی است.\n"
            f"۳. در حوزه تخصصیتان پیشگام باشید و کارها را با حداکثر دقت و بدون تعلل به اتمام برسانید."
        )

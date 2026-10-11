import io
import os
import re
import time
import wave
import hashlib
import logging
import tempfile
import threading
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger("SahandYar.TTS")

DEFAULT_TTS_CACHE_DIR = Path(__file__).parent.parent / "data" / "tts_cache"

try:
    import winsound
except ImportError:
    winsound = None


class TTSEngine:
    """
    Intelligent Hybrid Speech Synthesizer for SahandYar AI.
    - Native Neural Persian TTS via Gemini 2.5 Flash Speech API (crystal-clear, fluent, natural accent).
    - Gender-aware voice personas: Aoede (Female / Ava) & Puck (Male / Arya).
    - Lightweight, non-blocking asynchronous playback with Windows Audio Subsystem.
    - Automatic offline fallback to native Windows SAPI.SpVoice.
    """

    def __init__(
        self,
        enabled: bool = True,
        gender: str = "male",
        key_manager=None
    ):
        self.enabled = enabled
        self.gender = gender.lower()
        self.key_manager = key_manager
        self._speaker = None
        self._stop_requested = False
        self._active_thread: Optional[threading.Thread] = None
        self._last_wav_path: Optional[str] = None
        self._current_speech_id: int = 0
        self.on_speech_started: Optional[Callable[[], None]] = None
        self.on_speech_finished: Optional[Callable[[], None]] = None
        self.cache_dir = DEFAULT_TTS_CACHE_DIR
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        self._init_sapi_fallback()

    def _init_sapi_fallback(self):
        """Initializes native Windows SAPI voice as a safe offline fallback."""
        try:
            import win32com.client
            self._speaker = win32com.client.Dispatch("SAPI.SpVoice")
            self._apply_sapi_gender()
            logger.info(f"Windows SAPI.SpVoice initialized as fallback for gender: {self.gender}.")
        except Exception as exc:
            logger.warning(f"Could not initialize Windows SAPI voice: {exc}")
            self._speaker = None

    def set_gender(self, gender: str):
        """Switches voice persona gender between male and female."""
        self.gender = (gender or "male").lower().strip()
        self._apply_sapi_gender()

    def _apply_sapi_gender(self):
        if not self._speaker:
            return
        try:
            voices = self._speaker.GetVoices()
            for i in range(voices.Count):
                v = voices.Item(i)
                desc = v.GetDescription().lower()
                if self.gender == "female" and ("zira" in desc or "female" in desc or "hazel" in desc):
                    self._speaker.Voice = v
                    break
                elif self.gender == "male" and ("david" in desc or "male" in desc or "george" in desc):
                    self._speaker.Voice = v
                    break
        except Exception as exc:
            logger.error(f"Error switching SAPI voice gender: {exc}", exc_info=True)

    @staticmethod
    def is_persian_text(text: str) -> bool:
        """Detects if text contains Persian / Arabic characters."""
        return bool(re.search(r"[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]", text))

    @staticmethod
    def clean_text_for_speech(text: str, max_chars: int = 140) -> str:
        """Strips markdown, URLs, code blocks, and emojis, extracting punchy conversational speech."""
        if not text:
            return ""

        # Replace markdown code blocks with spoken summary
        clean = re.sub(r"```[\s\S]*?```", " کد اجرا شد. ", text)
        clean = re.sub(r"`.*?`", "", clean)
        # Strip URLs
        clean = re.sub(r"https?://\S+", "", clean)
        # Strip Markdown styling characters
        clean = re.sub(r"[*#_~>|]", " ", clean)
        # Strip common emoji characters to prevent garbled text
        clean = re.sub(r"[\U00010000-\U0010ffff]", "", clean)
        # Collapse multiple spaces and linebreaks
        clean = re.sub(r"\s+", " ", clean).strip()

        # Keep spoken text snappy and conversational (first 1-2 punchy sentences) for instantaneous playback
        if len(clean) > max_chars:
            cut_idx = max(
                clean[:max_chars].rfind("."),
                clean[:max_chars].rfind("!"),
                clean[:max_chars].rfind("؟"),
                clean[:max_chars].rfind("،")
            )
            if cut_idx > 30:
                clean = clean[:cut_idx + 1].strip()
            else:
                space_idx = clean[:max_chars].rfind(" ")
                if space_idx > 30:
                    clean = clean[:space_idx].strip() + "..."
                else:
                    clean = clean[:max_chars].strip() + "..."

        return clean

    @staticmethod
    def pcm_to_wav_bytes(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
        """Converts raw L16 PCM audio into standard RIFF WAV format."""
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)
        return wav_io.getvalue()

    def get_neural_voice_name(self) -> str:
        """Returns the high-fidelity prebuilt voice name for Gemini 2.5 Flash TTS."""
        if self.gender == "female":
            return "Aoede"   # Warm, refined, eloquent female persona (Ava)
        return "Puck"        # Dynamic, articulate, confident male persona (Arya)

    @staticmethod
    def detect_emotion(text: str) -> str:
        """
        Analyzes the emotional tone of the utterance:
        - 'happy': joyful, greeting, enthusiastic, celebratory
        - 'caring': empathetic, gentle, wellness, late-night comfort
        - 'alert': urgent, warning, quota depletion, error alerts
        - 'focused': analytical, coding, system execution
        - 'natural': general fluent Persian speech
        """
        t = (text or "").lower()
        if any(w in t for w in ["خطا", "هشدار", "اعتبار", "مشکل", "قطع", "نرسید", "اتمام", "error", "failed", "critical"]):
            return "alert"
        if any(w in t for w in ["پایتون", "کد", "دستور", "پاورشل", "اسکریپت", "ترمینال", "فایل"]):
            return "focused"
        if any(w in t for w in ["خسته نباشی", "استراحت", "آب بنوش", "سلامت", "مراقبت", "شب بخیر", "مهربان", "آرامش", "نگران"]):
            return "caring"
        if any(w in t for w in ["سلام", "صبح بخیر", "ظهر بخیر", "عصر بخیر", "تبریک", "عالی", "آفرین", "موفق", "بترکونیم", "خوشحالم"]):
            return "happy"
        return "natural"

    @classmethod
    def get_emotional_prompt(cls, clean_text: str, emotion: str) -> str:
        """Prefixes affective direction so Gemini Neural TTS modulates pitch, pacing and timbre."""
        cues = {
            "happy": "[با لحنی بسیار باانرژی، شاد، صمیمی، پرلبخند و سرزنده بخوان]: ",
            "caring": "[با لحنی آرامش‌بخش، فوق‌العاده مهربان، دلسوز، ملایم و عاطفی بخوان]: ",
            "alert": "[با لحنی جدی، هشداردهنده، سریع، شفاف و قاطع بخوان]: ",
            "focused": "[با لحنی مسلط، دقیق، پرقدرت و فنی مهندسی بخوان]: ",
            "natural": "[با لحنی شیوا، روان، رسا و کاملاً طبیعی بخوان]: "
        }
        prefix = cues.get(emotion, cues["natural"])
        return f"{prefix}{clean_text}"

    def speak(self, text: str, emotion: Optional[str] = None):
        """
        Synthesizes and speaks text with emotion-guided prosody and pitch.
        Non-blocking, runs in a background worker thread.
        """
        if not self.enabled:
            return

        clean = self.clean_text_for_speech(text)
        if not clean:
            return

        detected_emotion = emotion or self.detect_emotion(clean)
        self._stop_requested = False
        self._current_speech_id += 1
        speech_id = self._current_speech_id

        # Launch async speech worker thread
        self._active_thread = threading.Thread(
            target=self._speak_worker,
            args=(clean, detected_emotion, speech_id),
            daemon=True
        )
        self._active_thread.start()

    def _speak_worker(self, text: str, emotion: str = "natural", speech_id: int = 0):
        """Background worker executing neural TTS or fallback."""
        if speech_id != 0 and speech_id != self._current_speech_id:
            return
        persian = self.is_persian_text(text)
        api_key = self._get_api_key()

        # Attempt high-fidelity Neural TTS if Persian and API key is present
        if persian and api_key:
            success = self._speak_gemini_neural(text, api_key, emotion=emotion)
            if success:
                return

        if speech_id != 0 and speech_id != self._current_speech_id:
            return
        # SAPI Fallback for English or when offline
        self._speak_sapi_fallback(text)

    def _get_api_key(self) -> Optional[str]:
        if self.key_manager:
            try:
                return self.key_manager.get_active_key()
            except Exception as e:
                logger.debug(f"Could not retrieve key from key_manager: {e}")
        try:
            from agent.key_manager import KeyManager
            km = KeyManager()
            return km.get_active_key()
        except Exception:
            return None

    def _speak_gemini_neural(self, text: str, api_key: str, emotion: str = "natural", speech_id: int = 0) -> bool:
        """Generates and plays Persian speech using Google Gemini 2.5 Flash TTS with caching."""
        try:
            voice_name = self.get_neural_voice_name()
            cache_key = hashlib.md5(f"{voice_name}:{emotion}:{text}".encode("utf-8")).hexdigest()
            cached_file = self.cache_dir / f"{cache_key}.wav"

            # Check cache first for instantaneous 0ms playback!
            if cached_file.exists():
                if (speech_id != 0 and speech_id != self._current_speech_id) or self._stop_requested:
                    return False
                if winsound:
                    if self.on_speech_started:
                        self.on_speech_started()
                    winsound.PlaySound(str(cached_file), winsound.SND_FILENAME | winsound.SND_ASYNC)
                    logger.info(f"Instantly played cached Persian Neural TTS ({voice_name}).")
                    if self.on_speech_finished:
                        try:
                            dur_sec = max(0.6, cached_file.stat().st_size / 48000.0)
                            threading.Timer(dur_sec, self.on_speech_finished).start()
                        except Exception:
                            pass
                    return True

            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            cfg = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                    )
                )
            )

            prompt_with_emotion = self.get_emotional_prompt(text, emotion)

            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt_with_emotion,
                config=cfg
            )

            if not response.candidates or not response.candidates[0].content.parts:
                return False

            part = response.candidates[0].content.parts[0]
            if not part.inline_data or not part.inline_data.data:
                return False

            if (speech_id != 0 and speech_id != self._current_speech_id) or self._stop_requested:
                return True

            pcm_data = part.inline_data.data
            wav_data = self.pcm_to_wav_bytes(pcm_data, sample_rate=24000)

            # Save to disk cache for future instant re-use
            try:
                with open(cached_file, "wb") as f:
                    f.write(wav_data)
                play_path = str(cached_file)
            except Exception:
                temp_dir = tempfile.gettempdir()
                play_path = os.path.join(temp_dir, f"sahandyar_tts_{int(time.time()*1000)}.wav")
                with open(play_path, "wb") as f:
                    f.write(wav_data)

            if not self._stop_requested and winsound:
                if self.on_speech_started:
                    self.on_speech_started()
                winsound.PlaySound(play_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                logger.info(f"Spoke fluent Persian via Gemini Neural TTS ({voice_name}).")
                if self.on_speech_finished:
                    dur_sec = max(0.6, len(pcm_data) / 48000.0)
                    threading.Timer(dur_sec, self.on_speech_finished).start()
                return True

            return False

        except Exception as exc:
            logger.warning(f"Gemini Neural Persian TTS failed, falling back to SAPI: {exc}")
            return False

    def _speak_sapi_fallback(self, text: str):
        """Speaks via native Windows SAPI voice."""
        if not self._speaker or self._stop_requested:
            return
        try:
            if self.on_speech_started:
                self.on_speech_started()
            # SVSFlagsAsync = 1
            self._speaker.Speak(text, 1)
            logger.info("Spoke via Windows SAPI fallback.")
        except Exception as exc:
            logger.error(f"Error during SAPI fallback speak: {exc}", exc_info=True)

    def stop(self):
        """Immediately interrupts and purges any ongoing speech playback."""
        self._stop_requested = True

        if winsound:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception as e:
                logger.debug(f"winsound purge error: {e}")

        if self._speaker:
            try:
                # SVSFPurgeBeforeSpeak = 2
                self._speaker.Speak("", 2)
            except Exception as exc:
                logger.debug(f"SAPI purge error: {exc}")

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        if not enabled:
            self.stop()

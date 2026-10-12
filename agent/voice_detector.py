import os
import time
import wave
import struct
import math
import tempfile
import logging
from collections import deque
from typing import Optional, Dict, Any, List

from PyQt6.QtCore import QObject, pyqtSignal, QIODevice
from PyQt6.QtMultimedia import (
    QAudioSource,
    QAudioFormat,
    QMediaDevices,
    QAudioDevice
)

logger = logging.getLogger("NexA.VoiceDetector")

SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2  # 16-bit Int16


class ContinuousVoiceListener(QObject):
    """
    Hands-Free Real-time Voice Activity Detection (VAD) & Continuous Audio Listener.
    
    Provides natural human-to-human conversational flow for NexA:
    1. Continuously monitors the default microphone in the background.
    2. Dynamically tracks ambient background noise and detects when the user begins speaking.
    3. Keeps a pre-speech ring buffer (~300ms) so starting syllables are never clipped.
    4. Automatically detects natural pauses and speech completion after a calibrated silence period (~0.8-1.0s).
    5. Packages the speech into a broadcast-quality 16kHz PCM WAV file and emits it for immediate processing.
    6. Features acoustic interlock: safely pauses while the AI is speaking so NexA never talks to itself.
    """

    speech_started = pyqtSignal()
    speech_completed = pyqtSignal(str)   # emits path to recorded .wav file
    speech_canceled = pyqtSignal()
    audio_level = pyqtSignal(float)      # normalized 0.0 - 1.0 for UI audio wave
    state_changed = pyqtSignal(str)      # "idle", "hearing_speech", "paused", "stopped"
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        parent=None,
        silence_timeout_sec: float = 0.9,
        sensitivity: str = "medium",
        min_speech_duration_sec: float = 0.35,
        max_speech_duration_sec: float = 45.0
    ):
        super().__init__(parent)
        self.silence_timeout_sec = silence_timeout_sec
        self.sensitivity = sensitivity
        self.min_speech_duration_sec = min_speech_duration_sec
        self.max_speech_duration_sec = max_speech_duration_sec

        # Audio capture objects
        self.audio_source: Optional[QAudioSource] = None
        self.io_device: Optional[QIODevice] = None
        self.audio_format = QAudioFormat()
        self.audio_format.setSampleRate(SAMPLE_RATE)
        self.audio_format.setChannelCount(CHANNELS)
        self.audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        # Internal state
        self._is_running = False
        self._is_paused = False
        self._is_speaking = False
        self._speech_start_time: float = 0.0
        self._last_speech_time: float = 0.0
        self._noise_floor: float = 120.0

        # Buffers:
        # Pre-speech ring buffer holds ~300ms of audio (approx 10 chunks of 480 samples each)
        self._pre_speech_ring: deque = deque(maxlen=8)
        self._current_speech_buffer: List[bytes] = []

        # Wake-word management
        self.wake_word_mode = False
        self.wake_words = ["نکسا", "نِکسا", "nexa", "سلام نکسا", "هی نکسا"]
        self.active_dialog_timeout_sec = 30.0
        self._last_dialog_activity = 0.0

    # --- Configuration ---
    def set_wake_word_mode(self, enabled: bool):
        """Enables or disables requirement to say 'NexA' to initiate a conversation."""
        self.wake_word_mode = bool(enabled)
        logger.info(f"Wake-word mode set to: {self.wake_word_mode}")

    def is_dialog_active(self) -> bool:
        """Returns True if within active conversational window (within 30s of last exchange)."""
        if not self.wake_word_mode:
            return True
        return (time.time() - self._last_dialog_activity) < self.active_dialog_timeout_sec

    def activate_dialog(self):
        """Refreshes the active dialog session timer."""
        self._last_dialog_activity = time.time()
        logger.info("Conversational dialog session activated.")

    def deactivate_dialog(self):
        """Immediately puts assistant back into passive standby."""
        self._last_dialog_activity = 0.0
        logger.info("Conversational dialog returned to standby.")

    def set_silence_timeout(self, seconds: float):
        """Sets the silence timeout before declaring utterance complete."""
        self.silence_timeout_sec = max(0.4, min(3.0, float(seconds)))
        logger.info(f"Silence timeout set to {self.silence_timeout_sec}s")

    def set_sensitivity(self, level: str):
        """Sets VAD threshold sensitivity ('low', 'medium', 'high')."""
        if level in ["low", "medium", "high"]:
            self.sensitivity = level
            logger.info(f"VAD sensitivity set to {level}")

    def get_threshold(self) -> float:
        """Calculates dynamic speech detection threshold based on sensitivity and ambient floor."""
        if self.sensitivity == "high":
            # Sensitive to whispers and quiet speech
            return max(150.0, self._noise_floor * 1.5)
        elif self.sensitivity == "low":
            # High noise gate for noisy environments
            return max(500.0, self._noise_floor * 3.0)
        else:
            # Medium: standard desktop environment (normal comfortable speaking distance)
            return max(240.0, self._noise_floor * 1.8)

    # --- Lifecycle Controls ---
    def is_running(self) -> bool:
        return self._is_running

    def is_paused(self) -> bool:
        return self._is_paused

    def is_speaking(self) -> bool:
        return self._is_speaking

    def start(self) -> bool:
        """Starts real-time continuous microphone listening."""
        if self._is_running:
            return True

        try:
            device = QMediaDevices.defaultAudioInput()
            if device.isNull():
                err_msg = "دستگاه ورودی میکروفون در ویندوز یافت نشد."
                logger.warning(err_msg)
                self.error_occurred.emit(err_msg)
                return False

            self.audio_source = QAudioSource(device, self.audio_format, self)
            self.audio_source.setBufferSize(8192)
            self.io_device = self.audio_source.start()

            if not self.io_device:
                err_msg = "نتوانست جریان صوتی میکروفون را فعال کند."
                logger.error(err_msg)
                self.error_occurred.emit(err_msg)
                return False

            self.io_device.readyRead.connect(self._on_audio_ready)
            self._is_running = True
            self._is_paused = False
            self._is_speaking = False
            self._current_speech_buffer.clear()
            self._pre_speech_ring.clear()
            self.state_changed.emit("idle")
            logger.info("Continuous Voice Listener successfully started.")
            return True
        except Exception as exc:
            logger.error(f"Failed to start continuous voice listener: {exc}", exc_info=True)
            self.error_occurred.emit(str(exc))
            return False

    def stop(self):
        """Stops microphone capture and releases hardware resources."""
        if not self._is_running:
            return

        try:
            if self.audio_source:
                self.audio_source.stop()
                self.audio_source = None
            self.io_device = None
            self._is_running = False
            self._is_paused = False
            self._is_speaking = False
            self._current_speech_buffer.clear()
            self.state_changed.emit("stopped")
            logger.info("Continuous Voice Listener stopped.")
        except Exception as exc:
            logger.error(f"Error stopping voice listener: {exc}", exc_info=True)

    def pause_listening(self):
        """Temporarily mutes/pauses VAD (e.g. while AI is speaking / playing TTS)."""
        if self._is_running and not self._is_paused:
            self._is_paused = True
            self._is_speaking = False
            self._current_speech_buffer.clear()
            self.state_changed.emit("paused")
            logger.debug("Voice listener paused (AI interlock active).")

    def resume_listening(self):
        """Resumes VAD after AI finishes speaking."""
        if self._is_running and self._is_paused:
            self._is_paused = False
            self._is_speaking = False
            self._current_speech_buffer.clear()
            self._pre_speech_ring.clear()
            self.state_changed.emit("idle")
            logger.debug("Voice listener resumed (Listening for user speech).")

    # --- Audio Processing & VAD Core ---
    def _on_audio_ready(self):
        """Slot invoked whenever new audio chunks are available from QIODevice."""
        if not self._is_running or self._is_paused or not self.io_device:
            return

        try:
            raw_bytes = self.io_device.readAll().data()
            if raw_bytes:
                self.feed_pcm_chunk(raw_bytes)
        except Exception as exc:
            logger.error(f"Error reading PCM audio: {exc}", exc_info=True)

    def feed_pcm_chunk(self, raw_bytes: bytes):
        """
        Processes a raw 16-bit PCM chunk.
        Exposed publicly to enable programmatic simulation and unit testing.
        """
        if not raw_bytes or len(raw_bytes) < 4:
            return

        rms = self._calculate_rms(raw_bytes)
        now = time.time()

        # Emit normalized audio level for visual UI feedback (0.0 to 1.0)
        norm_level = min(1.0, rms / 1500.0)
        self.audio_level.emit(norm_level)

        threshold = self.get_threshold()

        if not self._is_speaking:
            # Maintain pre-speech ring buffer
            self._pre_speech_ring.append(raw_bytes)

            # Adaptively update background noise floor during silence
            if rms < threshold:
                self._noise_floor = 0.96 * self._noise_floor + 0.04 * rms

            # Speech onset detection
            if rms >= threshold:
                self._is_speaking = True
                self._speech_start_time = now
                self._last_speech_time = now
                self._current_speech_buffer.clear()
                # Prepend pre-speech ring buffer so the first syllable is never lost
                self._current_speech_buffer.extend(self._pre_speech_ring)
                self._current_speech_buffer.append(raw_bytes)
                self.speech_started.emit()
                self.state_changed.emit("hearing_speech")
                logger.info(f"User speech detected! RMS={rms:.1f} > Threshold={threshold:.1f}")

        else:
            # Currently in speech mode
            self._current_speech_buffer.append(raw_bytes)

            if rms >= threshold:
                # Active speech continues
                self._last_speech_time = now
            else:
                # Silence frame detected during speech
                silence_duration = now - self._last_speech_time
                total_duration = now - self._speech_start_time

                # Check safety max duration
                if total_duration >= self.max_speech_duration_sec:
                    logger.info("Max speech duration reached, wrapping utterance.")
                    self._finalize_speech()
                    return

                # Check if silence timeout exceeded
                if silence_duration >= self.silence_timeout_sec:
                    logger.info(
                        f"Silence timeout ({silence_duration:.2f}s >= {self.silence_timeout_sec}s) met. Speech complete."
                    )
                    self._finalize_speech()

    def _finalize_speech(self):
        """Finalizes speech recording, checks minimum duration, and generates WAV file."""
        now = time.time()
        speech_duration = max(0.0, self._last_speech_time - self._speech_start_time)
        self._is_speaking = False

        if speech_duration < self.min_speech_duration_sec or not self._current_speech_buffer:
            logger.debug(f"Speech duration ({speech_duration:.2f}s) below minimum ({self.min_speech_duration_sec}s); ignored.")
            self._current_speech_buffer.clear()
            self.speech_canceled.emit()
            self.state_changed.emit("idle")
            return

        # Combine all audio chunks
        full_pcm = b"".join(self._current_speech_buffer)
        self._current_speech_buffer.clear()

        # Save to temporary uncompressed WAV file
        try:
            temp_dir = tempfile.gettempdir()
            wav_path = os.path.join(temp_dir, f"nexa_utterance_{int(time.time() * 1000)}.wav")
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(BYTES_PER_SAMPLE)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(full_pcm)

            logger.info(f"Utterance packaged into WAV: {wav_path} ({speech_duration:.2f}s, {len(full_pcm)} bytes)")
            self.speech_completed.emit(wav_path)
            self.state_changed.emit("idle")
        except Exception as exc:
            logger.error(f"Error packaging utterance to WAV: {exc}", exc_info=True)
            self.error_occurred.emit(str(exc))
            self.state_changed.emit("idle")

    @staticmethod
    def _calculate_rms(raw_bytes: bytes) -> float:
        """Fast calculation of Root Mean Square amplitude of 16-bit PCM bytes."""
        count = len(raw_bytes) // 2
        if count == 0:
            return 0.0

        try:
            # Unpack signed 16-bit little-endian samples
            samples = struct.unpack(f"<{count}h", raw_bytes[: count * 2])
            sum_squares = sum(s * s for s in samples)
            return math.sqrt(sum_squares / count)
        except Exception:
            return 0.0

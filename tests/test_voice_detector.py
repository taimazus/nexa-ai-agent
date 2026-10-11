import os
import time
import wave
import struct
import pytest
from unittest.mock import MagicMock, patch

from agent.voice_detector import ContinuousVoiceListener


@pytest.fixture
def voice_listener():
    # Use fast timeouts for deterministic testing
    return ContinuousVoiceListener(
        silence_timeout_sec=0.2,
        min_speech_duration_sec=0.15,
        max_speech_duration_sec=2.0
    )


def _generate_pcm_chunk(amplitude: int = 2000, num_samples: int = 480) -> bytes:
    """Helper to generate a 16-bit PCM chunk with a specified amplitude."""
    return struct.pack(f"<{num_samples}h", *([amplitude] * num_samples))


def test_listener_initial_state_and_configuration(voice_listener):
    """Test initial listener state and threshold calculations."""
    assert not voice_listener.is_running()
    assert not voice_listener.is_paused()
    assert not voice_listener.is_speaking()

    voice_listener.set_silence_timeout(0.8)
    assert voice_listener.silence_timeout_sec == 0.8

    voice_listener.set_sensitivity("high")
    th_high = voice_listener.get_threshold()
    voice_listener.set_sensitivity("low")
    th_low = voice_listener.get_threshold()
    assert th_high < th_low


def test_rms_calculation():
    """Verify Root Mean Square calculation for silent and loud audio."""
    silent_pcm = _generate_pcm_chunk(amplitude=0, num_samples=320)
    assert ContinuousVoiceListener._calculate_rms(silent_pcm) == 0.0

    loud_pcm = _generate_pcm_chunk(amplitude=3000, num_samples=320)
    rms = ContinuousVoiceListener._calculate_rms(loud_pcm)
    assert 2900.0 < rms < 3100.0


def test_speech_onset_and_silence_completion(voice_listener):
    """Simulate a complete user speech utterance followed by silence."""
    voice_listener._is_running = True

    speech_started_called = []
    speech_completed_files = []

    voice_listener.speech_started.connect(lambda: speech_started_called.append(True))
    voice_listener.speech_completed.connect(lambda path: speech_completed_files.append(path))

    loud_chunk = _generate_pcm_chunk(amplitude=4000, num_samples=800)
    silent_chunk = _generate_pcm_chunk(amplitude=50, num_samples=800)

    # 1. Feed loud speech chunks for 0.25s
    for _ in range(5):
        voice_listener.feed_pcm_chunk(loud_chunk)
        time.sleep(0.05)

    assert len(speech_started_called) == 1
    assert voice_listener.is_speaking()

    # 2. Feed silence beyond the 0.2s silence_timeout_sec
    time.sleep(0.25)
    voice_listener.feed_pcm_chunk(silent_chunk)

    assert not voice_listener.is_speaking()
    assert len(speech_completed_files) == 1
    wav_path = speech_completed_files[0]

    try:
        assert os.path.exists(wav_path)
        assert os.path.getsize(wav_path) > 100

        # Validate WAV structure
        with wave.open(wav_path, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 16000
            assert wf.getnframes() > 0
    finally:
        if os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass


def test_short_burst_noise_rejection(voice_listener):
    """Verify that a brief accidental noise (< min_speech_duration_sec) is rejected."""
    voice_listener._is_running = True
    canceled_called = []
    completed_called = []

    voice_listener.speech_canceled.connect(lambda: canceled_called.append(True))
    voice_listener.speech_completed.connect(lambda p: completed_called.append(p))

    loud_chunk = _generate_pcm_chunk(amplitude=4000, num_samples=320)
    silent_chunk = _generate_pcm_chunk(amplitude=50, num_samples=320)

    # Feed only one quick frame (duration << 0.15s)
    voice_listener.feed_pcm_chunk(loud_chunk)

    # Wait for silence timeout
    time.sleep(0.25)
    voice_listener.feed_pcm_chunk(silent_chunk)

    assert len(completed_called) == 0
    assert len(canceled_called) == 1


def test_pause_and_resume_interlock(voice_listener):
    """Verify that audio is ignored when listener is paused (AI speaking interlock)."""
    voice_listener._is_running = True
    voice_listener.pause_listening()
    assert voice_listener.is_paused()

    speech_started_called = []
    voice_listener.speech_started.connect(lambda: speech_started_called.append(True))

    loud_chunk = _generate_pcm_chunk(amplitude=5000, num_samples=800)
    # When paused, _on_audio_ready / feed_pcm_chunk should be ignored
    voice_listener._on_audio_ready()
    assert len(speech_started_called) == 0

    voice_listener.resume_listening()
    assert not voice_listener.is_paused()


def test_wake_word_mode_activation(voice_listener):
    """Verify wake-word mode dialog timeout and state transitions."""
    assert voice_listener.is_dialog_active()  # When wake_word_mode is False, always active

    voice_listener.set_wake_word_mode(True)
    assert not voice_listener.is_dialog_active()  # When True and unactivated, standby

    voice_listener.activate_dialog()
    assert voice_listener.is_dialog_active()

    voice_listener.deactivate_dialog()
    assert not voice_listener.is_dialog_active()


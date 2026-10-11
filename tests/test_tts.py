import io
import wave
import pytest
from unittest.mock import MagicMock, patch

from agent.tts import TTSEngine


def test_tts_initialization():
    engine = TTSEngine(enabled=True, gender="female")
    assert engine.enabled is True
    assert engine.gender == "female"
    assert engine.get_neural_voice_name() == "Aoede"

    engine.set_gender("male")
    assert engine.gender == "male"
    assert engine.get_neural_voice_name() == "Puck"


def test_is_persian_detection():
    assert TTSEngine.is_persian_text("سلام من سهندیار هستم") is True
    assert TTSEngine.is_persian_text("صبح بخیر دوست من! ☀️") is True
    assert TTSEngine.is_persian_text("Hello, how are you today?") is False
    assert TTSEngine.is_persian_text("1234567890 !@#$%") is False


def test_clean_text_for_speech():
    raw_markdown = """
    سلام دوست من! 🌟 من **سهندیار** هستم.
    ```python
    print("hello world")
    ```
    به وب‌سایت https://irres.ir سر بزنید و از `کدهای سیستم` لذت ببرید!
    """
    cleaned = TTSEngine.clean_text_for_speech(raw_markdown)

    assert "```" not in cleaned
    assert "https://" not in cleaned
    assert "**" not in cleaned
    assert "کد اجرا شد" in cleaned
    assert "سهندیار" in cleaned
    assert "🌟" not in cleaned


def test_pcm_to_wav_bytes():
    # 1 second of silence at 24000 Hz, 16-bit mono
    dummy_pcm = b"\x00\x00" * 24000
    wav_bytes = TTSEngine.pcm_to_wav_bytes(dummy_pcm, sample_rate=24000, channels=1, sample_width=2)

    assert wav_bytes.startswith(b"RIFF")
    assert b"WAVE" in wav_bytes

    # Parse with wave module to verify validity
    wav_io = io.BytesIO(wav_bytes)
    with wave.open(wav_io, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 24000
        assert wf.getnframes() == 24000


def test_speak_disabled_does_nothing():
    engine = TTSEngine(enabled=False)
    with patch.object(engine, "_speak_gemini_neural") as mock_gemini:
        with patch.object(engine, "_speak_sapi_fallback") as mock_sapi:
            engine.speak("سلام سهندیار")
            assert mock_gemini.call_count == 0
            assert mock_sapi.call_count == 0


def test_speak_persian_calls_gemini_neural():
    mock_km = MagicMock()
    mock_km.get_active_key.return_value = "AIzaFakeKey123"

    engine = TTSEngine(enabled=True, gender="female", key_manager=mock_km)

    with patch.object(engine, "_speak_gemini_neural", return_value=True) as mock_gemini:
        with patch.object(engine, "_speak_sapi_fallback") as mock_sapi:
            engine._speak_worker("سلام من سهندیار هستم")
            mock_gemini.assert_called_once_with("سلام من سهندیار هستم", "AIzaFakeKey123", emotion="natural")
            mock_sapi.assert_not_called()


def test_speak_persian_fallback_on_failure():
    mock_km = MagicMock()
    mock_km.get_active_key.return_value = "AIzaFakeKey123"

    engine = TTSEngine(enabled=True, gender="female", key_manager=mock_km)

    with patch.object(engine, "_speak_gemini_neural", return_value=False) as mock_gemini:
        with patch.object(engine, "_speak_sapi_fallback") as mock_sapi:
            engine._speak_worker("سلام من سهندیار هستم")
            mock_gemini.assert_called_once()
            mock_sapi.assert_called_once_with("سلام من سهندیار هستم")


def test_stop_and_set_enabled():
    engine = TTSEngine(enabled=True)
    engine.stop()
    assert engine._stop_requested is True

    engine.set_enabled(False)
    assert engine.enabled is False
    assert engine._stop_requested is True


def test_emotion_detection_and_prompting():
    assert TTSEngine.detect_emotion("هشدار! خطای بحرانی در سیستم رخ داد") == "alert"
    assert TTSEngine.detect_emotion("خسته نباشی دوست من، یه لیوان آب بنوش و استراحت کن") == "caring"
    assert TTSEngine.detect_emotion("سلام! صبح بخیر، امروز روز عالی و پرانرژی خواهد بود") == "happy"
    assert TTSEngine.detect_emotion("دستور پایتون با موفقیت در سیستم اجرا شد") == "focused"
    assert TTSEngine.detect_emotion("این یک پیام معمولی است.") == "natural"

    # Verify prompt prefixing
    p_happy = TTSEngine.get_emotional_prompt("سلام", "happy")
    assert "شاد" in p_happy or "پرانرژی" in p_happy
    assert "سلام" in p_happy

    p_caring = TTSEngine.get_emotional_prompt("استراحت کن", "caring")
    assert "مهربان" in p_caring or "آرامش‌بخش" in p_caring
    assert "استراحت کن" in p_caring


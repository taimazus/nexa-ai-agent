import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from ui.chat_window import AgentWorkerThread, ChatWindow


def test_agent_worker_thread_success(qapp):
    mock_engine = MagicMock()
    mock_engine.process_user_message.return_value = "پاسخ تست هوش مصنوعی"

    worker = AgentWorkerThread(mock_engine, "سلام")
    results = []
    worker.response_ready.connect(lambda reply: results.append(reply))

    worker.run()
    assert len(results) == 1
    assert results[0] == "پاسخ تست هوش مصنوعی"


def test_agent_worker_thread_exception_safety(qapp):
    mock_engine = MagicMock()
    mock_engine.process_user_message.side_effect = RuntimeError("شبیه‌سازی خطای بحرانی سرور")

    worker = AgentWorkerThread(mock_engine, "دستور خطا")
    states = []
    responses = []
    worker.state_changed.connect(lambda s: states.append(s))
    worker.response_ready.connect(lambda r: responses.append(r))

    # Must NOT raise exception and MUST emit error state and safe response
    worker.run()
    assert "error" in states
    assert len(responses) == 1
    assert "خطای غیرمنتظره" in responses[0]


def test_agent_worker_thread_cleans_temporary_audio(qapp):
    mock_engine = MagicMock()
    mock_engine.process_user_message.return_value = "شنیدم"

    # Create dummy temp WAV file
    temp_dir = tempfile.gettempdir()
    dummy_wav = os.path.join(temp_dir, "test_nexa_utterance_9999.wav")
    with open(dummy_wav, "wb") as f:
        f.write(b"RIFFdummydata")

    assert os.path.exists(dummy_wav)

    worker = AgentWorkerThread(mock_engine, "پیام صوتی", audio_path=dummy_wav)
    worker.run()

    # The temporary audio file MUST be cleaned up automatically
    assert not os.path.exists(dummy_wav)


def test_chat_window_creation_and_hands_free_flow(qapp, tmp_path):
    mock_engine = MagicMock()
    mock_engine.key_manager = MagicMock()
    mock_engine.memory_manager = MagicMock()
    mock_engine.persona_manager = MagicMock()
    mock_engine.learning_engine = MagicMock()

    mock_tts = MagicMock()
    mock_tts.enabled = False

    chat_win = ChatWindow(mock_engine, mock_tts)
    assert chat_win is not None
    assert chat_win.send_btn.isEnabled()

    # Simulate hands-free audio arrival
    dummy_audio = str(tmp_path / "voice.wav")
    with open(dummy_audio, "wb") as f:
        f.write(b"WAV_DATA")

    chat_win.hands_free_btn.setChecked(True)
    with patch.object(chat_win, "_on_send_clicked") as mock_send:
        chat_win._on_hands_free_speech_completed(dummy_audio)
        assert chat_win.current_attached_audio == dummy_audio
        mock_send.assert_called_once()

    # Test agent response handling
    chat_win._on_agent_response("پاسخ نهایی")
    assert chat_win.send_btn.isEnabled()
    badge_txt = chat_win.status_badge.text()
    assert ("مکالمه پیوسته" in badge_txt) or ("آماده" in badge_txt)


def test_chat_window_family_bar_and_switching(qapp):
    from agent.family.member import FamilyMember

    mock_engine = MagicMock()
    mock_fm = MagicMock()
    fake_member = FamilyMember({
        "id": "samyar",
        "name": "سامیار",
        "gender": "male",
        "role_title": "مهندس نرم‌افزار",
        "level": 5,
        "xp": 150,
        "specialties": ["پایتون", "سی‌شارپ"]
    })
    mock_fm.get_active_member.return_value = fake_member
    mock_fm.switch_member.return_value = fake_member
    mock_engine.family_manager = mock_fm

    mock_tts = MagicMock()
    mock_tts.enabled = False

    chat_win = ChatWindow(mock_engine, mock_tts)
    assert hasattr(chat_win, "family_bar")
    assert hasattr(chat_win, "family_buttons")
    assert len(chat_win.family_buttons) == 6
    assert "samyar" in chat_win.family_buttons
    assert "nexamehr" in chat_win.family_buttons

    # Click on samyar chip
    chat_win._on_family_chip_clicked("samyar")
    mock_fm.switch_member.assert_called_with("samyar")
    assert "سامیار" in chat_win.active_family_badge.text()
    assert "سطح 5" in chat_win.active_family_level.text()


def test_chat_window_alert_card_resilience(qapp):
    mock_engine = MagicMock()
    mock_tts = MagicMock()
    mock_tts.enabled = False
    chat_win = ChatWindow(mock_engine, mock_tts)

    # Both warning and critical severities must render safely without KeyError
    chat_win.add_alert_card("warning", "هشدار کاهش اعتبار")
    chat_win.add_alert_card("critical", "هشدار اتمام اعتبار")
    assert chat_win.messages_layout.count() >= 2


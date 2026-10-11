import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from agent.multi_ai import MultiAiCollaborator, PeerProvider
from agent.learning import LearningEngine
from agent.engine import AgentEngine


@pytest.fixture
def temp_multi_ai_files():
    temp_dir = tempfile.mkdtemp()
    settings_path = os.path.join(temp_dir, "peer_ai_settings.json")
    insights_path = os.path.join(temp_dir, "peer_insights.json")
    learnings_path = os.path.join(temp_dir, "learnings.json")
    yield settings_path, insights_path, learnings_path
    for p in [settings_path, insights_path, learnings_path]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


def test_multi_ai_collaborator_defaults_and_save(temp_multi_ai_files):
    settings_path, insights_path, _ = temp_multi_ai_files
    collab = MultiAiCollaborator(settings_path=settings_path, insights_path=insights_path)
    
    assert collab.active_provider == PeerProvider.OLLAMA.value or collab.active_provider == "ollama"
    assert "ollama" in collab.providers
    assert "openai" in collab.providers
    assert "claude" in collab.providers
    assert "deepseek" in collab.providers

    # Update provider config
    collab.configure_provider("openai", api_key="sk-mock-key-12345", model="gpt-4o")
    collab.set_active_provider("openai")
    
    # Reload from disk
    collab2 = MultiAiCollaborator(settings_path=settings_path, insights_path=insights_path)
    assert collab2.active_provider == "openai"
    assert collab2.providers["openai"]["api_key"] == "sk-mock-key-12345"
    assert collab2.providers["openai"]["model"] == "gpt-4o"


def test_consult_peer_ai_openai_mock(temp_multi_ai_files):
    settings_path, insights_path, _ = temp_multi_ai_files
    collab = MultiAiCollaborator(settings_path=settings_path, insights_path=insights_path)
    collab.configure_provider("openai", api_key="sk-mock-123", model="gpt-4o")

    mock_response_data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Peer AI analysis: The provided logic has a race condition in file writing."
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_response_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = collab.consult_peer_ai(
            prompt="Check this code for concurrency bugs",
            provider="openai"
        )
        assert res["success"] is True
        assert "race condition" in res["reply"]
        assert res["provider"] == "openai"


def test_consult_peer_ai_claude_mock(temp_multi_ai_files):
    settings_path, insights_path, _ = temp_multi_ai_files
    collab = MultiAiCollaborator(settings_path=settings_path, insights_path=insights_path)
    collab.configure_provider("claude", api_key="sk-ant-123", model="claude-3-5-sonnet")

    mock_response_data = {
        "content": [
            {
                "type": "text",
                "text": "Claude review: Consider using a semaphore instead of a mutex."
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_response_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = collab.consult_peer_ai(
            prompt="Improve concurrency",
            provider="claude"
        )
        assert res["success"] is True
        assert "semaphore" in res["reply"]


def test_peer_code_review_and_learning_distillation(temp_multi_ai_files):
    settings_path, insights_path, learnings_path = temp_multi_ai_files
    learning_engine = LearningEngine(storage_path=learnings_path)
    collab = MultiAiCollaborator(settings_path=settings_path, insights_path=insights_path, learning_engine=learning_engine)

    mock_review_data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": " ایراد پیدا شد: استفاده از متد باز کردن فایل بدون تعیین انکودینگ UTF-8 در ویندوز ممکن است خطای حروف فارسی ایجاد کند. پیشنهاد: همیشه از encoding='utf-8' استفاده کنید."
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_review_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        # 1. Peer code review
        rev = collab.peer_code_review(
            code="with open('file.txt', 'w') as f: f.write('سلام')",
            language="python",
            context="نوشتن پیام فارسی در فایل",
            provider="openai"
        )
        assert rev["success"] is True
        assert "UTF-8" in rev["review"]

        # 2. Learn from peer
        learn_res = collab.learn_from_peer_ai(
            topic="کدگذاری فایل‌های فارسی در ویندوز",
            peer_advice="همیشه در open() پارامتر encoding='utf-8' را تنظیم کن تا کاراکترها خراب نشوند.",
            category="file_io"
        )
        assert learn_res["success"] is True

        # Verify rule persisted into LearningEngine
        rules = learning_engine.query_learnings("کدگذاری فایل‌های فارسی")
        assert len(rules) == 1
        assert "encoding='utf-8'" in rules[0]["rule"]


def test_run_self_improvement(temp_multi_ai_files):
    settings_path, insights_path, learnings_path = temp_multi_ai_files
    learning_engine = LearningEngine(storage_path=learnings_path)
    collab = MultiAiCollaborator(settings_path=settings_path, insights_path=insights_path, learning_engine=learning_engine)

    mock_critique_data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "پیشنهاد بهبود: برای جلوگیری از زمان‌بندی بیش از حد، همیشه قبل از اجرای دستورات سنگین، حافظه رم را چک کن."
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_critique_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = collab.run_self_improvement(focus_area="مدیریت منابع و بهینه‌سازی سرعت", provider="openai")
        assert res["success"] is True
        assert "حافظه رم" in res["improvement_plan"]
        
        # Verify saved in insights history
        insights = collab.get_insights_history()
        assert len(insights) >= 1
        assert insights[0]["focus_area"] == "مدیریت منابع و بهینه‌سازی سرعت"


def test_agent_engine_registers_multi_ai_tools():
    engine = AgentEngine(api_key="AIzaSyMockKeyForMultiAiTest")
    assert "consult_peer_ai" in engine.tools_map
    assert "review_code_with_peer" in engine.tools_map
    assert "learn_from_peer_ai" in engine.tools_map
    assert "run_self_improvement" in engine.tools_map


def test_settings_window_multi_ai_tab(qapp, tmp_path):
    from agent.key_manager import KeyManager
    from agent.memory import MemoryManager
    from agent.persona import PersonaManager
    from ui.settings_window import SettingsWindow

    km = KeyManager(config_path=str(tmp_path / "keys.json"))
    mm = MemoryManager(storage_path=str(tmp_path / "memory.json"))
    pm = PersonaManager(config_path=str(tmp_path / "persona.json"))
    le = LearningEngine(storage_path=str(tmp_path / "learnings.json"))
    collab = MultiAiCollaborator(
        settings_path=str(tmp_path / "peer_settings.json"),
        insights_path=str(tmp_path / "peer_insights.json"),
        learning_engine=le
    )

    sw = SettingsWindow(
        key_manager=km,
        memory_manager=mm,
        persona_manager=pm,
        learning_engine=le,
        multi_ai=collab
    )

    assert hasattr(sw, "tab_multi_ai")
    assert sw.tabs.count() == 6
    assert "🌐" in sw.tabs.tabText(5)

    # Change combo to OpenAI
    idx = sw.peer_prov_combo.findData("openai")
    sw.peer_prov_combo.setCurrentIndex(idx)
    sw.peer_api_key.setText("sk-live-test-key")
    sw.peer_model_name.setText("gpt-4o")

    # Save
    sw._save_peer_provider_config()
    assert collab.providers["openai"]["api_key"] == "sk-live-test-key"
    assert collab.providers["openai"]["model"] == "gpt-4o"

    # Set Active
    sw._set_active_peer_provider()
    assert collab.active_provider == "openai"

    # Test distill button with text in result display
    sw.peer_result_display.setText("همیشه از ساختار try-finally برای آزادسازی منابع استفاده کن.")
    sw._distill_displayed_advice()
    learned = le.query_learnings("try-finally")
    assert len(learned) == 1
    assert "try-finally" in learned[0]["rule"]


def test_consult_peer_ai_ollama_mock(temp_multi_ai_files):
    settings_path, insights_path, _ = temp_multi_ai_files
    collab = MultiAiCollaborator(settings_path=settings_path, insights_path=insights_path)
    collab.configure_provider("ollama", model="llama3", base_url="http://localhost:11434")

    mock_ollama_data = {
        "message": {
            "role": "assistant",
            "content": "سلام! من مدل آفلاین Llama 3 هستم و بدون نیاز به اینترنت اجرا می‌شوم."
        }
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_ollama_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = collab.consult_peer_ai(
            prompt="آیا آفلاین کار می‌کنی؟",
            provider="ollama"
        )
        assert res["success"] is True
        assert "Llama 3" in res["reply"]
        assert res["provider"] == "ollama"


def test_consult_peer_ai_lm_studio_mock(temp_multi_ai_files):
    settings_path, insights_path, _ = temp_multi_ai_files
    collab = MultiAiCollaborator(settings_path=settings_path, insights_path=insights_path)
    collab.configure_provider("lm_studio", model="qwen2.5-7b", base_url="http://localhost:1234/v1")

    mock_lmstudio_data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "پاسخ از سرور محلی LM Studio با مدل Qwen."
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_lmstudio_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = collab.consult_peer_ai(
            prompt="وضعیت محلی را بگو",
            provider="lm_studio"
        )
        assert res["success"] is True
        assert "LM Studio" in res["reply"]
        assert res["provider"] == "lm_studio"


def test_agent_engine_offline_fallback(temp_multi_ai_files):
    settings_path, insights_path, learnings_path = temp_multi_ai_files
    le = LearningEngine(storage_path=learnings_path)
    collab = MultiAiCollaborator(settings_path=settings_path, insights_path=insights_path, learning_engine=le)
    collab.set_active_provider("ollama")

    engine = AgentEngine(api_key="mock-key-123", learning_engine=le, multi_ai=collab)

    # Mock chat.send_message to simulate Internet failure / Network down
    engine.chat = MagicMock()
    engine.chat.send_message.side_effect = ConnectionError("Could not reach Google Gemini servers (Offline)")

    # Mock Ollama local response
    mock_offline_res = {
        "success": True,
        "provider": "ollama",
        "model": "llama3",
        "reply": "این یک پاسخ کاملاً آفلاین از سرور محلی اولاما روی سخت‌افزار سیستم شماست."
    }

    with patch.object(collab, "consult_peer_ai", return_value=mock_offline_res) as mock_consult:
        reply = engine.process_user_message("یک جوک بگو")
        assert "پاسخ آفلاین توسط هوش مصنوعی محلی" in reply
        assert "اولاما" in reply
        assert "پاسخ کاملاً آفلاین" in reply
        mock_consult.assert_called_once()



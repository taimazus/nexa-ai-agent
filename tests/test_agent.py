import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.engine import AgentEngine


def test_agent_engine_init():
    engine = AgentEngine(api_key="TEST_FAKE_KEY")
    assert engine.model_name == "gemini-2.5-flash"
    assert engine.tools is not None


def test_dispatch_tool_call_valid():
    engine = AgentEngine(api_key="TEST_FAKE_KEY")
    result = engine.dispatch_tool("execute_powershell", {"command": "Write-Output 'Testing dispatch'"})
    assert result["success"] is True
    assert "Testing dispatch" in result["stdout"]


def test_dispatch_tool_call_unknown():
    engine = AgentEngine(api_key="TEST_FAKE_KEY")
    result = engine.dispatch_tool("unknown_fake_tool", {})
    assert result["success"] is False
    assert "Unknown tool" in result["error"]


def test_dispatch_memory_tools(tmp_path):
    mem_file = str(tmp_path / "mem.json")
    from agent.memory import MemoryManager
    mm = MemoryManager(storage_path=mem_file)
    engine = AgentEngine(api_key="TEST_FAKE_KEY", memory_manager=mm)

    res = engine.dispatch_tool("remember_fact", {"key": "name", "value": "Taimaz", "category": "user"})
    assert res["success"] is True

    recall_res = engine.dispatch_tool("recall_facts", {"query": "Taimaz"})
    assert len(recall_res) >= 1
    assert recall_res[0]["value"] == "Taimaz"


def test_dispatch_capture_webcam():
    engine = AgentEngine(api_key="TEST_FAKE_KEY")
    res = engine.dispatch_tool("capture_webcam", {"camera_index": 999})
    assert isinstance(res, dict)
    assert res["success"] is False
    assert "error" in res


def test_process_user_message_with_audio_and_mock_client(tmp_path):
    dummy_wav = str(tmp_path / "voice_test.wav")
    with open(dummy_wav, "wb") as f:
        f.write(b"RIFF dummy sound data")

    engine = AgentEngine(api_key="TEST_FAKE_KEY")
    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "شنیدم که گفتید سلام!"
    mock_chat.send_message.return_value = mock_response
    engine.chat = mock_chat

    reply = engine.process_user_message(message="متن صوتی", audio_path=dummy_wav)
    assert reply == "شنیدم که گفتید سلام!"
    assert mock_chat.send_message.called
    assert len(engine.conversation_history) == 1


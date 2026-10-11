import os
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.memory import MemoryManager


def test_memory_remember_and_recall(tmp_path):
    mem_file = str(tmp_path / "memory.json")
    mm = MemoryManager(storage_path=mem_file)

    res = mm.remember_fact("user_name", "علی", category="profile")
    assert res["success"] is True

    facts = mm.recall_facts("علی")
    assert len(facts) >= 1
    assert facts[0]["key"] == "user_name"
    assert facts[0]["value"] == "علی"


def test_memory_forget(tmp_path):
    mem_file = str(tmp_path / "memory.json")
    mm = MemoryManager(storage_path=mem_file)
    mm.remember_fact("favorite_editor", "VS Code")
    assert len(mm.recall_facts()) == 1

    forget_res = mm.forget_fact("favorite_editor")
    assert forget_res["success"] is True
    assert len(mm.recall_facts()) == 0


def test_memory_system_prompt_context(tmp_path):
    mem_file = str(tmp_path / "memory.json")
    mm = MemoryManager(storage_path=mem_file)
    mm.remember_fact("project_goal", "ساخت ربات دسکتاپ نئونی")

    prompt_context = mm.get_prompt_context()
    assert "project_goal" in prompt_context
    assert "ساخت ربات دسکتاپ نئونی" in prompt_context


def test_memory_persistence(tmp_path):
    mem_file = str(tmp_path / "memory.json")
    mm1 = MemoryManager(storage_path=mem_file)
    mm1.remember_fact("api_preference", "gemini-2.5-flash")

    mm2 = MemoryManager(storage_path=mem_file)
    recalled = mm2.recall_facts("api_preference")
    assert len(recalled) == 1
    assert recalled[0]["value"] == "gemini-2.5-flash"

import os
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.learning import LearningEngine


def test_learning_record_and_query(tmp_path):
    learn_file = str(tmp_path / "learnings.json")
    le = LearningEngine(storage_path=learn_file)

    res = le.record_learning(
        trigger="PowerShell path with spaces",
        corrective_rule="همیشه مسیرهای ویندوزی دارای فاصله را داخل کوتیشن قرار بده.",
        category="powershell"
    )
    assert res["success"] is True

    rules = le.query_learnings("spaces")
    assert len(rules) == 1
    assert "کوتیشن" in rules[0]["rule"]


def test_learning_prompt_injection(tmp_path):
    learn_file = str(tmp_path / "learnings.json")
    le = LearningEngine(storage_path=learn_file)
    le.record_learning(
        trigger="Import error in script",
        corrective_rule="قبل از ایمپورت، موجودیت پکیج را چک کن یا با try/except هندل کن.",
        category="python"
    )

    injection = le.get_prompt_injection()
    assert "قوانین و درس‌های آموخته‌شده" in injection
    assert "ایمپورت" in injection


def test_learning_clear(tmp_path):
    learn_file = str(tmp_path / "learnings.json")
    le = LearningEngine(storage_path=learn_file)
    le.record_learning("test", "rule")
    assert len(le.query_learnings()) == 1

    le.clear_learnings()
    assert len(le.query_learnings()) == 0

import os
import sys
import json
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.key_manager import KeyManager


def test_key_manager_initialization(tmp_path):
    config_file = str(tmp_path / "settings.json")
    km = KeyManager(config_path=config_file, default_key="KEY_DEFAULT")
    assert len(km.get_keys()) == 1
    assert km.get_active_key() == "KEY_DEFAULT"


def test_key_manager_add_and_remove(tmp_path):
    config_file = str(tmp_path / "settings.json")
    km = KeyManager(config_path=config_file)
    km.add_key("KEY_1")
    km.add_key("KEY_2")
    assert len(km.get_keys()) == 2
    assert km.get_active_key() == "KEY_1"

    km.remove_key("KEY_1")
    assert len(km.get_keys()) == 1
    assert km.get_active_key() == "KEY_2"


def test_key_manager_rotation_on_failure(tmp_path):
    config_file = str(tmp_path / "settings.json")
    km = KeyManager(config_path=config_file)
    km.add_key("KEY_1")
    km.add_key("KEY_2")
    km.add_key("KEY_3")

    first_key = km.get_active_key()
    assert first_key == "KEY_1"

    # Mark current key as failed (quota exceeded)
    next_key = km.mark_current_failed(reason="429 Quota Exceeded")
    assert next_key == "KEY_2"
    assert km.get_active_key() == "KEY_2"

    # Rotation again
    third_key = km.mark_current_failed(reason="ResourceExhausted")
    assert third_key == "KEY_3"
    assert km.get_active_key() == "KEY_3"


def test_key_manager_persistence(tmp_path):
    config_file = str(tmp_path / "settings.json")
    km1 = KeyManager(config_path=config_file)
    km1.add_key("PERSISTENT_KEY")

    km2 = KeyManager(config_path=config_file)
    assert "PERSISTENT_KEY" in [k["key"] for k in km2.get_keys()]


def test_key_manager_pool_health_and_quota_warning(tmp_path):
    config_file = str(tmp_path / "settings.json")
    km = KeyManager(config_path=config_file)
    km.add_key("KEY_A", label="کلید اول")
    km.add_key("KEY_B", label="کلید دوم")

    health = km.get_pool_health()
    assert health["total_keys"] == 2
    assert health["active_keys"] == 2
    assert health["is_low_quota"] is False
    assert health["is_depleted"] is False

    # One key fails due to quota limit
    km.mark_current_failed(reason="429 ResourceExhausted")
    health2 = km.get_pool_health()
    assert health2["active_keys"] == 1
    assert health2["exhausted_keys"] == 1
    assert health2["is_low_quota"] is True
    assert "هشدار" in health2["alert_message"]

    # Second key also fails
    km.mark_current_failed(reason="Quota Exceeded")
    health3 = km.get_pool_health()
    assert health3["is_depleted"] is True
    assert "بحرانی" in health3["alert_message"]

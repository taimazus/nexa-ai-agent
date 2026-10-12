import os
import sys
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.tools import (
    execute_powershell,
    execute_python,
    file_operations,
    system_diagnostics,
    fetch_url,
    capture_webcam
)


def test_execute_powershell_echo():
    result = execute_powershell("Write-Output 'Hello from PowerShell'")
    assert result["success"] is True
    assert "Hello from PowerShell" in result["stdout"]
    assert result["returncode"] == 0


def test_execute_powershell_unicode_persian():
    result = execute_powershell("Write-Output 'سلام دنیا'")
    assert result["success"] is True
    assert "سلام دنیا" in result["stdout"]


def test_execute_python_code():
    code = "import math\nprint(f'PI={math.pi:.2f}')"
    result = execute_python(code)
    assert result["success"] is True
    assert "PI=3.14" in result["output"]


def test_file_operations_write_and_read(tmp_path):
    test_file = str(tmp_path / "test_persian.txt")
    write_res = file_operations("write", test_file, "متن تستی با انکودینگ UTF-8")
    assert write_res["success"] is True

    read_res = file_operations("read", test_file)
    assert read_res["success"] is True
    assert read_res["content"] == "متن تستی با انکودینگ UTF-8"


def test_system_diagnostics_returns_expected_keys():
    res = system_diagnostics()
    assert res["success"] is True
    assert "os" in res["data"]
    assert "cpu_cores" in res["data"]
    assert "memory_mb" in res["data"]


def test_fetch_url_invalid():
    res = fetch_url("https://invalid-domain-that-does-not-exist-xyz.com")
    assert res["success"] is False
    assert "error" in res


def test_capture_webcam_invalid_index():
    res = capture_webcam(camera_index=999)
    assert res["success"] is False
    assert "error" in res


def test_capture_webcam_runs_or_reports(tmp_path):
    target_img = str(tmp_path / "webcam_snap.jpg")
    res = capture_webcam(camera_index=0, save_path=target_img)
    assert isinstance(res, dict)
    assert "success" in res
    if res["success"]:
        assert os.path.exists(target_img)
        assert res["width"] > 0
        assert res["height"] > 0
    else:
        assert "error" in res


def test_file_operations_safe_deletion(tmp_path):
    # Safe deletion of disposable file
    temp_file = tmp_path / "temp_delete_me.txt"
    temp_file.write_text("حذف تستی", encoding="utf-8")
    del_res = file_operations("delete", str(temp_file))
    assert del_res["success"] is True
    assert not temp_file.exists()


def test_file_operations_blocks_protected_deletion():
    # Attempting to delete system drive or root paths must be blocked
    res_drive = file_operations("delete", "C:\\")
    assert res_drive["success"] is False
    assert "مسدود" in res_drive["error"] or "حساس" in res_drive["error"]

    res_win = file_operations("delete", "C:\\Windows")
    assert res_win["success"] is False
    assert "مسدود" in res_win["error"] or "حساس" in res_win["error"]


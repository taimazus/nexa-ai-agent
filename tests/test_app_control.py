import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from agent.family.app_controller import AppController
from agent.engine import AgentEngine


@pytest.fixture
def temp_workflows_file(tmp_path):
    return tmp_path / "test_app_workflows.json"


@pytest.fixture
def app_controller(temp_workflows_file):
    return AppController(workflows_path=temp_workflows_file)


def test_app_controller_defaults(app_controller, temp_workflows_file):
    """Test that default workflows are created and saved on first run."""
    assert temp_workflows_file.exists()
    workflows = app_controller.list_workflows()
    assert len(workflows) >= 3
    names = [w["name"] for w in workflows]
    assert "notepad_quick_note" in names
    assert "excel_new_spreadsheet" in names
    assert "save_current_file" in names


def test_learn_and_list_workflow(app_controller):
    """Test learning a custom app workflow and filtering by app name."""
    steps = [
        {"action": "launch", "target": "photoshop"},
        {"action": "wait", "ms": 100},
        {"action": "hotkey", "key": "ctrl+n"},
        {"action": "type", "text": "{project_name}"}
    ]
    res = app_controller.learn_workflow(
        name="photoshop_new_canvas",
        app_name="Photoshop",
        description="ایجاد بوم جدید در فتوشاپ",
        steps=steps,
        trigger_phrases=["بوم جدید باز کن"]
    )
    assert res["success"] is True
    assert res["workflow_name"] == "photoshop_new_canvas"
    assert res["steps_count"] == 4

    # List filtered
    ps_workflows = app_controller.list_workflows(app_name="photoshop")
    assert len(ps_workflows) == 1
    assert ps_workflows[0]["name"] == "photoshop_new_canvas"

    # List non-existent filter
    none_workflows = app_controller.list_workflows(app_name="nonexistent")
    assert len(none_workflows) == 0


def test_execute_workflow_success_and_param_substitution(app_controller):
    """Test executing a workflow with dynamic parameter substitution."""
    steps = [
        {"action": "launch", "target": "notepad"},
        {"action": "wait", "ms": 10},
        {"action": "type", "text": "Hello {user_name}! File: {doc_title}"},
        {"action": "hotkey", "key": "ctrl+s"}
    ]
    app_controller.learn_workflow(
        name="test_substitution",
        app_name="notepad",
        description="تست جایگزینی متغیرها",
        steps=steps
    )

    with patch("agent.tools.launch_or_focus_app") as mock_launch, \
         patch("agent.tools.send_app_keys") as mock_keys:
        
        exec_res = app_controller.execute_workflow(
            workflow_name="test_substitution",
            parameters={"user_name": "سهند", "doc_title": "گزارش مالی"}
        )

        assert exec_res["success"] is True
        assert exec_res["total_steps"] == 4
        mock_launch.assert_called_with("notepad")
        
        # Verify substitution happened in type step
        mock_keys.assert_any_call(keys_or_text="Hello سهند! File: گزارش مالی")
        mock_keys.assert_any_call(hotkey="ctrl+s")


def test_execute_workflow_not_found(app_controller):
    """Test error handling when workflow does not exist."""
    res = app_controller.execute_workflow("ghost_workflow_that_does_not_exist")
    assert res["success"] is False
    assert "یافت نشد" in res["error"]


def test_inspect_app_ui_parsing(app_controller):
    """Test PowerShell output parsing when inspecting UI elements."""
    mock_ps_json = json.dumps([
        {
            "Name": "File",
            "ControlType": "MenuItem",
            "AutomationId": "Item 1",
            "BoundingRectangle": "0,0,50,20",
            "IsEnabled": True
        },
        {
            "Name": "Save",
            "ControlType": "Button",
            "AutomationId": "BtnSave",
            "BoundingRectangle": "100,50,80,30",
            "IsEnabled": True
        }
    ])

    with patch.object(app_controller, "_run_powershell", return_value={"success": True, "stdout": mock_ps_json, "stderr": ""}):
        res = app_controller.inspect_app_ui(window_title="Notepad")
        assert res["success"] is True
        assert res["total_elements"] == 2
        assert res["elements"][0]["name"] == "File"
        assert res["elements"][1]["automation_id"] == "BtnSave"


def test_invoke_app_element_success(app_controller):
    """Test invoking a button in an application window."""
    with patch.object(app_controller, "_run_powershell", return_value={"success": True, "stdout": "INVOKED\n", "stderr": ""}):
        res = app_controller.invoke_app_element(window_title="Calculator", element_name="Seven")
        assert res["success"] is True
        assert "با موفقیت کلیک/اجرا شد" in res["message"]


def test_engine_registers_app_controller_tools():
    """Verify that AgentEngine registers all AppController tools in tools_map and callable_tools."""
    with patch("google.genai.Client"):
        engine = AgentEngine(api_key="dummy_key_for_test")
        
        # Verify tools_map
        for tool_name in ["inspect_app_ui", "invoke_app_element", "learn_app_workflow", "list_app_workflows", "execute_app_workflow"]:
            assert tool_name in engine.tools_map, f"{tool_name} must be in engine.tools_map"
        
        # Verify callable_tools list
        callable_names = [f.__name__ for f in engine.callable_tools]
        assert "wrapped_inspect_ui" in callable_names
        assert "wrapped_invoke_element" in callable_names
        assert "wrapped_learn_workflow" in callable_names
        assert "wrapped_list_workflows" in callable_names
        assert "wrapped_execute_workflow" in callable_names

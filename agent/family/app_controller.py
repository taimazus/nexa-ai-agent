import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("NexA.Family.AppController")

WORKFLOWS_PATH = Path(__file__).parent.parent.parent / "data" / "app_workflows.json"


class AppController:
    """
    Universal Desktop Application Controller and Autonomous Learning Engine.
    Enables NexA (specifically Artin and NexaMehr) to:
    1. Inspect interactive UI elements (Buttons, Text boxes, Menus, Tabs) of ANY Windows software.
    2. Click or invoke elements by human-readable names or Automation IDs.
    3. Learn complete multi-step app workflows by name and trigger phrases.
    4. Execute learned workflows autonomously with dynamic parameter injection.
    """

    def __init__(self, workflows_path: Optional[Path] = None):
        self.workflows_path = workflows_path or WORKFLOWS_PATH
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self._load_workflows()

    def _load_workflows(self):
        """Loads learned app workflows from JSON disk."""
        try:
            if self.workflows_path.exists():
                with open(self.workflows_path, "r", encoding="utf-8") as f:
                    self.workflows = json.load(f)
                logger.info(f"Loaded {len(self.workflows)} learned application workflows.")
            else:
                self._init_default_workflows()
        except Exception as exc:
            logger.error(f"Error loading app workflows: {exc}", exc_info=True)
            self._init_default_workflows()

    def _init_default_workflows(self):
        """Initializes built-in foundational workflows for everyday apps."""
        self.workflows = {
            "notepad_quick_note": {
                "name": "notepad_quick_note",
                "app_name": "notepad",
                "description": "باز کردن نوت‌پد و یادداشت‌برداری متن",
                "trigger_phrases": ["یک نوت در نوت پد بنویس", "نوت پد را باز کن و بنویس"],
                "steps": [
                    {"action": "launch", "target": "notepad"},
                    {"action": "wait", "ms": 600},
                    {"action": "type", "text": "{text}"}
                ]
            },
            "excel_new_spreadsheet": {
                "name": "excel_new_spreadsheet",
                "app_name": "excel",
                "description": "ایجاد فایل اکسل جدید و آماده‌سازی جدول",
                "trigger_phrases": ["اکسل را باز کن و جدول جدید بساز"],
                "steps": [
                    {"action": "launch", "target": "excel"},
                    {"action": "wait", "ms": 1200},
                    {"action": "hotkey", "key": "ctrl+n"}
                ]
            },
            "save_current_file": {
                "name": "save_current_file",
                "app_name": "",
                "description": "ذخیره فایل در برنامه فعال جاری با میانبر کلیدی",
                "trigger_phrases": ["این فایل را ذخیره کن", "سیو کن"],
                "steps": [
                    {"action": "hotkey", "key": "ctrl+s"}
                ]
            }
        }
        self.save_workflows()

    def save_workflows(self) -> bool:
        """Persists learned workflows to disk."""
        try:
            self.workflows_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.workflows_path, "w", encoding="utf-8") as f:
                json.dump(self.workflows, f, ensure_ascii=False, indent=2)
            logger.info("Saved application workflows successfully.")
            return True
        except Exception as exc:
            logger.error(f"Failed to save app workflows: {exc}", exc_info=True)
            return False

    def _run_powershell(self, script: str) -> Dict[str, Any]:
        """Executes a PowerShell script via standard input with UTF-8 encoding."""
        full_script = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
{script}
"""
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", "-"],
                input=full_script,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=12
            )
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            return {
                "success": proc.returncode == 0,
                "stdout": stdout,
                "stderr": stderr
            }
        except subprocess.TimeoutExpired:
            logger.warning("PowerShell command timed out after 12s.")
            return {"success": False, "stdout": "", "stderr": "Command timed out."}
        except Exception as exc:
            logger.error(f"Error running PowerShell: {exc}")
            return {"success": False, "stdout": "", "stderr": str(exc)}

    def inspect_app_ui(
        self,
        app_name_or_title: str = "",
        window_title: Optional[str] = None,
        control_type: Optional[str] = None,
        max_elements: int = 25
    ) -> Dict[str, Any]:
        """
        Scans and discovers interactive UI controls (buttons, text boxes, menus, tabs)
        inside the window of ANY Windows software using Windows UI Automation.
        """
        target = (window_title or app_name_or_title).lower()
        logger.info(f"Inspecting UI elements for app: {target}")
        ps_code = f"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$target = "{target}".ToLower()
$root = [System.Windows.Automation.AutomationElement]::RootElement

$foundWnd = $null
$windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)

foreach ($w in $windows) {{
    $t = $w.Current.Name.ToLower()
    $p = (Get-Process -Id $w.Current.ProcessId -ErrorAction SilentlyContinue).ProcessName.ToLower()
    if ($t.Contains($target) -or $p.Contains($target)) {{
        $foundWnd = $w
        break
    }}
}}

if (-not $foundWnd) {{
    Write-Output "WINDOW_NOT_FOUND"
    exit 0
}}

# Find interactive controls: Buttons, Edit, MenuItem, CheckBox, TabItem, List
$types = @(
    [System.Windows.Automation.ControlType]::Button,
    [System.Windows.Automation.ControlType]::Edit,
    [System.Windows.Automation.ControlType]::MenuItem,
    [System.Windows.Automation.ControlType]::CheckBox,
    [System.Windows.Automation.ControlType]::TabItem
)

$condList = New-Object System.Collections.Generic.List[System.Windows.Automation.Condition]
foreach ($ct in $types) {{
    $condList.Add((New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, $ct)))
}}
$orCond = New-Object System.Windows.Automation.OrCondition($condList.ToArray())

$elements = $foundWnd.FindAll([System.Windows.Automation.TreeScope]::Descendants, $orCond)

$resList = @()
$count = 0
foreach ($el in $elements) {{
    if ($count -ge {max_elements}) {{ break }}
    $name = $el.Current.Name
    $cType = $el.Current.ControlType.ProgrammaticName.Replace("ControlType.", "")
    $autoId = $el.Current.AutomationId
    $rect = $el.Current.BoundingRectangle

    if ($name -or $autoId) {{
        $resList += [PSCustomObject]@{{
            Name = $name
            Type = $cType
            Id = $autoId
            X = [int]$rect.X
            Y = [int]$rect.Y
            Width = [int]$rect.Width
            Height = [int]$rect.Height
        }}
        $count++
    }}
}}

$outJson = [PSCustomObject]@{{
    WindowTitle = $foundWnd.Current.Name
    ProcessId = $foundWnd.Current.ProcessId
    Elements = $resList
}} | ConvertTo-Json -Depth 3

Write-Output $outJson
"""
        res = self._run_powershell(ps_code)
        if not res["success"] or not res["stdout"]:
            return {
                "success": False,
                "error": res.get("stderr") or "نتوانست پنجره را بررسی کند."
            }

        stdout = res["stdout"]
        if "WINDOW_NOT_FOUND" in stdout:
            return {
                "success": False,
                "error": f"پنجره‌ای با نام یا فرآیند '{app_name_or_title}' در حال حاضر باز نیست."
            }

        try:
            data = json.loads(stdout)
            if isinstance(data, list):
                elements = data
                window_name = ""
            elif isinstance(data, dict):
                elements = data.get("Elements", [])
                window_name = data.get("WindowTitle", "")
                if isinstance(elements, dict):
                    elements = [elements]
            else:
                elements = []
                window_name = ""

            # Normalize keys to lowercase for clean python consumption
            normalized = []
            for el in elements:
                if isinstance(el, dict):
                    normalized.append({
                        "name": el.get("Name") or el.get("name", ""),
                        "control_type": el.get("ControlType") or el.get("control_type", ""),
                        "automation_id": el.get("AutomationId") or el.get("automation_id", ""),
                        "rect": el.get("Rect") or el.get("rect") or el.get("BoundingRectangle"),
                        "is_enabled": el.get("IsEnabled") if "IsEnabled" in el else el.get("is_enabled", True)
                    })

            return {
                "success": True,
                "app": target,
                "window_title": window_name,
                "total_elements": len(normalized),
                "controls_count": len(normalized),
                "elements": normalized,
                "controls": normalized
            }
        except Exception as exc:
            logger.warning(f"Error parsing UI elements JSON: {exc}")
            return {
                "success": False,
                "error": f"خطا در تحلیل ساختار پنجره: {str(exc)}",
                "raw": stdout[:300]
            }

    def invoke_app_element(
        self,
        app_name_or_title: str = "",
        element_name_or_id: str = "",
        window_title: Optional[str] = None,
        element_name: Optional[str] = None,
        automation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Locates an element by Name or AutomationId in the specified application
        and clicks/invokes it natively.
        """
        target_app = window_title or app_name_or_title
        target_el = element_name or automation_id or element_name_or_id
        logger.info(f"Invoking element '{target_el}' in '{target_app}'")
        ps_code = f"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$targetApp = "{target_app}".ToLower()
$targetEl = "{target_el}".ToLower()

$root = [System.Windows.Automation.AutomationElement]::RootElement
$windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)

$foundWnd = $null
foreach ($w in $windows) {{
    $t = $w.Current.Name.ToLower()
    $p = (Get-Process -Id $w.Current.ProcessId -ErrorAction SilentlyContinue).ProcessName.ToLower()
    if ($t.Contains($targetApp) -or $p.Contains($targetApp)) {{
        $foundWnd = $w
        break
    }}
}}

if (-not $foundWnd) {{
    Write-Output "WINDOW_NOT_FOUND"
    exit 0
}}

$allElements = $foundWnd.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)

$invoked = $false
foreach ($el in $allElements) {{
    $name = $el.Current.Name.ToLower()
    $aid = $el.Current.AutomationId.ToLower()
    if ($name -eq $targetEl -or $aid -eq $targetEl -or ($name.Contains($targetEl) -and $targetEl.Length -ge 3)) {{
        # Try InvokePattern
        $pat = $null
        if ($el.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$pat)) {{
            $pat.Invoke()
            $invoked = $true
            Write-Output "INVOKED"
            break
        }}
    }}
}}

if (-not $invoked) {{
    Write-Output "ELEMENT_NOT_INVOKED"
}}
"""
        res = self._run_powershell(ps_code)
        stdout = res.get("stdout", "")

        if "WINDOW_NOT_FOUND" in stdout:
            return {"success": False, "error": f"برنامه '{app_name_or_title}' پیدا نشد."}
        if "INVOKED" in stdout:
            return {
                "success": True,
                "app": app_name_or_title,
                "element": element_name_or_id,
                "message": f"المان «{element_name_or_id}» در پنجره با موفقیت کلیک/اجرا شد."
            }

        return {
            "success": False,
            "error": f"المان «{element_name_or_id}» یافت نشد یا الگوی اجرای کلیک نداشت."
        }

    def learn_workflow(
        self,
        name: str = "",
        app_name: str = "",
        description: str = "",
        steps: Optional[List[Dict[str, Any]]] = None,
        trigger_phrases: Optional[List[str]] = None,
        workflow_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Learns and persists a new multi-step automation workflow for ANY desktop software.
        """
        actual_name = workflow_name or name or "unnamed_workflow"
        actual_steps = steps or []
        clean_name = actual_name.strip().lower().replace(" ", "_")
        workflow_obj = {
            "name": clean_name,
            "app_name": app_name.strip(),
            "description": description.strip(),
            "trigger_phrases": trigger_phrases or [clean_name],
            "steps": actual_steps,
            "learned_at": time.time()
        }
        self.workflows[clean_name] = workflow_obj
        self.save_workflows()
        logger.info(f"Learned new workflow '{clean_name}' for app '{app_name}' with {len(actual_steps)} steps.")
        return {
            "success": True,
            "workflow_name": clean_name,
            "steps_count": len(actual_steps),
            "message": f"فرآیند خودکار «{clean_name}» برای نرم‌افزار «{app_name}» با موفقیت آموخته و ثبت شد."
        }

    def list_workflows(self, app_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all currently learned software automation workflows."""
        results = []
        for w in self.workflows.values():
            if app_name and app_name.lower() not in w.get("app_name", "").lower():
                continue
            results.append({
                "name": w["name"],
                "app_name": w["app_name"],
                "description": w["description"],
                "steps_count": len(w.get("steps", [])),
                "trigger_phrases": w.get("trigger_phrases", [])
            })
        return results

    def execute_workflow(
        self,
        workflow_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a learned software workflow step-by-step with dynamic parameter substitution.
        """
        from agent import tools

        clean_name = workflow_name.strip().lower().replace(" ", "_")
        workflow = self.workflows.get(clean_name)

        if not workflow:
            # Fuzzy search
            for k, v in self.workflows.items():
                if clean_name in k or any(clean_name in p for p in v.get("trigger_phrases", [])):
                    workflow = v
                    break

        if not workflow:
            return {
                "success": False,
                "error": f"فرآیند آموخته‌شده با نام '{workflow_name}' یافت نشد."
            }

        params = parameters or {}
        steps = workflow.get("steps", [])
        executed_steps = []

        logger.info(f"Executing workflow '{workflow['name']}' with {len(steps)} steps...")

        for idx, step in enumerate(steps, 1):
            action = step.get("action", "").lower()
            try:
                if action == "launch":
                    target = step.get("target") or workflow.get("app_name")
                    tools.launch_or_focus_app(target)
                    executed_steps.append(f"مرحله {idx}: باز کردن {target}")

                elif action == "focus":
                    target = step.get("target") or workflow.get("app_name")
                    tools.launch_or_focus_app(target)
                    executed_steps.append(f"مرحله {idx}: فوکوس روی پنجره {target}")

                elif action == "type":
                    raw_text = step.get("text", "")
                    # Substitute parameters like {text}, {filename}
                    for p_key, p_val in params.items():
                        raw_text = raw_text.replace(f"{{{p_key}}}", str(p_val))
                    tools.send_app_keys(keys_or_text=raw_text)
                    executed_steps.append(f"مرحله {idx}: تایپ متن")

                elif action == "hotkey":
                    key = step.get("key", "")
                    tools.send_app_keys(hotkey=key)
                    executed_steps.append(f"مرحله {idx}: فشردن کلید {key}")

                elif action == "click_element":
                    el_name = step.get("name", "")
                    app = step.get("app") or workflow.get("app_name")
                    self.invoke_app_element(app, el_name)
                    executed_steps.append(f"مرحله {idx}: کلیک روی المان {el_name}")

                elif action == "click":
                    x = step.get("x")
                    y = step.get("y")
                    tools.click_screen(x=x, y=y)
                    executed_steps.append(f"مرحله {idx}: کلیک ماوس در مختصات ({x}, {y})")

                elif action == "wait":
                    ms = step.get("ms", 500)
                    time.sleep(ms / 1000.0)
                    executed_steps.append(f"مرحله {idx}: انتظار {ms} میلی‌ثانیه")

            except Exception as step_exc:
                logger.error(f"Error in workflow step {idx}: {step_exc}", exc_info=True)
                return {
                    "success": False,
                    "workflow": workflow["name"],
                    "failed_at_step": idx,
                    "error": str(step_exc),
                    "executed_steps": executed_steps
                }

        return {
            "success": True,
            "workflow": workflow["name"],
            "total_steps": len(steps),
            "executed_steps": executed_steps,
            "message": f"فرآیند «{workflow['name']}» با موفقیت در {len(steps)} مرحله اجرا شد."
        }

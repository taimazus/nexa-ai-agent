import os
import sys
import subprocess
import logging
import platform
import json
import time
import ctypes
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import winreg
except ImportError:
    winreg = None

try:
    import win32gui
    import win32con
    import win32api
    import win32process
except ImportError:
    win32gui = None
    win32con = None
    win32api = None
    win32process = None

logger = logging.getLogger("NovaAgent.Tools")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def execute_powershell(command: str, timeout_seconds: int = 45) -> Dict[str, Any]:
    """
    Executes a PowerShell command securely and returns structured output.
    Forces UTF-8 encoding for reliable Persian and international text handling.
    """
    logger.info(f"Executing PowerShell command: {command[:120]}")
    encoded_cmd = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $OutputEncoding = [System.Text.Encoding]::UTF8; {command}"
    
    try:
        process = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", encoded_cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        returncode = process.returncode
        return {
            "success": returncode == 0,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "returncode": returncode
        }
    except subprocess.TimeoutExpired as exc:
        process.kill()
        logger.error(f"PowerShell command timed out after {timeout_seconds}s: {exc}")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout_seconds} seconds.",
            "returncode": -1
        }
    except Exception as exc:
        logger.error(f"Failed to execute PowerShell command: {exc}", exc_info=True)
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution error: {str(exc)}",
            "returncode": -1
        }


def execute_python(code: str, timeout_seconds: int = 45) -> Dict[str, Any]:
    """
    Executes Python code in an isolated subprocess with UTF-8 encoding.
    """
    logger.info("Executing Python snippet...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-c", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        returncode = process.returncode
        return {
            "success": returncode == 0,
            "output": stdout.strip(),
            "error": stderr.strip(),
            "returncode": returncode
        }
    except subprocess.TimeoutExpired as exc:
        process.kill()
        logger.error(f"Python execution timed out after {timeout_seconds}s: {exc}")
        return {
            "success": False,
            "output": "",
            "error": f"Python script timed out after {timeout_seconds}s.",
            "returncode": -1
        }
    except Exception as exc:
        logger.error(f"Failed to execute Python script: {exc}", exc_info=True)
        return {
            "success": False,
            "output": "",
            "error": f"Python error: {str(exc)}",
            "returncode": -1
        }


def file_operations(action: str, path: str, content: Optional[str] = None) -> Dict[str, Any]:
    """
    Handles file operations safely: read, write, append, list_dir, exists, delete.
    """
    action = action.lower()
    target_path = Path(path).resolve()
    logger.info(f"File operation: action='{action}', path='{target_path}'")
    
    try:
        if action == "read":
            if not target_path.exists():
                return {"success": False, "error": f"File does not exist: {target_path}"}
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                data = f.read()
            return {"success": True, "content": data, "size_bytes": len(data)}
            
        elif action == "write":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content or "")
            return {"success": True, "path": str(target_path), "bytes_written": len(content or "")}
            
        elif action == "append":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "a", encoding="utf-8") as f:
                f.write(content or "")
            return {"success": True, "path": str(target_path)}
            
        elif action == "list_dir":
            if not target_path.exists() or not target_path.is_dir():
                return {"success": False, "error": f"Directory not found: {target_path}"}
            items = []
            for child in target_path.iterdir():
                items.append({
                    "name": child.name,
                    "is_dir": child.is_dir(),
                    "size": child.stat().st_size if child.is_file() else None
                })
            return {"success": True, "directory": str(target_path), "items": items}
            
        elif action == "exists":
            return {"success": True, "exists": target_path.exists(), "is_file": target_path.is_file(), "is_dir": target_path.is_dir()}
            
        elif action == "delete":
            if not target_path.exists():
                return {"success": False, "error": f"Path not found: {target_path}"}

            # Safety Guard: Prevent catastrophic deletion of system root, drives, or user home directory
            resolved_str = str(target_path).lower().rstrip("\\/")
            system_drive = os.environ.get("SystemDrive", "C:").lower().rstrip("\\/")
            win_dir = os.environ.get("WINDIR", "C:\\Windows").lower().rstrip("\\/")
            prog_files = os.environ.get("ProgramFiles", "C:\\Program Files").lower().rstrip("\\/")
            user_home = str(Path.home()).lower().rstrip("\\/")

            protected_paths = {
                system_drive,
                f"{system_drive}\\",
                win_dir,
                f"{win_dir}\\system32",
                prog_files,
                user_home
            }

            if resolved_str in protected_paths or len(target_path.parts) <= 1 or target_path == target_path.anchor:
                logger.warning(f"Prevented dangerous deletion of protected path: {target_path}")
                return {
                    "success": False,
                    "error": f"عملیات حذف روی مسیرهای حساس یا ریشه سیستم‌عامل مسدود شده است: {target_path}"
                }

            if target_path.is_file():
                target_path.unlink()
            else:
                import shutil
                shutil.rmtree(target_path)
            return {"success": True, "deleted": str(target_path)}
            
        else:
            return {"success": False, "error": f"Unsupported action: {action}"}
            
    except Exception as exc:
        logger.error(f"Error in file operation '{action}' on '{path}': {exc}", exc_info=True)
        return {"success": False, "error": f"File operation error: {str(exc)}"}


def system_diagnostics() -> Dict[str, Any]:
    """
    Collects system diagnostics (OS, architecture, CPU count, memory, disks).
    """
    logger.info("Gathering system diagnostics...")
    try:
        import shutil
        total_b, used_b, free_b = shutil.disk_usage("C:\\")
        
        # Simple memory query via PowerShell without extra dependencies
        ps_mem = execute_powershell(
            "(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize, (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"
        )
        total_mb = 0
        free_mb = 0
        if ps_mem["success"] and ps_mem["stdout"]:
            lines = ps_mem["stdout"].splitlines()
            if len(lines) >= 2:
                try:
                    total_mb = int(lines[0].strip()) // 1024
                    free_mb = int(lines[1].strip()) // 1024
                except ValueError as val_err:
                    logger.warning(f"Could not parse memory numbers from PowerShell output: {val_err}")
                    
        return {
            "success": True,
            "data": {
                "os": platform.platform(),
                "machine": platform.machine(),
                "python_version": platform.python_version(),
                "cpu_cores": os.cpu_count(),
                "memory_mb": {
                    "total": total_mb,
                    "free": free_mb,
                    "used": total_mb - free_mb if total_mb > free_mb else 0
                },
                "disk_c_gb": {
                    "total": round(total_b / (1024**3), 2),
                    "free": round(free_b / (1024**3), 2),
                    "used": round(used_b / (1024**3), 2)
                }
            }
        }
    except Exception as exc:
        logger.error(f"Error gathering system diagnostics: {exc}", exc_info=True)
        return {"success": False, "error": f"Diagnostics error: {str(exc)}"}


def fetch_url(url: str, timeout_seconds: int = 15) -> Dict[str, Any]:
    """
    Fetches raw text content from a web page URL.
    """
    logger.info(f"Fetching URL: {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NovaDesktopAgent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            content_type = response.headers.get("content-type", "")
            raw_data = response.read()
            text = raw_data.decode("utf-8", errors="replace")
            
            # Simple HTML tags strip if HTML
            if "html" in content_type.lower():
                import re
                text = re.sub(r"<script.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                
            return {
                "success": True,
                "url": url,
                "text": text[:6000],  # Return up to 6000 chars
                "truncated": len(text) > 6000
            }
    except Exception as exc:
        logger.error(f"Failed to fetch URL {url}: {exc}", exc_info=True)
        return {"success": False, "error": f"Network fetch error: {str(exc)}"}


def open_app_or_url(target: str) -> Dict[str, Any]:
    """
    Opens an application, file, or web URL via Windows Shell.
    """
    logger.info(f"Opening app or URL: {target}")
    try:
        os.startfile(target)
        return {"success": True, "target": target}
    except Exception as exc:
        logger.error(f"Failed to open '{target}': {exc}", exc_info=True)
        # Try powershell Start-Process
        res = execute_powershell(f"Start-Process '{target}'")
        if res["success"]:
            return {"success": True, "target": target}
        return {"success": False, "error": f"Could not open target: {str(exc)}"}


def capture_screenshot(save_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Captures a screenshot of the primary Windows desktop.
    """
    logger.info("Capturing desktop screenshot...")
    try:
        from PIL import ImageGrab
        import tempfile
        import base64
        
        img = ImageGrab.grab()
        if not save_path:
            temp_dir = tempfile.gettempdir()
            save_path = os.path.join(temp_dir, "nova_screen.png")
            
        img.save(save_path, format="PNG")
        
        # Read base64
        with open(save_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("ascii")
            
        return {
            "success": True,
            "path": save_path,
            "width": img.width,
            "height": img.height,
            "base64_data": b64_str
        }
    except Exception as exc:
        logger.error(f"Failed to capture screenshot: {exc}", exc_info=True)
        return {"success": False, "error": f"Screenshot error: {str(exc)}"}


def capture_webcam(camera_index: int = 0, save_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Captures a frame from the connected webcam using OpenCV and saves it.
    Returns the saved image path and base64 encoded image string.
    """
    logger.info(f"Capturing frame from webcam index {camera_index}...")
    try:
        import cv2
        import tempfile
        import base64

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            logger.error(f"Cannot open webcam device index {camera_index}")
            return {"success": False, "error": f"Webcam device index {camera_index} is not available or disconnected."}

        try:
            # Warm-up read
            ret, frame = cap.read()
            if not ret or frame is None:
                return {"success": False, "error": "Failed to read initial frame from webcam."}

            # Actual frame read
            ret, frame = cap.read()
            if not ret or frame is None:
                return {"success": False, "error": "Empty frame captured from webcam."}
        finally:
            cap.release()

        if not save_path:
            temp_dir = tempfile.gettempdir()
            save_path = os.path.join(temp_dir, "nova_webcam.jpg")

        cv2.imwrite(save_path, frame)
        h, w, _ = frame.shape

        with open(save_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("ascii")

        logger.info(f"Webcam image saved to: {save_path} ({w}x{h})")
        return {
            "success": True,
            "path": save_path,
            "width": w,
            "height": h,
            "base64_data": b64_str
        }
    except Exception as exc:
        logger.error(f"Failed to capture webcam frame: {exc}", exc_info=True)
        return {"success": False, "error": f"Webcam capture error: {str(exc)}"}


def list_installed_apps(query: Optional[str] = None) -> Dict[str, Any]:
    """
    Discovers all installed software, applications, and shortcuts on the Windows system.
    Scans the Windows Registry, Start Menu directories, and common Windows utilities.
    """
    logger.info(f"Listing installed applications (query='{query}')...")
    results = []
    seen = set()

    # 1. Standard Windows Accessories & Built-in Utilities
    builtins = [
        {"name": "Notepad (یادداشت)", "path": "notepad.exe", "source": "Built-in"},
        {"name": "Calculator (ماشین حساب)", "path": "calc.exe", "source": "Built-in"},
        {"name": "Paint (نقاشی)", "path": "mspaint.exe", "source": "Built-in"},
        {"name": "File Explorer (مدیریت فایل)", "path": "explorer.exe", "source": "Built-in"},
        {"name": "Task Manager (مدیریت وظایف)", "path": "taskmgr.exe", "source": "Built-in"},
        {"name": "Command Prompt (خط فرمان)", "path": "cmd.exe", "source": "Built-in"},
        {"name": "PowerShell", "path": "powershell.exe", "source": "Built-in"},
        {"name": "Windows Settings (تنظیمات ویندوز)", "path": "ms-settings:", "source": "Built-in"},
        {"name": "Control Panel (کنترل پنل)", "path": "control.exe", "source": "Built-in"},
        {"name": "Snipping Tool (ابزار برش صفحه)", "path": "snippingtool.exe", "source": "Built-in"}
    ]
    for b in builtins:
        seen.add(b["name"].lower())
        results.append(b)

    # 2. Windows Registry
    if winreg:
        roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        for root, rpath in roots:
            try:
                with winreg.OpenKey(root, rpath) as key:
                    count = winreg.QueryInfoKey(key)[0]
                    for i in range(count):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                except OSError:
                                    continue

                                if not name or not name.strip():
                                    continue
                                
                                clean_name = name.strip()
                                lower_name = clean_name.lower()
                                if lower_name in seen:
                                    continue
                                seen.add(lower_name)

                                version = ""
                                try:
                                    version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                                except OSError as oe:
                                    logger.debug(f"Optional DisplayVersion not present: {oe}")

                                install_loc = ""
                                try:
                                    install_loc, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                                except OSError as oe:
                                    logger.debug(f"Optional InstallLocation not present: {oe}")

                                results.append({
                                    "name": clean_name,
                                    "version": str(version),
                                    "path": install_loc,
                                    "source": "Registry"
                                })
                        except Exception as item_err:
                            logger.debug(f"Error reading subkey: {item_err}")
            except Exception as reg_err:
                logger.warning(f"Error accessing registry path {rpath}: {reg_err}")

    # 3. Start Menu Shortcuts
    start_dirs = [
        Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    ]
    for sdir in start_dirs:
        try:
            if sdir.exists():
                for p in sdir.rglob("*.lnk"):
                    stem = p.stem.strip()
                    lower_stem = stem.lower()
                    if lower_stem not in seen:
                        seen.add(lower_stem)
                        results.append({
                            "name": stem,
                            "path": str(p),
                            "source": "StartMenu"
                        })
        except Exception as sm_err:
            logger.warning(f"Error scanning Start Menu at {sdir}: {sm_err}")

    if query:
        q = query.lower().strip()
        filtered = [r for r in results if q in r["name"].lower() or (r.get("path") and q in r["path"].lower())]
        return {
            "success": True,
            "query": query,
            "count": len(filtered),
            "apps": filtered[:100]
        }

    results.sort(key=lambda x: x["name"].lower())
    return {
        "success": True,
        "count": len(results),
        "apps": results[:500]
    }


def list_open_windows() -> Dict[str, Any]:
    """
    Lists all currently visible, active application windows on the desktop.
    Returns window handles (HWND), window titles, and process IDs.
    """
    logger.info("Listing active open application windows...")
    windows = []
    ignored_titles = {
        "program manager", "default ime", "msctfime ui", "gdi+ window",
        "nvidia geforce overlay", "settings"
    }

    if win32gui and win32process:
        def enum_handler(hwnd, extra):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).strip()
                    if title and not any(ig in title.lower() for ig in ignored_titles):
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        extra.append({
                            "hwnd": hwnd,
                            "title": title,
                            "pid": pid
                        })
            except Exception as e:
                logger.debug(f"EnumWindows error on hwnd {hwnd}: {e}")

        try:
            win32gui.EnumWindows(enum_handler, windows)
        except Exception as exc:
            logger.error(f"Error enumerating windows via win32gui: {exc}", exc_info=True)

    # Fallback or complement with tasklist if windows empty
    if not windows:
        try:
            import csv
            import io
            res = subprocess.run(["tasklist", "/v", "/fo", "csv"], capture_output=True, text=True, encoding="cp1252", errors="replace")
            reader = csv.DictReader(io.StringIO(res.stdout))
            for row in reader:
                title = row.get("Window Title", "").strip()
                pname = row.get("Image Name", "").strip()
                pid_str = row.get("PID", "0")
                if title and title != "N/A" and not any(ig in title.lower() for ig in ignored_titles):
                    try:
                        pid = int(pid_str)
                    except ValueError:
                        pid = 0
                    windows.append({
                        "hwnd": 0,
                        "title": title,
                        "pid": pid,
                        "process_name": pname
                    })
        except Exception as exc:
            logger.error(f"Error querying tasklist for open windows: {exc}", exc_info=True)

    return {
        "success": True,
        "count": len(windows),
        "windows": windows
    }


def bring_window_to_foreground(hwnd: int) -> bool:
    """
    Brings a target window handle (HWND) to the foreground, bypassing Windows focus locks.
    """
    if not hwnd or not win32gui:
        return False
    try:
        user32 = ctypes.windll.user32
        # Pulse Alt (VK_MENU = 0x12) to bypass foreground lock restrictions
        user32.keybd_event(0x12, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(0x12, 0, 2, 0)

        if win32con:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception as exc:
        logger.error(f"Error bringing window {hwnd} to foreground: {exc}", exc_info=True)
        return False


def launch_or_focus_app(app_name_or_path: str) -> Dict[str, Any]:
    """
    Launches an application or brings its active window to the foreground.
    Accepts app names like 'Notepad', 'Excel', 'Chrome', 'Calculator', or file paths.
    """
    logger.info(f"Launching or focusing application: {app_name_or_path}")
    q = app_name_or_path.lower().strip()

    # 1. Check if window is already open
    open_win = list_open_windows()
    for w in open_win.get("windows", []):
        w_title = w.get("title", "").lower()
        if q in w_title or (w.get("process_name") and q in w.get("process_name").lower()):
            hwnd = w.get("hwnd", 0)
            if hwnd:
                bring_window_to_foreground(hwnd)
                return {
                    "success": True,
                    "action": "focused_existing_window",
                    "title": w.get("title"),
                    "hwnd": hwnd,
                    "pid": w.get("pid")
                }
            else:
                # Use powershell AppActivate
                execute_powershell(f"$w = New-Object -ComObject WScript.Shell; $w.AppActivate({w.get('pid')})")
                return {
                    "success": True,
                    "action": "focused_via_pid",
                    "title": w.get("title"),
                    "pid": w.get("pid")
                }

    # 2. Mapping of common friendly names to standard executables
    friendly_map = {
        "notepad": "notepad.exe",
        "یادداشت": "notepad.exe",
        "نوت پد": "notepad.exe",
        "نوت‌پد": "notepad.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "ماشین حساب": "calc.exe",
        "paint": "mspaint.exe",
        "نقاشی": "mspaint.exe",
        "word": "winword.exe",
        "ورد": "winword.exe",
        "excel": "excel.exe",
        "اکسل": "excel.exe",
        "chrome": "chrome.exe",
        "کروم": "chrome.exe",
        "edge": "msedge.exe",
        "firefox": "firefox.exe",
        "فایرفاکس": "firefox.exe",
        "telegram": "telegram.exe",
        "تلگرام": "telegram.exe",
        "code": "code",
        "vscode": "code",
        "vs code": "code",
        "explorer": "explorer.exe",
        "فایل منیجر": "explorer.exe",
        "taskmgr": "taskmgr.exe",
        "تسک منیجر": "taskmgr.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe"
    }

    target = friendly_map.get(q, app_name_or_path)

    # 3. If target is not an executable name and not found, search installed apps
    if not target.endswith(".exe") and not os.path.exists(target):
        found_apps = list_installed_apps(query=q).get("apps", [])
        if found_apps:
            best_match = found_apps[0]
            if best_match.get("path") and os.path.exists(best_match["path"]):
                target = best_match["path"]

    # 4. Launch application
    try:
        os.startfile(target)
        time.sleep(1.5)
        # Try to focus the newly opened window
        new_win = list_open_windows()
        for w in new_win.get("windows", []):
            if q in w.get("title", "").lower():
                if w.get("hwnd"):
                    bring_window_to_foreground(w["hwnd"])
                return {
                    "success": True,
                    "action": "launched_and_focused",
                    "target": target,
                    "title": w.get("title"),
                    "hwnd": w.get("hwnd")
                }

        return {
            "success": True,
            "action": "launched",
            "target": target,
            "note": "Application started successfully."
        }
    except Exception as exc:
        logger.warning(f"os.startfile failed for '{target}': {exc}. Trying PowerShell...")
        ps_res = execute_powershell(f"Start-Process '{target}'")
        if ps_res["success"]:
            return {
                "success": True,
                "action": "launched_via_powershell",
                "target": target
            }
        logger.error(f"Failed to launch application '{target}': {exc}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to launch application '{target}': {str(exc)}"
        }


def type_unicode_text(text: str) -> bool:
    """
    Types unicode text directly into the focused window using Windows SendInput API.
    Supports Persian, Arabic, English, emoji, numbers, and symbols.
    """
    try:
        user32 = ctypes.windll.user32
        
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
            ]

        class INPUT(ctypes.Structure):
            class _INPUT(ctypes.Union):
                _fields_ = [("ki", KEYBDINPUT)]
            _anonymous_ = ("_input",)
            _fields_ = [("type", ctypes.c_ulong), ("_input", _INPUT)]

        for char in text:
            if char == "\n":
                # Send Enter key
                inp_down = INPUT()
                inp_down.type = 1
                inp_down.ki.wVk = 0x0D  # VK_RETURN
                inp_down.ki.wScan = 0
                inp_down.ki.dwFlags = 0

                inp_up = INPUT()
                inp_up.type = 1
                inp_up.ki.wVk = 0x0D
                inp_up.ki.wScan = 0
                inp_up.ki.dwFlags = 0x0002  # KEYEVENTF_KEYUP
                
                events = (INPUT * 2)(inp_down, inp_up)
                user32.SendInput(2, events, ctypes.sizeof(INPUT))
            else:
                inp_down = INPUT()
                inp_down.type = 1
                inp_down.ki.wVk = 0
                inp_down.ki.wScan = ord(char)
                inp_down.ki.dwFlags = 0x0004  # KEYEVENTF_UNICODE

                inp_up = INPUT()
                inp_up.type = 1
                inp_up.ki.wVk = 0
                inp_up.ki.wScan = ord(char)
                inp_up.ki.dwFlags = 0x0004 | 0x0002  # KEYEVENTF_UNICODE | KEYEVENTF_KEYUP

                events = (INPUT * 2)(inp_down, inp_up)
                user32.SendInput(2, events, ctypes.sizeof(INPUT))

            time.sleep(0.015)
        return True
    except Exception as exc:
        logger.error(f"Error in type_unicode_text: {exc}", exc_info=True)
        return False


def send_app_keys(keys_or_text: Optional[str] = None, hotkey: Optional[str] = None, app_name_or_title: Optional[str] = None) -> Dict[str, Any]:
    """
    Sends keystrokes, shortcuts, or text typing to any application.
    - hotkey: e.g. 'ctrl+s', 'ctrl+c', 'ctrl+v', 'ctrl+a', 'alt+f4', 'enter', 'tab', 'esc', 'win+r'
    - keys_or_text: Text string to type (supports Persian and English).
    - app_name_or_title: If provided, brings that application window to front first.
    """
    logger.info(f"Sending keys: hotkey='{hotkey}', text_len={len(keys_or_text or '')}, target_app='{app_name_or_title}'")
    
    # If target app requested, focus it first
    if app_name_or_title:
        focus_res = launch_or_focus_app(app_name_or_title)
        time.sleep(0.3)
        if not focus_res.get("success"):
            logger.warning(f"Could not focus app '{app_name_or_title}', proceeding with current window.")

    hotkey_executed = None
    if hotkey:
        hk = hotkey.lower().strip().replace(" ", "")
        hotkey_map = {
            "ctrl+s": "^s",
            "ctrl+c": "^c",
            "ctrl+v": "^v",
            "ctrl+a": "^a",
            "ctrl+z": "^z",
            "ctrl+y": "^y",
            "ctrl+n": "^n",
            "ctrl+f": "^f",
            "ctrl+w": "^w",
            "ctrl+p": "^p",
            "ctrl+o": "^o",
            "ctrl+t": "^t",
            "alt+f4": "%{F4}",
            "alt+tab": "%{TAB}",
            "enter": "{ENTER}",
            "return": "{ENTER}",
            "esc": "{ESC}",
            "escape": "{ESC}",
            "tab": "{TAB}",
            "backspace": "{BACKSPACE}",
            "delete": "{DELETE}",
            "f5": "{F5}",
            "space": " "
        }
        send_code = hotkey_map.get(hk)
        if send_code:
            ps_cmd = f"$w = New-Object -ComObject WScript.Shell; $w.SendKeys('{send_code}')"
            execute_powershell(ps_cmd)
            hotkey_executed = hk
            time.sleep(0.2)
        else:
            logger.warning(f"Unmapped hotkey '{hotkey}', attempting direct SendKeys format.")
            ps_cmd = f"$w = New-Object -ComObject WScript.Shell; $w.SendKeys('{hotkey}')"
            execute_powershell(ps_cmd)
            hotkey_executed = hotkey

    typed_count = 0
    if keys_or_text:
        ok = type_unicode_text(keys_or_text)
        if ok:
            typed_count = len(keys_or_text)
        else:
            # Fallback via PowerShell clipboard paste
            try:
                import subprocess
                ps_clip = f"Set-Clipboard -Value @'\n{keys_or_text}\n'@; $w = New-Object -ComObject WScript.Shell; $w.SendKeys('^v')"
                execute_powershell(ps_clip)
                typed_count = len(keys_or_text)
            except Exception as exc:
                logger.error(f"Fallback paste failed: {exc}", exc_info=True)

    return {
        "success": True,
        "app_targeted": app_name_or_title,
        "hotkey_executed": hotkey_executed,
        "characters_typed": typed_count
    }


def click_screen(x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1, app_name_or_title: Optional[str] = None) -> Dict[str, Any]:
    """
    Clicks the mouse at specified coordinates or in the focused application.
    """
    logger.info(f"Clicking screen: x={x}, y={y}, button={button}, clicks={clicks}, app={app_name_or_title}")
    if app_name_or_title:
        launch_or_focus_app(app_name_or_title)
        time.sleep(0.3)

    try:
        user32 = ctypes.windll.user32
        if x is not None and y is not None:
            user32.SetCursorPos(int(x), int(y))
            time.sleep(0.05)

        btn = button.lower().strip()
        down_flag = 0x0002 if btn == "left" else 0x0008  # MOUSEEVENTF_LEFTDOWN / RIGHTDOWN
        up_flag = 0x0004 if btn == "left" else 0x0010    # MOUSEEVENTF_LEFTUP / RIGHTUP

        for _ in range(clicks):
            user32.mouse_event(down_flag, 0, 0, 0, 0)
            time.sleep(0.05)
            user32.mouse_event(up_flag, 0, 0, 0, 0)
            time.sleep(0.05)

        return {
            "success": True,
            "x": x,
            "y": y,
            "button": btn,
            "clicks": clicks
        }
    except Exception as exc:
        logger.error(f"Error performing mouse click: {exc}", exc_info=True)
        return {"success": False, "error": f"Mouse click error: {str(exc)}"}


def close_app(process_name_or_title: str, force: bool = False) -> Dict[str, Any]:
    """
    Closes an application gracefully or forcefully by process name or window title.
    """
    logger.info(f"Closing application: {process_name_or_title} (force={force})")
    q = process_name_or_title.lower().strip()

    # Find matching window
    matched_hwnds = []
    matched_pids = set()
    open_win = list_open_windows()
    for w in open_win.get("windows", []):
        if q in w.get("title", "").lower() or (w.get("process_name") and q in w.get("process_name").lower()):
            if w.get("hwnd"):
                matched_hwnds.append(w["hwnd"])
            if w.get("pid"):
                matched_pids.add(w["pid"])

    if not force and win32gui and win32con and matched_hwnds:
        for hwnd in matched_hwnds:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            except Exception as e:
                logger.debug(f"WM_CLOSE error: {e}")
        time.sleep(0.5)
        return {"success": True, "method": "WM_CLOSE", "target": process_name_or_title}

    # If force or no hwnd, use taskkill
    target_clean = process_name_or_title if process_name_or_title.endswith(".exe") else f"{process_name_or_title}.exe"
    res = subprocess.run(["taskkill", "/f", "/im", target_clean], capture_output=True, text=True)
    if res.returncode == 0:
        return {"success": True, "method": "taskkill_im", "target": target_clean}

    # Try taskkill by PID
    killed_pids = []
    for pid in matched_pids:
        k_res = subprocess.run(["taskkill", "/f", "/pid", str(pid)], capture_output=True, text=True)
        if k_res.returncode == 0:
            killed_pids.append(pid)

    if killed_pids:
        return {"success": True, "method": "taskkill_pid", "pids": killed_pids}

    return {
        "success": False,
        "error": f"No running process or window found matching '{process_name_or_title}'."
    }



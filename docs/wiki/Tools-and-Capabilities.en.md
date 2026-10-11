<div lang="en" dir="ltr" align="left">

# OS Tools & Capabilities 🛠️

**English Version** | [نسخه فارسی](Tools-and-Capabilities.fa.md)

Unlike passive text chatbots, Nova Desktop AI Agent is an **autonomous operating system agent** equipped with real system execution capabilities to run commands, manage files, open desktop applications, query hardware status, and capture live visuals.

---

## 1. Core Tool Registry

| Tool Name | Parameters | Purpose & Windows Integration |
| :--- | :--- | :--- |
| **`execute_powershell`** | `command`, `timeout_seconds` | Executes PowerShell and CMD commands with forced UTF-8 encoding for seamless international & Persian character preservation. |
| **`execute_python`** | `code`, `timeout_seconds` | Executes Python scripts, mathematics, and data processing in an isolated subprocess with strict standard output capturing. |
| **`file_operations`** | `action`, `path`, `content` | Comprehensive filesystem manager: `read`, `write`, `append`, `list_dir`, `exists`, and safe `delete`. |
| **`system_diagnostics`** | _None_ | Queries Windows version, CPU architecture, core counts, free/used RAM in MB, and primary disk drive capacities in GB. |
| **`open_app_or_url`** | `target` | Launches native desktop applications (e.g. Notepad, Calculator, VS Code) or opens URLs in the default browser. |
| **`fetch_url`** | `url`, `timeout_seconds` | Fetches web pages over HTTP, strips scripts/styles, and extracts readable text content for AI analysis. |
| **`capture_screenshot`** | `save_path` (optional) | Takes a full screenshot of the primary Windows monitor and encodes as PNG + base64 for multimodal vision. |
| **`capture_webcam`** | `camera_index`, `save_path` (optional) | Captures a live camera frame via OpenCV to identify faces, documents, desk objects, or the user's environment. |

---

## 2. Real-World Execution Scenarios

### Scenario 1: Telemetry & Memory Inspection
- **User Prompt:** *"Check my computer hardware and tell me how much RAM is free"*
- **Agent Action:** Dispatches `system_diagnostics` ➔ Parses memory stats ➔ Generates concise response:
  > *"Your system has 16 GB of physical RAM, currently utilizing 5.4 GB with 10.6 GB free. Drive C has 120 GB free space."*

### Scenario 2: Python Code Execution
- **User Prompt:** *"Write a Python script that calculates fibonacci numbers up to 100 and print them"*
- **Agent Action:** Dispatches `execute_python` with generated code ➔ Reads stdout ➔ Presents formatted code card with verified output.

### Scenario 3: Project Filesystem Creation
- **User Prompt:** *"Create a folder named Projects on my Desktop with a starter README inside"*
- **Agent Action:** Dispatches `file_operations` targeting the Desktop path with UTF-8 encoding and folder recursion.

---

## 3. Reliability & Guardrails
- All external processes are bound to execution timeouts (default: 45s) to prevent frozen states or runaway subprocesses.
- Command errors and non-zero exit codes are intercepted and automatically forwarded to the **Continuous Self-Learning Engine** (`LearningEngine`) to synthesize corrective rules for future queries.

</div>

<div lang="en" dir="ltr" align="left">

# Tools & Operating System Capabilities 🛠️

[نسخه فارسی](Tools-and-Capabilities.fa.md) | **English Version**

Unlike conversational-only chatbots, **NexA AI** Desktop Agent by **Rahkar Electronic Sahand** ([irres.ir](https://irres.ir)) is equipped with an **Autonomous Agent Toolset**. NexA can interact directly with Windows OS, automate desktop applications, manage inboxes, write social media content, and monitor hardware metrics.

---

## 1. Complete Catalog of NexA AI Tools

### 1.1. Core System & Multimodal Tools
| Tool Name | Parameters | Purpose & Windows Operation |
| :--- | :--- | :--- |
| **`execute_powershell`** | `command`, `timeout_seconds` | Executes PowerShell and CMD commands with mandatory UTF-8 encoding for full Persian and multi-byte text fidelity. |
| **`execute_python`** | `code`, `timeout_seconds` | Executes code snippets, mathematical algorithms, and data transformations in an isolated Python process. |
| **`file_operations`** | `action`, `path`, `content` | Comprehensive file management: `read`, `write`, `append`, `list_dir`, `exists`, and safe `delete`. |
| **`system_diagnostics`** | _None_ | Gathers system telemetry: Windows build, CPU architecture, RAM consumption, and drive space. |
| **`open_app_or_url`** | `target` | Launches desktop apps (e.g., Notepad, Calculator, VS Code) or web targets in default browsers. |
| **`fetch_url`** | `url`, `timeout_seconds` | Scrapes web pages, strips scripts/styles, and extracts structured text for analysis. |
| **`capture_screenshot`** | `save_path` (optional) | Captures instant desktop displays and exports PNG/base64 representations. |
| **`capture_webcam`** | `camera_index`, `save_path` (optional) | Connects to webcam hardware via OpenCV to inspect physical user environments. |

### 1.2. NexA Family Ecosystem & Personalization Tools
| Tool Name | Parameters | Purpose |
| :--- | :--- | :--- |
| **`switch_family_member`** | `member_name` | Switches the active agent persona (NexaMehr, NexaNoo, SamYar, Artin, Nila, Tara, Parsa). |
| **`customize_family_member`** | `name`, `display_name_fa`, `gender`, `mood`, `avatar_style`, ... | Dynamically customizes character traits, tone, voice speaker, and visual avatar styling. |
| **`teach_family_skill`** | `member_name`, `skill_name`, `steps` | Teaches new step-by-step capabilities to family members, awarding experience points (XP). |
| **`add_family_member`** | `name`, `display_name_fa`, `role`, `personality`, ... | Registers a new custom agent member into the NexA family. |
| **`list_family_members`** | _None_ | Lists active members, experience levels, and current role assignments. |

### 1.3. Desktop Application Control & Macro Engine Tools
| Tool Name | Parameters | Purpose |
| :--- | :--- | :--- |
| **`inspect_app_ui`** | `window_title`, `control_type` | Inspects the UI Automation control tree of target windows (buttons, text inputs, menus, checkboxes). |
| **`invoke_app_element`** | `window_title`, `element_name`, `control_type`, `action` | Automatically invokes and clicks elements in Windows desktop applications. |
| **`learn_app_workflow`** | `workflow_name`, `app_name`, `steps`, `description` | Saves multi-step desktop workflows for future execution as automated macros. |
| **`execute_app_workflow`** | `workflow_name`, `parameters` | Executes learned workflows, injecting dynamic parameters (e.g. `{text}` or `{filename}`). |
| **`list_app_workflows`** | _None_ | Enumerates all memorized desktop automation workflows. |

### 1.4. Email & Instagram Integration Tools
| Tool Name | Parameters | Purpose |
| :--- | :--- | :--- |
| **`check_emails`** | `folder`, `limit`, `unread_only`, `search_query` | Connects via IMAP, retrieves messages, categorizes urgent/financial topics, and prepares spoken summaries. |
| **`send_email`** | `to_email`, `subject`, `body` | Sends emails or replies using the configured SMTP server. |
| **`configure_email_settings`** | `imap_server`, `smtp_server`, `email_address`, ... | Configures email credentials through conversational voice instructions. |
| **`plan_instagram_content`** | `topic`, `target_audience`, `content_type` | Plans reels scripts, post concepts, engagement hooks, and viral hashtags. |
| **`open_instagram`** | _None_ | Opens Instagram in the default web browser. |
| **`copy_caption_to_clipboard`** | `caption` | Copies captions and hashtags directly to the Windows clipboard for fast publishing. |

---

## 2. Safety, Sandboxing & Continuous Learning
* **Timeouts:** All system executions have enforced timeouts to prevent hanging processes.
* **Error Analysis via `LearningEngine`:** When tool execution encounters errors, the failure mode is inspected and preventative rules are saved to the persistent knowledge base.

</div>

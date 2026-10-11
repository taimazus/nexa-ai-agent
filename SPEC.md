# Functional Specification: SahandYar AI Desktop Agent (دستیار هوشمند سَهندیار)

> **طراحی و توسعه:** شرکت راهکار الکترونیک سهند &nbsp;|&nbsp; وب‌سایت رسمی: [https://irres.ir](https://irres.ir)

## 1. Overview
SahandYar Desktop Agent (سَهندیار) is a proprietary autonomous, animated desktop assistant for Windows developed by **Rahkar Electronic Sahand** (irres.ir). It provides:
- A draggable, transparent, always-on-top animated mascot (Neon 3D Robot) with multi-state reactive animations (Idle, Thinking, Working/Executing, Speaking, Success, Error).
- An interactive Chat & Command Center with modern dark/neon glassmorphism aesthetics, Markdown rendering, and code syntax styling.
- An Agentic Tool Execution Engine powered by Gemini (`gemini-2.5-flash`), capable of multi-turn function calling for:
  - PowerShell / CMD command execution.
  - Python code generation and execution.
  - File management (create, read, write, list).
  - Web scraping & URL fetching.
  - System monitoring (CPU, RAM, active windows).
  - Desktop screenshots and Multimodal Vision queries.
- Voice/TTS feedback using Windows Speech API.

## 2. Architecture & Modules
```
c:\Users\Taimazus\Desktop\MyAgent/
├── agent/
│   ├── __init__.py
│   ├── config.py           # Configuration, API keys, paths, system prompts
│   ├── engine.py           # Gemini interaction, function calling loop
│   ├── tools.py            # Concrete tool implementations (Shell, Python, File, Web, Screen)
│   └── tts.py              # Asynchronous Windows TTS integration
├── ui/
│   ├── __init__.py
│   ├── mascot.py           # Transparent animated desktop widget (QPainter + QTimer)
│   ├── speech_bubble.py    # Floating speech bubble attached to the mascot
│   ├── chat_window.py      # Glassmorphic chat & command dialog
│   └── styles.py           # Curated dark/neon QSS and visual themes
├── tests/
│   ├── __init__.py
│   ├── test_tools.py       # Unit tests for tool execution & safety boundaries
│   ├── test_agent.py       # Unit tests for agent tool dispatching & error recovery
│   └── test_mascot_state.py# Unit tests for mascot state transitions
├── main.py                 # Application entrypoint & tray icon
└── SPEC.md                 # This specification
```

## 3. Tool Specifications
1. `execute_powershell(command: str) -> dict`:
   - Runs `powershell.exe -NoProfile -NonInteractive -Command "..."`
   - Returns `{success: bool, stdout: str, stderr: str, returncode: int}`
   - Timeout: 30s. Captures stderr and stdout with UTF-8 encoding.
2. `execute_python(code: str) -> dict`:
   - Runs isolated Python execution via subprocess.
   - Returns `{success: bool, output: str, error: str}`
3. `file_operations(action: str, path: str, content: str = None) -> dict`:
   - Actions: `read`, `write`, `append`, `list_dir`, `exists`
   - Strict UTF-8 support and path validation.
4. `system_diagnostics() -> dict`:
   - Returns OS, CPU load, memory usage, available disks, active windows.
5. `capture_desktop_screenshot() -> str`:
   - Captures screen using PyQt6 `QScreen.grabWindow` or PIL ImageGrab.
   - Saves temporary PNG and passes base64 image data to Gemini for visual reasoning.
6. `fetch_url(url: str) -> dict`:
   - Fetches web page content, extracts clean text.

## 4. Edge Cases & Safety Constraints
- **Unicode Encoding**: Windows console defaults to cp1252 or cp1256. All subprocesses and file I/O must explicitly force UTF-8 (`PYTHONIOENCODING=utf-8`, `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`).
- **Silent Failure Ban**: Every exception in tool execution and API calls must be logged and formatted into structured error dictionaries returned to the LLM and UI.
- **Non-blocking UI**: LLM calls and tool executions must run on worker threads (`QThread` or `concurrent.futures`), never freezing the mascot animation loop.
- **Window Positioning**: Mascot and chat window must calculate coordinates based on `QScreen.availableGeometry` to avoid spawning off-screen.

## 5. API Key Pool & Automatic Failover (KeyManager)
- Module: `agent/key_manager.py`
- Stores an ordered pool of Gemini API keys in `data/settings.json`.
- State tracking for each key: `status` ('active', 'quota_exceeded', 'invalid', 'cooldown').
- Fallback mechanics:
  - When Gemini raises an API error (quota exhausted, 429, 403, invalid credentials), `KeyManager` marks the current key with a cooldown timestamp and smoothly switches to the next available key.
  - The chat session is recreated with the existing conversation history so zero context is lost.
- Persistence: Settings survive restarts.

## 6. Persistent Long-Term Memory (MemoryManager)
- Module: `agent/memory.py`
- Stores structured memories, user preferences, past commands, and project facts in `data/memory.json`.
- Autonomous Tool Interface:
  - `remember_fact(key: str, value: str, category: str = "general") -> dict`: Allows Gemini to autonomously save facts the user mentioned.
  - `recall_facts(query: str = "") -> dict`: Searches remembered facts by keyword or returns all.
  - `forget_fact(key: str) -> dict`: Removes a specific memory item.
- Context Injection:
  - On every message cycle, the latest relevant memories are compiled and dynamically injected into the system instruction, guaranteeing the agent never forgets past instructions, preferences, and project facts.

## 7. Settings UI (SettingsWindow)
- Module: `ui/settings_window.py`
- Glassmorphic modal window accessible from chat header and system tray.
- Tab 1: API Keys management (add key, remove key, status badge, test key button).
- Tab 2: Memory browser (search memories, add custom note, delete memories).
- Tab 3: Persona & Voice (Gender selection: Male/Female, Name, Voice pitch/rate, Palette preview).
- Tab 4: Self-Learning (Review lessons learned from past mistakes, add manual rules, clear lessons).

## 8. Configurable Gender & Persona (PersonaManager)
- Module: `agent/persona.py`
- Personas:
  - `MALE` ("آریا" / Arya): SAPI male voice (Microsoft David/George), analytical tone, neon cyan/cobalt palette.
  - `FEMALE` ("آوا" / Ava): SAPI female voice (Microsoft Zira/Hazel), warm & sharp tone, neon magenta/aurora violet palette.
- Integrates with `TTSEngine` to automatically select gender-specific voice tokens in Windows SAPI.
- Dynamically shifts Mascot neon theme palette between Cyber Cyan and Radiant Aurora Magenta.

## 9. Continuous Self-Learning Engine (LearningEngine)
- Module: `agent/learning.py`
- Persistence: `data/learnings.json`
- Mistake recording & continuous reflection:
  - Captures failed tool calls (e.g. invalid syntax in PowerShell, missing python packages, permission issues).
  - Listens to user corrections (e.g., "اشتباه کردی", "این دستور کار نکرد", "دیگه اینکارو نکن").
  - Formulates actionable corrective rules: e.g. "در ویندوز مسیرهایی که فاصله دارند باید داخل گیومه باشند".
  - Injects all active lessons into Gemini's system instruction on every prompt turn:
    `### درس‌های آموخته‌شده از خطاهای گذشته (قوانین طلایی برای جلوگیری از تکرار اشتباه): ...`
  - Autonomous tools:
    - `record_learning(trigger: str, corrective_rule: str, category: str = "general") -> dict`
    - `query_learnings(topic: str = "") -> list`

## 10. Proactive Quota & Credit Warning System
- Module: `agent/key_manager.py`, `agent/engine.py`, `ui/mascot.py`, `ui/chat_window.py`
- Trigger Conditions:
  - Key exhaustion event (HTTP 429, ResourceExhausted, QuotaExceeded).
  - Low pool headroom (when active keys in pool <= 1).
  - Critical pool exhaustion (when 0 active keys remain).
- Multi-Channel Notification:
  1. Visual: Desktop Mascot transitions to warning/error state with amber/red glow.
  2. Floating Desktop Speech Bubble: Shows immediate clear alert on the desktop.
  3. Audio TTS: Speaks warning "هشدار: اعتبار کلید API به پایان رسید."
  4. Chat Banner: Shows glowing warning banner in chat with direct shortcut button to Settings.
  5. Windows System Tray: Balloon/toast notification to notify the user even when chat is minimized.

## 11. Multiple Selectable 3D Avatars (AvatarStyle)
- Module: `agent/persona.py`, `ui/mascot.py`, `ui/settings_window.py`
- Selectable Avatars:
  1. `CYBER_BOT`: ربات نئونی هوشمند با رینگ‌های هولوگرافیک و ویزور دیجیتال.
  2. `CYBER_CAT`: گربه سه‌بعدی کاوایی و بامزه با گوش‌های هولوگرافیک، چشمان درخشان، گونه‌های سرخ و سبیل‌های نوری.
  3. `ASTRAL_ORB`: گوی کوانتومی نورانی با بال‌های انرژی شناور و ذرات ستاره‌ای.
  4. `ASTRO_PANDA`: پاندای فضانورد تپلی و دوست‌داشتنی با کلاه حباب‌دار شیشه‌ای سه‌بعدی و دست‌های سایبری.
- 3D Volumetric Aesthetics:
  - Spherical radial gradients with dynamic light specular highlights.
  - Perspective foreshortening for rotating orbital rings.
  - Soft floating depth shadow projected below the character.
- Runtime Switching:
  - Settings UI tab "شخصیت و صدا" with visual cards/thumbnails.
  - Mascot right-click context menu "🎨 تغییر شکلک و آواتار".
  - Persistent state in `data/persona_settings.json`.

## 12. Multimodal Hardware Integration (Microphone, Webcam, Speaker)
- Microphone Voice Input:
  - Module: `agent/audio_recorder.py` via PyQt6 `QMediaCaptureSession` & `QMediaRecorder`.
  - Records uncompressed Wave audio (`.wav`) from the system default microphone (`Conexant ISST Audio`).
  - Directly transmitted as multimodal audio parts to Gemini 2.5 Flash (`google-genai`).
  - Supports Persian & English voice commands without manual transcription barriers.
- Webcam Vision:
  - Module: `agent/tools.py` (`capture_webcam`) via OpenCV (`cv2.VideoCapture(0)`).
  - Can be called autonomously by the agent or manually triggered by the user via the `📷` button or mascot context menu.
  - Generates high-res image frame, saves to temp disk, and forwards to Gemini for multimodal vision reasoning.
- Speaker Voice Output (TTS):
  - Module: `agent/tts.py` via Windows SAPI (`win32com.client.Dispatch("SAPI.SpVoice")`).
  - Dynamic gender voice matching (Microsoft David for male, Microsoft Zira for female).
  - Non-blocking asynchronous playback with clean markdown/emoji stripping and mute toggle (`🔊`/`🔇`).

## 13. Life Companion & Emotional Personalization Engine
- Modules: `agent/persona.py`, `agent/companion.py`, `ui/settings_window.py`
- User Profile: `user_name`, `user_role`
- Assistant Identity: `assistant_custom_name`
- Emotional & Relationship Tones:
  - `INTIMATE`: Warm, empathetic, devoted friend.
  - `MOTIVATIONAL`: Uplifting mentor, energizing coach, celebrating milestones.
  - `WITTY`: Playful, clever humor, positive vibes.
  - `EXECUTIVE`: Professional senior advisor, high-precision engineering brevity.
- Aesthetics & Visual Personalization:
  - Custom neon themes: Cyber Cobalt, Aurora Radiant, Imperial Gold, Emerald Neon, Nebula Violet.
  - Mascot sizing: Small (120px), Standard (160px), Large (200px).
- Daily Life & Health Companion Routines:
  - Proactive time-of-day contextual greetings (Morning, Noon, Evening, Night).
  - 50-minute health & hydration check-ins (eye relief, water intake, stretching).

## 14. Multi-AI Interaction, Peer Code Review & Self-Improvement Engine
- Modules: `agent/multi_ai.py`, `agent/engine.py`, `ui/settings_window.py`
- Persistence: `data/peer_ai_settings.json`, `data/peer_insights.json`
- Supported Peer Providers:
  - `openai`: OpenAI API compatible (GPT-4o, GPT-4o-mini, ChatGPT) via `/chat/completions`.
  - `claude`: Anthropic Claude API (`/v1/messages`).
  - `deepseek`: DeepSeek API (`/chat/completions`).
  - `ollama`: Local open-source models (Llama 3, Mistral, Qwen, DeepSeek-R1) at `http://localhost:11434/api/chat` (100% free, zero external keys needed).
  - `openrouter`: OpenRouter multi-model gateway.
  - `gemini_peer`: Secondary Gemini model instance for independent adversarial peer check.
- Core Capabilities:
  - **`consult_peer_ai(provider, model, prompt, role, api_key_override)`**: Consults an external AI model on architectural, algorithmic, or factual queries.
  - **`peer_code_review(code, language, context)`**: Submits code to a peer AI to find subtle bugs, concurrency traps, memory leaks, performance bottlenecks, and security flaws.
  - **`peer_critique_and_learn(topic, own_answer, peer_answer)`**: Performs comparative critique between Nova's output and peer AI output; distills superior practices into `LearningEngine` rules.
  - **`run_self_improvement(focus_area)`**: Automated self-improvement loop: reviews recent execution records, prompts, and failure logs with a peer AI, and formulates high-impact operational rules.
- Autonomous Agent Tools:
  - `consult_peer_ai`
  - `review_code_with_peer`
  - `learn_from_peer_ai`
  - `run_self_improvement`
- UI Integration:
  - Tab 6 («🌐 تعامل با سایر هوش‌های مصنوعی») in Settings:
    - Provider selector (OpenAI, Claude, DeepSeek, Local Ollama, OpenRouter, Gemini Peer).
    - API key / Base URL configuration.
    - Model selection.
    - Live connection test & peer code review trigger.
    - History of peer insights.

## 15. Windows OS Theme & Accent Integration (Auto OS Theme Sync)
- Modules: `ui/theme_detector.py`, `ui/styles.py`, `agent/persona.py`, `main.py`
- Operating System Detection:
  - Windows Light/Dark Mode via Registry: `HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize` (`AppsUseLightTheme` / `SystemUsesLightTheme`).
  - Windows Accent Color via Registry: `HKCU\Software\Microsoft\Windows\DWM` (`ColorizationColor`) and `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Accent` (`AccentColorMenu`).
- Dynamic Adaptation:
  - When Windows switches to Dark Mode: Applies dark cyberpunk glassmorphism (`#0a0e17`, translucent dark acrylic).
  - When Windows switches to Light Mode: Applies crisp, frosted acrylic light theme (`#f8fafc`, dark slate text `#0f172a`, WCAG AA contrast).
  - Windows Accent Color is extracted and harmonized into primary/secondary neon glow for the desktop mascot visor, halos, and button gradients.
  - Live listener periodically monitors Windows registry events or timer ticks, seamlessly hot-reloading window stylesheets without application restart.
  - Configurable toggle: `sync_with_os_theme` in `data/persona_settings.json` and Settings UI.





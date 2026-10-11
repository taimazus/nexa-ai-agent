<div lang="en" dir="ltr" align="left">

# System Architecture & Data Flow 🏛️

**English Version** | [نسخه فارسی](Architecture.fa.md)

This technical specification details the modular architecture, lifecycle workflows, threading model, and data interactions uniting PyQt6, Google Gemini 2.5 Flash, and the Windows OS execution layer in Nova Desktop AI Agent.

---

## 1. High-Level Layered Architecture

The system is decomposed into four discrete, decoupled tiers:

```mermaid
graph TD
    subgraph UI_Layer [User Interface Tier - PyQt6]
        Mascot[DesktopMascot - Frameless 3D Desktop Pet]
        Bubble[SpeechBubble - Floating Context Speech Bubble]
        Chat[ChatWindow - Glassmorphic Cyber Command Center]
        Settings[SettingsWindow - Settings Dialog]
        Tray[SystemTray - Windows Tray Icon]
    end

    subgraph Coordination_Layer [Coordination & Background Threading]
        Worker[AgentWorkerThread - QThread Executor]
        VoiceRec[AudioRecorder - Wave Microphone Streamer]
        TTS[TTSEngine - Native Windows SAPI Synthesizer]
    end

    subgraph Core_Agent_Layer [AI Agent & Reasoning Tier]
        Engine[AgentEngine - Gemini Client & Chat Orchestrator]
        KeyMgr[KeyManager - Key Pool & Zero-Loss Rotation]
        MemMgr[MemoryManager - Persistent Long-Term Memory]
        LearnEng[LearningEngine - Failure Reflection Engine]
        PersonaMgr[PersonaManager - Gender, Tone & Theme Store]
    end

    subgraph System_Tools_Layer [OS Tool Execution Tier]
        Tools[PowerShell / Python / Files / Webcam / Vision / Diagnostics]
        OS[(Windows 10/11 & Hardware)]
    end

    Chat --> Worker
    Worker --> Engine
    Engine --> KeyMgr
    Engine --> MemMgr
    Engine --> LearnEng
    Engine --> PersonaMgr
    Engine --> Tools
    Tools --> OS
    Worker --> Mascot
    Worker --> Bubble
    Worker --> TTS
    VoiceRec --> Chat
```

---

## 2. Request Lifecycle & Tool Execution Sequence

When a user submits a prompt, voice recording, or webcam snapshot, execution flows asynchronously through the pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant Chat as Chat Window (UI)
    participant Worker as Background Worker (QThread)
    participant Mascot as Desktop Mascot
    participant Engine as Agent Engine
    participant Gemini as Google Gemini 2.5 API
    participant Tools as OS Tools
    participant TTS as Windows SAPI TTS

    User->>Chat: Text command / Mic audio / Webcam frame
    Chat->>Mascot: Set State -> "Thinking" (Purple scanner)
    Chat->>Worker: Dispatch asynchronously (Non-blocking GUI)
    Worker->>Engine: Send message + multimodal payloads
    Engine->>Gemini: Call chat.send_message() with tool declarations
    
    opt Multi-turn Autonomous Tool Execution
        Gemini-->>Engine: Tool call request (e.g. execute_powershell or capture_webcam)
        Engine->>Mascot: Set State -> "Working" (Orange data streams)
        Engine->>Tools: Execute with strict UTF-8 & timeout safety
        Tools-->>Engine: Structured output (stdout, stderr, exit code)
        Engine->>Gemini: Forward tool response back to Gemini session
    end

    Gemini-->>Engine: Final structured natural language response
    Engine-->>Worker: Return response text
    Worker->>Mascot: Set State -> "Speaking" / "Success"
    Worker->>Chat: Render Markdown message card
    Worker->>TTS: Speak response through speakers
    TTS-->>User: Audio playback (matching active persona gender)
```

---

## 3. Module Breakdown & Responsibility Matrix

- **`main.py`**: Application bootstrap, signal-slot choreography, window positioning, system tray setup.
- **`agent/engine.py`**: Gemini chat session management, prompt composition, failover retries, and tool routing.
- **`agent/tools.py`**: Isolated execution environments for PowerShell, Python subprocesses, filesystem I/O, OpenCV webcam capture, desktop screenshots, and system hardware telemetry.
- **`agent/key_manager.py`**: Thread-safe API key pool, persistent health state, automatic rotation upon quota exhaustion.
- **`agent/memory.py`**: Long-term persistent key-value memory store (`data/memory.json`), semantic queries, system prompt injection.
- **`agent/learning.py`**: Automated failure reflection, corrective rule formulation, and gold-rule injection (`data/learnings.json`).
- **`agent/audio_recorder.py`**: Uncompressed Wave audio recording from the default Windows microphone device.
- **`agent/tts.py`**: SAPI speech synthesis with non-blocking async speech and dynamic voice matching (David/Zira).
- **`ui/mascot.py`**: Volumetric 3D vector rendering without raster image assets, supporting 4 avatars, physics float, and reactive emotional visors.
- **`ui/chat_window.py`**: Glassmorphic UI with quick action chips, multimedia attachment bar, markdown code cards, and alert banners.
- **`ui/settings_window.py`**: Tabbed dialog for keys pool, memory inspection, learning engine records, voice testing, and 3D avatar selection.

</div>

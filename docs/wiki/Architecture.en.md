<div lang="en" dir="ltr" align="left">

# System Architecture & Data Flow 🏛️

**English Version** | [نسخه فارسی](Architecture.fa.md)

This document describes the modular architecture, execution lifecycles, multi-agent family ecosystem, continuous hands-free voice activity detection (VAD), and desktop application automation of **NexA AI (نِکسا)**, engineered by **Rahkar Electronic Sahand** ([https://irres.ir](https://irres.ir)).

---

## 1. High-Level Layered Architecture

The system is separated into 5 decoupled architectural tiers:

```mermaid
graph TD
    subgraph UI_Layer [UI Presentation Layer - PyQt6]
        Mascot[DesktopMascot - 3D Expressive Pet with Volumetric Lip-Sync]
        Bubble[SpeechBubble - Floating Dialogue Card]
        Chat[ChatWindow - Glassmorphic Cyberpunk Command Center]
        Settings[SettingsWindow - 6-Tab Configuration Studio]
        Tray[SystemTray - Background Windows Tray Monitor]
    end

    subgraph Audio_Voice_Layer [Audio & Conversational VAD Tier]
        VAD[ContinuousVoiceListener - Real-time VAD & Wake-Word Detector]
        AudioRec[AudioRecorder - Manual Wave Recorder]
        TTS[TTSEngine - Gemini Neural Speech & SAPI Fallback]
    end

    subgraph Family_Ecosystem_Layer [Multi-Agent Family Ecosystem]
        FamMgr[FamilyManager - Task Router & Skill Inheritance Director]
        Artin[Artin - Windows UI & Macro Automation Specialist]
        Nila[Nila - Email & Public Relations Assistant]
        Tara[Tara - Visual Designer & Reels Strategist]
        SamYar[SamYar - Senior Software & QA Engineer]
        Parents[NexaMehr & NexaNoo - Architecture & Caregivers]
    end

    subgraph Core_Agent_Layer [Core AI & Cognitive Engine]
        Engine[AgentEngine - Gemini Session & Tools Dispatcher]
        KeyMgr[KeyManager - API Key Pool with Zero-Loss Failover]
        MemMgr[MemoryManager - Long-term Knowledge Base]
        LearnEng[LearningEngine - Autonomous Self-Learning Loop]
        MultiAI[MultiAiCollaborator - Peer Review & Offline LLMs]
        CfgMgr[ServicesConfigManager - Persistent System Configuration]
    end

    subgraph Automation_Integrations_Layer [Automation & System Layer]
        AppCtrl[AppController - Native Windows UI Automation & Macros]
        EmailSvc[EmailService - Secure IMAP/SMTP Client]
        SocialMgr[SocialMediaManager - Reels Studio & Instagram Browser Hooks]
        OSTools[PowerShell / Python / Files / Webcam / Vision / Diagnostics]
        WinOS[(Windows 10/11 & Hardware)]
    end

    Chat --> VAD
    VAD --> Chat
    Chat --> Engine
    Engine --> FamMgr
    FamMgr --> Artin
    FamMgr --> Nila
    FamMgr --> Tara
    FamMgr --> SamYar
    FamMgr --> Parents
    Artin --> AppCtrl
    Nila --> EmailSvc
    Tara --> SocialMgr
    Engine --> KeyMgr
    Engine --> MemMgr
    Engine --> LearnEng
    Engine --> MultiAI
    Engine --> CfgMgr
    Engine --> OSTools
    AppCtrl --> WinOS
    EmailSvc --> WinOS
    SocialMgr --> WinOS
    OSTools --> WinOS
    Engine --> Mascot
    Engine --> Bubble
    Engine --> TTS
    TTS --> Mascot
```

---

## 2. Hands-Free Conversational Lifecycle (VAD & Acoustic Interlock)

Natural human-to-human hands-free voice loop without requiring mouse clicks:

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant Mic as Microphone (Conexant ISST)
    participant VAD as Voice Detector (ContinuousVoiceListener)
    participant Chat as Chat Window (ChatWindow)
    participant Engine as AI Engine (AgentEngine)
    participant TTS as Neural Speech (TTSEngine)
    participant Mascot as 3D Mascot (DesktopMascot)

    User->>Mic: Speaks utterance ("NexA, check my latest emails")
    Mic->>VAD: Streams 16-bit 16kHz PCM audio buffers
    Note over VAD: RMS energy exceeds threshold + prepends 300ms ring buffer
    VAD->>Chat: Emits speech_started signal
    Chat->>Mascot: Sets state to Thinking (listening posture)
    
    User->>Mic: Finishes sentence and pauses (~0.9s silence)
    Note over VAD: Silence duration exceeds timeout threshold
    VAD->>VAD: Packages accumulated PCM into Wave file
    VAD->>Chat: Emits speech_completed(wav_path)
    
    Note over VAD,Chat: Acoustic Interlock: Listening pauses so NexA never hears itself
    Chat->>Engine: Dispatches audio to Gemini 2.5 Flash
    Engine->>Engine: Transcribes, determines intent, routes to Nila
    Engine->>Chat: Generates conversational response
    Chat->>TTS: Synthesizes fluent speech
    TTS->>Mascot: Drives lip-sync mouth opening & eye gestures
    TTS-->>User: Plays audio through speaker
    
    Note over TTS,VAD: Speech finishes -> Voice listener automatically re-engages
    Chat->>VAD: Calls resume_listening()
    Note over VAD: Ready to hear user's next response hands-free!
```

---

## 3. Universal Desktop App Automation & Macro Execution Flow

How NexA connects to Windows software controls and executes learned macros:

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant Chat as Chat Window
    participant Engine as NexA Engine
    participant Artin as Artin (Family Member)
    participant AppCtrl as App Controller (AppController)
    participant WinUIA as Windows (UIAutomationClient)
    participant TargetApp as Target Software (Notepad, Excel, etc.)

    User->>Chat: "Open Notepad and type my meeting notes"
    Chat->>Engine: Forwards user intent
    Engine->>Artin: Delegates task to Artin (Desktop Automation specialist)
    Artin->>AppCtrl: Calls execute_workflow(notepad_quick_note)
    
    alt UI Inspection Needed
        AppCtrl->>WinUIA: Calls inspect_app_ui(Notepad)
        WinUIA-->>AppCtrl: Returns element tree (Buttons, Menus, Edit fields, bounds)
    end

    AppCtrl->>TargetApp: Step 1: Launch/Focus application (launch)
    AppCtrl->>TargetApp: Step 2: Send keystrokes & type substituted text (type)
    AppCtrl->>TargetApp: Step 3: Send shortcut key Ctrl+S (hotkey)
    TargetApp-->>AppCtrl: Operation completed
    AppCtrl-->>Engine: Reports success across 3 executed steps
    Engine-->>Chat: Speaks and presents completion summary to User
```

---

## 4. Module Responsibility Matrix

- **`main.py`**: Application bootstrap, signal routing, Windows dark/light mode detector, and accent color synchronization.
- **`agent/engine.py`**: Central coordinator, system prompt composition, key rotation management, and tool dispatcher.
- **`agent/voice_detector.py`**: Real-time continuous voice activity detection, dynamic noise tracking, silence timeout, and acoustic interlock.
- **`agent/family/manager.py`**: Family ecosystem director, prompt delegator, XP and level progression manager.
- **`agent/family/app_controller.py`**: Windows UI Automation client, control inspector, and macro workflow learner/executor.
- **`agent/integrations/email_client.py`**: Secure IMAP4 SSL / SMTP email client with priority categorization and auditory readout.
- **`agent/integrations/social_manager.py`**: Instagram viral Reels planner, caption and hashtag creator, and browser session launcher.
- **`agent/integrations/config_manager.py`**: Auto-detects host system defaults and persistently saves configurations in `data/integrations_config.json`.
- **`agent/key_manager.py`**: Gemini API key pool manager with zero-loss HTTP 429 failover.
- **`agent/memory.py`**: Persistent long-term memory store across restarts.
- **`agent/learning.py`**: Autonomous failure reflection engine synthesizing permanent corrective rules.
- **`agent/multi_ai.py`**: Peer AI collaborator interfacing with cloud LLMs (GPT-4o, Claude) and offline models (Ollama, LM Studio).
- **`agent/tts.py`**: Gemini Neural Speech synthesizer with offline Windows SAPI fallback.
- **`ui/mascot.py`**: Procedural vector renderer for 8 distinct 3D avatars, dynamic gaze tracking, and lip-sync.
- **`ui/chat_window.py`**: Cyberpunk glassmorphic chat interface with hands-free conversation button `🗣️`.
- **`ui/settings_window.py`**: 6-tab unified control center (Persona & Family, API Keys, Memory, Learning, Companion, Multi-AI).

</div>

<div lang="en" dir="ltr" align="left">

# Multimodal Hardware Integration (Microphone, Webcam & Speaker) 🎙️📷🔊

**English Version** | [نسخه فارسی](Multimodal-Hardware.fa.md)

One of the standout capabilities of Nova Desktop AI Agent is its native integration with Windows physical hardware. This transforms the agent from a purely textual assistant into an interactive, multimodal companion.

---

## 1. 🎙️ Microphone Voice Input

- **Dedicated Module:** `agent/audio_recorder.py` built on `PyQt6.QtMultimedia`.
- **How It Operates:**
  1. Clicking the microphone button (`🎙️`) in the chat input toolbar immediately initiates recording from the system's default audio input device.
  2. The button transforms into a pulsing red icon (`⏹️`), updating the status badge to `🎤 Recording audio...`, while the desktop mascot shifts into an attentive posture.
  3. Clicking the button again stops recording and saves uncompressed audio in `Wave (.wav)` format.
  4. The audio payload is passed directly to the Gemini 2.5 Flash model as a native audio part (`types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")`).
- **Core Benefit:** Gemini 2.5 Flash understands human speech natively (including Persian, English, and multilingual mixing) without requiring slow or error-prone third-party speech-to-text (STT) services.

---

## 2. 📷 Webcam Vision

- **Dedicated Module:** `capture_webcam` function in `agent/tools.py` using optimized `OpenCV` (`cv2.VideoCapture`).
- **Access Paths:**
  - **Quick Camera Button (`📷`):** Takes a crisp snapshot and attaches it to the prompt bar with a preview tag.
  - **Desktop Mascot Context Menu:** Right-click the desktop pet ➔ Select "📷 دیدن از وب‌کم و تحلیل".
  - **Autonomous AI Invocation:** If the user asks *"Look through the webcam and describe what I am holding"*, Gemini automatically dispatches the `capture_webcam` tool.
- **Use Cases:** User presence and face recognition, analyzing physical documents held to the lens, inspecting desk hardware, and real-world visual guidance.

---

## 3. 🔊 Speaker Voice Output (TTS)

- **Dedicated Module:** `agent/tts.py` utilizing the native Windows Speech API (`SAPI.SpVoice`).
- **Key Features:**
  - **Asynchronous Execution:** Non-blocking background speech synthesis ensures zero UI micro-stutters.
  - **Persona Voice Matching:**
    - Active Male Persona (**Arya**): Employs Microsoft David Desktop voice.
    - Active Female Persona (**Ava**): Employs Microsoft Zira Desktop voice.
  - **Pre-Speech Cleansing:** Markdown syntax, code blocks, raw URLs, and emojis are cleanly stripped before audio generation.
  - **Instant Mute Toggle:** The `🔊`/`🔇` button in the chat interface allows one-click muting at any time.

---

## 4. Hardware I/O Capability Matrix

| Channel | Physical Hardware | Module | Data Format |
| :--- | :--- | :--- | :--- |
| **Voice Input** | Laptop / Headset Microphone | `AudioRecorder` | Audio Wave (.wav) 16-bit PCM |
| **Vision Input (Webcam)** | Integrated or USB Webcam | `cv2.VideoCapture` | JPEG Image Frame (640x480+) |
| **Vision Input (Desktop)** | Display Monitor | `Pillow ImageGrab` | Fullscreen PNG Screenshot |
| **Audio Output** | System Speakers / Headphones | `SAPI.SpVoice` | Audio PCM Stream |

</div>

<div lang="en" dir="ltr" align="left">

# Multimodal Hardware Integration: Mic, Webcam & Speaker 🎙️📷🔊

[نسخه فارسی](Multimodal-Hardware.fa.md) | **English Version**

A defining capability of the **NexA AI** Desktop Agent by **Rahkar Electronic Sahand** ([irres.ir](https://irres.ir)) is real-time bidirectional communication with physical PC hardware peripherals (microphone, webcam, display, and speakers).

---

## 1. 🎙️ Microphone Voice Input: Manual & Continuous VAD

NexA provides two distinct audio capture pathways:

### 1.1. Continuous Hands-Free VAD (`ContinuousVoiceListener`):
- **Module:** `agent/voice_detector.py`
- **Workflow:**
  1. Continually reads 30ms audio chunks in the background without UI blocking.
  2. Measures RMS signal energy. When energy exceeds the threshold, speech state activates, prepending a 300ms pre-speech ring buffer so beginning syllables are preserved.
  3. When speech stops and a silence timeout (500ms to 1000ms) elapses, the WAV recording finalizes and routes immediately to the Gemini multimodal API.
  4. An acoustic interlock inhibits microphone recording while the agent speaks through the speakers to avoid acoustic feedback.
  5. Configurable between **Always-Listening** dialogue mode and **Wake-Word** gated activation.

### 1.2. Manual Push-to-Talk (`AudioRecorder`):
- **Module:** `agent/audio_recorder.py` powered by `PyQt6.QtMultimedia`.
- Triggered by clicking the microphone button (`🎙️`) in the chat input bar.
- Streams uncompressed 16-bit 16kHz WAV audio directly to the multimodal model.

---

## 2. 📷 Webcam Vision

- **Module:** `capture_webcam` in `agent/tools.py` via `OpenCV` (`cv2.VideoCapture`).
- **Access Channels:**
  - **Quick Camera Button (`📷`):** Captures high-res frames and attaches them as chat previews.
  - **Mascot Context Menu:** Option "📷 Capture Webcam & Analyze".
  - **Autonomous Tool Triggering:** Invoked when users ask visual questions about their desk or physical environment.

---

## 3. 🔊 Speaker Voice Output (TTS)

- **Module:** `agent/tts.py` utilizing the Windows native voice engine (`SAPI.SpVoice`).
- **Highlights:**
  - **Asynchronous Playback:** Non-blocking speech synthesis without UI lag.
  - **Family Voice Persona Matching:**
    - Male personas (NexaMehr, SamYar, Artin, Parsa): paired with male SAPI voices (`Microsoft David`).
    - Female personas (NexaNoo, Nila, Tara): paired with female SAPI voices (`Microsoft Zira`).
  - **Markdown & Code Filtering:** Strips code blocks, URLs, and emojis prior to speech synthesis for natural pronunciation.
  - **Instant Mute Toggle:** A dedicated mute button (`🔊`/`🔇`) controls audio output.

---

## 4. Hardware Channel Comparison

| Channel | Hardware Device | Supporting Module | Data Format | Operational Mode |
| :--- | :--- | :--- | :--- | :--- |
| **Continuous Voice (VAD)** | Microphone | `ContinuousVoiceListener` | WAV 16kHz PCM | Hands-free autonomous |
| **Manual Audio Input** | Microphone | `AudioRecorder` | WAV 16kHz PCM | User push-to-talk button |
| **Visual Input (Webcam)** | Integrated/USB Camera | `cv2.VideoCapture` | JPEG Image Frame | On-demand snapshots |
| **Visual Input (Desktop)** | Display Monitor | `Pillow ImageGrab` | Fullscreen PNG | Telemetry and inspection |
| **Audio Output (TTS)** | Speakers / Headphones | `SAPI.SpVoice` | Audio PCM Stream | Asynchronous & gender-matched |

</div>

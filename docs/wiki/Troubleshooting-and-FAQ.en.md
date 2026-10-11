<div lang="en" dir="ltr" align="left">

# Troubleshooting & FAQ ❓🛠️

**English Version** | [نسخه فارسی](Troubleshooting-and-FAQ.fa.md)

This diagnostic guide provides solutions to common questions, device troubleshooting, and quick setup instructions for Nova Desktop AI Agent.

---

## 1. Google Gemini API Keys

### FAQ: Where do I obtain a free Gemini API key?
**Answer:** Visit [Google AI Studio](https://aistudio.google.com/), sign in with your Google account, and click **Get API key**. Copy the key and add it to the Settings window (`⚙️`) under the «🔑 API Pool» tab.

### FAQ: What happens if an API key exhausts its quota?
**Answer:** Nova seamlessly transitions to the next available key in the pool with zero downtime and complete chat history retention. It is recommended to register 2-3 keys in the pool for uninterrupted operation.

---

## 2. Webcam Vision Troubleshooting

### Issue: The agent returns "Webcam device is not available".
**Remedy:**
1. Verify no other software (Zoom, Teams, Discord, browser tab) is holding an exclusive hardware lock on the camera.
2. In Windows Settings (`Settings > Privacy & Security > Camera`), ensure **Let desktop apps access your camera** is toggled ON.
3. If using an external USB camera, verify the cable connection.

---

## 3. Microphone Audio Recording

### Issue: Voice prompt is not captured when pressing the mic button.
**Remedy:**
1. Check Windows Sound Settings (`Settings > System > Sound`) to verify that the default microphone input device is operational and receiving signal.
2. Verify Windows microphone permissions under `Settings > Privacy > Microphone`.
3. The mic button turns red `⏹️` when recording; clicking it again finalizes and attaches the audio file.

---

## 4. Speaker Voice Output (TTS)

### FAQ: How do I mute or unmute the assistant?
**Answer:** Click the speaker icon (`🔊`) in the chat input toolbar. It toggles to `🔇` (muted) instantly. You can also test speech in the Settings window under the «👤 Persona & Voice» tab.

---

## 5. Running the Test Suite

To verify that all tools, key rotation mechanisms, memory stores, and multimodal hooks are operating correctly:
```powershell
python -m pytest tests/ -v
```
*(All 35 automated tests should pass with green checkmarks).*

</div>

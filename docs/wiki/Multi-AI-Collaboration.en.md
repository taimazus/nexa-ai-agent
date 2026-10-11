<div lang="en" dir="ltr" align="left">

# Multi-AI Collaboration, Peer Code Review & Self-Improvement 🌐🧠

[نسخه فارسی](Multi-AI-Collaboration.fa.md) | **English Version**

Nova is not isolated to a single neural architecture. Through its **Multi-AI Peer Collaboration Engine**, it can consult, cross-examine, and learn from external peer models (OpenAI, Anthropic Claude, DeepSeek, or local offline Ollama models). It actively submits its reasoning and code for critique, discovers subtle runtime traps, and permanently distills peer insights into its continuous learning registry.

---

## 1. Supported Peer Providers

Nova integrates with standard API contracts across multiple cloud and local inference runtimes:

| Provider | Recommended Models | Endpoint Protocol | Authentication / Cost |
| :--- | :--- | :--- | :--- |
| **Ollama** | `llama3`, `mistral`, `deepseek-r1`, `qwen2.5-coder` | `http://localhost:11434/api/chat` | **100% Free & Local** (Zero external API keys required) |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `o1-preview` | `/v1/chat/completions` REST API | Requires OpenAI API key |
| **Anthropic Claude** | `claude-3-5-sonnet-20241022` | `/v1/messages` REST API | Requires Anthropic API key |
| **DeepSeek** | `deepseek-chat`, `deepseek-reasoner` | `/v1/chat/completions` REST API | Requires DeepSeek API key |
| **OpenRouter** | Multi-model aggregator (Gemini, Llama, Mistral) | `/api/v1/chat/completions` | Requires OpenRouter API key |
| **Gemini Peer** | `gemini-2.5-flash`, `gemini-2.0-pro` | Native `google-genai` client | Secondary Gemini key for adversarial checks |

---

## 2. Core Operational Capabilities

### 1. Peer Code Review & Bug Discovery (`review_code_with_peer`)
Before running sensitive automation or when crafting complex scripts, Nova can dispatch code to a peer AI:
- Uncovering hidden runtime exceptions and OS-specific edge cases.
- Detecting permission mismatches, injection vectors, and command escaping issues in Windows.
- Pinpointing resource leaks and missing stream disposal.

### 2. Knowledge Distillation into Permanent Rules (`learn_from_peer_ai`)
Whenever a peer AI provides an actionable correction or architectural improvement:
- Nova distills the feedback into a concise golden rule.
- Persists it with the tag `[درس آموخته‌شده از هوش مصنوعی همکار]` in [data/learnings.json](file:///c:/Users/Taimazus/Desktop/MyAgent/data/learnings.json).
- Injects it into future system instructions so the agent never repeats that class of error.

### 3. Continuous Self-Improvement Protocol (`run_self_improvement`)
Nova can initiate an autonomous self-audit loop:
- Submits its operational history and current rules to a supervisory peer AI.
- Identifies cognitive or technical blind spots.
- Saves structured self-improvement plans into [data/peer_insights.json](file:///c:/Users/Taimazus/Desktop/MyAgent/data/peer_insights.json).

---

## 3. UI Settings Walkthrough

1. Open the Chat window and click the gear icon `⚙️`.
2. Navigate to Tab 6: **«🌐 هوش‌های مصنوعی همکار»** (Peer AI Providers).
3. Select your desired provider from the dropdown:
   - For **Ollama**, no API key is required (ensure Ollama is running locally).
   - For others, enter your API key in the password field.
4. Click **«🧪 تست اتصال (Ping)»** to test round-trip latency and connectivity.
5. Click **«🔍 باگ‌یابی و بازبینی کد»** to execute a peer review.
6. Click **«💡 ثبت مستقیم این تحلیل به عنوان قانون یادگیری»** to immediately commit the advice into Nova's permanent learned rules.

</div>

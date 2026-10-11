<div lang="en" dir="ltr" align="left">

# Persistent Memory & Continuous Self-Learning 🧠📈

**English Version** | [نسخه فارسی](Self-Learning-and-Memory.fa.md)

Two fundamental shortcomings of conventional AI assistants are "session amnesia upon reboot" and "repeating the same execution errors". Nova Desktop AI Agent addresses both challenges using a **persistent key-value long-term memory engine** and a **continuous failure-reflection self-learning engine**.

---

## 1. Continuous Self-Learning Engine

- **Module:** `agent/learning.py`
- **Persistence Store:** [data/learnings.json](file:///c:/Users/Taimazus/Desktop/MyAgent/data/learnings.json)
- **Autonomous Learning Loop:**
  1. **Failure Interception:** When a PowerShell command or Python execution produces a non-zero exit code or `stderr` exception, Nova captures the raw error.
  2. **Automated Reflection:** The engine analyzes the root cause and synthesizes an actionable **"Golden Corrective Rule"**.
  3. **Context Injection:** All active learned rules are injected into Gemini's system instruction on every prompt turn:
     ```markdown
     ### Lessons Learned from Past Mistakes (Golden Corrective Rules):
     - [PowerShell]: In Windows, paths containing whitespace must be wrapped in quotes.
     - [Python]: Package xyz is not installed; verify with pip list first.
     ```
  4. **User Correction Ingestion:** If the user notes *"That didn't work"* or *"Never use this flag again"*, the `record_learning` tool permanently stores the rule.

---

## 2. Persistent Long-Term Memory Store

- **Module:** `agent/memory.py`
- **Persistence Store:** [data/memory.json](file:///c:/Users/Taimazus/Desktop/MyAgent/data/memory.json)
- **Agent Autonomous Memory Tools:**
  - `remember_fact(key, value, category)`: Permanently writes user preferences, project paths, or personal facts.
  - `recall_facts(query)`: Semantic keyword search across saved facts.
  - `forget_fact(key)`: Removes obsolete or requested entries.
- **Boot Injection:** Stored facts are automatically supplied in the system prompt on every session initialization, surviving application restarts and system reboots.

---

## 3. Memory & Learning Inspection in Settings

You maintain full control over what Nova remembers and learns:
1. Open the Settings window (`⚙️`).
2. **«🧠 Long-Term Memory» Tab:** View the entire memory catalog, add new key-value facts manually, search, or delete outdated entries.
3. **«📈 Self-Learning from Errors» Tab:** Inspect the table of auto-generated rules, view error triggers, search topics, or clear records.

</div>

# Local LLM ChatBot

A lightweight, extensible Python chat assistant that talks to local Large Language Models (LLMs) via **[Ollama](https://ollama.com/)**.  
It supports dynamic model selection with fallback, (basic) streaming, conversational history, prompt engineering utilities, and optional quality‑repair hooks.

> Run fully offline once models are pulled. Ideal for prototyping agents, internal tools, or experimentation without sending data to external APIs.

---

## Table of Contents
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage Examples](#usage-examples)
- [Model Management (Ollama)](#model-management-ollama)
- [Prompt & Quality Tips](#prompt--quality-tips)
- [Streaming Mode](#streaming-mode)
- [Fallback Logic](#fallback-logic)
- [Extending (HTTP API Option)](#extending-http-api-option)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Key Features
- ✅ Local inference via Ollama CLI
- ✅ Automatic model fallback (e.g. `llama3` → `mistral` → `phi3`)
- ✅ Optional on‑demand model pull (ensure model present)
- ✅ Conversation history merging
- ✅ Blocking or basic streaming execution
- ✅ Configurable generation parameters (temperature, top_p, num_predict)
- ✅ Debug logging toggle
- ✅ Prompt sanitation (removal of control chars)
- 🧪 Optional post‑generation “repair” function (quality enforcement)
- 🧩 Designed to be easily upgraded to Ollama’s HTTP API

---

## Architecture Overview

```
+----------------------+
|   Your App / UI      |  (CLI script, FastAPI, Discord bot, etc.)
+-----------+----------+
            |
            v
     +--------------+
     | ollama_client|  <-- model selection, fallback, prompt build,
     +------+-------+      history injection, streaming, timeouts
            |
            v
     +---------------+
     |  Ollama Daemon|  <-- runs / pulls local LLMs
     +---------------+
            |
         Local Disk (model blobs)
```

Main entrypoint function: `ask_ollama(...)` inside `ollama_client.py`.

---

## Quick Start

```bash
# Pull at least one model
ollama pull phi3

# Test the model quickly
ollama run phi3 "Hello"

# Run a Python one‑liner using the client
python -c "from ollama_client import ask_ollama; print(ask_ollama('Give me a friendly greeting.', model='phi3'))"
```

---

## Requirements
| Component | Minimum |
|-----------|---------|
| Python    | 3.9+    |
| Ollama    | 0.11.0+ |
| Disk      | Depends on models (e.g. mistral ≈ 4.4 GB) |
| RAM       | 8 GB minimum for small models; more recommended for larger |

---

## Installation

```bash
git clone https://github.com/<YOUR_USER>/<YOUR_REPO>.git
cd <YOUR_REPO>

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# (Add dependencies if you introduce any; base version may have none)
pip install -r requirements.txt  # if the file exists
```

Check Ollama:
```bash
ollama --version
ollama list
```

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `OLLAMA_MODEL` | Preferred default model | `phi3` |
| `OLLAMA_FALLBACK_MODELS` | Comma list for fallback | `mistral,phi3` |
| `SYSTEM_PROMPT` | System role / behavior | `"You are a concise helpful assistant."` |
| `GEN_TEMPERATURE` | Sampling temperature | `0.6` |
| `GEN_TOP_P` | Nucleus sampling | `0.9` |
| `GEN_NUM_PREDICT` | Max tokens (-1 = model default) | `256` |
| `OLLAMA_TIMEOUT` | Inference inactivity timeout (seconds) | `180` |
| `OLLAMA_DEBUG` | Debug logs (1/0) | `1` |

Example:
```bash
export OLLAMA_MODEL=phi3
export OLLAMA_FALLBACK_MODELS=mistral,phi3
export SYSTEM_PROMPT="You are an accurate, polite assistant. Avoid hallucination."
export GEN_TEMPERATURE=0.5
export GEN_TOP_P=0.9
export OLLAMA_DEBUG=1
```

---

## Usage Examples

### 1. Basic Call
```python
from ollama_client import ask_ollama
print(ask_ollama("Give me a short inspirational sentence.", model="phi3"))
```

### 2. With Conversation History
```python
history = [
    {"role": "user", "content": "Hi, who are you?"},
    {"role": "assistant", "content": "I'm a local AI assistant running on your machine."}
]
response = ask_ollama(
    "Summarize your capabilities in one sentence.",
    model="phi3",
    history=history,
    use_history=True
)
print(response)
```

### 3. Streaming Mode
```python
resp = ask_ollama(
    "Explain what a hash map is in simple terms.",
    model="phi3",
    stream=True
)
```

### 4. Enforcing Non‑Short Output (Prompt Engineering)
```python
ask_ollama(
    "Write a helpful 3-sentence explanation of recursion. Do not answer in bullet points.",
    model="mistral"
)
```

### 5. Fallback Model Behavior
If `OLLAMA_MODEL=llama3` but it is not downloaded and `OLLAMA_FALLBACK_MODELS=mistral,phi3`:
- The client will pick the first installed model from that list automatically.

---

## Model Management (Ollama)

| Action | Command |
|--------|---------|
| List installed models | `ollama list` |
| Pull a model | `ollama pull mistral` |
| Run a quick test | `ollama run phi3 "Hello"` |
| Remove a model | `ollama rm mistral` |
| Daemon logs (Linux systemd) | `journalctl -u ollama -f` |

First run with a new model may be slow (download + unpack). Subsequent runs are much faster.

---

## Prompt & Quality Tips

| Problem | Tip |
|---------|-----|
| Very short answers | Explicit length: “Answer in at least 2 sentences.” |
| Hallucinations | Add: “If unsure, say you are unsure.” |
| Unstable formatting | Provide exact template scaffold in prompt. |
| Language drift | System prompt: “Always answer in English.” |
| Repetition | Lower temperature / add “Avoid repeating phrases.” |

Few‑shot example:
```python
history = [
  {"role": "user", "content": "Give me a cheerful greeting."},
  {"role": "assistant", "content": "Hello! I hope you're having a great day. How can I assist you?"},
  {"role": "user", "content": "Another one."},
  {"role": "assistant", "content": "Hi there! Ready whenever you are—what would you like to explore today?"}
]
ask_ollama("Give me a third unique greeting.", model="phi3", history=history, use_history=True)
```

---

## Streaming Mode
Current streaming is a simple stdout line reader (not token‑level structured events). It helps avoid “blank screen” during longer generations or downloads.  
To upgrade:
- Use Ollama HTTP API (`/api/generate` with `stream: true`) and parse JSON events.
- Pipe them through WebSocket for a web UI.

---

## Fallback Logic
1. Try preferred model (`OLLAMA_MODEL` or provided argument).
2. If not installed:
   - Iterate `OLLAMA_FALLBACK_MODELS`.
   - Use the first installed one.
3. If none installed:
   - Optionally auto‑pull the preferred model (controlled by the client).
4. Proceed with generation.

---

## Extending (HTTP API Option)
To gain:
- True parameter control (temperature, top_k, repeat_penalty, stop tokens)
- Proper streaming events
- Structured JSON

Sketch:
```python
import requests, json

def http_generate(prompt, model="mistral"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.6, "top_p": 0.9}
    }
    r = requests.post(url, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    return data.get("response")
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Long silence, no answer | Model downloading | Run `ollama pull model` first; show progress |
| Empty / nonsense output | Weak small model | Use better prompt or switch to `mistral` / `llama3` |
| Timeout error | Slow hardware / large model | Increase `OLLAMA_TIMEOUT` |
| CLI not found | PATH issue | Reinstall or add Ollama to PATH |
| High RAM usage | Large model loaded | Use a smaller model (phi3, qwen2:0.5b) |
| Mixed language output | Not constrained | Add explicit language rule in system prompt |
| Very short answer | Under-specified prompt | Add minimum length requirement |

Debug:
```bash
export OLLAMA_DEBUG=1
python -c "from ollama_client import ask_ollama; ask_ollama('Test', model='phi3')"
```

---

## Roadmap
- [ ] Native HTTP API client (JSON streaming)
- [ ] Web UI (FastAPI + WebSocket)
- [ ] Response cache layer
- [ ] Automatic quality repair module (config-toggle)
- [ ] Benchmark script for latency & token throughput
- [ ] Multi-user session isolation
- [ ] Prompt template registry

---

## Contributing
1. Fork the repo  
2. Create a feature branch: `git checkout -b feat/improve-stream`  
3. Commit with clear messages  
4. Open a Pull Request describing changes (screenshots if UI-related)  

---

## License
Choose and add a license file (e.g. MIT or Apache-2.0).  
Example (MIT):
Create `LICENSE` file with MIT template text.

---

## Disclaimer
Local models may hallucinate or produce inaccurate information. Always verify critical outputs before use in production or decision pipelines.

---

## Quick Copy/Paste Recap
```bash
ollama pull phi3
python -c "from ollama_client import ask_ollama; print(ask_ollama('Say something encouraging.', model='phi3'))"
```

---

Happy hacking! 🚀
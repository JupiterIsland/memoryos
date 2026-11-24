# QUICKSTART — Zero to First Result in Under 5 Minutes ($0.00)

**MemoryOS // Jupiter Studio (`v2.1.2`)** runs on the **Python 3.11+ standard library** (`0` third-party `pip` packages, `0` `ffmpeg` install required, `0` Docker containers, and a hard **`$0.00` spend lock** enabled by default).

---

## 1. Clone & Launch (60 Seconds, Zero API Keys Required)

### Windows (PowerShell)
```powershell
git clone https://github.com/JupiterIsland/memoryos.git
cd memoryos
Copy-Item .env.example .env
python -B apps/jupiter_studio.py
```

### Linux / macOS
```bash
git clone https://github.com/JupiterIsland/memoryos.git
cd memoryos
cp .env.example .env
python3 -B apps/jupiter_studio.py
```

Your browser opens **[http://127.0.0.1:7860](http://127.0.0.1:7860)** automatically.

> **Verify everything on your hardware first (optional, ~45s):**
> ```bash
> python -B verify.py          # Full 21-module compile, NEON 5/5, 164 unit tests & EWC benchmarks
> python -B verify.py --quick  # 3-second smoke check
> ```

---

## 2. Get Value Immediately at $0.00 (No Credit Card Needed)

Even before pasting a single cloud API key, three workflows work out of the box:

1. **Teach Frank (`Operations` stage):**
   - Type a prompt in the chat box and watch **Frank-v1** (`3,246`-parameter continual-learning CPU router, `0 MB` GPU VRAM) classify intent live.
   - Open the left sidebar -> **Memory Vault** -> pin a project rule into local SQLite (`QuietAdvisorDB.sqlite`) so every model recalls it automatically.
2. **Run Free Open-Weight Models (`HF Models` stage):**
   - Click **HF Models** in the top bar to browse live **[huggingface.co/models](https://huggingface.co/models)** with automatic **8 GB GPU VRAM fit badges**.
   - If you have **[Ollama](https://ollama.com)** running locally (`http://127.0.0.1:11434`), click **`Ollama Pull ($0)`** on any quantized GGUF model (for example `unsloth/gemma-4-E2B-it-GGUF` or `unsloth/Qwen3.5-4B-GGUF`) to run it locally at **$0.00**.
3. **Index a Video Clip (`Cloud Video` stage — Zero `ffmpeg` Needed):**
   - Click **Cloud Video** -> **Choose Video (`.mp4` / `.mov` / `.webm`)**.
   - Your browser samples keyframes natively on `<canvas>` (no `ffmpeg` or `opencv` required), MemoryOS's CPU frame-delta gate drops static duplicate frames, and only real scene cuts are sent to your selected vision model:
     - **100% Local Free ($0.00):** `Gemma 4 E2B GGUF (HF Local Vision · $0.00)` via Ollama (`ollama pull hf.co/unsloth/gemma-4-E2B-it-GGUF`).
     - **0 MB Local VRAM Cloud:** Set `TOKENLAB_API_KEY` (AMD Token Lab) or `GEMINI_API_KEY` in `.env` and restart.

---

## 3. Optional Cloud Keys & The Hard `$0.00` Spend Lock

Open `.env` and fill in **only** the providers you actually want to use (leave placeholders untouched — Jupiter Studio ignores `your-...-here` values safely):

| Capability | `.env` Variable | Cost & Safety Notes |
| :--- | :--- | :--- |
| **Local Open-Weight Chat & Vision** | *(None — uses `OLLAMA_HOST=http://127.0.0.1:11434`)* | **$0.00** local execution |
| **Hugging Face Hub & Router** | `HF_TOKEN=hf_...` | Public Hub search + GGUF pulls are **$0.00** without a token |
| **AMD Token Lab (Chat & Video VLM)** | `TOKENLAB_API_KEY=tl-...` | `0 MB` local VRAM cloud offload |
| **Fast Cloud Coding** | `GROQ_API_KEY` / `CEREBRAS_API_KEY` / `OPENROUTER_API_KEY` | Optional OpenAI-compatible failover |
| **Cloud Video Generation** | `GEMINI_API_KEY` / `FAL_KEY` / `REPLICATE_API_TOKEN` | Saved to `./outputs/video` (`MEMORYOS_VIDEO_OUTPUT_DIR`). **Blocked by default** via `MEMORYOS_VIDEO_MAX_JOB_USD="0.00"` until you intentionally raise the cap. |

---

## 4. Common Newcomer Troubleshooting

* **`Microsoft Store Python stub detected` on Windows:** Install standard Python `3.11+` from [python.org/downloads](https://www.python.org/downloads/) and check **"Add Python to PATH"**.
* **`Port 7860 is already in use`:** Launch on another port with `python -B apps/jupiter_studio.py --port 7861`.
* **`Blocked before cloud dispatch: exceeds hard spend cap $0.00 USD`:** That is the Glass Box safety lock protecting your bill. Keep `MEMORYOS_VIDEO_MAX_JOB_USD="0.00"` for strict zero spend, or raise `MEMORYOS_VIDEO_MAX_JOB_USD` in `.env` (and `Cap $` in the UI) when you intentionally want a paid cloud render.

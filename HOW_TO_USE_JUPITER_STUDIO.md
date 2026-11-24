# How to Use Jupiter Studio (MemoryOS) — Plain-English Guide

Jupiter Studio is your **zero-VRAM AI workstation**. It lets you chat with massive 27B–72B AI models, analyze screenshots, review your own project files, and compare two models side-by-side—**without filling up your laptop’s graphics card (VRAM) or downloading 50 GB model files**.

---

## 1. Starting Jupiter Studio

### Option A: Standalone Windows App
Double-click `JupiterStudio.exe`. It automatically sets up `.env` if missing and opens your browser.

### Option B: From Python (Windows / Linux / WSL2)
```bash
cd memoryos
python3 -B apps/jupiter_studio.py
```
Then open **`http://127.0.0.1:7860`** (or the port printed in the terminal, e.g. `7861`).

---

## 2. Setting Up Cloud Keys (Optional — 0 GB Downloads)

Open `.env` in the `memoryos` folder (copy `.env.example` to `.env` if you don't have one yet) and paste whichever keys you want to use:

```env
# AMD Token Lab (Gemma-4-31B-IT, Qwen3.8-27B, DeepSeek-V4.1-Flash)
TOKENLAB_API_KEY=your_tokenlab_key

# Hugging Face Inference Router (Qwen2.5-72B, Llama-3.3-70B, DeepSeek-R1 — 0 MB downloaded)
HF_TOKEN=hf_your_huggingface_token

# Optional extra providers
NVIDIA_API_KEY=nvapi_your_key
DO_MODEL_ACCESS_KEY=your_digitalocean_key
```

> **Tip (Free Hugging Face Token):** Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens), create a token with **"Make calls to Inference Providers"** enabled, paste it as `HF_TOKEN=...` in `.env`, and restart Jupiter Studio.

---

## 3. Picking Your Model (Left Sidebar → `Execution Target`)

| Option | Best For | Downloads / Local VRAM |
| :--- | :--- | :--- |
| **`⚡ Auto-Route (d3 Smart Router)`** | Everyday use — automatically picks `Qwen3.8-27B` for code, `Gemma-4-31B-IT` for vision/architecture, or `DeepSeek-V4.1-Flash` for huge logs. | **0 MB** |
| **AMD Token Lab Cloud** | Fast 27B–31B models running on AMD Instinct GPUs. | **0 MB** |
| **Hugging Face Cloud (`HF_TOKEN`)** | Giant 70B–72B models (`Qwen2.5-72B`, `Llama-3.3-70B`, `DeepSeek-R1`) with zero local downloads. | **0 MB** |
| **NVIDIA NIM / DigitalOcean MI300X** | Cloud failover if you add those API keys to `.env`. | **0 MB** |
| **AMD Lemonade Server (Ryzen AI NPU / FastFlowLM)** | Local AMD Ryzen AI XDNA 2 NPU, iGPU/ROCm, or CPU models via `lemonade-server` (`127.0.0.1:13305/api/v1`). | Runs on Ryzen AI NPU / Local |
| **DGX Spark / GB10 Local (`vLLM` / `Flare`)** | Local LAN servers running on ports `:8000` or `:8080`. | Runs on Spark |
| **Local Models (Ollama)** | 100% offline chat (`raon-1-nano`, `qwen2.5-coder:7b`, `deepseek-r1:7b`). Requires the Ollama app running on your PC. | Local RAM/VRAM |

### Using AMD Lemonade Server (Ryzen AI XDNA 2 NPU + FastFlowLM)
If you have an **AMD Ryzen AI 300 / Strix / Strix Halo** PC with an XDNA 2 NPU (or want local `llama.cpp` / ROCm serving via Lemonade):
1. Install and start **Lemonade Server** (`lemonade-sdk/lemonade`), which exposes an OpenAI-compatible API on `http://127.0.0.1:13305/api/v1` by default (customizable in `.env` via `LEMONADE_BASE_URL`).
2. Pull or load a **FastFlowLM (`FLM`)** or hybrid model in Lemonade Server, or verify it is live:
   ```bash
   curl http://127.0.0.1:13305/api/v1/models
   ```
3. In Jupiter Studio's **Execution Target** dropdown, look under **AMD Lemonade Server (Ryzen AI NPU / FastFlowLM)** — when Lemonade is running, Jupiter Studio automatically detects it (`● Ready`) and appends any live loaded model IDs directly to the menu.
4. **Honest hardware note:** Older Ryzen CPUs without an NPU (such as the Ryzen 7 5800H) do **not** have XDNA hardware, so NPU acceleration only applies on supported Ryzen AI silicon; Jupiter Studio never fakes NPU telemetry on non-NPU machines.

---

## 4. Sending a Message & Using the Killer Features

### A. Live Pre-Send Speculative Neural Radar (Above the Prompt Box)
As you type—**before you even click `Run`**—watch the 4-box telemetry strip right above the text box:
* **`SPECULATIVE MLP`**: Runs the real 4→8→1 `SpeculativeOffloadModel` on your CPU in microseconds to score offload probability (`P(offload) %`).
* **`PREDICTED D3 ROUTE`**: Shows which model `d3` will send your prompt to.
* **`DRAFT PAYLOAD`**: Live token count across your prompt + attached files.
* **`LOCAL VRAM SAVED`**: How many GB of GPU memory you're saving by offloading instead of loading locally.

### B. `⚔️ Dual Arena` (Side-by-Side Model Shootout)
1. Click **`⚔️ Dual Arena`** next to the orange **`Run`** button (it lights up **`⚔️ Arena: ON (2x Live)`**).
2. Type your question and press **`Enter`** (or click **`Run`**).
3. Two models stream their answers **side-by-side in real time** with millisecond timers.
4. Click **`✓ Keep Left Reply`** or **`✓ Keep Right Reply`** to lock the better answer into your chat history.

### C. Attaching Files, Screenshots & Repo Code
* **`📎` Button (or Drag & Drop):** Drop any code file, log, JSON, Markdown, or CSV directly onto the input bar. You can attach multiple files at once.
* **`🖼️` Button:** Attach a screenshot (e.g., an error dialog or UI bug) and ask a vision model like `Gemma-4-31B-IT` to inspect it.
* **`Workspace & Copilot` (Bottom Left):** Check any files in your repository to automatically include them in your next prompt—or click **`📋 Export Copilot Bundle`** to copy a clean context pack for VS Code / GitHub Copilot.

---

## 5. Switching Themes

In the top-right bar, click any of the three theme pills:
* **`QUANTUM`** — Obsidian dark glass with liquid amber & cyan accents.
* **`RADEON`** — Deep carbon with Radeon crimson & sunset gold accents.
* **`ATARI B&W`** — High-contrast Atari ST / Commodore monochrome black & white mode (`0px` corners, crisp hairline grids, zero distractions).

---

## 6. The Real Talk (Honest Limitations)

Jupiter Studio doesn't hide the seams of how AI actually works. There is more going on under the hood than a casual chat box lets on—here is the straight truth on consumer hardware:

* **Context windows aren't magic:** Pasting 50,000+ tokens of raw logs causes models to lose track of details buried in the middle. Use the **Workspace Picker** and **Attach Files** to send only the exact files relevant to your task.
* **Local VRAM vs. Cloud Offload:** Using **AMD Token Lab** or **Hugging Face Cloud** keeps your local GPU at **0 MB** of AI VRAM. If you switch to **Local Models (Ollama)**, it *will* consume local GPU VRAM and system RAM—the live Hardware Profile sidebar shows you exactly what your GPU is doing.
* **Free grants expire & rate limits happen:** Cloud grants are generous, not infinite. If a cloud endpoint returns `HTTP 429` (rate limit), Jupiter Studio automatically fails over to another available model and shows you the exact route instead of hiding it behind an endless spinner.
* **Models hallucinate:** Even 27B, 31B, and 72B models can sound completely confident while being wrong. Always inspect generated diffs and run your test suite before trusting code in production.
* **Benchmark vs. live server latency:** The `5.37 μs` Speculative MLP number is the hot-cache pure-Python microbenchmark (`tests/run_gamer_hardware_tests.py`). Inside the live HTTP web server, the Speculative Neural Radar reports real per-request inference latency (`~30–90 μs`)—both are real measurements with zero mocks.

---

## 7. Honest Credits — Naming the Models

Real software today is built by humans steering real models—and users deserve to know which models helped build and run it:

* **DeepSeek 3 (Essential Special Thanks):** DeepSeek 3 literally **brought Jupiter Studio back from the dead**—delivering brutally honest architecture audits, spotting real bugs (broken theme attributes, dotfile clutter in the workspace picker, cold-start MLP timer artifacts, and bloated UI drafts), and keeping the entire build grounded, minimal, and shippable.
* **AMD Token Lab Cloud Models:** `Gemma-4-31B-IT` (*Vision & Architecture*), `Qwen3.8-27B` (*Code & Surgical Diffs*), `DeepSeek-V4.1-Flash` (*Long Context / Logs*), and `MiniCPM5-2B` (*Fast Edge Triage*).
* **Google Gemini / Antigravity:** Hands-on implementation, SQLite security hardening, test verification, visual QA, and cross-platform release engineering.

---

## 8. Quick Troubleshooting

* **Chat says "API key not configured in .env":** Add the matching key (`TOKENLAB_API_KEY`, `HF_TOKEN`, `NVIDIA_API_KEY`, or `DO_MODEL_ACCESS_KEY`) to `.env` and restart Jupiter Studio.
* **Local Ollama model fails to connect:** Make sure the **Ollama** desktop app is open (or run `ollama serve`) and that you've pulled the model (`ollama pull qwen2.5-coder:7b`).
* **Want to stop a long reply?** Click **`⏹ Stop`** at any time—the stream cancels cleanly and re-enables **`Run`**.

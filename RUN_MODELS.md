# Do This To Run Models in Jupiter Studio

A plain-English cheat sheet for starting each local server, downloading models, and enabling cloud providers.

> **Tip:** Inside Jupiter Studio, pick any model in the top dropdown and click **`? Run`** — Studio automatically detects whether the model is already installed or shows the exact command to copy and run.

---

## 1. Built-In Helper (`Frank-v1` — Zero Setup)
Works immediately out of the box with **0 MB GPU VRAM** and no internet:
1. Select **`Frank-v1`** (`studio:frank`) in the top model dropdown (or use `auto:d3`).
2. Open the **FrankHub** tab in the left rail to pin memories, teach Frank phrasing, or run **Audit Frank**.

---

## 2. AMD Lemonade Server (Local NPU / GGUF / FastFlowLM)
**Important (Windows + WSL2):** Run Jupiter Studio **natively on Windows** (`python apps/jupiter_studio.py` or `JupiterStudio.exe`) so it talks directly to Lemonade on `http://127.0.0.1:13305`.

### Start Lemonade Server:
```powershell
lemonade-server serve --port 13305
```
*(If calling Lemonade from WSL2 instead of native Windows, bind all interfaces: `lemonade-server serve --port 13305 --host 0.0.0.0`.)*

### Download a Model into Lemonade:
```powershell
lemonade-server pull Qwen3.5-4B-GGUF
lemonade-server pull Bonsai-4B-gguf
```
Once downloaded, refresh Jupiter Studio — your downloaded Lemonade models automatically appear as **`(Lemonade Live)`** under **AMD Lemonade Server** in the dropdown.

---

## 3. Ollama (Local Free Models & Downloadable Presets)
Presets shown in the dropdown (like `bonsai-2:27b`, `gemma4:12b`, `inkling-2-mini`, `raon-1-nano`, `qwen2.5-coder:7b`) are **downloadable on demand**.

### Step 1 — Start Ollama:
Open the Ollama desktop app, or run:
```powershell
ollama serve
```

### Step 2 — Download any preset you want to use:
```powershell
# Lightweight / fast coding (fits easily on 8 GB GPUs)
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:1.5b

# Other downloadable presets in Jupiter Studio
ollama pull gemma4:12b
ollama pull bonsai-2:27b
ollama pull inkling-2-mini
ollama pull raon-1-nano
ollama pull deepseek-r1:7b
```

### Step 3 — Optional: Build the Local `frank` Ollama Model:
```powershell
cd "C:\path\to\memoryos"
ollama create frank -f memory/models/Modelfile.frank
```
Refresh Jupiter Studio and select **`frank:latest (Ollama Installed)`** or any pulled model.

---

## 4. Cloud Servers (0 MB Local VRAM)
No model downloads required — add the key(s) you want to `.env` in the repo root and restart Jupiter Studio:

| Provider | Add to `.env` | Best For |
| :--- | :--- | :--- |
| **AMD Token Lab** | `TOKENLAB_API_KEY=...` | Architecture (`DeepSeek-V4.1-Flash`), Design/Vision (`Gemma-4-31B-IT`), Diffs (`Qwen3.8-27B`), Cheap BG (`MiniCPM5-2B`) |
| **Google Gemini API** | `GEMINI_API_KEY=...` | Interactions API v1 (`gemini-4-argon`, `gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemma-4-31b-it`) |
| **OpenAI Cloud** | `OPENAI_API_KEY=sk-...` | Flagship & Vision (`gpt-4o`), Fast & Low Cost (`gpt-4o-mini`) |
| **Groq** | `GROQ_API_KEY=gsk_...` | Ultra-fast coding (`llama-3.3-70b-versatile`) |
| **OpenRouter** | `OPENROUTER_API_KEY=sk-or-...` | Multi-model gateway (DeepSeek, Gemma, Qwen) |
| **Cerebras** | `CEREBRAS_API_KEY=...` | Fast wafer-scale inference (`llama-3.3-70b`, `qwen-3-32b`) |
| **Hugging Face Router** | `HF_TOKEN=hf_...` | Serverless open-weights (`Qwen2.5-72B`, `DeepSeek-R1`) |
| **NVIDIA NIM / Brev** | `NVIDIA_API_KEY=nvapi-...` | NIM hosted models |
| **DigitalOcean MI300X** | `DO_MODEL_ACCESS_KEY=...` | Serverless AMD MI300X |

---

## 5. DGX Spark / Local vLLM / NVIDIA Flare (32 GB+ Unified / Workstation)
```bash
# Local vLLM on port 8000
vllm serve Qwen/Qwen3.8-Flash-Next --port 8000
```
Set `VLLM_BASE_URL` or `FLARE_BASE_URL` in `.env` if running on another host/port.

---

## 6. Running Jupiter Studio Natively on Windows (Recommended)
Running natively on Windows connects **Ollama**, **Lemonade Server**, **NVIDIA GPU telemetry**, and **Cloud Providers** simultaneously:

```powershell
cd "C:\path\to\memoryos"
python -B apps/jupiter_studio.py
```
Or launch the built standalone app:
```powershell
.\dist\JupiterStudio\JupiterStudio.exe --workspace "C:\path\to\memoryos"
```
Then open **`http://127.0.0.1:7860`**.

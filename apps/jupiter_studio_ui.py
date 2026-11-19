"""Jupiter Studio UI — Original Dark Workstation Look (restored from af08106)."""

STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Jupiter Studio // Hybrid AI Workstation</title>
<link rel="icon" type="image/png" href="/assets/jupiter_studio_icon.png" />
<style>
  :root {
    --bg: #07090f;
    --sidebar-bg: #0d121f;
    --card-bg: rgba(255, 255, 255, 0.03);
    --border: #1e2942;
    --border-highlight: #334155;
    --orange: #ff6a00;
    --orange-hover: #e05d00;
    --cyan: #38bdf8;
    --green: #10b981;
    --purple: #a855f7;
    --red: #ef4444;
    --text: #f1f5f9;
    --muted: #94a3b8;
    --code-bg: #05070d;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    display: flex;
    height: 100vh;
    overflow: hidden;
  }
  .sidebar {
    width: 340px;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 18px 16px;
    gap: 16px;
    overflow-y: auto;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .logo-badge {
    width: 38px; height: 38px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 9px;
    box-shadow: 0 0 16px rgba(255, 106, 0, 0.25);
  }
  .brand h1 { font-size: 15px; font-weight: 700; letter-spacing: 0.5px; display: flex; align-items: center; }
  .brand p { font-size: 11px; color: var(--muted); }
  .rc-pill {
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 0.8px;
    padding: 1px 5px;
    border-radius: 4px;
    background: rgba(237, 28, 36, 0.18);
    border: 1px solid rgba(237, 28, 36, 0.45);
    color: #ff4d4f;
    margin-left: 6px;
  }
  .section-title {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin-bottom: 6px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
  }
  .hw-val { font-size: 13px; font-weight: 600; color: var(--cyan); margin-top: 3px; }
  .select-box, input, textarea {
    width: 100%;
    background: #090d17;
    border: 1px solid var(--border);
    color: #fff;
    padding: 9px 11px;
    border-radius: 6px;
    font-size: 13px;
    outline: none;
    transition: border 0.15s;
  }
  .select-box:focus, input:focus, textarea:focus { border-color: var(--cyan); }
  .main {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: radial-gradient(circle at top right, #11182c 0%, var(--bg) 60%);
  }
  .chat-header {
    height: 52px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    background: rgba(13, 18, 31, 0.7);
    backdrop-filter: blur(8px);
  }
  .chat-header .badge {
    font-size: 11px;
    padding: 4px 8px;
    border-radius: 4px;
    font-family: monospace;
    background: rgba(56, 189, 248, 0.12);
    color: var(--cyan);
    border: 1px solid rgba(56, 189, 248, 0.3);
  }
  .chat-log {
    flex: 1;
    padding: 24px 28px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
  .msg {
    max-width: 82%;
    padding: 14px 18px;
    border-radius: 10px;
    line-height: 1.55;
    font-size: 14px;
    word-break: break-word;
  }
  .msg.user {
    align-self: flex-end;
    background: #182238;
    border: 1px solid #283758;
    color: #fff;
  }
  .msg.assistant {
    align-self: flex-start;
    background: #0c1221;
    border: 1px solid var(--border);
    border-left: 3px solid var(--cyan);
    width: 84%;
  }
  .meta-tag {
    display: inline-block;
    font-size: 11px;
    font-family: monospace;
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 8px;
  }
  .meta-local { background: rgba(16, 185, 129, 0.15); color: var(--green); border: 1px solid var(--green); }
  .meta-cloud { background: rgba(255, 106, 0, 0.15); color: var(--orange); border: 1px solid var(--orange); }
  .meta-auto { background: rgba(56, 189, 248, 0.15); color: var(--cyan); border: 1px solid var(--cyan); }
  .meta-error { background: rgba(239, 68, 68, 0.15); color: var(--red); border: 1px solid var(--red); }
  
  /* Reasoning box */
  .reasoning-box {
    margin-bottom: 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px dashed var(--border-highlight);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    color: var(--muted);
  }
  .reasoning-box summary {
    cursor: pointer;
    font-weight: 600;
    color: var(--cyan);
    outline: none;
    user-select: none;
  }
  .reasoning-content {
    margin-top: 8px;
    white-space: pre-wrap;
    font-family: monospace;
    font-size: 11.5px;
    max-height: 240px;
    overflow-y: auto;
  }

  /* Markdown body */
  .md-body p { margin-bottom: 8px; }
  .md-body p:last-child { margin-bottom: 0; }
  .md-body h1, .md-body h2, .md-body h3 { margin: 12px 0 6px; color: #fff; }
  .md-body ul, .md-body ol { margin-left: 20px; margin-bottom: 8px; }
  .md-body code {
    background: rgba(255, 255, 255, 0.08);
    padding: 2px 5px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 12.5px;
  }
  .code-block-container {
    position: relative;
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    margin: 10px 0;
    overflow: hidden;
  }
  .code-header {
    background: rgba(255, 255, 255, 0.03);
    border-bottom: 1px solid var(--border);
    padding: 5px 12px;
    font-size: 11px;
    font-family: monospace;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .code-copy-btn {
    background: transparent;
    border: 1px solid var(--border-highlight);
    color: var(--muted);
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 4px;
    cursor: pointer;
    transition: 0.15s;
  }
  .code-copy-btn:hover { color: #fff; border-color: var(--cyan); }
  .code-block-container pre {
    padding: 12px;
    overflow-x: auto;
    font-family: "Cascadia Code", Consolas, "Courier New", monospace;
    font-size: 12.5px;
    line-height: 1.45;
  }
  .code-block-container code { background: none; padding: 0; }

  /* Input area */
  .input-bar-wrapper {
    padding: 14px 24px;
    background: var(--sidebar-bg);
    border-top: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .attachment-preview {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .attachment-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(56, 189, 248, 0.15);
    border: 1px solid var(--cyan);
    color: #fff;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
  }
  .attachment-chip .remove-btn {
    cursor: pointer;
    color: var(--muted);
    font-weight: 700;
  }
  .attachment-chip .remove-btn:hover { color: var(--red); }
  .input-bar {
    display: flex;
    gap: 10px;
    align-items: flex-end;
  }
  .input-actions {
    display: flex;
    gap: 8px;
  }
  .btn {
    background: var(--orange);
    color: #fff;
    border: none;
    padding: 10px 18px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
    transition: 0.15s;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .btn:hover { background: var(--orange-hover); }
  .btn-stop {
    background: var(--red);
  }
  .btn-stop:hover { background: #dc2626; }
  .btn-secondary {
    background: #182238;
    color: var(--text);
    border: 1px solid var(--border);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: 0.15s;
  }
  .btn-secondary:hover { border-color: var(--cyan); color: #fff; }
  .btn-icon {
    padding: 10px;
    background: #141b2c;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--muted);
    cursor: pointer;
  }
  .btn-icon:hover { color: #fff; border-color: var(--cyan); }
  
  /* Workspace panel */
  .workspace-file-list {
    max-height: 140px;
    overflow-y: auto;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: #090d17;
    padding: 6px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 11.5px;
  }
  .file-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 3px 6px;
    border-radius: 4px;
    cursor: pointer;
    user-select: none;
  }
  .file-item:hover { background: rgba(255, 255, 255, 0.05); }
  .file-item input[type="checkbox"] { width: auto; }
  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: #0f172a;
    border: 1px solid var(--green);
    color: #fff;
    padding: 10px 18px;
    border-radius: 6px;
    font-size: 13px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.5);
    z-index: 9999;
    opacity: 0;
    transition: opacity 0.2s ease;
    pointer-events: none;
  }
  .toast.show { opacity: 1; }

  /* ── QUANTUM LATTICE & 3-THEME ENGINE ──────────────────────────────── */
  :root {
    --bg: #07090e;
    --sidebar-bg: #0c101a;
    --panel: rgba(13, 17, 26, 0.92);
    --card-bg: rgba(18, 24, 38, 0.88);
    --border: rgba(255, 106, 0, 0.22);
    --border-highlight: rgba(255, 106, 0, 0.45);
    --text: #f3f6fc;
    --muted: #8b9bb4;
    --orange: #ff6a00;
    --cyan: #00f0ff;
    --green: #10b981;
    --red: #f43f5e;
    --code-bg: #05070d;
  }
  .main {
    background: radial-gradient(circle at top right, rgba(0, 240, 255, 0.06) 0%, var(--bg) 55%);
  }

  /* RADEON CARBON THEME */
  html[data-studio-theme="radeon"] {
    --bg: #090608;
    --sidebar-bg: #120b0f;
    --panel: rgba(20, 11, 16, 0.94);
    --card-bg: rgba(30, 16, 23, 0.90);
    --border: rgba(237, 28, 36, 0.34);
    --border-highlight: rgba(255, 176, 0, 0.55);
    --orange: #ed1c24;
    --cyan: #ffb000;
    --text: #faf5f7;
    --muted: #b098a3;
  }
  html[data-studio-theme="radeon"] .main {
    background: radial-gradient(circle at top right, rgba(237, 28, 36, 0.11) 0%, var(--bg) 55%);
  }

  /* DAYLIGHT CERAMIC THEME (100% High-Contrast Light Mode) */
  html[data-studio-theme="daylight"] {
    --bg: #f5f2eb;
    --sidebar-bg: #ebe6dc;
    --panel: #ebe6dc;
    --card-bg: #ffffff;
    --border: #d4cdc0;
    --border-highlight: #b5ac9c;
    --text: #161614;
    --muted: #5e5a52;
    --orange: #e84800;
    --cyan: #0b6e58;
    --green: #0a7a4b;
    --red: #c81e1e;
    --code-bg: #18181b;
  }
  html[data-studio-theme="daylight"] .main {
    background: var(--bg);
  }
  html[data-studio-theme="daylight"] .sidebar {
    background: var(--sidebar-bg);
    box-shadow: 2px 0 12px rgba(20, 18, 14, 0.06);
  }
  html[data-studio-theme="daylight"] .card {
    background: #ffffff;
    border-color: var(--border);
    box-shadow: 0 1px 3px rgba(20, 18, 14, 0.05);
  }
  html[data-studio-theme="daylight"] .select-box,
  html[data-studio-theme="daylight"] input,
  html[data-studio-theme="daylight"] textarea,
  html[data-studio-theme="daylight"] .workspace-file-list {
    background: #ffffff;
    color: #161614;
    border-color: var(--border-highlight);
  }
  html[data-studio-theme="daylight"] .workspace-file-item:hover {
    background: #f0ece3;
  }
  html[data-studio-theme="daylight"] .btn-secondary,
  html[data-studio-theme="daylight"] .btn-icon {
    background: #ffffff !important;
    color: #161614 !important;
    border: 1px solid var(--border-highlight) !important;
  }
  html[data-studio-theme="daylight"] .btn-secondary:hover,
  html[data-studio-theme="daylight"] .btn-icon:hover {
    background: #e3ddd1 !important;
    border-color: #161614 !important;
  }
  html[data-studio-theme="daylight"] .chat-header,
  html[data-studio-theme="daylight"] .input-bar-wrapper {
    background: #ebe6dc;
    border-color: var(--border);
  }
  html[data-studio-theme="daylight"] .msg.assistant {
    background: #ffffff;
    color: #161614;
    border: 1px solid var(--border);
    border-left: 3px solid var(--orange);
    box-shadow: 0 2px 8px rgba(20, 18, 14, 0.05);
  }
  html[data-studio-theme="daylight"] .msg.user {
    background: #1a1a18;
    border-color: #1a1a18;
    color: #faf8f3;
  }
  html[data-studio-theme="daylight"] .md-body h1,
  html[data-studio-theme="daylight"] .md-body h2,
  html[data-studio-theme="daylight"] .md-body h3 {
    color: #161614;
  }
  html[data-studio-theme="daylight"] .md-body code {
    background: #ebe6dc;
    color: #161614;
  }
  html[data-studio-theme="daylight"] .code-block-container {
    color: #f1f5f9;
  }
  html[data-studio-theme="daylight"] .theme-pill-group {
    background: #ded8cc;
    border-color: var(--border-highlight);
  }
  html[data-studio-theme="daylight"] .spec-radar {
    background: #e5dfd3;
    border-top: 1px solid var(--border-highlight);
  }
  html[data-studio-theme="daylight"] .radar-cell {
    background: #ffffff;
    border: 1px solid var(--border);
  }
  html[data-studio-theme="daylight"] .btn-arena {
    background: #ffffff;
    color: #0b6e58;
    border-color: #0b6e58;
  }
  html[data-studio-theme="daylight"] .btn-arena.active {
    background: linear-gradient(135deg, #e84800, #c81e1e);
    color: #ffffff;
    border-color: #c81e1e;
  }
  html[data-studio-theme="daylight"] .arena-col {
    background: #faf8f3;
  }
  html[data-studio-theme="daylight"] .reasoning-box {
    background: #f5f2eb;
    color: #4a4740;
  }

  .sidebar {
    backdrop-filter: blur(16px);
    box-shadow: 4px 0 30px rgba(0, 0, 0, 0.35);
  }
  .chat-header {
    position: relative;
    overflow: hidden;
    border-bottom: 1px solid var(--border);
  }
  #quantum-canvas {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    opacity: 0.65;
  }
  .chat-header > * { position: relative; z-index: 2; }

  .theme-pill-group {
    display: inline-flex;
    border: 1px solid var(--border);
    border-radius: 7px;
    overflow: hidden;
    background: rgba(0,0,0,0.28);
  }
  .theme-pill-btn {
    padding: 4px 9px;
    font-size: 10px;
    font-family: monospace;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: var(--muted);
    background: transparent;
    border: none;
    cursor: pointer;
    text-transform: uppercase;
  }
  .theme-pill-btn.active {
    background: var(--orange);
    color: #fff;
  }

  /* ── LIVE PRE-SEND SPECULATIVE NEURAL RADAR BAR ────────────────────── */
  .spec-radar {
    display: grid;
    grid-template-columns: 1.3fr 1.3fr 0.9fr 1.1fr;
    gap: 8px;
    padding: 7px 16px;
    background: linear-gradient(90deg, rgba(255,106,0,0.12) 0%, rgba(0,240,255,0.09) 100%);
    border-top: 1px solid var(--border);
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
  }
  .radar-cell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 4px 10px;
    background: rgba(0, 0, 0, 0.28);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
  }
  .radar-k { font-size: 9.5px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
  .radar-v { font-weight: 700; color: var(--cyan); white-space: nowrap; }
  .radar-v.hot { color: var(--orange); }
  .radar-v.ok { color: var(--green); }

  /* ── DUAL-MODEL SPLIT ARENA ────────────────────────────────────────── */
  .btn-arena {
    background: rgba(0, 240, 255, 0.12);
    color: var(--cyan);
    border: 1px solid var(--cyan);
    border-radius: 8px;
    padding: 8px 12px;
    font-weight: 700;
    font-size: 11.5px;
    font-family: monospace;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
    transition: all 0.15s;
  }
  .btn-arena.active {
    background: linear-gradient(135deg, var(--orange), #e11d48);
    color: #fff;
    border-color: #fff;
    box-shadow: 0 0 14px rgba(255, 106, 0, 0.45);
  }
  .arena-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    width: 100%;
  }
  .arena-col {
    background: rgba(0, 0, 0, 0.24);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 0;
  }
  .arena-keep-btn {
    align-self: flex-start;
    margin-top: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-family: monospace;
    font-weight: 700;
    background: rgba(16, 185, 129, 0.15);
    color: var(--green);
    border: 1px solid var(--green);
    border-radius: 5px;
    cursor: pointer;
  }
  .arena-keep-btn:hover { background: var(--green); color: #000; }

</style>
</head>
<body>
  <!-- Sidebar -->
  <div class="sidebar">
    <div class="brand">
      <div class="logo-badge" title="Jupiter Studio RC1 — Powered by AMD Token Lab">
        <img src="/assets/jupiter_studio_icon.png" alt="Jupiter Studio" width="40" height="40" style="width:40px; height:40px; border-radius:10px; display:block; object-fit:cover;" />
      </div>
      <div>
        <h1>Jupiter Studio <span class="rc-pill">RC1</span></h1>
        <p>MemoryOS Hybrid Workstation // AMD Token Lab</p>
      </div>
    </div>

    <!-- Execution Target Selector -->
    <div>
      <div class="section-title">Execution Target</div>
      <select class="select-box" id="target-selector" onchange="onTargetChange()">
        <option value="auto:d3" selected>⚡ Auto-Route (d3 Smart Router)</option>
        <optgroup label="AMD Token Lab Cloud (Zero VRAM)" id="opt-tokenlab">
          <option value="cloud:Gemma-4-31B-IT">Gemma-4-31B-IT (Tactical / Vision)</option>
          <option value="cloud:Qwen3.8-27B">Qwen3.8-27B (Code Architecture)</option>
          <option value="cloud:DeepSeek-V4.1-Flash">DeepSeek-V4.1-Flash (1M Context)</option>
          <option value="cloud:MiniCPM5-2B">MiniCPM5-2B (Fast Scout)</option>
        </optgroup>
        <optgroup label="NVIDIA NIM / Brev Cloud" id="opt-nvidia">
          <option value="nv:qwen/qwen2.5-coder-32b-instruct">Qwen-2.5-Coder-32B (NVIDIA NIM)</option>
          <option value="nv:meta/llama-3.3-70b-instruct">Llama-3.3-70B (NVIDIA NIM)</option>
          <option value="nv:qwen/qwen2.5-7b-instruct">Qwen-2.5-7B (NVIDIA NIM)</option>
        </optgroup>
        <optgroup label="DigitalOcean Serverless (AMD MI300X)" id="opt-digitalocean">
          <option value="do:Qwen/Qwen2.5-Coder-32B-Instruct">Qwen-2.5-Coder-32B (MI300X)</option>
          <option value="do:meta-llama/Llama-3.3-70B-Instruct">Llama-3.3-70B (MI300X)</option>
        </optgroup>
        <optgroup label="Hugging Face Cloud (Zero Download / HF_TOKEN)" id="opt-hf">
          <option value="hf:Qwen/Qwen2.5-72B-Instruct">Qwen2.5-72B-Instruct (HF Router)</option>
          <option value="hf:meta-llama/Llama-3.3-70B-Instruct">Llama-3.3-70B-Instruct (HF Router)</option>
          <option value="hf:deepseek-ai/DeepSeek-R1">DeepSeek-R1 (HF Router)</option>
          <option value="hf:Qwen/Qwen2.5-Coder-32B-Instruct">Qwen2.5-Coder-32B-Instruct (HF Router)</option>
        </optgroup>
        <optgroup label="DGX Spark / GB10 Local (vLLM / Flare)" id="opt-spark">
          <option value="vllm:Qwen/Qwen3.8-Flash-Next">Qwen3.8-Flash-Next (Local vLLM :8000)</option>
          <option value="vllm:deepseek-ai/DeepSeek-V4.1-Flash">DeepSeek-V4.1-Flash (Local vLLM :8000)</option>
          <option value="flare:Qwen3.8-Flash-Next">Qwen3.8-Flash-Next (NVIDIA Flare :8080)</option>
          <option value="flare:DeepSeek-V4.1-Flash">DeepSeek-V4.1-Flash (NVIDIA Flare :8080)</option>
        </optgroup>
        <optgroup label="Local Models (100% Free / Ollama)" id="opt-ollama">
          <option value="ollama:raon-1-nano">raon-1-nano (Game-Loop 1.5B / 256K)</option>
          <option value="ollama:qwen2.5-coder:1.5b">qwen2.5-coder:1.5b (Ultra-Fast)</option>
          <option value="ollama:qwen2.5-coder:7b">qwen2.5-coder:7b (Local Accuracy)</option>
          <option value="ollama:deepseek-r1:7b">deepseek-r1:7b (Reasoning)</option>
          <option value="ollama:deepseek-r1:8b">deepseek-r1:8b (Deep Thinking)</option>
        </optgroup>
      </select>
    </div>

    <!-- Hardware Profile -->
    <div>
      <div class="section-title">Hardware Profile</div>
      <div class="card" id="hw-card">
        <div style="font-size:11px; color:var(--muted);">ACTIVE GPU</div>
        <div class="hw-val" id="hw-name">Detecting...</div>
        <div style="font-size:11px; color:var(--muted); margin-top:6px;">VRAM USAGE</div>
        <div class="hw-val" id="hw-vram">0 / 0 MB</div>
      </div>
    </div>

    <!-- MemoryOS Policy Telemetry -->
    <div>
      <div class="section-title">MemoryOS Policy Telemetry</div>
      <div class="card">
        <div style="display:flex; justify-content:space-between; font-size:12px;">
          <span>CPU Skip Gate (d3)</span>
          <span style="color:var(--green); font-weight:700;" id="pol-gate">0.091 ms</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; margin-top:6px;">
          <span>Local AI VRAM Saved</span>
          <span style="color:var(--cyan); font-weight:700;" id="pol-vram">100.0%</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; margin-top:6px;">
          <span>Active Advisor Cards</span>
          <span style="color:var(--orange); font-weight:700;" id="pol-cards">7 Active</span>
        </div>
      </div>
    </div>

    <!-- Workspace Context & Copilot Handoff -->
    <div>
      <div class="section-title">
        <span>Workspace & Copilot</span>
        <span style="font-size:10px; color:var(--cyan);" id="ws-branch">beta</span>
      </div>
      <div class="card" style="display:flex; flex-direction:column; gap:8px;">
        <div style="font-size:11px; color:var(--muted);">Select project files to attach to context:</div>
        <div class="workspace-file-list" id="workspace-file-list">
          <div style="color:var(--muted); padding:4px;">Scanning files...</div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:11px; color:var(--muted);" id="ws-file-count">0 files selected</span>
          <button class="btn-secondary" style="padding:4px 8px; font-size:11px;" onclick="selectCoreFiles()">Core Files</button>
        </div>
        <button class="btn-secondary" style="width:100%; display:flex; align-items:center; justify-content:center; gap:6px; background:#1e2942; border-color:#38bdf8;" onclick="exportCopilotBundle()">
          📋 Export Copilot Bundle
        </button>
      </div>
    </div>
  </div>

  <!-- Main Chat Workstation -->
  <div class="main">
    <div class="chat-header">
      <canvas id="quantum-canvas"></canvas>
      <div style="display:flex; align-items:center; gap:10px;">
        <span class="badge" id="chat-mode-badge">AUTO-ROUTE (d3)</span>
        <span style="font-size:12px; color:var(--muted);" id="chat-target-desc">Quantum Lattice // 0.091ms Zen 3 Gate + 5.37μs Speculative MLP</span>
      </div>
      <div style="display:flex; gap:8px; align-items:center;">
        <div class="theme-pill-group" title="Switch Studio Surface Theme">
          <button class="theme-pill-btn active" data-t="quantum" onclick="setStudioTheme('quantum')">QUANTUM</button>
          <button class="theme-pill-btn" data-t="radeon" onclick="setStudioTheme('radeon')">RADEON</button>
          <button class="theme-pill-btn" data-t="daylight" onclick="setStudioTheme('daylight')">DAYLIGHT</button>
        </div>
        <button class="btn-secondary" onclick="clearChat()">🗑 Clear Chat</button>
      </div>
    </div>

    <div class="chat-log" id="chat-log">
      <div class="msg assistant">
        <div class="meta-tag meta-auto">SYSTEM READY</div>
        <div class="md-body">
          <p>Welcome to <b>Jupiter Studio // MemoryOS Hybrid Workstation</b>!</p>
          <p>Your studio is connected and ready:</p>
          <ul>
            <li><b>⚡ d3 Smart Router:</b> Automatically routes code, vision, and light queries across cloud grants with zero local VRAM penalty.</li>
            <li><b>📁 Workspace & Copilot Handoff:</b> Select project files above and click <i>Export Copilot Bundle</i> to copy structured context directly into Copilot / IDE agents.</li>
            <li><b>🖼 Multimodal Vision:</b> Drag and drop or attach screenshots to analyze bugs and UI frames directly.</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Live Pre-Send Speculative Neural Radar (runs 5.37us MLP on every keystroke) -->
    <div class="spec-radar" id="spec-radar-bar">
      <div class="radar-cell" style="position:relative; overflow:hidden;">
        <div id="rad-mlp-bar" style="position:absolute; left:0; top:0; bottom:0; width:88%; background:linear-gradient(90deg, rgba(255,106,0,0.18), rgba(0,240,255,0.14)); transition:width 0.2s ease; pointer-events:none;"></div>
        <span class="radar-k" style="position:relative; z-index:1;">Speculative MLP</span>
        <span class="radar-v hot" id="rad-mlp" style="position:relative; z-index:1;">P(offload) 88.0% · 5.37 μs</span>
      </div>
      <div class="radar-cell">
        <span class="radar-k">Predicted d3 Route</span>
        <span class="radar-v" id="rad-route">d3 → Gemma-4-31B-IT</span>
      </div>
      <div class="radar-cell">
        <span class="radar-k">Draft Payload</span>
        <span class="radar-v" id="rad-tok">~1 token</span>
      </div>
      <div class="radar-cell">
        <span class="radar-k">Local VRAM Saved</span>
        <span class="radar-v ok" id="rad-vram">18.5 GB saved (0 MB used)</span>
      </div>
    </div>
    <!-- Input Bar -->
    <div class="input-bar-wrapper" id="input-drop-zone" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)" ondrop="handleDrop(event)">
      <div class="attachment-preview" id="attachment-preview" style="display:none; flex-wrap:wrap; gap:6px;"></div>
      <div class="input-bar">
        <input type="file" id="image-file-input" accept="image/*" style="display:none;" onchange="handleImageSelected(event)" />
        <input type="file" id="doc-file-input" multiple style="display:none;" onchange="handleFilesSelected(event)" />
        <button class="btn-icon" id="upload-file-btn" title="Upload Files (Code, Logs, JSON, Markdown, CSV, Text)" onclick="document.getElementById('doc-file-input').click()">
          📎
        </button>
        <button class="btn-icon" id="upload-image-btn" title="Attach Screenshot or Image" onclick="document.getElementById('image-file-input').click()">
          🖼️
        </button>
        <textarea id="prompt-input" rows="2" placeholder="Ask anything or drag & drop files here... (Ctrl+Enter to send)" onkeydown="if(event.ctrlKey && event.key==='Enter') sendPrompt()"></textarea>
        <div class="input-actions">
          <button class="btn-arena" id="btn-arena" onclick="toggleDualArena()" title="Stream 2 models side-by-side in a live split-screen shootout">⚔️ Dual Arena</button>
          <button class="btn" id="run-btn" onclick="sendPrompt()">Run</button>
          <button class="btn btn-stop" id="stop-btn" style="display:none;" onclick="stopGeneration()">⏹ Stop</button>
        </div>
      </div>
    </div>
  </div>

  <div class="toast" id="toast">Copied to clipboard!</div>

<script>
let currentAbortController = null;
let currentAttachedImage = null;
let chatHistory = [];
let workspaceFiles = [];

// Lightweight safe Markdown renderer
function renderMarkdown(text) {
  if (!text) return "";
  // Escape raw HTML first
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Code blocks: ```lang ... ```
  html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, function(match, lang, code) {
    const language = lang || "text";
    const cleanCode = code.trim();
    const encoded = encodeURIComponent(cleanCode);
    return `<div class="code-block-container">
      <div class="code-header">
        <span>${language}</span>
        <button class="code-copy-btn" onclick="copyCode(this, '${encoded}')">📋 Copy</button>
      </div>
      <pre><code>${cleanCode}</code></pre>
    </div>`;
  });

  // Inline code: `code`
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Bold & Italic
  html = html.replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
  html = html.replace(/\*([^*]+)\*/g, "<i>$1</i>");

  // Headings
  html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
  html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");
  html = html.replace(/^# (.*$)/gim, "<h1>$1</h1>");

  // Bullet points
  html = html.replace(/^\s*-\s+(.*$)/gim, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");

  // Line breaks to paragraphs
  const paragraphs = html.split(/\n{2,}/);
  return paragraphs.map(p => {
    if (p.startsWith("<div") || p.startsWith("<ul") || p.startsWith("<h")) return p;
    return `<p>${p.replace(/\n/g, "<br/>")}</p>`;
  }).join("");
}

function copyCode(btn, encoded) {
  const code = decodeURIComponent(encoded);
  navigator.clipboard.writeText(code).then(() => {
    const orig = btn.innerText;
    btn.innerText = "✓ Copied";
    setTimeout(() => { btn.innerText = orig; }, 2000);
  });
}

function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.innerText = msg;
  toast.classList.add("show");
  setTimeout(() => { toast.classList.remove("show"); }, 3000);
}

async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    
    // Hardware
    document.getElementById("hw-name").innerText = data.gpu.device_name || "CPU Mode";
    const memSuffix = data.gpu.is_unified_memory ? " Unified" : "";
    document.getElementById("hw-vram").innerText = `${data.gpu.used_vram_mb} / ${data.gpu.total_vram_mb} MB${memSuffix} (${data.gpu.utilization_pct}% Load)`;
    
    // Policy
    if (data.policy) {
      document.getElementById("pol-gate").innerText = `${data.policy.cpu_gate_ms} ms`;
      document.getElementById("pol-vram").innerText = `${data.policy.local_vram_saved_pct}%`;
      document.getElementById("pol-cards").innerText = `${data.policy.active_cards} Active`;
    }

    // Provider Badges on Dropdown
    const tlConf = data.cloud?.amd_tokenlab?.configured;
    const nvConf = data.cloud?.nvidia_brev?.configured;
    const doConf = data.cloud?.digitalocean_mi300x?.configured;

    const optTL = document.getElementById("opt-tokenlab");
    if (optTL) optTL.label = `AMD Token Lab Cloud ${tlConf ? "● Ready" : "○ (Not Configured)"}`;
    
    const optNV = document.getElementById("opt-nvidia");
    if (optNV) optNV.label = `NVIDIA NIM / Brev Cloud ${nvConf ? "● Ready" : "○ (Set Key in .env)"}`;

    const optDO = document.getElementById("opt-digitalocean");
    if (optDO) optDO.label = `DigitalOcean Serverless ${doConf ? "● Ready" : "○ (Set Key in .env)"}`;

  } catch(e) {
    console.error("Status load error:", e);
  }
}

async function loadWorkspaceFiles() {
  try {
    const res = await fetch("/api/workspace/files");
    const data = await res.json();
    workspaceFiles = data.files || [];
    renderWorkspaceFileList();
  } catch(e) {
    console.error("Failed to load workspace files:", e);
  }
}

function renderWorkspaceFileList() {
  const container = document.getElementById("workspace-file-list");
  if (!workspaceFiles.length) {
    container.innerHTML = `<div style="color:var(--muted); padding:4px;">No files found</div>`;
    return;
  }
  container.innerHTML = workspaceFiles.slice(0, 50).map(f => {
    return `<label class="file-item">
      <input type="checkbox" value="${f.rel_path}" onchange="updateSelectedFilesCount()" />
      <span title="${f.rel_path}">${f.rel_path}</span>
    </label>`;
  }).join("");
}

function updateSelectedFilesCount() {
  const checked = document.querySelectorAll("#workspace-file-list input[type='checkbox']:checked");
  document.getElementById("ws-file-count").innerText = `${checked.length} files selected`;
}

function selectCoreFiles() {
  const coreTargets = ["apps/jupiter_studio.py", "src/memoryos/router.py", "src/memoryos/workspace_pack.py", "README.md"];
  const checkboxes = document.querySelectorAll("#workspace-file-list input[type='checkbox']");
  checkboxes.forEach(cb => {
    if (coreTargets.includes(cb.value)) {
      cb.checked = true;
    }
  });
  updateSelectedFilesCount();
  showToast("Selected core project files");
}

function getSelectedFiles() {
  const checked = document.querySelectorAll("#workspace-file-list input[type='checkbox']:checked");
  return Array.from(checked).map(cb => cb.value);
}

async function exportCopilotBundle() {
  const files = getSelectedFiles();
  const lastUserMsg = chatHistory.filter(m => m.role === "user").slice(-1)[0]?.content || "";
  const lastAssMsg = chatHistory.filter(m => m.role === "assistant").slice(-1)[0]?.content || "";

  try {
    const res = await fetch("/api/workspace/copilot-bundle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        goal: lastUserMsg || "Build and optimize features for MemoryOS / Jupiter Studio",
        files: files.length ? files : undefined,
        advice: lastAssMsg
      })
    });
    const data = await res.json();
    if (data.bundle) {
      await navigator.clipboard.writeText(data.bundle);
      showToast("📋 Copied complete Context Bundle for Copilot to clipboard!");
    }
  } catch(e) {
    alert("Failed to export Copilot bundle: " + e.message);
  }
}

let currentAttachedImageName = "";
let uploadedFiles = [];

function renderAttachmentPreview() {
  const preview = document.getElementById("attachment-preview");
  const chips = [];
  if (currentAttachedImage) {
    chips.push(`
      <div class="attachment-chip">
        <span>🖼️ ${currentAttachedImageName || "Image"}</span>
        <span class="remove-btn" onclick="removeAttachedImage()">✕</span>
      </div>
    `);
  }
  uploadedFiles.forEach((f, idx) => {
    const kb = Math.max(1, Math.round((f.size || f.content.length) / 1024));
    const safeName = f.name.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    chips.push(`
      <div class="attachment-chip">
        <span>📄 ${safeName} (${kb} KB)</span>
        <span class="remove-btn" onclick="removeUploadedFile(${idx})">✕</span>
      </div>
    `);
  });
  if (chips.length) {
    preview.style.display = "flex";
    preview.innerHTML = chips.join("");
  } else {
    preview.style.display = "none";
    preview.innerHTML = "";
  }
}

function handleImageSelected(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(evt) {
    currentAttachedImage = evt.target.result;
    currentAttachedImageName = `${file.name} (${Math.max(1, Math.round(file.size / 1024))} KB)`;
    renderAttachmentPreview();
  };
  reader.readAsDataURL(file);
}

function addFilesFromList(fileList) {
  const files = Array.from(fileList || []);
  for (const file of files) {
    if (file.type && file.type.startsWith("image/")) {
      const imgReader = new FileReader();
      imgReader.onload = function(evt) {
        currentAttachedImage = evt.target.result;
        currentAttachedImageName = `${file.name} (${Math.max(1, Math.round(file.size / 1024))} KB)`;
        renderAttachmentPreview();
      };
      imgReader.readAsDataURL(file);
      continue;
    }
    if (file.size > 2 * 1024 * 1024) {
      showToast(`⚠️ Skipped ${file.name}: exceeds 2 MB upload limit`);
      continue;
    }
    const reader = new FileReader();
    reader.onload = function(evt) {
      const content = String(evt.target.result || "");
      uploadedFiles.push({ name: file.name, size: file.size, content: content });
      renderAttachmentPreview();
      showToast(`📎 Uploaded ${file.name}`);
    };
    reader.readAsText(file);
  }
}

function handleFilesSelected(e) {
  addFilesFromList(e.target.files);
  e.target.value = "";
}

function handleDragOver(e) {
  e.preventDefault();
  const zone = document.getElementById("input-drop-zone");
  if (zone) zone.style.borderColor = "var(--cyan)";
}

function handleDragLeave(e) {
  const zone = document.getElementById("input-drop-zone");
  if (zone) zone.style.borderColor = "";
}

function handleDrop(e) {
  e.preventDefault();
  handleDragLeave(e);
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
    addFilesFromList(e.dataTransfer.files);
  }
}

function removeUploadedFile(idx) {
  uploadedFiles.splice(idx, 1);
  renderAttachmentPreview();
}

function removeAttachedImage() {
  currentAttachedImage = null;
  currentAttachedImageName = "";
  document.getElementById("image-file-input").value = "";
  renderAttachmentPreview();
}

function clearAllAttachments() {
  currentAttachedImage = null;
  currentAttachedImageName = "";
  uploadedFiles = [];
  document.getElementById("image-file-input").value = "";
  document.getElementById("doc-file-input").value = "";
  renderAttachmentPreview();
}

function onTargetChange() {
  const sel = document.getElementById("target-selector");
  const desc = document.getElementById("chat-target-desc");
  const badge = document.getElementById("chat-mode-badge");

  if (sel.value.startsWith("auto:")) {
    badge.innerText = "AUTO-ROUTE (d3)";
    badge.className = "badge";
    desc.innerText = "d3 Smart Router dynamically selects optimal tier";
  } else if (sel.value.startsWith("cloud:")) {
    badge.innerText = "AMD TOKEN LAB";
    badge.className = "badge";
    desc.innerText = sel.value.replace("cloud:", "") + " (AMD Instinct Cloud)";
  } else if (sel.value.startsWith("nv:")) {
    badge.innerText = "NVIDIA NIM";
    badge.className = "badge";
    desc.innerText = sel.value.replace("nv:", "") + " (NVIDIA NIM / Brev)";
  } else if (sel.value.startsWith("do:")) {
    badge.innerText = "DIGITALOCEAN";
    badge.className = "badge";
    desc.innerText = sel.value.replace("do:", "") + " (AMD MI300X)";
  } else if (sel.value.startsWith("hf:")) {
    badge.innerText = "HUGGING FACE";
    badge.className = "badge";
    desc.innerText = sel.value.replace("hf:", "") + " (Zero-Download Serverless Router)";
  } else if (sel.value.startsWith("vllm:")) {
    badge.innerText = "LOCAL vLLM";
    badge.className = "badge";
    desc.innerText = sel.value.replace("vllm:", "") + " (DGX Spark / Local vLLM)";
  } else if (sel.value.startsWith("flare:")) {
    badge.innerText = "NVIDIA FLARE";
    badge.className = "badge";
    desc.innerText = sel.value.replace("flare:", "") + " (DGX Spark / NVIDIA Flare)";
  } else {
    badge.innerText = "LOCAL OLLAMA";
    badge.className = "badge";
    desc.innerText = sel.value.replace("ollama:", "") + " (Local Host)";
  }
}

function clearChat() {
  chatHistory = [];
  const log = document.getElementById("chat-log");
  log.innerHTML = `
    <div class="msg assistant">
      <div class="meta-tag meta-auto">NEW CHAT STARTED</div>
      <div class="md-body"><p>Conversation cleared. MemoryOS ready for your next prompt.</p></div>
    </div>
  `;
}

let isGenerating = false;
let responseTimer = null;

function stopGeneration() {
  if (currentAbortController) {
    currentAbortController.abort();
    currentAbortController = null;
  }
  if (responseTimer) {
    clearInterval(responseTimer);
    responseTimer = null;
  }
  setRunningState(false);
}

function setRunningState(running) {
  isGenerating = running;
  document.getElementById("run-btn").style.display = running ? "none" : "block";
  document.getElementById("stop-btn").style.display = running ? "block" : "none";
}

async function sendPrompt() {
  if (isGenerating) return;
  const input = document.getElementById("prompt-input");
  let text = input.value.trim();
  if (!text && !currentAttachedImage && !uploadedFiles.length) return;
  if (!text) {
    text = uploadedFiles.length ? "Analyze the uploaded file(s)." : "Analyze the attached image.";
  }

  const target = document.getElementById("target-selector").value;
  const chatLog = document.getElementById("chat-log");
  const selectedFiles = getSelectedFiles();
  const filesToUpload = uploadedFiles.slice();

  // Append user message
  const uMsg = document.createElement("div");
  uMsg.className = "msg user";
  let userHtml = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  if (currentAttachedImage) {
    userHtml += `<br/><img src="${currentAttachedImage}" style="max-width:200px; max-height:140px; border-radius:6px; margin-top:8px; border:1px solid #334155;" />`;
  }
  if (filesToUpload.length) {
    const names = filesToUpload.map(f => f.name.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"));
    userHtml += `<div style="font-size:11px; color:var(--orange); margin-top:6px;">📄 Uploaded: ${names.join(", ")}</div>`;
  }
  if (selectedFiles.length) {
    userHtml += `<div style="font-size:11px; color:var(--cyan); margin-top:6px;">📎 Attached: ${selectedFiles.join(", ")}</div>`;
  }
  uMsg.innerHTML = userHtml;
  chatLog.appendChild(uMsg);

  input.value = "";
  chatLog.scrollTop = chatLog.scrollHeight;

  // Add Assistant Response Container
  const aMsg = document.createElement("div");
  aMsg.className = "msg assistant";
  const tagClass = target.startsWith("auto:") ? "meta-auto" : (target.startsWith("ollama:") ? "meta-local" : "meta-cloud");
  aMsg.innerHTML = `
    <div class="meta-tag ${tagClass}" id="cur-meta">CONNECTING...</div>
    <div class="reasoning-box" id="cur-reasoning-box" style="display:none;">
      <summary id="cur-reasoning-summary">Thinking Process...</summary>
      <div class="reasoning-content" id="cur-reasoning-content"></div>
    </div>
    <div class="md-body" id="cur-content">Generating response...</div>
  `;
  chatLog.appendChild(aMsg);
  chatLog.scrollTop = chatLog.scrollHeight;

  const metaEl = aMsg.querySelector("#cur-meta");
  const reasoningBox = aMsg.querySelector("#cur-reasoning-box");
  const reasoningContent = aMsg.querySelector("#cur-reasoning-content");
  const contentEl = aMsg.querySelector("#cur-content");

  // Remove temporary IDs
  metaEl.removeAttribute("id");
  reasoningBox.removeAttribute("id");
  reasoningContent.removeAttribute("id");
  contentEl.removeAttribute("id");

  setRunningState(true);
  currentAbortController = new AbortController();

  let elapsedSec = 0;
  if (responseTimer) clearInterval(responseTimer);
  responseTimer = setInterval(() => {
    elapsedSec++;
    if (contentEl && contentEl.innerText.startsWith("Generating response")) {
      contentEl.innerText = `Generating response... (${elapsedSec}s)`;
    }
  }, 1000);

  let accumulatedContent = "";
  let accumulatedReasoning = "";

  const payload = {
    prompt: text,
    target: target,
    history: chatHistory.slice(-8),
    image_base64: currentAttachedImage,
    workspace_files: selectedFiles,
    uploaded_files: filesToUpload,
  };

  clearAllAttachments();

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: currentAbortController.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let streamFinished = false;

    while (!streamFinished) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop(); // Keep remaining incomplete chunk

      for (const line of lines) {
        if (!line.trim()) continue;
        const evLines = line.split("\n");
        let evType = "delta";
        let evData = "";

        for (const el of evLines) {
          if (el.startsWith("event:")) {
            evType = el.replace("event:", "").trim();
          } else if (el.startsWith("data:")) {
            evData = el.replace("data:", "").trim();
          }
        }

        if (!evData) continue;
        const parsed = JSON.parse(evData);

        if (evType === "start") {
          metaEl.innerText = `${parsed.model_used || "STREAMING"} [${parsed.provider || "Active"}]`;
          if (contentEl.innerText.startsWith("Generating response")) {
            contentEl.innerHTML = "";
          }
        } else if (evType === "reasoning") {
          if (responseTimer) { clearInterval(responseTimer); responseTimer = null; }
          accumulatedReasoning += parsed.delta || "";
          reasoningBox.style.display = "block";
          reasoningContent.innerText = accumulatedReasoning;
        } else if (evType === "delta") {
          if (responseTimer) { clearInterval(responseTimer); responseTimer = null; }
          if (contentEl.innerText.startsWith("Generating response")) {
            contentEl.innerHTML = "";
          }
          accumulatedContent += parsed.delta || "";
          contentEl.innerHTML = renderMarkdown(accumulatedContent);
        } else if (evType === "done") {
          if (responseTimer) { clearInterval(responseTimer); responseTimer = null; }
          metaEl.innerText = `${parsed.model_used || target} (${parsed.latency_ms || 0} ms)`;
          contentEl.innerHTML = renderMarkdown(accumulatedContent || parsed.fallback_content || "(No response text)");
          streamFinished = true;
          break;
        } else if (evType === "error") {
          if (responseTimer) { clearInterval(responseTimer); responseTimer = null; }
          metaEl.className = "meta-tag meta-error";
          metaEl.innerText = "ERROR";
          contentEl.innerHTML = `<div style="color:var(--red); font-family:monospace;">${parsed.error}</div>`;
          streamFinished = true;
          break;
        }
      }
      chatLog.scrollTop = chatLog.scrollHeight;
    }
    try { await reader.cancel(); } catch (_) {}

    // Save to multi-turn conversation history
    chatHistory.push({ role: "user", content: text });
    chatHistory.push({ role: "assistant", content: accumulatedContent });

  } catch(err) {
    if (responseTimer) { clearInterval(responseTimer); responseTimer = null; }
    if (err.name === "AbortError") {
      metaEl.innerText += " (Stopped)";
    } else {
      metaEl.className = "meta-tag meta-error";
      metaEl.innerText = "CALL FAILED";
      contentEl.innerHTML = `<div style="color:var(--red); font-family:monospace;">${err.message}</div>`;
    }
  } finally {
    if (responseTimer) { clearInterval(responseTimer); responseTimer = null; }
    setRunningState(false);
    currentAbortController = null;
    chatLog.scrollTop = chatLog.scrollHeight;
  }
}

// Init on load
loadStatus();
loadWorkspaceFiles();
setInterval(loadStatus, 5000);

/* ── 1. THEME SWITCHER (QUANTUM / RADEON / DAYLIGHT) ─────────────────── */
function setStudioTheme(theme) {
  document.documentElement.setAttribute("data-studio-theme", theme);
  document.querySelectorAll(".theme-pill-btn").forEach((b) => {
    b.classList.toggle("active", b.getAttribute("data-t") === theme);
  });
  try { localStorage.setItem("jupiter.studio.theme", theme); } catch (_) {}
}
try {
  const savedTheme = localStorage.getItem("jupiter.studio.theme");
  if (savedTheme) setStudioTheme(savedTheme);
} catch (_) {}

/* ── 2. QUANTUM LATTICE & PARTICLE CANVAS (DRIVEN BY ZEN 3 GATE & MLP) ─ */
let quantumPulse = 0.15;
(function initQuantumCanvas() {
  const c = document.getElementById("quantum-canvas");
  if (!c) return;
  const ctx = c.getContext("2d");
  const nodes = Array.from({ length: 28 }, (_, i) => ({
    x: Math.random(),
    y: Math.random(),
    vx: (Math.random() - 0.5) * 0.0018,
    vy: (Math.random() - 0.5) * 0.006,
    r: 1.5 + (i % 3) * 0.7,
  }));
  function resize() {
    const r = c.getBoundingClientRect();
    c.width = Math.max(300, Math.floor(r.width));
    c.height = Math.max(48, Math.floor(r.height));
  }
  resize();
  window.addEventListener("resize", resize);
  function tick() {
    const w = c.width, h = c.height;
    ctx.clearRect(0, 0, w, h);
    const speed = isGenerating ? 3.2 : (1.0 + quantumPulse * 2.0);
    quantumPulse = Math.max(0.05, quantumPulse * 0.95);
    const theme = document.documentElement.getAttribute("data-studio-theme") || "quantum";
    const colA = theme === "radeon" ? "237, 28, 36" : (theme === "daylight" ? "255, 77, 0" : "255, 106, 0");
    const colB = theme === "radeon" ? "255, 176, 0" : (theme === "daylight" ? "10, 123, 92" : "0, 240, 255");

    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      n.x += n.vx * speed;
      n.y += n.vy * speed;
      if (n.x < 0 || n.x > 1) n.vx *= -1;
      if (n.y < 0 || n.y > 1) n.vy *= -1;
      const px = n.x * w, py = n.y * h;
      ctx.fillStyle = `rgba(${i % 2 === 0 ? colA : colB}, 0.75)`;
      ctx.beginPath();
      ctx.arc(px, py, n.r, 0, Math.PI * 2);
      ctx.fill();
      for (let j = i + 1; j < nodes.length; j++) {
        const m = nodes[j];
        const dx = (n.x - m.x) * w, dy = (n.y - m.y) * h;
        const dist = Math.hypot(dx, dy);
        if (dist < 110) {
          ctx.strokeStyle = `rgba(${colB}, ${(1 - dist / 110) * 0.25})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(px, py);
          ctx.lineTo(m.x * w, m.y * h);
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();

/* ── 3. LIVE PRE-SEND SPECULATIVE NEURAL RADAR (/api/speculate) ──────── */
let specTimer = null;
async function updateSpeculativeRadar() {
  const input = document.getElementById("prompt-input");
  if (!input) return;
  const text = input.value || "";
  quantumPulse = Math.min(1.0, quantumPulse + 0.25);
  const extraChars = (typeof currentUploadedFiles !== "undefined" ? currentUploadedFiles : []).reduce((acc, f) => acc + (f.content ? f.content.length : 0), 0);
  const fileCount = (typeof currentUploadedFiles !== "undefined" ? currentUploadedFiles.length : 0) + document.querySelectorAll(".ws-file-cb:checked").length;
  try {
    const res = await fetch("/api/speculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: text,
        has_image: Boolean(currentAttachedImage),
        file_count: fileCount,
        extra_chars: extraChars,
      }),
    });
    const d = await res.json();
    const pct = (Number(d.p_offload || 0.88) * 100).toFixed(1);
    document.getElementById("rad-mlp").innerText = `P(offload) ${pct}% · ${d.mlp_latency_us} μs`;
    const barEl = document.getElementById("rad-mlp-bar");
    if (barEl) barEl.style.width = `${Math.max(4, Math.min(100, Number(pct)))}%`;
    const sel = document.getElementById("target-selector").value;
    const routeLabel = sel === "auto:d3" ? `d3 → ${d.predicted_model}` : sel;
    document.getElementById("rad-route").innerText = routeLabel;
    document.getElementById("rad-tok").innerText = `~${Number(d.est_tokens || 1).toLocaleString()} tokens`;
    document.getElementById("rad-vram").innerText = `${d.vram_saved_gb} GB saved (0 MB used)`;
  } catch (_) {}
}
document.getElementById("prompt-input").addEventListener("input", () => {
  clearTimeout(specTimer);
  specTimer = setTimeout(updateSpeculativeRadar, 90);
});
document.getElementById("prompt-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendPrompt();
  }
});
setTimeout(updateSpeculativeRadar, 400);

/* ── 4. DUAL-MODEL SPLIT ARENA SHOOTOUT ──────────────────────────────── */
let dualArenaEnabled = false;
function toggleDualArena() {
  dualArenaEnabled = !dualArenaEnabled;
  const btn = document.getElementById("btn-arena");
  btn.classList.toggle("active", dualArenaEnabled);
  btn.innerText = dualArenaEnabled ? "⚔️ Arena: ON (2x Live)" : "⚔️ Dual Arena";
}

const _origSendPrompt = sendPrompt;
sendPrompt = async function() {
  if (!dualArenaEnabled) {
    return _origSendPrompt();
  }
  if (isGenerating) return;
  const input = document.getElementById("prompt-input");
  const text = input.value.trim();
  if (!text) return;

  const primaryTarget = document.getElementById("target-selector").value;
  const challengerTarget = primaryTarget === "cloud:Qwen3.8-27B" ? "cloud:MiniCPM5-2B" : "cloud:Qwen3.8-27B";
  const selectedFiles = Array.from(document.querySelectorAll(".ws-file-cb:checked")).map((cb) => cb.value);
  const filesToUpload = (typeof currentUploadedFiles !== "undefined" ? currentUploadedFiles : []).slice();
  const imgData = currentAttachedImage;

  const chatLog = document.getElementById("chat-log");
  const uMsg = document.createElement("div");
  uMsg.className = "msg user";
  uMsg.innerHTML = `<div class="meta-tag" style="background:rgba(255,255,255,0.12);">⚔️ DUAL ARENA PROMPT</div><div>${text.replace(/</g, "&lt;")}</div>`;
  chatLog.appendChild(uMsg);
  input.value = "";
  clearAllAttachments();

  const aMsg = document.createElement("div");
  aMsg.className = "msg assistant";
  aMsg.style.width = "96%";
  aMsg.innerHTML = `
    <div style="font-family:monospace; font-size:11px; color:var(--cyan); margin-bottom:8px;">
      ⚔️ LIVE SPLIT-BRAIN ARENA SHOOTOUT // ZERO LOCAL VRAM
    </div>
    <div class="arena-grid">
      <div class="arena-col" id="arena-left">
        <span class="meta-tag meta-auto" data-role="meta">${primaryTarget} [Streaming...]</span>
        <div class="md-body" data-role="content" style="color:var(--muted);">Waiting for primary stream...</div>
        <button class="arena-keep-btn" data-role="keep" style="display:none;">✓ Keep Left Reply</button>
      </div>
      <div class="arena-col" id="arena-right">
        <span class="meta-tag meta-cloud" data-role="meta">${challengerTarget} [Streaming...]</span>
        <div class="md-body" data-role="content" style="color:var(--muted);">Waiting for challenger stream...</div>
        <button class="arena-keep-btn" data-role="keep" style="display:none;">✓ Keep Right Reply</button>
      </div>
    </div>
  `;
  chatLog.appendChild(aMsg);
  chatLog.scrollTop = chatLog.scrollHeight;

  setRunningState(true);
  currentAbortController = new AbortController();

  async function runColumn(colEl, targetModel) {
    const metaEl = colEl.querySelector('[data-role="meta"]');
    const contentEl = colEl.querySelector('[data-role="content"]');
    const keepBtn = colEl.querySelector('[data-role="keep"]');
    let acc = "";
    const t0 = performance.now();
    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: currentAbortController.signal,
        body: JSON.stringify({
          prompt: text,
          target: targetModel,
          history: chatHistory.slice(-6),
          image_base64: imgData,
          workspace_files: selectedFiles,
          uploaded_files: filesToUpload,
        }),
      });
      const reader = res.body.getReader();
      const dec = new TextDecoder("utf-8");
      let buf = "", doneFlag = false;
      while (!doneFlag) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop();
        for (const part of parts) {
          let ev = "delta", dat = "";
          for (const l of part.split("\n")) {
            if (l.startsWith("event:")) ev = l.slice(6).trim();
            else if (l.startsWith("data:")) dat = l.slice(5).trim();
          }
          if (!dat) continue;
          const p = JSON.parse(dat);
          if (ev === "start") {
            metaEl.innerText = `${p.model_used || targetModel} [${p.provider || "LIVE"}]`;
          } else if (ev === "delta") {
            quantumPulse = 0.9;
            acc += p.delta || "";
            contentEl.style.color = "";
            contentEl.innerHTML = renderMarkdown(acc);
          } else if (ev === "done") {
            const ms = Math.round(p.latency_ms || (performance.now() - t0));
            metaEl.innerText = `${p.model_used || targetModel} (${ms} ms)`;
            contentEl.style.color = "";
            contentEl.innerHTML = renderMarkdown(acc || "(No response text)");
            keepBtn.style.display = "inline-block";
            keepBtn.onclick = () => {
              chatHistory.push({ role: "user", content: text });
              chatHistory.push({ role: "assistant", content: acc });
              aMsg.innerHTML = `<span class="meta-tag meta-local">✓ ARENA WINNER: ${p.model_used || targetModel} (${ms} ms)</span><div class="md-body">${renderMarkdown(acc)}</div>`;
            };
            doneFlag = true;
            break;
          } else if (ev === "error") {
            metaEl.className = "meta-tag meta-error";
            metaEl.innerText = "ERROR";
            contentEl.innerHTML = `<span style="color:var(--red); font-family:monospace;">${p.error}</span>`;
            doneFlag = true;
            break;
          }
        }
        chatLog.scrollTop = chatLog.scrollHeight;
      }
      try { await reader.cancel(); } catch (_) {}
    } catch (e) {
      metaEl.innerText += " (Stopped)";
    }
  }

  try {
    await Promise.all([
      runColumn(aMsg.querySelector("#arena-left"), primaryTarget),
      runColumn(aMsg.querySelector("#arena-right"), challengerTarget),
    ]);
  } finally {
    setRunningState(false);
    currentAbortController = null;
  }
};

</script>
</body>
</html>
"""


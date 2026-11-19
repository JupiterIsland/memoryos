#!/usr/bin/env python3
"""
Jupiter Studio // MemoryOS Hybrid Desktop Workstation (Zero-Dependency Python).
Features:
  1) Real-time SSE token streaming (/api/chat/stream) with reasoning display & Stop button.
  2) Smart Auto-Route (d3) across AMD Token Lab, NVIDIA NIM / Brev, DigitalOcean MI300X, and Local Ollama.
  3) Dynamic provider readiness badges & live Quiet Advisor / Zen 3 policy telemetry.
  4) Multi-turn conversation history with client-side Markdown rendering & 1-click code copying.
  5) Workspace folder scanner, context packer, screenshot drop, and 1-click 'Export Copilot Bundle'.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.memoryos.gpu_backends import MultiGPUDetector
from src.memoryos.router import (
    DO_MODEL_MAP,
    MODEL_PROFILES,
    NVIDIA_MODEL_MAP,
    _get_do_credentials,
    _get_nvidia_credentials,
    _get_tokenlab_credentials,
    _is_configured_key,
    get_cloud_provider_status,
    get_policy_telemetry,
    route_task,
    select_model_with_d3,
)
from src.memoryos.workspace_pack import (
    export_copilot_bundle,
    pack_workspace_context,
    scan_workspace_files,
)

PORT = int(os.getenv("JUPITER_STUDIO_PORT", 7860))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")


def _get_local_vllm_credentials() -> Tuple[str, str]:
    """Return (api_key, base_url) for a local vLLM / SGLang / TensorFold OpenAI-compatible server."""
    base_url = os.getenv("LOCAL_VLLM_BASE_URL", "http://127.0.0.1:8000/v1").strip().rstrip("/")
    api_key = os.getenv("LOCAL_VLLM_API_KEY", "EMPTY").strip()
    return api_key, base_url


def _get_nvidia_flare_credentials() -> Tuple[str, str]:
    """Return (api_key, base_url) for a local NVIDIA Flare (DGX Spark Rust inference server) endpoint."""
    base_url = os.getenv("NVIDIA_FLARE_BASE_URL", "http://127.0.0.1:8080/v1").strip().rstrip("/")
    api_key = os.getenv("NVIDIA_FLARE_API_KEY", "EMPTY").strip()
    return api_key, base_url

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Jupiter Studio // Hybrid AI Workstation</title>
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
</style>
</head>
<body>
  <!-- Sidebar -->
  <div class="sidebar">
    <div class="brand">
      <div class="logo-badge" title="Jupiter Studio RC1 — Powered by AMD Token Lab">
        <svg viewBox="0 0 40 40" width="38" height="38" aria-hidden="true">
          <defs>
            <linearGradient id="orbGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#FF8A00"/>
              <stop offset="100%" stop-color="#E52E71"/>
            </linearGradient>
            <linearGradient id="ringG" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#38BDF8"/>
              <stop offset="50%" stop-color="#A855F7"/>
              <stop offset="100%" stop-color="#FF8A00"/>
            </linearGradient>
          </defs>
          <rect width="40" height="40" rx="9" fill="#0d1424" stroke="#1e2942" stroke-width="1.2"/>
          <g transform="translate(20, 20) rotate(-22)">
            <ellipse cx="0" cy="0" rx="14" ry="4" fill="none" stroke="url(#ringG)" stroke-width="1.6"/>
            <circle cx="0" cy="0" r="7" fill="url(#orbGrad)"/>
            <ellipse cx="2.5" cy="1" rx="1.5" ry="0.9" fill="#991B1B"/>
          </g>
        </svg>
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
        <optgroup label="DGX Spark / GB10 Local (vLLM / Flare)" id="opt-spark">
          <option value="vllm:Qwen/Qwen3.8-Flash-Next">Qwen3.8-Flash-Next (Local vLLM :8000)</option>
          <option value="vllm:deepseek-ai/DeepSeek-V4.1-Flash">DeepSeek-V4.1-Flash (Local vLLM :8000)</option>
          <option value="flare:Qwen3.8-Flash-Next">Qwen3.8-Flash-Next (NVIDIA Flare :8080)</option>
          <option value="flare:DeepSeek-V4.1-Flash">DeepSeek-V4.1-Flash (NVIDIA Flare :8080)</option>
        </optgroup>
        <optgroup label="Local Models (100% Free / Ollama)" id="opt-ollama">
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
      <div style="display:flex; align-items:center; gap:10px;">
        <span class="badge" id="chat-mode-badge">AUTO-ROUTE (d3)</span>
        <span style="font-size:12px; color:var(--muted);" id="chat-target-desc">Dynamically routes to fastest optimal model</span>
      </div>
      <div style="display:flex; gap:8px;">
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

    <!-- Input Bar -->
    <div class="input-bar-wrapper">
      <div class="attachment-preview" id="attachment-preview" style="display:none;"></div>
      <div class="input-bar">
        <input type="file" id="image-file-input" accept="image/*" style="display:none;" onchange="handleImageSelected(event)" />
        <button class="btn-icon" title="Attach Screenshot or Image" onclick="document.getElementById('image-file-input').click()">
          🖼️
        </button>
        <textarea id="prompt-input" rows="2" placeholder="Ask your model anything... (Ctrl+Enter to send)" onkeydown="if(event.ctrlKey && event.key==='Enter') sendPrompt()"></textarea>
        <div class="input-actions">
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

function handleImageSelected(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(evt) {
    currentAttachedImage = evt.target.result;
    const preview = document.getElementById("attachment-preview");
    preview.style.display = "flex";
    preview.innerHTML = `
      <div class="attachment-chip">
        <span>🖼️ ${file.name} (${Math.round(file.size / 1024)} KB)</span>
        <span class="remove-btn" onclick="removeAttachedImage()">✕</span>
      </div>
    `;
  };
  reader.readAsDataURL(file);
}

function removeAttachedImage() {
  currentAttachedImage = null;
  document.getElementById("image-file-input").value = "";
  const preview = document.getElementById("attachment-preview");
  preview.style.display = "none";
  preview.innerHTML = "";
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
  const text = input.value.trim();
  if (!text) return;

  const target = document.getElementById("target-selector").value;
  const chatLog = document.getElementById("chat-log");
  const selectedFiles = getSelectedFiles();

  // Append user message
  const uMsg = document.createElement("div");
  uMsg.className = "msg user";
  let userHtml = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  if (currentAttachedImage) {
    userHtml += `<br/><img src="${currentAttachedImage}" style="max-width:200px; max-height:140px; border-radius:6px; margin-top:8px; border:1px solid #334155;" />`;
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
  };

  removeAttachedImage();

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

    while (true) {
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
        } else if (evType === "error") {
          if (responseTimer) { clearInterval(responseTimer); responseTimer = null; }
          metaEl.className = "meta-tag meta-error";
          metaEl.innerText = "ERROR";
          contentEl.innerHTML = `<div style="color:var(--red); font-family:monospace;">${parsed.error}</div>`;
        }
      }
      chatLog.scrollTop = chatLog.scrollHeight;
    }

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
</script>
</body>
</html>
"""


class JupiterStudioHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            payload = HTML_PAGE.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path == "/api/status":
            prof = MultiGPUDetector.get_active_profile()
            cloud = get_cloud_provider_status()
            policy = get_policy_telemetry()
            self._send_json({"gpu": prof.__dict__, "cloud": cloud, "policy": policy})
            return

        if self.path == "/api/workspace/files":
            files = scan_workspace_files(REPO_ROOT, max_files=150)
            self._send_json({"files": files, "repo_root": str(REPO_ROOT)})
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            body = {}

        if self.path == "/api/workspace/copilot-bundle":
            goal = body.get("goal", "")
            files = body.get("files") or None
            advice = body.get("advice", "")
            bundle = export_copilot_bundle(REPO_ROOT, user_goal=goal, selected_files=files, assistant_advice=advice)
            self._send_json({"bundle": bundle})
            return

        if self.path == "/api/workspace/pack":
            files = body.get("files") or None
            pack = pack_workspace_context(REPO_ROOT, selected_files=files)
            self._send_json(pack)
            return

        if self.path == "/api/chat/stream":
            self._handle_chat_stream(body)
            return

        if self.path == "/api/chat":
            self._handle_chat_sync(body)
            return

        self._send_json({"error": "Unknown endpoint"}, status=404)

    def _handle_chat_stream(self, body: Dict[str, Any]) -> None:
        prompt = body.get("prompt", "")
        target = body.get("target", "auto:d3")
        history = body.get("history") or []
        image_base64 = body.get("image_base64")
        workspace_files = body.get("workspace_files") or []

        # Send SSE headers
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        def _send(event_type: str, data: Dict[str, Any]) -> None:
            try:
                line = f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode("utf-8")
                self.wfile.write(line)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass

        t0 = time.perf_counter()

        # Build context if workspace files were attached
        effective_prompt = prompt
        if workspace_files:
            pack = pack_workspace_context(REPO_ROOT, selected_files=workspace_files, include_git=True)
            effective_prompt = (
                f"{prompt}\n\n---\n### Attached Project Workspace Context:\n{pack['bundle_text']}"
            )

        # Resolve model and provider
        model_name, provider_key, is_local = self._resolve_target(target, effective_prompt, bool(image_base64))
        _send("start", {"model_used": model_name, "provider": provider_key, "is_local": is_local})

        # Stream execution
        try:
            if is_local:
                self._stream_ollama(model_name, effective_prompt, history, _send)
            else:
                self._stream_cloud(provider_key, model_name, effective_prompt, history, image_base64, _send)

            latency = round((time.perf_counter() - t0) * 1000, 2)
            _send("done", {"latency_ms": latency, "model_used": model_name})
        except Exception as exc:
            _send("error", {"error": str(exc)})

    def _handle_chat_sync(self, body: Dict[str, Any]) -> None:
        prompt = body.get("prompt", "")
        target = body.get("target", "auto:d3")
        image_base64 = body.get("image_base64")
        t0 = time.perf_counter()

        model_name, provider_key, is_local = self._resolve_target(target, prompt, bool(image_base64))
        content = ""
        err = ""

        try:
            if is_local:
                content = self._call_ollama(model_name, prompt)
            else:
                content, err = self._call_cloud_direct(provider_key, model_name, prompt)
        except Exception as exc:
            err = str(exc)

        latency = round((time.perf_counter() - t0) * 1000, 2)
        self._send_json({
            "model_used": f"{provider_key}: {model_name}",
            "content": content or f"[{err}]",
            "latency_ms": latency,
            "is_local": is_local,
        })

    def _resolve_target(self, target: str, prompt: str, has_image: bool) -> Tuple[str, str, bool]:
        if target == "auto:d3":
            total_chars = len(prompt)
            decision = select_model_with_d3(prompt_text=prompt, has_image=has_image, context_chars=total_chars)
            selected_model = decision.get("selected_model", "Gemma-4-31B-IT")
            tier = decision.get("selected_tier", "balanced_code")
            # If AMD Token Lab is ready, use it; otherwise NIM or DO
            status = get_cloud_provider_status()
            if status["amd_tokenlab"]["configured"]:
                return selected_model, "AMD Token Lab", False
            if status["nvidia_brev"]["configured"]:
                nv_model = NVIDIA_MODEL_MAP.get(selected_model, "meta/llama-3.3-70b-instruct")
                return nv_model, "NVIDIA NIM", False
            if status["digitalocean_mi300x"]["configured"]:
                do_model = DO_MODEL_MAP.get(selected_model, "meta-llama/Llama-3.3-70B-Instruct")
                return do_model, "DigitalOcean MI300X", False
            return "qwen2.5-coder:7b", "Local Ollama", True

        if target.startswith("ollama:"):
            return target.split(":", 1)[1], "Local Ollama", True

        if target.startswith("cloud:"):
            return target.split(":", 1)[1], "AMD Token Lab", False

        if target.startswith("nv:"):
            return target.split(":", 1)[1], "NVIDIA NIM", False

        if target.startswith("do:"):
            return target.split(":", 1)[1], "DigitalOcean MI300X", False

        if target.startswith("vllm:"):
            return target.split(":", 1)[1], "Local vLLM (Spark)", False

        if target.startswith("flare:"):
            return target.split(":", 1)[1], "NVIDIA Flare (Spark)", False

        return "Gemma-4-31B-IT", "AMD Token Lab", False

    def _stream_cloud(
        self,
        provider_key: str,
        model_name: str,
        prompt: str,
        history: List[Dict[str, str]],
        image_base64: Optional[str],
        _send: Any,
    ) -> None:
        is_local_openai = False
        if "Local vLLM" in provider_key:
            api_key, base_url = _get_local_vllm_credentials()
            is_local_openai = True
        elif "Flare" in provider_key:
            api_key, base_url = _get_nvidia_flare_credentials()
            is_local_openai = True
        elif "NVIDIA" in provider_key:
            api_key, base_url = _get_nvidia_credentials()
        elif "DigitalOcean" in provider_key:
            api_key, base_url = _get_do_credentials()
        else:
            api_key, base_url = _get_tokenlab_credentials()

        if not is_local_openai and not api_key:
            raise RuntimeError(f"{provider_key} API key not configured in .env")

        # Build messages with history
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": "You are a world-class AI software architect and coding engineer in Jupiter Studio."}
        ]
        for h in history:
            role = h.get("role", "user")
            content = h.get("content", "")
            if content:
                messages.append({"role": role, "content": content})

        # Append current user prompt
        if image_base64:
            user_content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
            user_content.append({"type": "image_url", "image_url": {"url": image_base64}})
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": prompt})

        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 2048,
            "stream": True,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "JupiterStudio/0.2",
        }
        if api_key and api_key.upper() != "EMPTY":
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(
            url,
            data=payload,
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=120.0) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    obj = json.loads(data_str)
                    choices = obj.get("choices") or []
                    if choices:
                        delta = choices[0].get("delta") or {}
                        reasoning = delta.get("reasoning_content") or delta.get("reasoning")
                        if reasoning:
                            _send("reasoning", {"delta": reasoning})
                        content = delta.get("content")
                        if content:
                            _send("delta", {"delta": content})
                except json.JSONDecodeError:
                    continue

    def _stream_ollama(
        self,
        model_name: str,
        prompt: str,
        history: List[Dict[str, str]],
        _send: Any,
    ) -> None:
        url = f"{OLLAMA_HOST}/api/generate"
        payload = json.dumps({
            "model": model_name,
            "prompt": prompt,
            "stream": True,
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120.0) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        chunk = obj.get("response", "")
                        if chunk:
                            _send("delta", {"delta": chunk})
                        if obj.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            raise RuntimeError(f"Ollama error: {exc}. Ensure Ollama is running on host ({OLLAMA_HOST}).") from exc

    def _call_cloud_direct(self, provider_key: str, model_name: str, prompt: str) -> Tuple[str, str]:
        is_local_openai = False
        if "Local vLLM" in provider_key:
            api_key, base_url = _get_local_vllm_credentials()
            is_local_openai = True
        elif "Flare" in provider_key:
            api_key, base_url = _get_nvidia_flare_credentials()
            is_local_openai = True
        elif "NVIDIA" in provider_key:
            api_key, base_url = _get_nvidia_credentials()
        elif "DigitalOcean" in provider_key:
            api_key, base_url = _get_do_credentials()
        else:
            api_key, base_url = _get_tokenlab_credentials()

        if not is_local_openai and not api_key:
            return "", f"{provider_key} API key not configured in .env"

        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1024,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "JupiterStudio/0.2",
        }
        if api_key and api_key.upper() != "EMPTY":
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(
            url,
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"], ""
        except Exception as exc:
            return "", str(exc)

    def _call_ollama(self, model: str, prompt: str) -> str:
        url = f"{OLLAMA_HOST}/api/generate"
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "")
        except Exception as exc:
            return f"[Ollama Call Failed]: {exc}\nEnsure Ollama is running on host ({OLLAMA_HOST})."


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), JupiterStudioHandler)
    print(f"[+] Jupiter Studio active at http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopped")


if __name__ == "__main__":
    main()

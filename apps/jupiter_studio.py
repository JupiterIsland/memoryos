#!/usr/bin/env python3
"""
Jupiter Studio // MemoryOS Hybrid Desktop App (Zero-Dependency Python).
Connects seamlessly to:
  1) Local Ollama (http://127.0.0.1:11434) — qwen2.5-coder, deepseek-r1, etc.
  2) Cloud APIs — AMD Token Lab (Gemma-4-31B-IT, Qwen3.8-27B) & DigitalOcean MI300X.
  3) MemoryOS Hardware Router & Live GPU/VRAM telemetry.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.memoryos.gpu_backends import MultiGPUDetector
from src.memoryos.router import DO_MODEL_MAP, MODEL_PROFILES, get_cloud_provider_status, route_task

PORT = int(os.getenv("JUPITER_STUDIO_PORT", 7860))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Jupiter Studio // Hybrid AI Workstation</title>
<style>
  :root {
    --bg: #090c15;
    --panel: #111728;
    --panel-border: #1e2942;
    --orange: #ff6a00;
    --cyan: #38bdf8;
    --green: #10b981;
    --purple: #a855f7;
    --text: #f1f5f9;
    --muted: #94a3b8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    height: 100vh;
    overflow: hidden;
  }
  .sidebar {
    width: 320px;
    background: var(--panel);
    border-right: 1px solid var(--panel-border);
    display: flex;
    flex-direction: column;
    padding: 18px;
    gap: 16px;
    overflow-y: auto;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .logo-badge {
    width: 36px; height: 36px;
    background: radial-gradient(circle, var(--orange) 0%, #b34700 100%);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 18px; color: #fff;
  }
  .brand h1 { font-size: 16px; font-weight: 700; letter-spacing: 0.5px; }
  .brand p { font-size: 11px; color: var(--muted); }
  .section-title {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin-bottom: 6px;
  }
  .card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--panel-border);
    border-radius: 8px;
    padding: 12px;
  }
  .hw-val { font-size: 13px; font-weight: 600; color: var(--cyan); margin-top: 4px; }
  .select-box, input, textarea {
    width: 100%;
    background: #0d121f;
    border: 1px solid var(--panel-border);
    color: #fff;
    padding: 8px 10px;
    border-radius: 6px;
    font-size: 13px;
    outline: none;
  }
  .select-box:focus, input:focus, textarea:focus { border-color: var(--cyan); }
  .main {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100vh;
  }
  .chat-log {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .msg {
    max-width: 80%;
    padding: 14px 18px;
    border-radius: 10px;
    line-height: 1.5;
    font-size: 14px;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .msg.user {
    align-self: flex-end;
    background: #1e2942;
    border: 1px solid #334155;
    color: #fff;
  }
  .msg.assistant {
    align-self: flex-start;
    background: #101726;
    border: 1px solid #1e2942;
    border-left: 3px solid var(--cyan);
  }
  .meta-tag {
    display: inline-block;
    font-size: 10px;
    font-family: monospace;
    padding: 2px 6px;
    border-radius: 4px;
    margin-bottom: 6px;
  }
  .meta-local { background: rgba(16, 185, 129, 0.15); color: var(--green); border: 1px solid var(--green); }
  .meta-cloud { background: rgba(255, 106, 0, 0.15); color: var(--orange); border: 1px solid var(--orange); }
  .input-bar {
    padding: 16px 24px;
    background: var(--panel);
    border-top: 1px solid var(--panel-border);
    display: flex;
    gap: 12px;
  }
  .btn {
    background: var(--orange);
    color: #fff;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.15s;
  }
  .btn:hover { background: #e05d00; }
  .btn-secondary {
    background: #1e2942;
    border: 1px solid var(--panel-border);
  }
  .btn-secondary:hover { background: #273554; }
</style>
</head>
<body>
  <div class="sidebar">
    <div class="brand">
      <div class="logo-badge">J</div>
      <div>
        <h1>Jupiter Studio</h1>
        <p>MemoryOS Hybrid Engine</p>
      </div>
    </div>

    <div>
      <div class="section-title">Hardware Profile</div>
      <div class="card" id="hw-card">
        <div style="font-size:11px; color:var(--muted);">ACTIVE GPU</div>
        <div class="hw-val" id="hw-name">Detecting...</div>
        <div style="font-size:11px; color:var(--muted); margin-top:6px;">VRAM USAGE</div>
        <div class="hw-val" id="hw-vram">0 / 0 MB</div>
      </div>
    </div>

    <div>
      <div class="section-title">Execution Target</div>
      <select class="select-box" id="target-selector" onchange="onTargetChange()">
        <optgroup label="Local Models (100% Free / Ollama)">
          <option value="ollama:qwen2.5-coder:1.5b">qwen2.5-coder:1.5b (Ultra-Fast)</option>
          <option value="ollama:qwen2.5-coder:7b">qwen2.5-coder:7b (High Accuracy)</option>
          <option value="ollama:deepseek-r1:7b">deepseek-r1:7b (Reasoning)</option>
          <option value="ollama:deepseek-r1:8b">deepseek-r1:8b (Deep Thinking)</option>
          <option value="ollama:gemma4:26b">gemma4:26b (Heavy Local)</option>
        </optgroup>
        <optgroup label="Cloud Offload (AMD Token Lab Grant)">
          <option value="cloud:Gemma-4-31B-IT">Gemma-4-31B-IT (Tactical / Vision)</option>
          <option value="cloud:Qwen3.8-27B">Qwen3.8-27B (Surgical Code Diff)</option>
          <option value="cloud:DeepSeek-V4.1-Flash">DeepSeek-V4.1-Flash (1M Context)</option>
        </optgroup>
        <optgroup label="DigitalOcean Serverless (AMD MI300X)">
          <option value="do:Qwen/Qwen2.5-Coder-32B-Instruct">Qwen-2.5-Coder-32B (MI300X)</option>
          <option value="do:meta-llama/Llama-3.3-70B-Instruct">Llama-3.3-70B (MI300X)</option>
        </optgroup>
      </select>
    </div>

    <div>
      <div class="section-title">MemoryOS Policy</div>
      <div class="card">
        <div style="display:flex; justify-content:space-between; font-size:12px;">
          <span>CPU Skip Gate (d3)</span>
          <span style="color:var(--green); font-weight:700;">0.092 ms</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; margin-top:6px;">
          <span>Local AI VRAM Penalty</span>
          <span style="color:var(--cyan); font-weight:700;">0 MB</span>
        </div>
      </div>
    </div>
  </div>

  <div class="main">
    <div class="chat-log" id="chat-log">
      <div class="msg assistant">
        <div class="meta-tag meta-local">SYSTEM READY</div>
Welcome to <b>Jupiter Studio</b>!
Your hybrid workstation is active:
• <b>Local Models:</b> Running directly on your Ollama server with zero rate limits.
• <b>Cloud Grants:</b> Ready to burst to 31B/70B models via AMD Token Lab & DigitalOcean MI300X.
Type your prompt below to start building.
      </div>
    </div>

    <div class="input-bar">
      <textarea id="prompt-input" rows="2" placeholder="Ask your local Ollama or cloud model anything... (Ctrl+Enter to send)" onkeydown="if(event.ctrlKey && event.key==='Enter') sendPrompt()"></textarea>
      <button class="btn" onclick="sendPrompt()">Run</button>
    </div>
  </div>

<script>
async function loadStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    document.getElementById('hw-name').innerText = data.gpu.device_name || 'CPU Mode';
    document.getElementById('hw-vram').innerText = `${data.gpu.used_vram_mb} / ${data.gpu.total_vram_mb} MB (${data.gpu.utilization_pct}% Load)`;
  } catch(e) {
    console.error(e);
  }
}
loadStatus();
setInterval(loadStatus, 5000);

async function sendPrompt() {
  const input = document.getElementById('prompt-input');
  const text = input.value.trim();
  if(!text) return;

  const target = document.getElementById('target-selector').value;
  const chatLog = document.getElementById('chat-log');

  // Add User Message
  const uMsg = document.createElement('div');
  uMsg.className = 'msg user';
  uMsg.innerText = text;
  chatLog.appendChild(uMsg);
  input.value = '';
  chatLog.scrollTop = chatLog.scrollHeight;

  // Add Loading Assistant Message
  const aMsg = document.createElement('div');
  aMsg.className = 'msg assistant';
  aMsg.innerHTML = `<div class="meta-tag meta-local">RUNNING...</div>Generating response...`;
  chatLog.appendChild(aMsg);
  chatLog.scrollTop = chatLog.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: text, target: target })
    });
    const data = await res.json();
    const tagClass = data.is_local ? 'meta-local' : 'meta-cloud';
    aMsg.innerHTML = `<div class="meta-tag ${tagClass}">${data.model_used} (${data.latency_ms} ms)</div>\n${escapeHtml(data.content)}`;
  } catch(err) {
    aMsg.innerHTML = `<div class="meta-tag meta-cloud">ERROR</div>${err.message}`;
  }
  chatLog.scrollTop = chatLog.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function onTargetChange() {}
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
        self.end_headers()
        self.wfile.write(payload)

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
            self._send_json({"gpu": prof.__dict__, "cloud": cloud})
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        if self.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            body = json.loads(raw.decode("utf-8")) if raw else {}
            prompt = body.get("prompt", "")
            target = body.get("target", "ollama:qwen2.5-coder:1.5b")

            import time

            t0 = time.perf_counter()

            if target.startswith("ollama:"):
                model_name = target.split(":", 1)[1]
                content = self._call_ollama(model_name, prompt)
                latency = round((time.perf_counter() - t0) * 1000, 2)
                self._send_json({
                    "model_used": f"Local Ollama: {model_name}",
                    "content": content,
                    "latency_ms": latency,
                    "is_local": True,
                })
                return

            if target.startswith("cloud:"):
                model_name = target.split(":", 1)[1]
                content, err = self._call_openai_compat(
                    base_url=os.getenv("TOKENLAB_BASE_URL", "https://api.tokenlab.amd.com/v1"),
                    api_key=os.getenv("TOKENLAB_API_KEY", ""),
                    model=model_name,
                    prompt=prompt,
                )
                latency = round((time.perf_counter() - t0) * 1000, 2)
                if err:
                    res = route_task(prompt, forced_model=model_name, save_checkpoint=False, log_to_advisor=False)
                    content = f"[Token Lab Note: {err}]\n\n{res.get('content', '')}"
                self._send_json({
                    "model_used": f"AMD Cloud: {model_name}",
                    "content": content,
                    "latency_ms": latency,
                    "is_local": False,
                })
                return

            if target.startswith("do:"):
                model_name = target.split(":", 1)[1]
                content, err = self._call_openai_compat(
                    base_url=os.getenv("DO_INFERENCE_BASE_URL", "https://inference.do-ai.run/v1"),
                    api_key=os.getenv("DO_MODEL_ACCESS_KEY", ""),
                    model=model_name,
                    prompt=prompt,
                )
                latency = round((time.perf_counter() - t0) * 1000, 2)
                if err:
                    content = f"[DigitalOcean Note: {err}]"
                self._send_json({
                    "model_used": f"DigitalOcean MI300X: {model_name}",
                    "content": content,
                    "latency_ms": latency,
                    "is_local": False,
                })
                return

        self._send_json({"error": "Unknown endpoint"}, status=404)

    def _call_openai_compat(
        self,
        base_url: str,
        api_key: str,
        model: str,
        prompt: str,
    ) -> tuple[str, str]:
        """Direct zero-dependency OpenAI-compatible HTTP call (no mock fallback)."""
        clean_key = api_key.strip()
        if not clean_key:
            return "", "API key not configured in .env"
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant inside Jupiter Studio."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {clean_key}",
                "Content-Type": "application/json",
                "User-Agent": "JupiterStudio/0.2",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"], ""
        except Exception as exc:
            # Automatic fallback to AMD Token Lab Anthropic-compatible /v1/messages
            if "tokenlab.amd.com" in base_url:
                anth_text, anth_err = self._call_anthropic_messages(base_url, clean_key, model, prompt)
                if not anth_err:
                    return anth_text, ""
                return "", f"{exc} | /v1/messages: {anth_err}"
            return "", str(exc)

    def _call_anthropic_messages(
        self,
        base_url: str,
        api_key: str,
        model: str,
        prompt: str,
    ) -> tuple[str, str]:
        """Call AMD Token Lab Anthropic-compatible /v1/messages endpoint."""
        url = f"{base_url.rstrip('/')}/messages"
        payload = json.dumps({
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
                "User-Agent": "JupiterStudio/0.2",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                parts = [
                    blk.get("text", "")
                    for blk in data.get("content", [])
                    if isinstance(blk, dict) and blk.get("type") == "text"
                ]
                return "".join(parts).strip(), ""
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
            return f"[Ollama Call Failed]: {exc}\nEnsure Ollama is running on Windows (ollama serve)."


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), JupiterStudioHandler)
    print(f"[+] Jupiter Studio active at http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopped")


if __name__ == "__main__":
    main()

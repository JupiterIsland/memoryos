"""Jupiter Studio UI — Original Dark Workstation Look (restored from af08106)."""

STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Jupiter Studio // Hybrid AI Workstation</title>
<link rel="icon" type="image/png" href="/assets/jupiter_studio_icon.png" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
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


  /* ── FLAGSHIP TYPOGRAPHY, SCROLLBARS & SURFACE POLISH ─────────────── */
  :root {
    --font-sans: "Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --font-mono: "JetBrains Mono", "Cascadia Code", ui-monospace, SFMono-Regular, monospace;
    --bg: #090b10;
    --sidebar-bg: #0d1017;
    --card-bg: rgba(255, 255, 255, 0.032);
    --border: rgba(255, 255, 255, 0.085);
    --border-highlight: rgba(255, 255, 255, 0.16);
    --text: #eef1f7;
    --muted: #8a94a6;
    --orange: #ff6b1a;
    --cyan: #38bdf8;
    --green: #22c55e;
    --red: #f43f5e;
  }

  body {
    font-family: var(--font-sans) !important;
    font-size: 14px;
    letter-spacing: -0.011em;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-feature-settings: "cv02", "cv03", "cv04", "cv11";
  }

  /* Slim custom scrollbars (no glaring native Windows white track) */
  * {
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 255, 255, 0.16) transparent;
  }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 999px;
  }
  ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.28); }
  html[data-studio-theme="atari"] * {
    scrollbar-color: #000000 #ffffff;
  }
  html[data-studio-theme="atari"] ::-webkit-scrollbar-thumb {
    background: #000000;
  }

  /* Sidebar polish */
  .sidebar {
    width: 316px;
    padding: 18px 16px;
    gap: 14px;
    border-right: 1px solid var(--border);
  }
  .brand h1 {
    font-size: 15.5px;
    font-weight: 700;
    letter-spacing: -0.02em;
  }
  .brand p {
    font-size: 11.5px;
    color: var(--muted);
    margin-top: 1px;
  }
  .section-title {
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin-bottom: 7px;
  }
  .card {
    border-radius: 11px;
    padding: 13px 14px;
    border: 1px solid var(--border);
    background: var(--card-bg);
  }
  .hw-val {
    font-size: 13.5px;
    font-weight: 600;
    letter-spacing: -0.01em;
    font-variant-numeric: tabular-nums;
  }
  .select-box {
    font-family: var(--font-sans);
    font-size: 13px;
    font-weight: 500;
    padding: 10px 12px;
    border-radius: 9px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-highlight);
    color: var(--text);
  }
  .select-box option, .select-box optgroup {
    background: #111520;
    color: #eef1f7;
  }
  html[data-studio-theme="atari"] .select-box option,
  html[data-studio-theme="atari"] .select-box optgroup {
    background: #ffffff;
    color: #000000;
  }

  /* Custom sleek checkboxes inside workspace file list */
  .workspace-file-list {
    background: rgba(0, 0, 0, 0.24) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px;
    padding: 4px;
    max-height: 176px;
  }
  .workspace-file-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 7px;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--text);
    transition: background 0.12s;
  }
  .workspace-file-item:hover { background: rgba(255, 255, 255, 0.05); }
  .workspace-file-item input[type="checkbox"] {
    appearance: none;
    -webkit-appearance: none;
    width: 14px !important;
    height: 14px !important;
    min-width: 14px;
    padding: 0 !important;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.28);
    background: rgba(255, 255, 255, 0.04);
    cursor: pointer;
    position: relative;
    transition: all 0.12s;
  }
  .workspace-file-item input[type="checkbox"]:checked {
    background: var(--orange);
    border-color: var(--orange);
  }
  .workspace-file-item input[type="checkbox"]:checked::after {
    content: "";
    position: absolute;
    left: 4px;
    top: 1px;
    width: 4px;
    height: 8px;
    border: solid #fff;
    border-width: 0 1.8px 1.8px 0;
    transform: rotate(45deg);
  }

  /* Header & Theme Pill polish */
  .chat-header {
    height: 58px;
    padding: 0 24px;
    background: rgba(13, 16, 23, 0.78);
    backdrop-filter: blur(14px);
  }
  .chat-header .badge {
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 4px 10px;
    border-radius: 999px;
  }
  .theme-pill-group {
    border-radius: 8px;
    padding: 2px;
    gap: 2px;
  }
  .theme-pill-btn {
    font-family: var(--font-mono);
    font-size: 10.5px;
    padding: 5px 10px;
    border-radius: 6px;
    transition: all 0.15s;
  }
  .btn-secondary {
    font-family: var(--font-sans);
    font-size: 12.5px;
    font-weight: 600;
    border-radius: 8px;
    padding: 7px 12px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-highlight);
    color: var(--text);
  }
  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.10);
    border-color: rgba(255, 255, 255, 0.25);
  }

  /* Centered, spacious conversation thread */
  .chat-log {
    padding: 28px 32px;
    align-items: center;
  }
  .msg {
    width: 100% !important;
    max-width: 840px !important;
    padding: 18px 22px;
    border-radius: 14px;
    font-size: 14.5px;
    line-height: 1.68;
  }
  .msg.user {
    align-self: center;
    max-width: 840px !important;
    background: rgba(255, 107, 26, 0.10);
    border: 1px solid rgba(255, 107, 26, 0.28);
    color: var(--text);
  }
  .msg.assistant {
    align-self: center;
    background: rgba(255, 255, 255, 0.028);
    border: 1px solid var(--border);
    border-left: 3px solid var(--cyan);
  }
  .md-body p { margin-bottom: 10px; }
  .md-body li { margin-bottom: 5px; }
  .md-body code, .code-block-container pre {
    font-family: var(--font-mono) !important;
  }

  /* Starter prompt chips inside welcome card */
  .starter-chips {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin-top: 16px;
  }
  .starter-chip {
    text-align: left;
    padding: 10px 13px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 12.5px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.14s;
  }
  .starter-chip:hover {
    border-color: var(--orange);
    background: rgba(255, 107, 26, 0.08);
    transform: translateY(-1px);
  }
  .starter-chip span {
    display: block;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 2px;
  }

  /* Speculative Neural Radar — sleek pill bar with tabular-nums */
  .spec-radar {
    padding: 8px 24px;
    gap: 10px;
    background: rgba(255, 255, 255, 0.018);
    border-top: 1px solid var(--border);
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
  }
  .radar-cell {
    padding: 6px 12px;
    border-radius: 9px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border);
  }
  .radar-k {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.05em;
  }
  .radar-v {
    font-size: 11.5px;
    font-weight: 600;
  }

  /* Unified sleek input composer */
  .input-bar-wrapper {
    padding: 12px 24px 16px;
    background: rgba(13, 16, 23, 0.85);
    border-top: 1px solid var(--border);
  }
  .input-bar {
    max-width: 840px;
    margin: 0 auto;
    width: 100%;
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid var(--border-highlight);
    border-radius: 14px;
    padding: 8px 10px;
    gap: 8px;
    align-items: center;
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  .input-bar:focus-within {
    border-color: var(--orange);
    box-shadow: 0 0 0 3px rgba(255, 107, 26, 0.14);
  }
  #prompt-input {
    background: transparent !important;
    border: none !important;
    font-family: var(--font-sans) !important;
    font-size: 14.5px !important;
    line-height: 1.5;
    padding: 6px 8px !important;
    color: var(--text) !important;
  }
  .btn-icon {
    width: 36px;
    height: 36px;
    border-radius: 9px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border);
    color: var(--muted);
    transition: all 0.14s;
  }
  .btn-icon:hover {
    color: var(--text);
    border-color: var(--border-highlight);
    background: rgba(255, 255, 255, 0.09);
  }
  .btn-arena {
    font-family: var(--font-sans);
    font-size: 12.5px;
    font-weight: 600;
    height: 36px;
    padding: 0 13px;
    border-radius: 9px;
  }
  .btn {
    font-family: var(--font-sans);
    font-size: 13px;
    font-weight: 700;
    height: 36px;
    padding: 0 18px;
    border-radius: 9px;
    letter-spacing: -0.01em;
  }


  /* ── ARCHITECTURAL SHARP GLASSMORPHISM (SMOKED CRYSTAL EDITION) ────── */
  :root {
    --bg: #05070c;
    --sidebar-bg: rgba(11, 15, 24, 0.72);
    --card-bg: linear-gradient(155deg, rgba(255, 255, 255, 0.065) 0%, rgba(255, 255, 255, 0.02) 100%);
    --border: rgba(255, 255, 255, 0.13);
    --border-highlight: rgba(255, 255, 255, 0.24);
    --rim: inset 0 1px 0 rgba(255, 255, 255, 0.20);
    --depth: 0 14px 36px rgba(0, 0, 0, 0.52);
    --text: #ffffff;
    --muted: #98a4b8;
    --orange: #ff6a00;
    --cyan: #22d3ee;
    --green: #10b981;
    --red: #fb7185;
  }

  /* Optical light-pool + faint architectural grid so frosted glass actually refracts depth */
  body {
    background:
      radial-gradient(ellipse 55% 45% at 78% 8%, rgba(34, 211, 238, 0.14), transparent 65%),
      radial-gradient(ellipse 48% 42% at 22% 92%, rgba(255, 106, 0, 0.13), transparent 65%),
      linear-gradient(rgba(255, 255, 255, 0.024) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.024) 1px, transparent 1px),
      #05070c !important;
    background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px, 100% 100% !important;
  }
  .main {
    background: transparent !important;
  }

  /* Smoked-glass sidebar with crisp 1px edge */
  .sidebar {
    background: var(--sidebar-bg) !important;
    backdrop-filter: blur(26px) saturate(165%) !important;
    -webkit-backdrop-filter: blur(26px) saturate(165%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.14) !important;
    box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.06), 12px 0 40px rgba(0, 0, 0, 0.55) !important;
  }

  /* Sharper architectural geometry + crystalline top-rim highlight */
  .card {
    background: var(--card-bg) !important;
    backdrop-filter: blur(18px) saturate(150%);
    -webkit-backdrop-filter: blur(18px) saturate(150%);
    border: 1px solid var(--border) !important;
    border-radius: 5px !important;
    box-shadow: var(--rim), 0 8px 24px rgba(0, 0, 0, 0.34);
  }
  .select-box {
    border-radius: 4px !important;
    background: rgba(8, 12, 20, 0.72) !important;
    border: 1px solid var(--border-highlight) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.10);
    color: #ffffff !important;
  }
  .select-box:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 1px var(--cyan), 0 0 18px rgba(34, 211, 238, 0.22);
  }

  /* Kill glaring white native checkboxes (.ws-file-cb) -> sharp smoked-glass squares */
  .workspace-file-list {
    border-radius: 4px !important;
    background: rgba(4, 7, 13, 0.65) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
  }
  input[type="checkbox"],
  .ws-file-cb {
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 14px !important;
    height: 14px !important;
    min-width: 14px !important;
    padding: 0 !important;
    margin: 0 !important;
    border-radius: 2px !important;
    border: 1px solid rgba(255, 255, 255, 0.30) !important;
    background: rgba(255, 255, 255, 0.05) !important;
    cursor: pointer;
    position: relative;
    vertical-align: middle;
    transition: all 0.12s ease;
  }
  input[type="checkbox"]:hover,
  .ws-file-cb:hover {
    border-color: var(--cyan) !important;
  }
  input[type="checkbox"]:checked,
  .ws-file-cb:checked {
    background: var(--orange) !important;
    border-color: var(--orange) !important;
    box-shadow: 0 0 10px rgba(255, 106, 0, 0.45);
  }
  input[type="checkbox"]:checked::after,
  .ws-file-cb:checked::after {
    content: "";
    position: absolute;
    left: 4px;
    top: 1px;
    width: 4px;
    height: 8px;
    border: solid #ffffff;
    border-width: 0 1.8px 1.8px 0;
    transform: rotate(45deg);
  }

  /* Crisp frosted top header */
  .chat-header {
    background: rgba(10, 14, 22, 0.66) !important;
    backdrop-filter: blur(22px) saturate(165%) !important;
    -webkit-backdrop-filter: blur(22px) saturate(165%) !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.14) !important;
    box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.04), 0 8px 28px rgba(0, 0, 0, 0.35);
  }
  .chat-header .badge {
    border-radius: 3px !important;
    background: rgba(34, 211, 238, 0.12) !important;
    border: 1px solid rgba(34, 211, 238, 0.48) !important;
    color: #67e8f9 !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16);
  }
  .theme-pill-group {
    border-radius: 4px !important;
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
  }
  .theme-pill-btn {
    border-radius: 2px !important;
    color: #c5cedd;
  }
  .theme-pill-btn.active {
    background: linear-gradient(135deg, #ff6a00, #ff8533) !important;
    color: #ffffff !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.30);
  }

  /* Sharp cut-crystal glass message panes */
  .msg {
    border-radius: 6px !important;
    backdrop-filter: blur(22px) saturate(160%);
    -webkit-backdrop-filter: blur(22px) saturate(160%);
    box-shadow: var(--rim), var(--depth);
  }
  .msg.assistant {
    background: linear-gradient(155deg, rgba(19, 25, 39, 0.78) 0%, rgba(11, 15, 24, 0.68) 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-left: 2px solid var(--cyan) !important;
  }
  .msg.user {
    background: linear-gradient(155deg, rgba(255, 106, 0, 0.16) 0%, rgba(255, 106, 0, 0.06) 100%) !important;
    border: 1px solid rgba(255, 106, 0, 0.42) !important;
    color: #ffffff !important;
  }
  .meta-tag {
    border-radius: 3px !important;
    font-weight: 700;
    letter-spacing: 0.06em;
  }
  .md-body { color: #e2e8f2; }
  .md-body h1, .md-body h2, .md-body h3 { color: #ffffff; font-weight: 700; }

  /* Sharp faceted starter tiles */
  .starter-chip {
    border-radius: 4px !important;
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.13) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
    color: #f8fafc !important;
  }
  .starter-chip:hover {
    background: rgba(34, 211, 238, 0.09) !important;
    border-color: rgba(34, 211, 238, 0.55) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25), 0 6px 20px rgba(0, 0, 0, 0.35);
  }
  .starter-chip span { color: var(--cyan); font-weight: 700; }

  /* Sharp glass Speculative Neural Radar strip */
  .spec-radar {
    background: rgba(8, 12, 20, 0.62) !important;
    backdrop-filter: blur(20px) saturate(160%);
    border-top: 1px solid rgba(255, 255, 255, 0.13) !important;
  }
  .radar-cell {
    border-radius: 4px !important;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.13) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16);
  }

  /* Precision glass composer dock + sharp controls */
  .input-bar-wrapper {
    background: rgba(8, 11, 18, 0.72) !important;
    backdrop-filter: blur(24px) saturate(170%) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.12) !important;
  }
  .input-bar {
    border-radius: 6px !important;
    background: rgba(16, 22, 34, 0.74) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18), 0 10px 28px rgba(0, 0, 0, 0.45);
  }
  .input-bar:focus-within {
    border-color: var(--orange) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22), 0 0 0 1px var(--orange), 0 0 24px rgba(255, 106, 0, 0.22) !important;
  }
  .btn, .btn-secondary, .btn-icon, .btn-arena {
    border-radius: 4px !important;
  }
  .btn {
    background: linear-gradient(135deg, #ff6a00 0%, #ff4500 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.26) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35), 0 4px 16px rgba(255, 106, 0, 0.35);
    color: #ffffff !important;
  }
  .btn-arena {
    background: rgba(34, 211, 238, 0.10) !important;
    border: 1px solid rgba(34, 211, 238, 0.48) !important;
    color: #67e8f9 !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18);
  }
  .btn-arena:hover {
    background: rgba(34, 211, 238, 0.18) !important;
    border-color: #67e8f9 !important;
  }
  .btn-secondary {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16);
    color: #ffffff !important;
  }
  .btn-icon {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    color: #cbd5e1 !important;
  }
  .code-block-container {
    border-radius: 5px !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
  }

  /* RADEON SHARP CRYSTAL THEME */
  html[data-studio-theme="radeon"] body {
    background:
      radial-gradient(ellipse 55% 45% at 78% 10%, rgba(237, 28, 36, 0.20), transparent 65%),
      radial-gradient(ellipse 48% 42% at 22% 90%, rgba(255, 176, 0, 0.14), transparent 65%),
      linear-gradient(rgba(255, 255, 255, 0.022) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.022) 1px, transparent 1px),
      #080507 !important;
    background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px, 100% 100% !important;
  }
  html[data-studio-theme="radeon"] .sidebar {
    background: rgba(18, 9, 13, 0.76) !important;
    border-right-color: rgba(237, 28, 36, 0.30) !important;
  }

  /* ATARI ST / COMMODORE HI-RES MONOCHROME BLACK & WHITE THEME */
  html[data-studio-theme="atari"] {
    --bg: #ffffff;
    --sidebar-bg: #ffffff;
    --panel: #ffffff;
    --card-bg: #ffffff;
    --border: #000000;
    --border-highlight: #000000;
    --text: #000000;
    --muted: #222222;
    --orange: #000000;
    --cyan: #000000;
    --green: #000000;
    --red: #000000;
    --code-bg: #000000;
  }
  html[data-studio-theme="atari"] body {
    font-family: var(--font-mono) !important;
    background:
      radial-gradient(#000000 0.55px, transparent 0.55px),
      radial-gradient(#000000 0.55px, #ffffff 0.55px) !important;
    background-size: 4px 4px !important;
    background-position: 0 0, 2px 2px !important;
    color: #000000 !important;
  }
  html[data-studio-theme="atari"] * {
    border-radius: 0px !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
  }
  html[data-studio-theme="atari"] .sidebar {
    background: #ffffff !important;
    border-right: 2px solid #000000 !important;
    box-shadow: none !important;
  }
  html[data-studio-theme="atari"] .card,
  html[data-studio-theme="atari"] .msg.assistant,
  html[data-studio-theme="atari"] .radar-cell,
  html[data-studio-theme="atari"] .input-bar {
    background: #ffffff !important;
    border: 2px solid #000000 !important;
    box-shadow: 3px 3px 0px #000000 !important;
    color: #000000 !important;
  }
  html[data-studio-theme="atari"] .msg.assistant {
    border-left: 5px solid #000000 !important;
  }
  html[data-studio-theme="atari"] .msg.user {
    background: #000000 !important;
    color: #ffffff !important;
    border: 2px solid #000000 !important;
    box-shadow: 3px 3px 0px #555555 !important;
  }
  html[data-studio-theme="atari"] .chat-header,
  html[data-studio-theme="atari"] .input-bar-wrapper,
  html[data-studio-theme="atari"] .spec-radar {
    background: #ffffff !important;
    border-color: #000000 !important;
    border-width: 2px !important;
    box-shadow: none !important;
  }
  html[data-studio-theme="atari"] #quantum-canvas {
    filter: grayscale(100%) contrast(300%);
    opacity: 0.25;
  }
  html[data-studio-theme="atari"] .chat-header .badge,
  html[data-studio-theme="atari"] .meta-tag,
  html[data-studio-theme="atari"] .rc-pill {
    background: #000000 !important;
    color: #ffffff !important;
    border: 1px solid #000000 !important;
    box-shadow: none !important;
  }
  html[data-studio-theme="atari"] .md-body,
  html[data-studio-theme="atari"] .md-body h1,
  html[data-studio-theme="atari"] .md-body h2,
  html[data-studio-theme="atari"] .md-body h3,
  html[data-studio-theme="atari"] .select-box,
  html[data-studio-theme="atari"] .starter-chip,
  html[data-studio-theme="atari"] .starter-chip span,
  html[data-studio-theme="atari"] .theme-pill-btn,
  html[data-studio-theme="atari"] .hw-val,
  html[data-studio-theme="atari"] .radar-k,
  html[data-studio-theme="atari"] .radar-v,
  html[data-studio-theme="atari"] #prompt-input {
    color: #000000 !important;
  }
  html[data-studio-theme="atari"] .select-box,
  html[data-studio-theme="atari"] .starter-chip,
  html[data-studio-theme="atari"] .workspace-file-list,
  html[data-studio-theme="atari"] .btn-secondary,
  html[data-studio-theme="atari"] .btn-icon,
  html[data-studio-theme="atari"] .btn-arena {
    background: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #000000 !important;
    box-shadow: 2px 2px 0px #000000 !important;
  }
  html[data-studio-theme="atari"] .starter-chip:hover,
  html[data-studio-theme="atari"] .btn-secondary:hover,
  html[data-studio-theme="atari"] .btn-icon:hover,
  html[data-studio-theme="atari"] .btn-arena:hover,
  html[data-studio-theme="atari"] .btn-arena.active,
  html[data-studio-theme="atari"] .theme-pill-btn.active,
  html[data-studio-theme="atari"] .btn {
    background: #000000 !important;
    color: #ffffff !important;
    border: 2px solid #000000 !important;
    box-shadow: 2px 2px 0px #555555 !important;
  }
  html[data-studio-theme="atari"] .starter-chip:hover span {
    color: #ffffff !important;
  }
  html[data-studio-theme="atari"] .theme-pill-group {
    background: #ffffff !important;
    border: 2px solid #000000 !important;
  }
  html[data-studio-theme="atari"] input[type="checkbox"],
  html[data-studio-theme="atari"] .ws-file-cb {
    border: 2px solid #000000 !important;
    background: #ffffff !important;
  }
  html[data-studio-theme="atari"] input[type="checkbox"]:checked,
  html[data-studio-theme="atari"] .ws-file-cb:checked {
    background: #000000 !important;
    border-color: #000000 !important;
    box-shadow: none !important;
  }
  html[data-studio-theme="atari"] #rad-mlp-bar {
    background: repeating-linear-gradient(45deg, #000000, #000000 2px, #ffffff 2px, #ffffff 5px) !important;
    opacity: 0.14;
  }
  html[data-studio-theme="atari"] .code-block-container {
    background: #000000 !important;
    color: #ffffff !important;
    border: 2px solid #000000 !important;
  }
  html[data-studio-theme="atari"] .logo-badge img {
    filter: grayscale(100%) contrast(220%);
  }

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
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Export Copilot Bundle
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
          <button class="theme-pill-btn" data-t="atari" onclick="setStudioTheme('atari')">ATARI B&amp;W</button>
        </div>
        <button class="btn-secondary" onclick="clearChat()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/></svg>Clear</button>
      </div>
    </div>

    <div class="chat-log" id="chat-log">
      <div class="msg assistant">
        <div class="meta-tag meta-auto">MEMORYOS v1.0.0-RC1 // ZERO LOCAL VRAM</div>
        <div class="md-body">
          <h3 style="margin-top:2px; font-size:18px; letter-spacing:-0.02em;">Jupiter Studio Workstation</h3>
          <p style="color:var(--muted);">Hardware-aware routing via 0.091 ms AMD Zen 3 gate and 5.37 μs Speculative Offload MLP. Local GPU VRAM remains completely free for native apps.</p>
          <div class="starter-chips">
            <button class="starter-chip" onclick="useStarter('Review the selected repository files for bugs, security risks, or performance improvements.')">
              <span>Code Audit</span>
              Review selected workspace files
            </button>
            <button class="starter-chip" onclick="useStarter('Explain how MemoryOS keeps local VRAM at 0 MB while running 27B–31B models.')">
              <span>Architecture</span>
              Trace zero-VRAM offload pipeline
            </button>
            <button class="starter-chip" onclick="toggleDualArena(); useStarter('Compare Python asyncio vs multiprocessing for I/O-bound telemetry pipelines in 5 bullet points.')">
              <span>Dual Arena Demo</span>
              Race two models side-by-side live
            </button>
            <button class="starter-chip" onclick="useStarter('Write focused Python unittest coverage for the attached module.')">
              <span>Verification</span>
              Generate targeted unit tests
            </button>
          </div>
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
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
        </button>
        <button class="btn-icon" id="upload-image-btn" title="Attach Screenshot or Image" onclick="document.getElementById('image-file-input').click()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        </button>
        <textarea id="prompt-input" rows="2" placeholder="Ask anything or drag & drop files here... (Ctrl+Enter to send)" onkeydown="if(event.ctrlKey && event.key==='Enter') sendPrompt()"></textarea>
        <div class="input-actions">
          <button class="btn-arena" id="btn-arena" onclick="toggleDualArena()" title="Stream 2 models side-by-side in a live split-screen shootout"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="18" rx="1"/><rect x="14" y="3" width="7" height="18" rx="1"/></svg> Dual Arena</button>
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
    const lowerName = (file.name || "").toLowerCase();
    if (
      lowerName === ".env" ||
      (lowerName.startsWith(".env.") && lowerName !== ".env.example") ||
      lowerName.endsWith(".pem") ||
      lowerName.endsWith(".key") ||
      lowerName === "credentials.json"
    ) {
      showToast(`🔒 Blocked ${file.name}: secret files are never sent to cloud models`);
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

/* ── 1. THEME SWITCHER (QUANTUM / RADEON / ATARI B&W) ────────────────── */
function setStudioTheme(theme) {
  if (theme === "daylight") theme = "atari";
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
    const colA = theme === "radeon" ? "237, 28, 36" : (theme === "atari" ? "0, 0, 0" : "255, 106, 0");
    const colB = theme === "radeon" ? "255, 176, 0" : (theme === "atari" ? "0, 0, 0" : "0, 240, 255");

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
    const latStr = Number(d.mlp_latency_us) >= 1000 ? `${(Number(d.mlp_latency_us)/1000).toFixed(2)} ms` : `${Number(d.mlp_latency_us).toFixed(1)} μs`;
    document.getElementById("rad-mlp").innerText = `${pct}% · ${latStr}`;
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
function useStarter(txt) { const el = document.getElementById("prompt-input"); el.value = txt; updateSpeculativeRadar(); sendPrompt(); }
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


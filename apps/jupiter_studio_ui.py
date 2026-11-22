"""Single-module Precision Obsidian UI for Jupiter Studio (v1.1.0)."""

STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="quantum">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Jupiter Studio — MemoryOS Command Workstation</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700&display=swap" rel="stylesheet" />
<style>
  :root,
  [data-theme="quantum"] {
    --bg: #090a0f;
    --bg-rail: #0d0f15;
    --bg-surface: #12151e;
    --bg-elevated: #171b26;
    --bg-hover: rgba(255, 255, 255, 0.045);
    --bg-active: rgba(56, 189, 248, 0.11);
    --border: rgba(255, 255, 255, 0.08);
    --border-strong: rgba(255, 255, 255, 0.15);
    --border-accent: rgba(56, 189, 248, 0.35);
    --text: #f3f5f8;
    --text-soft: #c7cdd8;
    --muted: #7f8798;
    --accent: #38bdf8;
    --accent-dim: rgba(56, 189, 248, 0.14);
    --cyan: #38bdf8;
    --amber: #f59e0b;
    --orange: #fb923c;
    --green: #34d399;
    --red: #f87171;
    --purple: #a78bfa;
    --user-bg: #161b26;
    --code-bg: #0b0d13;
    --shadow-lg: 0 20px 50px rgba(0, 0, 0, 0.55);
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
    --font-sans: "Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  }

  [data-theme="radeon"] {
    --bg: #0c090a;
    --bg-rail: #120d0f;
    --bg-surface: #181114;
    --bg-elevated: #21161a;
    --bg-hover: rgba(255, 255, 255, 0.05);
    --bg-active: rgba(239, 68, 68, 0.14);
    --border: rgba(255, 200, 190, 0.09);
    --border-strong: rgba(255, 200, 190, 0.18);
    --border-accent: rgba(239, 68, 68, 0.42);
    --text: #f7f1f1;
    --text-soft: #d9c7c9;
    --muted: #9b8186;
    --accent: #ef4444;
    --accent-dim: rgba(239, 68, 68, 0.15);
    --cyan: #f59e0b;
    --amber: #fbbf24;
    --orange: #f97316;
    --green: #4ade80;
    --red: #ff5a5f;
    --purple: #fb7185;
    --user-bg: #1e1316;
    --code-bg: #0b0708;
    --shadow-lg: 0 22px 54px rgba(0, 0, 0, 0.65);
  }

  [data-theme="atari"] {
    --bg: #000000;
    --bg-rail: #070707;
    --bg-surface: #0e0e0e;
    --bg-elevated: #161616;
    --bg-hover: rgba(255, 255, 255, 0.08);
    --bg-active: rgba(255, 255, 255, 0.16);
    --border: rgba(255, 255, 255, 0.22);
    --border-strong: rgba(255, 255, 255, 0.48);
    --border-accent: #ffffff;
    --text: #ffffff;
    --text-soft: #e5e5e5;
    --muted: #a3a3a3;
    --accent: #ffffff;
    --accent-dim: rgba(255, 255, 255, 0.14);
    --cyan: #ffffff;
    --amber: #d4d4d4;
    --orange: #e5e5e5;
    --green: #ffffff;
    --red: #ffffff;
    --purple: #d4d4d4;
    --user-bg: #141414;
    --code-bg: #050505;
    --shadow-lg: 0 18px 40px rgba(0, 0, 0, 0.9);
  }

  * {
    box-sizing: border-box;
  }

  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 14px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }

  #quantum-canvas {
    position: fixed;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
    opacity: 0.55;
  }

  .studio-shell {
    position: relative;
    z-index: 1;
    display: flex;
    width: 100%;
    height: 100vh;
    overflow: hidden;
  }

  /* ── LEFT RAIL ─────────────────────────────────────────── */
  .sidebar {
    width: 292px;
    min-width: 292px;
    height: 100vh;
    background: var(--bg-rail);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    transition: margin-left 0.2s ease, transform 0.2s ease;
    z-index: 20;
  }

  .sidebar.collapsed {
    margin-left: -292px;
  }

  .brand-header {
    height: 54px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  .brand-lockup {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .brand-mark {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    background: var(--accent-dim);
    border: 1px solid var(--border-accent);
    display: grid;
    place-items: center;
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  .brand-title {
    font-size: 14px;
    font-weight: 700;
    letter-spacing: -0.015em;
    color: var(--text);
  }

  .brand-ver {
    font-family: var(--font-mono);
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 999px;
    border: 1px solid var(--border);
    color: var(--muted);
    background: rgba(255, 255, 255, 0.02);
  }

  .rail-actions {
    padding: 12px 12px 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  .btn-new-session {
    width: 100%;
    height: 36px;
    border-radius: 8px;
    border: 1px solid var(--border-strong);
    background: var(--bg-elevated);
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 13px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 12px;
    cursor: pointer;
    transition: border-color 0.15s ease, background 0.15s ease;
  }

  .btn-new-session:hover {
    border-color: var(--border-accent);
    background: var(--bg-hover);
  }

  .kbd-hint {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1px 5px;
    background: rgba(255, 255, 255, 0.02);
  }

  .rail-tabs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 3px;
    gap: 3px;
  }

  .rail-tab {
    height: 28px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--muted);
    font-family: var(--font-sans);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: all 0.15s ease;
  }

  .rail-tab.active {
    background: var(--bg-elevated);
    color: var(--text);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
  }

  .rail-pane {
    flex: 1;
    min-height: 0;
    display: none;
    flex-direction: column;
    overflow: hidden;
  }

  .rail-pane.active {
    display: flex;
  }

  /* Sessions list */
  .session-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .session-item {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 9px 10px;
    border-radius: 8px;
    border: 1px solid transparent;
    cursor: pointer;
    transition: background 0.14s ease, border-color 0.14s ease;
  }

  .session-item:hover {
    background: var(--bg-hover);
    border-color: var(--border);
  }

  .session-item.active {
    background: var(--bg-active);
    border-color: var(--border-accent);
  }

  .session-main {
    min-width: 0;
    flex: 1;
  }

  .session-title {
    font-size: 12.5px;
    font-weight: 500;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .session-meta {
    margin-top: 2px;
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .session-del {
    opacity: 0;
    width: 22px;
    height: 22px;
    border: none;
    border-radius: 5px;
    background: transparent;
    color: var(--muted);
    cursor: pointer;
    display: grid;
    place-items: center;
    font-size: 14px;
    line-height: 1;
    flex-shrink: 0;
  }

  .session-item:hover .session-del,
  .session-item.active .session-del {
    opacity: 0.85;
  }

  .session-del:hover {
    opacity: 1;
    color: var(--red);
    background: rgba(248, 113, 113, 0.12);
  }

  /* Workspace pane */
  .ws-toolbar {
    padding: 10px 12px 8px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  .ws-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 11px;
    color: var(--muted);
  }

  .branch-pill {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--accent);
    background: var(--accent-dim);
    border: 1px solid var(--border-accent);
    border-radius: 999px;
    padding: 1px 8px;
    max-width: 155px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .ws-input {
    width: 100%;
    height: 30px;
    border-radius: 7px;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    color: var(--text);
    padding: 0 10px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    outline: none;
  }

  .ws-input:focus {
    border-color: var(--border-accent);
  }

  .ws-btn-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }

  .btn-mini {
    height: 27px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    color: var(--text-soft);
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.14s ease;
  }

  .btn-mini:hover {
    border-color: var(--border-strong);
    color: var(--text);
    background: var(--bg-hover);
  }

  .ws-file-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 6px 10px;
  }

  .ws-file-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 8px;
    border-radius: 6px;
    cursor: pointer;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-soft);
    user-select: none;
  }

  .ws-file-row:hover {
    background: var(--bg-hover);
    color: var(--text);
  }

  .ws-file-row input {
    accent-color: var(--accent);
    margin: 0;
  }

  /* Bottom Telemetry Dock */
  .telemetry-dock {
    padding: 12px 14px;
    border-top: 1px solid var(--border);
    background: rgba(0, 0, 0, 0.22);
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 9px;
  }

  .tel-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 11px;
  }

  .tel-title {
    font-weight: 600;
    color: var(--text-soft);
    letter-spacing: 0.02em;
    text-transform: uppercase;
    font-size: 10px;
  }

  .health-pill {
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 600;
    padding: 1px 7px;
    border-radius: 999px;
    border: 1px solid var(--border);
    color: var(--green);
    background: rgba(52, 211, 153, 0.08);
  }

  .hw-gpu-line {
    font-family: var(--font-sans);
    font-size: 11.5px;
    font-weight: 600;
    color: var(--text);
    line-height: 1.3;
  }

  .hw-vram-line {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--muted);
  }

  .vram-track {
    width: 100%;
    height: 4px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    overflow: hidden;
  }

  .vram-fill {
    height: 100%;
    width: 0%;
    background: var(--accent);
    transition: width 0.35s ease;
  }

  .tel-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    padding-top: 4px;
    border-top: 1px solid var(--border);
  }

  .tel-cell {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .tel-k {
    font-size: 9.5px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--muted);
  }

  .tel-v {
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* ── MAIN STAGE ────────────────────────────────────────── */
  .stage {
    flex: 1;
    min-width: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  .topbar {
    height: 54px;
    padding: 0 20px;
    border-bottom: 1px solid var(--border);
    background: rgba(9, 10, 15, 0.72);
    backdrop-filter: blur(12px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-shrink: 0;
  }

  [data-theme="radeon"] .topbar {
    background: rgba(12, 9, 10, 0.78);
  }

  [data-theme="atari"] .topbar {
    background: rgba(0, 0, 0, 0.92);
  }

  .topbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }

  .icon-btn {
    width: 32px;
    height: 32px;
    border-radius: 7px;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    color: var(--text-soft);
    display: grid;
    place-items: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.14s ease;
  }

  .icon-btn:hover {
    border-color: var(--border-strong);
    color: var(--text);
  }

  .target-group {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }

  #target-selector {
    height: 32px;
    max-width: 340px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    color: var(--text);
    padding: 0 10px;
    font-family: var(--font-mono);
    font-size: 12px;
    outline: none;
    cursor: pointer;
  }

  #target-selector:focus {
    border-color: var(--border-accent);
  }

  .cmd-trigger {
    height: 32px;
    padding: 0 10px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    color: var(--text-soft);
    font-family: var(--font-sans);
    font-size: 12px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.14s ease;
  }

  .cmd-trigger:hover {
    border-color: var(--border-accent);
    color: var(--text);
  }

  .topbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .theme-switch {
    display: flex;
    align-items: center;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 2px;
    gap: 2px;
  }

  .theme-btn {
    height: 26px;
    padding: 0 9px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.14s ease;
  }

  .theme-btn.active {
    background: var(--bg-elevated);
    color: var(--text);
    border: 1px solid var(--border);
  }

  .btn-clear {
    height: 30px;
    padding: 0 10px;
    border-radius: 7px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--muted);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
  }

  .btn-clear:hover {
    color: var(--text);
    border-color: var(--border-strong);
    background: var(--bg-hover);
  }

  /* ── THREAD & MESSAGES ─────────────────────────────────── */
  .thread-wrap {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 28px 24px 16px;
    scroll-behavior: smooth;
  }

  .thread-inner {
    width: 100%;
    max-width: 820px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .empty-state {
    margin: 56px auto 24px;
    max-width: 640px;
    width: 100%;
    text-align: left;
  }

  .empty-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent);
    background: var(--accent-dim);
    border: 1px solid var(--border-accent);
    padding: 4px 10px;
    border-radius: 999px;
    margin-bottom: 14px;
  }

  .empty-title {
    margin: 0 0 8px;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.025em;
    color: var(--text);
  }

  .empty-sub {
    margin: 0 0 22px;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.6;
  }

  .starter-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .starter-card {
    text-align: left;
    padding: 13px 15px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    color: var(--text);
    cursor: pointer;
    transition: border-color 0.15s ease, transform 0.15s ease, background 0.15s ease;
  }

  .starter-card:hover {
    border-color: var(--border-accent);
    background: var(--bg-elevated);
    transform: translateY(-1px);
  }

  .starter-k {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--accent);
    margin-bottom: 4px;
  }

  .starter-t {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  }

  .msg {
    display: flex;
    flex-direction: column;
    gap: 8px;
    animation: msgIn 0.18s ease-out;
  }

  @keyframes msgIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .msg.user {
    align-self: flex-end;
    max-width: 82%;
    background: var(--user-bg);
    border: 1px solid var(--border-strong);
    border-radius: 12px 12px 3px 12px;
    padding: 12px 16px;
    color: var(--text);
  }

  .msg.assistant {
    align-self: stretch;
    padding: 2px 0 4px 16px;
    border-left: 2px solid var(--border-accent);
  }

  .msg-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .meta-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--muted);
  }

  .meta-local { color: var(--green); }
  .meta-cloud { color: var(--accent); }
  .meta-auto  { color: var(--amber); }
  .meta-error { color: var(--red); }

  .msg-copy-btn {
    border: 1px solid var(--border);
    background: var(--bg-surface);
    color: var(--muted);
    border-radius: 5px;
    padding: 2px 8px;
    font-family: var(--font-mono);
    font-size: 10.5px;
    cursor: pointer;
  }

  .msg-copy-btn:hover {
    color: var(--text);
    border-color: var(--border-strong);
  }

  .reasoning-box {
    border: 1px solid var(--border);
    background: var(--bg-surface);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12.5px;
  }

  .reasoning-box summary {
    cursor: pointer;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--muted);
    user-select: none;
  }

  .reasoning-content {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--text-soft);
    white-space: pre-wrap;
    line-height: 1.5;
  }

  /* Markdown styles */
  .md-body {
    color: var(--text);
    font-size: 14px;
    line-height: 1.65;
    word-break: break-word;
  }

  .md-body p { margin: 0 0 10px; }
  .md-body p:last-child { margin-bottom: 0; }
  .md-body h1, .md-body h2, .md-body h3 {
    margin: 14px 0 8px;
    font-weight: 700;
    letter-spacing: -0.015em;
  }
  .md-body h1 { font-size: 18px; }
  .md-body h2 { font-size: 16px; }
  .md-body h3 { font-size: 14.5px; }
  .md-body ul, .md-body ol { margin: 6px 0 10px; padding-left: 20px; }
  .md-body li { margin: 3px 0; }
  .md-body blockquote {
    margin: 8px 0;
    padding: 6px 12px;
    border-left: 2px solid var(--border-strong);
    color: var(--text-soft);
    background: rgba(255, 255, 255, 0.02);
  }
  .md-body code {
    font-family: var(--font-mono);
    font-size: 12.5px;
    padding: 1.5px 5px;
    border-radius: 5px;
    background: var(--code-bg);
    border: 1px solid var(--border);
  }
  .md-body pre {
    position: relative;
    margin: 10px 0;
    border-radius: 9px;
    border: 1px solid var(--border);
    background: var(--code-bg);
    overflow: hidden;
  }
  .code-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 12px;
    background: rgba(255, 255, 255, 0.03);
    border-bottom: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--muted);
  }
  .code-copy {
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-soft);
    border-radius: 4px;
    padding: 2px 7px;
    font-family: var(--font-mono);
    font-size: 10px;
    cursor: pointer;
  }
  .code-copy:hover { color: var(--text); border-color: var(--border-strong); }
  .md-body pre code {
    display: block;
    border: none;
    background: transparent;
    padding: 12px 14px;
    overflow-x: auto;
    line-height: 1.5;
  }

  /* Dual Arena Split Grid */
  .arena-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .arena-col {
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--bg-surface);
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-width: 0;
  }

  .arena-keep-btn {
    align-self: flex-start;
    height: 28px;
    padding: 0 12px;
    border-radius: 6px;
    border: 1px solid var(--border-accent);
    background: var(--accent-dim);
    color: var(--text);
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
  }

  /* ── FLOATING COMPOSER DOCK ────────────────────────────── */
  .composer-region {
    padding: 8px 24px 20px;
    flex-shrink: 0;
  }

  .composer-card {
    width: 100%;
    max-width: 820px;
    margin: 0 auto;
    border-radius: 14px;
    border: 1px solid var(--border-strong);
    background: var(--bg-surface);
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    transition: border-color 0.16s ease;
  }

  .composer-card:focus-within {
    border-color: var(--border-accent);
  }

  .composer-card.drag-over {
    border-color: var(--accent);
    background: var(--bg-elevated);
  }

  .radar-strip {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 7px 14px;
    border-bottom: 1px solid var(--border);
    background: rgba(0, 0, 0, 0.22);
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--muted);
  }

  .radar-items {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
  }

  .radar-metric {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .radar-metric b {
    color: var(--text-soft);
    font-weight: 600;
  }

  .radar-bar-track {
    width: 48px;
    height: 4px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.09);
    overflow: hidden;
  }

  #rad-mlp-bar {
    height: 100%;
    width: 24%;
    background: var(--accent);
    transition: width 0.22s ease;
  }

  .attach-row {
    display: none;
    flex-wrap: wrap;
    gap: 6px;
    padding: 8px 14px 0;
  }

  .attach-row.visible {
    display: flex;
  }

  .attach-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 9px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: var(--bg-elevated);
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-soft);
  }

  .attach-chip button {
    border: none;
    background: transparent;
    color: var(--muted);
    cursor: pointer;
    font-size: 13px;
    padding: 0 2px;
  }

  .attach-chip button:hover { color: var(--red); }

  #prompt-input {
    width: 100%;
    min-height: 54px;
    max-height: 190px;
    resize: none;
    border: none;
    outline: none;
    background: transparent;
    color: var(--text);
    padding: 12px 16px 8px;
    font-family: var(--font-sans);
    font-size: 14px;
    line-height: 1.5;
  }

  #prompt-input::placeholder {
    color: var(--muted);
  }

  .composer-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px 10px;
    gap: 10px;
  }

  .footer-left, .footer-right {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .tool-pill {
    height: 30px;
    padding: 0 10px;
    border-radius: 7px;
    border: 1px solid var(--border);
    background: var(--bg-elevated);
    color: var(--text-soft);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    transition: all 0.14s ease;
  }

  .tool-pill:hover {
    border-color: var(--border-strong);
    color: var(--text);
  }

  .tool-pill.arena-active {
    border-color: var(--border-accent);
    background: var(--accent-dim);
    color: var(--text);
  }

  .btn-send {
    height: 32px;
    padding: 0 16px;
    border-radius: 8px;
    border: 1px solid var(--border-accent);
    background: var(--accent);
    color: #06090f;
    font-family: var(--font-sans);
    font-size: 12.5px;
    font-weight: 700;
    cursor: pointer;
    transition: filter 0.15s ease;
  }

  [data-theme="atari"] .btn-send {
    background: #ffffff;
    color: #000000;
  }

  .btn-send:hover { filter: brightness(1.08); }
  .btn-send:disabled { opacity: 0.45; cursor: not-allowed; }

  .btn-stop {
    display: none;
    height: 32px;
    padding: 0 14px;
    border-radius: 8px;
    border: 1px solid rgba(248, 113, 113, 0.4);
    background: rgba(248, 113, 113, 0.14);
    color: var(--red);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
  }

  /* ── COMMAND PALETTE MODAL ─────────────────────────────── */
  .cmd-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.65);
    backdrop-filter: blur(6px);
    display: none;
    align-items: flex-start;
    justify-content: center;
    padding-top: 10vh;
    z-index: 90;
  }

  .cmd-backdrop.open {
    display: flex;
  }

  .cmd-dialog {
    width: min(560px, 92vw);
    border-radius: 14px;
    border: 1px solid var(--border-strong);
    background: var(--bg-surface);
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .cmd-search-wrap {
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
  }

  #cmd-search {
    flex: 1;
    border: none;
    outline: none;
    background: transparent;
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 14px;
  }

  .cmd-list {
    max-height: 360px;
    overflow-y: auto;
    padding: 6px;
  }

  .cmd-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 12px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 13px;
    color: var(--text-soft);
  }

  .cmd-item:hover,
  .cmd-item.selected {
    background: var(--bg-active);
    color: var(--text);
  }

  .cmd-group {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    padding: 1px 6px;
    border: 1px solid var(--border);
    border-radius: 4px;
  }

  /* Toast */
  #toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 120;
    padding: 9px 14px;
    border-radius: 8px;
    border: 1px solid var(--border-strong);
    background: var(--bg-elevated);
    color: var(--text);
    font-size: 12.5px;
    box-shadow: var(--shadow-lg);
    opacity: 0;
    pointer-events: none;
    transform: translateY(8px);
    transition: opacity 0.18s ease, transform 0.18s ease;
  }

  #toast.show {
    opacity: 1;
    transform: translateY(0);
  }

  @media (max-width: 900px) {
    .sidebar {
      position: fixed;
      left: 0;
      top: 0;
      box-shadow: var(--shadow-lg);
    }
    .starter-grid, .arena-grid {
      grid-template-columns: 1fr;
    }
    .cmd-trigger span.hide-sm { display: none; }
  }
</style>
</head>
<body>
<canvas id="quantum-canvas"></canvas>

<div class="studio-shell">
  <!-- LEFT NAVIGATION & TELEMETRY RAIL -->
  <aside class="sidebar" id="sidebar">
    <div class="brand-header">
      <div class="brand-lockup">
        <div class="brand-mark">JS</div>
        <span class="brand-title">Jupiter Studio</span>
      </div>
      <span class="brand-ver">v1.1.0</span>
    </div>

    <div class="rail-actions">
      <button class="btn-new-session" id="btn-new-session" onclick="newSession()">
        <span>+ New Session</span>
        <span class="kbd-hint">Ctrl+K</span>
      </button>

      <div class="rail-tabs" role="tablist">
        <button class="rail-tab active" id="tab-sessions" onclick="switchRailTab('sessions')">Sessions</button>
        <button class="rail-tab" id="tab-workspace" onclick="switchRailTab('workspace')">Workspace</button>
      </div>
    </div>

    <!-- Pane 1: Persistent SQLite Chat History -->
    <div class="rail-pane active" id="pane-sessions">
      <div class="session-scroll" id="session-list">
        <div style="padding:18px 10px; color:var(--muted); font-size:12px;">Loading session history...</div>
      </div>
    </div>

    <!-- Pane 2: Workspace & Copilot Bundle -->
    <div class="rail-pane" id="pane-workspace">
      <div class="ws-toolbar">
        <div class="ws-header-row">
          <span id="ws-file-count">0 files</span>
          <span class="branch-pill" id="ws-branch">main</span>
        </div>
        <input class="ws-input" id="ws-filter-input" type="text" placeholder="Filter repo files..." oninput="renderWorkspaceFileList()" />
        <div class="ws-btn-row">
          <button class="btn-mini" onclick="selectCoreFiles()">Core Files</button>
          <button class="btn-mini" onclick="exportCopilotBundle()">Copilot Bundle</button>
        </div>
      </div>
      <div class="ws-file-scroll" id="workspace-file-list">
        <div style="padding:12px 6px; color:var(--muted); font-size:11.5px;">Indexing workspace...</div>
      </div>
    </div>

    <!-- Compact Workstation & Policy Telemetry Dock -->
    <div class="telemetry-dock">
      <div class="tel-head">
        <span class="tel-title">Workstation Health</span>
        <span class="health-pill" id="hw-health">98 / A+</span>
      </div>
      <div class="hw-gpu-line" id="hw-gpu">Detecting local silicon...</div>
      <div class="hw-vram-line" id="hw-vram">0 / 0 MB</div>
      <div class="vram-track"><div class="vram-fill" id="hw-vram-bar"></div></div>
      <div class="tel-grid">
        <div class="tel-cell">
          <span class="tel-k">Gate</span>
          <span class="tel-v" id="pol-gate">HYDRA</span>
        </div>
        <div class="tel-cell">
          <span class="tel-k">VRAM Saved</span>
          <span class="tel-v" id="pol-vram">0 GB</span>
        </div>
        <div class="tel-cell">
          <span class="tel-k">Cards</span>
          <span class="tel-v" id="pol-cards">0</span>
        </div>
      </div>
    </div>
  </aside>

  <!-- MAIN WORKSPACE STAGE -->
  <main class="stage">
    <header class="topbar">
      <div class="topbar-left">
        <button class="icon-btn" id="btn-toggle-rail" onclick="toggleSidebar()" title="Toggle Navigation Rail">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <line x1="9" y1="3" x2="9" y2="21" />
          </svg>
        </button>

        <div class="target-group">
          <select id="target-selector" onchange="onTargetChange()">
            <option value="auto:d3" selected>⚡ Auto-Route (d3 Smart Router)</option>
            <optgroup label="AMD Token Lab Cloud (Zero VRAM)" id="opt-tokenlab">
              <option value="cloud:Gemma-4-31B-IT">Gemma-4-31B-IT (Vision &amp; Architecture)</option>
              <option value="cloud:Qwen3.8-27B">Qwen3.8-27B (Code &amp; Surgical Diffs)</option>
              <option value="cloud:DeepSeek-V4.1-Flash">DeepSeek-V4.1-Flash (Long Context / Logs)</option>
              <option value="cloud:MiniCPM5-2B">MiniCPM5-2B (Fast Edge Triage)</option>
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
            <optgroup label="AMD Lemonade Server (Ryzen AI NPU / FastFlowLM)" id="opt-lemonade">
              <option value="lemonade:Qwen3-4B-Instruct-2507-FLM">Qwen3-4B-Instruct-FLM (FastFlowLM XDNA 2)</option>
              <option value="lemonade:Qwen2.5-7B-Instruct-Hybrid">Qwen2.5-7B-Instruct-Hybrid (Ryzen AI NPU+iGPU)</option>
              <option value="lemonade:Llama-3.2-3B-Instruct-Hybrid">Llama-3.2-3B-Instruct-Hybrid (Fast NPU)</option>
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

          <button class="cmd-trigger" onclick="openCommandPalette()" title="Command Palette (Ctrl+K)">
            <span class="hide-sm">Palette</span>
            <span class="kbd-hint">Ctrl+K</span>
          </button>
        </div>
      </div>

      <div class="topbar-right">
        <div class="theme-switch" role="group" aria-label="Studio Theme">
          <button class="theme-btn active" id="theme-quantum" onclick="setStudioTheme('quantum')">QUANTUM</button>
          <button class="theme-btn" id="theme-radeon" onclick="setStudioTheme('radeon')">RADEON</button>
          <button class="theme-btn" id="theme-atari" onclick="setStudioTheme('atari')">ATARI B&amp;W</button>
        </div>
        <button class="btn-clear" onclick="clearChat()">New</button>
      </div>
    </header>

    <section class="thread-wrap" id="chat-log">
      <div class="thread-inner" id="thread-inner">
        <div class="empty-state" id="empty-state">
          <div class="empty-badge">MEMORYOS PRECISION WORKSTATION</div>
          <h1 class="empty-title">Jupiter Studio</h1>
          <p class="empty-sub">
            Zero-VRAM cloud-first cascade across AMD Token Lab, NVIDIA Brev, Lemonade Server, and Ollama — backed by persistent SQLite sessions and pre-send speculative routing.
          </p>
          <div class="starter-grid">
            <button class="starter-card" onclick="useStarter('Audit the MemoryOS repository architecture and highlight the highest-leverage improvements.')">
              <div class="starter-k">ARCHITECTURE</div>
              <div class="starter-t">Audit workspace design &amp; modules</div>
            </button>
            <button class="starter-card" onclick="useStarter('Inspect local hardware VRAM headroom and recommend an optimal Hydra routing policy.')">
              <div class="starter-k">TELEMETRY</div>
              <div class="starter-t">Hardware &amp; VRAM routing profile</div>
            </button>
            <button class="starter-card" onclick="useStarter('Compare two frontier models on designing a deterministic agent memory compaction pass.')">
              <div class="starter-k">SPLIT-BRAIN</div>
              <div class="starter-t">Compare reasoning strategies</div>
            </button>
            <button class="starter-card" onclick="selectCoreFiles(); switchRailTab('workspace'); showToast('Core workspace files attached.');">
              <div class="starter-k">CONTEXT</div>
              <div class="starter-t">Attach core repository files</div>
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="composer-region">
      <div class="composer-card" id="composer-card">
        <div class="radar-strip">
          <div class="radar-items">
            <div class="radar-metric">
              <span>MLP</span>
              <div class="radar-bar-track"><div id="rad-mlp-bar"></div></div>
              <b id="rad-mlp">Ready</b>
            </div>
            <div class="radar-metric"><span>ROUTE</span> <b id="rad-route">auto:d3</b></div>
            <div class="radar-metric"><span>DRAFT</span> <b id="rad-tok">0 tok</b></div>
            <div class="radar-metric"><span>VRAM</span> <b id="rad-vram">0.0 GB</b></div>
          </div>
          <span id="stream-status" style="color:var(--muted);">Idle</span>
        </div>

        <div class="attach-row" id="attachment-preview"></div>

        <textarea
          id="prompt-input"
          rows="2"
          placeholder="Ask anything, attach workspace files, or press Ctrl+K to switch silicon targets..."
          oninput="autoGrowPrompt(this); scheduleSpeculativeRadar();"
          onkeydown="handleComposerKey(event)"
        ></textarea>

        <div class="composer-footer">
          <div class="footer-left">
            <input type="file" id="upload-file-input" multiple style="display:none;" onchange="addFilesFromList(this.files); this.value='';" />
            <input type="file" id="upload-image-input" accept="image/*" style="display:none;" onchange="addFilesFromList(this.files); this.value='';" />

            <button class="tool-pill" id="upload-file-btn" onclick="document.getElementById('upload-file-input').click()">+ File</button>
            <button class="tool-pill" id="upload-image-btn" onclick="document.getElementById('upload-image-input').click()">+ Image</button>
            <button class="tool-pill" id="btn-arena" onclick="toggleDualArena()">⚔ Dual Arena</button>
          </div>

          <div class="footer-right">
            <button class="btn-stop" id="btn-stop" onclick="stopGeneration()">Stop</button>
            <button class="btn-send" id="btn-send" onclick="sendPrompt()">Send ↵</button>
          </div>
        </div>
      </div>
    </section>
  </main>
</div>

<!-- COMMAND PALETTE OVERLAY -->
<div class="cmd-backdrop" id="cmd-backdrop" onclick="if (event.target === this) closeCommandPalette();">
  <div class="cmd-dialog">
    <div class="cmd-search-wrap">
      <span style="font-family:var(--font-mono); color:var(--accent); font-size:12px;">&gt;_</span>
      <input id="cmd-search" type="text" placeholder="Jump to model target, theme, or studio action..." oninput="renderCommandPalette()" onkeydown="handlePaletteKey(event)" />
      <span class="kbd-hint">ESC</span>
    </div>
    <div class="cmd-list" id="cmd-list"></div>
  </div>
</div>

<div id="toast"></div>

<script>
const SENSITIVE_BASENAMES = new Set([
  ".env", ".htpasswd", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
  "credentials.json", "secrets.json", "service_account.json", ".npmrc", ".pypirc", ".netrc"
]);
const SENSITIVE_EXTS = [".env", ".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".kdbx"];

let activeSessionId = null;
let chatHistory = [];
let allWorkspaceFiles = [];
let selectedFiles = [];
let uploadedFiles = [];
let currentAttachedImage = null;
let currentAbortController = null;
let dualArenaMode = false;
let radarTimer = null;
let quantumPulse = 0.0;
let currentTheme = "quantum";

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function isSafeImageDataUri(uri) {
  if (!uri || typeof uri !== "string") return false;
  return /^data:image\/(?:png|jpeg|jpg|gif|webp);base64,[A-Za-z0-9+/=]+$/i.test(uri.trim());
}

function isSensitiveFilename(name) {
  const clean = String(name || "").split(/[\\/]/).pop().trim().replace(/[. ]+$/, "").toLowerCase();
  if (!clean) return false;
  if (clean.startsWith(".env")) return true;
  if (SENSITIVE_BASENAMES.has(clean)) return true;
  return SENSITIVE_EXTS.some((ext) => clean.endsWith(ext));
}

function showToast(msg) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = String(msg || "");
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(String(text || ""));
    showToast("Copied to clipboard");
  } catch (_) {
    showToast("Clipboard unavailable");
  }
}

function copyCodeBlock(btn) {
  const pre = btn ? btn.closest("pre") : null;
  const code = pre ? pre.querySelector("code") : null;
  if (code) copyToClipboard(code.innerText || code.textContent || "");
}
window.copyCodeBlock = copyCodeBlock;

function renderMarkdown(md) {
  let src = String(md || "").replace(/\r\n/g, "\n");
  const codeBlocks = [];
  src = src.replace(/```([A-Za-z0-9_+-]*)\n([\s\S]*?)```/g, (_, lang, body) => {
    const idx = codeBlocks.length;
    const safeLang = escapeHtml(lang || "code");
    const safeBody = escapeHtml(body.replace(/\n$/, ""));
    codeBlocks.push(
      `<pre><div class="code-bar"><span>${safeLang}</span><button class="code-copy" onclick="copyCodeBlock(this)">Copy</button></div><code>${safeBody}</code></pre>`
    );
    return `@@CODEBLOCK_${idx}@@`;
  });

  const lines = src.split("\n");
  const out = [];
  let inList = false;

  const formatInline = (text) => {
    let s = escapeHtml(text);
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color:var(--accent);">$1</a>');
    return s;
  };

  for (const line of lines) {
    const trimmed = line.trim();
    const cbMatch = /^@@CODEBLOCK_(\d+)@@$/.exec(trimmed);
    if (cbMatch) {
      if (inList) { out.push("</ul>"); inList = false; }
      out.push(codeBlocks[Number(cbMatch[1])] || "");
      continue;
    }
    if (/^[-*] /.test(trimmed)) {
      if (!inList) { out.push("<ul>"); inList = true; }
      out.push(`<li>${formatInline(trimmed.slice(2))}</li>`);
      continue;
    }
    if (inList) { out.push("</ul>"); inList = false; }
    if (/^### /.test(trimmed)) { out.push(`<h3>${formatInline(trimmed.slice(4))}</h3>`); continue; }
    if (/^## /.test(trimmed)) { out.push(`<h2>${formatInline(trimmed.slice(3))}</h2>`); continue; }
    if (/^# /.test(trimmed)) { out.push(`<h1>${formatInline(trimmed.slice(2))}</h1>`); continue; }
    if (/^> /.test(trimmed)) { out.push(`<blockquote>${formatInline(trimmed.slice(2))}</blockquote>`); continue; }
    if (!trimmed) { continue; }
    out.push(`<p>${formatInline(line)}</p>`);
  }
  if (inList) out.push("</ul>");

  return out.join("").replace(/@@CODEBLOCK_(\d+)@@/g, (_, idx) => codeBlocks[Number(idx)] || "");
}

/* ── THEME & SUBTLE MATRIX CANVAS ───────────────────────── */
function setStudioTheme(themeName) {
  const valid = ["quantum", "radeon", "atari"].includes(themeName) ? themeName : "quantum";
  currentTheme = valid;
  document.documentElement.setAttribute("data-theme", valid);
  localStorage.setItem("jupiter_studio_theme", valid);
  ["quantum", "radeon", "atari"].forEach((t) => {
    const b = document.getElementById("theme-" + t);
    if (b) b.classList.toggle("active", t === valid);
  });
}

function initQuantumCanvas() {
  const canvas = document.getElementById("quantum-canvas");
  if (!canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");
  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  };
  resize();
  window.addEventListener("resize", resize);

  let phase = 0;
  function frame() {
    phase += 0.014;
    quantumPulse = Math.max(0, quantumPulse * 0.94);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const step = 34;
    const baseRgb = currentTheme === "radeon"
      ? "239, 68, 68"
      : currentTheme === "atari"
        ? "255, 255, 255"
        : "56, 189, 248";

    for (let x = 18; x < canvas.width; x += step) {
      for (let y = 18; y < canvas.height; y += step) {
        const wave = Math.sin(x * 0.012 + phase) * Math.cos(y * 0.012 - phase * 0.7);
        const alpha = 0.035 + Math.max(0, wave) * (0.045 + quantumPulse * 0.09);
        ctx.fillStyle = `rgba(${baseRgb}, ${alpha.toFixed(3)})`;
        ctx.fillRect(x, y, 1.5, 1.5);
      }
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

/* ── SIDEBAR & TABS ─────────────────────────────────────── */
function toggleSidebar() {
  const sb = document.getElementById("sidebar");
  if (sb) sb.classList.toggle("collapsed");
}

function switchRailTab(tab) {
  const isSessions = tab !== "workspace";
  document.getElementById("tab-sessions")?.classList.toggle("active", isSessions);
  document.getElementById("tab-workspace")?.classList.toggle("active", !isSessions);
  document.getElementById("pane-sessions")?.classList.toggle("active", isSessions);
  document.getElementById("pane-workspace")?.classList.toggle("active", !isSessions);
}

/* ── PERSISTENT SQLITE SESSIONS ─────────────────────────── */
function formatRelativeIso(iso) {
  if (!iso) return "";
  try {
    const dt = new Date(iso);
    const diffMin = Math.round((Date.now() - dt.getTime()) / 60000);
    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.round(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    return dt.toLocaleDateString();
  } catch (_) {
    return "";
  }
}

async function loadSessions() {
  const listEl = document.getElementById("session-list");
  if (!listEl) return;
  try {
    const res = await fetch("/api/sessions");
    const data = await res.json();
    const sessions = Array.isArray(data.sessions) ? data.sessions : [];
    if (!sessions.length) {
      listEl.innerHTML = `<div style="padding:18px 10px; color:var(--muted); font-size:12px;">No saved sessions yet. Send a prompt to begin a persistent thread.</div>`;
      return;
    }
    listEl.innerHTML = sessions.map((s) => {
      const isAct = s.id === activeSessionId;
      const count = Number(s.message_count || 0);
      return `
        <div class="session-item ${isAct ? "active" : ""}" onclick="openSession('${escapeHtml(s.id)}')">
          <div class="session-main">
            <div class="session-title">${escapeHtml(s.title || "Studio Session")}</div>
            <div class="session-meta">
              <span>${count} msg</span>
              <span>·</span>
              <span>${escapeHtml(formatRelativeIso(s.updated_at || s.created_at))}</span>
            </div>
          </div>
          <button class="session-del" title="Delete session" onclick="event.stopPropagation(); deleteSession('${escapeHtml(s.id)}')">&times;</button>
        </div>
      `;
    }).join("");
  } catch (_) {
    listEl.innerHTML = `<div style="padding:14px 10px; color:var(--muted); font-size:12px;">Session history offline</div>`;
  }
}

function clearThreadDom() {
  const inner = document.getElementById("thread-inner");
  if (!inner) return;
  inner.innerHTML = `
    <div class="empty-state" id="empty-state">
      <div class="empty-badge">MEMORYOS PRECISION WORKSTATION</div>
      <h1 class="empty-title">Jupiter Studio</h1>
      <p class="empty-sub">
        Zero-VRAM cloud-first cascade across AMD Token Lab, NVIDIA Brev, Lemonade Server, and Ollama — backed by persistent SQLite sessions and pre-send speculative routing.
      </p>
      <div class="starter-grid">
        <button class="starter-card" onclick="useStarter('Audit the MemoryOS repository architecture and highlight the highest-leverage improvements.')">
          <div class="starter-k">ARCHITECTURE</div>
          <div class="starter-t">Audit workspace design &amp; modules</div>
        </button>
        <button class="starter-card" onclick="useStarter('Inspect local hardware VRAM headroom and recommend an optimal Hydra routing policy.')">
          <div class="starter-k">TELEMETRY</div>
          <div class="starter-t">Hardware &amp; VRAM routing profile</div>
        </button>
        <button class="starter-card" onclick="useStarter('Compare two frontier models on designing a deterministic agent memory compaction pass.')">
          <div class="starter-k">SPLIT-BRAIN</div>
          <div class="starter-t">Compare reasoning strategies</div>
        </button>
        <button class="starter-card" onclick="selectCoreFiles(); switchRailTab('workspace'); showToast('Core workspace files attached.');">
          <div class="starter-k">CONTEXT</div>
          <div class="starter-t">Attach core repository files</div>
        </button>
      </div>
    </div>
  `;
}

function dismissEmptyState() {
  const empty = document.getElementById("empty-state");
  if (empty) empty.remove();
}

function appendUserMessageEl(text, extraHtml = "") {
  dismissEmptyState();
  const inner = document.getElementById("thread-inner");
  const uMsg = document.createElement("div");
  uMsg.className = "msg user";
  uMsg.innerHTML = `<div>${escapeHtml(text).replace(/\n/g, "<br/>")}</div>${extraHtml}`;
  inner.appendChild(uMsg);
  scrollThreadBottom();
  return uMsg;
}

function appendAssistantMessageEl(metaLabel, metaClass = "meta-cloud") {
  dismissEmptyState();
  const inner = document.getElementById("thread-inner");
  const aMsg = document.createElement("div");
  aMsg.className = "msg assistant";
  aMsg.innerHTML = `
    <div class="msg-head">
      <span class="meta-tag ${metaClass}" data-role="meta">${escapeHtml(metaLabel)}</span>
      <button class="msg-copy-btn" data-role="copy" style="display:none;">Copy</button>
    </div>
    <details class="reasoning-box" data-role="reasoning-box" style="display:none;">
      <summary>Reasoning Trace</summary>
      <div class="reasoning-content" data-role="reasoning-content"></div>
    </details>
    <div class="md-body" data-role="content" style="color:var(--muted);">Thinking...</div>
  `;
  inner.appendChild(aMsg);
  scrollThreadBottom();
  return aMsg;
}

function scrollThreadBottom() {
  const wrap = document.getElementById("chat-log");
  if (wrap) wrap.scrollTop = wrap.scrollHeight;
}

async function openSession(sid) {
  if (!sid) return;
  try {
    const res = await fetch(`/api/sessions/${encodeURIComponent(sid)}`);
    if (!res.ok) throw new Error("Failed to load session");
    const data = await res.json();
    activeSessionId = sid;
    chatHistory = [];
    const inner = document.getElementById("thread-inner");
    inner.innerHTML = "";
    const msgs = Array.isArray(data.messages) ? data.messages : [];
    if (!msgs.length) {
      clearThreadDom();
    } else {
      for (const m of msgs) {
        if (m.role === "user") {
          appendUserMessageEl(m.content || "");
          chatHistory.push({ role: "user", content: m.content || "" });
        } else {
          const aMsg = appendAssistantMessageEl(m.meta_label || "Restored Reply", "meta-cloud");
          const rBox = aMsg.querySelector('[data-role="reasoning-box"]');
          const rBody = aMsg.querySelector('[data-role="reasoning-content"]');
          const cEl = aMsg.querySelector('[data-role="content"]');
          const copyBtn = aMsg.querySelector('[data-role="copy"]');
          if (m.reasoning && rBox && rBody) {
            rBox.style.display = "block";
            rBody.textContent = m.reasoning;
          }
          cEl.style.color = "";
          cEl.innerHTML = renderMarkdown(m.content || "");
          if (copyBtn) {
            copyBtn.style.display = "inline-block";
            copyBtn.onclick = () => copyToClipboard(m.content || "");
          }
          chatHistory.push({ role: "assistant", content: m.content || "" });
        }
      }
    }
    if (data.session && data.session.target) {
      const sel = document.getElementById("target-selector");
      if (sel && Array.from(sel.options).some((o) => o.value === data.session.target)) {
        sel.value = data.session.target;
        onTargetChange();
      }
    }
    loadSessions();
  } catch (err) {
    showToast(err.message || "Could not load session");
  }
}

async function newSession() {
  stopGeneration();
  activeSessionId = null;
  chatHistory = [];
  clearThreadDom();
  loadSessions();
  document.getElementById("prompt-input")?.focus();
}

function clearChat() {
  newSession();
}

async function deleteSession(sid) {
  try {
    await fetch(`/api/sessions/${encodeURIComponent(sid)}`, { method: "DELETE" });
    if (activeSessionId === sid) {
      activeSessionId = null;
      chatHistory = [];
      clearThreadDom();
    }
    loadSessions();
    showToast("Session removed");
  } catch (_) {
    showToast("Delete failed");
  }
}

/* ── MODELS, TELEMETRY & WORKSPACE ──────────────────────── */
function getFileRelPath(entry) {
  if (typeof entry === "string") return entry;
  return entry && typeof entry === "object" ? String(entry.rel_path || "") : "";
}

async function loadModels() {
  try {
    const res = await fetch("/api/models");
    if (!res.ok) return;
    const data = await res.json();
    const p = data.providers || {};

    const optHF = document.getElementById("opt-hf");
    if (optHF && p.hf) {
      optHF.label = `Hugging Face Cloud ${p.hf.ready ? "● Ready" : "○ (Set HF_TOKEN in .env)"}`;
    }
    const optLemonade = document.getElementById("opt-lemonade");
    if (optLemonade && p.lemonade) {
      const lModels = Array.isArray(data.lemonade_installed) ? data.lemonade_installed : [];
      optLemonade.label = p.lemonade.ready
        ? `AMD Lemonade Server (Ryzen AI ● ${lModels.length} Ready)`
        : "AMD Lemonade Server (Ryzen AI ○ Offline)";
      if (lModels.length > 0) {
        const existing = new Set(Array.from(optLemonade.querySelectorAll("option")).map((o) => o.value));
        lModels.forEach((mId) => {
          const val = `lemonade:${mId}`;
          if (!existing.has(val)) {
            const opt = document.createElement("option");
            opt.value = val;
            opt.textContent = `${mId} (Lemonade Live)`;
            optLemonade.appendChild(opt);
          }
        });
      }
    }
    const optSpark = document.getElementById("opt-spark");
    if (optSpark) {
      const sparkReady = Boolean((p.vllm && p.vllm.ready) || (p.flare && p.flare.ready));
      optSpark.label = `DGX Spark / GB10 Local ${sparkReady ? "● Ready" : "○ (Local vLLM/Flare Offline)"}`;
    }
    const optOllama = document.getElementById("opt-ollama");
    if (optOllama && p.ollama) {
      const oModels = Array.isArray(data.ollama_installed) ? data.ollama_installed : [];
      optOllama.label = p.ollama.ready
        ? `Local Models (Ollama ● ${oModels.length} Installed)`
        : "Local Models (Ollama ○ Offline)";
      if (oModels.length > 0) {
        const existing = new Set(Array.from(optOllama.querySelectorAll("option")).map((o) => o.value));
        oModels.forEach((mId) => {
          const val = `ollama:${mId}`;
          if (!existing.has(val)) {
            const opt = document.createElement("option");
            opt.value = val;
            opt.textContent = `${mId} (Ollama Installed)`;
            optOllama.appendChild(opt);
          }
        });
      }
    }
  } catch (_) {}
}

async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();
    const gpuEl = document.getElementById("hw-gpu");
    const hwVramEl = document.getElementById("hw-vram");
    const healthEl = document.getElementById("hw-health");
    const barEl = document.getElementById("hw-vram-bar");
    const gateEl = document.getElementById("pol-gate");
    const vramEl = document.getElementById("pol-vram");
    const cardsEl = document.getElementById("pol-cards");

    const gpu = data.gpu || {};
    const usedMb = Number(gpu.used_vram_mb ?? 0);
    const totalMb = Number(gpu.total_vram_mb ?? 0);
    const utilPct = Number(gpu.utilization_pct ?? 0);
    const suffix = gpu.is_unified_memory ? " Unified" : "";
    if (gpuEl) {
      gpuEl.textContent = gpu.device_name || "CPU Mode";
    }
    if (hwVramEl) {
      hwVramEl.textContent = `${usedMb} / ${totalMb} MB${suffix} (${utilPct}% Load)`;
    }
    if (barEl) {
      const pct = totalMb > 0 ? Math.min(100, Math.round((usedMb / totalMb) * 100)) : 4;
      barEl.style.width = `${pct}%`;
    }
    if (healthEl && data.health) {
      const score = Number(data.health.score ?? 100);
      const grade = data.health.grade || "A";
      healthEl.textContent = `${score} / ${grade}`;
      healthEl.style.color = score >= 80 ? "var(--green)" : (score >= 60 ? "var(--orange)" : "var(--red)");
    }
    if (data.policy) {
      if (gateEl) gateEl.textContent = `${data.policy.cpu_gate_ms ?? 0.091} ms`;
      if (vramEl) vramEl.textContent = `${data.policy.local_vram_saved_pct ?? 100}%`;
      if (cardsEl) cardsEl.textContent = `${data.policy.active_cards ?? 0} Active`;
    }

    const optTL = document.getElementById("opt-tokenlab");
    if (optTL && data.cloud?.amd_tokenlab) {
      optTL.label = `AMD Token Lab Cloud ${data.cloud.amd_tokenlab.configured ? "● Ready" : "○ (Set Key in .env)"}`;
    }
    const optNV = document.getElementById("opt-nvidia");
    if (optNV && data.cloud?.nvidia_brev) {
      optNV.label = `NVIDIA NIM / Brev Cloud ${data.cloud.nvidia_brev.configured ? "● Ready" : "○ (Set Key in .env)"}`;
    }
    const optDO = document.getElementById("opt-digitalocean");
    if (optDO && data.cloud?.digitalocean_mi300x) {
      optDO.label = `DigitalOcean Serverless ${data.cloud.digitalocean_mi300x.configured ? "● Ready" : "○ (Set Key in .env)"}`;
    }
    const optHF = document.getElementById("opt-hf");
    if (optHF && data.cloud?.huggingface) {
      optHF.label = `Hugging Face Cloud ${data.cloud.huggingface.configured ? "● Ready" : "○ (Set HF_TOKEN in .env)"}`;
    }
  } catch (_) {}
}

async function loadWorkspaceFiles() {
  try {
    const res = await fetch("/api/workspace/files");
    if (!res.ok) return;
    const data = await res.json();
    const rawFiles = Array.isArray(data.files) ? data.files : [];
    allWorkspaceFiles = rawFiles.map(getFileRelPath).filter(Boolean);
    const availableSet = new Set(allWorkspaceFiles);
    selectedFiles = selectedFiles.filter((p) => availableSet.has(p));
    const brEl = document.getElementById("ws-branch");
    const cntEl = document.getElementById("ws-file-count");
    if (brEl) brEl.textContent = data.git_branch || "workspace";
    if (cntEl) cntEl.textContent = `${allWorkspaceFiles.length} files`;
    renderWorkspaceFileList();
  } catch (_) {}
}

function renderWorkspaceFileList() {
  const listEl = document.getElementById("workspace-file-list");
  if (!listEl) return;
  const q = (document.getElementById("ws-filter-input")?.value || "").trim().toLowerCase();
  const filtered = allWorkspaceFiles.filter((f) => !q || f.toLowerCase().includes(q)).slice(0, 120);
  if (!filtered.length) {
    listEl.innerHTML = `<div style="padding:10px 6px; color:var(--muted); font-size:11.5px;">No matching files</div>`;
    return;
  }
  listEl.innerHTML = filtered.map((relPath) => {
    const checked = selectedFiles.includes(relPath) ? "checked" : "";
    return `
      <label class="ws-file-row">
        <input type="checkbox" class="ws-file-cb" ${checked} onchange="toggleWorkspaceFile('${escapeHtml(relPath)}', this.checked)" />
        <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(relPath)}</span>
      </label>
    `;
  }).join("");
}

function toggleWorkspaceFile(path, on) {
  if (on && !selectedFiles.includes(path)) selectedFiles.push(path);
  if (!on) selectedFiles = selectedFiles.filter((p) => p !== path);
  renderAttachmentPreview();
}

function selectCoreFiles() {
  const preferred = ["apps/jupiter_studio.py", "apps/jupiter_studio_ui.py", "README.md", "memoryos.py"];
  const picked = allWorkspaceFiles.filter((f) => preferred.some((p) => f.endsWith(p))).slice(0, 5);
  selectedFiles = Array.from(new Set([...selectedFiles, ...picked]));
  renderWorkspaceFileList();
  renderAttachmentPreview();
}

async function exportCopilotBundle() {
  try {
    const res = await fetch("/api/workspace/copilot-bundle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        goal: document.getElementById("prompt-input")?.value || "",
        files: selectedFiles,
        advice: "",
      }),
    });
    const data = await res.json();
    if (data.bundle) {
      await copyToClipboard(data.bundle);
      showToast("Copilot context bundle copied");
    }
  } catch (_) {
    showToast("Export failed");
  }
}

/* ── FILE & IMAGE ATTACHMENTS ───────────────────────────── */
function addFilesFromList(fileList) {
  if (!fileList || !fileList.length) return;
  for (const file of fileList) {
    if (isSensitiveFilename(file.name)) {
      showToast(`Blocked secret file: ${file.name}`);
      continue;
    }
    const reader = new FileReader();
    if ((file.type || "").startsWith("image/")) {
      reader.onload = () => {
        if (isSafeImageDataUri(reader.result)) {
          currentAttachedImage = reader.result;
          renderAttachmentPreview();
        }
      };
      reader.readAsDataURL(file);
    } else {
      reader.onload = () => {
        uploadedFiles.push({ name: file.name, content: String(reader.result || "").slice(0, 120000) });
        renderAttachmentPreview();
      };
      reader.readAsText(file);
    }
  }
}

function clearAllAttachments() {
  uploadedFiles = [];
  selectedFiles = [];
  currentAttachedImage = null;
  renderWorkspaceFileList();
  renderAttachmentPreview();
}

function renderAttachmentPreview() {
  const box = document.getElementById("attachment-preview");
  if (!box) return;
  const chips = [];
  if (currentAttachedImage) {
    chips.push(`<span class="attach-chip">Image attached <button onclick="currentAttachedImage=null; renderAttachmentPreview();">&times;</button></span>`);
  }
  uploadedFiles.forEach((f, idx) => {
    chips.push(`<span class="attach-chip">${escapeHtml(f.name)} <button onclick="uploadedFiles.splice(${idx},1); renderAttachmentPreview();">&times;</button></span>`);
  });
  selectedFiles.forEach((p, idx) => {
    chips.push(`<span class="attach-chip">${escapeHtml(p)} <button onclick="selectedFiles.splice(${idx},1); renderWorkspaceFileList(); renderAttachmentPreview();">&times;</button></span>`);
  });
  box.innerHTML = chips.join("");
  box.classList.toggle("visible", chips.length > 0);
}

/* ── SPECULATIVE RADAR & COMMAND PALETTE ────────────────── */
function onTargetChange() {
  const sel = document.getElementById("target-selector");
  const rt = document.getElementById("rad-route");
  if (sel && rt) rt.textContent = sel.value;
  updateSpeculativeRadar();
}

function scheduleSpeculativeRadar() {
  clearTimeout(radarTimer);
  radarTimer = setTimeout(updateSpeculativeRadar, 180);
}

async function updateSpeculativeRadar() {
  const text = document.getElementById("prompt-input")?.value || "";
  const target = document.getElementById("target-selector")?.value || "auto:d3";
  quantumPulse = Math.min(1.0, quantumPulse + 0.18);
  const extraChars = uploadedFiles.reduce((acc, f) => acc + (f.content ? f.content.length : 0), 0);
  const fileCount = uploadedFiles.length + selectedFiles.length;
  try {
    const res = await fetch("/api/speculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: text,
        target: target,
        has_image: Boolean(currentAttachedImage),
        file_count: fileCount,
        extra_chars: extraChars,
      }),
    });
    if (!res.ok) return;
    const d = await res.json();
    const rawProb = d.p_offload ?? 0.88;
    const pct = (Number(rawProb) * 100).toFixed(1);
    const latNum = Number(d.mlp_latency_us || 0);
    const latStr = latNum >= 1000 ? `${(latNum / 1000).toFixed(2)} ms` : `${latNum.toFixed(1)} μs`;
    const bar = document.getElementById("rad-mlp-bar");
    const mlpEl = document.getElementById("rad-mlp");
    const rtEl = document.getElementById("rad-route");
    const tokEl = document.getElementById("rad-tok");
    const vrEl = document.getElementById("rad-vram");
    if (bar) bar.style.width = `${Math.max(6, Math.min(100, Number(pct)))}%`;
    if (mlpEl) mlpEl.textContent = `${pct}% · ${latStr}`;
    if (rtEl) rtEl.textContent = target === "auto:d3" ? `d3 → ${d.predicted_model}` : target;
    if (tokEl) tokEl.textContent = `~${Number(d.est_tokens || 1).toLocaleString()} tok`;
    if (vrEl) vrEl.textContent = d.is_local ? "Local Exec" : `${d.vram_saved_gb ?? 0} GB saved`;
  } catch (_) {}
}

function openCommandPalette() {
  const back = document.getElementById("cmd-backdrop");
  const inp = document.getElementById("cmd-search");
  if (!back || !inp) return;
  back.classList.add("open");
  inp.value = "";
  renderCommandPalette();
  setTimeout(() => inp.focus(), 20);
}

function closeCommandPalette() {
  document.getElementById("cmd-backdrop")?.classList.remove("open");
}

function getPaletteEntries() {
  const sel = document.getElementById("target-selector");
  const entries = [];
  if (sel) {
    Array.from(sel.options).forEach((opt) => {
      const grp = opt.parentElement && opt.parentElement.tagName === "OPTGROUP" ? opt.parentElement.label : "Auto";
      entries.push({ label: opt.textContent, group: grp, action: () => { sel.value = opt.value; onTargetChange(); } });
    });
  }
  entries.push({ label: "New Persistent Session", group: "Action", action: () => newSession() });
  entries.push({ label: "Toggle Dual Arena Mode", group: "Action", action: () => toggleDualArena() });
  entries.push({ label: "Theme: QUANTUM", group: "Theme", action: () => setStudioTheme("quantum") });
  entries.push({ label: "Theme: RADEON", group: "Theme", action: () => setStudioTheme("radeon") });
  entries.push({ label: "Theme: ATARI B&W", group: "Theme", action: () => setStudioTheme("atari") });
  return entries;
}

function renderCommandPalette() {
  const list = document.getElementById("cmd-list");
  const q = (document.getElementById("cmd-search")?.value || "").trim().toLowerCase();
  if (!list) return;
  const items = getPaletteEntries().filter((e) => !q || e.label.toLowerCase().includes(q) || e.group.toLowerCase().includes(q));
  list.innerHTML = "";
  items.slice(0, 30).forEach((item, idx) => {
    const row = document.createElement("div");
    row.className = "cmd-item" + (idx === 0 ? " selected" : "");
    row.innerHTML = `<span>${escapeHtml(item.label)}</span><span class="cmd-group">${escapeHtml(item.group)}</span>`;
    row.onclick = () => { item.action(); closeCommandPalette(); };
    list.appendChild(row);
  });
}

function handlePaletteKey(ev) {
  if (ev.key === "Escape") { closeCommandPalette(); return; }
  if (ev.key === "Enter") {
    ev.preventDefault();
    const first = document.querySelector("#cmd-list .cmd-item");
    if (first) first.click();
  }
}

document.addEventListener("keydown", (ev) => {
  if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === "k") {
    ev.preventDefault();
    const back = document.getElementById("cmd-backdrop");
    if (back && back.classList.contains("open")) closeCommandPalette();
    else openCommandPalette();
  }
});

/* ── COMPOSER & SSE STREAMING ───────────────────────────── */
function autoGrowPrompt(el) {
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 190) + "px";
}

function handleComposerKey(ev) {
  if (ev.key === "Enter" && !ev.shiftKey) {
    ev.preventDefault();
    sendPrompt();
  }
}

function useStarter(text) {
  const inp = document.getElementById("prompt-input");
  if (!inp) return;
  inp.value = text;
  autoGrowPrompt(inp);
  scheduleSpeculativeRadar();
  inp.focus();
}

function toggleDualArena() {
  dualArenaMode = !dualArenaMode;
  const btn = document.getElementById("btn-arena");
  if (btn) btn.classList.toggle("arena-active", dualArenaMode);
  showToast(dualArenaMode ? "Dual Arena armed" : "Single-stream mode");
}

function setRunningState(running) {
  const sendBtn = document.getElementById("btn-send");
  const stopBtn = document.getElementById("btn-stop");
  const st = document.getElementById("stream-status");
  if (sendBtn) sendBtn.disabled = running;
  if (stopBtn) stopBtn.style.display = running ? "inline-flex" : "none";
  if (st) st.textContent = running ? "Streaming..." : "Idle";
}

function stopGeneration() {
  if (currentAbortController) {
    currentAbortController.abort();
    currentAbortController = null;
  }
  setRunningState(false);
}

function parseSseBlock(block) {
  const lines = String(block || "").split("\n");
  let evType = "message";
  const dataLines = [];
  for (const line of lines) {
    if (line.startsWith("event:")) evType = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (!dataLines.length) return null;
  try {
    return { evType, parsed: JSON.parse(dataLines.join("\n")) };
  } catch (_) {
    return null;
  }
}

function pickArenaChallenger(primary) {
  const sel = document.getElementById("target-selector");
  if (!sel) return primary;
  const opts = Array.from(sel.options).map((o) => o.value).filter((v) => v && v !== primary && v !== "auto:d3");
  return opts[0] || primary;
}

async function sendPromptSingle() {
  const input = document.getElementById("prompt-input");
  const text = (input?.value || "").trim();
  if (!text && !currentAttachedImage && !uploadedFiles.length && !selectedFiles.length) return;

  const target = document.getElementById("target-selector")?.value || "auto:d3";
  const filesToUpload = uploadedFiles.slice();
  const wsToSend = selectedFiles.slice();
  const imgData = currentAttachedImage;

  let extraHtml = "";
  if (isSafeImageDataUri(imgData)) {
    extraHtml += `<br/><img src="${imgData}" alt="Attached" style="max-width:220px; max-height:140px; border-radius:8px; margin-top:8px; border:1px solid var(--border);" />`;
  }
  if (filesToUpload.length) {
    extraHtml += `<div style="font-size:11px; color:var(--amber); margin-top:6px;">Uploaded: ${filesToUpload.map((f) => escapeHtml(f.name)).join(", ")}</div>`;
  }
  if (wsToSend.length) {
    extraHtml += `<div style="font-size:11px; color:var(--accent); margin-top:6px;">Workspace: ${wsToSend.map((p) => escapeHtml(p)).join(", ")}</div>`;
  }

  appendUserMessageEl(text || "(Attached context)", extraHtml);
  if (input) { input.value = ""; input.style.height = "auto"; }
  clearAllAttachments();

  const aMsg = appendAssistantMessageEl(`${target} · connecting...`, "meta-cloud");
  const metaEl = aMsg.querySelector('[data-role="meta"]');
  const rBox = aMsg.querySelector('[data-role="reasoning-box"]');
  const rBody = aMsg.querySelector('[data-role="reasoning-content"]');
  const contentEl = aMsg.querySelector('[data-role="content"]');
  const copyBtn = aMsg.querySelector('[data-role="copy"]');

  setRunningState(true);
  currentAbortController = new AbortController();
  let acc = "";
  let accReasoning = "";
  let modelLabel = target;
  const t0 = performance.now();

  try {
    const res = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: currentAbortController.signal,
      body: JSON.stringify({
        prompt: text,
        target,
        session_id: activeSessionId,
        history: chatHistory.slice(-8),
        image_base64: imgData,
        workspace_files: wsToSend,
        uploaded_files: filesToUpload,
      }),
    });
    if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

    const reader = res.body.getReader();
    const dec = new TextDecoder("utf-8");
    let buf = "";
    let doneFlag = false;

    const handlePart = (part) => {
      if (!part.trim()) return;
      const evt = parseSseBlock(part);
      if (!evt) return;
      const { evType: ev, parsed: p } = evt;
      if (ev === "start") {
        modelLabel = p.model_used || target;
        metaEl.textContent = `${modelLabel} [${p.provider || "LIVE"}]`;
        metaEl.className = `meta-tag ${p.is_local ? "meta-local" : "meta-cloud"}`;
      } else if (ev === "reasoning") {
        accReasoning += p.delta || "";
        if (rBox && rBody) {
          rBox.style.display = "block";
          rBody.textContent = accReasoning;
        }
      } else if (ev === "delta") {
        quantumPulse = 0.85;
        acc += p.delta || "";
        contentEl.style.color = "";
        contentEl.innerHTML = renderMarkdown(acc);
      } else if (ev === "done") {
        const ms = Math.round(p.latency_ms || (performance.now() - t0));
        metaEl.textContent = `${p.model_used || modelLabel} · ${ms} ms`;
        contentEl.style.color = "";
        contentEl.innerHTML = renderMarkdown(acc || "(No response text)");
        if (copyBtn) {
          copyBtn.style.display = "inline-block";
          copyBtn.onclick = () => copyToClipboard(acc);
        }
        chatHistory.push({ role: "user", content: text });
        chatHistory.push({ role: "assistant", content: acc });
        if (p.session_id) {
          activeSessionId = p.session_id;
          loadSessions();
        }
        doneFlag = true;
      } else if (ev === "error") {
        metaEl.className = "meta-tag meta-error";
        metaEl.textContent = "ERROR";
        contentEl.innerHTML = `<span style="color:var(--red); font-family:var(--font-mono);">${escapeHtml(p.error || "Unknown error")}</span>`;
        doneFlag = true;
      }
    };

    while (!doneFlag) {
      const { done, value } = await reader.read();
      if (done) { buf += dec.decode(); break; }
      buf += dec.decode(value, { stream: true }).replace(/\r\n/g, "\n");
      const parts = buf.split("\n\n");
      buf = parts.pop();
      for (const part of parts) {
        handlePart(part);
        if (doneFlag) break;
      }
      scrollThreadBottom();
    }
    if (!doneFlag && buf.trim()) handlePart(buf);
    try { await reader.cancel(); } catch (_) {}
  } catch (e) {
    if (e && e.name === "AbortError") {
      metaEl.textContent += " (Stopped)";
    } else {
      metaEl.className = "meta-tag meta-error";
      metaEl.textContent = "CALL FAILED";
      contentEl.innerHTML = `<span style="color:var(--red); font-family:var(--font-mono);">${escapeHtml(e ? e.message : "Unknown error")}</span>`;
    }
  } finally {
    setRunningState(false);
    currentAbortController = null;
  }
}

async function sendPromptArena() {
  const input = document.getElementById("prompt-input");
  const text = (input?.value || "").trim();
  if (!text && !currentAttachedImage && !uploadedFiles.length && !selectedFiles.length) return;

  const primaryTarget = document.getElementById("target-selector")?.value || "auto:d3";
  const challengerTarget = pickArenaChallenger(primaryTarget);
  const filesToUpload = uploadedFiles.slice();
  const wsToSend = selectedFiles.slice();
  const imgData = currentAttachedImage;

  appendUserMessageEl(`[DUAL ARENA] ${text}`);
  if (input) { input.value = ""; input.style.height = "auto"; }
  clearAllAttachments();

  dismissEmptyState();
  const inner = document.getElementById("thread-inner");
  const aMsg = document.createElement("div");
  aMsg.className = "msg assistant";
  aMsg.innerHTML = `
    <div class="meta-tag meta-auto" style="margin-bottom:6px;">⚔ DUAL ARENA SPLIT STREAM</div>
    <div class="arena-grid">
      <div class="arena-col" data-side="left">
        <span class="meta-tag meta-auto" data-role="meta">${escapeHtml(primaryTarget)} [Streaming...]</span>
        <details class="reasoning-box" data-role="reasoning-box" style="display:none;"><summary>Reasoning Trace</summary><div class="reasoning-content" data-role="reasoning-content"></div></details>
        <div class="md-body" data-role="content" style="color:var(--muted);">Waiting for stream...</div>
        <button class="arena-keep-btn" data-role="keep" style="display:none;">✓ Keep Left Reply</button>
      </div>
      <div class="arena-col" data-side="right">
        <span class="meta-tag meta-cloud" data-role="meta">${escapeHtml(challengerTarget)} [Streaming...]</span>
        <details class="reasoning-box" data-role="reasoning-box" style="display:none;"><summary>Reasoning Trace</summary><div class="reasoning-content" data-role="reasoning-content"></div></details>
        <div class="md-body" data-role="content" style="color:var(--muted);">Waiting for challenger...</div>
        <button class="arena-keep-btn" data-role="keep" style="display:none;">✓ Keep Right Reply</button>
      </div>
    </div>
  `;
  inner.appendChild(aMsg);
  scrollThreadBottom();

  setRunningState(true);
  currentAbortController = new AbortController();

  async function runColumn(colEl, targetModel) {
    const metaEl = colEl.querySelector('[data-role="meta"]');
    const rBox = colEl.querySelector('[data-role="reasoning-box"]');
    const rBody = colEl.querySelector('[data-role="reasoning-content"]');
    const contentEl = colEl.querySelector('[data-role="content"]');
    const keepBtn = colEl.querySelector('[data-role="keep"]');
    let acc = "";
    let accReasoning = "";
    const t0 = performance.now();
    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: currentAbortController.signal,
        body: JSON.stringify({
          prompt: text,
          target: targetModel,
          session_id: activeSessionId,
          history: chatHistory.slice(-6),
          image_base64: imgData,
          workspace_files: wsToSend,
          uploaded_files: filesToUpload,
        }),
      });
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader();
      const dec = new TextDecoder("utf-8");
      let buf = "";
      let doneFlag = false;

      const handlePart = (part) => {
        if (!part.trim()) return;
        const evt = parseSseBlock(part);
        if (!evt) return;
        const { evType: ev, parsed: p } = evt;
        if (ev === "start") {
          metaEl.textContent = `${p.model_used || targetModel} [${p.provider || "LIVE"}]`;
        } else if (ev === "reasoning") {
          accReasoning += p.delta || "";
          if (rBox && rBody) { rBox.style.display = "block"; rBody.textContent = accReasoning; }
        } else if (ev === "delta") {
          quantumPulse = 0.85;
          acc += p.delta || "";
          contentEl.style.color = "";
          contentEl.innerHTML = renderMarkdown(acc);
        } else if (ev === "done") {
          const ms = Math.round(p.latency_ms || (performance.now() - t0));
          const winnerLabel = p.model_used || targetModel;
          metaEl.textContent = `${winnerLabel} (${ms} ms)`;
          contentEl.style.color = "";
          contentEl.innerHTML = renderMarkdown(acc || "(No response text)");
          keepBtn.style.display = "inline-block";
          keepBtn.onclick = () => {
            chatHistory.push({ role: "user", content: text });
            chatHistory.push({ role: "assistant", content: acc });
            aMsg.innerHTML = `<span class="meta-tag meta-local">✓ ARENA WINNER: ${escapeHtml(winnerLabel)} (${ms} ms)</span><div class="md-body">${renderMarkdown(acc)}</div>`;
          };
          doneFlag = true;
        } else if (ev === "error") {
          metaEl.className = "meta-tag meta-error";
          metaEl.textContent = "ERROR";
          contentEl.innerHTML = `<span style="color:var(--red); font-family:var(--font-mono);">${escapeHtml(p.error || "Unknown error")}</span>`;
          doneFlag = true;
        }
      };

      while (!doneFlag) {
        const { done, value } = await reader.read();
        if (done) { buf += dec.decode(); break; }
        buf += dec.decode(value, { stream: true }).replace(/\r\n/g, "\n");
        const parts = buf.split("\n\n");
        buf = parts.pop();
        for (const part of parts) {
          handlePart(part);
          if (doneFlag) break;
        }
        scrollThreadBottom();
      }
      if (!doneFlag && buf.trim()) handlePart(buf);
      try { await reader.cancel(); } catch (_) {}
    } catch (e) {
      if (e && e.name === "AbortError") metaEl.textContent += " (Stopped)";
      else {
        metaEl.className = "meta-tag meta-error";
        metaEl.textContent = "CALL FAILED";
        contentEl.innerHTML = `<span style="color:var(--red); font-family:var(--font-mono);">${escapeHtml(e ? e.message : "Unknown error")}</span>`;
      }
    }
  }

  try {
    await Promise.all([
      runColumn(aMsg.querySelector('[data-side="left"]'), primaryTarget),
      runColumn(aMsg.querySelector('[data-side="right"]'), challengerTarget),
    ]);
  } finally {
    setRunningState(false);
    currentAbortController = null;
    loadSessions();
  }
}

async function sendPrompt() {
  if (dualArenaMode) return sendPromptArena();
  return sendPromptSingle();
}

/* Drag and Drop on Composer */
(function initDragDrop() {
  const card = document.getElementById("composer-card");
  if (!card) return;
  card.addEventListener("dragover", (e) => { e.preventDefault(); card.classList.add("drag-over"); });
  card.addEventListener("dragleave", () => card.classList.remove("drag-over"));
  card.addEventListener("drop", (e) => {
    e.preventDefault();
    card.classList.remove("drag-over");
    if (e.dataTransfer && e.dataTransfer.files) addFilesFromList(e.dataTransfer.files);
  });
})();

window.addEventListener("DOMContentLoaded", () => {
  const savedTheme = localStorage.getItem("jupiter_studio_theme") || "quantum";
  setStudioTheme(savedTheme);
  initQuantumCanvas();
  loadModels();
  loadStatus();
  loadWorkspaceFiles();
  loadSessions();
  updateSpeculativeRadar();
  setInterval(loadStatus, 15000);
});
</script>
</body>
</html>
"""

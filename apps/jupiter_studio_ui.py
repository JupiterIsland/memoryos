"""Single-module Precision Obsidian UI for Jupiter Studio (v2.0.0)."""

STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Jupiter Studio — Personal Intelligence Control Plane</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&family=Syne:wght@600;700;800&display=swap" rel="stylesheet" />
<style>
  :root,
  [data-theme="dark"] {
    --bg: #000000;
    --bg-rail: #040404;
    --bg-surface: #090909;
    --bg-elevated: #121212;
    --bg-hover: rgba(255, 255, 255, 0.06);
    --bg-active: rgba(255, 255, 255, 0.14);
    --border: rgba(255, 255, 255, 0.16);
    --border-strong: rgba(255, 255, 255, 0.40);
    --border-accent: rgba(255, 255, 255, 0.78);
    --text: #ffffff;
    --text-soft: #d4d4d4;
    --muted: #7a7a7a;
    --accent: #ffffff;
    --accent-dim: rgba(255, 255, 255, 0.10);
    --cyan: #ffffff;
    --amber: #d4d4d4;
    --orange: #ffffff;
    --green: #ffffff;
    --red: #ff1744;
    --purple: #ffffff;
    --user-bg: #0e0e0e;
    --code-bg: #050505;
    --shadow-lg: 0 22px 54px rgba(0, 0, 0, 0.92);
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
    --font-display: "Syne", "Space Grotesk", sans-serif;
    --font-sans: "Space Grotesk", -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: "Space Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  }

  [data-theme="light"] {
    --bg: #ffffff;
    --bg-rail: #f6f6f6;
    --bg-surface: #ffffff;
    --bg-elevated: #ebebeb;
    --bg-hover: rgba(0, 0, 0, 0.05);
    --bg-active: rgba(0, 0, 0, 0.11);
    --border: rgba(0, 0, 0, 0.15);
    --border-strong: rgba(0, 0, 0, 0.36);
    --border-accent: rgba(0, 0, 0, 0.80);
    --text: #000000;
    --text-soft: #262626;
    --muted: #666666;
    --accent: #000000;
    --accent-dim: rgba(0, 0, 0, 0.07);
    --cyan: #000000;
    --amber: #262626;
    --orange: #000000;
    --green: #000000;
    --red: #d90429;
    --purple: #000000;
    --user-bg: #f3f3f3;
    --code-bg: #f5f5f5;
    --shadow-lg: 0 18px 42px rgba(0, 0, 0, 0.14);
  }

  /* ═══ PURPLE GLASS — 2030 CSS CRAFT SHOWCASE (EDITION 01) ═══ */
  [data-theme="purple"] {
    --bg: #04010a;
    --bg-rail: rgba(16, 6, 36, 0.56);
    --bg-surface: rgba(28, 12, 58, 0.44);
    --bg-elevated: rgba(52, 22, 106, 0.56);
    --bg-hover: rgba(216, 180, 254, 0.10);
    --bg-active: rgba(192, 132, 252, 0.22);
    --border: rgba(216, 180, 254, 0.20);
    --border-strong: rgba(232, 121, 249, 0.46);
    --border-accent: rgba(192, 132, 252, 0.72);
    --text: #faf5ff;
    --text-soft: #e9d5ff;
    --muted: #a78bfa;
    --accent: #c084fc;
    --accent-dim: rgba(168, 85, 247, 0.20);
    --cyan: #e879f9;
    --amber: #d8b4fe;
    --orange: #c084fc;
    --green: #f3e8ff;
    --red: #ff2a5f;
    --purple: #c084fc;
    --user-bg: rgba(46, 16, 92, 0.54);
    --code-bg: rgba(8, 3, 20, 0.80);
    --shadow-lg: 0 24px 64px rgba(4, 0, 14, 0.78), 0 0 36px rgba(168, 85, 247, 0.14);
  }

  @keyframes purpleAuraShift {
    0%, 100% { background-position: 0% 0%, 100% 100%, 50% 50%; }
    50% { background-position: 18% 12%, 82% 88%, 45% 55%; }
  }

  [data-theme="purple"] body {
    background-color: #04010a;
    background-image:
      radial-gradient(ellipse 65% 55% at 86% 6%, rgba(168, 85, 247, 0.28), transparent 64%),
      radial-gradient(ellipse 58% 52% at 12% 94%, rgba(217, 70, 239, 0.20), transparent 64%),
      radial-gradient(ellipse 46% 40% at 48% 48%, rgba(76, 29, 149, 0.28), transparent 72%);
    background-size: 130% 130%, 130% 130%, 100% 100%;
    animation: purpleAuraShift 18s ease-in-out infinite;
  }

  [data-theme="purple"] .sidebar,
  [data-theme="purple"] .topbar,
  [data-theme="purple"] .cc-card,
  [data-theme="purple"] .composer-card,
  [data-theme="purple"] .telemetry-dock,
  [data-theme="purple"] .starter-card,
  [data-theme="purple"] .mem-fact-card,
  [data-theme="purple"] .cmd-dialog,
  [data-theme="purple"] .theme-switch,
  [data-theme="purple"] .rail-tabs,
  [data-theme="purple"] .btn-new-session,
  [data-theme="purple"] #target-selector {
    backdrop-filter: blur(26px) saturate(185%);
    -webkit-backdrop-filter: blur(26px) saturate(185%);
    box-shadow: inset 0 1px 0 rgba(245, 232, 255, 0.24), 0 18px 46px rgba(4, 0, 14, 0.62);
  }

  [data-theme="purple"] .cc-card,
  [data-theme="purple"] .starter-card,
  [data-theme="purple"] .composer-card {
    background: linear-gradient(155deg, rgba(52, 20, 102, 0.44), rgba(12, 4, 28, 0.64));
    transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  }

  [data-theme="purple"] .cc-card:hover,
  [data-theme="purple"] .starter-card:hover {
    border-color: rgba(232, 121, 249, 0.56);
    transform: translateY(-1px);
    box-shadow: inset 0 1px 0 rgba(250, 245, 255, 0.34), 0 22px 54px rgba(10, 0, 28, 0.72), 0 0 28px rgba(192, 132, 252, 0.20);
  }

  [data-theme="purple"] .brand-title,
  [data-theme="purple"] .empty-title {
    background: linear-gradient(125deg, #ffffff 10%, #e9d5ff 52%, #e879f9 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }

  @keyframes heatFlash {
    0%, 100% {
      color: #ff1744;
      border-color: #ff1744;
      background: rgba(255, 23, 68, 0.16);
      box-shadow: 0 0 12px rgba(255, 23, 68, 0.45);
    }
    50% {
      color: #ffffff;
      border-color: #ff1744;
      background: #ff1744;
      box-shadow: 0 0 20px rgba(255, 23, 68, 0.85);
    }
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
    transition: margin-left 0.28s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.22s ease, transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
    z-index: 20;
  }

  body.sidebar-collapsed .sidebar,
  .sidebar.collapsed {
    margin-left: -292px;
    opacity: 0;
    pointer-events: none;
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

  .brand-title {
    font-family: var(--font-display);
    font-size: 16px;
    font-weight: 800;
    letter-spacing: -0.02em;
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
    grid-template-columns: repeat(3, 1fr);
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
    padding: 2px 9px;
    white-space: nowrap;
  }

  .ws-header-row .branch-pill {
    max-width: 170px;
    overflow: hidden;
    text-overflow: ellipsis;
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
    appearance: none;
    -webkit-appearance: none;
    width: 14px;
    height: 14px;
    min-width: 14px;
    border-radius: 4px;
    border: 1px solid var(--border-strong);
    background: var(--bg-surface);
    display: grid;
    place-items: center;
    cursor: pointer;
    margin: 0;
    transition: border-color 0.14s ease, background 0.14s ease;
  }

  .ws-file-row input:checked {
    background: var(--accent);
    border-color: var(--accent);
  }

  .ws-file-row input:checked::after {
    content: "";
    width: 4px;
    height: 8px;
    border: solid #06090f;
    border-width: 0 2px 2px 0;
    transform: rotate(45deg) translate(-1px, -1px);
  }

  .mem-stat-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    padding: 8px 10px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-family: var(--font-mono);
    font-size: 10.5px;
  }

  .mem-fact-card {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    font-size: 12px;
  }

  .mem-topic-pill {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 9.5px;
    text-transform: uppercase;
    color: var(--accent);
    background: var(--accent-dim);
    border: 1px solid var(--border-accent);
    padding: 1px 6px;
    border-radius: 999px;
    margin-bottom: 4px;
  }

  .btn-free-vram {
    height: 22px;
    padding: 0 7px;
    border-radius: 5px;
    border: 1px solid var(--border-accent);
    background: var(--accent-dim);
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    white-space: nowrap;
    flex-shrink: 0;
    cursor: pointer;
  }

  .btn-free-vram:hover {
    filter: brightness(1.12);
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
    gap: 6px;
    font-size: 11px;
  }

  .tel-title {
    font-weight: 600;
    color: var(--text-soft);
    letter-spacing: 0.02em;
    text-transform: uppercase;
    font-size: 9.5px;
    white-space: nowrap;
    min-width: 0;
  }

  .health-pill {
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid var(--border-strong);
    color: var(--text);
    background: var(--bg-elevated);
    white-space: nowrap;
  }

  .health-pill.heat-warn {
    animation: heatFlash 1.15s ease-in-out infinite;
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
    transition: width 0.28s cubic-bezier(0.22, 1, 0.36, 1);
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
    position: relative;
    z-index: 50;
  }

  [data-theme="dark"] .topbar {
    background: rgba(0, 0, 0, 0.92);
  }

  [data-theme="light"] .topbar {
    background: rgba(255, 255, 255, 0.92);
  }

  [data-theme="purple"] .topbar {
    background: rgba(14, 5, 30, 0.56);
  }

  .cc-wrap {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 20px 24px 36px;
    display: none;
    flex-direction: column;
    gap: 16px;
  }

  .cc-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 14px;
  }

  .cc-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .cc-card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .cc-title {
    font-family: var(--font-display);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--accent);
  }

  .cc-table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--font-mono);
    font-size: 11px;
  }

  .cc-table th, .cc-table td {
    text-align: left;
    padding: 6px 8px;
    border-bottom: 1px solid var(--border);
    color: var(--text-soft);
  }

  .cc-table th {
    color: var(--muted);
    font-weight: 600;
    font-size: 10px;
    text-transform: uppercase;
  }

  .topbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }

  .icon-btn {
    width: auto;
    height: 32px;
    padding: 0 10px;
    border-radius: 7px;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    color: var(--text-soft);
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    white-space: nowrap;
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
    padding: 0 10px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 600;
    white-space: nowrap;
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

  .settings-wrap {
    position: relative;
  }

  .settings-popover {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 276px;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid var(--border-strong);
    background: var(--bg-elevated);
    box-shadow: var(--shadow-lg);
    display: none;
    flex-direction: column;
    gap: 12px;
    z-index: 90;
  }

  .settings-popover.open {
    display: flex;
  }

  [data-theme="purple"] .settings-popover {
    background: rgba(18, 7, 38, 0.88);
    backdrop-filter: blur(26px) saturate(185%);
    -webkit-backdrop-filter: blur(26px) saturate(185%);
    border-color: rgba(192, 132, 252, 0.36);
  }

  .settings-section {
    display: flex;
    flex-direction: column;
    gap: 7px;
  }

  .settings-label {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }

  .settings-tools {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .settings-tool-btn {
    width: 100%;
    text-align: left;
    padding: 7px 10px;
    border-radius: 7px;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    color: var(--text-soft);
    font-family: var(--font-sans);
    font-size: 12px;
    font-weight: 500;
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    transition: all 0.14s ease;
  }

  .settings-tool-btn:hover {
    border-color: var(--border-strong);
    color: var(--text);
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
    font-family: var(--font-display);
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text);
  }

  .empty-sub {
    margin: 0 0 18px;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.55;
  }

  .frank-hero {
    margin: 0 0 18px;
    padding: 15px 16px;
    border-radius: 12px;
    border: 1px solid var(--border-strong);
    background: var(--bg-surface);
    display: flex;
    flex-direction: column;
    gap: 12px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  [data-theme="purple"] .frank-hero {
    background: rgba(18, 7, 38, 0.54);
    backdrop-filter: blur(22px) saturate(175%);
    -webkit-backdrop-filter: blur(22px) saturate(175%);
    border-color: rgba(192, 132, 252, 0.34);
    box-shadow: 0 12px 34px rgba(8, 2, 20, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.14);
  }

  .frank-hero-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
  }

  .frank-hero-kicker {
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text);
  }

  .frank-hero-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    padding-top: 10px;
    padding-bottom: 10px;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }

  .frank-hero-cell {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
  }

  .frank-hero-k {
    font-family: var(--font-mono);
    font-size: 9.5px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
  }

  .frank-hero-v {
    font-family: var(--font-mono);
    font-size: 12.5px;
    font-weight: 700;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .frank-hero-reason {
    font-size: 12px;
    color: var(--text-soft);
    line-height: 1.45;
  }

  @media (max-width: 640px) {
    .frank-hero-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
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
    flex-direction: column;
    gap: 6px;
    padding: 8px 14px;
    border-bottom: 1px solid var(--border);
    background: rgba(0, 0, 0, 0.22);
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--muted);
    transition: background 0.25s ease, border-color 0.25s ease;
  }

  .radar-strip.frank-pulse {
    background: var(--accent-dim);
    border-bottom-color: var(--border-accent);
  }

  .frank-summary-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    min-width: 0;
  }

  .frank-summary-main {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    overflow: hidden;
  }

  .frank-tag {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid var(--border-strong);
    color: var(--text);
    background: var(--bg-surface);
    flex-shrink: 0;
  }

  #frank-summary-text {
    font-family: var(--font-sans);
    font-size: 12px;
    font-weight: 500;
    color: var(--text-soft);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .frank-summary-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .btn-math-toggle {
    height: 20px;
    padding: 0 7px;
    border-radius: 4px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.14s ease;
  }

  .btn-math-toggle:hover,
  .btn-math-toggle.active {
    border-color: var(--border-strong);
    color: var(--text);
    background: var(--bg-surface);
  }

  .radar-items {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
  }

  .radar-items.radar-math-drawer {
    display: none;
    padding-top: 6px;
    border-top: 1px solid var(--border);
  }

  .radar-items.radar-math-drawer.open {
    display: flex;
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

  #frank-telemetry-chip {
    padding: 1px 6px;
    border-radius: 5px;
    border: 1px solid transparent;
    transition: border-color 0.25s ease, background 0.25s ease;
  }

  #frank-telemetry-chip.frank-pulse {
    border-color: var(--border-accent);
    background: var(--accent-dim);
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

  [data-theme="light"] .vram-track,
  [data-theme="light"] .radar-bar-track {
    background: rgba(0, 0, 0, 0.10);
  }

  [data-theme="light"] .radar-strip {
    background: rgba(0, 0, 0, 0.04);
  }

  [data-theme="dark"] .btn-send {
    background: #ffffff;
    color: #000000;
  }

  [data-theme="light"] .btn-send {
    background: #000000;
    color: #ffffff;
  }

  [data-theme="purple"] .btn-send {
    background: linear-gradient(135deg, #c084fc 0%, #9333ea 55%, #e879f9 100%);
    color: #ffffff;
    border-color: rgba(232, 121, 249, 0.75);
    box-shadow: 0 0 22px rgba(192, 132, 252, 0.42);
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
    body.sidebar-collapsed .sidebar,
    .sidebar.collapsed {
      margin-left: 0;
      transform: translateX(-105%);
      opacity: 0;
      pointer-events: none;
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
        <span class="brand-title">Jupiter Studio</span>
      </div>
      <span class="brand-ver">v2.2.0</span>
    </div>

    <div class="rail-actions">
      <button class="btn-new-session" id="btn-new-session" onclick="newSession()">
        <span>+ New Chat</span>
        <span class="kbd-hint">Ctrl+K</span>
      </button>

      <div class="rail-tabs" role="tablist">
        <button class="rail-tab active" id="tab-sessions" onclick="switchRailTab('sessions')">Chats</button>
        <button class="rail-tab" id="tab-workspace" onclick="switchRailTab('workspace')">Files</button>
        <button class="rail-tab" id="tab-memory" onclick="switchRailTab('memory')">Frank</button>
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

    <!-- Pane 3: FrankHub — Memory Vault, EWC Training & Anti-Forgetting Audit -->
    <div class="rail-pane" id="pane-memory">
      <div class="ws-toolbar">
        <div class="ws-header-row" style="margin-bottom:2px;">
          <span style="font-weight:700; color:var(--text); letter-spacing:0.02em;">FrankHub</span>
          <span class="branch-pill" id="frank-hub-badge" title="Frank-v1 Built-In Neural Helper">Frank-v1 · 0 MB VRAM</span>
        </div>
        <div style="font-size:11px; color:var(--muted); line-height:1.35; margin-bottom:2px;">Where Frank learns — Memory Vault, EWC replay &amp; audits.</div>
        <div class="ws-btn-row">
          <button class="btn-mini" id="btn-reclaim-vram" onclick="reclaimVramNow()">Free VRAM &amp; RAM</button>
          <button class="btn-mini" id="btn-train-ewc" onclick="trainContinualModel()">Train Frank</button>
        </div>
        <button class="btn-mini" id="btn-audit-ewc" onclick="runAntiForgettingAudit()" style="width:100%;">Audit Frank (Anti-Forgetting Self-Test)</button>
        <div class="mem-stat-row">
          <div><span style="color:var(--muted);">ENERGY</span> <b id="mem-wh-saved">0.0 Wh</b></div>
          <div><span style="color:var(--muted);">EWC</span> <b id="mem-ewc-status">0 ep</b></div>
        </div>
        <div id="mem-audit-box" style="display:none; padding:7px 9px; border-radius:7px; border:1px solid var(--border-accent); background:var(--accent-dim); font-family:var(--font-mono); font-size:10.5px; color:var(--text);"></div>
        <input class="ws-input" id="mem-topic-input" type="text" placeholder="Memory topic (e.g. hardware, goal)..." />
        <div style="display:flex; gap:6px;">
          <input class="ws-input" id="mem-content-input" type="text" placeholder="Install persistent memory fact..." onkeydown="if(event.key==='Enter') installMemoryFact();" />
          <button class="btn-mini" style="padding:0 10px; white-space:nowrap;" onclick="installMemoryFact()">Pin</button>
        </div>
        <div style="display:flex; gap:6px;">
          <select class="ws-input" id="frank-teach-intent" style="width:108px; padding:0 6px;">
            <option value="fast_code">fast_code</option>
            <option value="architecture">architecture</option>
            <option value="large_design">large_design</option>
            <option value="cheap_bg">cheap_bg</option>
            <option value="vram_reclaim">vram_reclaim</option>
            <option value="memory_pin">memory_pin</option>
          </select>
          <input class="ws-input" id="frank-teach-input" type="text" placeholder="Teach Frank phrasing..." onkeydown="if(event.key==='Enter') teachFrank();" />
          <button class="btn-mini" style="padding:0 8px; white-space:nowrap;" onclick="teachFrank()">Teach</button>
        </div>
      </div>
      <div class="session-scroll" id="memory-fact-list">
        <div style="padding:12px 6px; color:var(--muted); font-size:11.5px;">No persistent memories pinned yet.</div>
      </div>
    </div>

    <!-- Compact Workstation & Policy Telemetry Dock -->
    <div class="telemetry-dock">
      <div class="tel-head">
        <span class="tel-title">System Health</span>
        <div style="display:flex; align-items:center; gap:6px; flex-shrink:0;">
          <button class="btn-free-vram" onclick="reclaimVramNow()" title="Unload idle local models & free RAM/VRAM">Free VRAM</button>
          <span class="health-pill" id="hw-health">98 / A+</span>
        </div>
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
        <button class="icon-btn" id="btn-toggle-sidebar" onclick="toggleSidebar()" title="Collapse or expand sidebar" aria-expanded="true">Sidebar</button>

        <div class="target-group">
          <select id="target-selector" onchange="onTargetChange()">
            <option value="auto:d3" selected>Frank: Auto (Routes by Intent &amp; Hardware)</option>
            <optgroup label="Jupiter Studio Built-In Helper (0 MB VRAM)" id="opt-studio">
              <option value="studio:frank">Frank-v1 (Built-In EWC Helper Neural Net · Always Offline-Ready)</option>
            </optgroup>
            <optgroup label="AMD Token Lab Cloud (Zero VRAM)" id="opt-tokenlab">
              <option value="cloud:Gemma-4-31B-IT">Gemma-4-31B-IT (Large Design Docs &amp; Vision)</option>
              <option value="cloud:Qwen3.8-27B">Qwen3.8-27B (Code &amp; Surgical Diffs)</option>
              <option value="cloud:DeepSeek-V4.1-Flash">DeepSeek-V4.1-Flash (Architecture Reviews &amp; Logs)</option>
              <option value="cloud:MiniCPM5-2B">MiniCPM5-2B (Cheap Background Tasks)</option>
              <option value="cloud:MiniCPM-V-4.7-35B-A3B">MiniCPM-V-4.7-35B-A3B (Multimodal MoE · Token Lab)</option>
              <option value="cloud:MiniCPM-V-4.7-1B">MiniCPM-V-4.7-1B (Edge Vision 1B · Token Lab)</option>
            </optgroup>
            <optgroup label="OpenAI Cloud (OPENAI_API_KEY)" id="opt-openai">
              <option value="openai:gpt-4o-mini">gpt-4o-mini (OpenAI Fast &amp; Low Cost)</option>
              <option value="openai:gpt-4o">gpt-4o (OpenAI Flagship &amp; Vision)</option>
            </optgroup>
            <optgroup label="Google Gemini API (GEMINI_API_KEY)" id="opt-gemini">
              <option value="gemini:gemini-4-argon">Gemini 4 Argon (Flagship Reasoning · 1M Context)</option>
              <option value="gemini:gemini-3.8-flash">Gemini 3.8 Flash (Fast Coding &amp; Agents)</option>
              <option value="gemini:gemini-3.6-flash">Gemini 3.6 Flash (Balanced Multimodal)</option>
              <option value="gemini:gemini-3.5-flash-lite">Gemini 3.5 Flash-Lite (High-Throughput &amp; Low Cost)</option>
              <option value="gemini:gemma-4-31b-it">Gemma 4 31B IT (Open Model · Gemini API)</option>
            </optgroup>
            <optgroup label="Groq Cloud (Fast Coding LPU)" id="opt-groq">
              <option value="groq:llama-3.3-70b-versatile">Llama-3.3-70B-Versatile (Groq Fast Coding)</option>
              <option value="groq:qwen/qwen3-32b">Qwen3-32B (Groq Reasoning)</option>
              <option value="groq:llama-3.1-8b-instant">Llama-3.1-8B-Instant (Groq Background)</option>
            </optgroup>
            <optgroup label="OpenRouter Cloud (Multi-Model Gateway)" id="opt-openrouter">
              <option value="openrouter:deepseek/deepseek-chat">DeepSeek-V4/Chat (OpenRouter Architecture)</option>
              <option value="openrouter:google/gemma-3-27b-it">Gemma-3-27B-IT (OpenRouter Design Docs)</option>
              <option value="openrouter:qwen/qwen-2.5-coder-32b-instruct">Qwen-2.5-Coder-32B (OpenRouter Code)</option>
            </optgroup>
            <optgroup label="Cerebras Cloud (Wafer-Scale Fast Inference)" id="opt-cerebras">
              <option value="cerebras:llama-3.3-70b">Llama-3.3-70B (Cerebras Cloud)</option>
              <option value="cerebras:qwen-3-32b">Qwen-3-32B (Cerebras Cloud)</option>
              <option value="cerebras:llama3.1-8b">Llama-3.1-8B (Cerebras Background)</option>
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
              <option value="hf:Qwen/Qwen3.8-27B">Qwen3.8-27B Multimodal (HF Router)</option>
              <option value="hf:Qwen/Qwen2.5-72B-Instruct">Qwen2.5-72B-Instruct (HF Router)</option>
              <option value="hf:meta-llama/Llama-3.3-70B-Instruct">Llama-3.3-70B-Instruct (HF Router)</option>
              <option value="hf:deepseek-ai/DeepSeek-R1">DeepSeek-R1 (HF Router)</option>
              <option value="hf:Qwen/Qwen2.5-Coder-32B-Instruct">Qwen2.5-Coder-32B-Instruct (HF Router)</option>
            </optgroup>
            <optgroup label="AMD Lemonade Server (Local GGUF / NPU)" id="opt-lemonade">
              <option value="lemonade:Qwen3-4B-Instruct-2507-GGUF">Qwen3-4B-Instruct-2507-GGUF (Lemonade Local · 2.5 GB)</option>
              <option value="lemonade:Gemma-4-E2B-it-GGUF">Gemma-4-E2B-it-GGUF (Lemonade Vision · 4.1 GB)</option>
              <option value="lemonade:Llama-3.2-3B-Instruct-GGUF">Llama-3.2-3B-Instruct-GGUF (Lemonade Fast · 2.1 GB)</option>
            </optgroup>
            <optgroup label="DGX Spark / GB10 &amp; 32GB+ Unified Local" id="opt-spark">
              <option value="ollama:inkling-2-mini">inkling-2-mini (Thinking Machines 26B Looped MoE · 1M Ctx)</option>
              <option value="vllm:Qwen/Qwen3.8-Flash-Next">Qwen3.8-Flash-Next (Local vLLM :8000)</option>
              <option value="vllm:deepseek-ai/DeepSeek-V4.1-Flash">DeepSeek-V4.1-Flash (Local vLLM :8000)</option>
              <option value="flare:Qwen3.8-Flash-Next">Qwen3.8-Flash-Next (NVIDIA Flare :8080)</option>
              <option value="flare:DeepSeek-V4.1-Flash">DeepSeek-V4.1-Flash (NVIDIA Flare :8080)</option>
            </optgroup>
            <optgroup label="Local Models (100% Free / Ollama)" id="opt-ollama">
              <option value="ollama:qwen2.5-coder:7b">qwen2.5-coder:7b (Local Accuracy)</option>
              <option value="ollama:qwen2.5-coder:1.5b">qwen2.5-coder:1.5b (Ultra-Fast)</option>
              <option value="ollama:deepseek-r1:7b">deepseek-r1:7b (Reasoning)</option>
              <option value="ollama:deepseek-r1:8b">deepseek-r1:8b (Deep Thinking)</option>
              <option value="ollama:gemma4:26b">gemma4:26b (Gemma 4 Multimodal Local)</option>
              <option value="ollama:frank:latest">frank:latest (Modelfile.frank · Local Ollama)</option>
              <option value="ollama:bonsai-2:27b">bonsai-2:27b (PrismML Ternary 27B · Low VRAM)</option>
              <option value="ollama:gemma4:12b">gemma4:12b (Gemma 4 12B · Ollama)</option>
              <option value="ollama:raon-1-nano">raon-1-nano (Game-Loop 1.5B / 256K)</option>
              <option value="ollama:hf.co/unsloth/gemma-4-E2B-it-GGUF">hf.co/unsloth/gemma-4-E2B-it-GGUF (HF Local Vision · $0)</option>
              <option value="ollama:hf.co/unsloth/Qwen3.5-4B-GGUF">hf.co/unsloth/Qwen3.5-4B-GGUF (HF Local 4B · $0)</option>
              <option value="ollama:hf.co/prism-ml/Bonsai-4B-gguf">hf.co/prism-ml/Bonsai-4B-gguf (HF Ternary 4B · $0)</option>
            </optgroup>
          </select>
        </div>
      </div>

      <div class="topbar-right">
        <div class="theme-switch" role="group" aria-label="Console Stage">
          <button class="theme-btn active" id="stage-btn-ops" onclick="switchStageView('ops')">Operations</button>
          <button class="theme-btn" id="stage-btn-video" onclick="switchStageView('video')">Cloud Video</button>
          <button class="theme-btn" id="stage-btn-hf" onclick="switchStageView('hf')">HF Models</button>
          <button class="theme-btn" id="stage-btn-cc" onclick="switchStageView('control')">Control Centre</button>
        </div>
        <div class="settings-wrap">
          <button class="btn-clear" id="btn-settings-menu" onclick="toggleSettingsMenu()" aria-expanded="false" aria-controls="settings-popover">Settings</button>
          <div class="settings-popover" id="settings-popover" role="menu">
            <div class="settings-section">
              <span class="settings-label">Appearance</span>
              <div class="theme-switch" role="group" aria-label="Studio Theme" style="width:100%; justify-content:space-between;">
                <button class="theme-btn" id="theme-light" onclick="setStudioTheme('light')" style="flex:1;">LIGHT</button>
                <button class="theme-btn active" id="theme-dark" onclick="setStudioTheme('dark')" style="flex:1;">DARK</button>
                <button class="theme-btn" id="theme-purple" onclick="setStudioTheme('purple')" style="flex:1;">PURPLE GLASS</button>
              </div>
            </div>
            <div class="settings-section">
              <span class="settings-label">Tools</span>
              <div class="settings-tools">
                <button class="settings-tool-btn" onclick="toggleSettingsMenu(false); openCommandPalette();">
                  <span>Command Palette</span>
                  <span class="kbd-hint">Ctrl+K</span>
                </button>
                <button class="settings-tool-btn" id="btn-run-guide" onclick="toggleSettingsMenu(false); toggleModelRunHelper();">
                  <span>Model Run Guide</span>
                  <span class="kbd-hint">? Run</span>
                </button>
                <button class="settings-tool-btn" onclick="toggleSettingsMenu(false); openFrankHub();">
                  <span>FrankHub &amp; EWC Audit</span>
                  <span class="kbd-hint">Frank</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        <button class="btn-clear" onclick="clearChat()">New</button>
      </div>
    </header>

    <div id="model-run-helper" style="display:none; padding:9px 16px; border-bottom:1px solid var(--border); background:var(--bg-surface); font-size:12px; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap;">
      <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; min-width:0;">
        <span id="mrh-badge" style="font-family:var(--font-mono); font-size:10.5px; font-weight:700; padding:2px 7px; border-radius:999px; border:1px solid var(--border-accent); color:var(--accent); background:var(--accent-dim);">RUN GUIDE</span>
        <span id="mrh-text" style="color:var(--text-soft);"></span>
        <code id="mrh-cmd" style="display:none; font-family:var(--font-mono); font-size:11px; padding:2px 8px; border-radius:6px; background:var(--bg-elevated); border:1px solid var(--border); color:var(--text); user-select:all;"></code>
      </div>
      <div style="display:flex; align-items:center; gap:6px;">
        <button class="btn-mini" id="mrh-copy" style="display:none; padding:3px 9px;" onclick="copyModelRunCmd()">Copy Command</button>
        <button class="btn-mini" style="padding:3px 8px;" onclick="document.getElementById('model-run-helper').style.display='none'; manualRunHelperOpen=false;">Hide</button>
      </div>
    </div>

    <div id="recovery-banner" style="display:none; padding:9px 16px; border-bottom:1px solid var(--border-accent); background:var(--accent-dim); font-size:12px; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap;">
      <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; min-width:0;">
        <span style="font-family:var(--font-mono); font-size:10.5px; font-weight:700; padding:2px 8px; border-radius:999px; border:1px solid var(--border-accent); color:var(--accent); background:var(--bg-surface);">CRASH RECOVERY</span>
        <div id="recovery-list" style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; color:var(--text);"></div>
      </div>
      <button class="btn-mini" style="padding:3px 8px;" onclick="document.getElementById('recovery-banner').style.display='none';">Hide</button>
    </div>

    <section class="cc-wrap" id="control-centre-stage">
      <div class="cc-card">
        <div class="cc-card-head">
          <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
            <span class="cc-title">Personal Intelligence Control Centre</span>
            <span class="branch-pill" id="cc-health-badge">Probing...</span>
            <span class="branch-pill" id="cc-ledger-badge">Ledger Unverified</span>
          </div>
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button class="btn-mini" onclick="verifyControlLedger()">Verify Hash Chain</button>
            <button class="btn-mini" onclick="loadControlCentre()">Refresh</button>
          </div>
        </div>
      </div>

      <div class="cc-grid">
        <div class="cc-card">
          <div class="cc-card-head">
            <span class="cc-title">Resource Fabric</span>
          </div>
          <div id="cc-providers-grid" style="display:flex; flex-wrap:wrap; gap:6px;"></div>
        </div>

        <div class="cc-card">
          <div class="cc-card-head">
            <span class="cc-title">Circuit Breakers</span>
            <button class="btn-mini" onclick="resetCircuitBreakers()">Reset All</button>
          </div>
          <table class="cc-table">
            <thead>
              <tr><th>Resource</th><th>State</th><th>Failures</th><th>Action</th></tr>
            </thead>
            <tbody id="cc-breakers-body"></tbody>
          </table>
        </div>
      </div>

      <div class="cc-card">
        <div class="cc-card-head">
          <span class="cc-title">Declarative Plugin Packs (Zero Arbitrary Exec)</span>
        </div>
        <div id="cc-plugins-grid" class="cc-grid"></div>
        <div id="cc-plugin-approval" style="display:none; padding:9px 12px; border-radius:8px; border:1px solid var(--border-accent); background:var(--accent-dim); align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap;">
          <span id="cc-plugin-approval-text" style="font-size:12px; color:var(--text);"></span>
          <div style="display:flex; gap:6px;">
            <button class="btn-mini" onclick="confirmPendingPluginOp()">Approve &amp; Execute</button>
            <button class="btn-mini" onclick="cancelPendingPluginOp()">Cancel</button>
          </div>
        </div>
        <pre id="cc-plugin-output" style="display:none; margin:0; padding:10px 12px; border-radius:8px; background:var(--code-bg); border:1px solid var(--border); font-family:var(--font-mono); font-size:11px; color:var(--text-soft); overflow:auto; max-height:220px;"></pre>
      </div>

      <div class="cc-card">
        <div class="cc-card-head">
          <span class="cc-title">Operations Run Ledger (ops_run_log)</span>
        </div>
        <div style="overflow-x:auto;">
          <table class="cc-table">
            <thead>
              <tr><th>Op ID</th><th>Objective</th><th>Intent</th><th>Resource</th><th>Guard</th><th>Status</th><th>Latency</th></tr>
            </thead>
            <tbody id="cc-ledger-body"></tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="cc-wrap" id="cloud-video-stage">
      <div class="cc-card">
        <div class="cc-card-head">
          <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
            <span class="cc-title">Cloud Video Offload Studio</span>
            <span class="branch-pill" id="vid-vram-pill">0 MB Local VRAM</span>
            <span class="branch-pill" id="vid-analyzer-pill">Analyzer: Checking...</span>
            <span class="branch-pill" id="vid-generator-pill">Generator: Checking...</span>
            <span class="branch-pill" id="vid-storage-pill">Output: Checking...</span>
          </div>
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button class="btn-mini" onclick="loadCloudVideoStage()">Refresh</button>
          </div>
        </div>
      </div>

      <div class="cc-grid">
        <div class="cc-card">
          <div class="cc-card-head">
            <span class="cc-title">1. Cloud Video Analyzer &amp; Scene Indexer</span>
            <span class="branch-pill">CPU Gate -&gt; Token Lab</span>
          </div>
          <div style="font-size:12px; color:var(--text-soft);">
            Samples keyframes in your browser on CPU, drops static/duplicate frames via MemoryOS delta gating, and offloads only scene transitions to AMD Token Lab (0 MB RTX VRAM).
          </div>
          <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
            <input type="file" id="vid-file-input" accept="video/*" style="display:none;" onchange="onVideoFileChosen(this.files && this.files[0])" />
            <button class="btn-mini" onclick="document.getElementById('vid-file-input').click()">Choose Video (.mp4 / .mov / .webm)</button>
            <select class="ws-input" id="vid-analyze-model" style="width:auto; min-width:210px; padding:0 8px;">
              <option value="cloud:MiniCPM-V-4.7-35B-A3B">MiniCPM-V-4.7-35B-A3B (Token Lab · $0 Grant)</option>
              <option value="cloud:MiniCPM-V-4.7-1B">MiniCPM-V-4.7-1B (Fast Vision · Token Lab)</option>
              <option value="cloud:Gemma-4-31B-IT">Gemma-4-31B-IT (Deep Vision · Token Lab)</option>
              <option value="ollama:hf.co/unsloth/gemma-4-E2B-it-GGUF">Gemma 4 E2B GGUF (HF Local Vision · $0.00)</option>
              <option value="ollama:gemma4:26b">gemma4:26b (Local Ollama Vision · $0.00)</option>
              <option value="hf:Qwen/Qwen3.8-27B">Qwen 3.8 27B Vision (HF Router)</option>
              <option value="gemini:gemini-3.8-flash">Gemini 3.8 Flash (Google Gemini API)</option>
            </select>
            <select class="ws-input" id="vid-sample-interval" style="width:auto; padding:0 8px;" title="Sample interval in seconds">
              <option value="2">Every 2s</option>
              <option value="4" selected>Every 4s</option>
              <option value="8">Every 8s</option>
            </select>
            <select class="ws-input" id="vid-max-frames" style="width:auto; padding:0 8px;" title="Max keyframes sent to cloud">
              <option value="4">Max 4 cloud</option>
              <option value="8" selected>Max 8 cloud</option>
              <option value="12">Max 12 cloud</option>
            </select>
          </div>
          <video id="vid-preview-player" controls style="display:none; width:100%; max-height:240px; border-radius:8px; border:1px solid var(--border); background:#000;"></video>
          <canvas id="vid-sample-canvas" style="display:none;"></canvas>
          <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
            <input class="ws-input" id="vid-prompt-hint" type="text" placeholder="Focus hint (e.g. Archive Signal VHS cuts, guitars, studio gear)..." style="flex:1; min-width:200px;" />
            <label style="display:inline-flex; align-items:center; gap:5px; font-size:11.5px; color:var(--text-soft); cursor:pointer;">
              <input type="checkbox" id="vid-save-vault" checked /> Save to Vault
            </label>
            <button class="btn-send" id="btn-vid-analyze" onclick="runCloudVideoAnalyze()" style="height:30px;">Analyze Video in Cloud</button>
          </div>
          <div id="vid-analyze-status" style="font-family:var(--font-mono); font-size:11px; color:var(--muted);">Pick a local video clip to sample and index in the cloud.</div>
          <div id="vid-analyze-metrics" style="display:none; padding:8px 10px; border-radius:8px; border:1px solid var(--border); background:var(--code-bg); font-family:var(--font-mono); font-size:11px; color:var(--text-soft);"></div>
          <div id="vid-scene-results" style="display:flex; flex-direction:column; gap:6px; max-height:260px; overflow-y:auto;"></div>
        </div>

        <div class="cc-card">
          <div class="cc-card-head">
            <span class="cc-title">2. Multi-Provider Cloud Video Generator</span>
            <span class="branch-pill" id="vid-gen-dest-pill">0 MB VRAM -&gt; ./outputs/video</span>
          </div>
          <div id="vid-gen-setup-note" style="display:none; padding:8px 10px; border-radius:8px; border:1px solid var(--border-accent); background:var(--accent-dim); font-size:11.5px; color:var(--text);"></div>
          <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
            <select class="ws-input" id="vid-gen-target" style="flex:1; min-width:230px; padding:0 8px;" onchange="onVideoGenTargetChange()">
              <option value="gemini:gemini-omni-1.2-flash" selected>Gemini Omni 1.2 Flash (Google Cloud)</option>
              <option value="fal:fal-ai/wan-25-preview/text-to-video">Wan 2.5 Preview (fal.ai Draft · ~$0.05/s)</option>
              <option value="fal:fal-ai/pika/v2.2/text-to-video">Pika 2.2 (fal.ai Fast Draft · ~$0.04/s)</option>
              <option value="fal:fal-ai/kling-video/v2.1/standard/text-to-video">Kling 2.1 Standard (fal.ai · ~$0.11/s)</option>
              <option value="replicate:wan-video/wan-2.5-t2v">Wan 2.5 T2V (Replicate · ~$0.05/s)</option>
              <option value="replicate:runwayml/gen4-turbo">Runway Gen-4 Turbo (Replicate · ~$0.12/s)</option>
              <option value="replicate:luma/ray-2">Luma Ray 2 (Replicate · ~$0.24/s)</option>
              <option value="hf:Wan-AI/Wan2.2-TI2V-5B">Wan 2.2 TI2V 5B (Hugging Face Open-Weight · ~$0.05/s)</option>
              <option value="hf:Wan-AI/Wan2.2-T2V-A14B">Wan 2.2 T2V A14B MoE (Hugging Face Open-Weight · ~$0.08/s)</option>
            </select>
            <button class="btn-mini" onclick="applyVideoPreset('draft')" title="Low-cost quick preview preset">Draft 360p · 5s</button>
            <button class="btn-mini" onclick="applyVideoPreset('hero')" title="Full HD flagship render preset">Hero 1080p · 10s</button>
          </div>
          <textarea class="ws-input" id="vid-gen-prompt" rows="3" style="height:74px; padding:8px 10px; font-family:var(--font-sans); resize:vertical;" placeholder="Describe a video scene to generate in the cloud (e.g. Analog CRT studio rack glowing in deep monochrome shadow, slow push-in)..."></textarea>
          <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
            <select class="ws-input" id="vid-gen-aspect" style="width:auto; padding:0 8px;">
              <option value="16:9" selected>16:9 Landscape</option>
              <option value="9:16">9:16 Portrait</option>
            </select>
            <select class="ws-input" id="vid-gen-res" style="width:auto; padding:0 8px;" onchange="updateVideoCostEstimate()">
              <option value="360p">360p Fast</option>
              <option value="720p" selected>720p HD</option>
              <option value="1080p">1080p Full HD</option>
              <option value="4k">4K Ultra HD</option>
            </select>
            <select class="ws-input" id="vid-gen-duration" style="width:auto; padding:0 8px;" onchange="updateVideoCostEstimate()">
              <option value="3">3s</option>
              <option value="5" selected>5s</option>
              <option value="8">8s</option>
              <option value="10">10s</option>
              <option value="15">15s</option>
            </select>
            <label style="display:inline-flex; align-items:center; gap:5px; font-family:var(--font-mono); font-size:11px; color:var(--muted);">
              Cap $:
              <input class="ws-input" id="vid-gen-max-usd" type="number" min="0" step="0.25" value="0.00" style="width:76px; padding:0 6px;" oninput="updateVideoCostEstimate()" />
            </label>
            <input class="ws-input" id="vid-gen-prev-id" type="text" placeholder="Optional previous_interaction_id (Omni edit/extend)..." style="flex:1; min-width:150px;" />
          </div>
          <div id="vid-gen-cost-bar" style="padding:7px 10px; border-radius:8px; border:1px solid var(--border); background:var(--code-bg); font-family:var(--font-mono); font-size:11px; color:var(--text-soft);">
            Pre-Flight Estimate: $0.50 USD (5s x $0.10/s) · Cap $0.00 (HARD ZERO-SPEND LOCK)
          </div>
          <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; font-size:11px; color:var(--muted);">
            <label style="display:inline-flex; align-items:center; gap:4px;">First frame: <input type="file" id="vid-gen-first-frame" accept="image/*" style="max-width:155px; font-size:10.5px;" /></label>
            <label style="display:inline-flex; align-items:center; gap:4px;">Last frame: <input type="file" id="vid-gen-last-frame" accept="image/*" style="max-width:155px; font-size:10.5px;" /></label>
            <button class="btn-send" id="btn-vid-generate" onclick="runCloudVideoGenerate()" style="height:30px; margin-left:auto;">Generate in Cloud</button>
          </div>
          <div style="font-size:11px; color:var(--muted);">Text-to-video &amp; image-to-video run in cloud (0 MB VRAM); uploading source videos for Omni edits is regionally restricted in UK/EEA/Switzerland.</div>
          <div id="vid-gen-status" style="font-family:var(--font-mono); font-size:11px; color:var(--muted);">Ready. Outputs stream directly to external drive.</div>
        </div>
      </div>

      <div class="cc-grid">
        <div class="cc-card">
          <div class="cc-card-head">
            <span class="cc-title">Indexed Scene MemoryVault Search</span>
            <div style="display:flex; gap:6px;">
              <input class="ws-input" id="vid-scene-search" type="text" placeholder="Search scenes (e.g. guitar, dusk)..." style="width:200px;" onkeydown="if(event.key==='Enter') searchIndexedScenes();" />
              <button class="btn-mini" onclick="searchIndexedScenes()">Search Vault</button>
            </div>
          </div>
          <div id="vid-vault-scenes" style="display:flex; flex-direction:column; gap:6px; max-height:240px; overflow-y:auto;"></div>
        </div>

        <div class="cc-card">
          <div class="cc-card-head">
            <span class="cc-title">Cloud Video Output Gallery</span>
            <button class="btn-mini" onclick="loadCloudVideoStage()">Reload Clips</button>
          </div>
          <div id="vid-outputs-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:10px;"></div>
        </div>
      </div>

      <div class="cc-card">
        <div class="cc-card-head">
          <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
            <span class="cc-title">Auditable Video Spend &amp; Savings Ledger</span>
            <span class="branch-pill" id="vid-ledger-spend-pill">Est. Spend: $0.00</span>
            <span class="branch-pill" id="vid-ledger-gated-pill">Frames Gated: 0</span>
            <span class="branch-pill" id="vid-ledger-chain-pill">SHA-256 Valid</span>
          </div>
          <button class="btn-mini" onclick="loadVideoSpendLedger()">Refresh Ledger</button>
        </div>
        <div style="overflow-x:auto;">
          <table class="cc-table">
            <thead>
              <tr><th>Type</th><th>Provider / Model</th><th>Scope</th><th>Est. Cost</th><th>Local VRAM</th><th>Ledger Event</th></tr>
            </thead>
            <tbody id="vid-ledger-body"></tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="cc-wrap" id="hf-hub-stage">
      <div class="cc-card">
        <div class="cc-card-head">
          <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
            <span class="cc-title">Hugging Face Open-Weight Model Hub</span>
            <span class="branch-pill" id="hf-billing-pill">HF Billing: Checking...</span>
            <span class="branch-pill" id="hf-lock-pill">Spend Lock: Cap $0.00</span>
            <span class="branch-pill" id="hf-cache-pill">On Disk: 0 models ($0.00)</span>
            <span class="branch-pill" id="hf-ollama-pill">Ollama: Checking...</span>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="btn-mini" onclick="loadHfHubStage()">Refresh Hub</button>
            <button class="btn-mini" onclick="switchStageView('ops')">Back to Chat</button>
          </div>
        </div>
        <div id="hf-safety-banner" style="padding:8px 10px; border-radius:8px; border:1px solid var(--border-accent); background:var(--code-bg); font-family:var(--font-mono); font-size:11px; color:var(--text-soft);">
          Public Hugging Face Hub Explorer ($0.00) · Calibrated for AMD Ryzen 7 5800H (16 GB RAM) + NVIDIA RTX 3070 (8 GB VRAM). Pull GGUF weights straight into Local Ollama at $0.00 or inspect open-weight video/vision models under your hard zero-spend lock.
        </div>
        <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:4px;">
          <input class="ws-input" id="hf-search-input" type="text" placeholder="Search huggingface.co/models (e.g. qwen3, gemma-4, wan2.2, ltx-video, kokoro, gguf)..." style="flex:1; min-width:240px;" onkeydown="if(event.key==='Enter'){event.preventDefault(); searchHfHubModels();}" />
          <select class="ws-input" id="hf-sort-select" style="width:auto; padding:0 8px;" onchange="searchHfHubModels()">
            <option value="trendingScore" selected>Trending Now</option>
            <option value="downloads">Most Downloads</option>
            <option value="likes">Most Likes</option>
          </select>
          <label style="display:inline-flex; align-items:center; gap:5px; font-size:11.5px; color:var(--text-soft); cursor:pointer;">
            <input type="checkbox" id="hf-warm-only" onchange="searchHfHubModels()" /> Live Serverless Only
          </label>
          <button class="btn-send" onclick="searchHfHubModels()" style="height:30px;">Search Hub</button>
        </div>
        <div id="hf-task-pills" style="display:flex; gap:6px; flex-wrap:wrap; margin-top:2px;">
          <button class="btn-mini active" data-hftask="8gb-gguf" onclick="selectHfTask('8gb-gguf')">8GB Local GGUF ($0.00)</button>
          <button class="btn-mini" data-hftask="text-to-video" onclick="selectHfTask('text-to-video')">Text-to-Video</button>
          <button class="btn-mini" data-hftask="image-text-to-text" onclick="selectHfTask('image-text-to-text')">Vision / Video VLM</button>
          <button class="btn-mini" data-hftask="text-generation" onclick="selectHfTask('text-generation')">Coding &amp; Reasoning</button>
          <button class="btn-mini" data-hftask="text-to-speech" onclick="selectHfTask('text-to-speech')">Voice &amp; TTS</button>
        </div>
        <div id="hf-action-status" style="font-family:var(--font-mono); font-size:11px; color:var(--muted);"></div>
        <div id="hf-models-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(290px, 1fr)); gap:10px;"></div>
      </div>

      <div class="cc-card">
        <div class="cc-card-head">
          <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
            <span class="cc-title">Already Downloaded in Local Hugging Face Cache ($0.00)</span>
            <span class="branch-pill" id="hf-disk-total-pill">0.0 MB on Disk</span>
          </div>
        </div>
        <div style="overflow-x:auto;">
          <table class="cc-table">
            <thead>
              <tr><th>Repository</th><th>Format</th><th>Size</th><th>8GB RTX 3070 Fit</th><th>Cache Location</th><th>Action ($0.00)</th></tr>
            </thead>
            <tbody id="hf-local-cache-body"></tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="thread-wrap" id="chat-log">
      <div class="thread-inner" id="thread-inner">
        <div class="empty-state" id="empty-state">
          <div class="empty-badge">ROUTER FIRST · PERSONAL AI CONTROL PLANE</div>
          <h1 class="empty-title">Jupiter Studio</h1>
          <p class="empty-sub">
            Frank analyzes your request, picks the best compute engine, and keeps your local VRAM free.
          </p>

          <div class="frank-hero" id="frank-hero-card">
            <div class="frank-hero-head">
              <span class="frank-hero-kicker">FRANK DECISION · LIVE ROUTING</span>
              <span class="branch-pill" id="fh-badge">0 MB VRAM · EWC</span>
            </div>
            <div class="frank-hero-grid">
              <div class="frank-hero-cell">
                <span class="frank-hero-k">Selected Engine</span>
                <span class="frank-hero-v" id="fh-model">Frank: Auto</span>
              </div>
              <div class="frank-hero-cell">
                <span class="frank-hero-k">Intent</span>
                <span class="frank-hero-v" id="fh-intent">Ready</span>
              </div>
              <div class="frank-hero-cell">
                <span class="frank-hero-k">VRAM Saved</span>
                <span class="frank-hero-v" id="fh-vram">Local GPU Free</span>
              </div>
              <div class="frank-hero-cell">
                <span class="frank-hero-k">Decision Time</span>
                <span class="frank-hero-v" id="fh-lat">&lt; 1 ms</span>
              </div>
            </div>
            <div class="frank-hero-reason" id="fh-reason">
              Type an objective below — Frank classifies intent on CPU in under a millisecond and routes automatically.
            </div>
          </div>

          <div class="starter-grid">
            <button class="starter-card" onclick="useStarter('Audit the MemoryOS repository architecture and highlight the highest-leverage improvements.')">
              <div class="starter-k">ARCHITECTURE OPS</div>
              <div class="starter-t">Audit system design &amp; bottlenecks</div>
            </button>
            <button class="starter-card" onclick="useStarter('Inspect local hardware VRAM headroom and recommend an optimal silicon allocation policy.')">
              <div class="starter-k">SILICON TELEMETRY</div>
              <div class="starter-t">Check VRAM &amp; compute pool health</div>
            </button>
            <button class="starter-card" onclick="openFrankHub(); runAntiForgettingAudit();">
              <div class="starter-k">FRANKHUB AUDIT</div>
              <div class="starter-t">Run live EWC anti-forgetting check</div>
            </button>
            <button class="starter-card" onclick="selectCoreFiles(); switchRailTab('workspace'); showToast('Core workspace files attached.');">
              <div class="starter-k">WORKSPACE CONTEXT</div>
              <div class="starter-t">Attach core repository files</div>
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="composer-region" id="composer-region">
      <div class="composer-card" id="composer-card">
        <div class="radar-strip" id="frank-radar-strip">
          <div class="frank-summary-row">
            <div class="frank-summary-main">
              <span class="frank-tag">FRANK</span>
              <span id="frank-summary-text">Ready — routes by intent &amp; keeps local VRAM free</span>
            </div>
            <div class="frank-summary-actions">
              <button class="btn-math-toggle" id="btn-toggle-math" onclick="toggleMathDrawer()" aria-expanded="false" title="Show or hide raw MLP, token, and Frank Softmax telemetry">Math</button>
              <span id="stream-status" style="color:var(--muted);">Idle</span>
            </div>
          </div>
          <div class="radar-math-drawer radar-items" id="radar-math-drawer">
            <div class="radar-metric">
              <span>MLP</span>
              <div class="radar-bar-track"><div id="rad-mlp-bar"></div></div>
              <b id="rad-mlp">Ready</b>
            </div>
            <div class="radar-metric"><span>ROUTE</span> <b id="rad-route">auto:d3</b></div>
            <div class="radar-metric"><span>DRAFT</span> <b id="rad-tok">0 tok</b></div>
            <div class="radar-metric" id="frank-telemetry-chip" title="Frank-v1 onboard neural intent classifier (0 MB VRAM)">
              <span>FRANK</span> <b id="rad-frank">-- (--%)</b>
            </div>
            <div class="radar-metric"><span>VRAM</span> <b id="rad-vram">0.0 GB</b></div>
          </div>
        </div>

        <div class="attach-row" id="attachment-preview"></div>

        <textarea
          id="prompt-input"
          rows="2"
          placeholder="State an objective... (Jupiter Studio selects the optimal compute resource automatically; Ctrl+K to inspect/override)"
          oninput="autoGrowPrompt(this); scheduleSpeculativeRadar();"
          onkeydown="handleComposerKey(event)"
        ></textarea>

        <div class="composer-footer">
          <div class="footer-left">
            <input type="file" id="upload-file-input" multiple style="display:none;" onchange="addFilesFromList(this.files); this.value='';" />
            <input type="file" id="upload-image-input" accept="image/*" style="display:none;" onchange="addFilesFromList(this.files); this.value='';" />

            <button class="tool-pill" id="upload-file-btn" onclick="document.getElementById('upload-file-input').click()">+ File</button>
            <button class="tool-pill" id="upload-image-btn" onclick="document.getElementById('upload-image-input').click()">+ Image</button>
            <button class="tool-pill" id="btn-arena" onclick="toggleDualArena()">Dual Arena</button>
          </div>

          <div class="footer-right">
            <button class="btn-stop" id="btn-stop" onclick="stopGeneration()">Stop</button>
            <button class="btn-send" id="btn-send" onclick="sendPrompt()">Send</button>
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
let currentTheme = "dark";
let activeStageView = "ops";
let pendingPluginOp = null;

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

/* ── THEME (LIGHT / DARK / PURPLE GLASS) & MATRIX CANVAS ─ */
function setStudioTheme(themeName) {
  let mode = String(themeName || "dark").toLowerCase();
  if (mode === "surprise" || mode === "purple-glass") mode = "purple";
  if (mode === "quantum" || mode === "radeon" || mode === "atari") mode = "dark";
  if (!["light", "dark", "purple"].includes(mode)) mode = "dark";

  currentTheme = mode;
  document.documentElement.setAttribute("data-theme", mode);
  localStorage.setItem("jupiter_studio_theme", mode);

  ["light", "dark", "purple"].forEach((t) => {
    const b = document.getElementById("theme-" + t);
    if (b) b.classList.toggle("active", t === mode);
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
    const baseRgb = currentTheme === "light"
      ? "0, 0, 0"
      : currentTheme === "purple"
        ? "192, 132, 252"
        : "255, 255, 255";

    for (let x = 18; x < canvas.width; x += step) {
      for (let y = 18; y < canvas.height; y += step) {
        const wave = Math.sin(x * 0.012 + phase) * Math.cos(y * 0.012 - phase * 0.7);
        const alpha = (currentTheme === "light" ? 0.045 : 0.032) + Math.max(0, wave) * (0.045 + quantumPulse * 0.09);
        ctx.fillStyle = `rgba(${baseRgb}, ${alpha.toFixed(3)})`;
        ctx.fillRect(x, y, 1.5, 1.5);
      }
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

/* ── STAGE SWITCH, CRASH RECOVERY & CONTROL CENTRE ──────── */
let currentVideoFileObj = null;
let currentVideoBlobUrl = null;

let activeHfTask = "8gb-gguf";

function switchStageView(view) {
  activeStageView = view === "control" ? "control" : (view === "video" ? "video" : (view === "hf" ? "hf" : "ops"));
  const isOps = activeStageView === "ops";
  const isVideo = activeStageView === "video";
  const isHf = activeStageView === "hf";
  const isCC = activeStageView === "control";
  const chatEl = document.getElementById("chat-log");
  const compEl = document.getElementById("composer-region");
  const vidEl = document.getElementById("cloud-video-stage");
  const hfEl = document.getElementById("hf-hub-stage");
  const ccEl = document.getElementById("control-centre-stage");
  if (chatEl) chatEl.style.display = isOps ? "flex" : "none";
  if (compEl) compEl.style.display = isOps ? "block" : "none";
  if (vidEl) vidEl.style.display = isVideo ? "flex" : "none";
  if (hfEl) hfEl.style.display = isHf ? "flex" : "none";
  if (ccEl) ccEl.style.display = isCC ? "flex" : "none";
  document.getElementById("stage-btn-ops")?.classList.toggle("active", isOps);
  document.getElementById("stage-btn-video")?.classList.toggle("active", isVideo);
  document.getElementById("stage-btn-hf")?.classList.toggle("active", isHf);
  document.getElementById("stage-btn-cc")?.classList.toggle("active", isCC);
  if (isCC) loadControlCentre();
  if (isVideo) loadCloudVideoStage();
  if (isHf) loadHfHubStage();
}

function selectHfTask(task) {
  activeHfTask = task || "8gb-gguf";
  document.querySelectorAll("#hf-task-pills button[data-hftask]").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-hftask") === activeHfTask);
  });
  searchHfHubModels();
}

function routeHfModelToChat(targetVal, labelText) {
  const sel = document.getElementById("target-selector");
  if (!sel || !targetVal) return;
  let existing = Array.from(sel.options).find((o) => o.value === targetVal);
  if (!existing) {
    const grpId = targetVal.startsWith("ollama:") ? "opt-ollama" : "opt-hf";
    const grp = document.getElementById(grpId) || sel;
    const opt = document.createElement("option");
    opt.value = targetVal;
    opt.textContent = labelText || targetVal;
    grp.appendChild(opt);
  }
  sel.value = targetVal;
  onTargetChange();
  switchStageView("ops");
}

function routeHfModelToVideo(targetVal, labelText, isAnalyzer) {
  if (isAnalyzer) {
    const anSel = document.getElementById("vid-analyze-model");
    if (anSel && targetVal) {
      if (!Array.from(anSel.options).some((o) => o.value === targetVal)) {
        const opt = document.createElement("option");
        opt.value = targetVal;
        opt.textContent = labelText || targetVal;
        anSel.appendChild(opt);
      }
      anSel.value = targetVal;
    }
    switchStageView("video");
    return;
  }
  switchStageView("video");
  setTimeout(() => {
    const genSel = document.getElementById("vid-gen-target");
    if (genSel && targetVal) {
      if (!Array.from(genSel.options).some((o) => o.value === targetVal)) {
        const opt = document.createElement("option");
        opt.value = targetVal;
        opt.textContent = labelText || targetVal;
        genSel.appendChild(opt);
      }
      genSel.value = targetVal;
      onVideoGenTargetChange();
    }
  }, 180);
}

async function pullAndSelectHfGguf(btnEl) {
  const repoId = btnEl?.getAttribute("data-repo") || "";
  const statusEl = document.getElementById("hf-action-status");
  if (!repoId) return;
  const origTxt = btnEl.textContent;
  btnEl.disabled = true;
  btnEl.textContent = "Pulling $0 GGUF...";
  if (statusEl) {
    statusEl.style.color = "var(--text-soft)";
    statusEl.textContent = `Pulling hf.co/${repoId} into Local Ollama (127.0.0.1:11434 · $0.00)...`;
  }
  try {
    const res = await fetch("/api/hf/ollama-pull", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_id: repoId }),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) {
      if (statusEl) {
        statusEl.style.color = "var(--warning, #d97706)";
        statusEl.textContent = d.error || `Could not pull ${repoId}. Run in terminal: ollama run hf.co/${repoId}`;
      }
      return;
    }
    if (statusEl) {
      statusEl.style.color = "var(--success, #16a34a)";
      statusEl.textContent = `Pulled ${d.ollama_model} ($0.00) -> routed into Chat selector!`;
    }
    routeHfModelToChat(d.studio_target, `${d.ollama_model} (HF Local GGUF · $0)`);
  } catch (err) {
    if (statusEl) {
      statusEl.style.color = "var(--warning, #d97706)";
      statusEl.textContent = `Ollama pull error: ${err.message || err}`;
    }
  } finally {
    btnEl.disabled = false;
    btnEl.textContent = origTxt;
  }
}

function renderHfModelsGrid(models) {
  const grid = document.getElementById("hf-models-grid");
  if (!grid) return;
  if (!Array.isArray(models) || !models.length) {
    grid.innerHTML = `<div style="font-size:12px; color:var(--muted);">No Hugging Face models matched this filter.</div>`;
    return;
  }
  grid.innerHTML = models.map((m) => {
    const fit = m.hardware_fit || {};
    const fitColor = fit.tier === "fits_8gb_local" ? "var(--success, #16a34a)" : (fit.tier === "hybrid_cpu_gpu" ? "var(--warning, #d97706)" : "var(--text-soft)");
    const provList = Array.isArray(m.live_providers) && m.live_providers.length
      ? `Providers: ${m.live_providers.join(", ")}`
      : "Weights on HF Hub";
    const diskBadge = m.cached_locally
      ? `<span class="branch-pill" style="border-color:var(--success, #16a34a); color:var(--success, #16a34a);">ON DISK · $0</span>`
      : "";

    let actionsHtml = "";
    if (m.is_gguf && m.ollama_target) {
      const chatLbl = `${m.id} (HF Local GGUF · $0)`;
      actionsHtml += `<button class="btn-mini" data-target="${escapeHtml(m.ollama_target)}" data-label="${escapeHtml(chatLbl)}" onclick="routeHfModelToChat(this.dataset.target, this.dataset.label)">Select in Chat ($0)</button>`;
      actionsHtml += `<button class="btn-mini" data-repo="${escapeHtml(m.id)}" onclick="pullAndSelectHfGguf(this)">Ollama Pull ($0)</button>`;
      if (m.is_vision) {
        actionsHtml += `<button class="btn-mini" data-target="${escapeHtml(m.ollama_target)}" data-label="${escapeHtml(chatLbl)}" onclick="routeHfModelToVideo(this.dataset.target, this.dataset.label, true)">Video VLM ($0)</button>`;
      }
    } else if (m.is_video && m.video_target) {
      const vidLbl = `${m.id} (HF Open-Weight Video)`;
      actionsHtml += `<button class="btn-mini" data-target="${escapeHtml(m.video_target)}" data-label="${escapeHtml(vidLbl)}" onclick="routeHfModelToVideo(this.dataset.target, this.dataset.label, false)">Open in Video Stage</button>`;
    } else {
      const hfLbl = `${m.id} (HF Router)`;
      actionsHtml += `<button class="btn-mini" data-target="${escapeHtml(m.hf_router_target)}" data-label="${escapeHtml(hfLbl)}" onclick="routeHfModelToChat(this.dataset.target, this.dataset.label)">Route via HF</button>`;
      if (m.is_vision) {
        actionsHtml += `<button class="btn-mini" data-target="${escapeHtml(m.hf_router_target)}" data-label="${escapeHtml(hfLbl)}" onclick="routeHfModelToVideo(this.dataset.target, this.dataset.label, true)">Use as Video VLM</button>`;
      }
    }
    if (m.url && String(m.url).startsWith("https://huggingface.co/")) {
      actionsHtml += `<a class="btn-mini" href="${escapeHtml(m.url)}" target="_blank" rel="noopener noreferrer" style="text-decoration:none; display:inline-flex; align-items:center;">HF Card</a>`;
    }

    return `
      <div style="padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg-surface); display:flex; flex-direction:column; gap:6px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:6px;">
          <div style="font-family:var(--font-mono); font-size:11.5px; font-weight:600; color:var(--text); word-break:break-all;">${escapeHtml(m.id)}</div>
          ${diskBadge}
        </div>
        <div style="font-family:var(--font-mono); font-size:10.5px; color:${fitColor};">${escapeHtml(fit.label || "")}</div>
        <div style="font-family:var(--font-mono); font-size:10px; color:var(--muted);">
          ${escapeHtml(m.pipeline_tag || "model")} · DL ${Number(m.downloads || 0).toLocaleString()} · Likes ${Number(m.likes || 0).toLocaleString()}
        </div>
        <div style="font-family:var(--font-mono); font-size:10px; color:var(--text-soft);">${escapeHtml(provList)}</div>
        <div style="display:flex; gap:5px; flex-wrap:wrap; margin-top:auto; padding-top:4px;">${actionsHtml}</div>
      </div>
    `;
  }).join("");
}

async function searchHfHubModels() {
  const q = (document.getElementById("hf-search-input")?.value || "").trim();
  const sort = document.getElementById("hf-sort-select")?.value || "trendingScore";
  const warm = document.getElementById("hf-warm-only")?.checked ? "1" : "0";
  const grid = document.getElementById("hf-models-grid");
  if (grid) grid.innerHTML = `<div style="font-family:var(--font-mono); font-size:11px; color:var(--muted);">Querying huggingface.co/models ($0.00 public Hub API)...</div>`;
  try {
    const params = new URLSearchParams({ q, task: activeHfTask, sort, warm_only: warm, limit: "12" });
    const res = await fetch(`/api/hf/models?${params.toString()}`);
    if (res.ok) {
      const d = await res.json();
      renderHfModelsGrid(d.models || []);
    }
  } catch (err) {
    if (grid) grid.innerHTML = `<div style="font-size:11.5px; color:var(--muted);">Hub search error: ${escapeHtml(String(err))}</div>`;
  }
}

async function loadHfHubStage() {
  searchHfHubModels();
  try {
    const res = await fetch("/api/hf/status");
    if (!res.ok) return;
    const d = await res.json();
    const s = d.safety || {};
    const billPill = document.getElementById("hf-billing-pill");
    const lockPill = document.getElementById("hf-lock-pill");
    const cachePill = document.getElementById("hf-cache-pill");
    const olPill = document.getElementById("hf-ollama-pill");
    const banner = document.getElementById("hf-safety-banner");
    const diskPill = document.getElementById("hf-disk-total-pill");
    const tbody = document.getElementById("hf-local-cache-body");

    if (billPill) {
      billPill.textContent = !s.can_pay ? "HF Card: NONE ($0.00 SAFE)" : "HF Card: ATTACHED";
    }
    if (lockPill) {
      lockPill.textContent = s.zero_spend_locked ? "Spend Lock: HARD $0.00" : "Spend Lock: Custom";
    }
    const cacheCount = Number(d.local_cache?.count || 0);
    const cacheMb = Number(d.local_cache?.total_size_mb || 0);
    if (cachePill) cachePill.textContent = `On Disk: ${cacheCount} repos ($0.00)`;
    if (diskPill) diskPill.textContent = `${cacheMb.toFixed(1)} MB on Disk`;
    if (olPill) olPill.textContent = d.ollama?.live ? `Local Ollama: LIVE (${(d.ollama.models || []).length})` : "Local Ollama: OFFLINE";
    if (banner && s.billing_summary) {
      banner.textContent = `${s.billing_summary} · RTX 3070 (8 GB VRAM) Hardware-Fit Active.`;
    }
    if (tbody) {
      const localList = Array.isArray(d.local_cache?.models) ? d.local_cache.models : [];
      if (!localList.length) {
        tbody.innerHTML = `<tr><td colspan="6" style="color:var(--muted);">No local Hugging Face repositories found in cache.</td></tr>`;
      } else {
        tbody.innerHTML = localList.map((item) => {
          const fmt = item.is_gguf ? "GGUF ($0 Ollama)" : (item.has_safetensors ? "Safetensors" : "Hub Snapshot");
          const actBtn = item.ollama_target
            ? `<button class="btn-mini" data-target="${escapeHtml(item.ollama_target)}" data-label="${escapeHtml(item.id + ' (Local Disk · $0)')}" onclick="routeHfModelToChat(this.dataset.target, this.dataset.label)">Use in Chat ($0)</button>`
            : `<span style="font-family:var(--font-mono); font-size:10.5px; color:var(--muted);">Local Cache</span>`;
          return `
            <tr>
              <td style="font-family:var(--font-mono); font-size:11px;">${escapeHtml(item.id)}</td>
              <td>${escapeHtml(fmt)}</td>
              <td style="font-family:var(--font-mono);">${Number(item.size_mb || 0).toFixed(1)} MB</td>
              <td style="font-family:var(--font-mono); font-size:10.5px;">${escapeHtml(item.hardware_fit?.label || "")}</td>
              <td style="font-family:var(--font-mono); font-size:10px; color:var(--muted);">${escapeHtml(item.cache_dir || "")}</td>
              <td>${actBtn}</td>
            </tr>
          `;
        }).join("");
      }
    }
  } catch (_) {}
}

function readImageInputAsDataUri(fileInputEl) {
  return new Promise((resolve, reject) => {
    const f = fileInputEl && fileInputEl.files && fileInputEl.files[0];
    if (!f) { resolve(null); return; }
    const reader = new FileReader();
    reader.onload = () => resolve(typeof reader.result === "string" ? reader.result : null);
    reader.onerror = () => reject(new Error("Could not read image frame"));
    reader.readAsDataURL(f);
  });
}

function onVideoFileChosen(file) {
  if (!file) return;
  currentVideoFileObj = file;
  if (currentVideoBlobUrl) {
    try { URL.revokeObjectURL(currentVideoBlobUrl); } catch (_) {}
  }
  currentVideoBlobUrl = URL.createObjectURL(file);
  const player = document.getElementById("vid-preview-player");
  const st = document.getElementById("vid-analyze-status");
  if (player) {
    player.src = currentVideoBlobUrl;
    player.style.display = "block";
  }
  if (st) st.textContent = `Loaded '${file.name}' (${(file.size / (1024 * 1024)).toFixed(2)} MB). Ready to CPU-gate & analyze in cloud.`;
}

function seekVideoPreview(sec) {
  const player = document.getElementById("vid-preview-player");
  if (player && player.src) {
    try {
      player.currentTime = Math.max(0, Number(sec) || 0);
      player.play().catch(() => {});
    } catch (_) {}
  }
}

async function extractFramesFromVideoFile(file, intervalSec = 4, maxSampled = 24) {
  const player = document.getElementById("vid-preview-player");
  const canvas = document.getElementById("vid-sample-canvas");
  if (!player || !canvas || !canvas.getContext) throw new Error("Canvas video sampler unavailable");
  if (!currentVideoBlobUrl) {
    currentVideoBlobUrl = URL.createObjectURL(file);
    player.src = currentVideoBlobUrl;
    player.style.display = "block";
  }

  await new Promise((resolve, reject) => {
    if (player.readyState >= 1 && Number.isFinite(player.duration) && player.duration > 0) {
      resolve();
      return;
    }
    const onMeta = () => { player.removeEventListener("error", onErr); resolve(); };
    const onErr = () => { player.removeEventListener("loadedmetadata", onMeta); reject(new Error("Browser could not decode video metadata")); };
    player.addEventListener("loadedmetadata", onMeta, { once: true });
    player.addEventListener("error", onErr, { once: true });
  });

  const duration = Number.isFinite(player.duration) && player.duration > 0 ? player.duration : 10;
  const step = Math.max(1, Number(intervalSec) || 4);
  const timestamps = [];
  for (let t = 0; t < duration && timestamps.length < maxSampled; t += step) {
    timestamps.push(Math.min(duration - 0.05, Math.max(0, Number(t.toFixed(2)))));
  }
  if (!timestamps.length) timestamps.push(0);

  const srcW = player.videoWidth || 640;
  const srcH = player.videoHeight || 360;
  const targetW = Math.min(480, Math.max(240, srcW));
  const targetH = Math.max(135, Math.round(targetW * (srcH / Math.max(1, srcW))));
  canvas.width = targetW;
  canvas.height = targetH;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });

  const tiny = document.createElement("canvas");
  tiny.width = 64;
  tiny.height = 36;
  const tinyCtx = tiny.getContext("2d", { willReadFrequently: true });

  const frames = [];
  let prevTinyData = null;

  for (const ts of timestamps) {
    await new Promise((resolve) => {
      const doneSeek = () => resolve();
      player.addEventListener("seeked", doneSeek, { once: true });
      player.currentTime = ts;
    });
    ctx.drawImage(player, 0, 0, targetW, targetH);
    tinyCtx.drawImage(player, 0, 0, 64, 36);
    const imgData = tinyCtx.getImageData(0, 0, 64, 36).data;

    let mseSum = 0;
    let lumaSum = 0;
    let lumaMax = 0;
    const nPx = 64 * 36;
    const lumaVals = new Float32Array(nPx);
    for (let i = 0; i < nPx; i++) {
      const idx = i * 4;
      const luma = 0.299 * imgData[idx] + 0.587 * imgData[idx + 1] + 0.114 * imgData[idx + 2];
      lumaVals[i] = luma;
      lumaSum += luma;
      if (luma > lumaMax) lumaMax = luma;
      if (prevTinyData) {
        const dR = imgData[idx] - prevTinyData[idx];
        const dG = imgData[idx + 1] - prevTinyData[idx + 1];
        const dB = imgData[idx + 2] - prevTinyData[idx + 2];
        mseSum += (dR * dR + dG * dG + dB * dB) / 3.0;
      }
    }
    const meanLuma = lumaSum / nPx;
    let varSum = 0;
    for (let i = 0; i < nPx; i++) {
      const diff = lumaVals[i] - meanLuma;
      varSum += diff * diff;
    }
    const mseDelta = prevTinyData ? Number((mseSum / nPx).toFixed(3)) : 255.0;
    prevTinyData = new Uint8ClampedArray(imgData);

    frames.push({
      timestamp_s: ts,
      data_uri: canvas.toDataURL("image/jpeg", 0.78),
      mse_delta: mseDelta,
      metrics: {
        brightness: Number((meanLuma / 255.0).toFixed(4)),
        contrast: Number(Math.min(1.0, Math.sqrt(varSum / nPx) / 128.0).toFixed(4)),
        intensity: Number((lumaMax / 255.0).toFixed(4)),
      },
    });
  }
  return frames;
}

function getStoredVideoInteractionMap() {
  try {
    const raw = localStorage.getItem("jupiter_video_interaction_ids");
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_) {
    return {};
  }
}

function storeVideoInteractionId(filename, interactionId) {
  if (!filename || !interactionId) return;
  try {
    const map = getStoredVideoInteractionMap();
    map[String(filename)] = String(interactionId);
    localStorage.setItem("jupiter_video_interaction_ids", JSON.stringify(map));
  } catch (_) {}
}

function useVideoInteractionId(btn) {
  const iid = btn?.dataset?.iid || "";
  const prevEl = document.getElementById("vid-gen-prev-id");
  if (prevEl && iid) {
    prevEl.value = iid;
    prevEl.focus();
    showToast("Loaded previous_interaction_id for cloud edit/extend");
  }
}

function renderVideoSceneList(targetEl, scenes, clickable = true) {
  if (!targetEl) return;
  if (!Array.isArray(scenes) || !scenes.length) {
    targetEl.innerHTML = `<div style="font-size:11.5px; color:var(--muted);">No indexed scenes matched yet.</div>`;
    return;
  }
  targetEl.innerHTML = scenes.map((s) => {
    const rawTs = Number(s.timestamp_s);
    const safeTs = Number.isFinite(rawTs) ? rawTs : 0;
    return `
    <div style="padding:8px 10px; border-radius:8px; border:1px solid var(--border); background:var(--bg-surface); ${clickable ? "cursor:pointer;" : ""}" ${clickable ? `onclick="seekVideoPreview(${safeTs})"` : ""}>
      <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:3px;">
        <span class="mem-topic-pill" style="margin:0;">${escapeHtml(s.timestamp_label || "00:00")} · ${escapeHtml(s.video_name || s.video_slug || "clip")}</span>
        <span style="font-family:var(--font-mono); font-size:10px; color:var(--muted);">${s.mood ? escapeHtml(s.mood) : ""}</span>
      </div>
      <div style="font-weight:600; font-size:12px; color:var(--text);">${escapeHtml(s.label || "Scene Marker")}</div>
      <div style="font-size:11.5px; color:var(--text-soft); margin-top:2px;">${escapeHtml(s.summary || "")}</div>
    </div>
  `;
  }).join("");
}

let cachedVideoCatalog = [];

function syncVideoGenSetupBanner() {
  const sel = document.getElementById("vid-gen-target");
  const setupBox = document.getElementById("vid-gen-setup-note");
  if (!sel || !setupBox) return;
  const targetVal = sel.value || "gemini:gemini-omni-1.2-flash";
  const match = cachedVideoCatalog.find((c) => c.target === targetVal);
  if (match && !match.ready) {
    setupBox.style.display = "block";
    setupBox.textContent = `Add ${match.env_var}=your_key to .env and restart Jupiter Studio to run ${match.label} (0 MB VRAM).`;
  } else if (!cachedVideoCatalog.length) {
    setupBox.style.display = "none";
  } else {
    setupBox.style.display = "none";
  }
}

function onVideoGenTargetChange() {
  syncVideoGenSetupBanner();
  updateVideoCostEstimate();
}

function applyVideoPreset(kind) {
  const sel = document.getElementById("vid-gen-target");
  const resEl = document.getElementById("vid-gen-res");
  const durEl = document.getElementById("vid-gen-duration");
  if (kind === "draft") {
    if (resEl) resEl.value = "360p";
    if (durEl) durEl.value = "5";
    const draftPref = cachedVideoCatalog.find((c) => c.tier === "draft" && c.ready)
      || cachedVideoCatalog.find((c) => c.ready)
      || cachedVideoCatalog.find((c) => c.tier === "draft");
    if (sel && draftPref) sel.value = draftPref.target;
    showToast("Applied Draft preset (360p · 5s · low cost)");
  } else {
    if (resEl) resEl.value = "1080p";
    if (durEl) durEl.value = "10";
    const heroPref = cachedVideoCatalog.find((c) => c.tier === "hero" && c.ready)
      || cachedVideoCatalog.find((c) => c.ready)
      || cachedVideoCatalog.find((c) => c.target === "gemini:gemini-omni-1.2-flash");
    if (sel && heroPref) sel.value = heroPref.target;
    showToast("Applied Hero preset (1080p · 10s · flagship)");
  }
  onVideoGenTargetChange();
}

async function updateVideoCostEstimate() {
  const bar = document.getElementById("vid-gen-cost-bar");
  const target = document.getElementById("vid-gen-target")?.value || "gemini:gemini-omni-1.2-flash";
  const resolution = document.getElementById("vid-gen-res")?.value || "720p";
  const duration = Number(document.getElementById("vid-gen-duration")?.value || 5);
  const rawCap = (document.getElementById("vid-gen-max-usd")?.value || "").trim();
  if (!bar) return;
  try {
    const qs = new URLSearchParams({ target, duration: String(duration), resolution });
    if (rawCap !== "") qs.set("max_budget_usd", rawCap);
    const res = await fetch(`/api/video/estimate?${qs.toString()}`);
    if (!res.ok) return;
    const est = await res.json();
    const estUsd = Number(est.estimated_cost_usd || 0).toFixed(2);
    const rateUsd = Number(est.rate_per_sec_usd || 0).toFixed(2);
    const capTxt = est.max_budget_usd != null ? `Cap $${Number(est.max_budget_usd).toFixed(2)}` : "No Cap";
    const statusTxt = est.within_budget ? "WITHIN CAP" : "OVER CAP (BLOCKED)";
    bar.style.borderColor = est.within_budget ? "var(--border)" : "var(--red)";
    bar.style.color = est.within_budget ? "var(--text-soft)" : "var(--red)";
    bar.textContent = `Pre-Flight Estimate: $${estUsd} USD (${est.duration_s}s ${est.resolution} x $${rateUsd}/s · ${est.provider}) | ${capTxt} · ${statusTxt}`;
  } catch (_) {}
}

function renderVideoSpendLedger(data) {
  const spendPill = document.getElementById("vid-ledger-spend-pill");
  const gatedPill = document.getElementById("vid-ledger-gated-pill");
  const chainPill = document.getElementById("vid-ledger-chain-pill");
  const body = document.getElementById("vid-ledger-body");
  const s = data?.summary || {};
  if (spendPill) spendPill.textContent = `Est. Spend: $${Number(s.total_est_spend_usd || 0).toFixed(2)}`;
  if (gatedPill) gatedPill.textContent = `Frames Gated: ${Number(s.total_frames_skipped || 0)}`;
  if (chainPill) chainPill.textContent = data?.ledger_valid === false ? "SHA-256 ALERT" : `SHA-256 Valid (${Number(data?.event_count || 0)})`;
  if (!body) return;
  const entries = Array.isArray(data?.entries) ? data.entries : [];
  if (!entries.length) {
    body.innerHTML = `<tr><td colspan="6" style="color:var(--muted);">No cloud video jobs recorded in control_plane_ledger yet.</td></tr>`;
    return;
  }
  body.innerHTML = entries.map((e) => {
    const isGen = e.event === "cloud_video_generate";
    const kind = isGen ? "GENERATE" : "ANALYZE";
    const scope = isGen
      ? `${Number(e.duration_s || 0)}s · ${e.resolution || "720p"}`
      : `Skipped ${Number(e.frames_skipped || 0)}/${Number(e.frames_total || 0)}`;
    const costStr = isGen ? `$${Number(e.est_cost_usd || 0).toFixed(2)}` : "$0.00 (Gated)";
    return `
      <tr>
        <td>${escapeHtml(kind)}</td>
        <td>${escapeHtml(e.provider || "")} · ${escapeHtml(e.model || "")}</td>
        <td>${escapeHtml(scope)}</td>
        <td>${escapeHtml(costStr)}</td>
        <td>${Number(e.local_vram_mb || 0)} MB</td>
        <td>${escapeHtml(e.event_id || "")}</td>
      </tr>
    `;
  }).join("");
}

async function loadVideoSpendLedger() {
  try {
    const res = await fetch("/api/video/ledger");
    if (res.ok) renderVideoSpendLedger(await res.json());
  } catch (_) {}
}

async function loadCloudVideoStage() {
  try {
    const [stRes, scRes, ldRes] = await Promise.all([
      fetch("/api/video/status"),
      fetch("/api/video/scenes"),
      fetch("/api/video/ledger"),
    ]);
    if (stRes.ok) {
      const d = await stRes.json();
      const anPill = document.getElementById("vid-analyzer-pill");
      const genPill = document.getElementById("vid-generator-pill");
      const storPill = document.getElementById("vid-storage-pill");
      const destPill = document.getElementById("vid-gen-dest-pill");
      const outGrid = document.getElementById("vid-outputs-grid");
      const targetSel = document.getElementById("vid-gen-target");
      const anReady = Boolean(d.analyzer?.ready);
      const genReady = Boolean(d.generator?.ready);
      if (anPill) anPill.textContent = `Analyzer: ${anReady ? "READY (Cloud)" : "OFFLINE"}`;
      if (genPill) genPill.textContent = `Video Gen: ${genReady ? "READY (Cloud)" : "SET API KEY"}`;
      if (storPill) storPill.textContent = `Output: ${d.generator?.output_dir || "./outputs/video"}`;
      if (destPill) destPill.textContent = `0 MB VRAM -> ${d.generator?.output_dir || "./outputs/video"}`;

      cachedVideoCatalog = Array.isArray(d.generator?.catalog) ? d.generator.catalog : [];
      if (targetSel && cachedVideoCatalog.length) {
        const prevVal = targetSel.value;
        targetSel.innerHTML = cachedVideoCatalog.map((item) => {
          const badge = item.ready ? "READY" : `SET ${item.env_var}`;
          return `<option value="${escapeHtml(item.target)}">${escapeHtml(item.label)} [${escapeHtml(badge)}]</option>`;
        }).join("");
        if (cachedVideoCatalog.some((c) => c.target === prevVal)) targetSel.value = prevVal;
      }
      syncVideoGenSetupBanner();
      updateVideoCostEstimate();

      if (outGrid) {
        const vids = Array.isArray(d.outputs) ? d.outputs : [];
        const iidMap = getStoredVideoInteractionMap();
        if (!vids.length) {
          outGrid.innerHTML = `<div style="font-size:11.5px; color:var(--muted);">No cloud-generated .mp4 clips saved yet.</div>`;
        } else {
          outGrid.innerHTML = vids.map((v) => {
            const safeUrl = String(v.video_url || "").startsWith("/api/video/outputs/") ? v.video_url : "";
            const storedIid = v.interaction_id || iidMap[String(v.filename || "")] || "";
            const iidBtn = storedIid
              ? `<button class="btn-mini" data-iid="${escapeHtml(storedIid)}" onclick="useVideoInteractionId(this)" style="margin-top:2px;">Use Interaction ID</button>`
              : "";
            return `
              <div style="padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg-surface); display:flex; flex-direction:column; gap:6px;">
                ${safeUrl ? `<video controls preload="metadata" src="${escapeHtml(safeUrl)}" style="width:100%; max-height:160px; border-radius:6px; background:#000;"></video>` : ""}
                <div style="font-family:var(--font-mono); font-size:10.5px; color:var(--text); word-break:break-all;">${escapeHtml(v.filename || "clip.mp4")}</div>
                <div style="font-family:var(--font-mono); font-size:10px; color:var(--muted);">${Number(v.size_mb || 0)} MB · 0 MB Local VRAM</div>
                ${iidBtn}
              </div>
            `;
          }).join("");
        }
      }
    }
    if (scRes.ok) {
      const sd = await scRes.json();
      renderVideoSceneList(document.getElementById("vid-vault-scenes"), sd.scenes || [], false);
    }
    if (ldRes.ok) {
      renderVideoSpendLedger(await ldRes.json());
    }
  } catch (_) {}
}

async function runCloudVideoAnalyze() {
  const btn = document.getElementById("btn-vid-analyze");
  const st = document.getElementById("vid-analyze-status");
  const met = document.getElementById("vid-analyze-metrics");
  const listEl = document.getElementById("vid-scene-results");
  if (!currentVideoFileObj) {
    showToast("Choose a video file first");
    return;
  }
  const target = document.getElementById("vid-analyze-model")?.value || "cloud:MiniCPM-V-4.7-35B-A3B";
  const intervalSec = Number(document.getElementById("vid-sample-interval")?.value || 4);
  const maxCloud = Number(document.getElementById("vid-max-frames")?.value || 8);
  const promptHint = document.getElementById("vid-prompt-hint")?.value || "";
  const saveVault = Boolean(document.getElementById("vid-save-vault")?.checked);

  if (btn) btn.disabled = true;
  if (st) st.textContent = "Sampling keyframes on CPU & computing pixel MSE deltas...";
  try {
    const frames = await extractFramesFromVideoFile(currentVideoFileObj, intervalSec, 24);
    if (st) st.textContent = `Sending ${frames.length} sampled frames through CPU gate -> ${target} (0 MB VRAM)...`;
    const res = await fetch("/api/video/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_name: currentVideoFileObj.name,
        target,
        prompt_hint: promptHint,
        max_cloud_frames: maxCloud,
        save_to_vault: saveVault,
        frames,
      }),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) throw new Error(d.error || `HTTP ${res.status}`);
    if (st) st.textContent = `Indexed ${d.scenes?.length || 0} scene(s) via ${d.model} [${d.provider}] in ${Math.round(d.total_ms || 0)} ms.`;
    if (met) {
      met.style.display = "block";
      met.textContent = `Sampled: ${d.frames_total} | CPU Gate Skipped: ${d.frames_skipped} (${d.frames_skipped_pct}%) | Cloud Offloaded: ${d.frames_offloaded} | Gate Latency: ${d.gate_ms} ms | Local VRAM: ${d.local_vram_mb} MB`;
    }
    renderVideoSceneList(listEl, d.scenes || [], true);
    loadCloudVideoStage();
    loadMemoryVault();
    showToast(`Cloud video indexed (${d.frames_skipped_pct}% static frames skipped)`);
  } catch (err) {
    if (st) st.textContent = `Analyze failed: ${err.message || err}`;
    showToast(err.message || "Cloud video analysis failed");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function searchIndexedScenes() {
  const q = (document.getElementById("vid-scene-search")?.value || "").trim();
  try {
    const res = await fetch(`/api/video/scenes?q=${encodeURIComponent(q)}`);
    if (!res.ok) return;
    const d = await res.json();
    renderVideoSceneList(document.getElementById("vid-vault-scenes"), d.scenes || [], false);
  } catch (_) {}
}

async function runCloudVideoGenerate() {
  const btn = document.getElementById("btn-vid-generate");
  const st = document.getElementById("vid-gen-status");
  const prompt = (document.getElementById("vid-gen-prompt")?.value || "").trim();
  if (!prompt) {
    showToast("Enter a video generation prompt");
    return;
  }
  const target = document.getElementById("vid-gen-target")?.value || "gemini:gemini-omni-1.2-flash";
  const aspect_ratio = document.getElementById("vid-gen-aspect")?.value || "16:9";
  const resolution = document.getElementById("vid-gen-res")?.value || "720p";
  const duration = Number(document.getElementById("vid-gen-duration")?.value || 5);
  const previous_interaction_id = (document.getElementById("vid-gen-prev-id")?.value || "").trim() || null;
  const rawCap = (document.getElementById("vid-gen-max-usd")?.value || "").trim();
  const max_budget_usd = rawCap !== "" ? Number(rawCap) : null;

  if (btn) btn.disabled = true;
  if (st) st.textContent = `Dispatching ${target} job to cloud (0 MB Local VRAM)...`;
  try {
    const first_frame_data_uri = await readImageInputAsDataUri(document.getElementById("vid-gen-first-frame"));
    const last_frame_data_uri = await readImageInputAsDataUri(document.getElementById("vid-gen-last-frame"));
    const res = await fetch("/api/video/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target,
        prompt,
        aspect_ratio,
        resolution,
        duration,
        max_budget_usd,
        first_frame_data_uri,
        last_frame_data_uri,
        previous_interaction_id,
      }),
    });
    const d = await res.json();
    if (!res.ok || !d.ok) throw new Error(d.error || d.setup_hint || `HTTP ${res.status}`);
    if (st) {
      const iid = d.interaction_id ? ` · ID: ${d.interaction_id}` : "";
      const est = d.estimated_cost_usd != null ? ` · Est. $${Number(d.estimated_cost_usd).toFixed(2)}` : "";
      st.textContent = `Saved ${d.filename} (${(Number(d.size_bytes || 0) / (1024 * 1024)).toFixed(2)} MB${est}) · 0 MB Local VRAM${iid}`;
    }
    if (d.interaction_id) {
      storeVideoInteractionId(d.filename, d.interaction_id);
      const prevEl = document.getElementById("vid-gen-prev-id");
      if (prevEl) prevEl.value = d.interaction_id;
    }
    loadCloudVideoStage();
    loadMemoryVault();
    showToast(`Cloud video saved: ${d.filename}`);
  } catch (err) {
    if (st) st.textContent = `Generate notice: ${err.message || err}`;
    showToast(err.message || "Cloud video generation unavailable");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function loadRecoveryBanner() {
  const banner = document.getElementById("recovery-banner");
  const listEl = document.getElementById("recovery-list");
  if (!banner || !listEl) return;
  try {
    const res = await fetch("/api/ops/recovery");
    if (!res.ok) return;
    const data = await res.json();
    const items = Array.isArray(data.recoverable) ? data.recoverable : [];
    if (!items.length) {
      banner.style.display = "none";
      listEl.innerHTML = "";
      return;
    }
    listEl.innerHTML = "";
    items.slice(0, 4).forEach((item) => {
      const chip = document.createElement("div");
      chip.style.cssText = "display:inline-flex; align-items:center; gap:6px; padding:3px 8px; border-radius:7px; border:1px solid var(--border); background:var(--bg-surface); font-size:11.5px;";
      const lbl = document.createElement("span");
      lbl.textContent = `${item.state || "RECOVERING"}: ${String(item.objective || item.operation_id).slice(0, 56)}`;
      const btnRes = document.createElement("button");
      btnRes.className = "btn-mini";
      btnRes.style.padding = "2px 7px";
      btnRes.textContent = "Resume";
      btnRes.onclick = () => resumeRecoveredOp(item.operation_id, item.objective || "");
      const btnDis = document.createElement("button");
      btnDis.className = "btn-mini";
      btnDis.style.padding = "2px 7px";
      btnDis.textContent = "Dismiss";
      btnDis.onclick = () => dismissRecoveredOp(item.operation_id);
      chip.append(lbl, btnRes, btnDis);
      listEl.appendChild(chip);
    });
    banner.style.display = "flex";
  } catch (_) {}
}

async function resumeRecoveredOp(opId, objective) {
  await dismissRecoveredOp(opId, true);
  switchStageView("ops");
  const inp = document.getElementById("prompt-input");
  if (inp && objective) {
    inp.value = objective;
    autoGrowPrompt(inp);
    sendPrompt();
  }
}

async function dismissRecoveredOp(opId, quiet = false) {
  try {
    await fetch("/api/ops/recovery/dismiss", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operation_id: opId }),
    });
    if (!quiet) showToast(`Dismissed recovery entry ${opId}`);
    loadRecoveryBanner();
    if (activeStageView === "control") loadControlCentre();
  } catch (_) {}
}

async function loadControlCentre() {
  try {
    const [hRes, pRes, lRes, mRes] = await Promise.all([
      fetch("/api/control-plane/health"),
      fetch("/api/plugins"),
      fetch("/api/ops/ledger"),
      fetch("/api/models"),
    ]);
    if (hRes.ok) {
      const h = await hRes.json();
      const hb = document.getElementById("cc-health-badge");
      if (hb) hb.textContent = `${String(h.status || "healthy").toUpperCase()} · ${Math.round(h.latency_ms || 0)} ms`;
      const lb = document.getElementById("cc-ledger-badge");
      const led = h.subsystems?.ledger || {};
      if (lb) lb.textContent = `${led.valid ? "LEDGER VALID" : "LEDGER ALERT"} · ${Number(led.event_count || 0)} events`;

      const bBody = document.getElementById("cc-breakers-body");
      if (bBody) {
        const breakers = Array.isArray(h.breakers) ? h.breakers : [];
        if (!breakers.length) {
          bBody.innerHTML = `<tr><td colspan="4" style="color:var(--muted);">All providers nominal (no tripped breakers recorded yet).</td></tr>`;
        } else {
          bBody.innerHTML = "";
          breakers.forEach((b) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${escapeHtml(b.name)}</td><td>${escapeHtml(b.state)}</td><td>${Number(b.failures || 0)} / ${Number(b.failure_threshold || 5)}</td><td></td>`;
            const rstBtn = document.createElement("button");
            rstBtn.className = "btn-mini";
            rstBtn.style.padding = "2px 8px";
            rstBtn.textContent = "Reset";
            rstBtn.onclick = () => resetCircuitBreakers(b.name);
            tr.lastElementChild.appendChild(rstBtn);
            bBody.appendChild(tr);
          });
        }
      }
    }

    if (mRes.ok) {
      const m = await mRes.json();
      const pGrid = document.getElementById("cc-providers-grid");
      if (pGrid) {
        const prov = m.providers || {};
        pGrid.innerHTML = "";
        Object.entries(prov).filter(([k]) => k !== "auto").forEach(([k, info]) => {
          const pill = document.createElement("span");
          pill.className = "branch-pill";
          pill.style.borderColor = info?.ready ? "var(--border-accent)" : "var(--border)";
          pill.style.color = info?.ready ? "var(--text)" : "var(--muted)";
          pill.title = info?.reason || "Ready";
          pill.textContent = `${k}: ${info?.ready ? "READY" : "OFFLINE"}`;
          pGrid.appendChild(pill);
        });
      }
    }

    if (pRes.ok) {
      const p = await pRes.json();
      const plugGrid = document.getElementById("cc-plugins-grid");
      if (plugGrid) {
        plugGrid.innerHTML = "";
        (p.loaded || []).forEach((pack) => {
          const card = document.createElement("div");
          card.className = "cc-card";
          const policyText = pack.require_human_approval ? "Approval Required" : "Auto-Approved Read-Only";
          card.innerHTML = `
            <div class="cc-card-head">
              <strong style="color:var(--text);">${escapeHtml(pack.name)}</strong>
              <span class="branch-pill">${escapeHtml(policyText)}</span>
            </div>
            <div style="font-size:11px; color:var(--muted); font-family:var(--font-mono);">SDK v${escapeHtml(pack.sdk_version)} · ${escapeHtml((pack.permissions || []).join(", "))}</div>
          `;
          const btnRow = document.createElement("div");
          btnRow.style.cssText = "display:flex; flex-wrap:wrap; gap:6px; margin-top:4px;";
          (pack.operations || []).forEach((opName) => {
            const b = document.createElement("button");
            b.className = "btn-mini";
            b.textContent = `Run ${opName.split(".").pop()}`;
            b.onclick = () => runPluginOperation(opName, false);
            btnRow.appendChild(b);
          });
          card.appendChild(btnRow);
          plugGrid.appendChild(card);
        });
      }
    }

    if (lRes.ok) {
      const l = await lRes.json();
      const lBody = document.getElementById("cc-ledger-body");
      if (lBody) {
        const runs = Array.isArray(l.runs) ? l.runs : [];
        if (!runs.length) {
          lBody.innerHTML = `<tr><td colspan="7" style="color:var(--muted);">No dispatched operations logged yet.</td></tr>`;
        } else {
          lBody.innerHTML = runs.map((r) => `
            <tr>
              <td>${escapeHtml(r.op_id)}</td>
              <td>${escapeHtml(String(r.objective || "").slice(0, 48))}</td>
              <td>${escapeHtml(r.intent)}</td>
              <td>${escapeHtml(r.executed_target)}</td>
              <td>${escapeHtml(r.hardware_guard)}</td>
              <td>${escapeHtml(r.status)}</td>
              <td>${Math.round(Number(r.latency_ms || 0))} ms</td>
            </tr>
          `).join("");
        }
      }
    }
  } catch (_) {}
}

async function verifyControlLedger() {
  try {
    const res = await fetch("/api/ledger/verify");
    const d = await res.json();
    const lb = document.getElementById("cc-ledger-badge");
    if (lb) lb.textContent = `${d.valid ? "LEDGER VALID" : "LEDGER ALERT"} · ${Number(d.event_count || 0)} events`;
    showToast(d.valid ? `Immutable ledger verified (${d.event_count || 0} events)` : `Ledger verification failed: ${d.reason || "tampered"}`);
  } catch (_) {}
}

async function resetCircuitBreakers(provider = "") {
  try {
    await fetch("/api/breakers/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(provider ? { provider } : {}),
    });
    showToast(provider ? `Reset breaker: ${provider}` : "All circuit breakers reset");
    loadControlCentre();
  } catch (_) {}
}

async function runPluginOperation(opName, approved = false) {
  const outEl = document.getElementById("cc-plugin-output");
  const appEl = document.getElementById("cc-plugin-approval");
  const appTxt = document.getElementById("cc-plugin-approval-text");
  try {
    const res = await fetch("/api/plugins/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operation: opName, approved }),
    });
    const d = await res.json();
    if (res.status === 409 && d.approval_required) {
      pendingPluginOp = opName;
      if (appTxt) appTxt.textContent = `Policy check: '${opName}' requires operator approval before execution.`;
      if (appEl) appEl.style.display = "flex";
      return;
    }
    if (appEl) appEl.style.display = "none";
    pendingPluginOp = null;
    if (outEl) {
      outEl.style.display = "block";
      outEl.textContent = JSON.stringify(d, null, 2);
    }
    showToast(res.ok ? `Executed ${opName}` : (d.error || "Plugin execution failed"));
    loadControlCentre();
  } catch (_) {
    showToast("Plugin execution request failed");
  }
}

function confirmPendingPluginOp() {
  if (!pendingPluginOp) return;
  const op = pendingPluginOp;
  pendingPluginOp = null;
  runPluginOperation(op, true);
}

function cancelPendingPluginOp() {
  pendingPluginOp = null;
  const appEl = document.getElementById("cc-plugin-approval");
  if (appEl) appEl.style.display = "none";
}

/* ── SIDEBAR & TABS ─────────────────────────────────────── */
function setSidebarCollapsed(collapsed, persist = true) {
  const sb = document.getElementById("sidebar");
  const isCollapsed = Boolean(collapsed);
  document.body.classList.toggle("sidebar-collapsed", isCollapsed);
  if (sb) sb.classList.toggle("collapsed", isCollapsed);
  const topBtn = document.getElementById("btn-toggle-sidebar");
  if (topBtn) {
    topBtn.classList.toggle("active", !isCollapsed);
    topBtn.setAttribute("aria-expanded", String(!isCollapsed));
  }
  if (persist) {
    try {
      localStorage.setItem("jupiter_studio_sidebar_collapsed", isCollapsed ? "1" : "0");
    } catch (_) {}
  }
}

function toggleSidebar() {
  const isCollapsed = document.body.classList.contains("sidebar-collapsed") || Boolean(document.getElementById("sidebar")?.classList.contains("collapsed"));
  setSidebarCollapsed(!isCollapsed, true);
}

let lastLockedFrankDecision = null;
let lastSpeculationSnapshot = null;
let frankPulseTimer = null;

const FRANK_INTENT_LABELS = {
  fast_code: "Code & Diffs",
  architecture: "Architecture & Audit",
  large_design: "Large Design & Specs",
  cheap_bg: "Quick Background",
  vram_reclaim: "VRAM & Memory Cleanup",
  memory_pin: "Memory Vault",
  idle: "Ready",
};

function toggleSettingsMenu(forceOpen) {
  const pop = document.getElementById("settings-popover");
  const btn = document.getElementById("btn-settings-menu");
  if (!pop) return;
  const next = typeof forceOpen === "boolean" ? forceOpen : !pop.classList.contains("open");
  pop.classList.toggle("open", next);
  if (btn) btn.setAttribute("aria-expanded", String(next));
}

function toggleMathDrawer() {
  const drawer = document.getElementById("radar-math-drawer");
  const btn = document.getElementById("btn-toggle-math");
  if (!drawer) return;
  const open = drawer.classList.toggle("open");
  if (btn) {
    btn.classList.toggle("active", open);
    btn.setAttribute("aria-expanded", String(open));
    btn.textContent = open ? "Hide Math" : "Math";
  }
}

document.addEventListener("click", (e) => {
  const wrap = document.querySelector(".settings-wrap");
  const pop = document.getElementById("settings-popover");
  if (pop && pop.classList.contains("open") && wrap && !wrap.contains(e.target)) {
    toggleSettingsMenu(false);
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") toggleSettingsMenu(false);
});

function formatDecisionLatency(pred, spec) {
  const us = Number(pred?.latency_us || spec?.mlp_latency_us || 0);
  if (!us || !Number.isFinite(us)) return "< 1 ms";
  return us >= 1000 ? `${(us / 1000).toFixed(2)} ms` : `${us.toFixed(0)} us`;
}

function updateFrankPresentation(pred, spec, pulse = false) {
  const summaryEl = document.getElementById("frank-summary-text");
  const stripEl = document.getElementById("frank-radar-strip");
  const fhModel = document.getElementById("fh-model");
  const fhIntent = document.getElementById("fh-intent");
  const fhVram = document.getElementById("fh-vram");
  const fhLat = document.getElementById("fh-lat");
  const fhReason = document.getElementById("fh-reason");

  const activeSpec = spec || lastSpeculationSnapshot;
  const target = document.getElementById("target-selector")?.value || "auto:d3";
  const modelName = activeSpec?.predicted_model || (target === "auto:d3" ? "Frank: Auto" : target.split(":").slice(1).join(":") || target);
  const isLocal = Boolean(activeSpec?.is_local);
  const vramSaved = Number(activeSpec?.vram_saved_gb ?? 0);
  const vramText = isLocal ? "0 MB VRAM (Local)" : (vramSaved > 0 ? `${vramSaved} GB VRAM saved` : "Local GPU Free");

  const intentKey = pred && pred.intent ? String(pred.intent) : "idle";
  const intentLabel = FRANK_INTENT_LABELS[intentKey] || intentKey;
  const rawPct = pred ? Number(pred.confidence_pct ?? (Number(pred.confidence || 0) * 100)) : 0;
  const pct = Number.isFinite(rawPct) ? Math.round(rawPct) : 0;
  const hasIntent = Boolean(pred && intentKey !== "idle" && pct > 0);
  const latText = formatDecisionLatency(pred, activeSpec);

  if (summaryEl) {
    if (hasIntent) {
      summaryEl.textContent = `${modelName} · ${intentLabel} (${pct}%) · ${vramText}`;
    } else if (activeSpec?.predicted_model) {
      summaryEl.textContent = `${modelName} ready · ${vramText}`;
    } else {
      summaryEl.textContent = "Ready — routes by intent & keeps local VRAM free";
    }
  }

  if (fhModel) fhModel.textContent = modelName;
  if (fhIntent) fhIntent.textContent = hasIntent ? `${intentLabel} (${pct}%)` : "Ready";
  if (fhVram) fhVram.textContent = isLocal ? "0 MB (Local)" : (vramSaved > 0 ? `${vramSaved} GB saved` : "Local GPU Free");
  if (fhLat) fhLat.textContent = latText;
  if (fhReason) {
    if (hasIntent) {
      fhReason.textContent = isLocal
        ? `Frank detected ${intentLabel} (${pct}%) and kept execution local (${modelName}) in ${latText}.`
        : `Frank detected ${intentLabel} (${pct}%) and routed to ${modelName}, saving ~${vramSaved} GB local VRAM.`;
    } else {
      fhReason.textContent = "Type an objective below — Frank classifies intent on CPU in under a millisecond and routes automatically.";
    }
  }

  if (pulse && stripEl) {
    stripEl.classList.remove("frank-pulse");
    void stripEl.offsetWidth;
    stripEl.classList.add("frank-pulse");
    clearTimeout(frankPulseTimer);
    frankPulseTimer = setTimeout(() => stripEl.classList.remove("frank-pulse"), 650);
  }
}

function renderFrankChip(pred, pulse = false) {
  const valEl = document.getElementById("rad-frank");
  const chipEl = document.getElementById("frank-telemetry-chip");
  const intent = pred && pred.intent ? String(pred.intent) : "idle";
  const rawPct = pred ? Number(pred.confidence_pct ?? (Number(pred.confidence || 0) * 100)) : 0;
  const pct = Number.isFinite(rawPct) ? Math.round(rawPct) : 0;
  if (valEl) {
    if (!pred || intent === "idle" || pct <= 0) {
      valEl.textContent = "-- (--%)";
      if (chipEl) chipEl.title = "Frank-v1 onboard neural intent classifier (0 MB VRAM)";
    } else {
      valEl.textContent = `${intent} (${pct}%)`;
      if (chipEl) {
        const probs = pred.probs && typeof pred.probs === "object"
          ? Object.entries(pred.probs)
              .sort((a, b) => Number(b[1]) - Number(a[1]))
              .slice(0, 3)
              .map(([k, v]) => `${k}: ${Math.round(Number(v) * 100)}%`)
              .join(" | ")
          : "";
        const lat = pred.latency_us != null ? ` · ${pred.latency_us} us` : "";
        chipEl.title = `${pred.model || "Frank-v1"}${lat}${probs ? " · " + probs : ""}`;
      }
    }
  }
  updateFrankPresentation(pred, lastSpeculationSnapshot, pulse);
}

async function updateFrankTelemetry(promptText) {
  const clean = String(promptText || "").trim();
  if (!clean) return;
  try {
    const res = await fetch(`/api/frank/predict?q=${encodeURIComponent(clean)}`);
    if (!res.ok) return;
    const d = await res.json();
    lastLockedFrankDecision = d;
    renderFrankChip(d, true);
  } catch (e) {
    console.error("Frank telemetry failed", e);
  }
}

function switchRailTab(tab) {
  const normalized = (tab === "frankhub") ? "memory" : tab;
  const mode = normalized === "workspace" ? "workspace" : (normalized === "memory" ? "memory" : "sessions");
  document.getElementById("tab-sessions")?.classList.toggle("active", mode === "sessions");
  document.getElementById("tab-workspace")?.classList.toggle("active", mode === "workspace");
  document.getElementById("tab-memory")?.classList.toggle("active", mode === "memory");
  document.getElementById("pane-sessions")?.classList.toggle("active", mode === "sessions");
  document.getElementById("pane-workspace")?.classList.toggle("active", mode === "workspace");
  document.getElementById("pane-memory")?.classList.toggle("active", mode === "memory");
  if (mode === "memory") {
    loadMemoryVault();
    loadFrankStatus();
  }
}

function openFrankHub() {
  setSidebarCollapsed(false, false);
  switchRailTab("frankhub");
}

async function loadFrankStatus() {
  const badgeEl = document.getElementById("frank-hub-badge");
  try {
    const res = await fetch("/api/frank/status");
    if (!res.ok) return;
    const d = await res.json();
    const intentsCount = Array.isArray(d.intents) ? d.intents.length : 6;
    const ewcText = d.ewc_protected ? "EWC" : "raw";
    if (badgeEl) badgeEl.textContent = `${d.model || "Frank-v1"} · ${intentsCount} intents · ${ewcText}`;
    if (d.last_prediction && !lastLockedFrankDecision) {
      lastLockedFrankDecision = d.last_prediction;
      renderFrankChip(d.last_prediction, false);
    }
  } catch (_) {}
}

async function loadMemoryVault() {
  const listEl = document.getElementById("memory-fact-list");
  if (!listEl) return;
  try {
    const res = await fetch("/api/memory/vault");
    if (!res.ok) return;
    const data = await res.json();
    const s = data.summary || {};
    const whEl = document.getElementById("mem-wh-saved");
    const ewcEl = document.getElementById("mem-ewc-status");
    if (whEl) whEl.textContent = `${Number(s.estimated_wh_saved || 0).toFixed(2)} Wh`;
    if (ewcEl) ewcEl.textContent = `${Number(s.episodes_count || 0)} ep`;
    const facts = Array.isArray(data.facts) ? data.facts : [];
    if (!facts.length) {
      listEl.innerHTML = `<div style="padding:14px 8px; color:var(--muted); font-size:12px;">No persistent memories pinned yet. Pin rules or hardware preferences so models never forget them across threads.</div>`;
      return;
    }
    listEl.innerHTML = facts.map((f) => `
      <div class="mem-fact-card">
        <div style="min-width:0; flex:1;">
          <span class="mem-topic-pill">${escapeHtml(f.topic || "general")}</span>
          <div style="color:var(--text-soft); word-break:break-word;">${escapeHtml(f.content || "")}</div>
          <div style="font-family:var(--font-mono); font-size:10px; color:var(--muted); margin-top:4px;">Recalled ${Number(f.recall_count || 0)}x</div>
        </div>
        <button class="session-del" style="opacity:0.75;" title="Remove memory" onclick="forgetMemoryFact(${Number(f.id)})">&times;</button>
      </div>
    `).join("");
  } catch (_) {}
}

async function reclaimVramNow() {
  try {
    const res = await fetch("/api/memory/reclaim", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const d = await res.json();
    const unloaded = Array.isArray(d.unloaded_models) && d.unloaded_models.length ? ` (Unloaded ${d.unloaded_models.join(", ")})` : "";
    showToast(`Reclaimed ${d.vram_freed_mb || 0} MB VRAM · ${d.ram_freed_mb || 0} MB RAM${unloaded}`);
    loadStatus();
    loadMemoryVault();
  } catch (_) {
    showToast("Memory reclaim failed");
  }
}

async function trainContinualModel() {
  try {
    const res = await fetch("/api/memory/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ epochs: 80, seed_defaults: true }),
    });
    const d = await res.json();
    if (d.trained) {
      showToast(`EWC continual model updated (${d.episodes_total} ep · ${(Number(d.accuracy || 0) * 100).toFixed(0)}% acc)`);
    } else {
      showToast("No routing episodes logged yet to train EWC");
    }
    loadMemoryVault();
    updateSpeculativeRadar();
  } catch (_) {
    showToast("EWC training failed");
  }
}

async function runAntiForgettingAudit() {
  const box = document.getElementById("mem-audit-box");
  if (box) {
    box.style.display = "block";
    box.textContent = "Running Naive SGD vs EWC+Replay retention test...";
  }
  try {
    const res = await fetch("/api/memory/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const d = await res.json();
    const na = Math.round(Number(d.naive_task_a_after || 0) * 100);
    const ea = Math.round(Number(d.ewc_task_a_after || 0) * 100);
    const eb = Math.round(Number(d.ewc_task_b_after || 0) * 100);
    if (box) {
      box.textContent = `${d.passed ? "PASS" : "CHECK"} · Naive A→B kept ${na}% · EWC+Replay kept ${ea}% / B=${eb}% (${d.mlp_mean_us} μs)`;
    }
    showToast(d.passed ? "Anti-forgetting audit PASSED (100% retained)" : "Anti-forgetting audit completed");
  } catch (_) {
    if (box) box.textContent = "Audit request failed";
  }
}

async function installMemoryFact() {
  const topicEl = document.getElementById("mem-topic-input");
  const bodyEl = document.getElementById("mem-content-input");
  const topic = (topicEl?.value || "general").trim();
  const content = (bodyEl?.value || "").trim();
  if (!content) { showToast("Enter memory text first"); return; }
  try {
    const res = await fetch("/api/memory/remember", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, content }),
    });
    if (res.ok) {
      if (bodyEl) bodyEl.value = "";
      showToast("Persistent memory installed");
      loadMemoryVault();
    }
  } catch (_) {
    showToast("Failed to install memory");
  }
}

async function forgetMemoryFact(factId) {
  try {
    await fetch(`/api/memory/fact/${Number(factId)}`, { method: "DELETE" });
    loadMemoryVault();
    showToast("Memory removed");
  } catch (_) {}
}

async function teachFrank() {
  const pEl = document.getElementById("frank-teach-input");
  const iEl = document.getElementById("frank-teach-intent");
  const prompt = (pEl?.value || "").trim();
  const intent = iEl?.value || "fast_code";
  if (!prompt) { showToast("Enter an example prompt for Frank"); return; }
  try {
    const res = await fetch("/api/frank/teach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, intent }),
    });
    const d = await res.json();
    if (res.ok && d.taught) {
      if (pEl) pEl.value = "";
      showToast(`Frank learned '${intent}' (retention ${(Number(d.curriculum_retention || 1) * 100).toFixed(0)}%)`);
    } else {
      showToast(d.error || "Teach failed");
    }
  } catch (_) {
    showToast("Could not reach /api/frank/teach");
  }
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
      <div style="display:flex; gap:6px; align-items:center;">
        <button class="msg-copy-btn" data-role="speak" onclick="speakAssistantEl(this)">Speak</button>
        <button class="msg-copy-btn" data-role="copy" style="display:none;">Copy</button>
      </div>
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

async function speakAssistantEl(btn) {
  const msgEl = btn?.closest(".msg");
  const text = (msgEl?.querySelector('[data-role="content"]')?.innerText || "").trim();
  if (!text) return;
  const orig = btn.textContent;
  btn.textContent = "CUDA...";
  btn.disabled = true;
  try {
    const res = await fetch("/api/voice/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "custom_voice", speaker: "Ryan", text: text.slice(0, 1200) }),
    });
    const d = await res.json();
    if (d && d.audio_url) {
      const a = new Audio(d.audio_url);
      a.play();
      showToast(`Speaking via CUDA (${d.latency_ms || 0} ms)`);
    } else if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(text.slice(0, 800)));
      showToast("Voice Studio (:7870) offline — using browser speech");
    }
  } catch {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(text.slice(0, 800)));
    }
  } finally {
    btn.textContent = orig;
    btn.disabled = false;
  }
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

let lastModelsData = null;
let manualRunHelperOpen = false;
let currentModelRunCmd = "";

function toggleModelRunHelper() {
  manualRunHelperOpen = !manualRunHelperOpen;
  updateModelRunHelper();
}

function copyModelRunCmd() {
  if (!currentModelRunCmd) return;
  navigator.clipboard?.writeText(currentModelRunCmd).then(() => showToast("Command copied")).catch(() => showToast(currentModelRunCmd));
}

function updateModelRunHelper() {
  const bar = document.getElementById("model-run-helper");
  const badge = document.getElementById("mrh-badge");
  const text = document.getElementById("mrh-text");
  const cmdEl = document.getElementById("mrh-cmd");
  const copyBtn = document.getElementById("mrh-copy");
  const target = document.getElementById("target-selector")?.value || "auto:d3";
  if (!bar || !badge || !text || !cmdEl || !copyBtn) return;

  const p = lastModelsData?.providers || {};
  const oInstalled = Array.isArray(lastModelsData?.ollama_installed) ? lastModelsData.ollama_installed : [];
  const lInstalled = Array.isArray(lastModelsData?.lemonade_installed) ? lastModelsData.lemonade_installed : [];

  let status = "READY";
  let msg = "Ready to run — type a prompt below.";
  let cmd = "";
  let needsAction = false;

  if (target.startsWith("studio:")) {
    status = "BUILT-IN READY";
    msg = "Frank-v1 runs offline on CPU (0 MB VRAM). Zero download needed.";
  } else if (target.startsWith("auto:")) {
    status = "AUTO-ROUTER";
    msg = "Routes automatically across your ready cloud + local servers (Token Lab, HF, Ollama, Lemonade, Frank-v1).";
  } else if (target.startsWith("ollama:")) {
    const modelName = target.slice("ollama:".length);
    const hasExact = oInstalled.some((m) => m === modelName || m === `${modelName}:latest`);
    const isFrank = modelName === "frank" || modelName === "frank:latest";
    const setupCmd = isFrank ? "ollama create frank -f memory/models/Modelfile.frank" : `ollama pull ${modelName}`;
    if (!p.ollama?.ready) {
      status = "START OLLAMA";
      msg = p.ollama?.reason || "Ollama server is offline. Start Ollama app, then select a local model:";
      cmd = hasExact ? "ollama serve" : `ollama serve  # then: ${setupCmd}`;
      needsAction = true;
    } else if (!hasExact) {
      status = "DOWNLOAD NEEDED";
      msg = isFrank
        ? "Build local Frank alias from Modelfile.frank once in PowerShell/Terminal:"
        : "Not downloaded yet in Ollama. Run this once in PowerShell/Terminal, then send a prompt:";
      cmd = setupCmd;
      needsAction = true;
    } else {
      status = "OLLAMA READY";
      msg = `Installed locally in Ollama (${modelName}). Ready to chat.`;
    }
  } else if (target.startsWith("lemonade:")) {
    const modelName = target.slice("lemonade:".length);
    const hasExact = lInstalled.includes(modelName);
    if (!p.lemonade?.ready && lInstalled.length === 0 && (p.lemonade?.reason || "").includes("0 models")) {
      status = "DOWNLOAD NEEDED";
      msg = "Lemonade Server is running on :13305, but 0 models are downloaded yet. Pull a GGUF model:";
      cmd = `lemonade-server pull ${modelName}`;
      needsAction = true;
    } else if (!p.lemonade?.ready) {
      status = "START LEMONADE";
      msg = "Start AMD Lemonade Server (or run Jupiter Studio natively on Windows to reach 127.0.0.1:13305):";
      cmd = `lemonade-server serve --port 13305 --host 0.0.0.0`;
      needsAction = true;
    } else if (!hasExact) {
      status = "DOWNLOAD NEEDED";
      const avail = lInstalled.length ? ` Installed now: ${lInstalled.join(", ")}.` : "";
      msg = `Not downloaded in Lemonade yet.${avail} Pull it with:`;
      cmd = `lemonade-server pull ${modelName}`;
      needsAction = true;
    } else {
      status = "LEMONADE READY";
      msg = `Downloaded & ready on AMD Lemonade Server (:13305).`;
    }
  } else if (target.startsWith("vllm:")) {
    const modelName = target.slice("vllm:".length);
    if (!p.vllm?.ready) {
      status = "START vLLM";
      msg = "Start a local vLLM server on port 8000:";
      cmd = `vllm serve ${modelName} --port 8000`;
      needsAction = true;
    }
  } else if (target.startsWith("flare:")) {
    if (!p.flare?.ready) {
      status = "START FLARE";
      msg = "Start your local NVIDIA Flare endpoint on port 8080 (set FLARE_BASE_URL in .env if different).";
      needsAction = true;
    }
  } else {
    const keyMap = {
      "cloud:": ["cloud", "TOKENLAB_API_KEY"],
      "openai:": ["openai", "OPENAI_API_KEY"],
      "gemini:": ["gemini", "GEMINI_API_KEY"],
      "groq:": ["groq", "GROQ_API_KEY"],
      "openrouter:": ["openrouter", "OPENROUTER_API_KEY"],
      "cerebras:": ["cerebras", "CEREBRAS_API_KEY"],
      "nv:": ["nv", "NVIDIA_API_KEY"],
      "do:": ["do", "DO_MODEL_ACCESS_KEY"],
      "hf:": ["hf", "HF_TOKEN"],
    };
    for (const [prefix, [provKey, envVar]] of Object.entries(keyMap)) {
      if (target.startsWith(prefix)) {
        if (p[provKey]?.billing_error) {
          status = "NO CREDITS";
          msg = p[provKey].reason || `${envVar} has no remaining credits or was rejected.`;
          cmd = "";
          needsAction = true;
        } else if (!p[provKey]?.ready) {
          status = "ADD API KEY";
          msg = `Add ${envVar} to .env and restart Jupiter Studio (0 MB local VRAM):`;
          cmd = `${envVar}=your_key_here`;
          needsAction = true;
        } else {
          status = "CLOUD READY";
          msg = "Cloud provider configured (0 MB local VRAM). Ready to chat.";
        }
        break;
      }
    }
  }

  currentModelRunCmd = cmd;
  badge.textContent = status;
  text.textContent = msg;
  if (cmd) {
    cmdEl.style.display = "inline-block";
    cmdEl.textContent = cmd;
    copyBtn.style.display = "inline-flex";
  } else {
    cmdEl.style.display = "none";
    copyBtn.style.display = "none";
  }
  bar.style.display = (needsAction || manualRunHelperOpen) ? "flex" : "none";
}

function syncCloudOptGroup(groupId, provObj, title, envVar) {
  const grp = document.getElementById(groupId);
  if (!grp || !provObj) return;
  if (provObj.ready) {
    grp.label = `${title} [READY · Zero VRAM]`;
  } else if (provObj.billing_error) {
    grp.label = `${title} [NO CREDITS / DISABLED]`;
  } else {
    grp.label = `${title} [OFFLINE · Set ${envVar}]`;
  }
  Array.from(grp.querySelectorAll("option")).forEach((opt) => {
    opt.disabled = !provObj.ready;
  });
}

async function loadModels(verifyKeys = false) {
  try {
    const res = await fetch(verifyKeys ? "/api/models?verify=1" : "/api/models");
    if (!res.ok) return;
    const data = await res.json();
    lastModelsData = data;
    const p = data.providers || {};

    const optStudio = document.getElementById("opt-studio");
    if (optStudio) {
      optStudio.label = "Jupiter Studio Built-In Helper [READY · 0 MB VRAM]";
    }
    syncCloudOptGroup("opt-tokenlab", p.cloud, "AMD Token Lab Cloud", "TOKENLAB_API_KEY");
    syncCloudOptGroup("opt-openai", p.openai, "OpenAI Cloud", "OPENAI_API_KEY");
    syncCloudOptGroup("opt-gemini", p.gemini, "Google Gemini API", "GEMINI_API_KEY");
    syncCloudOptGroup("opt-nvidia", p.nv, "NVIDIA NIM / Brev Cloud", "NVIDIA_API_KEY");
    syncCloudOptGroup("opt-digitalocean", p.do, "DigitalOcean MI300X", "DO_MODEL_ACCESS_KEY");
    syncCloudOptGroup("opt-hf", p.hf, "Hugging Face Cloud", "HF_TOKEN");
    syncCloudOptGroup("opt-groq", p.groq, "Groq Cloud", "GROQ_API_KEY");
    syncCloudOptGroup("opt-openrouter", p.openrouter, "OpenRouter Cloud", "OPENROUTER_API_KEY");
    syncCloudOptGroup("opt-cerebras", p.cerebras, "Cerebras Cloud", "CEREBRAS_API_KEY");

    const optLemonade = document.getElementById("opt-lemonade");
    if (optLemonade && p.lemonade) {
      const lModels = Array.isArray(data.lemonade_installed) ? data.lemonade_installed : [];
      if (p.lemonade.ready) {
        optLemonade.label = `AMD Lemonade Server (${lModels.length} Ready)`;
      } else if ((p.lemonade.reason || "").includes("0 models")) {
        optLemonade.label = "AMD Lemonade Server [ONLINE · 0 Models Downloaded]";
      } else {
        optLemonade.label = "AMD Lemonade Server [OFFLINE]";
      }
      if (lModels.length > 0) {
        const existing = new Set(Array.from(optLemonade.querySelectorAll("option")).map((o) => o.value));
        lModels.forEach((mId) => {
          const val = `lemonade:${mId}`;
          if (!existing.has(val)) {
            const opt = document.createElement("option");
            opt.value = val;
            opt.textContent = `${mId} (Lemonade Live)`;
            optLemonade.insertBefore(opt, optLemonade.firstChild);
          }
        });
      }
      const lSet = new Set(lModels);
      Array.from(optLemonade.querySelectorAll("option")).forEach((opt) => {
        const mid = opt.value.slice("lemonade:".length);
        opt.disabled = !(p.lemonade.ready && lSet.has(mid));
      });
    }
    const optOllama = document.getElementById("opt-ollama");
    const oModels = Array.isArray(data.ollama_installed) ? data.ollama_installed : [];
    const oSet = new Set(oModels);
    const hasOllamaModel = (mid) => oSet.has(mid) || oSet.has(`${mid}:latest`);
    if (optOllama && p.ollama) {
      optOllama.label = p.ollama.ready
        ? `Local Models (Ollama · ${oModels.length} Installed)`
        : `Local Models (${p.ollama.reason || "Ollama Offline"})`;
      if (oModels.length > 0) {
        const existing = new Set(Array.from(optOllama.querySelectorAll("option")).map((o) => o.value));
        oModels.forEach((mId) => {
          const val = `ollama:${mId}`;
          if (!existing.has(val)) {
            const opt = document.createElement("option");
            opt.value = val;
            opt.textContent = `${mId} (Ollama Installed)`;
            optOllama.insertBefore(opt, optOllama.firstChild);
          }
        });
      }
      Array.from(optOllama.querySelectorAll("option")).forEach((opt) => {
        const mid = opt.value.slice("ollama:".length);
        opt.disabled = !(p.ollama.ready && hasOllamaModel(mid));
      });
    }
    const optSpark = document.getElementById("opt-spark");
    if (optSpark) {
      const sparkReady = Boolean((p.vllm && p.vllm.ready) || (p.flare && p.flare.ready));
      optSpark.label = `DGX Spark / GB10 Local ${sparkReady ? "[READY]" : "[OFFLINE]"}`;
      Array.from(optSpark.querySelectorAll("option")).forEach((opt) => {
        if (opt.value.startsWith("ollama:")) {
          opt.disabled = !(p.ollama?.ready && hasOllamaModel(opt.value.slice("ollama:".length)));
        } else if (opt.value.startsWith("vllm:")) {
          opt.disabled = !Boolean(p.vllm && p.vllm.ready);
        } else if (opt.value.startsWith("flare:")) {
          opt.disabled = !Boolean(p.flare && p.flare.ready);
        }
      });
    }
    updateModelRunHelper();
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
      const tempVal = gpu.temperature_c !== null && gpu.temperature_c !== undefined ? Number(gpu.temperature_c) : null;
      healthEl.textContent = tempVal !== null ? `${Math.round(tempVal)}C · ${score}/${grade}` : `${score}/${grade}`;
      healthEl.style.color = "";
      const heatAlert = score < 80 || (tempVal !== null && tempVal >= 60);
      healthEl.classList.toggle("heat-warn", heatAlert);
    }
    if (data.policy) {
      if (gateEl) gateEl.textContent = data.policy.cpu_gate_ms != null ? `${data.policy.cpu_gate_ms} ms` : "--";
      if (vramEl) vramEl.textContent = `${data.policy.local_vram_saved_pct ?? 100}%`;
      if (cardsEl) cardsEl.textContent = `${data.policy.active_cards ?? 0} Active`;
    }

    const optTL = document.getElementById("opt-tokenlab");
    if (optTL && data.cloud?.amd_tokenlab) {
      optTL.label = `AMD Token Lab Cloud ${data.cloud.amd_tokenlab.configured ? "[READY]" : "[OFFLINE · Set Key]"}`;
    }
    const optNV = document.getElementById("opt-nvidia");
    if (optNV && data.cloud?.nvidia_brev) {
      optNV.label = `NVIDIA NIM / Brev Cloud ${data.cloud.nvidia_brev.configured ? "[READY]" : "[OFFLINE · Set Key]"}`;
    }
    const optDO = document.getElementById("opt-digitalocean");
    if (optDO && data.cloud?.digitalocean_mi300x) {
      optDO.label = `DigitalOcean Serverless ${data.cloud.digitalocean_mi300x.configured ? "[READY]" : "[OFFLINE · Set Key]"}`;
    }
    const optHF = document.getElementById("opt-hf");
    if (optHF && data.cloud?.huggingface) {
      optHF.label = `Hugging Face Cloud ${data.cloud.huggingface.configured ? "[READY]" : "[OFFLINE · Set HF_TOKEN]"}`;
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
  updateModelRunHelper();
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
    lastSpeculationSnapshot = d;
    if (text.trim() && d.frank) {
      renderFrankChip(d.frank, false);
    } else if (!text.trim() && lastLockedFrankDecision) {
      renderFrankChip(lastLockedFrankDecision, false);
    } else {
      updateFrankPresentation(null, d, false);
    }
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
  entries.push({ label: "View: Operations Console", group: "Stage", action: () => switchStageView("ops") });
  entries.push({ label: "View: Cloud Video Studio (Analyze & Generate · 0 MB VRAM)", group: "Stage", action: () => switchStageView("video") });
  entries.push({ label: "View: Hugging Face Open-Weight Hub (8GB Fit & $0.00 GGUF)", group: "Stage", action: () => switchStageView("hf") });
  entries.push({ label: "View: Control Centre (Ledger, Breakers, Plugins)", group: "Stage", action: () => switchStageView("control") });
  entries.push({ label: "New Persistent Session", group: "Action", action: () => newSession() });
  entries.push({ label: "Toggle Dual Arena Mode", group: "Action", action: () => toggleDualArena() });
  entries.push({ label: "Theme: LIGHT", group: "Theme", action: () => setStudioTheme("light") });
  entries.push({ label: "Theme: DARK", group: "Theme", action: () => setStudioTheme("dark") });
  entries.push({ label: "Theme: PURPLE GLASS (2030 CSS Showcase)", group: "Theme", action: () => setStudioTheme("purple") });
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
  switchStageView("ops");
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
  const enabled = Array.from(sel.options)
    .filter((o) => o.value && !o.disabled && o.value !== primary && o.value !== "auto:d3")
    .map((o) => o.value);
  const preferred = enabled.find((v) => v !== "studio:frank");
  return preferred || enabled[0] || primary;
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
  if (text) updateFrankTelemetry(text);
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
      if (ev === "ops_plan") {
        const planLine = `[Control Plane ${p.op_id || ""}] intent=${p.intent || "?"} -> resource=${p.primary_target || "?"} (${p.hardware_guard || "nominal"})\n`;
        accReasoning += planLine;
        if (rBox && rBody) {
          rBox.style.display = "block";
          rBody.textContent = accReasoning;
        }
      } else if (ev === "start") {
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
        loadModels(false);
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
  if (text) updateFrankTelemetry(text);
  if (input) { input.value = ""; input.style.height = "auto"; }
  clearAllAttachments();

  dismissEmptyState();
  const inner = document.getElementById("thread-inner");
  const aMsg = document.createElement("div");
  aMsg.className = "msg assistant";
  aMsg.innerHTML = `
    <div class="meta-tag meta-auto" style="margin-bottom:6px;">DUAL ARENA SPLIT STREAM</div>
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
        if (ev === "ops_plan") {
        const planLine = `[Control Plane ${p.op_id || ""}] intent=${p.intent || "?"} -> resource=${p.primary_target || "?"} (${p.hardware_guard || "nominal"})\n`;
        accReasoning += planLine;
        if (rBox && rBody) {
          rBox.style.display = "block";
          rBody.textContent = accReasoning;
        }
      } else if (ev === "start") {
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
  const savedTheme = localStorage.getItem("jupiter_studio_theme") || "dark";
  setStudioTheme(savedTheme);
  const savedSidebar = localStorage.getItem("jupiter_studio_sidebar_collapsed");
  const initialCollapsed = savedSidebar !== null ? savedSidebar === "1" : window.innerWidth <= 900;
  setSidebarCollapsed(initialCollapsed, false);
  initQuantumCanvas();
  loadModels();
  loadStatus();
  loadWorkspaceFiles();
  loadSessions();
  loadMemoryVault();
  loadFrankStatus();
  loadRecoveryBanner();
  updateSpeculativeRadar();
  setInterval(loadStatus, 15000);
});
</script>
</body>
</html>
"""

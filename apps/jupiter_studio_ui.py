"""Jupiter Studio UI — Industrial Hardware-Bench Interface (Braun / Avionics / Oscilloscope).

Separated from apps/jupiter_studio.py so UI templates stay modular while remaining
100% zero-dependency and PyInstaller-compatible.
"""

STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="day">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>JUPITER STUDIO // MemoryOS Hardware Bench</title>
<link rel="icon" type="image/png" href="/assets/jupiter_studio_icon.png" />
<style>
  :root {
    --chassis: #f2eee6;
    --well: #e6e0d4;
    --panel: #faf7f1;
    --panel-alt: #ede8dd;
    --ink: #151513;
    --ink-2: #4a4842;
    --muted: #767268;
    --hairline: #cfc7b8;
    --hairline-strong: #9e9687;
    --accent: #ff4d00;
    --accent-ink: #ffffff;
    --signal: #0a7b5c;
    --signal-bg: rgba(10, 123, 92, 0.10);
    --warn: #b45309;
    --err: #c81e1e;
    --code-bg: #181816;
    --code-ink: #ece8df;
    --scope-bg: #151614;
    --scope-grid: rgba(255, 77, 0, 0.14);
    --scope-line: #ff6a26;
    --font-sans: "Space Grotesk", "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
    --font-mono: "JetBrains Mono", "IBM Plex Mono", "Cascadia Code", ui-monospace, monospace;
  }

  html[data-theme="phosphor"] {
    --chassis: #111210;
    --well: #0b0c0a;
    --panel: #171815;
    --panel-alt: #1e201b;
    --ink: #ece9df;
    --ink-2: #b9b5a8;
    --muted: #7d7a70;
    --hairline: #2a2c26;
    --hairline-strong: #46493f;
    --accent: #ffb000;
    --accent-ink: #111210;
    --signal: #34d399;
    --signal-bg: rgba(52, 211, 153, 0.12);
    --warn: #f59e0b;
    --err: #f87171;
    --code-bg: #0a0b09;
    --code-ink: #f4efe3;
    --scope-bg: #080907;
    --scope-grid: rgba(255, 176, 0, 0.14);
    --scope-line: #ffb000;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; overflow: hidden; }
  body {
    background: var(--chassis);
    color: var(--ink);
    font-family: var(--font-sans);
    font-size: 13px;
    line-height: 1.5;
    display: flex;
    flex-direction: column;
    -webkit-font-smoothing: antialiased;
  }

  /* ── TOP INSTRUMENT BEZEL ───────────────────────────────────────────── */
  .bezel {
    height: 54px;
    background: var(--panel);
    border-bottom: 1px solid var(--hairline-strong);
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 16px;
    padding: 0 14px;
    flex-shrink: 0;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .brand-mark {
    width: 32px;
    height: 32px;
    border: 1px solid var(--hairline-strong);
    background: #141413;
    overflow: hidden;
    flex-shrink: 0;
  }
  .brand-mark img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .brand-text { display: flex; flex-direction: column; line-height: 1.1; }
  .brand-title {
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }
  .brand-sub {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  /* Live Oscilloscope Strip */
  .scope-rack {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
  }
  .scope-window {
    position: relative;
    height: 34px;
    flex: 1;
    max-width: 420px;
    min-width: 140px;
    background: var(--scope-bg);
    border: 1px solid var(--hairline-strong);
    overflow: hidden;
  }
  #scope-canvas { width: 100%; height: 100%; display: block; }
  .scope-label {
    position: absolute;
    top: 3px;
    left: 6px;
    font-family: var(--font-mono);
    font-size: 9px;
    color: rgba(255, 255, 255, 0.55);
    letter-spacing: 0.08em;
    pointer-events: none;
  }
  .scope-readout {
    position: absolute;
    bottom: 2px;
    right: 6px;
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--scope-line);
    letter-spacing: 0.06em;
    pointer-events: none;
  }

  .bezel-meters {
    display: flex;
    align-items: center;
    gap: 14px;
    font-family: var(--font-mono);
    font-size: 11px;
  }
  .meter {
    display: flex;
    flex-direction: column;
    line-height: 1.15;
    border-left: 1px solid var(--hairline);
    padding-left: 10px;
  }
  .meter-k { font-size: 9px; color: var(--muted); letter-spacing: 0.09em; text-transform: uppercase; }
  .meter-v { font-size: 11px; font-weight: 700; color: var(--ink); }
  .meter-v.ok { color: var(--signal); }
  .meter-v.hot { color: var(--accent); }

  .bezel-controls {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .hw-btn {
    height: 30px;
    padding: 0 10px;
    background: var(--panel-alt);
    color: var(--ink);
    border: 1px solid var(--hairline-strong);
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: background 0.1s, border-color 0.1s, transform 0.06s;
  }
  .hw-btn:hover { background: var(--well); border-color: var(--ink); }
  .hw-btn:active { transform: translateY(1px); }
  .hw-btn.active {
    background: var(--ink);
    color: var(--panel);
    border-color: var(--ink);
  }
  .hw-btn.accent {
    background: var(--accent);
    color: var(--accent-ink);
    border-color: var(--accent);
  }
  .hw-btn.accent:hover { filter: brightness(1.06); }
  .hw-btn.danger {
    background: var(--err);
    color: #fff;
    border-color: var(--err);
  }
  .hw-btn:disabled { opacity: 0.45; cursor: not-allowed; }

  .led {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--signal);
    display: inline-block;
  }
  .led.busy { background: var(--accent); animation: blink 0.7s steps(2) infinite; }
  @keyframes blink { 50% { opacity: 0.25; } }

  /* ── THREE-BAY WORKBENCH GRID ───────────────────────────────────────── */
  .bench {
    flex: 1;
    display: grid;
    grid-template-columns: 278px 1fr 272px;
    min-height: 0;
    background: var(--hairline-strong);
    gap: 1px;
  }
  .bench.no-inspector {
    grid-template-columns: 278px 1fr 0px;
  }
  .bench.no-inspector .bay-right { display: none; }

  .bay {
    background: var(--chassis);
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }
  .bay-head {
    height: 32px;
    padding: 0 12px;
    background: var(--panel-alt);
    border-bottom: 1px solid var(--hairline);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ink-2);
    flex-shrink: 0;
  }
  .bay-index { color: var(--accent); margin-right: 6px; }
  .bay-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  /* ── BAY 01: ROUTING PATCHBAY + WORKSPACE FILES ─────────────────────── */
  .bus-group { display: flex; flex-direction: column; gap: 4px; }
  .bus-label {
    font-family: var(--font-mono);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
    padding: 2px 2px 2px 0;
    border-bottom: 1px dotted var(--hairline-strong);
  }
  .patch-btn {
    width: 100%;
    text-align: left;
    background: var(--panel);
    color: var(--ink);
    border: 1px solid var(--hairline);
    padding: 6px 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    font-family: var(--font-mono);
    font-size: 11px;
    transition: border-color 0.1s, background 0.1s;
  }
  .patch-btn:hover { border-color: var(--ink); background: var(--panel-alt); }
  .patch-btn.selected {
    background: var(--ink);
    color: var(--panel);
    border-color: var(--ink);
  }
  .patch-btn .patch-tag {
    font-size: 9px;
    color: var(--muted);
    letter-spacing: 0.05em;
    flex-shrink: 0;
  }
  .patch-btn.selected .patch-tag { color: var(--accent); }
  .patch-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  /* Workspace file bay */
  .file-filter {
    width: 100%;
    height: 28px;
    padding: 0 8px;
    background: var(--panel);
    color: var(--ink);
    border: 1px solid var(--hairline-strong);
    font-family: var(--font-mono);
    font-size: 11px;
    outline: none;
  }
  .file-filter:focus { border-color: var(--accent); }
  .file-list {
    border: 1px solid var(--hairline);
    background: var(--panel);
    max-height: 220px;
    overflow-y: auto;
  }
  .file-row {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 5px 8px;
    border-bottom: 1px solid var(--hairline);
    font-family: var(--font-mono);
    font-size: 10.5px;
    cursor: pointer;
    user-select: none;
  }
  .file-row:last-child { border-bottom: none; }
  .file-row:hover { background: var(--panel-alt); }
  .file-row.checked { background: var(--signal-bg); }
  .file-row input { accent-color: var(--accent); cursor: pointer; }
  .file-row .fname { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .file-row .fsize { color: var(--muted); font-size: 9.5px; }

  /* ── BAY 02: EXECUTION TAPE + TACTILE COMMAND DECK ──────────────────── */
  .tape-bay {
    background: var(--panel);
    position: relative;
  }
  .tape {
    flex: 1;
    overflow-y: auto;
    padding: 18px 24px 28px 24px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
  .tape-empty {
    margin: auto;
    max-width: 560px;
    border: 1px solid var(--hairline-strong);
    background: var(--chassis);
    padding: 20px 22px;
  }
  .tape-empty-kicker {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 6px;
  }
  .tape-empty h2 {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 8px;
  }
  .tape-empty p {
    color: var(--ink-2);
    font-size: 12.5px;
    margin-bottom: 14px;
  }
  .quick-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .quick-key {
    text-align: left;
    background: var(--panel);
    border: 1px solid var(--hairline-strong);
    padding: 8px 10px;
    cursor: pointer;
    color: var(--ink);
    font-family: var(--font-mono);
    font-size: 11px;
  }
  .quick-key:hover { border-color: var(--accent); background: var(--panel-alt); }
  .quick-key span { display: block; font-size: 9px; color: var(--muted); margin-bottom: 2px; text-transform: uppercase; }

  /* Tape entry blocks */
  .entry {
    border-left: 3px solid var(--hairline-strong);
    padding-left: 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .entry.user { border-left-color: var(--ink); }
  .entry.assistant { border-left-color: var(--accent); }
  .entry.error { border-left-color: var(--err); }

  .entry-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .entry-seq { color: var(--ink); font-weight: 700; }
  .entry-badge {
    padding: 1px 6px;
    border: 1px solid var(--hairline-strong);
    background: var(--chassis);
    color: var(--ink);
    font-weight: 700;
  }
  .entry-badge.live { border-color: var(--accent); color: var(--accent); }
  .entry-badge.ok { border-color: var(--signal); color: var(--signal); }
  .entry-badge.err { border-color: var(--err); color: var(--err); }

  .entry-body {
    font-size: 13.5px;
    line-height: 1.62;
    color: var(--ink);
    word-break: break-word;
  }
  .entry-body p { margin-bottom: 8px; }
  .entry-body p:last-child { margin-bottom: 0; }
  .entry-body code {
    font-family: var(--font-mono);
    font-size: 12px;
    background: var(--well);
    padding: 1px 5px;
    border: 1px solid var(--hairline);
  }
  .entry-body pre {
    margin: 10px 0;
    background: var(--code-bg);
    color: var(--code-ink);
    border: 1px solid var(--hairline-strong);
    overflow-x: auto;
  }
  .code-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.10);
    font-family: var(--font-mono);
    font-size: 10px;
    color: #9e9a90;
    text-transform: uppercase;
  }
  .code-copy {
    background: transparent;
    color: #ece8df;
    border: 1px solid rgba(255, 255, 255, 0.22);
    font-family: var(--font-mono);
    font-size: 9.5px;
    padding: 1px 7px;
    cursor: pointer;
    text-transform: uppercase;
  }
  .code-copy:hover { border-color: var(--accent); color: var(--accent); }
  .entry-body pre code {
    display: block;
    background: transparent;
    border: none;
    padding: 10px 12px;
    color: var(--code-ink);
    font-size: 12px;
    line-height: 1.5;
  }

  .reasoning-panel {
    border: 1px dashed var(--hairline-strong);
    background: var(--chassis);
    padding: 8px 10px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--ink-2);
    white-space: pre-wrap;
    display: none;
  }
  .reasoning-panel summary {
    cursor: pointer;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-size: 10px;
    color: var(--muted);
    margin-bottom: 4px;
  }

  /* ── COMMAND DECK (INPUT + STAGING TRAY) ────────────────────────────── */
  .deck {
    border-top: 1px solid var(--hairline-strong);
    background: var(--chassis);
    padding: 10px 16px 12px 16px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .deck.drag-over {
    outline: 2px dashed var(--accent);
    outline-offset: -4px;
    background: var(--panel-alt);
  }
  .staging-tray {
    display: none;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
  }
  .staging-tray.has-items { display: flex; }
  .stage-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 8px;
    background: var(--panel);
    border: 1px solid var(--hairline-strong);
    font-family: var(--font-mono);
    font-size: 10.5px;
  }
  .stage-chip button {
    background: none;
    border: none;
    color: var(--err);
    font-family: var(--font-mono);
    font-weight: 700;
    cursor: pointer;
    padding: 0 2px;
  }
  .deck-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 8px;
    align-items: stretch;
  }
  #prompt-input {
    width: 100%;
    min-height: 54px;
    max-height: 180px;
    resize: none;
    background: var(--panel);
    color: var(--ink);
    border: 1px solid var(--hairline-strong);
    padding: 10px 12px;
    font-family: var(--font-sans);
    font-size: 13.5px;
    outline: none;
  }
  #prompt-input:focus { border-color: var(--accent); }
  .deck-actions {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  .deck-subbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
  }
  .deck-tools { display: flex; gap: 6px; align-items: center; }

  /* ── BAY 03: LIVE SIGNAL INSPECTOR ──────────────────────────────────── */
  .spec-card {
    background: var(--panel);
    border: 1px solid var(--hairline);
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .spec-title {
    font-family: var(--font-mono);
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
  }
  .kv-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 11px;
    border-bottom: 1px dotted var(--hairline);
    padding-bottom: 3px;
  }
  .kv-row:last-child { border-bottom: none; padding-bottom: 0; }
  .kv-k { color: var(--muted); font-size: 10px; }
  .kv-v { color: var(--ink); font-weight: 700; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 155px; }
  .kv-v.ok { color: var(--signal); }
  .kv-v.hot { color: var(--accent); }

  /* Signal path diagram */
  .path-node {
    font-family: var(--font-mono);
    font-size: 10px;
    padding: 5px 8px;
    border: 1px solid var(--hairline-strong);
    background: var(--chassis);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .path-node.active { border-color: var(--accent); background: var(--panel-alt); }
  .path-arrow {
    text-align: center;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    line-height: 1;
  }

  /* Health gauge */
  .health-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    font-family: var(--font-mono);
  }
  .health-num { font-size: 26px; font-weight: 700; line-height: 1; }
  .health-grade {
    font-size: 12px;
    font-weight: 700;
    padding: 2px 7px;
    border: 1px solid var(--signal);
    color: var(--signal);
  }
  .bar-track {
    height: 6px;
    background: var(--well);
    border: 1px solid var(--hairline);
    overflow: hidden;
  }
  .bar-fill {
    height: 100%;
    background: var(--signal);
    width: 100%;
    transition: width 0.3s ease;
  }

  /* Modal for IDE bundle export */
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(15, 15, 13, 0.65);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 99;
  }
  .modal-backdrop.open { display: flex; }
  .modal-box {
    width: min(760px, 92vw);
    max-height: 82vh;
    background: var(--panel);
    border: 1px solid var(--hairline-strong);
    display: flex;
    flex-direction: column;
  }
  .modal-body {
    flex: 1;
    padding: 12px;
    overflow: auto;
  }
  .modal-body textarea {
    width: 100%;
    height: 360px;
    background: var(--code-bg);
    color: var(--code-ink);
    border: 1px solid var(--hairline-strong);
    padding: 10px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    resize: vertical;
  }

  /* Scrollbars */
  ::-webkit-scrollbar { width: 7px; height: 7px; }
  ::-webkit-scrollbar-track { background: var(--well); }
  ::-webkit-scrollbar-thumb { background: var(--hairline-strong); }

  @media (max-width: 1060px) {
    .bench { grid-template-columns: 240px 1fr 0px; }
    .bay-right { display: none; }
    .bezel-meters { display: none; }
  }
  @media (max-width: 720px) {
    .bench { grid-template-columns: 1fr; }
    .bay-left, .bay-right { display: none; }
  }
</style>
</head>
<body>

  <!-- TOP INSTRUMENT BEZEL -->
  <header class="bezel">
    <div class="brand">
      <div class="brand-mark">
        <img src="/assets/jupiter_studio_icon.png" alt="J" />
      </div>
      <div class="brand-text">
        <span class="brand-title">Jupiter Studio</span>
        <span class="brand-sub">MemoryOS Bench // v1.0.0-RC1</span>
      </div>
    </div>

    <div class="scope-rack">
      <div class="scope-window" title="Live host-gate & token-stream oscilloscope">
        <canvas id="scope-canvas"></canvas>
        <span class="scope-label">CH1 // ZEN3 GATE + STREAM</span>
        <span class="scope-readout" id="scope-readout">0.091 ms IDLE</span>
      </div>

      <div class="bezel-meters">
        <div class="meter">
          <span class="meter-k">Local VRAM</span>
          <span class="meter-v ok" id="m-vram">0 MB</span>
        </div>
        <div class="meter">
          <span class="meter-k">Active Bus</span>
          <span class="meter-v hot" id="m-target">AUTO:D3</span>
        </div>
        <div class="meter">
          <span class="meter-k">Last Latency</span>
          <span class="meter-v" id="m-lat">-- ms</span>
        </div>
      </div>
    </div>

    <div class="bezel-controls">
      <span class="led" id="sys-led" title="System ready"></span>
      <button class="hw-btn" id="btn-theme" onclick="toggleTheme()">PHOSPHOR</button>
      <button class="hw-btn active" id="btn-inspector" onclick="toggleInspector()">INSPECTOR</button>
      <button class="hw-btn" onclick="openExportBundle()">EXPORT</button>
      <button class="hw-btn" onclick="clearTape()">CLEAR</button>
    </div>
  </header>

  <!-- THREE-BAY MODULAR BENCH -->
  <main class="bench" id="bench-grid">

    <!-- BAY 01: ROUTING PATCHBAY + WORKSPACE FILES -->
    <aside class="bay bay-left">
      <div class="bay-head">
        <span><span class="bay-index">01</span>Routing Patchbay</span>
        <span id="patch-count">14 BUSES</span>
      </div>
      <div class="bay-scroll">
        <div id="patchbay-container" style="display:flex; flex-direction:column; gap:10px;"></div>

        <div class="bus-group" style="margin-top:4px;">
          <div class="bus-label">
            <span>Workspace Context</span>
            <span id="selected-files-count">0 STAGED</span>
          </div>
          <input class="file-filter" id="file-filter" type="text" placeholder="Filter repo files..." oninput="renderWorkspaceFiles()" />
          <div class="file-list" id="workspace-file-list">
            <div class="file-row" style="color:var(--muted);">Scanning workspace...</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- BAY 02: EXECUTION TAPE + COMMAND DECK -->
    <section class="bay tape-bay">
      <div class="bay-head">
        <span><span class="bay-index">02</span>Execution Tape</span>
        <span id="tape-status">READY // ZERO LOCAL VRAM</span>
      </div>

      <div class="tape" id="chat-log">
        <div class="tape-empty" id="tape-empty">
          <div class="tape-empty-kicker">MemoryOS // Zero-VRAM Hybrid Instrument</div>
          <h2>Hardware-Aware Inference Bench</h2>
          <p>
            Select any remote or local execution bus in Bay 01, attach source files or screenshots directly
            onto the command deck below, and transmit. Local GPU VRAM remains reserved for native workloads
            while host-side Zen 3 gating runs in 0.091 ms.
          </p>
          <div class="quick-grid">
            <button class="quick-key" onclick="quickPrompt('Audit the selected workspace files for bugs, security risks, and performance regressions.')">
              <span>01 // Code Audit</span>
              Inspect staged files for risks
            </button>
            <button class="quick-key" onclick="quickPrompt('Explain how MemoryOS keeps local VRAM at 0 MB while routing to AMD Instinct via Token Lab.')">
              <span>02 // Architecture</span>
              Trace zero-VRAM routing path
            </button>
            <button class="quick-key" onclick="quickPrompt('Write a clean, minimal Python unit test for the selected module.')">
              <span>03 // Verification</span>
              Generate targeted unit tests
            </button>
            <button class="quick-key" onclick="quickPrompt('Compare local Ollama vs AMD Token Lab latency and VRAM tradeoffs for a 31B model on an 8 GB laptop.')">
              <span>04 // Benchmark</span>
              Local vs Instinct tradeoff
            </button>
          </div>
        </div>
      </div>

      <div class="deck" id="command-deck">
        <div class="staging-tray" id="staging-tray"></div>

        <div class="deck-row">
          <textarea
            id="prompt-input"
            placeholder="Enter instruction or drop files onto the deck... (Enter to transmit, Shift+Enter for newline)"
          ></textarea>
          <div class="deck-actions">
            <button class="hw-btn accent" id="btn-send" onclick="sendPrompt()" style="height:34px; justify-content:center;">TRANSMIT</button>
            <button class="hw-btn danger" id="btn-stop" onclick="stopGeneration()" style="height:24px; justify-content:center; display:none;">STOP</button>
          </div>
        </div>

        <div class="deck-subbar">
          <div class="deck-tools">
            <input type="file" id="file-upload-input" multiple style="display:none;" onchange="handleFileUpload(event)" />
            <input type="file" id="image-upload-input" accept="image/*" style="display:none;" onchange="handleImageUpload(event)" />
            <button class="hw-btn" style="height:24px;" onclick="document.getElementById('file-upload-input').click()">+ FILE</button>
            <button class="hw-btn" style="height:24px;" onclick="document.getElementById('image-upload-input').click()">+ IMAGE</button>
            <span id="deck-hint">DROP CODE, LOGS, JSON, OR IMAGES</span>
          </div>
          <span id="deck-route-label">BUS: auto:d3</span>
        </div>
      </div>
    </section>

    <!-- BAY 03: LIVE SIGNAL & HARDWARE INSPECTOR -->
    <aside class="bay bay-right">
      <div class="bay-head">
        <span><span class="bay-index">03</span>Signal Inspector</span>
        <span id="insp-clock">00:00:00</span>
      </div>
      <div class="bay-scroll">
        <div class="spec-card">
          <div class="spec-title"><span>Workstation Health</span><span id="health-status">HEALTHY</span></div>
          <div class="health-row">
            <span class="health-num" id="health-score">100</span>
            <span class="health-grade" id="health-grade">GRADE A</span>
          </div>
          <div class="bar-track"><div class="bar-fill" id="health-bar"></div></div>
          <div class="kv-row"><span class="kv-k">VRAM HEADROOM</span><span class="kv-v ok" id="h-vram">100%</span></div>
          <div class="kv-row"><span class="kv-k">THERMAL HEADROOM</span><span class="kv-v ok" id="h-therm">100%</span></div>
        </div>

        <div class="spec-card">
          <div class="spec-title"><span>Signal Path</span><span>LIVE</span></div>
          <div class="path-node active"><span>01 HOST GATE</span><span id="p-gate">0.091 ms</span></div>
          <div class="path-arrow">|</div>
          <div class="path-node"><span>02 ROUTER</span><span id="p-router">d3 AUX</span></div>
          <div class="path-arrow">|</div>
          <div class="path-node"><span>03 TARGET</span><span id="p-target">AUTO</span></div>
        </div>

        <div class="spec-card">
          <div class="spec-title"><span>Hardware Profile</span><span id="hw-vendor">--</span></div>
          <div class="kv-row"><span class="kv-k">GPU</span><span class="kv-v" id="hw-name">Detecting...</span></div>
          <div class="kv-row"><span class="kv-k">VRAM USED</span><span class="kv-v ok" id="hw-vram">0 MB</span></div>
          <div class="kv-row"><span class="kv-k">TELEMETRY</span><span class="kv-v" id="hw-src">--</span></div>
          <div class="kv-row"><span class="kv-k">CPU GATE</span><span class="kv-v" id="hw-gate">0.091 ms</span></div>
        </div>

        <div class="spec-card">
          <div class="spec-title"><span>Cloud & Local Buses</span><span>LINK</span></div>
          <div class="kv-row"><span class="kv-k">AMD TOKEN LAB</span><span class="kv-v" id="c-tokenlab">--</span></div>
          <div class="kv-row"><span class="kv-k">NVIDIA NIM</span><span class="kv-v" id="c-nvidia">--</span></div>
          <div class="kv-row"><span class="kv-k">DIGITALOCEAN</span><span class="kv-v" id="c-do">--</span></div>
          <div class="kv-row"><span class="kv-k">LOCAL OLLAMA</span><span class="kv-v" id="c-ollama">11434</span></div>
        </div>
      </div>
    </aside>

  </main>

  <!-- EXPORT BUNDLE MODAL -->
  <div class="modal-backdrop" id="export-modal">
    <div class="modal-box">
      <div class="bay-head">
        <span>IDE Context Bundle Export</span>
        <div style="display:flex; gap:6px;">
          <button class="hw-btn accent" style="height:22px;" onclick="copyExportBundle()">COPY</button>
          <button class="hw-btn" style="height:22px;" onclick="closeExportBundle()">CLOSE</button>
        </div>
      </div>
      <div class="modal-body">
        <textarea id="export-textarea" readonly></textarea>
      </div>
    </div>
  </div>

<script>
const PATCH_BUSES = [
  {
    group: "AUTO BUS",
    busTag: "d3",
    items: [
      { value: "auto:d3", label: "Auto-Route (d3 Gate)", tag: "AUTO" },
    ],
  },
  {
    group: "AMD TOKEN LAB",
    busTag: "0 MB VRAM",
    items: [
      { value: "cloud:Gemma-4-31B-IT", label: "Gemma-4-31B-IT", tag: "31B VLM" },
      { value: "cloud:Qwen3.8-27B", label: "Qwen3.8-27B", tag: "27B CODE" },
      { value: "cloud:DeepSeek-V4.1-Flash", label: "DeepSeek-V4.1-Flash", tag: "1M CTX" },
      { value: "cloud:MiniCPM5-2B", label: "MiniCPM5-2B", tag: "2B FAST" },
    ],
  },
  {
    group: "NVIDIA NIM / BREV",
    busTag: "NIM",
    items: [
      { value: "nv:qwen/qwen2.5-coder-32b-instruct", label: "Qwen-2.5-Coder-32B", tag: "32B" },
      { value: "nv:meta/llama-3.3-70b-instruct", label: "Llama-3.3-70B", tag: "70B" },
      { value: "nv:qwen/qwen2.5-7b-instruct", label: "Qwen-2.5-7B", tag: "7B" },
    ],
  },
  {
    group: "DIGITALOCEAN MI300X",
    busTag: "MI300X",
    items: [
      { value: "do:Qwen/Qwen2.5-Coder-32B-Instruct", label: "Qwen-2.5-Coder-32B", tag: "MI300X" },
      { value: "do:meta-llama/Llama-3.3-70B-Instruct", label: "Llama-3.3-70B", tag: "MI300X" },
    ],
  },
  {
    group: "DGX SPARK / GB10 LOCAL",
    busTag: "LAN",
    items: [
      { value: "vllm:Qwen/Qwen3.8-Flash-Next", label: "Qwen3.8-Flash-Next", tag: "vLLM:8000" },
      { value: "vllm:deepseek-ai/DeepSeek-V4.1-Flash", label: "DeepSeek-V4.1-Flash", tag: "vLLM:8000" },
      { value: "flare:Qwen3.8-Flash-Next", label: "Qwen3.8-Flash-Next", tag: "FLARE:8080" },
      { value: "flare:DeepSeek-V4.1-Flash", label: "DeepSeek-V4.1-Flash", tag: "FLARE:8080" },
    ],
  },
  {
    group: "LOCAL OLLAMA",
    busTag: "LOCAL",
    items: [
      { value: "ollama:raon-1-nano", label: "raon-1-nano", tag: "1.5B 256K" },
      { value: "ollama:qwen2.5-coder:1.5b", label: "qwen2.5-coder:1.5b", tag: "1.5B" },
      { value: "ollama:qwen2.5-coder:7b", label: "qwen2.5-coder:7b", tag: "7B" },
      { value: "ollama:deepseek-r1:7b", label: "deepseek-r1:7b", tag: "7B R1" },
      { value: "ollama:deepseek-r1:8b", label: "deepseek-r1:8b", tag: "8B R1" },
    ],
  },
];

let selectedTarget = "auto:d3";
let workspaceFiles = [];
let selectedWorkspaceFiles = new Set();
let uploadedFiles = [];
let attachedImageBase64 = null;
let attachedImageName = null;
let chatHistory = [];
let seqCounter = 0;
let isGenerating = false;
let currentAbortController = null;
let scopeEnergy = 0.08;
let scopeTokens = 0;

/* ── PATCHBAY RENDERING ──────────────────────────────────────────────── */
function renderPatchbay() {
  const root = document.getElementById("patchbay-container");
  let total = 0;
  root.innerHTML = PATCH_BUSES.map((bus) => {
    total += bus.items.length;
    const btns = bus.items.map((item) => {
      const sel = item.value === selectedTarget ? "selected" : "";
      return `<button class="patch-btn ${sel}" onclick="selectTarget('${item.value}', '${item.label}')">
        <span class="patch-name">${escapeHtml(item.label)}</span>
        <span class="patch-tag">${escapeHtml(item.tag)}</span>
      </button>`;
    }).join("");
    return `<div class="bus-group">
      <div class="bus-label"><span>${escapeHtml(bus.group)}</span><span>${escapeHtml(bus.busTag)}</span></div>
      ${btns}
    </div>`;
  }).join("");
  document.getElementById("patch-count").innerText = `${total} BUSES`;
}

function selectTarget(val, label) {
  selectedTarget = val;
  renderPatchbay();
  const shortVal = val.split(":").slice(1).join(":") || val;
  document.getElementById("m-target").innerText = shortVal.slice(0, 18).toUpperCase();
  document.getElementById("deck-route-label").innerText = `BUS: ${val}`;
  document.getElementById("p-target").innerText = (label || shortVal).slice(0, 16).toUpperCase();
}

/* ── THEME & INSPECTOR TOGGLES ───────────────────────────────────────── */
function toggleTheme() {
  const html = document.documentElement;
  const next = html.getAttribute("data-theme") === "phosphor" ? "day" : "phosphor";
  html.setAttribute("data-theme", next);
  document.getElementById("btn-theme").innerText = next === "phosphor" ? "CERAMIC" : "PHOSPHOR";
}

function toggleInspector() {
  const grid = document.getElementById("bench-grid");
  const btn = document.getElementById("btn-inspector");
  const hidden = grid.classList.toggle("no-inspector");
  btn.classList.toggle("active", !hidden);
}

/* ── LIVE HARDWARE OSCILLOSCOPE ──────────────────────────────────────── */
(function initOscilloscope() {
  const canvas = document.getElementById("scope-canvas");
  const ctx = canvas.getContext("2d");
  const samples = new Array(120).fill(0);
  let phase = 0;

  function resize() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(120, Math.floor(rect.width * window.devicePixelRatio));
    canvas.height = Math.max(30, Math.floor(rect.height * window.devicePixelRatio));
  }
  resize();
  window.addEventListener("resize", resize);

  function frame() {
    const w = canvas.width;
    const h = canvas.height;
    const cs = getComputedStyle(document.documentElement);
    const bg = cs.getPropertyValue("--scope-bg").trim() || "#151614";
    const grid = cs.getPropertyValue("--scope-grid").trim() || "rgba(255,77,0,0.14)";
    const line = cs.getPropertyValue("--scope-line").trim() || "#ff6a26";

    phase += isGenerating ? 0.32 : 0.08;
    scopeEnergy = Math.max(0.08, scopeEnergy * 0.94);
    const amp = isGenerating ? Math.min(0.85, 0.3 + scopeEnergy) : 0.14;
    const pulse = Math.sin(phase) * amp + (Math.sin(phase * 3.7) * amp * 0.35);
    samples.push(pulse);
    if (samples.length > 120) samples.shift();

    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    // Graticule grid
    ctx.strokeStyle = grid;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    for (let x = 0; x < w; x += Math.max(24, w / 10)) {
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
    }
    ctx.stroke();

    // Waveform trace
    ctx.strokeStyle = line;
    ctx.lineWidth = Math.max(1.5, window.devicePixelRatio * 1.1);
    ctx.beginPath();
    const step = w / (samples.length - 1);
    for (let i = 0; i < samples.length; i++) {
      const x = i * step;
      const y = h / 2 - samples[i] * (h * 0.36);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();

/* ── STATUS & WORKSPACE FILES ────────────────────────────────────────── */
async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    const gpu = data.gpu || {};
    const cloud = data.cloud || {};
    const policy = data.policy || {};
    const health = data.health || null;

    document.getElementById("hw-name").innerText = gpu.name || "CPU / Host Only";
    document.getElementById("hw-vendor").innerText = (gpu.vendor || "HOST").toUpperCase();
    const usedMb = Math.round(gpu.memory_used_mb || 0);
    const totalMb = Math.round(gpu.memory_total_mb || 0);
    document.getElementById("hw-vram").innerText = totalMb ? `${usedMb} / ${totalMb} MB` : `${usedMb} MB`;
    document.getElementById("m-vram").innerText = `${usedMb} MB`;
    document.getElementById("hw-src").innerText = gpu.telemetry_source || "live";
    const gateMs = policy.zen3_gate_ms || "0.091 ms";
    document.getElementById("hw-gate").innerText = gateMs;
    document.getElementById("p-gate").innerText = gateMs;

    const fmtLink = (v) => (v ? "READY" : "OFFLINE");
    document.getElementById("c-tokenlab").innerText = fmtLink(cloud.tokenlab_configured);
    document.getElementById("c-tokenlab").className = "kv-v " + (cloud.tokenlab_configured ? "ok" : "");
    document.getElementById("c-nvidia").innerText = fmtLink(cloud.nvidia_configured);
    document.getElementById("c-nvidia").className = "kv-v " + (cloud.nvidia_configured ? "ok" : "");
    document.getElementById("c-do").innerText = fmtLink(cloud.digitalocean_configured);
    document.getElementById("c-do").className = "kv-v " + (cloud.digitalocean_configured ? "ok" : "");

    if (health) {
      document.getElementById("health-score").innerText = health.score;
      document.getElementById("health-grade").innerText = `GRADE ${health.grade}`;
      document.getElementById("health-status").innerText = (health.status || "healthy").toUpperCase();
      document.getElementById("health-bar").style.width = `${Math.max(0, Math.min(100, health.score))}%`;
      if (health.components) {
        document.getElementById("h-vram").innerText = `${health.components.vram_headroom}%`;
        document.getElementById("h-therm").innerText = `${health.components.thermal_headroom}%`;
      }
    }
  } catch (e) {}
}

async function loadWorkspaceFiles() {
  try {
    const res = await fetch("/api/workspace/files");
    const data = await res.json();
    workspaceFiles = data.files || [];
    renderWorkspaceFiles();
  } catch (e) {
    document.getElementById("workspace-file-list").innerHTML =
      `<div class="file-row" style="color:var(--err);">Workspace scan failed</div>`;
  }
}

function renderWorkspaceFiles() {
  const q = (document.getElementById("file-filter").value || "").toLowerCase().trim();
  const list = document.getElementById("workspace-file-list");
  const filtered = q ? workspaceFiles.filter((f) => f.path.toLowerCase().includes(q)) : workspaceFiles;
  if (!filtered.length) {
    list.innerHTML = `<div class="file-row" style="color:var(--muted);">No matching files</div>`;
    return;
  }
  list.innerHTML = filtered.slice(0, 100).map((f) => {
    const checked = selectedWorkspaceFiles.has(f.path);
    const safePath = escapeHtml(f.path);
    return `<label class="file-row ${checked ? "checked" : ""}">
      <input type="checkbox" ${checked ? "checked" : ""} onchange="toggleWorkspaceFile('${safePath.replace(/'/g, "\\'")}')" />
      <span class="fname" title="${safePath}">${safePath}</span>
      <span class="fsize">${f.size_kb}K</span>
    </label>`;
  }).join("");
  document.getElementById("selected-files-count").innerText = `${selectedWorkspaceFiles.size} STAGED`;
}

function toggleWorkspaceFile(path) {
  if (selectedWorkspaceFiles.has(path)) selectedWorkspaceFiles.delete(path);
  else selectedWorkspaceFiles.add(path);
  renderWorkspaceFiles();
}

/* ── FILE UPLOAD & DRAG-AND-DROP ─────────────────────────────────────── */
function handleFileUpload(ev) {
  addFilesFromList(ev.target.files);
  ev.target.value = "";
}

function handleImageUpload(ev) {
  const file = ev.target.files && ev.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    attachedImageBase64 = reader.result;
    attachedImageName = file.name;
    renderStagingTray();
  };
  reader.readAsDataURL(file);
  ev.target.value = "";
}

function addFilesFromList(fileList) {
  for (const file of Array.from(fileList || [])) {
    if (file.type && file.type.startsWith("image/")) {
      const r = new FileReader();
      r.onload = () => {
        attachedImageBase64 = r.result;
        attachedImageName = file.name;
        renderStagingTray();
      };
      r.readAsDataURL(file);
    } else {
      const r = new FileReader();
      r.onload = () => {
        uploadedFiles.push({ name: file.name, content: String(r.result || "").slice(0, 120000) });
        renderStagingTray();
      };
      r.readAsText(file);
    }
  }
}

function renderStagingTray() {
  const tray = document.getElementById("staging-tray");
  const chips = [];
  if (attachedImageBase64) {
    chips.push(`<span class="stage-chip">IMG: ${escapeHtml(attachedImageName || "image")} <button onclick="removeImage()">x</button></span>`);
  }
  uploadedFiles.forEach((f, idx) => {
    chips.push(`<span class="stage-chip">FILE: ${escapeHtml(f.name)} (${Math.max(1, Math.round(f.content.length / 1024))}KB) <button onclick="removeUploadedFile(${idx})">x</button></span>`);
  });
  tray.innerHTML = chips.join("");
  tray.classList.toggle("has-items", chips.length > 0);
}

function removeImage() {
  attachedImageBase64 = null;
  attachedImageName = null;
  renderStagingTray();
}
function removeUploadedFile(idx) {
  uploadedFiles.splice(idx, 1);
  renderStagingTray();
}
function clearAllAttachments() {
  uploadedFiles = [];
  attachedImageBase64 = null;
  attachedImageName = null;
  renderStagingTray();
}

const deckEl = document.getElementById("command-deck");
["dragenter", "dragover"].forEach((ev) => deckEl.addEventListener(ev, (e) => {
  e.preventDefault();
  deckEl.classList.add("drag-over");
}));
["dragleave", "drop"].forEach((ev) => deckEl.addEventListener(ev, (e) => {
  e.preventDefault();
  deckEl.classList.remove("drag-over");
}));
deckEl.addEventListener("drop", (e) => {
  if (e.dataTransfer && e.dataTransfer.files) addFilesFromList(e.dataTransfer.files);
});

/* ── MARKDOWN & TAPE RENDERING ───────────────────────────────────────── */
function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderMarkdown(md) {
  const blocks = [];
  let text = String(md || "").replace(/```([\w-]*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const id = blocks.length;
    blocks.push({ lang: lang || "TEXT", code: code.replace(/\n$/, "") });
    return `@@CODEBLOCK_${id}@@`;
  });
  text = escapeHtml(text);
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
  text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/^### (.+)$/gm, "<h4 style='margin:10px 0 4px; font-family:var(--font-mono); text-transform:uppercase; font-size:12px;'>$1</h4>");
  text = text.replace(/^## (.+)$/gm, "<h3 style='margin:12px 0 6px; font-size:14.5px;'>$1</h3>");
  text = text.replace(/\n/g, "<br/>");
  text = text.replace(/@@CODEBLOCK_(\d+)@@/g, (_, idx) => {
    const b = blocks[Number(idx)];
    const encoded = encodeURIComponent(b.code);
    return `<pre><div class="code-bar"><span>${escapeHtml(b.lang)}</span><button class="code-copy" onclick="copyCodeBlock(this, '${encoded}')">COPY</button></div><code>${escapeHtml(b.code)}</code></pre>`;
  });
  return text;
}

function copyCodeBlock(btn, encoded) {
  navigator.clipboard.writeText(decodeURIComponent(encoded));
  btn.innerText = "COPIED";
  setTimeout(() => (btn.innerText = "COPY"), 1200);
}

function utcStamp() {
  return new Date().toISOString().slice(11, 19) + " UTC";
}

function clearTape() {
  if (isGenerating) stopGeneration();
  chatHistory = [];
  seqCounter = 0;
  document.getElementById("chat-log").innerHTML = "";
  const empty = document.createElement("div");
  empty.className = "tape-empty";
  empty.id = "tape-empty";
  empty.innerHTML = `<div class="tape-empty-kicker">Tape Cleared</div><h2>Ready for Next Sequence</h2><p>Select a bus in Bay 01 and transmit.</p>`;
  document.getElementById("chat-log").appendChild(empty);
}

function quickPrompt(text) {
  document.getElementById("prompt-input").value = text;
  sendPrompt();
}

function setRunningState(running) {
  isGenerating = running;
  document.getElementById("btn-send").disabled = running;
  document.getElementById("btn-stop").style.display = running ? "inline-flex" : "none";
  document.getElementById("sys-led").classList.toggle("busy", running);
  document.getElementById("tape-status").innerText = running ? "TRANSMITTING // STREAM ACTIVE" : "READY // ZERO LOCAL VRAM";
  if (!running) {
    document.getElementById("scope-readout").innerText = "0.091 ms IDLE";
  }
}

function stopGeneration() {
  if (currentAbortController) currentAbortController.abort();
}

/* ── TRANSMIT / SSE STREAM ───────────────────────────────────────────── */
async function sendPrompt() {
  if (isGenerating) return;
  const input = document.getElementById("prompt-input");
  const text = input.value.trim();
  if (!text) return;

  const emptyEl = document.getElementById("tape-empty");
  if (emptyEl) emptyEl.remove();

  input.value = "";
  const chatLog = document.getElementById("chat-log");
  seqCounter += 1;
  const seqStr = String(seqCounter).padStart(3, "0");

  const selectedFiles = Array.from(selectedWorkspaceFiles);
  const filesToUpload = uploadedFiles.slice();
  const imgData = attachedImageBase64;
  const attachSummary = [
    ...selectedFiles.map((f) => `CTX:${f}`),
    ...filesToUpload.map((f) => `FILE:${f.name}`),
    ...(imgData ? [`IMG:${attachedImageName || "image"}`] : []),
  ];

  // Append user sequence block
  const uEntry = document.createElement("article");
  uEntry.className = "entry user";
  uEntry.innerHTML = `
    <div class="entry-head">
      <span><span class="entry-seq">SEQ ${seqStr} // TX</span> &middot; ${utcStamp()}</span>
      <span class="entry-badge">${escapeHtml(selectedTarget)}</span>
    </div>
    <div class="entry-body">${escapeHtml(text).replace(/\n/g, "<br/>")}</div>
    ${attachSummary.length ? `<div style="font-family:var(--font-mono); font-size:10px; color:var(--muted);">STAGED: ${escapeHtml(attachSummary.join(" | "))}</div>` : ""}
  `;
  chatLog.appendChild(uEntry);

  // Append assistant response block
  const aEntry = document.createElement("article");
  aEntry.className = "entry assistant";
  aEntry.innerHTML = `
    <div class="entry-head">
      <span><span class="entry-seq">SEQ ${seqStr} // RX</span> &middot; ${utcStamp()}</span>
      <span class="entry-badge live" data-role="meta">ROUTING...</span>
    </div>
    <details class="reasoning-panel" data-role="rbox">
      <summary>Reasoning Trace</summary>
      <div data-role="rcontent"></div>
    </details>
    <div class="entry-body" data-role="content" style="font-family:var(--font-mono); color:var(--muted);">Awaiting stream...</div>
  `;
  chatLog.appendChild(aEntry);
  chatLog.scrollTop = chatLog.scrollHeight;

  const metaEl = aEntry.querySelector('[data-role="meta"]');
  const contentEl = aEntry.querySelector('[data-role="content"]');
  const rBox = aEntry.querySelector('[data-role="rbox"]');
  const rContent = aEntry.querySelector('[data-role="rcontent"]');

  const payload = {
    prompt: text,
    target: selectedTarget,
    history: chatHistory.slice(-8),
    image_base64: imgData,
    workspace_files: selectedFiles,
    uploaded_files: filesToUpload,
  };
  clearAllAttachments();

  setRunningState(true);
  currentAbortController = new AbortController();
  const startedAt = performance.now();
  scopeTokens = 0;
  let accumulatedContent = "";
  let accumulatedReasoning = "";
  let timer = setInterval(() => {
    const sec = ((performance.now() - startedAt) / 1000).toFixed(1);
    document.getElementById("scope-readout").innerText = `RX ${sec}s // ${scopeTokens} CHUNKS`;
  }, 150);

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: currentAbortController.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop();

      for (const chunk of chunks) {
        if (!chunk.trim()) continue;
        let evType = "delta";
        let evData = "";
        for (const line of chunk.split("\n")) {
          if (line.startsWith("event:")) evType = line.slice(6).trim();
          else if (line.startsWith("data:")) evData = line.slice(5).trim();
        }
        if (!evData) continue;
        const parsed = JSON.parse(evData);

        if (evType === "start") {
          metaEl.innerText = `${parsed.model_used || selectedTarget} [${parsed.provider || "LIVE"}]`;
          contentEl.style.fontFamily = "";
          contentEl.style.color = "";
          contentEl.innerHTML = "";
        } else if (evType === "reasoning") {
          scopeEnergy = 0.7;
          scopeTokens += 1;
          accumulatedReasoning += parsed.delta || "";
          rBox.style.display = "block";
          rContent.innerText = accumulatedReasoning;
        } else if (evType === "delta") {
          scopeEnergy = 0.85;
          scopeTokens += 1;
          contentEl.style.fontFamily = "";
          contentEl.style.color = "";
          accumulatedContent += parsed.delta || "";
          contentEl.innerHTML = renderMarkdown(accumulatedContent);
        } else if (evType === "done") {
          const latMs = Math.round(parsed.latency_ms || (performance.now() - startedAt));
          metaEl.className = "entry-badge ok";
          metaEl.innerText = `${parsed.model_used || selectedTarget} // ${latMs} ms`;
          document.getElementById("m-lat").innerText = `${latMs} ms`;
          contentEl.style.fontFamily = "";
          contentEl.style.color = "";
          contentEl.innerHTML = renderMarkdown(accumulatedContent || parsed.fallback_content || "(Empty response)");
        } else if (evType === "error") {
          aEntry.classList.add("error");
          metaEl.className = "entry-badge err";
          metaEl.innerText = "ERROR";
          contentEl.innerHTML = `<div style="color:var(--err); font-family:var(--font-mono);">${escapeHtml(parsed.error)}</div>`;
        }
      }
      chatLog.scrollTop = chatLog.scrollHeight;
    }

    chatHistory.push({ role: "user", content: text });
    chatHistory.push({ role: "assistant", content: accumulatedContent });
  } catch (err) {
    if (err.name === "AbortError") {
      metaEl.className = "entry-badge";
      metaEl.innerText += " // STOPPED";
    } else {
      aEntry.classList.add("error");
      metaEl.className = "entry-badge err";
      metaEl.innerText = "LINK FAILED";
      contentEl.innerHTML = `<div style="color:var(--err); font-family:var(--font-mono);">${escapeHtml(err.message)}</div>`;
    }
  } finally {
    clearInterval(timer);
    setRunningState(false);
    currentAbortController = null;
    chatLog.scrollTop = chatLog.scrollHeight;
  }
}

/* ── EXPORT IDE BUNDLE ───────────────────────────────────────────────── */
async function openExportBundle() {
  const modal = document.getElementById("export-modal");
  const ta = document.getElementById("export-textarea");
  ta.value = "Packing workspace bundle...";
  modal.classList.add("open");
  try {
    const res = await fetch("/api/workspace/copilot-bundle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ files: Array.from(selectedWorkspaceFiles) }),
    });
    const data = await res.json();
    ta.value = data.bundle || JSON.stringify(data, null, 2);
  } catch (e) {
    ta.value = `Export failed: ${e.message}`;
  }
}
function closeExportBundle() {
  document.getElementById("export-modal").classList.remove("open");
}
function copyExportBundle() {
  navigator.clipboard.writeText(document.getElementById("export-textarea").value);
}

/* ── KEYBOARD & CLOCK ────────────────────────────────────────────────── */
document.getElementById("prompt-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendPrompt();
  }
});

setInterval(() => {
  document.getElementById("insp-clock").innerText = utcStamp();
}, 1000);

// Boot sequence
renderPatchbay();
loadStatus();
loadWorkspaceFiles();
setInterval(loadStatus, 5000);
</script>
</body>
</html>
"""

"""Jupiter Studio UI — chat-first workstation.

Design goals:
  * The conversation is the product: one readable column, real markdown, copy / retry / edit.
  * Model picker (Ctrl+K) shows which providers are actually reachable and why not, so
    nothing silently fails.
  * Saved conversations in a left rail (localStorage), context + hardware in a right drawer.
"""

STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Jupiter Studio</title>
<link rel="icon" type="image/png" href="/assets/jupiter_studio_icon.png" />
<style>
  :root {
    --bg: #0e0f11; --rail: #131417; --surface: #17191c; --raised: #1e2024; --hover: #25282d;
    --line: #2a2d32; --line-2: #3a3e45;
    --text: #e8e6e1; --text-2: #a9a59c; --muted: #6f6c66;
    --accent: #e8a33d; --accent-ink: #1a1306; --accent-soft: rgba(232,163,61,0.12);
    --ok: #5fbf8f; --bad: #e0685d; --code: #0a0b0c;
    --sans: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
    --serif: "Iowan Old Style", "Charter", "Georgia", serif;
    --mono: "JetBrains Mono", "Cascadia Code", "Consolas", ui-monospace, monospace;
  }
  html[data-theme="light"] {
    --bg: #f6f4ef; --rail: #efece5; --surface: #ffffff; --raised: #f3f0ea; --hover: #e9e5dd;
    --line: #e0dbd1; --line-2: #cdc6b9;
    --text: #1d1c19; --text-2: #55524b; --muted: #8b877e;
    --accent: #b8650f; --accent-ink: #ffffff; --accent-soft: rgba(184,101,15,0.10);
    --ok: #2f8a5c; --bad: #c0392b; --code: #1b1c1e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; }
  body { background: var(--bg); color: var(--text); font: 14px/1.55 var(--sans); overflow: hidden; -webkit-font-smoothing: antialiased; }
  button { font: inherit; color: inherit; background: none; border: none; cursor: pointer; }
  ::-webkit-scrollbar { width: 8px; height: 8px; }
  ::-webkit-scrollbar-thumb { background: var(--line-2); border-radius: 8px; }

  .app { display: grid; grid-template-columns: 248px 1fr 0px; height: 100vh; transition: grid-template-columns .18s ease; }
  .app.drawer-open { grid-template-columns: 248px 1fr 300px; }
  .app.rail-closed { grid-template-columns: 0px 1fr 0px; }
  .app.rail-closed.drawer-open { grid-template-columns: 0px 1fr 300px; }

  /* Left rail: conversations */
  .rail { background: var(--rail); border-right: 1px solid var(--line); display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
  .rail-top { padding: 14px 12px 10px; display: flex; align-items: center; gap: 10px; }
  .logo { width: 28px; height: 28px; border-radius: 7px; overflow: hidden; flex-shrink: 0; background: #000; }
  .logo img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .wordmark { font-weight: 650; letter-spacing: -0.01em; }
  .wordmark small { display: block; font: 500 10.5px var(--mono); color: var(--muted); letter-spacing: .04em; }
  .new-chat { margin: 4px 12px 10px; padding: 9px 12px; border: 1px solid var(--line-2); border-radius: 9px; text-align: left; display: flex; justify-content: space-between; align-items: center; }
  .new-chat:hover { background: var(--hover); }
  .kbd { font: 500 10.5px var(--mono); color: var(--muted); border: 1px solid var(--line-2); border-radius: 4px; padding: 0 5px; }
  .conv-list { flex: 1; overflow-y: auto; padding: 0 8px 12px; }
  .conv-group { font: 600 10.5px var(--mono); color: var(--muted); letter-spacing: .06em; text-transform: uppercase; padding: 12px 8px 4px; }
  .conv { display: flex; align-items: center; gap: 6px; padding: 7px 8px; border-radius: 7px; color: var(--text-2); cursor: pointer; }
  .conv:hover { background: var(--hover); color: var(--text); }
  .conv.active { background: var(--raised); color: var(--text); }
  .conv-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
  .conv-del { opacity: 0; color: var(--muted); padding: 0 4px; }
  .conv:hover .conv-del { opacity: 1; }
  .conv-del:hover { color: var(--bad); }
  .rail-foot { border-top: 1px solid var(--line); padding: 10px 12px; font: 11px var(--mono); color: var(--muted); display: flex; justify-content: space-between; }

  /* Main column */
  .main { display: flex; flex-direction: column; min-width: 0; position: relative; }
  .topbar { height: 52px; display: flex; align-items: center; gap: 8px; padding: 0 14px; border-bottom: 1px solid var(--line); }
  .icon-btn { width: 32px; height: 32px; border-radius: 8px; display: grid; place-items: center; color: var(--text-2); }
  .icon-btn:hover { background: var(--hover); color: var(--text); }
  .icon-btn.on { color: var(--accent); }
  .model-btn { display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 9px; border: 1px solid transparent; max-width: 420px; }
  .model-btn:hover { background: var(--hover); border-color: var(--line); }
  .model-btn .name { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .model-btn .prov { font: 11px var(--mono); color: var(--muted); }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ok); flex-shrink: 0; }
  .dot.bad { background: var(--bad); }
  .dot.busy { background: var(--accent); animation: pulse 1s infinite; }
  @keyframes pulse { 50% { opacity: .3; } }
  .spacer { flex: 1; }
  .vram-pill { font: 11px var(--mono); color: var(--text-2); border: 1px solid var(--line); border-radius: 999px; padding: 3px 10px; }

  .scroller { flex: 1; overflow-y: auto; }
  .thread { max-width: 780px; margin: 0 auto; padding: 28px 24px 40px; }

  .welcome { padding-top: 9vh; }
  .welcome h1 { font: 500 34px/1.15 var(--serif); letter-spacing: -0.015em; margin-bottom: 10px; }
  .welcome p { color: var(--text-2); max-width: 560px; margin-bottom: 26px; }
  .starters { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .starter { text-align: left; padding: 14px; border: 1px solid var(--line); border-radius: 12px; background: var(--surface); }
  .starter:hover { border-color: var(--line-2); background: var(--raised); }
  .starter b { display: block; font-weight: 600; margin-bottom: 3px; }
  .starter span { color: var(--muted); font-size: 12.5px; }

  .msg { margin-bottom: 26px; }
  .msg.user { display: flex; justify-content: flex-end; }
  .bubble { background: var(--raised); border: 1px solid var(--line); border-radius: 14px 14px 4px 14px; padding: 10px 14px; max-width: 85%; white-space: pre-wrap; word-break: break-word; }
  .attach-line { font: 11px var(--mono); color: var(--muted); margin-top: 6px; text-align: right; }
  .msg.ai .who { display: flex; align-items: center; gap: 8px; font: 11.5px var(--mono); color: var(--muted); margin-bottom: 6px; }
  .msg.ai .who b { color: var(--text-2); font-weight: 600; }
  .md { font-size: 14.5px; line-height: 1.7; word-break: break-word; }
  .md p { margin: 0 0 12px; }
  .md p:last-child { margin-bottom: 0; }
  .md h1, .md h2, .md h3, .md h4 { font-weight: 650; line-height: 1.3; margin: 20px 0 8px; letter-spacing: -0.01em; }
  .md h1 { font-size: 20px; } .md h2 { font-size: 17.5px; } .md h3 { font-size: 15.5px; } .md h4 { font-size: 14.5px; }
  .md ul, .md ol { margin: 0 0 12px 22px; }
  .md li { margin: 3px 0; }
  .md blockquote { border-left: 3px solid var(--accent); padding: 2px 12px; color: var(--text-2); margin: 0 0 12px; }
  .md a { color: var(--accent); }
  .md hr { border: none; border-top: 1px solid var(--line); margin: 16px 0; }
  .md :not(pre) > code { font: 12.5px var(--mono); background: var(--raised); border: 1px solid var(--line); border-radius: 5px; padding: 1px 5px; }
  .md table { border-collapse: collapse; margin: 0 0 12px; font-size: 13px; display: block; overflow-x: auto; }
  .md th, .md td { border: 1px solid var(--line); padding: 6px 10px; text-align: left; }
  .md th { background: var(--raised); font-weight: 600; }
  .codeblock { margin: 0 0 14px; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: var(--code); }
  .codebar { display: flex; justify-content: space-between; align-items: center; padding: 6px 12px; font: 11px var(--mono); color: #8d8a83; border-bottom: 1px solid #222; }
  .codebar button { color: #b9b5ad; font: 11px var(--mono); padding: 2px 6px; border-radius: 5px; }
  .codebar button:hover { background: #222; color: #fff; }
  .codeblock pre { margin: 0; padding: 12px 14px; overflow-x: auto; font: 12.8px/1.55 var(--mono); color: #e6e3dc; }
  .think { border: 1px solid var(--line); border-radius: 10px; margin-bottom: 12px; background: var(--surface); }
  .think summary { cursor: pointer; padding: 7px 12px; font: 11.5px var(--mono); color: var(--muted); list-style: none; }
  .think summary::before { content: "+ "; }
  .think[open] summary::before { content: "- "; }
  .think div { padding: 0 12px 10px; font: 12.5px/1.6 var(--mono); color: var(--text-2); white-space: pre-wrap; max-height: 280px; overflow-y: auto; }
  .caret::after { content: ""; display: inline-block; width: 8px; height: 15px; background: var(--accent); margin-left: 2px; vertical-align: -2px; animation: pulse .9s infinite; }
  .waiting { color: var(--muted); font: 12.5px var(--mono); }
  .err-box { border: 1px solid var(--bad); background: rgba(224,104,93,.08); color: var(--text); border-radius: 10px; padding: 10px 12px; font-size: 13.5px; }
  .err-box b { color: var(--bad); display: block; margin-bottom: 2px; font: 600 11.5px var(--mono); text-transform: uppercase; letter-spacing: .04em; }
  .msg-tools { display: flex; gap: 2px; margin-top: 8px; opacity: 0; transition: opacity .12s; }
  .msg:hover .msg-tools, .msg:last-child .msg-tools { opacity: 1; }
  .msg-tools button { font: 11.5px var(--mono); color: var(--muted); padding: 3px 8px; border-radius: 6px; }
  .msg-tools button:hover { background: var(--hover); color: var(--text); }
  .stat { font: 11px var(--mono); color: var(--muted); margin-left: auto; align-self: center; }

  /* Composer */
  .composer-wrap { padding: 0 24px 18px; }
  .composer { max-width: 780px; margin: 0 auto; background: var(--surface); border: 1px solid var(--line-2); border-radius: 16px; padding: 10px 10px 8px 14px; transition: border-color .12s; }
  .composer:focus-within { border-color: var(--accent); }
  .composer.drag { border-style: dashed; border-color: var(--accent); background: var(--accent-soft); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
  .chips:empty { display: none; }
  .chip { display: inline-flex; align-items: center; gap: 6px; font: 11.5px var(--mono); background: var(--raised); border: 1px solid var(--line); border-radius: 7px; padding: 3px 4px 3px 8px; }
  .chip button { color: var(--muted); padding: 0 4px; }
  .chip button:hover { color: var(--bad); }
  .chip img { width: 22px; height: 22px; object-fit: cover; border-radius: 4px; }
  #prompt { width: 100%; resize: none; border: none; outline: none; background: transparent; color: var(--text); font: 14.5px/1.55 var(--sans); max-height: 240px; min-height: 24px; }
  #prompt::placeholder { color: var(--muted); }
  .composer-row { display: flex; align-items: center; gap: 4px; margin-top: 6px; }
  .tool { font: 12px var(--sans); color: var(--text-2); padding: 5px 9px; border-radius: 8px; }
  .tool:hover { background: var(--hover); color: var(--text); }
  .send { width: 34px; height: 34px; border-radius: 10px; background: var(--accent); color: var(--accent-ink); display: grid; place-items: center; font-weight: 700; }
  .send:disabled { opacity: .35; cursor: not-allowed; }
  .send.stop { background: var(--text); color: var(--bg); }
  .hint { max-width: 780px; margin: 6px auto 0; font: 11px var(--mono); color: var(--muted); text-align: center; }

  /* Right drawer */
  .drawer { background: var(--rail); border-left: 1px solid var(--line); overflow: hidden; display: flex; flex-direction: column; min-width: 0; }
  .drawer-head { height: 52px; display: flex; align-items: center; padding: 0 14px; border-bottom: 1px solid var(--line); font-weight: 600; }
  .drawer-body { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 18px; }
  .sec-title { font: 600 10.5px var(--mono); color: var(--muted); letter-spacing: .06em; text-transform: uppercase; margin-bottom: 8px; display: flex; justify-content: space-between; }
  .kv { display: flex; justify-content: space-between; gap: 10px; font-size: 12.5px; padding: 5px 0; border-bottom: 1px solid var(--line); }
  .kv span:first-child { color: var(--muted); }
  .kv span:last-child { text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .health { display: flex; align-items: baseline; gap: 10px; }
  .health b { font: 600 30px var(--serif); }
  .bar { height: 5px; background: var(--raised); border-radius: 5px; overflow: hidden; margin-top: 6px; }
  .bar i { display: block; height: 100%; background: var(--ok); }
  .search { width: 100%; padding: 7px 10px; border-radius: 8px; border: 1px solid var(--line); background: var(--surface); color: var(--text); font: 12.5px var(--sans); outline: none; margin-bottom: 6px; }
  .search:focus { border-color: var(--accent); }
  .files { max-height: 260px; overflow-y: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
  .file { display: flex; gap: 8px; align-items: center; padding: 5px 8px; font: 11.5px var(--mono); cursor: pointer; border-bottom: 1px solid var(--line); }
  .file:last-child { border-bottom: none; }
  .file:hover { background: var(--hover); }
  .file input { accent-color: var(--accent); }
  .file .p { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .file .s { color: var(--muted); }

  /* Model palette */
  .overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: none; align-items: flex-start; justify-content: center; padding-top: 12vh; z-index: 50; }
  .overlay.open { display: flex; }
  .palette { width: min(620px, 92vw); max-height: 70vh; background: var(--surface); border: 1px solid var(--line-2); border-radius: 14px; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.35); }
  .palette input { border: none; border-bottom: 1px solid var(--line); background: transparent; color: var(--text); padding: 14px 16px; font: 15px var(--sans); outline: none; }
  .pal-list { overflow-y: auto; padding: 6px; }
  .pal-group { font: 600 10.5px var(--mono); color: var(--muted); letter-spacing: .06em; text-transform: uppercase; padding: 10px 10px 4px; display: flex; justify-content: space-between; }
  .pal-group em { font-style: normal; text-transform: none; letter-spacing: 0; color: var(--bad); font-weight: 500; }
  .pal-item { display: flex; align-items: center; gap: 10px; width: 100%; text-align: left; padding: 8px 10px; border-radius: 8px; }
  .pal-item:hover, .pal-item.kb { background: var(--hover); }
  .pal-item.sel { background: var(--accent-soft); }
  .pal-item.off { opacity: .45; }
  .pal-item .n { flex: 1; font-weight: 550; }
  .pal-item .t { font: 11px var(--mono); color: var(--muted); }
  .pal-foot { border-top: 1px solid var(--line); padding: 8px 14px; font: 11px var(--mono); color: var(--muted); display: flex; justify-content: space-between; }

  .toast { position: fixed; bottom: 22px; left: 50%; transform: translateX(-50%); background: var(--text); color: var(--bg); padding: 8px 14px; border-radius: 9px; font-size: 13px; opacity: 0; pointer-events: none; transition: opacity .15s; z-index: 60; }
  .toast.show { opacity: 1; }

  @media (max-width: 900px) {
    .app, .app.drawer-open { grid-template-columns: 0px 1fr 0px; }
    .starters { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<div class="app" id="app">

  <aside class="rail">
    <div class="rail-top">
      <div class="logo"><img src="/assets/jupiter_studio_icon.png" alt="" /></div>
      <div class="wordmark">Jupiter Studio<small>MEMORYOS RC1</small></div>
    </div>
    <button class="new-chat" onclick="newChat()"><span>New chat</span><span class="kbd">Ctrl+Shift+O</span></button>
    <div class="conv-list" id="conv-list"></div>
    <div class="rail-foot"><span id="foot-gpu">--</span><span id="foot-vram">0 MB</span></div>
  </aside>

  <main class="main">
    <div class="topbar">
      <button class="icon-btn" title="Toggle sidebar" onclick="toggleRail()">&#9776;</button>
      <button class="model-btn" onclick="openPalette()" title="Change model (Ctrl+K)">
        <span class="dot" id="model-dot"></span>
        <span class="name" id="model-name">Auto</span>
        <span class="prov" id="model-prov">d3 router</span>
        <span class="kbd">Ctrl+K</span>
      </button>
      <div class="spacer"></div>
      <span class="vram-pill" id="vram-pill">Local VRAM 0 MB</span>
      <button class="icon-btn" title="Light / dark" onclick="toggleTheme()">&#9680;</button>
      <button class="icon-btn" id="drawer-btn" title="Context & hardware" onclick="toggleDrawer()">&#9638;</button>
    </div>

    <div class="scroller" id="scroller">
      <div class="thread" id="thread"></div>
    </div>

    <div class="composer-wrap">
      <div class="composer" id="composer">
        <div class="chips" id="chips"></div>
        <textarea id="prompt" rows="1" placeholder="Message Jupiter Studio..."></textarea>
        <div class="composer-row">
          <input type="file" id="file-in" multiple hidden />
          <button class="tool" onclick="document.getElementById('file-in').click()">+ Attach</button>
          <button class="tool" onclick="toggleDrawer(true)" id="ctx-tool">Repo files</button>
          <div class="spacer"></div>
          <button class="send" id="send" onclick="onSendClick()" title="Send (Enter)">&uarr;</button>
        </div>
      </div>
      <div class="hint" id="hint">Enter to send &middot; Shift+Enter for a new line &middot; drop files or images anywhere</div>
    </div>
  </main>

  <aside class="drawer">
    <div class="drawer-head">Context &amp; hardware</div>
    <div class="drawer-body">
      <section>
        <div class="sec-title"><span>Repo files</span><span id="staged">0 selected</span></div>
        <input class="search" id="file-q" placeholder="Filter files..." oninput="renderFiles()" />
        <div class="files" id="files"><div class="file">Scanning...</div></div>
      </section>
      <section>
        <div class="sec-title"><span>Workstation health</span><span id="h-status">--</span></div>
        <div class="health"><b id="h-score">--</b><span id="h-grade" style="color:var(--muted)"></span></div>
        <div class="bar"><i id="h-bar" style="width:0%"></i></div>
      </section>
      <section>
        <div class="sec-title"><span>Hardware</span></div>
        <div class="kv"><span>GPU</span><span id="hw-name">--</span></div>
        <div class="kv"><span>VRAM</span><span id="hw-vram">--</span></div>
        <div class="kv"><span>Temp / load</span><span id="hw-temp">--</span></div>
        <div class="kv"><span>CPU gate</span><span id="hw-gate">0.091 ms</span></div>
      </section>
      <section>
        <div class="sec-title"><span>Providers</span><button class="kbd" onclick="loadModels(true)">refresh</button></div>
        <div id="prov-list"></div>
      </section>
    </div>
  </aside>
</div>

<div class="overlay" id="overlay" onclick="if(event.target===this)closePalette()">
  <div class="palette">
    <input id="pal-q" placeholder="Search models..." oninput="renderPalette()" />
    <div class="pal-list" id="pal-list"></div>
    <div class="pal-foot"><span>&uarr;&darr; navigate &middot; Enter select &middot; Esc close</span><span id="pal-count"></span></div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
/* ---------- Model catalogue ---------- */
const CATALOG = [
  { key: "auto", group: "Automatic", items: [ { v: "auto:d3", n: "Auto", t: "d3 picks the best model" } ] },
  { key: "cloud", group: "AMD Token Lab", items: [
    { v: "cloud:Gemma-4-31B-IT", n: "Gemma 4 31B", t: "vision + general" },
    { v: "cloud:Qwen3.8-27B", n: "Qwen 3.8 27B", t: "code" },
    { v: "cloud:DeepSeek-V4.1-Flash", n: "DeepSeek V4.1 Flash", t: "1M context, reasoning" },
    { v: "cloud:MiniCPM5-2B", n: "MiniCPM5 2B", t: "fast, short answers" } ] },
  { key: "nv", group: "NVIDIA NIM", items: [
    { v: "nv:qwen/qwen2.5-coder-32b-instruct", n: "Qwen 2.5 Coder 32B", t: "code" },
    { v: "nv:meta/llama-3.3-70b-instruct", n: "Llama 3.3 70B", t: "general" },
    { v: "nv:qwen/qwen2.5-7b-instruct", n: "Qwen 2.5 7B", t: "fast" } ] },
  { key: "do", group: "DigitalOcean MI300X", items: [
    { v: "do:Qwen/Qwen2.5-Coder-32B-Instruct", n: "Qwen 2.5 Coder 32B", t: "code" },
    { v: "do:meta-llama/Llama-3.3-70B-Instruct", n: "Llama 3.3 70B", t: "general" } ] },
  { key: "vllm", group: "DGX Spark - vLLM", items: [
    { v: "vllm:Qwen/Qwen3.8-Flash-Next", n: "Qwen 3.8 Flash Next", t: ":8000" },
    { v: "vllm:deepseek-ai/DeepSeek-V4.1-Flash", n: "DeepSeek V4.1 Flash", t: ":8000" } ] },
  { key: "flare", group: "DGX Spark - Flare", items: [
    { v: "flare:Qwen3.8-Flash-Next", n: "Qwen 3.8 Flash Next", t: ":8080" },
    { v: "flare:DeepSeek-V4.1-Flash", n: "DeepSeek V4.1 Flash", t: ":8080" } ] },
  { key: "ollama", group: "Local - Ollama", items: [] },
];
const OLLAMA_DEFAULTS = ["raon-1-nano", "qwen2.5-coder:1.5b", "qwen2.5-coder:7b", "deepseek-r1:7b", "deepseek-r1:8b"];

let providers = {};
let state = loadState();
let busy = false, abortCtl = null;
let attachments = [];       // {kind:'file'|'image', name, content}
let workspaceFiles = [], selectedFiles = new Set();
let palIndex = 0, palFlat = [];

function loadState() {
  try {
    const s = JSON.parse(localStorage.getItem("jupiter.v2") || "{}");
    return { convs: s.convs || [], activeId: s.activeId || null, model: s.model || "auto:d3", theme: s.theme || "dark", drawer: !!s.drawer };
  } catch { return { convs: [], activeId: null, model: "auto:d3", theme: "dark", drawer: false }; }
}
function save() {
  const trimmed = state.convs.slice(0, 60);
  localStorage.setItem("jupiter.v2", JSON.stringify({ ...state, convs: trimmed }));
}
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
function toast(msg) { const t = $("toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 1800); }

/* ---------- Conversations ---------- */
function activeConv() { return state.convs.find((c) => c.id === state.activeId) || null; }
function newChat() {
  if (busy) stop();
  state.activeId = null; save(); renderConvs(); renderThread(); $("prompt").focus();
}
function ensureConv(firstPrompt) {
  let c = activeConv();
  if (!c) {
    c = { id: "c" + Date.now(), title: firstPrompt.slice(0, 60), created: Date.now(), messages: [] };
    state.convs.unshift(c); state.activeId = c.id;
  }
  return c;
}
function openConv(id) { if (busy) stop(); state.activeId = id; save(); renderConvs(); renderThread(); }
function deleteConv(id, ev) {
  ev.stopPropagation();
  state.convs = state.convs.filter((c) => c.id !== id);
  if (state.activeId === id) state.activeId = null;
  save(); renderConvs(); renderThread();
}
function renderConvs() {
  const now = Date.now(), day = 86400000;
  const buckets = { Today: [], "Previous 7 days": [], Older: [] };
  state.convs.forEach((c) => {
    const age = now - c.created;
    (age < day ? buckets.Today : age < 7 * day ? buckets["Previous 7 days"] : buckets.Older).push(c);
  });
  let html = "";
  for (const [label, list] of Object.entries(buckets)) {
    if (!list.length) continue;
    html += `<div class="conv-group">${label}</div>`;
    html += list.map((c) => `<div class="conv ${c.id === state.activeId ? "active" : ""}" onclick="openConv('${c.id}')">
      <span class="conv-title">${esc(c.title || "Untitled")}</span>
      <button class="conv-del" title="Delete" onclick="deleteConv('${c.id}', event)">&times;</button></div>`).join("");
  }
  $("conv-list").innerHTML = html || `<div class="conv-group">No chats yet</div>`;
}

/* ---------- Markdown ---------- */
function inline(s) {
  return s
    .replace(/`([^`]+)`/g, (_, c) => `<code>${c}</code>`)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}
function renderMarkdown(src, streaming) {
  const codes = [];
  let text = String(src || "");
  // Close an unfinished fence while streaming so code renders live.
  if (streaming && (text.match(/```/g) || []).length % 2 === 1) text += "\n```";
  text = text.replace(/```([\w+#.-]*)[^\n]*\n([\s\S]*?)```/g, (_, lang, code) => {
    codes.push({ lang: lang || "text", code: code.replace(/\n$/, "") });
    return `\u0000${codes.length - 1}\u0000`;
  });
  const lines = esc(text).split("\n");
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const ln = lines[i];
    const codeMatch = ln.match(/^\u0000(\d+)\u0000$/);
    if (codeMatch) {
      const b = codes[+codeMatch[1]];
      out.push(`<div class="codeblock"><div class="codebar"><span>${esc(b.lang)}</span><button onclick="copyCode(this)">Copy</button></div><pre><code>${esc(b.code)}</code></pre></div>`);
      i++; continue;
    }
    if (/^#{1,4} /.test(ln)) { const lvl = ln.match(/^#+/)[0].length; out.push(`<h${lvl}>${inline(ln.slice(lvl + 1))}</h${lvl}>`); i++; continue; }
    if (/^(-{3,}|\*{3,})$/.test(ln.trim())) { out.push("<hr/>"); i++; continue; }
    if (/^&gt; ?/.test(ln)) {
      const q = []; while (i < lines.length && /^&gt; ?/.test(lines[i])) q.push(lines[i++].replace(/^&gt; ?/, ""));
      out.push(`<blockquote>${inline(q.join("<br/>"))}</blockquote>`); continue;
    }
    if (/^\s*\|.*\|\s*$/.test(ln) && i + 1 < lines.length && /^\s*\|?\s*:?-{2,}/.test(lines[i + 1])) {
      const row = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => inline(c.trim()));
      const head = row(ln); i += 2; const body = [];
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) body.push(row(lines[i++]));
      out.push(`<table><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${body.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`);
      continue;
    }
    if (/^\s*([-*+]|\d+[.)]) /.test(ln)) {
      const ordered = /^\s*\d+[.)] /.test(ln); const items = [];
      while (i < lines.length && /^\s*([-*+]|\d+[.)]) /.test(lines[i])) items.push(lines[i++].replace(/^\s*([-*+]|\d+[.)]) /, ""));
      out.push(`<${ordered ? "ol" : "ul"}>${items.map((it) => `<li>${inline(it)}</li>`).join("")}</${ordered ? "ol" : "ul"}>`); continue;
    }
    if (!ln.trim()) { i++; continue; }
    const para = []; 
    while (i < lines.length && lines[i].trim() && !/^(#{1,4} |\s*([-*+]|\d+[.)]) |&gt;|\u0000)/.test(lines[i]) && !/^\s*\|.*\|\s*$/.test(lines[i])) para.push(lines[i++]);
    if (!para.length) { para.push(lines[i++]); }
    out.push(`<p>${inline(para.join("<br/>"))}</p>`);
  }
  return out.join("");
}
function copyCode(btn) {
  navigator.clipboard.writeText(btn.closest(".codeblock").querySelector("code").innerText);
  btn.textContent = "Copied"; setTimeout(() => (btn.textContent = "Copy"), 1200);
}

/* ---------- Thread rendering ---------- */
function labelFor(v) {
  for (const g of CATALOG) for (const it of g.items) if (it.v === v) return { n: it.n, g: g.group };
  const [p, ...rest] = v.split(":"); return { n: rest.join(":") || v, g: p };
}
function renderThread() {
  const c = activeConv(), th = $("thread");
  if (!c || !c.messages.length) {
    th.innerHTML = `<div class="welcome">
      <h1>What are we building?</h1>
      <p>Chat with cloud models on AMD Instinct, NVIDIA NIM or your own machine. Attach files or pick repo files for context. Your local GPU stays free.</p>
      <div class="starters">
        <button class="starter" onclick="starter('Review the selected repo files for bugs and security problems. Be specific and show fixes.')"><b>Review my code</b><span>Pick files in Repo files first</span></button>
        <button class="starter" onclick="starter('Explain, step by step, how MemoryOS keeps local VRAM at 0 MB while still running 31B models.')"><b>Explain the architecture</b><span>How zero-VRAM routing works</span></button>
        <button class="starter" onclick="starter('Write focused unit tests for the attached file using unittest.')"><b>Write tests</b><span>For an attached or selected file</span></button>
        <button class="starter" onclick="starter('I get this error. What is causing it and how do I fix it?\n\n')"><b>Debug an error</b><span>Paste a traceback or log</span></button>
      </div></div>`;
    return;
  }
  th.innerHTML = c.messages.map((m, idx) => messageHtml(m, idx, idx === c.messages.length - 1)).join("");
  scrollDown(true);
}
function messageHtml(m, idx, isLast) {
  if (m.role === "user") {
    const att = (m.attach || []).length ? `<div class="attach-line">${esc(m.attach.join(" · "))}</div>` : "";
    return `<div class="msg user" data-i="${idx}"><div><div class="bubble">${esc(m.content)}</div>${att}
      <div class="msg-tools" style="justify-content:flex-end"><button onclick="editMsg(${idx})">Edit</button><button onclick="copyMsg(${idx})">Copy</button></div></div></div>`;
  }
  const lbl = labelFor(m.model || state.model);
  const body = m.error
    ? `<div class="err-box"><b>Request failed</b>${esc(m.error)}</div>`
    : (m.content ? renderMarkdown(m.content, m.streaming) : `<span class="waiting">${m.streaming ? "Thinking..." : "(empty response)"}</span>`);
  const think = m.reasoning ? `<details class="think" ${m.streaming && !m.content ? "open" : ""}><summary>Reasoning (${m.reasoning.length.toLocaleString()} chars)</summary><div>${esc(m.reasoning)}</div></details>` : "";
  const stat = m.stats ? `<span class="stat">${esc(m.stats)}</span>` : "";
  const tools = m.streaming ? "" : `<div class="msg-tools"><button onclick="copyMsg(${idx})">Copy</button>${isLast ? `<button onclick="retry()">Retry</button><button onclick="openPalette(true)">Retry with...</button>` : ""}${stat}</div>`;
  return `<div class="msg ai" data-i="${idx}"><div class="who"><span class="dot ${m.streaming ? "busy" : m.error ? "bad" : ""}"></span><b>${esc(lbl.n)}</b><span>${esc(m.provider || lbl.g)}</span></div>
    ${think}<div class="md ${m.streaming && m.content ? "caret" : ""}">${body}</div>${tools}</div>`;
}
function updateLast() {
  const c = activeConv(); if (!c) return;
  const idx = c.messages.length - 1;
  const el = document.querySelector(`.msg[data-i="${idx}"]`);
  const html = messageHtml(c.messages[idx], idx, true);
  if (el) el.outerHTML = html; else renderThread();
  scrollDown();
}
function scrollDown(force) {
  const s = $("scroller");
  if (force || s.scrollHeight - s.scrollTop - s.clientHeight < 160) s.scrollTop = s.scrollHeight;
}
function copyMsg(idx) { navigator.clipboard.writeText(activeConv().messages[idx].content || ""); toast("Copied"); }
function editMsg(idx) {
  if (busy) return;
  const c = activeConv(); const m = c.messages[idx];
  $("prompt").value = m.content; autosize();
  c.messages = c.messages.slice(0, idx); save(); renderThread(); $("prompt").focus();
}
function starter(text) { $("prompt").value = text; autosize(); $("prompt").focus(); if (!text.endsWith("\n\n")) send(); }

/* ---------- Sending ---------- */
function onSendClick() { busy ? stop() : send(); }
function stop() { if (abortCtl) abortCtl.abort(); }
function retry(modelOverride) {
  if (busy) return;
  const c = activeConv(); if (!c) return;
  let lastUser = -1;
  for (let k = c.messages.length - 1; k >= 0; k--) if (c.messages[k].role === "user") { lastUser = k; break; }
  if (lastUser < 0) return;
  const u = c.messages[lastUser];
  c.messages = c.messages.slice(0, lastUser + 1);
  if (modelOverride) setModel(modelOverride);
  stream(c, u.content, u.payloadExtras || {});
}
async function send() {
  const text = $("prompt").value.trim();
  if (!text || busy) return;
  const prov = state.model.split(":")[0];
  const pstate = providers[prov === "auto" ? "auto" : prov];
  if (pstate && !pstate.ready) { toast(pstate.reason || "That model is unavailable"); openPalette(); return; }

  const c = ensureConv(text);
  const extras = {
    uploaded_files: attachments.filter((a) => a.kind === "file").map((a) => ({ name: a.name, content: a.content })),
    image_base64: (attachments.find((a) => a.kind === "image") || {}).content || null,
    workspace_files: Array.from(selectedFiles),
  };
  const attachLabels = [...attachments.map((a) => a.name), ...extras.workspace_files.map((f) => f.split("/").pop())];
  c.messages.push({ role: "user", content: text, attach: attachLabels, payloadExtras: extras });
  $("prompt").value = ""; autosize();
  attachments = []; renderChips();
  renderConvs();
  stream(c, text, extras);
}
async function stream(c, text, extras) {
  const history = c.messages.filter((m) => !m.error && m.content).slice(0, -1).slice(-12).map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.content }));
  const ai = { role: "assistant", content: "", reasoning: "", model: state.model, streaming: true };
  c.messages.push(ai);
  renderThread(); setBusy(true);
  abortCtl = new AbortController();
  const t0 = performance.now(); let firstTok = 0, chunks = 0, pending = false;
  const paint = () => { if (!pending) { pending = true; requestAnimationFrame(() => { pending = false; updateLast(); }); } };
  try {
    const res = await fetch("/api/chat/stream", {
      method: "POST", headers: { "Content-Type": "application/json" }, signal: abortCtl.signal,
      body: JSON.stringify({ prompt: text, target: state.model, history, ...extras }),
    });
    if (!res.ok) throw new Error(`Server returned HTTP ${res.status}`);
    const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = "";
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split("\n\n"); buf = parts.pop();
      for (const part of parts) {
        let ev = "delta", data = "";
        for (const l of part.split("\n")) { if (l.startsWith("event:")) ev = l.slice(6).trim(); else if (l.startsWith("data:")) data += l.slice(5).trim(); }
        if (!data) continue;
        let p; try { p = JSON.parse(data); } catch { continue; }
        if (ev === "start") { ai.model = state.model.startsWith("auto") ? (p.model_used || ai.model) : ai.model; ai.provider = p.provider; paint(); }
        else if (ev === "reasoning") { ai.reasoning += p.delta || ""; if (!firstTok) firstTok = performance.now(); paint(); }
        else if (ev === "delta") { ai.content += p.delta || ""; chunks++; if (!firstTok) firstTok = performance.now(); paint(); }
        else if (ev === "error") { ai.error = p.error || "Unknown error"; }
        else if (ev === "notice") { ai.provider = p.message; paint(); }
        else if (ev === "done") { /* stats below */ }
      }
    }
    if (!ai.content && !ai.error) ai.error = "The model returned no text. Try again or pick another model.";
  } catch (e) {
    if (e.name === "AbortError") { ai.stats = "stopped"; if (!ai.content) ai.content = "_Stopped._"; }
    else ai.error = e.message.includes("Failed to fetch") ? "Lost connection to Jupiter Studio. Is the app still running?" : e.message;
  } finally {
    const total = (performance.now() - t0) / 1000;
    if (!ai.stats && !ai.error) {
      const ttft = firstTok ? ((firstTok - t0) / 1000).toFixed(1) + "s to first token · " : "";
      ai.stats = `${ttft}${total.toFixed(1)}s total`;
    }
    ai.streaming = false; abortCtl = null; setBusy(false);
    save(); updateLast();
  }
}
function setBusy(b) {
  busy = b;
  const s = $("send"); s.classList.toggle("stop", b); s.innerHTML = b ? "&#9632;" : "&uarr;"; s.title = b ? "Stop" : "Send (Enter)";
  $("model-dot").className = "dot " + (b ? "busy" : (providers[state.model.split(":")[0]] || {}).ready === false ? "bad" : "");
}

/* ---------- Attachments ---------- */
function addFiles(list) {
  for (const f of Array.from(list || [])) {
    const r = new FileReader();
    if (f.type.startsWith("image/")) {
      r.onload = () => { attachments = attachments.filter((a) => a.kind !== "image"); attachments.push({ kind: "image", name: f.name, content: r.result }); renderChips(); };
      r.readAsDataURL(f);
    } else {
      if (f.size > 2_000_000) { toast(`${f.name} is too large (2 MB max)`); continue; }
      r.onload = () => { attachments.push({ kind: "file", name: f.name, content: String(r.result) }); renderChips(); };
      r.readAsText(f);
    }
  }
}
function renderChips() {
  const chips = attachments.map((a, i) => `<span class="chip">${a.kind === "image" ? `<img src="${a.content}" alt=""/>` : ""}${esc(a.name)}<button onclick="removeAttachment(${i})">&times;</button></span>`);
  selectedFiles.forEach((p) => chips.push(`<span class="chip">repo: ${esc(p.split("/").pop())}<button onclick="toggleFile('${esc(p).replace(/'/g, "\\'")}')">&times;</button></span>`));
  $("chips").innerHTML = chips.join("");
}
function removeAttachment(i) { attachments.splice(i, 1); renderChips(); }
$("file-in").addEventListener("change", (e) => { addFiles(e.target.files); e.target.value = ""; });
let dragDepth = 0;
window.addEventListener("dragenter", (e) => { e.preventDefault(); dragDepth++; $("composer").classList.add("drag"); });
window.addEventListener("dragover", (e) => e.preventDefault());
window.addEventListener("dragleave", () => { if (--dragDepth <= 0) { dragDepth = 0; $("composer").classList.remove("drag"); } });
window.addEventListener("drop", (e) => { e.preventDefault(); dragDepth = 0; $("composer").classList.remove("drag"); addFiles(e.dataTransfer.files); });
$("prompt").addEventListener("paste", (e) => {
  const imgs = Array.from(e.clipboardData?.files || []).filter((f) => f.type.startsWith("image/"));
  if (imgs.length) { e.preventDefault(); addFiles(imgs); }
});

/* ---------- Repo files ---------- */
async function loadFiles() {
  try { const d = await (await fetch("/api/workspace/files")).json(); workspaceFiles = d.files || []; renderFiles(); }
  catch { $("files").innerHTML = `<div class="file">Could not scan workspace</div>`; }
}
function renderFiles() {
  const q = $("file-q").value.toLowerCase();
  const list = workspaceFiles.filter((f) => !q || f.path.toLowerCase().includes(q)).slice(0, 150);
  $("files").innerHTML = list.map((f) => {
    const p = esc(f.path), on = selectedFiles.has(f.path);
    return `<label class="file"><input type="checkbox" ${on ? "checked" : ""} onchange="toggleFile('${p.replace(/'/g, "\\'")}')"/><span class="p" title="${p}">${p}</span><span class="s">${f.size_kb}K</span></label>`;
  }).join("") || `<div class="file">No matches</div>`;
  $("staged").textContent = `${selectedFiles.size} selected`;
  $("ctx-tool").textContent = selectedFiles.size ? `Repo files (${selectedFiles.size})` : "Repo files";
}
function toggleFile(p) { selectedFiles.has(p) ? selectedFiles.delete(p) : selectedFiles.add(p); renderFiles(); renderChips(); }

/* ---------- Model palette ---------- */
async function loadModels(announce) {
  try {
    const d = await (await fetch("/api/models")).json();
    providers = d.providers || {};
    const installed = d.ollama_installed || [];
    const names = installed.length ? installed : OLLAMA_DEFAULTS;
    CATALOG.find((g) => g.key === "ollama").items = names.map((n) => ({ v: "ollama:" + n, n, t: installed.length ? "installed" : "not detected" }));
    renderProviders(); setModel(state.model, true);
    if (announce) toast("Providers refreshed");
  } catch { /* keep previous */ }
}
function renderProviders() {
  $("prov-list").innerHTML = CATALOG.filter((g) => g.key !== "auto").map((g) => {
    const p = providers[g.key] || {};
    return `<div class="kv"><span>${esc(g.group)}</span><span style="color:${p.ready ? "var(--ok)" : "var(--muted)"}" title="${esc(p.reason || "")}">${p.ready ? "ready" : "off"}</span></div>`;
  }).join("");
}
let retryMode = false;
function openPalette(forRetry) { retryMode = !!forRetry; $("overlay").classList.add("open"); $("pal-q").value = ""; palIndex = 0; renderPalette(); setTimeout(() => $("pal-q").focus(), 10); }
function closePalette() { $("overlay").classList.remove("open"); $("prompt").focus(); }
function renderPalette() {
  const q = $("pal-q").value.toLowerCase(); palFlat = []; let html = "";
  for (const g of CATALOG) {
    const p = providers[g.key] || { ready: g.key === "auto" };
    const items = g.items.filter((it) => !q || (it.n + " " + it.t + " " + g.group).toLowerCase().includes(q));
    if (!items.length) continue;
    html += `<div class="pal-group"><span>${esc(g.group)}</span>${p.ready ? "" : `<em>${esc(p.reason || "unavailable")}</em>`}</div>`;
    for (const it of items) {
      const k = palFlat.length; palFlat.push({ it, ready: p.ready });
      html += `<button class="pal-item ${it.v === state.model ? "sel" : ""} ${p.ready ? "" : "off"} ${k === palIndex ? "kb" : ""}" onclick="pickModel(${k})">
        <span class="dot ${p.ready ? "" : "bad"}"></span><span class="n">${esc(it.n)}</span><span class="t">${esc(it.t)}</span></button>`;
    }
  }
  $("pal-list").innerHTML = html || `<div class="pal-group">No models match</div>`;
  $("pal-count").textContent = `${palFlat.filter((x) => x.ready).length} ready / ${palFlat.length}`;
}
function pickModel(k) {
  const entry = palFlat[k]; if (!entry) return;
  if (!entry.ready) { toast("Unavailable: " + ((providers[entry.it.v.split(":")[0]] || {}).reason || "not configured")); return; }
  setModel(entry.it.v); closePalette();
  if (retryMode) { retryMode = false; retry(entry.it.v); }
}
function setModel(v, silent) {
  state.model = v; save();
  const l = labelFor(v); $("model-name").textContent = l.n; $("model-prov").textContent = v.startsWith("auto") ? "d3 router" : l.g;
  const p = providers[v.split(":")[0]];
  $("model-dot").className = "dot " + (p && !p.ready ? "bad" : "");
  if (!silent) toast(`Model: ${l.n}`);
}
$("pal-q").addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown") { palIndex = Math.min(palFlat.length - 1, palIndex + 1); renderPalette(); e.preventDefault(); }
  else if (e.key === "ArrowUp") { palIndex = Math.max(0, palIndex - 1); renderPalette(); e.preventDefault(); }
  else if (e.key === "Enter") { pickModel(palIndex); e.preventDefault(); }
  else if (e.key === "Escape") closePalette();
});

/* ---------- Status ---------- */
async function loadStatus() {
  try {
    const d = await (await fetch("/api/status")).json();
    const g = d.gpu || {}, h = d.health || {}, pol = d.policy || {};
    const used = Math.round(g.used_vram_mb || 0), total = Math.round(g.total_vram_mb || 0);
    $("hw-name").textContent = g.device_name || "CPU only";
    $("hw-vram").textContent = total ? `${used.toLocaleString()} / ${total.toLocaleString()} MB` : "--";
    $("hw-temp").textContent = g.temperature_c != null ? `${Math.round(g.temperature_c)}°C · ${Math.round(g.utilization_pct || 0)}%` : "--";
    $("hw-gate").textContent = `${pol.cpu_gate_ms ?? 0.091} ms`;
    $("foot-gpu").textContent = (g.device_name || "CPU").replace(/NVIDIA GeForce |AMD Radeon /, "").replace(" Laptop GPU", " Laptop");
    $("foot-vram").textContent = `${used.toLocaleString()} MB`;
    $("vram-pill").textContent = `Studio VRAM 0 MB · GPU ${used.toLocaleString()} MB in use`;
    if (h.score != null) {
      $("h-score").textContent = h.score; $("h-grade").textContent = `grade ${h.grade}`;
      $("h-status").textContent = h.status || ""; $("h-bar").style.width = h.score + "%";
      $("h-bar").style.background = h.score >= 80 ? "var(--ok)" : h.score >= 60 ? "var(--accent)" : "var(--bad)";
    }
  } catch {}
}

/* ---------- Layout ---------- */
function toggleTheme() { state.theme = state.theme === "dark" ? "light" : "dark"; document.documentElement.dataset.theme = state.theme; save(); }
function toggleDrawer(force) {
  state.drawer = force === true ? true : !state.drawer;
  $("app").classList.toggle("drawer-open", state.drawer); $("drawer-btn").classList.toggle("on", state.drawer); save();
}
function toggleRail() { $("app").classList.toggle("rail-closed"); }
function autosize() { const t = $("prompt"); t.style.height = "auto"; t.style.height = Math.min(240, t.scrollHeight) + "px"; }
$("prompt").addEventListener("input", autosize);
$("prompt").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); } });
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); }
  else if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "o") { e.preventDefault(); newChat(); }
  else if (e.key === "Escape" && busy) stop();
});

/* ---------- Boot ---------- */
document.documentElement.dataset.theme = state.theme;
if (state.drawer) toggleDrawer(true);
// Mark any message left mid-stream by a reload as finished.
state.convs.forEach((c) => c.messages.forEach((m) => { if (m.streaming) { m.streaming = false; if (!m.content) m.error = "Interrupted by page reload."; } }));
renderConvs(); renderThread(); setModel(state.model, true);
loadModels(); loadStatus(); loadFiles();
setInterval(loadStatus, 5000); setInterval(loadModels, 30000);
$("prompt").focus();
</script>
</body>
</html>
"""

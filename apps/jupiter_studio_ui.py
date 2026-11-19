"""Jupiter Studio UI — Half AMD (Ryzen Amber) / Half Radeon (Ruby Red) in an Atari Heavy-Sixer Deck.

Preserves the full chat-first engine:
  * Live /api/models readiness probe (marks ready vs offline providers with exact reasons)
  * Full multi-turn conversation history persisted in localStorage ("Cartridge Slots")
  * Complete Markdown + fenced code blocks with Copy, Edit, Retry, Retry with...
  * Multi-file + image drag-and-drop & paste + Workspace Repo File staging
"""

STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en" data-crt="color">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>JUPITER STUDIO // AMD x RADEON ATARI DECK</title>
<link rel="icon" type="image/png" href="/assets/jupiter_studio_icon.png" />
<style>
  :root {
    --bg: #0b0b0d;
    --abs-black: #121216;
    --surface: #17171c;
    --raised: #1e1e25;
    --hover: #272730;
    --line: #2e2e38;
    --line-2: #444452;
    --text: #f2eee6;
    --text-2: #b8b2a6;
    --muted: #7a756c;

    /* Half AMD (Left: Ryzen / Token Lab Sunset Amber) */
    --amd: #ff6a00;
    --amd-gold: #ffb000;
    --amd-soft: rgba(255, 106, 0, 0.14);

    /* Half Radeon (Right: Radeon Ruby Crimson) */
    --radeon: #ed1c24;
    --radeon-bright: #ff2e4c;
    --radeon-soft: rgba(237, 28, 36, 0.14);

    /* Atari Walnut & Chrome accents */
    --walnut-1: #5a351d;
    --walnut-2: #3d2210;
    --chrome: #d8d4c8;
    --ok: #30d158;
    --bad: #ff453a;
    --code: #08080a;

    --sans: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
    --mono: "JetBrains Mono", "Cascadia Code", "Consolas", ui-monospace, monospace;
  }

  html[data-crt="bw"] {
    --amd: #d8d4c8;
    --amd-gold: #ffffff;
    --radeon: #9e9a90;
    --radeon-bright: #e6e2d8;
    --amd-soft: rgba(255, 255, 255, 0.10);
    --radeon-soft: rgba(255, 255, 255, 0.08);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; overflow: hidden; }
  body {
    background: var(--bg);
    color: var(--text);
    font: 14px/1.55 var(--sans);
    display: flex;
    flex-direction: column;
    -webkit-font-smoothing: antialiased;
  }
  button { font: inherit; color: inherit; background: none; border: none; cursor: pointer; }
  ::-webkit-scrollbar { width: 8px; height: 8px; }
  ::-webkit-scrollbar-track { background: var(--abs-black); }
  ::-webkit-scrollbar-thumb { background: var(--line-2); }

  /* CRT Scanline overlay (subtle, pointer-events:none) */
  body::after {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 90;
    background: repeating-linear-gradient(
      to bottom,
      rgba(255, 255, 255, 0) 0px,
      rgba(255, 255, 255, 0) 2px,
      rgba(0, 0, 0, 0.16) 3px
    );
    opacity: 0.45;
  }

  /* ── ATARI 2600 RIBBED TOP DECK + SPLIT AMD/RADEON RIBBON ───────────── */
  .atari-deck {
    background:
      repeating-linear-gradient(
        to bottom,
        #18181d 0px,
        #18181d 3px,
        #0d0d10 3px,
        #0d0d10 6px
      );
    border-bottom: 3px solid var(--walnut-1);
    box-shadow: inset 0 -2px 0 var(--walnut-2);
    flex-shrink: 0;
  }

  /* Split Dual-Color Atari Racing Stripe: Left 50% AMD Amber, Right 50% Radeon Ruby */
  .dual-ribbon {
    height: 5px;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
  .ribbon-amd {
    background: linear-gradient(90deg, var(--amd) 0%, var(--amd-gold) 100%);
  }
  .ribbon-radeon {
    background: linear-gradient(90deg, var(--radeon) 0%, var(--radeon-bright) 100%);
  }

  .bezel-bar {
    height: 56px;
    padding: 0 14px;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 14px;
  }

  /* Atari Fuji x AMD Chevron Badge */
  .atari-brand {
    display: flex;
    align-items: center;
    gap: 11px;
    background: #101014;
    border: 1px solid var(--line-2);
    border-left: 4px solid var(--amd);
    border-right: 4px solid var(--radeon);
    padding: 5px 12px;
  }
  .fuji-svg { width: 32px; height: 24px; flex-shrink: 0; }
  .brand-stack { display: flex; flex-direction: column; line-height: 1.08; }
  .brand-main {
    font-family: var(--mono);
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    background: linear-gradient(90deg, var(--amd-gold) 0%, var(--text) 48%, var(--radeon-bright) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .brand-sub {
    font-family: var(--mono);
    font-size: 9.5px;
    letter-spacing: 0.12em;
    color: var(--text-2);
    text-transform: uppercase;
  }
  .brand-sub .half-a { color: var(--amd-gold); }
  .brand-sub .half-r { color: var(--radeon-bright); }

  /* Center Cartridge / Model Selector Slot */
  .cartridge-slot {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    min-width: 0;
  }
  .cartridge-btn {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 7px 14px;
    background: linear-gradient(90deg, rgba(255,106,0,0.16) 0%, #16161c 50%, rgba(237,28,36,0.16) 100%);
    border: 1px solid var(--line-2);
    border-top: 2px solid var(--chrome);
    font-family: var(--mono);
    max-width: 460px;
    transition: transform 0.08s, border-color 0.12s;
  }
  .cartridge-btn:hover {
    border-color: var(--amd-gold);
    transform: translateY(-1px);
  }
  .cart-label {
    font-size: 9.5px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--amd-gold);
    border-right: 1px solid var(--line-2);
    padding-right: 8px;
  }
  .cart-name {
    font-weight: 700;
    font-size: 12.5px;
    color: var(--text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .cart-prov {
    font-size: 10.5px;
    color: var(--radeon-bright);
    text-transform: uppercase;
  }
  .kbd {
    font: 600 10px var(--mono);
    color: var(--chrome);
    background: #0c0c10;
    border: 1px solid var(--line-2);
    padding: 1px 5px;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); flex-shrink: 0; box-shadow: 0 0 6px var(--ok); }
  .dot.bad { background: var(--bad); box-shadow: 0 0 6px var(--bad); }
  .dot.busy { background: var(--amd-gold); box-shadow: 0 0 8px var(--amd-gold); animation: pulse 0.8s infinite; }
  @keyframes pulse { 50% { opacity: 0.25; } }

  /* Atari Chrome Toggle Switches */
  .switch-bank {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .atari-switch {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4px 10px;
    background: linear-gradient(180deg, #2a2a34 0%, #141419 100%);
    border: 1px solid var(--line-2);
    border-top: 2px solid var(--chrome);
    font-family: var(--mono);
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text);
    min-width: 68px;
  }
  .atari-switch:hover { border-color: var(--amd-gold); color: var(--amd-gold); }
  .atari-switch.on {
    border-top-color: var(--radeon-bright);
    color: var(--radeon-bright);
    background: linear-gradient(180deg, rgba(237,28,36,0.22) 0%, #141419 100%);
  }
  .atari-switch small {
    font-size: 8px;
    color: var(--muted);
    letter-spacing: 0.08em;
  }

  /* ── THREE-COLUMN SPLIT WORKBENCH (LEFT AMD // CENTER ATARI // RIGHT RADEON) */
  .app {
    flex: 1;
    display: grid;
    grid-template-columns: 256px 1fr 296px;
    min-height: 0;
    transition: grid-template-columns 0.16s ease;
  }
  .app.no-drawer { grid-template-columns: 256px 1fr 0px; }
  .app.no-rail { grid-template-columns: 0px 1fr 296px; }
  .app.no-rail.no-drawer { grid-template-columns: 0px 1fr 0px; }

  /* LEFT WING: AMD RYZEN / TOKEN LAB (Sunset Amber Border & Accents) */
  .wing-amd {
    background: var(--abs-black);
    border-right: 2px solid var(--amd);
    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow: hidden;
  }
  .wing-head {
    height: 34px;
    padding: 0 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: var(--mono);
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    flex-shrink: 0;
  }
  .wing-head.amd-bar {
    background: linear-gradient(90deg, rgba(255,106,0,0.24) 0%, rgba(255,176,0,0.05) 100%);
    border-bottom: 1px solid var(--amd);
    color: var(--amd-gold);
  }
  .wing-head.radeon-bar {
    background: linear-gradient(90deg, rgba(237,28,36,0.06) 0%, rgba(237,28,36,0.26) 100%);
    border-bottom: 1px solid var(--radeon);
    color: var(--radeon-bright);
  }

  .new-cart-btn {
    margin: 10px 10px 8px;
    padding: 9px 11px;
    background: var(--amd-soft);
    border: 1px solid var(--amd);
    border-left: 4px solid var(--amd-gold);
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .new-cart-btn:hover { background: rgba(255, 106, 0, 0.25); }

  .conv-list { flex: 1; overflow-y: auto; padding: 0 8px 12px; }
  .conv-group {
    font: 700 9.5px var(--mono);
    color: var(--amd-gold);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 12px 6px 4px;
    border-bottom: 1px dotted rgba(255, 106, 0, 0.35);
    margin-bottom: 4px;
  }
  .conv {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 7px 8px;
    margin-bottom: 3px;
    border: 1px solid transparent;
    border-left: 3px solid transparent;
    color: var(--text-2);
    cursor: pointer;
    font-size: 12.5px;
  }
  .conv:hover { background: var(--hover); color: var(--text); border-left-color: var(--amd); }
  .conv.active {
    background: var(--raised);
    color: var(--text);
    border-color: var(--line-2);
    border-left: 3px solid var(--amd-gold);
  }
  .conv-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .conv-del { opacity: 0; color: var(--muted); font-family: var(--mono); padding: 0 4px; }
  .conv:hover .conv-del { opacity: 1; }
  .conv-del:hover { color: var(--bad); }

  .wing-foot {
    border-top: 1px solid var(--line);
    padding: 9px 12px;
    font: 10.5px var(--mono);
    color: var(--amd-gold);
    background: #0e0e12;
    display: flex;
    justify-content: space-between;
  }

  /* ── CENTER MONITOR: ATARI VECTOR / CONVERSATION CRT ────────────────── */
  .center-crt {
    display: flex;
    flex-direction: column;
    min-width: 0;
    background:
      radial-gradient(circle at 18% 0%, rgba(255, 106, 0, 0.06), transparent 42%),
      radial-gradient(circle at 82% 0%, rgba(237, 28, 36, 0.06), transparent 42%),
      var(--bg);
  }

  .scroller { flex: 1; overflow-y: auto; }
  .thread { max-width: 820px; margin: 0 auto; padding: 26px 24px 36px; }

  /* Atari x AMD x Radeon Hero Card */
  .welcome {
    margin-top: 3vh;
    border: 1px solid var(--line-2);
    background: var(--abs-black);
    position: relative;
    overflow: hidden;
  }
  .welcome-stripes {
    display: grid;
    grid-template-columns: 1fr 1fr;
    height: 6px;
  }
  .welcome-body { padding: 22px 24px 24px; }
  .welcome-kicker {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font: 700 10.5px var(--mono);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .kicker-amd { color: var(--amd-gold); }
  .kicker-sep { color: var(--muted); }
  .kicker-rad { color: var(--radeon-bright); }

  .welcome h1 {
    font-family: var(--mono);
    font-size: 24px;
    font-weight: 800;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .welcome p {
    color: var(--text-2);
    font-size: 13.5px;
    max-width: 620px;
    margin-bottom: 18px;
  }

  /* Atari Fuji Telemetry Banner inside Welcome */
  .telemetry-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 18px;
  }
  .tele-cell {
    background: var(--surface);
    border: 1px solid var(--line);
    padding: 8px 10px;
    font-family: var(--mono);
  }
  .tele-cell.amd-side { border-top: 2px solid var(--amd); }
  .tele-cell.rad-side { border-top: 2px solid var(--radeon); }
  .tele-k { font-size: 9px; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; }
  .tele-v { font-size: 13px; font-weight: 800; color: var(--text); margin-top: 2px; }

  .starters { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .starter {
    text-align: left;
    padding: 12px 14px;
    background: var(--surface);
    border: 1px solid var(--line-2);
    border-left: 4px solid var(--amd);
    transition: background 0.1s, border-color 0.1s;
  }
  .starter:nth-child(even) { border-left-color: var(--radeon); }
  .starter:hover { background: var(--raised); border-color: var(--chrome); }
  .starter b {
    display: block;
    font-family: var(--mono);
    font-size: 12px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 3px;
  }
  .starter:nth-child(odd) b { color: var(--amd-gold); }
  .starter:nth-child(even) b { color: var(--radeon-bright); }
  .starter span { color: var(--text-2); font-size: 12.5px; }

  /* Messages: User = AMD Amber Tag, Assistant = Radeon Ruby Tag */
  .msg { margin-bottom: 24px; }
  .msg.user {
    border-left: 3px solid var(--amd);
    background: linear-gradient(90deg, rgba(255,106,0,0.09) 0%, transparent 90%);
    padding: 10px 14px;
  }
  .msg.ai {
    border-left: 3px solid var(--radeon);
    background: linear-gradient(90deg, rgba(237,28,36,0.07) 0%, transparent 90%);
    padding: 10px 14px;
  }
  .who {
    display: flex;
    align-items: center;
    gap: 8px;
    font: 700 11px var(--mono);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .msg.user .who b { color: var(--amd-gold); }
  .msg.ai .who b { color: var(--radeon-bright); }
  .who span { color: var(--muted); font-weight: 500; }

  .user-text { white-space: pre-wrap; word-break: break-word; font-size: 14.5px; }
  .attach-line { font: 11px var(--mono); color: var(--amd-gold); margin-top: 6px; }

  .md { font-size: 14.5px; line-height: 1.68; word-break: break-word; }
  .md p { margin: 0 0 11px; }
  .md p:last-child { margin-bottom: 0; }
  .md h1, .md h2, .md h3, .md h4 {
    font-family: var(--mono);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin: 18px 0 8px;
    color: var(--amd-gold);
  }
  .md h1 { font-size: 18px; } .md h2 { font-size: 16px; } .md h3 { font-size: 14px; }
  .md ul, .md ol { margin: 0 0 12px 22px; }
  .md li { margin: 3px 0; }
  .md blockquote { border-left: 3px solid var(--amd-gold); padding: 2px 12px; color: var(--text-2); margin: 0 0 12px; }
  .md a { color: var(--amd-gold); }
  .md hr { border: none; border-top: 1px solid var(--line); margin: 14px 0; }
  .md :not(pre) > code {
    font: 12.5px var(--mono);
    background: var(--raised);
    border: 1px solid var(--line-2);
    color: var(--amd-gold);
    padding: 1px 5px;
  }
  .md table { border-collapse: collapse; margin: 0 0 12px; font-size: 12.5px; display: block; overflow-x: auto; font-family: var(--mono); }
  .md th, .md td { border: 1px solid var(--line-2); padding: 6px 10px; text-align: left; }
  .md th { background: var(--raised); color: var(--amd-gold); }

  .codeblock {
    margin: 0 0 14px;
    border: 1px solid var(--line-2);
    border-left: 3px solid var(--amd-gold);
    background: var(--code);
  }
  .codebar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 12px;
    font: 700 10.5px var(--mono);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--amd-gold);
    background: #121217;
    border-bottom: 1px solid var(--line);
  }
  .codebar button {
    color: var(--chrome);
    border: 1px solid var(--line-2);
    font: 700 10px var(--mono);
    padding: 2px 8px;
    text-transform: uppercase;
  }
  .codebar button:hover { border-color: var(--radeon-bright); color: var(--radeon-bright); }
  .codeblock pre { margin: 0; padding: 12px 14px; overflow-x: auto; font: 12.8px/1.55 var(--mono); color: #f0ece1; }

  .think { border: 1px dashed var(--line-2); margin-bottom: 10px; background: var(--abs-black); }
  .think summary { cursor: pointer; padding: 6px 10px; font: 700 10.5px var(--mono); color: var(--amd-gold); text-transform: uppercase; letter-spacing: 0.08em; list-style: none; }
  .think summary::before { content: "[+] "; }
  .think[open] summary::before { content: "[-] "; }
  .think div { padding: 0 10px 10px; font: 12px/1.55 var(--mono); color: var(--text-2); white-space: pre-wrap; max-height: 240px; overflow-y: auto; }

  .caret::after {
    content: "";
    display: inline-block;
    width: 9px;
    height: 15px;
    background: var(--radeon-bright);
    margin-left: 3px;
    vertical-align: -2px;
    animation: pulse 0.8s infinite;
  }
  .waiting { color: var(--amd-gold); font: 12px var(--mono); text-transform: uppercase; letter-spacing: 0.08em; }
  .err-box {
    border: 1px solid var(--bad);
    border-left: 4px solid var(--bad);
    background: rgba(255, 69, 58, 0.10);
    padding: 10px 12px;
    font-family: var(--mono);
    font-size: 12.5px;
  }
  .err-box b { color: var(--bad); display: block; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.08em; }

  .msg-tools { display: flex; gap: 6px; margin-top: 8px; opacity: 0; transition: opacity 0.12s; }
  .msg:hover .msg-tools, .msg:last-child .msg-tools { opacity: 1; }
  .msg-tools button {
    font: 700 10px var(--mono);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-2);
    border: 1px solid var(--line);
    background: var(--abs-black);
    padding: 3px 8px;
  }
  .msg-tools button:hover { border-color: var(--amd-gold); color: var(--amd-gold); }
  .stat { font: 10.5px var(--mono); color: var(--muted); margin-left: auto; align-self: center; }

  /* ── ATARI COMMAND DECK (COMPOSER) ──────────────────────────────────── */
  .composer-wrap {
    padding: 0 24px 16px;
  }
  .composer {
    max-width: 820px;
    margin: 0 auto;
    background: var(--abs-black);
    border: 1px solid var(--line-2);
    border-left: 4px solid var(--amd);
    border-right: 4px solid var(--radeon);
    padding: 10px 12px 8px;
  }
  .composer:focus-within { border-top-color: var(--amd-gold); border-bottom-color: var(--radeon-bright); }
  .composer.drag { outline: 2px dashed var(--amd-gold); background: var(--amd-soft); }

  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
  .chips:empty { display: none; }
  .chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font: 11px var(--mono);
    background: var(--raised);
    border: 1px solid var(--amd);
    padding: 2px 6px 2px 8px;
  }
  .chip button { color: var(--muted); font-weight: 700; padding: 0 3px; }
  .chip button:hover { color: var(--bad); }
  .chip img { width: 20px; height: 20px; object-fit: cover; }

  #prompt {
    width: 100%;
    resize: none;
    border: none;
    outline: none;
    background: transparent;
    color: var(--text);
    font: 14.5px/1.55 var(--sans);
    max-height: 220px;
    min-height: 26px;
  }
  #prompt::placeholder { color: var(--muted); }

  .composer-row { display: flex; align-items: center; gap: 6px; margin-top: 6px; }
  .deck-key {
    font: 700 10.5px var(--mono);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-2);
    background: var(--surface);
    border: 1px solid var(--line-2);
    padding: 5px 10px;
  }
  .deck-key:hover { border-color: var(--amd-gold); color: var(--amd-gold); }
  .spacer { flex: 1; }

  /* Atari Red Fire Button */
  .fire-btn {
    padding: 6px 16px;
    background: linear-gradient(90deg, var(--amd) 0%, var(--radeon) 100%);
    color: #fff;
    border: 1px solid var(--chrome);
    font: 800 11px var(--mono);
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }
  .fire-btn:hover { filter: brightness(1.12); }
  .fire-btn.stop { background: var(--bad); }

  .hint {
    max-width: 820px;
    margin: 6px auto 0;
    font: 10.5px var(--mono);
    color: var(--muted);
    text-align: center;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  /* ── RIGHT WING: RADEON RUBY TELEMETRY & REPO CONTEXT ───────────────── */
  .wing-radeon {
    background: var(--abs-black);
    border-left: 2px solid var(--radeon);
    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow: hidden;
  }
  .drawer-body {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .rad-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-top: 2px solid var(--radeon);
    padding: 10px;
  }
  .rad-card.amd-accent { border-top-color: var(--amd); }
  .sec-title {
    font: 800 10px var(--mono);
    color: var(--radeon-bright);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .rad-card.amd-accent .sec-title { color: var(--amd-gold); }

  .kv {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    font: 11.5px var(--mono);
    padding: 4px 0;
    border-bottom: 1px dotted var(--line);
  }
  .kv:last-child { border-bottom: none; }
  .kv span:first-child { color: var(--muted); }
  .kv span:last-child { text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 700; }

  /* Atari Segmented Power Bar for Workstation Health */
  .health-top { display: flex; align-items: baseline; justify-content: space-between; font-family: var(--mono); }
  .health-top b { font-size: 26px; font-weight: 800; color: var(--text); }
  .health-grade {
    font: 800 11px var(--mono);
    padding: 2px 7px;
    border: 1px solid var(--radeon-bright);
    color: var(--radeon-bright);
    text-transform: uppercase;
  }
  .seg-bar {
    height: 10px;
    margin-top: 6px;
    background: #0c0c10;
    border: 1px solid var(--line-2);
    overflow: hidden;
  }
  .seg-fill {
    height: 100%;
    background: repeating-linear-gradient(
      90deg,
      var(--amd) 0px,
      var(--amd-gold) 10px,
      var(--radeon) 20px,
      #0c0c10 20px,
      #0c0c10 23px
    );
  }

  .search {
    width: 100%;
    padding: 6px 8px;
    border: 1px solid var(--line-2);
    background: var(--abs-black);
    color: var(--text);
    font: 11.5px var(--mono);
    outline: none;
    margin-bottom: 6px;
  }
  .search:focus { border-color: var(--amd-gold); }
  .files { max-height: 220px; overflow-y: auto; border: 1px solid var(--line); background: var(--abs-black); }
  .file {
    display: flex;
    gap: 7px;
    align-items: center;
    padding: 5px 8px;
    font: 11px var(--mono);
    cursor: pointer;
    border-bottom: 1px solid var(--line);
  }
  .file:last-child { border-bottom: none; }
  .file:hover { background: var(--hover); }
  .file input { accent-color: var(--amd); }
  .file .p { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .file .s { color: var(--muted); }

  /* ── CARTRIDGE SELECTOR MODAL (CTRL+K) ──────────────────────────────── */
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.72);
    display: none;
    align-items: flex-start;
    justify-content: center;
    padding-top: 10vh;
    z-index: 80;
  }
  .overlay.open { display: flex; }
  .palette {
    width: min(640px, 94vw);
    max-height: 74vh;
    background: var(--abs-black);
    border: 2px solid var(--chrome);
    border-left: 5px solid var(--amd);
    border-right: 5px solid var(--radeon);
    display: flex;
    flex-direction: column;
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.75);
  }
  .palette input {
    border: none;
    border-bottom: 1px solid var(--line-2);
    background: #14141a;
    color: var(--text);
    padding: 13px 16px;
    font: 14px var(--mono);
    outline: none;
  }
  .pal-list { overflow-y: auto; padding: 6px; }
  .pal-group {
    font: 800 10px var(--mono);
    color: var(--amd-gold);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 10px 10px 4px;
    display: flex;
    justify-content: space-between;
    border-bottom: 1px dotted var(--line-2);
  }
  .pal-group em { font-style: normal; color: var(--radeon-bright); font-weight: 600; }
  .pal-item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    text-align: left;
    padding: 8px 10px;
    font-family: var(--mono);
    font-size: 12.5px;
  }
  .pal-item:hover, .pal-item.kb { background: var(--hover); }
  .pal-item.sel { background: var(--amd-soft); border-left: 3px solid var(--amd-gold); }
  .pal-item.off { opacity: 0.45; }
  .pal-item .n { flex: 1; font-weight: 700; }
  .pal-item .t { font-size: 10.5px; color: var(--muted); }
  .pal-foot {
    border-top: 1px solid var(--line-2);
    padding: 8px 14px;
    font: 10.5px var(--mono);
    color: var(--text-2);
    background: #101015;
    display: flex;
    justify-content: space-between;
  }

  .toast {
    position: fixed;
    bottom: 22px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(90deg, var(--amd) 0%, var(--radeon) 100%);
    color: #fff;
    padding: 8px 16px;
    border: 1px solid var(--chrome);
    font: 700 11.5px var(--mono);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s;
    z-index: 95;
  }
  .toast.show { opacity: 1; }

  @media (max-width: 960px) {
    .app { grid-template-columns: 0px 1fr 0px; }
    .telemetry-strip, .starters { grid-template-columns: 1fr 1fr; }
  }
</style>
</head>
<body>

  <!-- ATARI 2600 RIBBED TOP DECK -->
  <header class="atari-deck">
    <div class="dual-ribbon">
      <div class="ribbon-amd"></div>
      <div class="ribbon-radeon"></div>
    </div>
    <div class="bezel-bar">
      <!-- Left: Atari Fuji + AMD/Radeon Split Emblem -->
      <div class="atari-brand">
        <!-- Geometric Atari Fuji (Left Amber pillar, Center Chrome pillar, Right Radeon Ruby pillar) -->
        <svg class="fuji-svg" viewBox="0 0 36 26" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M13 3C13 13 8 20 2 23H7.5C12 19 14.5 13 14.5 3H13Z" fill="#FF6A00"/>
          <rect x="16.2" y="3" width="3.6" height="20" fill="#F2EEE6"/>
          <path d="M23 3C23 13 28 20 34 23H28.5C24 19 21.5 13 21.5 3H23Z" fill="#ED1C24"/>
        </svg>
        <div class="brand-stack">
          <span class="brand-main">Jupiter Studio</span>
          <span class="brand-sub"><span class="half-a">AMD RYZEN</span> // <span class="half-r">RADEON</span> ATARI DECK</span>
        </div>
      </div>

      <!-- Center: Cartridge / Model Selector Slot -->
      <div class="cartridge-slot">
        <button class="cartridge-btn" onclick="openPalette()" title="Select Model Cartridge (Ctrl+K)">
          <span class="cart-label">CARTRIDGE</span>
          <span class="dot" id="model-dot"></span>
          <span class="cart-name" id="model-name">Auto</span>
          <span class="cart-prov" id="model-prov">d3 router</span>
          <span class="kbd">Ctrl+K</span>
        </button>
      </div>

      <!-- Right: Atari Silver Toggle Switches -->
      <div class="switch-bank">
        <button class="atari-switch" onclick="toggleRail()">
          <span>SLOTS</span><small>LEFT BAY</small>
        </button>
        <button class="atari-switch" id="crt-switch" onclick="toggleCrt()">
          <span>TV TYPE</span><small id="crt-label">COLOR</small>
        </button>
        <button class="atari-switch" onclick="openPalette()">
          <span>SELECT</span><small>MODEL</small>
        </button>
        <button class="atari-switch" onclick="newChat()">
          <span>RESET</span><small>NEW CHAT</small>
        </button>
        <button class="atari-switch on" id="drawer-btn" onclick="toggleDrawer()">
          <span>RADEON</span><small>TELEMETRY</small>
        </button>
      </div>
    </div>
  </header>

  <!-- THREE-WING WORKBENCH -->
  <div class="app" id="app">

    <!-- LEFT WING: AMD RYZEN / TOKEN LAB CARTRIDGE SLOTS -->
    <aside class="wing-amd">
      <div class="wing-head amd-bar">
        <span>AMD // SESSION SLOTS</span>
        <span>0.091ms GATE</span>
      </div>
      <button class="new-cart-btn" onclick="newChat()">
        <span>+ INSERT NEW SESSION</span>
        <span class="kbd">RESET</span>
      </button>
      <div class="conv-list" id="conv-list"></div>
      <div class="wing-foot">
        <span id="foot-gpu">AMD / GPU</span>
        <span id="foot-vram">0 MB</span>
      </div>
    </aside>

    <!-- CENTER MONITOR: CONVERSATION & ATARI COMMAND DECK -->
    <main class="center-crt">
      <div class="scroller" id="scroller">
        <div class="thread" id="thread"></div>
      </div>

      <div class="composer-wrap">
        <div class="composer" id="composer">
          <div class="chips" id="chips"></div>
          <textarea id="prompt" rows="1" placeholder="Transmit command to cartridge... (drop files or images anywhere)"></textarea>
          <div class="composer-row">
            <input type="file" id="file-in" multiple hidden />
            <button class="deck-key" onclick="document.getElementById('file-in').click()">+ ATTACH FILE</button>
            <button class="deck-key" onclick="toggleDrawer(true)" id="ctx-tool">REPO FILES</button>
            <button class="deck-key" onclick="openPalette()">CARTRIDGE [CTRL+K]</button>
            <div class="spacer"></div>
            <button class="fire-btn" id="send" onclick="onSendClick()" title="Fire / Transmit (Enter)">FIRE &uarr;</button>
          </div>
        </div>
        <div class="hint" id="hint">ENTER = FIRE &middot; SHIFT+ENTER = NEWLINE &middot; CTRL+K = SWAP CARTRIDGE &middot; ZERO LOCAL VRAM</div>
      </div>
    </main>

    <!-- RIGHT WING: RADEON RUBY TELEMETRY & REPO CONTEXT -->
    <aside class="wing-radeon">
      <div class="wing-head radeon-bar">
        <span>RADEON // TELEMETRY BAY</span>
        <span id="vram-pill">0 MB VRAM</span>
      </div>
      <div class="drawer-body">
        <section class="rad-card">
          <div class="sec-title"><span>Workstation Health</span><span id="h-status">HEALTHY</span></div>
          <div class="health-top">
            <b id="h-score">100</b>
            <span class="health-grade" id="h-grade">GRADE A</span>
          </div>
          <div class="seg-bar"><div class="seg-fill" id="h-bar" style="width:100%"></div></div>
        </section>

        <section class="rad-card">
          <div class="sec-title"><span>GPU &amp; Zen 3 Gate</span></div>
          <div class="kv"><span>DEVICE</span><span id="hw-name">--</span></div>
          <div class="kv"><span>VRAM IN USE</span><span id="hw-vram">--</span></div>
          <div class="kv"><span>THERMAL / LOAD</span><span id="hw-temp">--</span></div>
          <div class="kv"><span>AMD ZEN 3 GATE</span><span id="hw-gate">0.091 ms</span></div>
        </section>

        <section class="rad-card amd-accent">
          <div class="sec-title"><span>Repo Context Files</span><span id="staged">0 STAGED</span></div>
          <input class="search" id="file-q" placeholder="Filter workspace files..." oninput="renderFiles()" />
          <div class="files" id="files"><div class="file">Scanning...</div></div>
        </section>

        <section class="rad-card">
          <div class="sec-title"><span>Bus Matrix</span><button class="kbd" onclick="loadModels(true)">PROBE</button></div>
          <div id="prov-list"></div>
        </section>
      </div>
    </aside>

  </div>

  <!-- CARTRIDGE PICKER MODAL (CTRL+K) -->
  <div class="overlay" id="overlay" onclick="if(event.target===this)closePalette()">
    <div class="palette">
      <input id="pal-q" placeholder="SELECT MODEL CARTRIDGE..." oninput="renderPalette()" />
      <div class="pal-list" id="pal-list"></div>
      <div class="pal-foot">
        <span>&uarr;&darr; SELECT &middot; ENTER LOAD CARTRIDGE &middot; ESC EXIT</span>
        <span id="pal-count"></span>
      </div>
    </div>
  </div>
  <div class="toast" id="toast"></div>

<script>
const CATALOG = [
  { key: "auto", group: "AMD d3 Smart Router", items: [ { v: "auto:d3", n: "Auto (d3 Gate)", t: "0.091ms host gate + Instinct" } ] },
  { key: "cloud", group: "AMD Token Lab (Instinct Cloud)", items: [
    { v: "cloud:Gemma-4-31B-IT", n: "Gemma 4 31B", t: "vision + reasoning" },
    { v: "cloud:Qwen3.8-27B", n: "Qwen 3.8 27B", t: "code architecture" },
    { v: "cloud:DeepSeek-V4.1-Flash", n: "DeepSeek V4.1 Flash", t: "1M context" },
    { v: "cloud:MiniCPM5-2B", n: "MiniCPM5 2B", t: "fast response" } ] },
  { key: "nv", group: "NVIDIA NIM", items: [
    { v: "nv:qwen/qwen2.5-coder-32b-instruct", n: "Qwen 2.5 Coder 32B", t: "code" },
    { v: "nv:meta/llama-3.3-70b-instruct", n: "Llama 3.3 70B", t: "general" },
    { v: "nv:qwen/qwen2.5-7b-instruct", n: "Qwen 2.5 7B", t: "fast" } ] },
  { key: "do", group: "DigitalOcean AMD Instinct MI300X", items: [
    { v: "do:Qwen/Qwen2.5-Coder-32B-Instruct", n: "Qwen 2.5 Coder 32B", t: "MI300X" },
    { v: "do:meta-llama/Llama-3.3-70B-Instruct", n: "Llama 3.3 70B", t: "MI300X" } ] },
  { key: "vllm", group: "DGX Spark - Local vLLM", items: [
    { v: "vllm:Qwen/Qwen3.8-Flash-Next", n: "Qwen 3.8 Flash Next", t: ":8000" },
    { v: "vllm:deepseek-ai/DeepSeek-V4.1-Flash", n: "DeepSeek V4.1 Flash", t: ":8000" } ] },
  { key: "flare", group: "DGX Spark - NVIDIA Flare", items: [
    { v: "flare:Qwen3.8-Flash-Next", n: "Qwen 3.8 Flash Next", t: ":8080" },
    { v: "flare:DeepSeek-V4.1-Flash", n: "DeepSeek V4.1 Flash", t: ":8080" } ] },
  { key: "ollama", group: "Local Ollama", items: [] },
];
const OLLAMA_DEFAULTS = ["raon-1-nano", "qwen2.5-coder:1.5b", "qwen2.5-coder:7b", "deepseek-r1:7b", "deepseek-r1:8b"];

let providers = {};
let state = loadState();
let busy = false, abortCtl = null;
let attachments = [];
let workspaceFiles = [], selectedFiles = new Set();
let palIndex = 0, palFlat = [];
let lastStatusGpu = { used: 0, total: 8192, gate: 0.091 };

function loadState() {
  try {
    const s = JSON.parse(localStorage.getItem("jupiter.v2") || "{}");
    return {
      convs: s.convs || [],
      activeId: s.activeId || null,
      model: s.model || "auto:d3",
      crt: s.crt || "color",
      drawer: s.drawer !== undefined ? !!s.drawer : true,
    };
  } catch {
    return { convs: [], activeId: null, model: "auto:d3", crt: "color", drawer: true };
  }
}
function save() {
  localStorage.setItem("jupiter.v2", JSON.stringify({ ...state, convs: state.convs.slice(0, 60) }));
}
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.remove("show"), 1900);
}

/* ---------- Conversations ("Cartridge Slots") ---------- */
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
  const buckets = { "ACTIVE SLOTS": [], "PREVIOUS 7 DAYS": [], "ARCHIVE": [] };
  state.convs.forEach((c) => {
    const age = now - c.created;
    (age < day ? buckets["ACTIVE SLOTS"] : age < 7 * day ? buckets["PREVIOUS 7 DAYS"] : buckets["ARCHIVE"]).push(c);
  });
  let html = "";
  for (const [label, list] of Object.entries(buckets)) {
    if (!list.length) continue;
    html += `<div class="conv-group">${label}</div>`;
    html += list.map((c) => `<div class="conv ${c.id === state.activeId ? "active" : ""}" onclick="openConv('${c.id}')">
      <span class="conv-title">${esc(c.title || "UNTITLED")}</span>
      <button class="conv-del" title="Eject slot" onclick="deleteConv('${c.id}', event)">&times;</button></div>`).join("");
  }
  $("conv-list").innerHTML = html || `<div class="conv-group">NO SESSIONS STORED</div>`;
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
  if (streaming && (text.match(/```/g) || []).length % 2 === 1) text += "\n```";
  text = text.replace(/```([\w+#.-]*)[^\n]*\n([\s\S]*?)```/g, (_, lang, code) => {
    codes.push({ lang: lang || "code", code: code.replace(/\n$/, "") });
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
      out.push(`<div class="codeblock"><div class="codebar"><span>${esc(b.lang)}</span><button onclick="copyCode(this)">COPY</button></div><pre><code>${esc(b.code)}</code></pre></div>`);
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
    if (!para.length) para.push(lines[i++]);
    out.push(`<p>${inline(para.join("<br/>"))}</p>`);
  }
  return out.join("");
}
function copyCode(btn) {
  navigator.clipboard.writeText(btn.closest(".codeblock").querySelector("code").innerText);
  btn.textContent = "COPIED"; setTimeout(() => (btn.textContent = "COPY"), 1200);
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
      <div class="welcome-stripes"><div class="ribbon-amd"></div><div class="ribbon-radeon"></div></div>
      <div class="welcome-body">
        <div class="welcome-kicker">
          <span class="kicker-amd">AMD RYZEN &amp; INSTINCT</span>
          <span class="kicker-sep">//</span>
          <span class="kicker-rad">RADEON TELEMETRY DECK</span>
        </div>
        <h1>Atari x AMD x Radeon Console</h1>
        <p>Host-side Zen 3 SIMD gating runs in 0.091 ms on the left wing while 27B-31B models execute on AMD Instinct via Token Lab on the right wing—keeping local studio VRAM at 0 MB.</p>
        <div class="telemetry-strip">
          <div class="tele-cell amd-side"><div class="tele-k">ZEN 3 GATE</div><div class="tele-v">0.091 ms</div></div>
          <div class="tele-cell amd-side"><div class="tele-k">SPECULATIVE MLP</div><div class="tele-v">5.37 &mu;s</div></div>
          <div class="tele-cell rad-side"><div class="tele-k">STUDIO VRAM</div><div class="tele-v">0 MB</div></div>
          <div class="tele-cell rad-side"><div class="tele-k">READY BUSES</div><div class="tele-v" id="welcome-buses">5 / 19</div></div>
        </div>
        <div class="starters">
          <button class="starter" onclick="starter('Review the selected repo files for bugs and security risks. Show exact fixes.')"><b>01 // Audit Staged Code</b><span>Select files in the Radeon bay and inspect</span></button>
          <button class="starter" onclick="starter('Explain step by step how MemoryOS keeps local VRAM at 0 MB while routing to AMD Instinct via Token Lab.')"><b>02 // Zero-VRAM Architecture</b><span>Trace the 0.091 ms Zen 3 gate to Instinct</span></button>
          <button class="starter" onclick="starter('Write focused Python unittest tests for the attached or selected module.')"><b>03 // Generate Unit Tests</b><span>Verify edge cases &amp; SQL/telemetry safety</span></button>
          <button class="starter" onclick="starter('Compare local 8 GB VRAM execution vs AMD Token Lab offload for a 31B model.')"><b>04 // Hardware Shootout</b><span>8 GB laptop GPU vs AMD Instinct MI300X</span></button>
        </div>
      </div>
    </div>`;
    return;
  }
  th.innerHTML = c.messages.map((m, idx) => messageHtml(m, idx, idx === c.messages.length - 1)).join("");
  scrollDown(true);
}
function messageHtml(m, idx, isLast) {
  if (m.role === "user") {
    const att = (m.attach || []).length ? `<div class="attach-line">ATTACHED: ${esc(m.attach.join(" · "))}</div>` : "";
    return `<div class="msg user" data-i="${idx}">
      <div class="who"><b>AMD // TX</b><span>COMMAND INPUT</span></div>
      <div class="user-text">${esc(m.content)}</div>${att}
      <div class="msg-tools"><button onclick="editMsg(${idx})">EDIT</button><button onclick="copyMsg(${idx})">COPY</button></div>
    </div>`;
  }
  const lbl = labelFor(m.model || state.model);
  const body = m.error
    ? `<div class="err-box"><b>CARTRIDGE FAULT</b>${esc(m.error)}</div>`
    : (m.content ? renderMarkdown(m.content, m.streaming) : `<span class="waiting">${m.streaming ? "RECEIVING STREAM..." : "(EMPTY RESPONSE)"}</span>`);
  const think = m.reasoning ? `<details class="think" ${m.streaming && !m.content ? "open" : ""}><summary>REASONING TRACE (${m.reasoning.length.toLocaleString()} CHARS)</summary><div>${esc(m.reasoning)}</div></details>` : "";
  const stat = m.stats ? `<span class="stat">${esc(m.stats)}</span>` : "";
  const tools = m.streaming ? "" : `<div class="msg-tools"><button onclick="copyMsg(${idx})">COPY</button>${isLast ? `<button onclick="retry()">RETRY</button><button onclick="openPalette(true)">SWAP CARTRIDGE &amp; RETRY</button>` : ""}${stat}</div>`;
  return `<div class="msg ai" data-i="${idx}">
    <div class="who"><span class="dot ${m.streaming ? "busy" : m.error ? "bad" : ""}"></span><b>RADEON // ${esc(lbl.n)}</b><span>${esc(m.provider || lbl.g)}</span></div>
    ${think}<div class="md ${m.streaming && m.content ? "caret" : ""}">${body}</div>${tools}
  </div>`;
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
function copyMsg(idx) { navigator.clipboard.writeText(activeConv().messages[idx].content || ""); toast("COPIED TO CLIPBOARD"); }
function editMsg(idx) {
  if (busy) return;
  const c = activeConv(); const m = c.messages[idx];
  $("prompt").value = m.content; autosize();
  c.messages = c.messages.slice(0, idx); save(); renderThread(); $("prompt").focus();
}
function starter(text) { $("prompt").value = text; autosize(); $("prompt").focus(); send(); }

/* ---------- Sending & Streaming ---------- */
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
  if (pstate && !pstate.ready) { toast(pstate.reason || "CARTRIDGE OFFLINE"); openPalette(); return; }

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
  const t0 = performance.now(); let firstTok = 0, pending = false;
  const paint = () => { if (!pending) { pending = true; requestAnimationFrame(() => { pending = false; updateLast(); }); } };
  try {
    const res = await fetch("/api/chat/stream", {
      method: "POST", headers: { "Content-Type": "application/json" }, signal: abortCtl.signal,
      body: JSON.stringify({ prompt: text, target: state.model, history, ...extras }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
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
        else if (ev === "delta") { ai.content += p.delta || ""; if (!firstTok) firstTok = performance.now(); paint(); }
        else if (ev === "notice") { ai.provider = p.message; paint(); }
        else if (ev === "error") { ai.error = p.error || "Unknown error"; }
      }
    }
    if (!ai.content && !ai.error) ai.error = "No response text received. Try another cartridge.";
  } catch (e) {
    if (e.name === "AbortError") { ai.stats = "STOPPED"; if (!ai.content) ai.content = "_Stopped._"; }
    else ai.error = e.message;
  } finally {
    const total = (performance.now() - t0) / 1000;
    if (!ai.stats && !ai.error) {
      const ttft = firstTok ? ((firstTok - t0) / 1000).toFixed(1) + "s TTFT · " : "";
      ai.stats = `${ttft}${total.toFixed(1)}s TOTAL`;
    }
    ai.streaming = false; abortCtl = null; setBusy(false);
    save(); updateLast();
  }
}
function setBusy(b) {
  busy = b;
  const s = $("send");
  s.classList.toggle("stop", b);
  s.innerHTML = b ? "STOP &#9632;" : "FIRE &uarr;";
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
      if (f.size > 2_000_000) { toast(`${f.name} EXCEEDS 2 MB`); continue; }
      r.onload = () => { attachments.push({ kind: "file", name: f.name, content: String(r.result) }); renderChips(); };
      r.readAsText(f);
    }
  }
}
function renderChips() {
  const chips = attachments.map((a, i) => `<span class="chip">${a.kind === "image" ? `<img src="${a.content}" alt=""/>` : ""}${esc(a.name)}<button onclick="removeAttachment(${i})">&times;</button></span>`);
  selectedFiles.forEach((p) => chips.push(`<span class="chip">REPO: ${esc(p.split("/").pop())}<button onclick="toggleFile('${esc(p).replace(/'/g, "\\'")}')">&times;</button></span>`));
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
  catch { $("files").innerHTML = `<div class="file">Workspace scan failed</div>`; }
}
function renderFiles() {
  const q = $("file-q").value.toLowerCase();
  const list = workspaceFiles.filter((f) => !q || f.path.toLowerCase().includes(q)).slice(0, 150);
  $("files").innerHTML = list.map((f) => {
    const p = esc(f.path), on = selectedFiles.has(f.path);
    return `<label class="file"><input type="checkbox" ${on ? "checked" : ""} onchange="toggleFile('${p.replace(/'/g, "\\'")}')"/><span class="p" title="${p}">${p}</span><span class="s">${f.size_kb}K</span></label>`;
  }).join("") || `<div class="file">No matching files</div>`;
  $("staged").textContent = `${selectedFiles.size} STAGED`;
  $("ctx-tool").textContent = selectedFiles.size ? `REPO FILES (${selectedFiles.size})` : "REPO FILES";
}
function toggleFile(p) { selectedFiles.has(p) ? selectedFiles.delete(p) : selectedFiles.add(p); renderFiles(); renderChips(); }

/* ---------- Cartridge Palette (Ctrl+K) ---------- */
async function loadModels(announce) {
  try {
    const d = await (await fetch("/api/models")).json();
    providers = d.providers || {};
    const installed = d.ollama_installed || [];
    const names = installed.length ? installed : OLLAMA_DEFAULTS;
    CATALOG.find((g) => g.key === "ollama").items = names.map((n) => ({ v: "ollama:" + n, n, t: installed.length ? "installed" : "offline" }));
    renderProviders(); setModel(state.model, true);
    let readyCnt = 0, totalCnt = 0;
    CATALOG.forEach((g) => {
      const ok = (providers[g.key] || { ready: g.key === "auto" }).ready;
      totalCnt += g.items.length;
      if (ok) readyCnt += g.items.length;
    });
    const wb = $("welcome-buses"); if (wb) wb.textContent = `${readyCnt} / ${totalCnt}`;
    if (announce) toast("BUS MATRIX PROBED");
  } catch {}
}
function renderProviders() {
  $("prov-list").innerHTML = CATALOG.filter((g) => g.key !== "auto").map((g) => {
    const p = providers[g.key] || {};
    return `<div class="kv"><span>${esc(g.group.split(" (")[0])}</span><span style="color:${p.ready ? "var(--ok)" : "var(--muted)"}" title="${esc(p.reason || "")}">${p.ready ? "ONLINE" : "OFFLINE"}</span></div>`;
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
    html += `<div class="pal-group"><span>${esc(g.group)}</span>${p.ready ? "" : `<em>${esc(p.reason || "OFFLINE")}</em>`}</div>`;
    for (const it of items) {
      const k = palFlat.length; palFlat.push({ it, ready: p.ready });
      html += `<button class="pal-item ${it.v === state.model ? "sel" : ""} ${p.ready ? "" : "off"} ${k === palIndex ? "kb" : ""}" onclick="pickModel(${k})">
        <span class="dot ${p.ready ? "" : "bad"}"></span><span class="n">${esc(it.n)}</span><span class="t">${esc(it.t)}</span></button>`;
    }
  }
  $("pal-list").innerHTML = html || `<div class="pal-group">NO MATCHING CARTRIDGES</div>`;
  $("pal-count").textContent = `${palFlat.filter((x) => x.ready).length} READY / ${palFlat.length}`;
}
function pickModel(k) {
  const entry = palFlat[k]; if (!entry) return;
  if (!entry.ready) { toast("OFFLINE: " + ((providers[entry.it.v.split(":")[0]] || {}).reason || "NOT CONFIGURED")); return; }
  setModel(entry.it.v); closePalette();
  if (retryMode) { retryMode = false; retry(entry.it.v); }
}
function setModel(v, silent) {
  state.model = v; save();
  const l = labelFor(v); $("model-name").textContent = l.n; $("model-prov").textContent = v.startsWith("auto") ? "d3 router" : l.g.split(" (")[0];
  const p = providers[v.split(":")[0]];
  $("model-dot").className = "dot " + (p && !p.ready ? "bad" : "");
  if (!silent) toast(`CARTRIDGE LOADED: ${l.n}`);
}
$("pal-q").addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown") { palIndex = Math.min(palFlat.length - 1, palIndex + 1); renderPalette(); e.preventDefault(); }
  else if (e.key === "ArrowUp") { palIndex = Math.max(0, palIndex - 1); renderPalette(); e.preventDefault(); }
  else if (e.key === "Enter") { pickModel(palIndex); e.preventDefault(); }
  else if (e.key === "Escape") closePalette();
});

/* ---------- Hardware Status ---------- */
async function loadStatus() {
  try {
    const d = await (await fetch("/api/status")).json();
    const g = d.gpu || {}, h = d.health || {}, pol = d.policy || {};
    const used = Math.round(g.used_vram_mb || 0), total = Math.round(g.total_vram_mb || 0);
    $("hw-name").textContent = g.device_name || "CPU ONLY";
    $("hw-vram").textContent = total ? `${used.toLocaleString()} / ${total.toLocaleString()} MB` : "--";
    $("hw-temp").textContent = g.temperature_c != null ? `${Math.round(g.temperature_c)}°C · ${Math.round(g.utilization_pct || 0)}%` : "--";
    $("hw-gate").textContent = `${pol.cpu_gate_ms ?? 0.091} ms`;
    $("foot-gpu").textContent = (g.device_name || "CPU").replace(/NVIDIA GeForce |AMD Radeon /, "").replace(" Laptop GPU", "");
    $("foot-vram").textContent = `${used.toLocaleString()} MB`;
    $("vram-pill").textContent = `STUDIO 0 MB · GPU ${used.toLocaleString()} MB`;
    if (h.score != null) {
      $("h-score").textContent = h.score; $("h-grade").textContent = `GRADE ${h.grade}`;
      $("h-status").textContent = (h.status || "healthy").toUpperCase();
      $("h-bar").style.width = h.score + "%";
    }
  } catch {}
}

/* ---------- Atari Toggle Switches ---------- */
function toggleCrt() {
  state.crt = state.crt === "color" ? "bw" : "color";
  document.documentElement.dataset.crt = state.crt;
  $("crt-label").textContent = state.crt === "color" ? "COLOR" : "B&W CRT";
  save();
}
function toggleDrawer(force) {
  state.drawer = force === true ? true : !state.drawer;
  $("app").classList.toggle("no-drawer", !state.drawer);
  $("drawer-btn").classList.toggle("on", state.drawer);
  save();
}
function toggleRail() { $("app").classList.toggle("no-rail"); }
function autosize() { const t = $("prompt"); t.style.height = "auto"; t.style.height = Math.min(220, t.scrollHeight) + "px"; }
$("prompt").addEventListener("input", autosize);
$("prompt").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); } });
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); }
  else if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "o") { e.preventDefault(); newChat(); }
  else if (e.key === "Escape" && busy) stop();
});

/* ---------- Boot ---------- */
document.documentElement.dataset.crt = state.crt;
$("crt-label").textContent = state.crt === "color" ? "COLOR" : "B&W CRT";
$("app").classList.toggle("no-drawer", !state.drawer);
$("drawer-btn").classList.toggle("on", state.drawer);
state.convs.forEach((c) => c.messages.forEach((m) => { if (m.streaming) { m.streaming = false; if (!m.content) m.error = "Interrupted by reload."; } }));
renderConvs(); renderThread(); setModel(state.model, true);
loadModels(); loadStatus(); loadFiles();
setInterval(loadStatus, 5000); setInterval(loadModels, 30000);
$("prompt").focus();
</script>
</body>
</html>
"""

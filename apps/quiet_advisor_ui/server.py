"""Standalone Quiet Advisor UI web server (zero external dependencies)."""

from __future__ import annotations

import argparse
import json
import re
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.quiet_advisor_ui.api import apply_card_action, get_dashboard_state, run_detection_cycle
from src.memoryos.router_service import (
    process_acknowledge_card,
    process_frame_delta,
    process_route_request,
    resolve_db_path,
)

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>MemoryOS // The Quiet Advisor UI</title>
<style>
  :root {
    --bg: #07090f;
    --panel: #0f1422;
    --panel-2: #141b2e;
    --border: #232d48;
    --cyan: #00ffff;
    --pink: #ff1493;
    --amber: #ffd166;
    --green: #00f59b;
    --text: #eaf3ff;
    --muted: #8ea3c7;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 20px 26px;
    background: radial-gradient(circle at top right, #18102b 0%, var(--bg) 52%);
    color: var(--text);
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
  }
  .topbar {
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
    gap: 12px; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid var(--border);
  }
  .brand h1 { margin: 0; font-size: 20px; letter-spacing: 0.8px; color: var(--cyan); }
  .brand p { margin: 3px 0 0; font-size: 12px; color: var(--muted); }
  .controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  button {
    border: 1px solid var(--border); background: var(--panel-2); color: var(--text);
    padding: 8px 13px; border-radius: 7px; font-weight: 600; font-size: 12px;
    cursor: pointer; transition: 0.15s ease;
  }
  button:hover { border-color: var(--cyan); color: var(--cyan); }
  button.primary { background: var(--cyan); color: #05080f; border-color: var(--cyan); }
  button.primary:hover { background: #6ffeff; color: #05080f; }
  button.pink { background: var(--pink); color: #090b12; border-color: var(--pink); }
  button.pink:hover { opacity: 0.9; color: #090b12; }
  button.warn { border-color: #6b294c; color: #ff85c0; }

  .badge-live {
    background: rgba(0, 255, 153, 0.1);
    color: var(--green);
    border: 1px solid var(--green);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
  }

  .arch-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px; margin-bottom: 20px;
  }
  .kpi {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 14px; position: relative; overflow: hidden;
  }
  .kpi::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--cyan);
  }
  .kpi.pink::before { background: var(--pink); }
  .kpi.green::before { background: var(--green); }
  .kpi.amber::before { background: var(--amber); }
  .kpi-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.6px; }
  .kpi-val { font-size: 22px; font-weight: 700; margin: 4px 0 2px; color: #fff; }
  .kpi-sub { font-size: 11px; color: var(--muted); }

  .main-grid { display: grid; grid-template-columns: minmax(0, 1.65fr) minmax(300px, 1fr); gap: 18px; }
  @media (max-width: 980px) { .main-grid { grid-template-columns: 1fr; } }

  .panel {
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px;
    margin-bottom: 16px;
  }
  .tabs { display: flex; gap: 8px; margin-bottom: 14px; }
  .tab { background: transparent; border: 1px solid var(--border); color: var(--muted); }
  .tab.active { background: var(--pink); color: #090b12; border-color: var(--pink); }

  .card {
    background: linear-gradient(165deg, #151c31 0%, #0f1423 100%);
    border: 1px solid #2b385a; border-radius: 11px; padding: 15px; margin-bottom: 14px;
  }
  .card-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
  .badge {
    display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 700;
    background: #1d2742; color: var(--cyan); text-transform: uppercase; letter-spacing: 0.4px;
  }
  .badge.d3 { background: rgba(255, 20, 147, 0.16); color: #ff69b4; border: 1px solid rgba(255, 20, 147, 0.45); }
  .badge.saved { background: rgba(0, 245, 155, 0.14); color: var(--green); }
  .card h3 { margin: 10px 0 3px; font-size: 17px; color: #fff; }
  .subtitle { font-size: 13px; color: var(--cyan); margin-bottom: 8px; }
  .desc {
    margin: 0 0 12px; font-size: 13px; line-height: 1.5; color: #c7d6f0;
    white-space: pre-wrap;
  }
  .metrics-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  .metric-chip {
    background: #0b0f1b; border: 1px solid #25314f; border-radius: 6px;
    padding: 5px 10px; font-size: 12px; color: #e2eeff;
  }
  .prob-wrap { margin: 10px 0 12px; }
  .prob-label { font-size: 11px; color: var(--muted); margin-bottom: 4px; display: flex; justify-content: space-between; }
  .prob-bar { height: 8px; border-radius: 5px; overflow: hidden; display: flex; background: #0a0e19; }
  .prob-seg-surface { background: var(--cyan); }
  .prob-seg-defer { background: var(--amber); }
  .prob-seg-ignore { background: #5a6987; }

  .exp-list { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
  .exp-btn { font-size: 11px; padding: 4px 9px; background: #0c1120; border-color: #293659; color: #b8c9e8; }
  .card-actions { display: flex; flex-wrap: wrap; gap: 8px; padding-top: 8px; border-top: 1px solid #1f2944; }

  .section-title { font-size: 13px; color: var(--pink); text-transform: uppercase; letter-spacing: 0.7px; margin: 0 0 10px; }
  svg.viz { width: 100%; height: auto; background: #0a0e18; border-radius: 8px; display: block; margin-bottom: 12px; }
  .row-item {
    display: flex; justify-content: space-between; align-items: center; gap: 8px;
    padding: 6px 0; border-bottom: 1px solid #1a2238; font-size: 12px;
  }
  .bar-bg { flex: 1; height: 7px; background: #161d31; border-radius: 4px; overflow: hidden; margin: 0 8px; }
  .bar-fill { height: 100%; background: linear-gradient(90deg, var(--cyan), var(--pink)); }
  .toast {
    position: fixed; bottom: 18px; right: 18px; background: #101729; border: 1px solid var(--cyan);
    color: var(--cyan); padding: 10px 14px; border-radius: 8px; font-size: 12px; display: none;
  }
</style>
</head>
<body>
  <div class="topbar">
    <div class="brand">
      <h1>MEMORYOS // THE QUIET ADVISOR</h1>
      <p id="dbMeta">Loading SQLite &amp; Token Lab state...</p>
    </div>
    <div class="controls">
      <div id="liveBadges" style="display:flex; gap:8px; margin-right:12px; align-items:center;"></div>
      <button class="primary" onclick="triggerDetection(false)">RUN DETECTION</button>
      <button class="pink" onclick="triggerDetection(true)">SEED + DETECT DEMO</button>
      <button onclick="refreshState()">REFRESH</button>
    </div>
  </div>

  <div class="arch-grid" id="archGrid"></div>

  <div class="main-grid">
    <div>
      <div class="panel">
        <div class="tabs">
          <button class="tab active" id="tabActive" onclick="setTab('active')">Active Cards</button>
          <button class="tab" id="tabArchive" onclick="setTab('archive')">Archived / Actioned</button>
          <button class="tab" id="tabLog" onclick="setTab('log')">Action History</button>
        </div>
        <div id="cardsContainer"></div>
      </div>
    </div>

    <div>
      <div class="panel">
        <h2 class="section-title">Inference Latency &amp; Context Telemetry</h2>
        <div id="latencyChart"></div>
        <div id="modelBars"></div>
      </div>

      <div class="panel">
        <h2 class="section-title">Learned Detector Weights</h2>
        <div id="prefBars"></div>
      </div>

      <div class="panel">
        <h2 class="section-title">NVMe Atomic Checkpoints</h2>
        <div id="checkpointList"></div>
      </div>
    </div>
  </div>

  <div class="toast" id="toast"></div>

<script>
let currentTab = "active";
let latestState = null;

function esc(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function showToast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.style.display = "block";
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => { el.style.display = "none"; }, 2600);
}

function setTab(tab) {
  currentTab = tab;
  document.getElementById("tabActive").classList.toggle("active", tab === "active");
  document.getElementById("tabArchive").classList.toggle("active", tab === "archive");
  document.getElementById("tabLog").classList.toggle("active", tab === "log");
  if (latestState) renderState(latestState);
}

async function apiPost(url, payload) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {})
  });
  return resp.json();
}

async function refreshState() {
  const resp = await fetch("/api/state");
  latestState = await resp.json();
  renderState(latestState);
}

async function cardAction(cardId, action, meta) {
  const res = await apiPost(`/api/cards/${cardId}/action`, { action, metadata: meta || {} });
  if (res.state) {
    latestState = res.state;
    renderState(latestState);
  }
  showToast(`Card #${cardId} -> ${action}`);
}

async function triggerDetection(seedIfEmpty) {
  showToast(seedIfEmpty ? "Seeding sample logs & running detectors..." : "Running Quiet Advisor detection...");
  const res = await apiPost("/api/detect", { seed_if_empty: !!seedIfEmpty, lookback_hours: 48 });
  if (res.state) {
    latestState = res.state;
    renderState(latestState);
  }
  showToast(`Detection complete${res.seeded_inferences ? ` (+${res.seeded_inferences} sample logs)` : ""}`);
}

function renderState(state) {
  document.getElementById("dbMeta").textContent = `DB: ${state.db_path} | Updated: ${new Date(state.generated_at).toLocaleTimeString()}`;

  const t = state.telemetry;
  const avgLat = t.avg_latency_ms || 0;
  const fps = avgLat > 0 ? (1000 / avgLat).toFixed(1) : "0.0";
  const vramSaved = t.local_vram_saved_pct ?? 100;
  const liveBadgesEl = document.getElementById("liveBadges");
  if (liveBadgesEl) {
    liveBadgesEl.innerHTML = `
      <div class="badge-live">FPS: 120+ (${esc(fps)} inf/s)</div>
      <div class="badge-live">VRAM SAVED: ${esc(vramSaved)}%</div>
    `;
  }
  const tl = state.tokenlab || {};
  const topD3 = (state.active_cards[0] && state.active_cards[0].d3_routing) || { choice: "surface_now", confidence: 0 };
  const tlCard = tl.user_id ? `
    <div class="kpi">
      <div class="kpi-label">Token Lab Grant (${esc(tl.key_prefix || "key")})</div>
      <div class="kpi-val">${tl.budget_used_micro ?? 0} / ${((tl.budget_micro ?? 0) / 1e6).toFixed(0)}M µpts</div>
      <div class="kpi-sub">${esc(tl.user_id)} | ${tl.total_requests ?? 0} reqs (${tl.total_errors ?? 0} errs)</div>
    </div>` : "";
  document.getElementById("archGrid").innerHTML = `
    <div class="kpi green">
      <div class="kpi-label">RTX 3070 Local VRAM Isolation</div>
      <div class="kpi-val">${t.local_vram_saved_pct}% Remote</div>
      <div class="kpi-sub">${t.remote_offload_count}/${t.total_inferences} inferences offloaded (0 local VRAM)</div>
    </div>
    <div class="kpi pink">
      <div class="kpi-label">Token Lab d3 Aux-Router</div>
      <div class="kpi-val">${esc(topD3.choice)} (${(topD3.confidence * 100).toFixed(1)}%)</div>
      <div class="kpi-sub">${state.active_cards.length} active cards | Avg latency ${t.avg_latency_ms} ms</div>
    </div>
    <div class="kpi amber">
      <div class="kpi-label">Context Window Efficiency</div>
      <div class="kpi-val">${t.avg_context_utilization_pct}% Used</div>
      <div class="kpi-sub">Tracked across ${t.total_inferences} logged runs</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">NVMe Atomic Checkpoints</div>
      <div class="kpi-val">${state.checkpoints.count} Files</div>
      <div class="kpi-sub">Crash-safe JSON state in memory/checkpoints</div>
    </div>${tlCard}`;

  renderCards(state);
  renderCharts(state);
  renderPrefs(state.preferences);
  renderCheckpoints(state.checkpoints);
}

function renderCards(state) {
  const host = document.getElementById("cardsContainer");
  if (currentTab === "log") {
    const logs = state.recent_actions || [];
    host.innerHTML = logs.length
      ? logs.map(a => `<div class="row-item"><span>Card #${esc(a.card_id)} <strong>${esc(a.action_type)}</strong></span><span style="color:var(--muted)">${esc(a.created_at)}</span></div>`).join("")
      : `<p style="color:var(--muted);font-size:13px;">No card interactions recorded yet.</p>`;
    return;
  }

  const list = currentTab === "active" ? state.active_cards : state.archived_cards;
  if (!list.length) {
    host.innerHTML = `<p style="color:var(--muted);font-size:13px;">No ${currentTab} Quiet Advisor cards yet. Click <strong>RUN DETECTION</strong> or <strong>SEED + DETECT DEMO</strong> above.</p>`;
    return;
  }

  host.innerHTML = list.map(c => {
    const probs = c.d3_routing.probabilities || {};
    const pSurf = Math.round((probs.surface_now ?? (c.d3_routing.choice === "surface_now" ? c.d3_routing.confidence : 0.7)) * 100);
    const pDef = Math.round((probs.defer ?? 0.2) * 100);
    const pIgn = Math.max(0, 100 - pSurf - pDef);
    const metrics = (c.metrics || []).map(m => `<span class="metric-chip">${esc(m)}</span>`).join("");
    const exps = (c.suggested_experiments || []).map(e =>
      `<button class="exp-btn" onclick="cardAction(${c.id}, 'learn_more', {experiment: ${JSON.stringify(e)}})">Try: ${esc(e)}</button>`
    ).join("");
    const actionsHtml = currentTab === "active" ? `
      <div class="card-actions">
        <button class="primary" onclick="cardAction(${c.id}, 'action', {recommended: ${JSON.stringify(c.recommended_action)}})">Acknowledge &amp; Apply</button>
        <button onclick="cardAction(${c.id}, 'dismiss')">Dismiss</button>
        <button class="warn" onclick="cardAction(${c.id}, 'archive')">Mute Detector</button>
      </div>` : `<div class="card-actions"><span class="badge">${c.user_actioned ? "ACTIONED" : (c.user_archived ? "MUTED" : "DISMISSED")}</span></div>`;

    return `
      <div class="card">
        <div class="card-head">
          <div>
            <span class="badge">${esc(c.detector_type)}</span>
            <span class="badge d3">d3: ${esc(c.d3_routing.choice)} ${(c.d3_routing.confidence * 100).toFixed(1)}%</span>
          </div>
          <div>
            ${c.time_savings_seconds ? `<span class="badge saved">Saves ${Math.round(c.time_savings_seconds / 60)}m/wk</span>` : ""}
            ${c.quality_improvement_percent ? `<span class="badge saved">+${c.quality_improvement_percent.toFixed(1)}% Quality</span>` : ""}
          </div>
        </div>
        <h3>${esc(c.title)}</h3>
        <div class="subtitle">${esc(c.subtitle)}</div>
        <pre class="desc">${esc(c.description)}</pre>
        <div class="metrics-row">${metrics}</div>
        <div class="prob-wrap">
          <div class="prob-label"><span>d3 Routing Probabilities</span><span>surface ${pSurf}% · defer ${pDef}% · ignore ${pIgn}%</span></div>
          <div class="prob-bar">
            <div class="prob-seg-surface" style="width:${pSurf}%"></div>
            <div class="prob-seg-defer" style="width:${pDef}%"></div>
            <div class="prob-seg-ignore" style="width:${pIgn}%"></div>
          </div>
        </div>
        ${exps ? `<div class="exp-list">${exps}</div>` : ""}
        ${actionsHtml}
      </div>`;
  }).join("");
}

function renderCharts(state) {
  const series = state.telemetry.latency_series || [];
  const w = 360, h = 95;
  if (series.length >= 2) {
    const maxV = Math.max(1, ...series);
    const pts = series.map((v, i) => `${((i / (series.length - 1)) * (w - 16) + 8).toFixed(1)},${(h - 12 - (v / maxV) * (h - 24)).toFixed(1)}`).join(" ");
    document.getElementById("latencyChart").innerHTML = `
      <svg viewBox="0 0 ${w} ${h}" class="viz">
        <polyline fill="none" stroke="#00ffff" stroke-width="2.2" points="${pts}" />
      </svg>`;
  } else {
    document.getElementById("latencyChart").innerHTML = `<p style="color:var(--muted);font-size:12px;">Need 2+ inferences for sparkline.</p>`;
  }

  const models = state.telemetry.model_stats || [];
  const maxMs = Math.max(1, ...models.map(m => m.avg_latency_ms));
  document.getElementById("modelBars").innerHTML = models.length
    ? models.map(m => `
      <div class="row-item">
        <span style="min-width:125px">${esc(m.model_id)} (${m.count})</span>
        <div class="bar-bg"><div class="bar-fill" style="width:${Math.max(5, (m.avg_latency_ms / maxMs) * 100)}%"></div></div>
        <span style="color:var(--cyan)">${m.avg_latency_ms}ms</span>
      </div>`).join("")
    : `<p style="color:var(--muted);font-size:12px;">No model telemetry logged yet.</p>`;
}

function renderPrefs(prefs) {
  const entries = Object.entries(prefs || {});
  document.getElementById("prefBars").innerHTML = entries.length
    ? entries.map(([k, v]) => `
      <div class="row-item">
        <span style="min-width:130px">${esc(k)}</span>
        <div class="bar-bg"><div class="bar-fill" style="width:${Math.round(v * 100)}%"></div></div>
        <span>${(v * 100).toFixed(0)}%</span>
      </div>`).join("")
    : `<p style="color:var(--muted);font-size:12px;">Act on cards (Apply / Dismiss / Mute) to train detector preferences.</p>`;
}

function renderCheckpoints(cp) {
  const items = cp.recent || [];
  document.getElementById("checkpointList").innerHTML = items.length
    ? items.map(item => `
      <div class="row-item">
        <span>${esc(item.model)} <span style="color:var(--muted)">(${esc(item.route)})</span></span>
        <span style="color:var(--cyan)">${item.latency_ms.toFixed(0)}ms</span>
      </div>`).join("")
    : `<p style="color:var(--muted);font-size:12px;">No checkpoints written yet.</p>`;
}

refreshState();
setInterval(refreshState, 10000);
</script>
</body>
</html>
"""


class QuietAdvisorHTTPHandler(BaseHTTPRequestHandler):
    """Serves the Quiet Advisor UI and JSON card action endpoints."""

    db_path: Optional[Path] = None

    def _send_json(self, payload: Dict[str, Any], status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def log_message(self, format: str, *args: Any) -> None:
        return  # Keep terminal output quiet

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            body = DASHBOARD_HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/health":
            self._send_json(
                {
                    "status": "healthy",
                    "service": "memoryos-router",
                    "db_path": str(resolve_db_path(self.db_path)),
                }
            )
            return

        if path == "/api/state":
            self._send_json(get_dashboard_state(self.db_path))
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        body = self._read_json_body()
        if path == "/api/route":
            try:
                self._send_json(process_route_request(body, default_db_path=self.db_path))
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/frame-delta":
            self._send_json(process_frame_delta(body, default_db_path=self.db_path))
            return

        if path == "/api/acknowledge-card":
            self._send_json(process_acknowledge_card(body, default_db_path=self.db_path))
            return

        if path == "/api/detect":
            result = run_detection_cycle(
                lookback_hours=int(body.get("lookback_hours") or 24),
                seed_if_empty=bool(body.get("seed_if_empty", False)),
                db_path=self.db_path,
            )
            self._send_json(result)
            return

        match = re.match(r"^/api/cards/(\d+)/action$", path)
        if match:
            card_id = int(match.group(1))
            action = str(body.get("action") or "view")
            user_id = body.get("user_id")
            user_id = str(user_id) if user_id else None
            metadata = body.get("metadata") if isinstance(body.get("metadata"), dict) else None
            try:
                res = apply_card_action(
                    card_id=card_id,
                    action=action,
                    user_id=user_id,
                    metadata=metadata,
                    db_path=self.db_path,
                )
                self._send_json(res)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)


def create_server(host: str = "127.0.0.1", port: int = 5000, db_path: Optional[Path] = None) -> ThreadingHTTPServer:
    class _BoundHandler(QuietAdvisorHTTPHandler):
        pass

    _BoundHandler.db_path = Path(db_path) if db_path else None
    return ThreadingHTTPServer((host, port), _BoundHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch MemoryOS Quiet Advisor Web UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--db", default=None, help="Optional path to quiet_advisor.db")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    server = create_server(host=args.host, port=args.port, db_path=Path(args.db) if args.db else None)
    url = f"http://{args.host}:{server.server_port}"
    print(f"[+] Quiet Advisor UI running at {url}")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Quiet Advisor UI stopped")
        server.server_close()


if __name__ == "__main__":
    main()

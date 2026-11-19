"""Interactive Hugging Face Space Demo for MemoryOS // Jupiter Studio v1.0.0-RC1.

Runs the real pure-Python SpeculativeOffloadModel (4->8->1 MLP) and QuietAdvisorEngine
detectors (ThermalThrottlingDetector, VRAMThrashingDetector, ContextWasteDetector,
and compute_workstation_health) live in the browser.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Tuple

import gradio as gr

from quiet_advisor_detectors import (
    InferenceLog,
    QuietAdvisorEngine,
    compute_workstation_health,
)
from speculative_offload import SpeculativeOffloadModel

HERE = Path(__file__).resolve().parent
MODEL = SpeculativeOffloadModel.load(HERE / "speculative_offload_v1.json")
ENGINE = QuietAdvisorEngine()


def run_speculative_demo(
    prompt: str,
    mse_delta_norm: float,
    context_util: float,
    secs_since_offload: float,
    model_switch_rate: float,
    has_image: bool,
) -> Tuple[str, str]:
    """Execute the real 4->8->1 SpeculativeOffloadModel forward pass and preview routing."""
    features = {
        "mse_delta_norm": float(mse_delta_norm),
        "context_utilization": float(context_util),
        "secs_since_offload": float(secs_since_offload),
        "model_switch_rate": float(model_switch_rate),
    }

    # Measure 100 forward passes for stable microsecond timing
    t0 = time.perf_counter_ns()
    p_offload = 0.0
    action = "digest"
    for _ in range(100):
        p_offload = MODEL.predict_proba(features)
        action = MODEL.decide(features)
    avg_us = (time.perf_counter_ns() - t0) / 100.0 / 1000.0

    # Heuristic d3 tier preview matching Jupiter Studio's frontier routing
    lower = (prompt or "").lower()
    if has_image or any(k in lower for k in ("screenshot", "image", "ui", "architecture", "design")):
        target_model = "Gemma-4-31B-IT (AMD Token Lab)"
        vram_saved_gb = 18.5
    elif len(prompt or "") > 1500 or any(k in lower for k in ("log", "transcript", "audit", "entire")):
        target_model = "DeepSeek-V4.1-Flash (1M Context)"
        vram_saved_gb = 14.0
    else:
        target_model = "Qwen3.8-27B (Code & Reasoning)"
        vram_saved_gb = 16.2

    summary = (
        f"### Speculative Decision: `{action.upper()}`\n\n"
        f"| Telemetry Metric | Measured Value |\n"
        f"| :--- | :--- |\n"
        f"| **Offload Probability `P(offload)`** | **`{p_offload * 100:.1f}%`** |\n"
        f"| **MLP Forward Pass Latency (avg of 100)** | **`{avg_us:.2f} μs`** |\n"
        f"| **Predicted `d3` Execution Target** | **`{target_model}`** |\n"
        f"| **Local Studio VRAM Consumed** | **`0 MB` (saves ~`{vram_saved_gb} GB` vs local)** |\n"
    )

    detail = (
        f"Input features -> mse_delta_norm={mse_delta_norm:.2f}, "
        f"context_utilization={context_util:.2f}, "
        f"secs_since_offload={secs_since_offload:.2f}, "
        f"model_switch_rate={model_switch_rate:.2f}\n"
        f"Thresholds -> tau_hi={MODEL.tau_hi}, tau_lo={MODEL.tau_lo}"
    )
    return summary, detail


def run_advisor_demo(
    gpu_temp_c: float,
    vram_used_mb: int,
    vram_total_mb: int,
    ctx_provided: int,
    ctx_used: int,
    error_pct: float,
) -> str:
    """Synthesize a 10-run telemetry window and run QuietAdvisorEngine + Workstation Health."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    num_runs = 10
    num_errors = round((error_pct / 100.0) * num_runs)

    inferences = []
    for i in range(num_runs):
        # Include 2 cool baseline runs so ThermalThrottlingDetector can measure throughput drop
        is_cool = i < 2 and gpu_temp_c >= 82.0
        temp = 58.0 if is_cool else float(gpu_temp_c)
        tps = 72.0 if is_cool else (42.0 if gpu_temp_c >= 82.0 else 65.0)
        inferences.append(
            InferenceLog(
                timestamp=now - timedelta(minutes=(num_runs - i) * 5),
                model_id="local-31b" if vram_used_mb >= 5500 else "Gemma-4-31B-IT",
                context_tokens_provided=int(ctx_provided),
                context_tokens_used=int(min(ctx_used, ctx_provided)),
                time_to_first_token_ms=140.0,
                total_latency_ms=1200.0 if vram_used_mb >= 5500 else 465.0,
                tokens_per_second=tps,
                gpu_utilization_percent=min(100.0, (vram_used_mb / max(1, vram_total_mb)) * 100.0),
                gpu_temperature_celsius=temp,
                gpu_memory_used_mb=int(vram_used_mb),
                error_flag=(i >= num_runs - num_errors),
            )
        )

    health = compute_workstation_health(inferences, vram_capacity_mb=int(vram_total_mb))
    insights = ENGINE.detect_patterns(inferences)
    comps = health["components"]

    lines = [
        f"## Workstation Health: `{health['score']} / 100` — **Grade {health['grade']}** (`{health['status'].upper()}`)",
        "",
        "| Axis | Score |",
        "| :--- | :--- |",
        f"| VRAM Headroom | `{comps['vram_headroom']}%` |",
        f"| Thermal Headroom | `{comps['thermal_headroom']}%` |",
        f"| Context Efficiency | `{comps['context_efficiency']}%` |",
        f"| Reliability | `{comps['reliability']}%` |",
        "",
        "### Active Quiet Advisor Cards",
    ]
    if not insights:
        lines.append("No hardware or efficiency issues detected — workstation operating within nominal bounds.")
    else:
        for ins in insights:
            lines.append(f"- **{ins.title}** (`{ins.detector_type.value}`) — {ins.subtitle}")
            lines.append(f"  - *Recommended action:* `{ins.recommended_action}`")
    return "\n".join(lines)


with gr.Blocks(title="MemoryOS // Jupiter Studio Interactive Demo", theme=gr.themes.Base()) as demo:
    gr.Markdown(
        "# MemoryOS // Jupiter Studio `v1.0.0-RC1`\n"
        "**Not another chatbot. An AI workstation.** Test the real pure-Python `SpeculativeOffloadModel` MLP "
        "and `QuietAdvisorEngine` detectors live below — "
        "[GitHub](https://github.com/JupiterIsland/memoryos) · "
        "[Download Standalone Builds](https://github.com/JupiterIsland/memoryos/releases/tag/v1.0.0-rc1)"
    )

    with gr.Tab("1. Speculative Offload MLP (5.37 μs)"):
        prompt_in = gr.Textbox(
            label="Draft Prompt",
            value="Audit quiet_advisor_scheduler.py for SQL injection and add circuit breakers.",
            lines=2,
        )
        with gr.Row():
            mse_in = gr.Slider(0.0, 1.0, value=0.72, step=0.02, label="MSE Frame / Complexity Delta")
            ctx_in = gr.Slider(0.0, 1.0, value=0.65, step=0.02, label="Context Utilization")
            sec_in = gr.Slider(0.0, 1.0, value=0.45, step=0.02, label="Normalized Secs Since Offload")
            sw_in = gr.Slider(0.0, 1.0, value=0.20, step=0.02, label="Model Switch Rate")
        img_in = gr.Checkbox(label="Screenshot / Vision Attachment Included", value=False)
        btn_spec = gr.Button("Run Speculative MLP Forward Pass", variant="primary")
        out_spec = gr.Markdown()
        out_detail = gr.Textbox(label="Feature Vector & Calibration", interactive=False)
        btn_spec.click(
            run_speculative_demo,
            inputs=[prompt_in, mse_in, ctx_in, sec_in, sw_in, img_in],
            outputs=[out_spec, out_detail],
        )

    with gr.Tab("2. Quiet Advisor & Workstation Health"):
        with gr.Row():
            temp_in = gr.Slider(40, 95, value=86, step=1, label="GPU Temperature (°C)")
            vram_used_in = gr.Slider(0, 8192, value=6800, step=128, label="Local VRAM Used (MB)")
            vram_tot_in = gr.Slider(4096, 24576, value=8192, step=1024, label="GPU VRAM Capacity (MB)")
        with gr.Row():
            ctx_prov_in = gr.Slider(1024, 32768, value=8192, step=1024, label="Context Provided (tokens)")
            ctx_used_in = gr.Slider(128, 32768, value=1200, step=128, label="Context Used (tokens)")
            err_in = gr.Slider(0, 100, value=0, step=10, label="Error Rate (%)")
        btn_adv = gr.Button("Run Quiet Advisor Diagnostics", variant="primary")
        out_adv = gr.Markdown()
        btn_adv.click(
            run_advisor_demo,
            inputs=[temp_in, vram_used_in, vram_tot_in, ctx_prov_in, ctx_used_in, err_in],
            outputs=[out_adv],
        )

    with gr.Tab("3. Download Jupiter Studio"):
        gr.Markdown(
            "### Download Standalone Binaries (`v1.0.0-RC1`)\n"
            "- **Windows x64:** `JupiterStudio-Windows-x64.zip`\n"
            "- **macOS (Apple Silicon):** `JupiterStudio-macOS-arm64.tar.gz`\n"
            "- **Linux x64:** `JupiterStudio-Linux-x64.tar.gz`\n\n"
            "Get all builds + `SHA256SUMS.txt` at **[GitHub Releases](https://github.com/JupiterIsland/memoryos/releases/tag/v1.0.0-rc1)**."
        )

if __name__ == "__main__":
    demo.launch()

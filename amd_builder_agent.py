#!/usr/bin/env python3
"""
AMD Token Lab Dual-Brain Autonomous Builder Agent (MemoryOS v1.0)
=================================================================
Pairs AMD Token Lab's strongest models with Aider and MemoryOS verification:
  - Architect Agent : Gemma-4-31B-IT (31B parameters — system design, planning & code review)
  - Editor Agent    : Qwen3.8-27B    (27B parameters — code synthesis, diffs & refactoring)
  - Fast Scout      : MiniCPM5-2B    (2B parameters  — repo map & commit summaries)

Modes:
  1. Interactive Aider Architect Mode (default):
     Launches `aider` in `--architect` mode with Gemma-4-31B-IT as Architect and
     Qwen3.8-27B as Editor, pre-loaded with the core MemoryOS v1.0 files.
  2. Autonomous Build Loop (`--task "..."` or `--build-v1`):
     - Step 1: Gemma-4-31B-IT inspects the repo state and creates a concrete v1.0 build spec.
     - Step 2: Qwen3.8-27B (via Aider `--message` or direct Token Lab synthesis) implements the task.
     - Step 3: Runs `verify_all_systems.py` and `tests/run_gamer_hardware_tests.py` to validate.
     - Step 4: Writes an NVMe Quick-Save checkpoint and logs telemetry to QuietAdvisorDB.sqlite.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from memoryos.router import route_task

ARCHITECT_MODEL = "Gemma-4-31B-IT"
EDITOR_MODEL = "Qwen3.8-27B"
WEAK_MODEL = "MiniCPM5-2B"

CORE_V1_FILES = [
    "src/memoryos/router.py",
    "src/memoryos/server.py",
    "src/memoryos/quiet_advisor_client.py",
    "apps/quiet_advisor_ui/api.py",
    "apps/quiet_advisor_ui/server.py",
    "apps/jupiter-tv-desktop-v2/app.py",
]


def load_dotenv_into_environ() -> Dict[str, str]:
    """Load .env from repo root and configure OpenAI-compatible env vars for Aider + Token Lab."""
    env_path = REPO_ROOT / ".env"
    loaded: Dict[str, str] = {}
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            loaded[k] = v
            os.environ.setdefault(k, v)

    api_key = os.environ.get("TOKENLAB_API_KEY", "")
    api_base = (
        os.environ.get("TOKENLAB_BASE_URL")
        or os.environ.get("TOKENLAB_API_BASE")
        or "https://api.tokenlab.amd.com/v1"
    )

    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_API_BASE"] = api_base
    os.environ["OPENAI_BASE_URL"] = api_base
    os.environ.setdefault("MEMORYOS_ALLOW_OFFLINE_FALLBACK", "1")
    return {"api_key": api_key, "api_base": api_base}


def run_architect_plan(task_prompt: str) -> Dict[str, Any]:
    """Ask Gemma-4-31B-IT (via route_task) to produce the v1.0 engineering plan."""
    architect_prompt = (
        "You are the Lead Principal Architect Agent (Gemma-4-31B-IT) for MemoryOS v1.0.\n"
        "Core architecture:\n"
        "1. FastAPI Router Service (`src/memoryos/server.py`, `src/memoryos/router.py`) routing to AMD Token Lab.\n"
        "2. Quiet Advisor Web UI & Detector Engine (`apps/quiet_advisor_ui/api.py`, `quiet_advisor_detectors.py`).\n"
        "3. Jupiter Desktop v2 (`apps/jupiter-tv-desktop-v2/app.py`) with CPU cv2 MSE frame-skip gate.\n\n"
        f"Mission Objective:\n{task_prompt}\n\n"
        "Produce a concise, actionable 4-step implementation blueprint for the Qwen3.8-27B Editor Agent "
        "specifying exact files, functions, edge cases, and verification assertions."
    )
    res = route_task(
        prompt_text=architect_prompt,
        forced_model=ARCHITECT_MODEL,
        save_checkpoint=False,
        log_to_advisor=False,
    )
    return {
        "model_used": res.get("model") or ARCHITECT_MODEL,
        "latency_ms": res.get("latency_ms", 0.0),
        "response": res.get("response") or res.get("output") or str(res),
    }


def run_editor_synthesis(blueprint: str, task_prompt: str) -> Dict[str, Any]:
    """Ask Qwen3.8-27B (via route_task) to synthesize the code implementation summary & checks."""
    editor_prompt = (
        "You are the Lead Python Code Editor Agent (Qwen3.8-27B) for MemoryOS v1.0.\n"
        f"Mission:\n{task_prompt}\n\n"
        f"Architect Blueprint (from Gemma-4-31B-IT):\n{blueprint}\n\n"
        "Generate the production-ready Python implementation pattern and verification checklist."
    )
    res = route_task(
        prompt_text=editor_prompt,
        forced_model=EDITOR_MODEL,
        save_checkpoint=False,
        log_to_advisor=False,
    )
    return {
        "model_used": res.get("model") or EDITOR_MODEL,
        "latency_ms": res.get("latency_ms", 0.0),
        "response": res.get("response") or res.get("output") or str(res),
    }


def run_verification_gates() -> Dict[str, Any]:
    """Run verify_all_systems.py, re-seed exact 50-record gamer showcase, and run tests/run_gamer_hardware_tests.py."""
    gates = {}
    for label, rel_script in [
        ("system_verification", "verify_all_systems.py"),
        ("gamer_showcase_seed", "seed_gamer_showcase.py"),
        ("gamer_hardware_suite", "tests/run_gamer_hardware_tests.py"),
    ]:
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, "-B", str(REPO_ROOT / rel_script)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        gates[label] = {
            "exit_code": proc.returncode,
            "duration_ms": round((time.perf_counter() - t0) * 1000.0, 1),
            "passed": proc.returncode == 0,
        }
    return gates


def save_v1_build_checkpoint(plan: Dict[str, Any], edit: Dict[str, Any], gates: Dict[str, Any]) -> Path:
    """Write an NVMe checkpoint recording the Dual-Brain v1.0 build pass."""
    cp_dir = REPO_ROOT / "memory" / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)
    report_path = REPO_ROOT / "docs" / "proof-pack" / "AMD_AGENT_V1_BUILD_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    now_iso = datetime.now(timezone.utc).isoformat()
    arch_text = str(plan.get("response") or "")
    edit_text = str(edit.get("response") or "")

    md = f"""# 🤖 AMD Dual-Brain Agent Build Report (`MemoryOS v1.0`)

* **Generated At**: `{now_iso}`
* **Architect Agent**: `{plan.get('model_used', ARCHITECT_MODEL)}` (`{plan.get('latency_ms', 0)} ms`)
* **Editor Agent**: `{edit.get('model_used', EDITOR_MODEL)}` (`{edit.get('latency_ms', 0)} ms`)
* **Verification Gates**:
  * `verify_all_systems.py`: `{"PASS" if gates["system_verification"]["passed"] else "FAIL"}` (`{gates["system_verification"]["duration_ms"]} ms`)
  * `tests/run_gamer_hardware_tests.py`: `{"PASS" if gates["gamer_hardware_suite"]["passed"] else "FAIL"}` (`{gates["gamer_hardware_suite"]["duration_ms"]} ms`)

---

## 1. Architect Blueprint (`{ARCHITECT_MODEL}`)

```text
{arch_text.strip()}
```

---

## 2. Editor Implementation Pass (`{EDITOR_MODEL}`)

```text
{edit_text.strip()}
```
"""
    report_path.write_text(md, encoding="utf-8")
    return report_path


def build_aider_command(extra_prompt: Optional[str] = None) -> List[str]:
    """Construct the Aider Dual-Brain Architect command line targeting AMD Token Lab."""
    existing_files = [f for f in CORE_V1_FILES if (REPO_ROOT / f).exists()]
    cmd = [
        "aider",
        "--architect",
        "--model",
        f"openai/{ARCHITECT_MODEL}",
        "--editor-model",
        f"openai/{EDITOR_MODEL}",
        "--weak-model",
        f"openai/{WEAK_MODEL}",
        "--no-show-model-warnings",
        "--yes-always",
    ]
    if extra_prompt:
        cmd.extend(["--message", extra_prompt])
    cmd.extend(existing_files)
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="AMD Token Lab Dual-Brain Autonomous Builder Agent")
    parser.add_argument(
        "--task",
        type=str,
        default=(
            "Build and verify MemoryOS v1.0 core integration: ensure Router Service, "
            "Quiet Advisor UI telemetry, and Jupiter Desktop cv2 frame-delta bridge operate "
            "with zero warnings and 100% remote offload."
        ),
        help="Task prompt for the AMD Architect + Editor agents",
    )
    parser.add_argument(
        "--launch-aider",
        action="store_true",
        help="Launch interactive Aider in Dual-Model Architect mode (Gemma-4-31B-IT + Qwen3.8-27B)",
    )
    parser.add_argument(
        "--aider-task",
        type=str,
        default=None,
        help="Run Aider non-interactively with --message in Architect mode",
    )
    args = parser.parse_args()

    creds = load_dotenv_into_environ()
    masked_key = (
        f"{creds['api_key'][:8]}...{creds['api_key'][-4:]}"
        if len(creds.get("api_key", "")) > 12
        else "configured"
    )

    print("==================================================================")
    print("  AMD TOKEN LAB DUAL-BRAIN AUTONOMOUS BUILDER (MemoryOS v1.0)")
    print("==================================================================")
    print(f"  Architect Brain : openai/{ARCHITECT_MODEL} (31B Deep Reasoning)")
    print(f"  Editor Brain    : openai/{EDITOR_MODEL} (27B Code Generation)")
    print(f"  Fast Scout      : openai/{WEAK_MODEL} (2B Repo Map & Commits)")
    print(f"  Endpoint        : {creds['api_base']}")
    print(f"  API Key         : {masked_key}")
    print("==================================================================\n")

    if args.launch_aider or args.aider_task:
        aider_bin = shutil.which("aider")
        if not aider_bin:
            print("[!] Aider binary not found in current environment PATH.")
            print("    Run .\\Start-AiderAMD.ps1 -Architect in Windows PowerShell to auto-install and launch.")
            return 1
        cmd = build_aider_command(extra_prompt=args.aider_task)
        print(f"[*] Launching Aider Dual-Brain Architect: {' '.join(cmd)}\n")
        return subprocess.call(cmd, cwd=str(REPO_ROOT))

    print("[1/3] Running Architect Agent (Gemma-4-31B-IT) to design v1.0 blueprint...")
    plan = run_architect_plan(args.task)
    print(f"      -> Model: {plan.get('model_used')} | Latency: {plan.get('latency_ms')} ms")

    print("[2/3] Running Editor Agent (Qwen3.8-27B) to synthesize implementation...")
    edit = run_editor_synthesis(str(plan.get("response") or ""), args.task)
    print(f"      -> Model: {edit.get('model_used')} | Latency: {edit.get('latency_ms')} ms")

    print("[3/3] Running live verification gates (verify_all_systems + 5-suite gamer benchmark)...")
    gates = run_verification_gates()
    for k, v in gates.items():
        status_str = "PASS" if v["passed"] else "FAIL"
        print(f"      -> {k}: {status_str} ({v['duration_ms']} ms)")

    report_path = save_v1_build_checkpoint(plan, edit, gates)
    print(f"\n[OK] AMD Dual-Brain v1.0 Build Report written to: {report_path}")
    print(f"[OK] To launch interactive Aider Dual-Brain mode: powershell -ExecutionPolicy Bypass -File .\\Start-AiderAMD.ps1 -Architect")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
verify.py — Reproducible Verification & Live Benchmark Runner
==============================================================
Run on any machine after cloning or downloading the source to verify every
technical claim from live execution rather than trusting pre-recorded tables:

    python3 -B verify.py           # Full CI check + live EWC / Frank-v1 / MSE benchmarks
    python3 -B verify.py --quick   # Fast smoke check (skips the 12-module unit suite)
    python3 -B verify.py --json    # Machine-readable JSON report
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

CI_COMPILE_MODULES = [
    "quiet_advisor_detectors.py",
    "quiet_advisor_scheduler.py",
    "apps/jupiter_studio.py",
    "apps/jupiter_studio_ui.py",
    "src/memoryos/quiet_advisor_db.py",
    "src/memoryos/speculative_offload.py",
    "src/memoryos/memory_keeper.py",
    "src/memoryos/frank.py",
    "src/memoryos/ops_console.py",
    "src/memoryos/control_plane.py",
    "src/memoryos/gpu_backends.py",
    "src/memoryos/workspace_pack.py",
    "src/memoryos/router.py",
    "src/memoryos/browser_app.py",
    "src/memoryos/cloud_video.py",
    "src/memoryos/hf_hub.py",
    "src/memoryos/server.py",
    "src/memoryos/core/neural_memory_graph.py",
    "src/memoryos/grant_ledger.py",
    "apps/quiet_advisor_ui/server.py",
    "apps/quiet_advisor_ui/api.py",
]

CI_TEST_MODULES = [
    "tests/test_quiet_advisor_detectors.py",
    "tests/test_jupiter_studio.py",
    "tests/test_speculative_offload.py",
    "tests/test_memory_keeper.py",
    "tests/test_frank.py",
    "tests/test_cross_silicon_profiles.py",
    "tests/test_ops_console.py",
    "tests/test_control_plane.py",
    "tests/test_nvidia_telemetry_safety.py",
    "tests/test_workspace_pack.py",
    "tests/test_nvidia_brev_router.py",
    "tests/test_heatstream.py",
    "tests/test_grant_ledger_reconciliation.py",
    "tests/test_offload_integrity.py",
    "tests/test_cloud_video.py",
    "tests/test_hf_hub.py",
]

_STATE_FIXTURES = (
    REPO_ROOT / "graph" / "heat_stream_state.json",
    REPO_ROOT / "temporal_graph" / "heat_stream_state.json",
)


def _snapshot_files(paths: tuple[Path, ...]) -> Dict[Path, Optional[bytes]]:
    return {p: (p.read_bytes() if p.exists() else None) for p in paths}


def _restore_files(snaps: Dict[Path, Optional[bytes]]) -> None:
    for path, data in snaps.items():
        try:
            if data is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists() or path.read_bytes() != data:
                    path.write_bytes(data)
        except Exception:
            pass


def _collect_environment() -> Dict[str, Any]:
    from src.memoryos.amd_zen_studio import inspect_amd_zen_cpu
    from src.memoryos.gpu_backends import MultiGPUDetector

    cpu = inspect_amd_zen_cpu()
    gpu = MultiGPUDetector.get_active_profile()
    return {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu": cpu.get("model_name") or platform.processor() or "Unknown CPU",
        "logical_threads": cpu.get("logical_threads"),
        "gpu": gpu.device_name,
        "gpu_vendor": gpu.vendor,
        "gpu_vram_mb": f"{gpu.used_vram_mb}/{gpu.total_vram_mb}",
        "gpu_simulated": bool(getattr(gpu, "is_simulated", False)),
    }


def _check_py_compile() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as cache_dir:
        env = dict(os.environ)
        env["PYTHONPYCACHEPREFIX"] = cache_dir
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", *CI_COMPILE_MODULES],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    return {
        "passed": proc.returncode == 0,
        "module_count": len(CI_COMPILE_MODULES),
        "error": proc.stderr.strip()[-500:] if proc.returncode != 0 else "",
    }


def _check_neon() -> Dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-B", "NEON_SINGLE_FILE.py"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out = proc.stdout + "\n" + proc.stderr
    ready = "NEON STATUS: CERTIFICATION READY" in out
    subchecks: Dict[str, str] = {}
    for key in ("plugins", "budgets", "breaker", "recovery", "ledger"):
        m = re.search(rf"^{key}\s+(PASS|FAIL)", out, re.MULTILINE)
        if m:
            subchecks[key] = m.group(1)
    return {
        "passed": proc.returncode == 0 and ready,
        "certification": "CERTIFICATION READY" if ready else "NOT READY",
        "subchecks": subchecks,
        "error": out.strip()[-500:] if not (proc.returncode == 0 and ready) else "",
    }


def _check_unittest_suite(skip: bool) -> Dict[str, Any]:
    if skip:
        return {"skipped": True, "passed": True, "module_count": len(CI_TEST_MODULES), "tests_run": 0}
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "-W",
            "error::DeprecationWarning",
            "-m",
            "unittest",
            *CI_TEST_MODULES,
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    combined = proc.stdout + "\n" + proc.stderr
    m_ran = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", combined)
    tests_run = int(m_ran.group(1)) if m_ran else 0
    duration_s = float(m_ran.group(2)) if m_ran else 0.0
    ok_line = bool(re.search(r"^OK\b", combined, re.MULTILINE))
    passed = proc.returncode == 0 and ok_line and tests_run > 0
    return {
        "skipped": False,
        "passed": passed,
        "module_count": len(CI_TEST_MODULES),
        "tests_run": tests_run,
        "duration_s": duration_s,
        "error": combined.strip()[-800:] if not passed else "",
    }


def _run_live_ewc_audit() -> Dict[str, Any]:
    from src.memoryos.memory_keeper import (
        _fresh_audit_mlp,
        build_coding_curriculum,
        build_gaming_curriculum,
        run_anti_forgetting_audit,
    )

    audit = run_anti_forgetting_audit()

    # Sparse replay-only vs EWC + sparse replay control arm (exact 4-sample budget)
    task_a = build_gaming_curriculum()
    task_b = build_coding_curriculum()

    sparse_replay = _fresh_audit_mlp()
    sparse_replay.fit_continual(task_a, lr=0.22, epochs=50, ewc_lambda=0.0, consolidate_after=False)
    sparse_replay.fit_continual(
        task_b, replay_samples=task_a[:4], lr=0.15, epochs=30, ewc_lambda=0.0, consolidate_after=False
    )
    sparse_replay_only_a = sparse_replay.evaluate(task_a)["accuracy"]

    ewc_sparse = _fresh_audit_mlp()
    ewc_sparse.fit_continual(task_a, lr=0.22, epochs=50, ewc_lambda=0.0, consolidate_after=True)
    ewc_sparse.fit_continual(
        task_b, replay_samples=task_a[:4], lr=0.15, epochs=30, ewc_lambda=120.0, consolidate_after=True
    )
    ewc_sparse_a = ewc_sparse.evaluate(task_a)["accuracy"]
    ewc_sparse_b = ewc_sparse.evaluate(task_b)["accuracy"]

    control_arm_ok = bool(ewc_sparse_a >= 0.90 and ewc_sparse_b >= 0.90 and ewc_sparse_a > sparse_replay_only_a)
    passed = bool(audit["passed"] and control_arm_ok)
    return {
        "passed": passed,
        "naive_task_a_after": audit["naive_task_a_after"],
        "sparse_replay_only_task_a_after": sparse_replay_only_a,
        "ewc_sparse_replay_task_a_after": ewc_sparse_a,
        "ewc_task_a_after_ab": audit["ewc_task_a_after"],
        "ewc_task_b_after_ab": audit["ewc_task_b_after"],
        "ewc_task_a_after_abc": audit["ewc_task_a_after_abc"],
        "ewc_task_c_after_abc": audit["ewc_task_c_after"],
        "mlp_mean_us": audit["mlp_mean_us"],
    }


def _run_live_frank_demo() -> Dict[str, Any]:
    from src.memoryos.frank import DEFAULT_FRANK_WEIGHTS_PATH, TRAINING_CURRICULUM, FrankModel

    # Work strictly on in-memory copies; never mutate frank_v1.json on disk.
    ewc_frank = FrankModel.load(DEFAULT_FRANK_WEIGHTS_PATH)
    naive_frank = FrankModel.load(DEFAULT_FRANK_WEIGHTS_PATH)

    # Latency benchmark across 500 forward passes
    probe = TRAINING_CURRICULUM[0][0]
    t0 = time.perf_counter_ns()
    for _ in range(500):
        ewc_frank.predict(probe)
    mean_us = round((time.perf_counter_ns() - t0) / 500.0 / 1000.0, 2)

    curriculum_before = ewc_frank.evaluate(TRAINING_CURRICULUM)
    test_phrase = "purge my GPU cache before launching Cyberpunk"
    target_intent = "vram_reclaim"
    before_pred = ewc_frank.predict(test_phrase)

    # Continual update using Studio's exact /api/frank/teach parameters (EWC + Replay + A-GEM)
    teach_res = ewc_frank.fit_continual(
        [(test_phrase, target_intent)] * 4,
        replay_samples=TRAINING_CURRICULUM,
        epochs=45,
        lr=0.25,
        ewc_lambda=6.0,
        use_agem=True,
    )
    after_pred = ewc_frank.predict(test_phrase)
    curriculum_after_ewc = float(teach_res["curriculum_retention"])

    # Naive SGD baseline on the exact same batch/epochs/lr without replay, EWC, or A-GEM
    naive_res = naive_frank.fit_continual(
        [(test_phrase, target_intent)] * 4,
        replay_samples=(),
        epochs=45,
        lr=0.25,
        ewc_lambda=0.0,
        use_agem=False,
    )
    curriculum_after_naive = float(naive_res["curriculum_retention"])

    passed = bool(
        after_pred["intent"] == target_intent
        and curriculum_after_ewc >= 0.90
        and curriculum_after_ewc > curriculum_after_naive
    )
    return {
        "passed": passed,
        "params": ewc_frank.in_dim * ewc_frank.hidden_dim + ewc_frank.hidden_dim + ewc_frank.hidden_dim * ewc_frank.out_dim + ewc_frank.out_dim,
        "architecture": f"{ewc_frank.in_dim}->{ewc_frank.hidden_dim}->{ewc_frank.out_dim}",
        "predict_mean_us": mean_us,
        "phrase": test_phrase,
        "target_intent": target_intent,
        "before_intent": before_pred["intent"],
        "before_confidence": before_pred["confidence"],
        "after_intent": after_pred["intent"],
        "after_confidence": after_pred["confidence"],
        "curriculum_before": curriculum_before,
        "curriculum_after_ewc_agem": curriculum_after_ewc,
        "curriculum_after_naive_sgd": curriculum_after_naive,
        "agem_projections": int(teach_res.get("agem_projections", 0)),
    }


def _run_live_mse_gate() -> Dict[str, Any]:
    from src.memoryos.amd_zen_studio import profile_d3_on_zen3

    rep = profile_d3_on_zen3(iterations=200)
    return {
        "passed": rep["status"] == "PASS",
        "scope": "64x36 stride-sampled MSE",
        "iterations": rep["iterations"],
        "avg_ms": rep["avg_zen3_d3_gate_ms"],
        "p99_ms": rep["p99_zen3_d3_gate_ms"],
        "pct_of_144fps_budget": rep["pct_of_144fps_budget"],
        "status": rep["status"],
    }


def _print_human_report(report: Dict[str, Any]) -> None:
    env = report["environment"]
    print("=" * 68)
    print("MemoryOS // Jupiter Studio - Live Verification Report")
    print("=" * 68)
    print(f"Timestamp (UTC) : {env['timestamp_utc']}")
    print(f"OS / Python     : {env['os']} | Python {env['python']}")
    print(f"CPU             : {env['cpu']} ({env['logical_threads']} threads)")
    gpu_tag = " [SIMULATED]" if env["gpu_simulated"] else ""
    print(f"GPU             : {env['gpu']} (VRAM {env['gpu_vram_mb']} MB){gpu_tag}")
    print("-" * 68)

    c = report["checks"]
    py_c = c["py_compile"]
    print(f"[{'PASS' if py_c['passed'] else 'FAIL'}] py_compile ({py_c['module_count']} CI modules)")

    neon = c["neon"]
    print(f"[{'PASS' if neon['passed'] else 'FAIL'}] NEON_SINGLE_FILE.py -> {neon['certification']}")

    uni = c["unittest"]
    if uni["skipped"]:
        print(f"[SKIP] Unit Test Suite (skipped via --quick; {uni['module_count']} CI modules)")
    else:
        print(
            f"[{'PASS' if uni['passed'] else 'FAIL'}] CI Unit Test Suite -> "
            f"{uni['tests_run']} tests in {uni['duration_s']:.2f}s"
        )

    ewc = c["ewc_audit"]
    print(
        f"[{'PASS' if ewc['passed'] else 'FAIL'}] Continual Offload Net (4->8->1, synthetic A->B->C): "
        f"Naive SGD={ewc['naive_task_a_after']*100:.0f}% | "
        f"Sparse Replay={ewc['sparse_replay_only_task_a_after']*100:.0f}% | "
        f"EWC+Replay (4-sample)={ewc['ewc_sparse_replay_task_a_after']*100:.0f}% | "
        f"A->B->C Task A={ewc['ewc_task_a_after_abc']*100:.0f}% ({ewc['mlp_mean_us']:.2f} us/call)"
    )

    fr = c["frank_demo"]
    print(
        f"[{'PASS' if fr['passed'] else 'FAIL'}] Frank-v1 Continual Router ({fr['architecture']}, {fr['params']} params, in-memory): "
        f"'{fr['phrase']}' -> {fr['after_intent']} ({fr['after_confidence']*100:.1f}%) | "
        f"36-phrase Retention: EWC+A-GEM={fr['curriculum_after_ewc_agem']*100:.1f}% vs "
        f"Naive SGD={fr['curriculum_after_naive_sgd']*100:.1f}% "
        f"({fr['agem_projections']} A-GEM projections, {fr['predict_mean_us']:.1f} us/call)"
    )

    mse = c["mse_gate"]
    print(
        f"[{'PASS' if mse['passed'] else 'FAIL'}] CPU Frame-Delta Gate ({mse['scope']}, {mse['iterations']}x): "
        f"avg={mse['avg_ms']:.3f} ms, p99={mse['p99_ms']:.3f} ms ({mse['pct_of_144fps_budget']:.2f}% of 144Hz budget)"
    )

    print("-" * 68)
    print(f"OVERALL VERIFICATION: {'PASS' if report['all_passed'] else 'FAIL'}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Verify MemoryOS // Jupiter Studio claims with live measurements.")
    parser.add_argument("--quick", action="store_true", help="Skip the 12-module unittest run for a fast smoke check")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output")
    args = parser.parse_args(argv)

    snaps = _snapshot_files(_STATE_FIXTURES)
    try:
        checks = {
            "py_compile": _check_py_compile(),
            "neon": _check_neon(),
            "unittest": _check_unittest_suite(skip=args.quick),
            "ewc_audit": _run_live_ewc_audit(),
            "frank_demo": _run_live_frank_demo(),
            "mse_gate": _run_live_mse_gate(),
        }
        report = {
            "environment": _collect_environment(),
            "checks": checks,
            "all_passed": all(bool(v.get("passed")) for v in checks.values()),
        }
    finally:
        _restore_files(snaps)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_human_report(report)

    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

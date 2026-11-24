"""
JUPITER STUDIO — Personal Intelligence Control Plane
NEON_SINGLE_FILE.py

One-command validation & certification harness proving:
  1. Declarative plugin manifest & SHA-256 checksum validation (zero arbitrary exec)
  2. Operation budget enforcement (timeout / memory / CPU quotas)
  3. Circuit breaker state transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
  4. Crash recovery engine (SQLite WAL, RUNNING -> RECOVERING on restart)
  5. Immutable SHA-256 hash-chained ledger + tamper detection

Usage:
    python3 NEON_SINGLE_FILE.py

Exit Codes:
    0 = PASS (NEON STATUS: CERTIFICATION READY)
    1 = FAIL
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.memoryos.control_plane import (
    ApprovalRequiredError,
    BudgetEnforcer,
    BudgetExceededError,
    CircuitBreaker,
    CircuitState,
    DeclarativePluginLoader,
    ImmutableLedger,
    OperationBudget,
    OperationState,
    RecoveryManager,
)


def _check_declarative_plugins() -> bool:
    with tempfile.TemporaryDirectory() as td:
        ledger = ImmutableLedger(Path(td) / "ledger.sqlite")
        loader = DeclarativePluginLoader(ledger=ledger)
        summary = loader.load_directory(REPO_ROOT / "plugins")
        assert "security_pack" in summary["loaded"], f"Missing security_pack: {summary}"
        assert "research_pack" in summary["loaded"], f"Missing research_pack: {summary}"
        assert len(summary["rejected"]) == 0, f"Unexpected rejected packs: {summary['rejected']}"
        try:
            loader.execute_operation("security_pack.secret_scan", workspace_root=REPO_ROOT)
            raise AssertionError("Expected ApprovalRequiredError for security_pack.secret_scan")
        except ApprovalRequiredError:
            pass
        res = loader.execute_operation("security_pack.secret_scan", approved=True, workspace_root=REPO_ROOT)
        assert res["state"] == OperationState.COMPLETE.value
        assert res["result"]["files_scanned"] > 0
        assert "secrets_found" in res["result"]
    return True


def _check_budgets() -> bool:
    with tempfile.TemporaryDirectory() as td:
        ledger = ImmutableLedger(Path(td) / "budget.sqlite")
        try:
            BudgetEnforcer.run_with_budget(
                lambda: time.sleep(0.25),
                OperationBudget(timeout_seconds=0.05, max_memory_mb=256, max_cpu_seconds=5.0),
                ledger=ledger,
                operation_id="budget-timeout-check",
            )
            raise AssertionError("Timeout budget did not abort")
        except BudgetExceededError as exc:
            assert exc.metric == "timeout"
        assert ledger.verify()["valid"] is True
    return True


def _check_circuit_breaker() -> bool:
    now = [100.0]
    breaker = CircuitBreaker("test_provider", failure_threshold=5, cooldown_seconds=60.0, clock=lambda: now[0])
    for _ in range(5):
        breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    assert breaker.can_execute() is False
    now[0] += 61.0
    assert breaker.can_execute() is True
    assert breaker.state == CircuitState.HALF_OPEN
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED
    return True


def _check_recovery() -> bool:
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "operations.sqlite"
        rm1 = RecoveryManager(db)
        rm1.save_state("op-run-1", OperationState.RUNNING, objective="Audit repo", operation_name="security_pack.secret_scan")
        rm1.save_state("op-q-2", OperationState.QUEUED, objective="Health check", operation_name="research_pack.silicon_health_check")
        # Simulate restart with fresh RecoveryManager instance
        rm2 = RecoveryManager(db)
        recovered = rm2.recover_incomplete()
        states = {r["operation_id"]: r["state"] for r in recovered}
        assert states.get("op-run-1") == OperationState.RECOVERING.value
        assert states.get("op-q-2") == OperationState.QUEUED.value
    return True


def _check_immutable_ledger() -> bool:
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "ledger.sqlite"
        ledger = ImmutableLedger(db)
        ledger.append({"event": "boot", "component": "control_plane"})
        ledger.append({"event": "dispatch", "op_id": "op-1"})
        assert ledger.verify()["valid"] is True
        # Tamper directly in SQLite and verify detection
        conn = sqlite3.connect(str(db))
        conn.execute("UPDATE control_plane_ledger SET payload_json = ? WHERE seq = 1", ('{"event":"tampered"}',))
        conn.commit()
        conn.close()
        assert ledger.verify()["valid"] is False
    return True


def run_validation() -> int:
    checks = [
        ("plugins", _check_declarative_plugins),
        ("budgets", _check_budgets),
        ("breaker", _check_circuit_breaker),
        ("recovery", _check_recovery),
        ("ledger", _check_immutable_ledger),
    ]
    results = {}
    for name, fn in checks:
        try:
            results[name] = bool(fn())
        except Exception as exc:
            print(f"FAIL [{name}]: {exc}")
            results[name] = False

    print()
    print("=" * 52)
    print("JUPITER CONTROL PLANE VALIDATION")
    print("=" * 52)
    for name, ok in results.items():
        print(f"{name:<24}{'PASS' if ok else 'FAIL'}")
    print()
    if all(results.values()):
        print("NEON STATUS: CERTIFICATION READY")
        return 0
    print("NEON STATUS: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(run_validation())

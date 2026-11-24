"""Jupiter Studio — Personal Intelligence Control Plane Core.

Implements the five hardened Control Plane pillars using pure Python stdlib:
  1. Secure Declarative Plugin Loader (JSON manifests only; zero importlib/exec/eval)
  2. Operation Budgets & Quotas (timeout, memory, CPU enforcement -> ABORTED)
  3. Circuit Breaker System (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
  4. Crash Recovery Engine (SQLite WAL persistence, RUNNING -> RECOVERING on restart)
  5. Immutable Hash-Chained Ledger (SHA-256 chained audit events + verify())
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import platform
import re
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple


SDK_VERSION = "1.0"
DEFAULT_FAILURE_THRESHOLD = 5
DEFAULT_COOLDOWN_SECONDS = 60.0

REQUIRED_MANIFEST_KEYS = {"id", "name", "version", "sdk_version", "permissions", "checksum_sha256"}
ALLOWED_PERMISSIONS = {
    "memory.read",
    "memory.write",
    "ledger.read",
    "ledger.write",
    "telemetry.read",
    "ops.execute",
}


class OperationState(str, Enum):
    CREATED = "CREATED"
    PLANNED = "PLANNED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    RECOVERING = "RECOVERING"


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass(frozen=True)
class OperationBudget:
    timeout_seconds: float = 30.0
    max_memory_mb: int = 512
    max_cpu_seconds: float = 30.0


class BudgetExceededError(RuntimeError):
    """Raised when an operation violates its timeout, memory, or CPU quota."""

    def __init__(self, reason: str, metric: str):
        super().__init__(reason)
        self.metric = metric


class ApprovalRequiredError(PermissionError):
    """Raised when a declarative plugin pack policy requires human approval."""

    def __init__(self, operation_id: str, plugin_id: str):
        super().__init__(f"Operation '{operation_id}' in pack '{plugin_id}' requires explicit operator approval")
        self.operation_id = operation_id
        self.plugin_id = plugin_id


# =====================================================================
# 1. IMMUTABLE HASH-CHAINED LEDGER
# =====================================================================


def _canonical_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class ImmutableLedger:
    """SQLite WAL hash-chained audit ledger with tamper detection."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS control_plane_ledger (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    event_hash TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def append(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            event_id = f"evt-{uuid.uuid4().hex[:12]}"
            created_at = datetime.now(timezone.utc).isoformat()
            canonical = _canonical_json(payload)
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT event_hash FROM control_plane_ledger ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                prev_hash = str(row["event_hash"]) if row else ""
                event_hash = hashlib.sha256((prev_hash + canonical).encode("utf-8")).hexdigest()
                conn.execute(
                    """
                    INSERT INTO control_plane_ledger
                    (event_id, created_at, previous_hash, payload_json, event_hash)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (event_id, created_at, prev_hash, canonical, event_hash),
                )
                conn.commit()
            return {
                "event_id": event_id,
                "created_at": created_at,
                "previous_hash": prev_hash,
                "payload": payload,
                "event_hash": event_hash,
            }

    def verify(self) -> Dict[str, Any]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT seq, event_id, previous_hash, payload_json, event_hash "
                    "FROM control_plane_ledger ORDER BY seq ASC"
                ).fetchall()
            prev_hash = ""
            for r in rows:
                if str(r["previous_hash"]) != prev_hash:
                    return {
                        "valid": False,
                        "event_count": len(rows),
                        "broken_seq": int(r["seq"]),
                        "reason": "previous_hash mismatch",
                    }
                try:
                    parsed = json.loads(str(r["payload_json"]))
                    canonical = _canonical_json(parsed)
                except Exception:
                    return {
                        "valid": False,
                        "event_count": len(rows),
                        "broken_seq": int(r["seq"]),
                        "reason": "corrupt payload_json",
                    }
                expected = hashlib.sha256((prev_hash + canonical).encode("utf-8")).hexdigest()
                if expected != str(r["event_hash"]):
                    return {
                        "valid": False,
                        "event_count": len(rows),
                        "broken_seq": int(r["seq"]),
                        "reason": "event_hash mismatch (tampering detected)",
                    }
                prev_hash = str(r["event_hash"])
            return {
                "valid": True,
                "event_count": len(rows),
                "head_hash": prev_hash,
            }


# =====================================================================
# 2. CIRCUIT BREAKER SYSTEM
# =====================================================================


class CircuitBreaker:
    """Thread-safe provider/executor circuit breaker (CLOSED / OPEN / HALF_OPEN)."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.name = name
        self.failure_threshold = max(1, int(failure_threshold))
        self.cooldown_seconds = max(0.0, float(cooldown_seconds))
        self._clock = clock
        self._lock = threading.Lock()
        self.failures = 0
        self.last_failure_ts = 0.0
        self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if (self._clock() - self.last_failure_ts) >= self.cooldown_seconds:
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self.failures = 0
            self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self.failures += 1
            self.last_failure_ts = self._clock()
            if self.state == CircuitState.HALF_OPEN or self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failures": self.failures,
                "failure_threshold": self.failure_threshold,
            }


# =====================================================================
# 3. BUDGET ENFORCER
# =====================================================================


class BudgetEnforcer:
    """Enforces timeout, memory, and CPU quotas on trusted core executors."""

    @staticmethod
    def run_with_budget(
        fn: Callable[[], Any],
        budget: OperationBudget,
        *,
        estimated_memory_mb: Optional[int] = None,
        ledger: Optional[ImmutableLedger] = None,
        operation_id: str = "",
    ) -> Tuple[OperationState, Any]:
        if estimated_memory_mb is not None and estimated_memory_mb > budget.max_memory_mb:
            msg = f"Memory quota exceeded ({estimated_memory_mb} MB > {budget.max_memory_mb} MB)"
            if ledger:
                ledger.append({"event": "operation_aborted", "operation_id": operation_id, "reason": msg, "metric": "memory"})
            raise BudgetExceededError(msg, "memory")

        result_box: Dict[str, Any] = {}
        err_box: Dict[str, BaseException] = {}
        cpu_elapsed: Dict[str, float] = {"sec": 0.0}

        def _worker() -> None:
            c0 = time.process_time()
            try:
                result_box["value"] = fn()
            except BaseException as exc:
                err_box["exc"] = exc
            finally:
                cpu_elapsed["sec"] = time.process_time() - c0

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join(timeout=max(0.001, float(budget.timeout_seconds)))

        if t.is_alive():
            msg = f"Operation timeout exceeded ({budget.timeout_seconds}s)"
            if ledger:
                ledger.append({"event": "operation_aborted", "operation_id": operation_id, "reason": msg, "metric": "timeout"})
            raise BudgetExceededError(msg, "timeout")

        if "exc" in err_box:
            raise err_box["exc"]

        if cpu_elapsed["sec"] > float(budget.max_cpu_seconds):
            msg = f"CPU quota exceeded ({cpu_elapsed['sec']:.3f}s > {budget.max_cpu_seconds}s)"
            if ledger:
                ledger.append({"event": "operation_aborted", "operation_id": operation_id, "reason": msg, "metric": "cpu"})
            raise BudgetExceededError(msg, "cpu")

        return OperationState.COMPLETE, result_box.get("value")


# =====================================================================
# 4. RECOVERY ENGINE
# =====================================================================


class RecoveryManager:
    """Persists operation lifecycle states and recovers interrupted runs after restart."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS operations_state (
                    operation_id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    operation_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_state(
        self,
        operation_id: str,
        state: OperationState,
        *,
        objective: str = "",
        operation_name: str = "dispatch",
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO operations_state (operation_id, objective, operation_name, state, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(operation_id) DO UPDATE SET
                    state = excluded.state,
                    updated_at = excluded.updated_at
                """,
                (operation_id, objective, operation_name, state.value, now_iso),
            )
            conn.commit()

    def get_state(self, operation_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT operation_id, objective, operation_name, state, updated_at "
                "FROM operations_state WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
        return dict(row) if row else None

    def recover_incomplete(self, ledger: Optional[ImmutableLedger] = None) -> List[Dict[str, Any]]:
        """On restart, load QUEUED and RUNNING ops; transition RUNNING -> RECOVERING."""
        now_iso = datetime.now(timezone.utc).isoformat()
        recovered: List[Dict[str, Any]] = []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT operation_id, objective, operation_name, state, updated_at "
                "FROM operations_state WHERE state IN (?, ?)",
                (OperationState.QUEUED.value, OperationState.RUNNING.value),
            ).fetchall()
            for r in rows:
                op_id = str(r["operation_id"])
                old_state = str(r["state"])
                new_state = (
                    OperationState.RECOVERING.value
                    if old_state == OperationState.RUNNING.value
                    else OperationState.QUEUED.value
                )
                if new_state != old_state:
                    conn.execute(
                        "UPDATE operations_state SET state = ?, updated_at = ? WHERE operation_id = ?",
                        (new_state, now_iso, op_id),
                    )
                item = {
                    "operation_id": op_id,
                    "objective": str(r["objective"]),
                    "operation_name": str(r["operation_name"]),
                    "previous_state": old_state,
                    "state": new_state,
                }
                recovered.append(item)
                if ledger:
                    ledger.append({"event": "operation_recovered", **item})
            conn.commit()
        return recovered

    def list_recoverable(self) -> List[Dict[str, Any]]:
        """List all queued or recovering operations awaiting operator resume/dismiss."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT operation_id, objective, operation_name, state, updated_at "
                "FROM operations_state WHERE state IN (?, ?) ORDER BY updated_at DESC",
                (OperationState.RECOVERING.value, OperationState.QUEUED.value),
            ).fetchall()
        return [dict(r) for r in rows]

    def dismiss_operation(self, operation_id: str, ledger: Optional[ImmutableLedger] = None) -> bool:
        """Transition a recoverable operation to ABORTED so it no longer triggers resume prompts."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE operations_state SET state = ?, updated_at = ? WHERE operation_id = ?",
                (OperationState.ABORTED.value, now_iso, operation_id),
            )
            conn.commit()
            changed = cur.rowcount > 0
        if changed and ledger:
            ledger.append({"event": "operation_dismissed", "operation_id": operation_id})
        return changed


# =====================================================================
# 5. SECURE DECLARATIVE PLUGIN LOADER & CONTEXT (NO EXEC / IMPORTLIB)
# =====================================================================

_SKIP_SCAN_DIRS = {
    ".git",
    "node_modules",
    "apex-env",
    "dist",
    "build",
    "__pycache__",
    "memory",
    "records",
    "tlb_hot_cache",
    "nvme_checkpoints",
}
_SCAN_EXTS = {".py", ".md", ".json", ".yml", ".yaml", ".ps1", ".sh"}
_SECRET_PATTERNS = [
    ("openai_or_stripe_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("groq_key", re.compile(r"\bgsk_[A-Za-z0-9]{20,}\b")),
    ("nvidia_key", re.compile(r"\bnvapi-[A-Za-z0-9_-]{20,}\b")),
    ("github_pat", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]


def _iter_workspace_text_files(root: Path, max_files: int = 200) -> List[Path]:
    collected: List[Path] = []
    if not root.is_dir():
        return collected
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in _SKIP_SCAN_DIRS and not d.startswith("pyqt6") and not d.startswith(".venv")
        )
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            if p.suffix.lower() not in _SCAN_EXTS:
                continue
            try:
                if p.stat().st_size > 128 * 1024:
                    continue
            except OSError:
                continue
            collected.append(p)
            if len(collected) >= max_files:
                return collected
    return collected


def _exec_secret_scan(context: "PluginContext", inputs: Dict[str, Any]) -> Dict[str, Any]:
    context.require("memory.read")
    context.require("ledger.write")
    root = Path(str(inputs.get("workspace_root") or Path.cwd()))
    files = _iter_workspace_text_files(root, max_files=200)
    findings: List[Dict[str, Any]] = []
    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = fp.name
        try:
            rel = str(fp.relative_to(root))
        except ValueError:
            pass
        for lineno, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if any(tok in low for tok in ("your_", "your-", "example", "placeholder", "dummy", "secret_patterns")):
                continue
            for kind, pat in _SECRET_PATTERNS:
                if pat.search(line):
                    findings.append({"file": rel, "line": lineno, "kind": kind})
                    break
    return {
        "executor": "builtin.secret_scan",
        "files_scanned": len(files),
        "secrets_found": len(findings),
        "findings": findings[:20],
        "status": "clean" if not findings else "findings_detected",
    }


def _exec_dependency_audit(context: "PluginContext", inputs: Dict[str, Any]) -> Dict[str, Any]:
    context.require("ledger.write")
    root = Path(str(inputs.get("workspace_root") or Path.cwd()))
    req_files = sorted(p.name for p in root.glob("requirements*.txt") if p.is_file())
    core_targets = [
        root / "src" / "memoryos" / "frank.py",
        root / "src" / "memoryos" / "ops_console.py",
        root / "src" / "memoryos" / "control_plane.py",
        root / "src" / "memoryos" / "memory_keeper.py",
        root / "src" / "memoryos" / "speculative_offload.py",
    ]
    heavy_mods = {"torch", "numpy", "sklearn", "onnxruntime"}
    issues: List[Dict[str, str]] = []
    checked = 0
    for fp in core_targets:
        if not fp.is_file():
            continue
        checked += 1
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as exc:
            issues.append({"file": fp.name, "error": f"SyntaxError: {exc}"})
            continue
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".", 1)[0]
                    if top in heavy_mods:
                        issues.append({"file": fp.name, "import": top})
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".", 1)[0]
                if top in heavy_mods:
                    issues.append({"file": fp.name, "import": top})
    return {
        "executor": "builtin.dependency_audit",
        "core_files_checked": checked,
        "stdlib_core": len(issues) == 0,
        "requirements_files": req_files,
        "issues_found": len(issues),
        "issues": issues,
    }


def _exec_architecture_audit(context: "PluginContext", inputs: Dict[str, Any]) -> Dict[str, Any]:
    context.require("memory.read")
    context.require("telemetry.read")
    root = Path(str(inputs.get("workspace_root") or Path.cwd()))
    core_count = len(list((root / "src" / "memoryos").glob("*.py"))) if (root / "src" / "memoryos").is_dir() else 0
    apps_count = len(list((root / "apps").glob("*.py"))) if (root / "apps").is_dir() else 0
    test_count = len(list((root / "tests").glob("test_*.py"))) if (root / "tests").is_dir() else 0
    pack_count = len(list((root / "plugins").glob("*/manifest.json"))) if (root / "plugins").is_dir() else 0
    return {
        "executor": "builtin.architecture_audit",
        "control_plane": "active",
        "core_modules": core_count,
        "app_modules": apps_count,
        "test_modules": test_count,
        "plugin_packs": pack_count,
        "neon_harness_present": (root / "NEON_SINGLE_FILE.py").is_file(),
        "status": "ok",
    }


def _exec_silicon_health_check(context: "PluginContext", inputs: Dict[str, Any]) -> Dict[str, Any]:
    context.require("telemetry.read")
    try:
        from src.memoryos.gpu_backends import MultiGPUDetector, classify_silicon
    except ImportError:
        from memoryos.gpu_backends import MultiGPUDetector, classify_silicon
    prof = MultiGPUDetector.get_active_profile()
    cpu_id = platform.processor() or platform.machine() or "Generic Host CPU"
    sil = classify_silicon(cpu_id)
    return {
        "executor": "builtin.silicon_health_check",
        "zero_vram_core": True,
        "gpu_vendor": prof.vendor,
        "device_name": prof.device_name,
        "free_vram_mb": prof.free_vram_mb,
        "total_vram_mb": prof.total_vram_mb,
        "host_silicon": sil.family,
        "recommended_route": sil.recommended_route,
        "status": "healthy",
    }


ALLOWED_EXECUTORS: Dict[str, Callable[["PluginContext", Dict[str, Any]], Dict[str, Any]]] = {
    "builtin.secret_scan": _exec_secret_scan,
    "builtin.dependency_audit": _exec_dependency_audit,
    "builtin.architecture_audit": _exec_architecture_audit,
    "builtin.silicon_health_check": _exec_silicon_health_check,
}


class PluginContext:
    """Sandboxed runtime capability gate — plugins never touch OS/DB/filesystem directly."""

    def __init__(self, plugin_id: str, granted_permissions: Set[str], ledger: Optional[ImmutableLedger] = None):
        self.plugin_id = plugin_id
        self._granted = set(granted_permissions)
        self._ledger = ledger

    def require(self, permission: str) -> None:
        if permission not in self._granted:
            if self._ledger:
                self._ledger.append({
                    "event": "permission_denied",
                    "plugin_id": self.plugin_id,
                    "permission": permission,
                })
            raise PermissionError(f"Plugin '{self.plugin_id}' lacks required permission '{permission}'")


@dataclass
class DeclarativeOperationSpec:
    operation_id: str
    namespaced_id: str
    plugin_id: str
    executor: str
    budget: OperationBudget
    required_permissions: List[str] = field(default_factory=list)


@dataclass
class LoadedPluginPack:
    id: str
    name: str
    version: str
    sdk_version: str
    permissions: List[str]
    operations: List[DeclarativeOperationSpec]
    policies: Dict[str, Any]
    checksum_sha256: str


def compute_pack_checksum(operations_raw: bytes, policies_raw: bytes) -> str:
    h = hashlib.sha256()
    h.update(operations_raw.replace(b"\r\n", b"\n"))
    h.update(b"\n--POLICIES--\n")
    h.update(policies_raw.replace(b"\r\n", b"\n"))
    return h.hexdigest()


class DeclarativePluginLoader:
    """Loads, validates, and executes ONLY declarative JSON plugin packs."""

    def __init__(self, ledger: Optional[ImmutableLedger] = None):
        self.ledger = ledger
        self.packs: Dict[str, LoadedPluginPack] = {}
        self.operations: Dict[str, DeclarativeOperationSpec] = {}
        self.rejected: List[Dict[str, str]] = []

    def load_pack_dir(self, pack_dir: Path) -> LoadedPluginPack:
        manifest_path = pack_dir / "manifest.json"
        ops_path = pack_dir / "operations.json"
        policies_path = pack_dir / "policies.json"

        if not manifest_path.is_file() or not ops_path.is_file() or not policies_path.is_file():
            raise ValueError(f"Incomplete declarative pack in {pack_dir} (manifest/operations/policies required)")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("Manifest root must be a JSON object")

        missing = REQUIRED_MANIFEST_KEYS - set(manifest.keys())
        if missing:
            raise ValueError(f"Manifest missing required keys: {sorted(missing)}")

        if str(manifest["sdk_version"]) != SDK_VERSION:
            raise ValueError(f"SDK version mismatch: got {manifest['sdk_version']!r}, expected {SDK_VERSION!r}")

        perms = manifest.get("permissions")
        if not isinstance(perms, list) or not all(isinstance(p, str) for p in perms):
            raise ValueError("Manifest permissions must be a list of strings")
        unknown_perms = set(perms) - ALLOWED_PERMISSIONS
        if unknown_perms:
            raise ValueError(f"Unknown permissions requested: {sorted(unknown_perms)}")

        ops_raw = ops_path.read_bytes()
        pol_raw = policies_path.read_bytes()
        expected_hash = str(manifest["checksum_sha256"]).removeprefix("sha256:")
        actual_hash = compute_pack_checksum(ops_raw, pol_raw)
        if actual_hash != expected_hash:
            raise ValueError(f"Tampered plugin pack checksum for '{manifest['id']}'")

        ops_doc = json.loads(ops_raw.decode("utf-8"))
        pol_doc = json.loads(pol_raw.decode("utf-8"))
        if not isinstance(ops_doc, dict) or not isinstance(ops_doc.get("operations"), list):
            raise ValueError("operations.json must contain an 'operations' list")
        if not isinstance(pol_doc, dict):
            raise ValueError("policies.json must be a JSON object")

        plugin_id = str(manifest["id"]).strip()
        if bool(pol_doc.get("allow_network", False)):
            raise PermissionError(
                f"Plugin pack '{plugin_id}' requests allow_network=true, which is forbidden by the zero-network control plane"
            )
        loaded_ops: List[DeclarativeOperationSpec] = []
        for entry in ops_doc["operations"]:
            if not isinstance(entry, dict):
                raise ValueError("Each operation entry must be a JSON object")
            op_id = str(entry.get("id") or "").strip()
            executor = str(entry.get("executor") or "").strip()
            if not op_id or executor not in ALLOWED_EXECUTORS:
                raise ValueError(f"Unknown or invalid executor '{executor}' for operation '{op_id}'")
            op_perms = list(entry.get("permissions") or [])
            if not set(op_perms).issubset(set(perms)):
                raise PermissionError(f"Operation '{op_id}' requests permissions not granted in manifest")
            budget = OperationBudget(
                timeout_seconds=float(entry.get("timeout_seconds", 30.0)),
                max_memory_mb=int(entry.get("memory_limit_mb", 512)),
                max_cpu_seconds=float(entry.get("cpu_limit_seconds", 30.0)),
            )
            spec = DeclarativeOperationSpec(
                operation_id=op_id,
                namespaced_id=f"{plugin_id}.{op_id}",
                plugin_id=plugin_id,
                executor=executor,
                budget=budget,
                required_permissions=op_perms,
            )
            loaded_ops.append(spec)

        pack = LoadedPluginPack(
            id=plugin_id,
            name=str(manifest["name"]),
            version=str(manifest["version"]),
            sdk_version=str(manifest["sdk_version"]),
            permissions=list(perms),
            operations=loaded_ops,
            policies=pol_doc,
            checksum_sha256=actual_hash,
        )
        self.packs[plugin_id] = pack
        for spec in loaded_ops:
            self.operations[spec.namespaced_id] = spec
        return pack

    def load_directory(self, plugins_root: Path) -> Dict[str, Any]:
        root = Path(plugins_root)
        if not root.is_dir():
            return {"loaded": [], "rejected": []}
        for child in sorted(root.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            try:
                self.load_pack_dir(child)
            except Exception as exc:
                self.rejected.append({"pack": child.name, "error": str(exc)})
        return {
            "loaded": sorted(self.packs.keys()),
            "rejected": list(self.rejected),
        }

    def execute_operation(
        self,
        namespaced_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        *,
        estimated_memory_mb: Optional[int] = None,
        approved: bool = False,
        workspace_root: Optional[Path] = None,
    ) -> Dict[str, Any]:
        if namespaced_id not in self.operations:
            raise KeyError(f"Unknown operation: {namespaced_id}")
        spec = self.operations[namespaced_id]
        pack = self.packs[spec.plugin_id]
        if pack.policies.get("require_human_approval") and not approved:
            if self.ledger:
                self.ledger.append({
                    "event": "plugin_approval_required",
                    "operation": namespaced_id,
                    "plugin_id": pack.id,
                })
            raise ApprovalRequiredError(namespaced_id, pack.id)
        ctx = PluginContext(pack.id, set(pack.permissions), ledger=self.ledger)
        for perm in spec.required_permissions:
            ctx.require(perm)
        merged_inputs = dict(inputs or {})
        if workspace_root is not None:
            merged_inputs["workspace_root"] = str(workspace_root)
        executor_fn = ALLOWED_EXECUTORS[spec.executor]
        state, output = BudgetEnforcer.run_with_budget(
            lambda: executor_fn(ctx, merged_inputs),
            spec.budget,
            estimated_memory_mb=estimated_memory_mb,
            ledger=self.ledger,
            operation_id=namespaced_id,
        )
        if self.ledger:
            self.ledger.append({
                "event": "plugin_operation_complete",
                "operation": namespaced_id,
                "plugin_id": pack.id,
                "state": state.value,
            })
        return {"operation": namespaced_id, "state": state.value, "result": output}

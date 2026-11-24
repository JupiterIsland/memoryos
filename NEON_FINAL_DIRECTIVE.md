# JUPITER STUDIO — NEON FINAL ARCHITECTURE DIRECTIVE
## Personal Intelligence Control Plane v1.0

### Mission
Stop building an AI application. Start building a **Control Plane**.

* **Replaceable:** Chat, Models, Prompts, Providers, Interfaces.
* **The Product:** Operations, Resources, Memory, Recovery, Auditability.

> *"If the machine crashed right now, could the operation still be explained, audited, recovered, and resumed?"*  
> If the answer is no, the architecture is incomplete.

---

### Core Architecture

```text
User Objective
        │
        ▼
Operations Engine (src/memoryos/ops_console.py)
        │
        ▼
Operations Planner + Frank-v1 (src/memoryos/frank.py)
        │
        ▼
Resource Fabric (src/memoryos/gpu_backends.py + router.py)
        │
        ▼
Control Plane Coordinator (src/memoryos/control_plane.py)
 ┌──────┼──────────┬───────────┐
 ▼      ▼          ▼           ▼
Memory Telemetry  Declarative  Circuit Breakers
Vault  & Silicon  Plugins      & Budgets
        │
        ▼
Immutable Hash-Chained Ledger (GET /api/ledger/verify)
        │
        ▼
Crash Recovery Engine (RecoveryManager)
```

---

### Non-Negotiable Control Plane Rules

1. **Zero Arbitrary Plugin Code Execution:** Third-party plugins use declarative JSON manifests only (`plugins/<pack>/manifest.json`, `operations.json`, `policies.json`) verified by SHA-256 checksum, SDK version (`1.0`), schema validation, and runtime-enforced `PluginContext` permissions. No `importlib`, `exec()`, or `eval()` on third-party plugin paths.
2. **Operation Budgets:** Every operation runs under an explicit `OperationBudget(timeout_seconds, max_memory_mb, max_cpu_seconds)`. Exceeding any limit transitions the operation to `ABORTED` and writes a chained ledger event.
3. **Circuit Breakers:** `CLOSED` → 5 consecutive failures → `OPEN` → cooldown (`60s`) → `HALF_OPEN` validation → `CLOSED` on success / `OPEN` on failure.
4. **Crash Recovery Engine:** Persists operation states (`CREATED`, `PLANNED`, `QUEUED`, `RUNNING`, `COMPLETE`, `FAILED`, `ABORTED`, `RECOVERING`) in SQLite WAL. On restart, `RUNNING` transitions to `RECOVERING` and `QUEUED`/`RECOVERING` operations are surfaced for re-planning and resumption.
5. **Immutable Hash-Chained Ledger:** Every event links via `event_hash = sha256(previous_hash + canonical_json(payload))` and is auditable at `GET /api/ledger/verify`.

---

### One-Command Control Plane Validation

```bash
python3 NEON_SINGLE_FILE.py
```

Expected exit code `0` and output: `NEON STATUS: CERTIFICATION READY`.

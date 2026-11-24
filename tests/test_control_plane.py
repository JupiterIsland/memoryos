"""Comprehensive Control Plane hardening tests (NEON Final Build Directive).

Covers:
  - Declarative plugin security (manifest, version, unknown op, permissions, tampered hash)
  - Budget enforcement (timeout, memory, CPU)
  - Circuit breaker (open threshold, half-open recovery, re-close)
  - Crash recovery engine (restart resume, queued, running -> recovering)
  - Immutable hash-chained ledger (integrity & tamper detection)
  - Live Studio HTTP endpoints (/api/ledger/verify, /api/plugins, /api/control-plane/health)
"""

from __future__ import annotations

import http.client
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import apps.jupiter_studio as jupiter_studio
import src.memoryos.server as router_server
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
    compute_pack_checksum,
)


def _write_pack(
    root: Path,
    pack_id: str,
    *,
    manifest_override: dict | None = None,
    operations: list | None = None,
    policies: dict | None = None,
    tamper_after_sign: bool = False,
) -> Path:
    d = root / pack_id
    d.mkdir(parents=True, exist_ok=True)
    ops_doc = {"operations": operations if operations is not None else [
        {
            "id": "secret_scan",
            "executor": "builtin.secret_scan",
            "timeout_seconds": 10,
            "memory_limit_mb": 256,
            "cpu_limit_seconds": 10,
            "permissions": ["memory.read", "ledger.write"],
        }
    ]}
    pol_doc = policies if policies is not None else {"allow_network": False}
    ops_raw = (json.dumps(ops_doc, indent=2) + "\n").encode("utf-8")
    pol_raw = (json.dumps(pol_doc, indent=2) + "\n").encode("utf-8")
    (d / "operations.json").write_bytes(ops_raw)
    (d / "policies.json").write_bytes(pol_raw)
    digest = compute_pack_checksum(ops_raw, pol_raw)
    manifest = {
        "id": pack_id,
        "name": "Test Pack",
        "version": "1.0.0",
        "sdk_version": "1.0",
        "permissions": ["memory.read", "ledger.write"],
        "checksum_sha256": f"sha256:{digest}",
    }
    if manifest_override:
        manifest.update(manifest_override)
    (d / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if tamper_after_sign:
        (d / "policies.json").write_text('{"allow_network": true}\n', encoding="utf-8")
    return d


class TestPluginSecurity(unittest.TestCase):
    def test_invalid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "bad_pack"
            d.mkdir()
            (d / "manifest.json").write_text('{"id": "bad_pack"}', encoding="utf-8")
            (d / "operations.json").write_text('{"operations": []}', encoding="utf-8")
            (d / "policies.json").write_text('{}', encoding="utf-8")
            loader = DeclarativePluginLoader()
            with self.assertRaises(ValueError):
                loader.load_pack_dir(d)

    def test_unknown_operation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = _write_pack(
                Path(td),
                "bad_exec",
                operations=[{"id": "evil", "executor": "os.system", "permissions": []}],
            )
            loader = DeclarativePluginLoader()
            with self.assertRaises(ValueError):
                loader.load_pack_dir(d)

    def test_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = _write_pack(Path(td), "old_sdk", manifest_override={"sdk_version": "0.1"})
            loader = DeclarativePluginLoader()
            with self.assertRaises(ValueError):
                loader.load_pack_dir(d)

    def test_permission_violation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = _write_pack(
                Path(td),
                "no_perm",
                manifest_override={"permissions": ["telemetry.read"]},
                operations=[{
                    "id": "secret_scan",
                    "executor": "builtin.secret_scan",
                    "permissions": ["memory.read"],
                }],
            )
            loader = DeclarativePluginLoader()
            with self.assertRaises(PermissionError):
                loader.load_pack_dir(d)

    def test_tampered_hash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = _write_pack(Path(td), "tampered", tamper_after_sign=True)
            loader = DeclarativePluginLoader()
            with self.assertRaises(ValueError):
                loader.load_pack_dir(d)

    def test_allow_network_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = _write_pack(Path(td), "net_pack", policies={"allow_network": True})
            loader = DeclarativePluginLoader()
            with self.assertRaises(PermissionError) as ctx:
                loader.load_pack_dir(d)
            self.assertIn("allow_network", str(ctx.exception))

            summary = loader.load_directory(Path(td))
            self.assertEqual(summary["loaded"], [])
            self.assertEqual(len(summary["rejected"]), 1)
            self.assertEqual(summary["rejected"][0]["pack"], "net_pack")


class TestBudgetEnforcement(unittest.TestCase):
    def test_timeout_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = ImmutableLedger(Path(td) / "l.sqlite")
            with self.assertRaises(BudgetExceededError) as ctx:
                BudgetEnforcer.run_with_budget(
                    lambda: time.sleep(0.25),
                    OperationBudget(timeout_seconds=0.04, max_memory_mb=512, max_cpu_seconds=10.0),
                    ledger=ledger,
                    operation_id="op-timeout",
                )
            self.assertEqual(ctx.exception.metric, "timeout")
            self.assertEqual(ledger.verify()["event_count"], 1)

    def test_memory_limit_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = ImmutableLedger(Path(td) / "l.sqlite")
            with self.assertRaises(BudgetExceededError) as ctx:
                BudgetEnforcer.run_with_budget(
                    lambda: "ok",
                    OperationBudget(timeout_seconds=5.0, max_memory_mb=128, max_cpu_seconds=5.0),
                    estimated_memory_mb=512,
                    ledger=ledger,
                    operation_id="op-mem",
                )
            self.assertEqual(ctx.exception.metric, "memory")

    def test_cpu_limit_enforced(self) -> None:
        def _burn_cpu() -> int:
            total = 0
            for i in range(400_000):
                total += (i * i) % 97
            return total

        with tempfile.TemporaryDirectory() as td:
            ledger = ImmutableLedger(Path(td) / "l.sqlite")
            with self.assertRaises(BudgetExceededError) as ctx:
                BudgetEnforcer.run_with_budget(
                    _burn_cpu,
                    OperationBudget(timeout_seconds=5.0, max_memory_mb=512, max_cpu_seconds=0.0001),
                    ledger=ledger,
                    operation_id="op-cpu",
                )
            self.assertEqual(ctx.exception.metric, "cpu")


class TestCircuitBreaker(unittest.TestCase):
    def test_opens_after_failure_threshold(self) -> None:
        b = CircuitBreaker("prov", failure_threshold=5, cooldown_seconds=60.0)
        for _ in range(5):
            b.record_failure()
        self.assertEqual(b.state, CircuitState.OPEN)
        self.assertFalse(b.can_execute())

    def test_half_open_recovery(self) -> None:
        now = [10.0]
        b = CircuitBreaker("prov", failure_threshold=5, cooldown_seconds=60.0, clock=lambda: now[0])
        for _ in range(5):
            b.record_failure()
        now[0] += 61.0
        self.assertTrue(b.can_execute())
        self.assertEqual(b.state, CircuitState.HALF_OPEN)

    def test_closes_after_success(self) -> None:
        now = [10.0]
        b = CircuitBreaker("prov", failure_threshold=5, cooldown_seconds=60.0, clock=lambda: now[0])
        for _ in range(5):
            b.record_failure()
        now[0] += 61.0
        self.assertTrue(b.can_execute())
        b.record_success()
        self.assertEqual(b.state, CircuitState.CLOSED)
        self.assertEqual(b.failures, 0)


class TestRecoveryEngine(unittest.TestCase):
    def test_resume_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "ops.sqlite"
            RecoveryManager(db).save_state("op-1", OperationState.RUNNING, objective="Audit")
            recovered = RecoveryManager(db).recover_incomplete()
            self.assertEqual(len(recovered), 1)
            self.assertEqual(recovered[0]["operation_id"], "op-1")
            self.assertEqual(recovered[0]["state"], OperationState.RECOVERING.value)

    def test_recover_queued_operation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "ops.sqlite"
            RecoveryManager(db).save_state("op-q", OperationState.QUEUED, objective="Queued task")
            recovered = RecoveryManager(db).recover_incomplete()
            self.assertEqual(recovered[0]["state"], OperationState.QUEUED.value)

    def test_recover_running_operation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "ops.sqlite"
            rm = RecoveryManager(db)
            rm.save_state("op-r", OperationState.RUNNING, objective="Running task")
            rm.save_state("op-done", OperationState.COMPLETE, objective="Done task")
            recovered = RecoveryManager(db).recover_incomplete()
            ids = [r["operation_id"] for r in recovered]
            self.assertEqual(ids, ["op-r"])
            self.assertEqual(RecoveryManager(db).get_state("op-r")["state"], OperationState.RECOVERING.value)


class TestImmutableLedger(unittest.TestCase):
    def test_hash_chain_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = ImmutableLedger(Path(td) / "ledger.sqlite")
            e1 = ledger.append({"event": "one"})
            e2 = ledger.append({"event": "two"})
            self.assertEqual(e2["previous_hash"], e1["event_hash"])
            v = ledger.verify()
            self.assertTrue(v["valid"])
            self.assertEqual(v["event_count"], 2)

    def test_hash_chain_tampering_detection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "ledger.sqlite"
            ledger = ImmutableLedger(db)
            ledger.append({"event": "one"})
            ledger.append({"event": "two"})
            conn = sqlite3.connect(str(db))
            conn.execute("UPDATE control_plane_ledger SET payload_json = ? WHERE seq = 1", ('{"event":"hacked"}',))
            conn.commit()
            conn.close()
            v = ledger.verify()
            self.assertFalse(v["valid"])
            self.assertEqual(v["broken_seq"], 1)


class TestControlPlaneHTTP(unittest.TestCase):
    def test_ledger_verify_plugins_and_health_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            temp_db = Path(td) / "studio_cp.sqlite"
            with mock.patch.object(jupiter_studio, "_get_studio_db_path", return_value=temp_db):
                srv = ThreadingHTTPServer(("127.0.0.1", 0), jupiter_studio.JupiterStudioHandler)
                port = srv.server_address[1]
                th = threading.Thread(target=srv.serve_forever, daemon=True)
                th.start()
                try:
                    base = f"http://127.0.0.1:{port}"
                    with urlopen(f"{base}/api/ledger/verify", timeout=5) as resp:
                        ver = json.loads(resp.read().decode("utf-8"))
                    self.assertTrue(ver["valid"])

                    with urlopen(f"{base}/api/plugins", timeout=5) as resp:
                        plugs = json.loads(resp.read().decode("utf-8"))
                    ids = [p["id"] for p in plugs["loaded"]]
                    self.assertIn("security_pack", ids)
                    self.assertIn("research_pack", ids)
                    self.assertEqual(plugs["rejected"], [])

                    with urlopen(f"{base}/api/control-plane/health", timeout=5) as resp:
                        hlth = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(hlth["status"], "healthy")
                    self.assertIn("ledger", hlth["subsystems"])

                    # Check UI HTML contains LIGHT / DARK / PURPLE GLASS themes, Control Centre, Recovery Banner, and zero icons/SVGs
                    with urlopen(f"{base}/", timeout=5) as resp:
                        html = resp.read().decode("utf-8")
                    for token in ("LIGHT", "DARK", "PURPLE GLASS", "Control Centre", "recovery-banner", "heatFlash"):
                        self.assertIn(token, html)
                    self.assertNotIn("SURPRISE", html)
                    self.assertNotIn("<svg", html)

                    # Check Recovery list & dismiss flow
                    rm = RecoveryManager(temp_db)
                    rm.save_state("op-interrupted-1", OperationState.RUNNING, objective="Scan repo")
                    rm.recover_incomplete()
                    with urlopen(f"{base}/api/ops/recovery", timeout=5) as resp:
                        rec = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(len(rec["recoverable"]), 1)
                    self.assertEqual(rec["recoverable"][0]["state"], "RECOVERING")

                    headers = {"Content-Type": "application/json", "Origin": base}
                    req_dis = Request(
                        f"{base}/api/ops/recovery/dismiss",
                        data=json.dumps({"operation_id": "op-interrupted-1"}).encode("utf-8"),
                        headers=headers,
                        method="POST",
                    )
                    with urlopen(req_dis, timeout=5) as resp:
                        dis = json.loads(resp.read().decode("utf-8"))
                    self.assertTrue(dis["dismissed"])

                    # Check Breakers list & reset flow
                    with urlopen(f"{base}/api/breakers", timeout=5) as resp:
                        br = json.loads(resp.read().decode("utf-8"))
                    self.assertIn("breakers", br)
                    req_rst = Request(
                        f"{base}/api/breakers/reset",
                        data=b"{}",
                        headers=headers,
                        method="POST",
                    )
                    with urlopen(req_rst, timeout=5) as resp:
                        rst = json.loads(resp.read().decode("utf-8"))
                    self.assertTrue(rst["reset"])

                    # Check Declarative Plugin policy approval gate (409 unapproved -> 200 approved)
                    req_unapproved = Request(
                        f"{base}/api/plugins/execute",
                        data=json.dumps({"operation": "security_pack.secret_scan", "approved": False}).encode("utf-8"),
                        headers=headers,
                        method="POST",
                    )
                    with self.assertRaises(HTTPError) as http_exc:
                        urlopen(req_unapproved, timeout=5)
                    self.assertEqual(http_exc.exception.code, 409)
                    http_exc.exception.close()

                    req_approved = Request(
                        f"{base}/api/plugins/execute",
                        data=json.dumps({"operation": "security_pack.secret_scan", "approved": True}).encode("utf-8"),
                        headers=headers,
                        method="POST",
                    )
                    with urlopen(req_approved, timeout=10) as resp:
                        exec_out = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(exec_out["state"], "COMPLETE")
                    self.assertGreater(exec_out["result"]["files_scanned"], 0)
                finally:
                    srv.shutdown()
                    srv.server_close()

    def test_real_plugin_executors_and_approval_policy(self) -> None:
        loader = DeclarativePluginLoader()
        root = Path(jupiter_studio.REPO_ROOT)
        summary = loader.load_directory(root / "plugins")
        self.assertIn("security_pack", summary["loaded"])
        self.assertIn("research_pack", summary["loaded"])

        with self.assertRaises(ApprovalRequiredError):
            loader.execute_operation("security_pack.secret_scan", workspace_root=root, approved=False)

        sec = loader.execute_operation("security_pack.secret_scan", workspace_root=root, approved=True)
        self.assertGreater(sec["result"]["files_scanned"], 0)

        dep = loader.execute_operation("security_pack.dependency_audit", workspace_root=root, approved=True)
        self.assertTrue(dep["result"]["stdlib_core"])
        self.assertEqual(dep["result"]["issues_found"], 0)

        si = loader.execute_operation("research_pack.silicon_health_check", workspace_root=root)
        self.assertIn("gpu_vendor", si["result"])
        self.assertTrue(si["result"]["zero_vram_core"])


class TestRouterServerSecurity(unittest.TestCase):
    def _req(
        self,
        port: int,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            resp = conn.getresponse()
            data = resp.read()
            return resp.status, {k.lower(): v for k, v in resp.getheaders()}, data
        finally:
            conn.close()

    def test_bind_host_policy_and_main_refuses_non_loopback_without_unsafe_lan(self) -> None:
        for host in ("127.0.0.1", "localhost", "::1", "[::1]"):
            self.assertTrue(router_server._is_loopback_bind_host(host), host)
            self.assertIsNone(router_server._bind_host_error(host, unsafe_lan=False), host)

        for host in ("0.0.0.0", "::", "", "192.168.1.25", "router.example"):
            self.assertFalse(router_server._is_loopback_bind_host(host), repr(host))
            self.assertIsNotNone(router_server._bind_host_error(host, unsafe_lan=False), repr(host))
            self.assertIsNone(router_server._bind_host_error(host, unsafe_lan=True), repr(host))

        for bad_host in ("0.0.0.0", "::", ""):
            argv = ["server.py", "--host", bad_host]
            with mock.patch.object(sys, "argv", argv), mock.patch.dict(
                os.environ, {"ROUTER_UNSAFE_LAN": ""}
            ), mock.patch.object(router_server, "create_fallback_server") as srv_cls:
                with self.assertRaises(SystemExit) as ctx:
                    router_server.main()
            self.assertEqual(ctx.exception.code, 2)
            srv_cls.assert_not_called()

        # Explicit --unsafe-lan or ROUTER_UNSAFE_LAN=1 permits non-loopback bind
        fake_srv = mock.MagicMock()
        for argv, env_patch in (
            (["server.py", "--host", "0.0.0.0", "--unsafe-lan"], {"ROUTER_UNSAFE_LAN": ""}),
            (["server.py", "--host", "0.0.0.0"], {"ROUTER_UNSAFE_LAN": "1"}),
        ):
            with mock.patch.object(sys, "argv", argv), mock.patch.dict(
                os.environ, env_patch
            ), mock.patch.object(router_server, "HAS_FASTAPI", False), mock.patch.object(
                router_server, "_init_services", return_value=Path("test.sqlite")
            ), mock.patch.object(
                router_server, "create_fallback_server", return_value=fake_srv
            ) as srv_cls:
                router_server.main()
            srv_cls.assert_called_once()
            fake_srv.serve_forever.assert_called()
            fake_srv.reset_mock()

    def test_fallback_server_enforces_host_origin_referer_and_sec_fetch_site(self) -> None:
        prev_qa_db = router_server._qa_db
        prev_hs = router_server._heat_stream
        with tempfile.TemporaryDirectory() as td:
            temp_db = Path(td) / "router_sec.sqlite"
            srv = router_server.create_fallback_server(host="127.0.0.1", port=0, db_path=temp_db)
            port = srv.server_address[1]
            th = threading.Thread(target=srv.serve_forever, daemon=True)
            th.start()
            try:
                # 1. Legitimate loopback requests succeed
                local_origin = f"http://127.0.0.1:{port}"
                status, hdrs, raw = self._req(
                    port, "GET", "/health", headers={"Host": f"127.0.0.1:{port}", "Origin": local_origin}
                )
                self.assertEqual(status, 200)
                self.assertEqual(hdrs.get("access-control-allow-origin"), local_origin)
                self.assertIn("Origin", hdrs.get("vary", ""))
                self.assertEqual(json.loads(raw.decode("utf-8"))["status"], "healthy")

                status, hdrs, _ = self._req(
                    port, "GET", "/health", headers={"Host": f"localhost:{port}", "Origin": f"http://localhost:{port}"}
                )
                self.assertEqual(status, 200)

                status, _, _ = self._req(
                    port, "OPTIONS", "/api/route", headers={"Host": f"127.0.0.1:{port}", "Origin": local_origin}
                )
                self.assertEqual(status, 204)

                post_body = json.dumps({"mse_delta": 0.01}).encode("utf-8")
                status, _, _ = self._req(
                    port,
                    "POST",
                    "/api/frame-delta",
                    headers={
                        "Host": f"127.0.0.1:{port}",
                        "Origin": local_origin,
                        "Content-Type": "application/json",
                        "Content-Length": str(len(post_body)),
                    },
                    body=post_body,
                )
                self.assertEqual(status, 200)

                # 2. Foreign Origin blocked with 403 across GET, POST, OPTIONS
                for method, path, body in (
                    ("GET", "/health", None),
                    ("OPTIONS", "/api/route", None),
                    ("POST", "/api/frame-delta", post_body),
                ):
                    req_headers = {"Host": f"127.0.0.1:{port}", "Origin": "https://evil.example"}
                    if body is not None:
                        req_headers["Content-Type"] = "application/json"
                        req_headers["Content-Length"] = str(len(body))
                    status, hdrs, _ = self._req(port, method, path, headers=req_headers, body=body)
                    self.assertEqual(status, 403, f"{method} {path} should block foreign Origin")
                    self.assertNotIn("access-control-allow-origin", hdrs)

                # 3. Foreign Host header (DNS rebinding) blocked with 403
                for bad_host in (f"evil.example:{port}", f"localhost.evil.example:{port}"):
                    status, _, _ = self._req(port, "GET", "/health", headers={"Host": bad_host})
                    self.assertEqual(status, 403, bad_host)
                    status, _, _ = self._req(
                        port,
                        "POST",
                        "/api/frame-delta",
                        headers={
                            "Host": bad_host,
                            "Content-Type": "application/json",
                            "Content-Length": str(len(post_body)),
                        },
                        body=post_body,
                    )
                    self.assertEqual(status, 403, bad_host)

                # 4. Sec-Fetch-Site: cross-site and foreign Referer blocked with 403
                status, _, _ = self._req(
                    port,
                    "GET",
                    "/health",
                    headers={"Host": f"127.0.0.1:{port}", "Sec-Fetch-Site": "cross-site"},
                )
                self.assertEqual(status, 403)

                status, _, _ = self._req(
                    port,
                    "POST",
                    "/api/frame-delta",
                    headers={
                        "Host": f"127.0.0.1:{port}",
                        "Referer": "https://evil.example/csrf.html",
                        "Content-Type": "application/json",
                        "Content-Length": str(len(post_body)),
                    },
                    body=post_body,
                )
                self.assertEqual(status, 403)

                # Same-origin Referer without Origin succeeds
                status, _, _ = self._req(
                    port,
                    "POST",
                    "/api/frame-delta",
                    headers={
                        "Host": f"127.0.0.1:{port}",
                        "Referer": f"http://127.0.0.1:{port}/",
                        "Content-Type": "application/json",
                        "Content-Length": str(len(post_body)),
                    },
                    body=post_body,
                )
                self.assertEqual(status, 200)
            finally:
                srv.shutdown()
                srv.server_close()
                if router_server._qa_db is not None:
                    try:
                        router_server._qa_db.close()
                    except Exception:
                        pass
                router_server._qa_db = prev_qa_db
                router_server._heat_stream = prev_hs

    def test_lan_and_testserver_origin_rules(self) -> None:
        # LAN-bound: matching Host origin allowed, cross-origin rejected
        self.assertIsNone(
            router_server._validate_local_request(
                host="192.168.1.50:5000",
                origin="http://192.168.1.50:5000",
                sec_fetch_site="same-origin",
                referer="",
                loopback_bound=False,
            )
        )
        self.assertIsNotNone(
            router_server._validate_local_request(
                host="192.168.1.50:5000",
                origin="https://evil.example",
                sec_fetch_site="cross-site",
                referer="",
                loopback_bound=False,
            )
        )
        # FastAPI TestClient extra host 'testserver' allowed only when passed explicitly
        self.assertIsNone(
            router_server._validate_local_request(
                host="testserver",
                origin="",
                sec_fetch_site="",
                referer="",
                loopback_bound=True,
                extra_local_hosts=("testserver",),
            )
        )
        self.assertIsNotNone(
            router_server._validate_local_request(
                host="testserver",
                origin="",
                sec_fetch_site="",
                referer="",
                loopback_bound=True,
            )
        )

    def test_verify_script_quick_json(self) -> None:
        import subprocess
        import sys

        repo_root = Path(__file__).resolve().parents[1]
        proc = subprocess.run(
            [sys.executable, "-B", str(repo_root / "verify.py"), "--quick", "--json"],
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["all_passed"])
        for key in ("py_compile", "neon", "ewc_audit", "frank_demo", "mse_gate"):
            self.assertIn(key, payload["checks"])
            self.assertTrue(payload["checks"][key]["passed"], key)


if __name__ == "__main__":
    unittest.main()

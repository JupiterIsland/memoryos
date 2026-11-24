# tests/test_grant_ledger_reconciliation.py
# Read-only. Does not pin, write, or mutate the vault.
# Adapted from an external audit sketch to validate the real AMD Token Lab export schema.
# Run: pytest tests/test_grant_ledger_reconciliation.py -v
#  or: python -B -m unittest tests/test_grant_ledger_reconciliation.py -v

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    import pytest
except ImportError:
    pytest = None

from memoryos.grant_ledger import DEFAULT_EXPORT_PATH, load_audit_trail, load_ledger_snapshot

GRANT_ID = "1E13760B"
WINDOW = "2026-11-14"

if pytest is not None:
    @pytest.fixture(scope="module")
    def ledger():
        return load_ledger_snapshot(grant_id=GRANT_ID, window=WINDOW)

    @pytest.fixture(scope="module")
    def trail():
        return load_audit_trail(grant_id=GRANT_ID, window=WINDOW)


def check_request_count_reconciles(ledger):
    """Per-model reqs must sum to usage_totals.requests and match raw request rows."""
    per_model = sum(m["requests"] for m in ledger["models"].values())
    assert per_model == ledger["gateway"]["allowed"], (
        f"reqs {per_model} != usage_totals.requests {ledger['gateway']['allowed']}"
    )
    assert len(ledger["requests"]) == per_model, (
        f"raw requests {len(ledger['requests'])} != per_model {per_model}"
    )


def check_token_count_reconciles(ledger):
    """Per-model tokens must sum to usage_totals.tokens and per-request token totals."""
    per_model = sum(m["tokens"] for m in ledger["models"].values())
    per_req = sum(r["tokens"] for r in ledger["requests"])
    assert per_model == ledger["gateway"]["tokens"], (
        f"toks {per_model} != gateway {ledger['gateway']['tokens']}"
    )
    assert per_req == per_model, (
        f"per_req toks {per_req} != per_model toks {per_model}"
    )


def check_upts_internal_consistency_and_honest_upstream_gap(ledger):
    """
    Per-model µpts must equal usage_totals.points_micro and the sum of raw request µpts (74).
    Any difference vs account.budget_used_micro (78) must NEVER be masked by a synthesized
    overhead bucket: if the raw export provides no overhead_attribution, unattributed_gap
    must be surfaced explicitly.
    """
    per_model = sum(m["upts"] for m in ledger["models"].values())
    per_req = sum(r["upts"] for r in ledger["requests"])
    usage_totals_upts = ledger["grant"]["usage_totals_upts"]
    consumed = ledger["grant"]["consumed"]

    assert per_model == usage_totals_upts == per_req, (
        f"internal µpts mismatch: per_model={per_model}, "
        f"usage_totals={usage_totals_upts}, per_req={per_req}"
    )

    overhead = ledger.get("overhead_attribution", {})
    attributed_total = overhead.get("total", 0) if isinstance(overhead, dict) else 0
    expected_unattributed = (consumed - per_model) - attributed_total
    assert ledger["grant"]["unattributed_gap"] == expected_unattributed, (
        f"unattributed_gap mismatch: got {ledger['grant']['unattributed_gap']}, "
        f"expected {expected_unattributed}"
    )
    # Current raw AMD Token Lab export has no overhead_attribution key:
    # verify grant_ledger.py does not fabricate one and surfaces the 4 µpts gap honestly.
    assert overhead == {}, f"unexpected fabricated overhead_attribution: {overhead!r}"
    assert ledger["grant"]["unattributed_gap"] == 4


def check_unit_label_is_consistent(ledger):
    """Canonical unit label must be 'µpts' across ledger views and the Quiet Advisor UI."""
    labels = {ledger["grant"]["unit_label"], ledger["gateway"]["unit_label"]}
    assert labels == {"µpts"}, f"unit label drift across ledger views: {labels}"

    ui_server = REPO_ROOT / "apps" / "quiet_advisor_ui" / "server.py"
    if ui_server.is_file():
        src = ui_server.read_text(encoding="utf-8")
        assert "µpts" in src, "Quiet Advisor UI missing canonical 'µpts' label"
        assert "ppts" not in src, "Quiet Advisor UI contains drifted 'ppts' label"
        assert "UPTS" not in src, "Quiet Advisor UI contains drifted 'UPTS' label"


def check_audit_trail_covers_every_ledger_request(ledger, trail):
    """No request may exist in the ledger without a trail entry."""
    ledger_ids = {r["id"] for r in ledger["requests"]}
    trail_ids = {r["id"] for r in trail["entries"]}
    missing = ledger_ids - trail_ids
    assert not missing, f"ledger requests absent from audit trail: {missing}"


def check_audit_trail_has_no_orphans(ledger, trail):
    """No trail entry may reference a request outside the ledger window."""
    ledger_ids = {r["id"] for r in ledger["requests"]}
    orphans = [e["id"] for e in trail["entries"] if e["id"] not in ledger_ids]
    assert not orphans, f"trail entries with no ledger request: {orphans}"


def check_error_burst_is_visible_in_raw_requests(ledger, trail):
    """
    The raw AMD Token Lab export (tokenlab.requests) must explicitly contain
    all 8 historical error rows reported in usage_totals.errors.
    """
    errors = [e for e in trail["entries"] if e["status"] != "OK"]
    expected_errors = ledger["gateway"]["errors"]
    assert len(errors) == expected_errors == 8, (
        f"expected {expected_errors} error rows in audit trail, found {len(errors)}"
    )
    assert all(e["model"] == "d3" for e in errors), "unexpected model in error burst"
    assert all(e.get("finish_reason") == "client_error" for e in errors), (
        "unexpected finish_reason in error burst"
    )


# Pytest entry points
def test_request_count_reconciles(ledger):
    check_request_count_reconciles(ledger)


def test_token_count_reconciles(ledger):
    check_token_count_reconciles(ledger)


def test_upts_internal_consistency_and_honest_upstream_gap(ledger):
    check_upts_internal_consistency_and_honest_upstream_gap(ledger)


def test_unit_label_is_consistent(ledger):
    check_unit_label_is_consistent(ledger)


def test_audit_trail_covers_every_ledger_request(ledger, trail):
    check_audit_trail_covers_every_ledger_request(ledger, trail)


def test_audit_trail_has_no_orphans(ledger, trail):
    check_audit_trail_has_no_orphans(ledger, trail)


def test_error_burst_is_visible_in_raw_requests(ledger, trail):
    check_error_burst_is_visible_in_raw_requests(ledger, trail)


# Unittest TestCase wrapper for standard verify.py CI runner
@unittest.skipUnless(
    DEFAULT_EXPORT_PATH.is_file(),
    "Local memory/tokenlab_export.json not present in fresh clone",
)
class TestGrantLedgerReconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = load_ledger_snapshot(grant_id=GRANT_ID, window=WINDOW)
        cls.trail = load_audit_trail(grant_id=GRANT_ID, window=WINDOW)

    def test_request_count_reconciles(self):
        check_request_count_reconciles(self.ledger)

    def test_token_count_reconciles(self):
        check_token_count_reconciles(self.ledger)

    def test_upts_internal_consistency_and_honest_upstream_gap(self):
        check_upts_internal_consistency_and_honest_upstream_gap(self.ledger)

    def test_unit_label_is_consistent(self):
        check_unit_label_is_consistent(self.ledger)

    def test_audit_trail_covers_every_ledger_request(self):
        check_audit_trail_covers_every_ledger_request(self.ledger, self.trail)

    def test_audit_trail_has_no_orphans(self):
        check_audit_trail_has_no_orphans(self.ledger, self.trail)

    def test_error_burst_is_visible_in_raw_requests(self):
        check_error_burst_is_visible_in_raw_requests(self.ledger, self.trail)


if __name__ == "__main__":
    unittest.main()

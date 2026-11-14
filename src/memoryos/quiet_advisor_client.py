"""Re-exports QuietAdvisorClient, MemoryOSRouterClient, compute_mse_delta, and extract_cv2_frame."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_CLIENT_PATH = Path(__file__).resolve().parents[2] / "apps" / "jupiter-tv-desktop-v2" / "quiet_advisor_client.py"
_spec = importlib.util.spec_from_file_location("_jupiter_quiet_advisor_client", str(_CLIENT_PATH))
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

QuietAdvisorClient = _mod.QuietAdvisorClient
MemoryOSRouterClient = _mod.MemoryOSRouterClient
compute_mse_delta = _mod.compute_mse_delta
extract_cv2_frame = _mod.extract_cv2_frame

__all__ = [
    "QuietAdvisorClient",
    "MemoryOSRouterClient",
    "compute_mse_delta",
    "extract_cv2_frame",
]

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.memoryos.browser_app import ContextSyncBridge
from src.memoryos.core.heat_stream import MemoryHeatStream


class TestHeatStreamSmoke(unittest.TestCase):
    def test_heat_stream_and_browser_bridge_in_temp_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = MemoryHeatStream(
                tlb_cache_dir=str(root / "tlb"),
                temp_graph_path=str(root / "graph"),
                checkpoint_dir=str(root / "checkpoints"),
                scan_interval=5.0,
            )
            hot_blocks = engine.scan_for_hot_memories()
            self.assertIsInstance(hot_blocks, list)
            context = engine.get_hot_context(limit=3)
            self.assertIsInstance(context, str)

            browser_file = root / "browser_context.md"
            bridge = ContextSyncBridge(
                memoryos_cli_dir=str(root),
                browser_context_file=str(browser_file),
            )
            sync_result = bridge.export_context_file(output_path=str(browser_file))
            self.assertTrue(sync_result or browser_file.exists())


if __name__ == "__main__":
    unittest.main()

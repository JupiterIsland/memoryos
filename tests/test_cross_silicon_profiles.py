"""Cross-silicon hardware classification, console companion, and zero-VRAM routing tests.

Covers PC, Console, Mobile ARM, and Server processors:
- Consoles: Xbox Series X|S, PlayStation 5, Nintendo Switch
- PC/Laptop: AMD Ryzen, Intel Core Ultra / Xeon, Apple M-Series, Qualcomm Snapdragon X
- Mobile ARM: Qualcomm Snapdragon, Apple A-Series, Huawei Kirin, MediaTek Dimensity,
              Samsung Exynos, Google Tensor, UNISOC
- Server/Enterprise: Huawei Kunpeng, NVIDIA Grace, Ampere ARM, IBM POWER
"""

from __future__ import annotations

import time
import unittest

from src.memoryos.frank import DEFAULT_FRANK_WEIGHTS_PATH, FrankModel
from src.memoryos.gpu_backends import (
    ConsoleCompanionManager,
    SILICON_CATALOG,
    classify_silicon,
)
from src.memoryos.speculative_offload import DEFAULT_WEIGHTS_PATH, SpeculativeOffloadModel


class TestCrossSiliconProfiles(unittest.TestCase):
    def test_console_processors_ps5_xbox_switch(self) -> None:
        ps5 = classify_silicon("PlayStation 5 AMD Oberon Zen 2 APU")
        xbox = classify_silicon("Xbox Series X Scarlett Custom APU")
        switch = classify_silicon("Nintendo Switch NVIDIA Tegra")

        self.assertEqual(ps5.category, "console")
        self.assertEqual(ps5.vendor, "AMD")
        self.assertTrue(ps5.unified_memory)
        self.assertEqual(ps5.recommended_route, "console_companion_cloud")

        self.assertEqual(xbox.category, "console")
        self.assertEqual(xbox.vendor, "AMD")
        self.assertTrue(xbox.unified_memory)
        self.assertEqual(xbox.recommended_route, "console_companion_cloud")

        self.assertEqual(switch.category, "console")
        self.assertEqual(switch.vendor, "NVIDIA")
        self.assertEqual(switch.isa, "arm64")

    def test_pc_and_laptop_processors_apple_intel_snapdragon_amd(self) -> None:
        apple_m = classify_silicon("Apple M4 Max")
        intel = classify_silicon("Intel Core Ultra 9 285H")
        snap_x = classify_silicon("Qualcomm Snapdragon X Elite")
        amd = classify_silicon("AMD Ryzen 9 7945HX")

        self.assertEqual((apple_m.vendor, apple_m.isa, apple_m.unified_memory), ("Apple", "arm64", True))
        self.assertEqual((intel.vendor, intel.isa, intel.unified_memory), ("Intel", "x86_64", False))
        self.assertEqual((snap_x.vendor, snap_x.isa, snap_x.unified_memory), ("Qualcomm", "arm64", True))
        self.assertEqual((amd.vendor, amd.isa, amd.recommended_route), ("AMD", "x86_64", "lemonade_or_tokenlab"))

    def test_mobile_arm_processors_huawei_snapdragon_apple_mediatek_exynos_tensor_unisoc(self) -> None:
        cases = [
            ("Huawei HiSilicon Kirin 9010", "Huawei", "arm64", "frank_edge_plus_cloud"),
            ("Qualcomm Snapdragon 8 Elite", "Qualcomm", "arm64", "frank_edge_plus_cloud"),
            ("Apple A18 Pro iPhone", "Apple", "arm64", "frank_edge_plus_cloud"),
            ("MediaTek Dimensity 9400", "MediaTek", "arm64", "frank_edge_plus_cloud"),
            ("Samsung Exynos 2500", "Samsung", "arm64", "frank_edge_plus_cloud"),
            ("Google Tensor G4 Pixel", "Google", "arm64", "frank_edge_plus_cloud"),
            ("UNISOC Tiger T820", "UNISOC", "arm64", "cloud_offload_strict"),
        ]
        for chip, expected_vendor, expected_isa, expected_route in cases:
            spec = classify_silicon(chip)
            self.assertEqual(spec.vendor, expected_vendor, chip)
            self.assertEqual(spec.isa, expected_isa, chip)
            self.assertEqual(spec.category, "mobile_arm", chip)
            self.assertTrue(spec.unified_memory, chip)
            self.assertEqual(spec.recommended_route, expected_route, chip)
            self.assertTrue(spec.local_frank_supported, chip)

    def test_server_specialists_kunpeng_grace_ampere_power(self) -> None:
        kunpeng = classify_silicon("Huawei Kunpeng 920")
        grace = classify_silicon("NVIDIA Grace GB200")
        ampere = classify_silicon("Ampere Altra Max")
        power = classify_silicon("IBM POWER10")

        self.assertEqual((kunpeng.vendor, kunpeng.isa), ("Huawei", "arm64"))
        self.assertEqual((grace.vendor, grace.isa, grace.unified_memory), ("NVIDIA", "arm64", True))
        self.assertEqual((ampere.vendor, ampere.isa), ("Ampere", "arm64"))
        self.assertEqual((power.vendor, power.isa), ("IBM", "ppc64le"))
        self.assertGreaterEqual(len(SILICON_CATALOG), 18)

    def test_console_companion_d3_gate_ps5_and_xbox(self) -> None:
        for mode in ("ps_remote_play", "xbox_cloud_companion", "hdmi_capture"):
            mgr = ConsoleCompanionManager(mode=mode)
            started = mgr.start_companion()
            self.assertEqual(started["status"], "COMPANION_ACTIVE")
            self.assertEqual(started["mode"], mode)
            self.assertIn("0 MB", started["vram_overhead_on_console"])

            # 8 static frames (skipped) + 2 scene-change frames (triggered)
            deltas = [1.2, 2.5, 0.4, 3.1, 18.5, 0.9, 1.1, 24.0, 2.0, 0.5]
            actions = [mgr.process_incoming_frame_delta(d, threshold=12.0)["action"] for d in deltas]
            self.assertEqual(actions.count("SKIP_ZERO_COST"), 8)
            self.assertEqual(actions.count("TRIGGER_CLOUD_VLM"), 2)

    def test_zero_vram_pure_python_models_portable_latency(self) -> None:
        frank = FrankModel.load(DEFAULT_FRANK_WEIGHTS_PATH)
        spec_mlp = SpeculativeOffloadModel.load(DEFAULT_WEIGHTS_PATH)

        t0 = time.perf_counter()
        pred = frank.predict("review this architecture and check vram headroom")
        frank_us = (time.perf_counter() - t0) * 1_000_000.0

        t1 = time.perf_counter()
        decision = spec_mlp.decide_with_confidence([0.85, 0.72, 0.15, 0.10])
        mlp_us = (time.perf_counter() - t1) * 1_000_000.0

        self.assertIn(pred["intent"], ("architecture", "vram_reclaim", "fast_code", "large_design", "cheap_bg", "memory_pin"))
        self.assertIn(decision["action"], ("offload_now", "digest", "hold"))
        self.assertLess(frank_us, 10_000.0)
        self.assertLess(mlp_us, 5_000.0)


if __name__ == "__main__":
    unittest.main()

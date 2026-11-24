"""
Unit tests verifying Phase 1 NVIDIA telemetry, multi-GPU safety, and simulation guard fixes.
Covers acceptance criteria in docs/specs/NVIDIA_BACKEND_ASSESSMENT.md.
"""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from apex_core.engine import GPUContextManager
from src.memoryos.core.heat_stream import MemoryHeatStream
from src.memoryos.core.neural_memory_graph import GPUTelemetry, NeuralMemoryGraph
from src.memoryos.gpu_backends import (
    HardwareProfile,
    MultiGPUDetector,
    _read_linux_unified_memory_mb,
)
from src.memoryos.integrations.riva_voice import RivaVoiceClient
from src.memoryos.router import get_policy_telemetry, route_task


class TestNvidiaTelemetrySafety(unittest.TestCase):
    def test_policy_telemetry_measures_positive_cpu_gate_ms(self) -> None:
        tel = get_policy_telemetry()
        self.assertIsInstance(tel["cpu_gate_ms"], float)
        self.assertGreater(tel["cpu_gate_ms"], 0.0)
        self.assertLess(tel["cpu_gate_ms"], 50.0)
        self.assertIn(f"{tel['cpu_gate_ms']:.3f}ms", tel["routing_engine"])

    def test_route_task_prefer_local_uses_runtime_detection_not_hardcoded_rtx3070(self) -> None:
        cpu_profile = HardwareProfile(
            vendor="cpu_fallback",
            device_name="CPU Mode (Zero Local VRAM)",
            total_vram_mb=0,
            used_vram_mb=0,
            free_vram_mb=0,
            utilization_pct=0.0,
            temperature_c=None,
            power_watts=None,
            telemetry_source="cpu_only",
        )
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite"
            with patch.object(MultiGPUDetector, "get_active_profile", return_value=cpu_profile):
                res = route_task(
                    "Check local routing telemetry",
                    prefer_local=True,
                    save_checkpoint=False,
                    log_to_advisor=False,
                    db_path=db_path,
                )
        self.assertNotEqual(res["gpu_id"], "local-rtx3070")
        self.assertEqual(res["gpu_id"], "local-cpu")
        self.assertEqual(res["gpu_memory_used_mb"], 0)
        self.assertEqual(res["gpu_utilization_percent"], 0.0)
        self.assertEqual(res["routing_policy"], "local_cpu_fallback_worker")

    def test_gpu_context_manager_cpu_only_and_separated_stats(self) -> None:
        with patch("apex_core.engine.TORCH_AVAILABLE", False), patch.object(
            MultiGPUDetector, "detect_nvidia", return_value=None
        ):
            mgr = GPUContextManager()
            self.assertEqual(mgr.get_device(), "cpu")
            self.assertEqual(mgr.get_device_memory(), 0.0)
            self.assertEqual(mgr.get_device_utilization(), 0.0)
            stats = mgr.get_memory_stats()
            self.assertFalse(stats["available"])
            self.assertEqual(stats["source"], "unavailable")
            self.assertIsNone(stats["total_mb"])
            self.assertIsNone(stats["free_mb"])
            self.assertIsNone(stats["torch_allocated_mb"])

    def test_gpu_context_manager_multi_gpu_selection_and_validation(self) -> None:
        fake_torch = SimpleNamespace(
            cuda=SimpleNamespace(
                is_available=lambda: True,
                device_count=lambda: 2,
            ),
            backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False)),
            version=SimpleNamespace(hip=None),
        )
        with patch("apex_core.engine.TORCH_AVAILABLE", True), patch(
            "apex_core.engine.torch", fake_torch, create=True
        ):
            mgr = GPUContextManager(device_index=1)
            self.assertEqual(mgr.get_device(), "cuda:1")
            self.assertEqual(mgr.select_device(0), "cuda:0")
            with self.assertRaises(ValueError):
                GPUContextManager(device_index=2)
            with self.assertRaises(ValueError):
                mgr.select_device(-1)

    def test_neural_memory_graph_missing_telemetry_never_routes_to_gpu_vram(self) -> None:
        with patch.dict("sys.modules", {"pynvml": None}), patch.object(
            MultiGPUDetector, "detect_nvidia", return_value=None
        ):
            tel = GPUTelemetry(allow_simulation=False)
            mem = tel.get_gpu_memory_info()
            self.assertFalse(mem["available"])
            self.assertFalse(mem["simulated"])
            self.assertEqual(mem["telemetry_status"], "unavailable")
            self.assertIsNone(mem["total_mb"])
            self.assertIsNone(tel.get_gpu_load())

            with tempfile.TemporaryDirectory() as tmp:
                hs = MemoryHeatStream(
                    tlb_cache_dir=tmp,
                    temp_graph_path=tmp,
                    checkpoint_dir=tmp,
                )
                graph = NeuralMemoryGraph(hs)
                graph.gpu = tel
                # Even high heat_score must not route to gpu_vram without verified live telemetry
                tier = graph.predict_memory_tier("block-1", heat_score=0.95, access_frequency=10)
                self.assertEqual(tier, "cpu_cache")
                report = graph.voice_status_report()
                self.assertIn("unavailable", report)

    def test_neural_memory_graph_simulation_flag_never_fools_placement(self) -> None:
        with patch.dict("sys.modules", {"pynvml": None}), patch.object(
            MultiGPUDetector, "detect_nvidia", return_value=None
        ):
            tel = GPUTelemetry(allow_simulation=True)
            mem = tel.get_gpu_memory_info()
            self.assertFalse(mem["available"])
            self.assertTrue(mem["simulated"])
            self.assertEqual(mem["telemetry_status"], "simulated")

            with tempfile.TemporaryDirectory() as tmp:
                hs = MemoryHeatStream(
                    tlb_cache_dir=tmp,
                    temp_graph_path=tmp,
                    checkpoint_dir=tmp,
                )
                graph = NeuralMemoryGraph(hs)
                graph.gpu = tel
                tier = graph.predict_memory_tier("block-1", heat_score=0.95, access_frequency=10)
                self.assertNotEqual(tier, "gpu_vram")

    def test_riva_voice_client_explicit_unavailable_vs_simulated(self) -> None:
        with patch.dict("sys.modules", {"riva": None, "riva.client": None}):
            client = RivaVoiceClient(allow_simulation=False)
            status = client.get_backend_status()
            self.assertFalse(status["available"])
            self.assertFalse(status["simulated"])
            self.assertEqual(status["mode"], "unavailable")
            self.assertEqual(client.text_to_speech("hello"), b"")
            self.assertEqual(client.speech_to_text("dummy.wav"), "")

            sim_client = RivaVoiceClient(allow_simulation=True)
            sim_status = sim_client.get_backend_status()
            self.assertTrue(sim_status["simulated"])
            self.assertEqual(sim_status["mode"], "simulated")
            self.assertTrue(sim_client.text_to_speech("hello").startswith(b"PCM_AUDIO_SIMULATION"))

    def test_detect_nvidia_dgx_spark_gb10_unified_memory_na_fallback(self) -> None:
        fake_smi_proc = SimpleNamespace(
            returncode=0,
            stdout="NVIDIA GB10, [N/A], [N/A], [N/A], 14, 58, [N/A]\n",
        )
        with patch("src.memoryos.gpu_backends.shutil.which", return_value="/usr/bin/nvidia-smi"), patch(
            "src.memoryos.gpu_backends.subprocess.run", return_value=fake_smi_proc
        ), patch(
            "src.memoryos.gpu_backends._read_linux_unified_memory_mb",
            return_value=(128000, 18400, 109600),
        ):
            prof = MultiGPUDetector.detect_nvidia(device_index=0)

        self.assertIsNotNone(prof)
        self.assertEqual(prof.vendor, "nvidia")
        self.assertEqual(prof.device_name, "NVIDIA GB10")
        self.assertTrue(prof.is_unified_memory)
        self.assertEqual(prof.total_vram_mb, 128000)
        self.assertEqual(prof.used_vram_mb, 18400)
        self.assertEqual(prof.free_vram_mb, 109600)
        self.assertEqual(prof.utilization_pct, 14.0)
        self.assertEqual(prof.temperature_c, 58.0)
        self.assertIsNone(prof.power_watts)
        self.assertEqual(prof.telemetry_source, "nvidia-smi+proc_meminfo_unified")

    def test_read_linux_unified_memory_mb_parses_proc_meminfo(self) -> None:
        sample = (
            "MemTotal:       131072000 kB\n"
            "MemFree:         20480000 kB\n"
            "MemAvailable:   110592000 kB\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            meminfo = Path(tmp) / "meminfo"
            meminfo.write_text(sample, encoding="utf-8")
            parsed = _read_linux_unified_memory_mb(meminfo)
        self.assertEqual(parsed, (128000, 20000, 108000))


if __name__ == "__main__":
    unittest.main()

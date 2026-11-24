"""
Multi-Vendor GPU Backend & Console Companion Layer for MemoryOS.

Supports hardware-aware telemetry and routing policies across:
- NVIDIA GPUs (RTX / GTX via NVML & nvidia-smi)
- AMD GPUs (Radeon / Instinct via sysfs & ROCm rocm-smi)
- Intel Arc / Iris (via sysfs / DirectML telemetry)
- Gaming Handhelds (Steam Deck, ASUS ROG Ally, Lenovo Legion Go APUs)
- Console Companion Mode (Capture card / Remote Play stream monitoring for PS5, Xbox, Switch)
"""

from __future__ import annotations

import json
import math
import os
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class HardwareProfile:
    vendor: str  # "nvidia", "amd", "intel", "handheld_apu", "cpu_fallback", "console_capture"
    device_name: str
    total_vram_mb: int
    used_vram_mb: int
    free_vram_mb: int
    utilization_pct: float
    temperature_c: Optional[float]
    power_watts: Optional[float]
    telemetry_source: str
    is_handheld: bool = False
    console_mode_active: bool = False
    is_unified_memory: bool = False


def _parse_optional_float(raw: str) -> Optional[float]:
    """Parse an nvidia-smi numeric field, returning None for [N/A] / [Not Supported] / empty."""
    cleaned = raw.strip()
    if not cleaned or cleaned.startswith("[") or cleaned.upper() in ("N/A", "NOT SUPPORTED", "NONE"):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _read_linux_unified_memory_mb(meminfo_path: Path = Path("/proc/meminfo")) -> Optional[tuple[int, int, int]]:
    """Read (total_mb, used_mb, free_mb) from Linux /proc/meminfo for unified-memory GPUs (e.g. GB10 / DGX Spark)."""
    if not meminfo_path.exists():
        return None
    try:
        values_kb: Dict[str, int] = {}
        for line in meminfo_path.read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            key, rest = line.split(":", 1)
            tokens = rest.strip().split()
            if tokens and tokens[0].isdigit():
                values_kb[key.strip()] = int(tokens[0])
        total_kb = values_kb.get("MemTotal")
        if not total_kb:
            return None
        avail_kb = values_kb.get("MemAvailable")
        if avail_kb is None:
            avail_kb = (
                values_kb.get("MemFree", 0)
                + values_kb.get("Buffers", 0)
                + values_kb.get("Cached", 0)
            )
        total_mb = int(total_kb // 1024)
        free_mb = int(avail_kb // 1024)
        used_mb = max(0, total_mb - free_mb)
        return total_mb, used_mb, free_mb
    except Exception:
        return None


class MultiGPUDetector:
    """Detects active graphics hardware and handles vendor-specific policies."""

    @staticmethod
    def detect_nvidia(device_index: int = 0) -> Optional[HardwareProfile]:
        """Detect NVIDIA GPU via nvidia-smi if available for the specified device index.

        Handles unified-memory NVIDIA platforms (e.g., DGX Spark / GB10) where nvidia-smi
        reports [N/A] or [Not Supported] for discrete VRAM fields by falling back to /proc/meminfo.
        """
        smi = shutil.which("nvidia-smi") or shutil.which("nvidia-smi.exe")
        if not smi:
            # Check default Windows path
            win_smi = Path(r"C:\Windows\System32\nvidia-smi.exe")
            if win_smi.exists():
                smi = str(win_smi)

        if not smi:
            return None

        try:
            cmd = [
                smi,
                "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip():
                lines = [ln.strip() for ln in res.stdout.strip().splitlines() if ln.strip()]
                if not (0 <= device_index < len(lines)):
                    return None
                parts = [p.strip() for p in lines[device_index].split(",")]
                if len(parts) >= 5:
                    name = parts[0]
                    raw_total = _parse_optional_float(parts[1])
                    raw_used = _parse_optional_float(parts[2])
                    raw_free = _parse_optional_float(parts[3])
                    raw_util = _parse_optional_float(parts[4])
                    temp = _parse_optional_float(parts[5]) if len(parts) > 5 else None
                    power = _parse_optional_float(parts[6]) if len(parts) > 6 else None

                    name_lower = name.lower()
                    is_unified = any(k in name_lower for k in ("gb10", "dgx spark", "tegra", "orin"))
                    telemetry_source = "nvidia-smi"

                    if raw_total is None or raw_used is None or raw_free is None:
                        is_unified = True
                        unified_mem = _read_linux_unified_memory_mb()
                        if unified_mem is not None:
                            total, used, free = unified_mem
                            telemetry_source = "nvidia-smi+proc_meminfo_unified"
                        else:
                            total = int(raw_total) if raw_total is not None else 0
                            used = int(raw_used) if raw_used is not None else 0
                            free = int(raw_free) if raw_free is not None else 0
                            telemetry_source = "nvidia-smi_unified_unavailable"
                    else:
                        total = max(0, int(raw_total))
                        used = max(0, int(raw_used))
                        free = max(0, int(raw_free))

                    util = max(0.0, min(100.0, float(raw_util))) if (raw_util is not None and math.isfinite(raw_util)) else 0.0
                    return HardwareProfile(
                        vendor="nvidia",
                        device_name=name,
                        total_vram_mb=total,
                        used_vram_mb=used,
                        free_vram_mb=free,
                        utilization_pct=util,
                        temperature_c=temp if (temp is not None and math.isfinite(temp)) else None,
                        power_watts=power if (power is not None and math.isfinite(power)) else None,
                        telemetry_source=telemetry_source,
                        is_unified_memory=is_unified,
                    )
        except Exception:
            pass
        return None

    @staticmethod
    def detect_amd() -> Optional[HardwareProfile]:
        """Detect AMD GPU via sysfs (Linux) or rocm-smi."""
        # Check Linux sysfs DRM
        drm_path = Path("/sys/class/drm")
        if drm_path.exists():
            cards = sorted(
                (p for p in drm_path.glob("card[0-9]*") if p.name[4:].isdigit()),
                key=lambda p: int(p.name[4:]),
            )
            for card in cards:
                device_file = card / "device/vendor"
                if device_file.exists():
                    try:
                        vendor_id = device_file.read_text(encoding="utf-8", errors="replace").strip().lower()
                        if vendor_id == "0x1002":  # AMD PCI Vendor ID
                            # Read total VRAM if exposed by amdgpu
                            vram_file = card / "device/mem_info_vram_total"
                            used_file = card / "device/mem_info_vram_used"
                            busy_file = card / "device/gpu_busy_percent"
                            total_mb = 0
                            used_mb = 0
                            util_pct = 0.0
                            temp_c: Optional[float] = None
                            if vram_file.exists():
                                total_mb = max(0, int(int(vram_file.read_text(encoding="utf-8").strip()) / (1024 * 1024)))
                            if used_file.exists():
                                used_mb = max(0, int(int(used_file.read_text(encoding="utf-8").strip()) / (1024 * 1024)))
                            if busy_file.exists():
                                raw_busy = _parse_optional_float(busy_file.read_text(encoding="utf-8"))
                                if raw_busy is not None and math.isfinite(raw_busy):
                                    util_pct = max(0.0, min(100.0, raw_busy))
                            hwmon_dir = card / "device/hwmon"
                            if hwmon_dir.is_dir():
                                for temp_file in sorted(hwmon_dir.glob("hwmon*/temp1_input")):
                                    raw_milli_c = _parse_optional_float(temp_file.read_text(encoding="utf-8"))
                                    if raw_milli_c is not None and math.isfinite(raw_milli_c):
                                        temp_c = round(raw_milli_c / 1000.0, 1)
                                        break
                            return HardwareProfile(
                                vendor="amd",
                                device_name="AMD Radeon / Instinct Graphics",
                                total_vram_mb=total_mb,
                                used_vram_mb=used_mb,
                                free_vram_mb=max(0, total_mb - used_mb),
                                utilization_pct=util_pct,
                                temperature_c=temp_c,
                                power_watts=None,
                                telemetry_source="sysfs_amdgpu",
                            )
                    except Exception:
                        pass
        return None

    @staticmethod
    def detect_handheld_formfactor() -> bool:
        """Detect if running on a PC gaming handheld (Steam Deck, Ally, Legion Go)."""
        dmi_path = Path("/sys/class/dmi/id/product_name")
        if dmi_path.exists():
            try:
                prod = dmi_path.read_text().lower()
                if any(k in prod for k in ("jupiter", "galileo", "rog ally", "legion go", "ayaneo", "onexplayer")):
                    return True
            except Exception:
                pass
        return False

    @classmethod
    def get_active_profile(cls, device_index: int = 0) -> HardwareProfile:
        """Probe all backends and return the primary active profile."""
        is_handheld = cls.detect_handheld_formfactor()

        # 1. Try NVIDIA
        nv = cls.detect_nvidia(device_index=device_index)
        if nv:
            nv.is_handheld = is_handheld
            return nv

        # 2. Try AMD
        amd = cls.detect_amd()
        if amd:
            amd.is_handheld = is_handheld
            return amd

        # 3. Fallback to CPU Mode (or APU Handheld)
        device_name = "Handheld APU (Shared System Memory)" if is_handheld else "CPU Mode (Zero Local VRAM)"
        return HardwareProfile(
            vendor="handheld_apu" if is_handheld else "cpu_fallback",
            device_name=device_name,
            total_vram_mb=0 if not is_handheld else 16384,
            used_vram_mb=0,
            free_vram_mb=0 if not is_handheld else 16384,
            utilization_pct=0.0,
            temperature_c=None,
            power_watts=None,
            telemetry_source="hardware_topology",
            is_handheld=is_handheld,
        )


class ConsoleCompanionManager:
    """Manages Companion Mode for PS5, Xbox Series X|S, and Nintendo Switch."""

    SUPPORTED_MODES = ["hdmi_capture", "ps_remote_play", "xbox_cloud_companion", "rtsp_stream"]

    def __init__(self, mode: str = "hdmi_capture", capture_device_id: int = 0):
        self.mode = mode if mode in self.SUPPORTED_MODES else "hdmi_capture"
        self.capture_device_id = capture_device_id
        self.active = False
        self.frames_analyzed = 0
        self.frames_skipped_by_d3 = 0

    def start_companion(self) -> Dict[str, Any]:
        """Start the companion capture listener."""
        self.active = True
        return {
            "status": "COMPANION_ACTIVE",
            "mode": self.mode,
            "target_console": "PlayStation 5 / Xbox Series X / Nintendo Switch",
            "capture_device": f"/dev/video{self.capture_device_id}" if os.name != "nt" else f"Video Device {self.capture_device_id}",
            "d3_frame_skip_gate": "CPU Stride-Sampled MSE Gate Active",
            "vram_overhead_on_console": "0 MB (Runs on host Companion PC)",
        }

    def process_incoming_frame_delta(self, mse_delta: float, threshold: float = 12.0) -> Dict[str, Any]:
        """Process an incoming console video frame through the d3 skip shield."""
        delta_val = float(mse_delta)
        thresh_val = float(threshold)
        if not math.isfinite(delta_val) or delta_val < 0.0:
            delta_val = 0.0
        if not math.isfinite(thresh_val) or thresh_val < 0.0:
            thresh_val = 12.0
        self.frames_analyzed += 1
        is_changed = delta_val >= thresh_val
        if not is_changed:
            self.frames_skipped_by_d3 += 1
        return {
            "console_frame_id": self.frames_analyzed,
            "mse_delta": round(delta_val, 4),
            "significant_change": is_changed,
            "action": "TRIGGER_CLOUD_VLM" if is_changed else "SKIP_ZERO_COST",
            "skipped_ratio": round(self.frames_skipped_by_d3 / max(1, self.frames_analyzed), 3),
        }


@dataclass(frozen=True)
class SiliconSpec:
    family: str
    vendor: str
    category: str          # "console", "pc_laptop", "mobile_arm", "server_arm", "server_x86", "server_power"
    isa: str               # "x86_64", "arm64", "ppc64le"
    unified_memory: bool
    recommended_route: str
    local_frank_supported: bool = True


SILICON_CATALOG: Dict[str, SiliconSpec] = {
    "ps5": SiliconSpec("PlayStation 5 (AMD Zen 2 / RDNA 2 APU)", "AMD", "console", "x86_64", True, "console_companion_cloud"),
    "xbox_series": SiliconSpec("Xbox Series X|S (AMD Zen 2 / RDNA 2 APU)", "AMD", "console", "x86_64", True, "console_companion_cloud"),
    "switch": SiliconSpec("Nintendo Switch (NVIDIA Tegra)", "NVIDIA", "console", "arm64", True, "console_companion_cloud"),
    "amd_ryzen": SiliconSpec("AMD Ryzen / EPYC", "AMD", "pc_laptop", "x86_64", False, "lemonade_or_tokenlab"),
    "intel_core": SiliconSpec("Intel Core / Core Ultra / Xeon", "Intel", "pc_laptop", "x86_64", False, "ollama_or_cloud_cascade"),
    "apple_m": SiliconSpec("Apple Silicon M-Series", "Apple", "pc_laptop", "arm64", True, "ollama_metal_or_cloud"),
    "apple_a": SiliconSpec("Apple A-Series Mobile", "Apple", "mobile_arm", "arm64", True, "frank_edge_plus_cloud"),
    "snapdragon_x": SiliconSpec("Qualcomm Snapdragon X (Windows-on-ARM)", "Qualcomm", "pc_laptop", "arm64", True, "frank_npu_or_cloud"),
    "snapdragon_mobile": SiliconSpec("Qualcomm Snapdragon Mobile", "Qualcomm", "mobile_arm", "arm64", True, "frank_edge_plus_cloud"),
    "huawei_kirin": SiliconSpec("Huawei HiSilicon Kirin", "Huawei", "mobile_arm", "arm64", True, "frank_edge_plus_cloud"),
    "huawei_kunpeng": SiliconSpec("Huawei HiSilicon Kunpeng", "Huawei", "server_arm", "arm64", False, "frank_cpu_plus_cloud"),
    "mediatek_dimensity": SiliconSpec("MediaTek Dimensity / Helio", "MediaTek", "mobile_arm", "arm64", True, "frank_edge_plus_cloud"),
    "samsung_exynos": SiliconSpec("Samsung Exynos", "Samsung", "mobile_arm", "arm64", True, "frank_edge_plus_cloud"),
    "google_tensor": SiliconSpec("Google Tensor", "Google", "mobile_arm", "arm64", True, "frank_edge_plus_cloud"),
    "unisoc": SiliconSpec("UNISOC Mobile / IoT", "UNISOC", "mobile_arm", "arm64", True, "cloud_offload_strict"),
    "nvidia_grace": SiliconSpec("NVIDIA Grace ARM CPU", "NVIDIA", "server_arm", "arm64", True, "vllm_or_nim_local"),
    "ampere_arm": SiliconSpec("Ampere Computing ARM Server", "Ampere", "server_arm", "arm64", False, "frank_cpu_plus_cloud"),
    "ibm_power": SiliconSpec("IBM POWER Enterprise", "IBM", "server_power", "ppc64le", False, "frank_cpu_plus_cloud"),
}


def classify_silicon(chip_string: str) -> SiliconSpec:
    """Classify a CPU/SoC/Console identifier string into a MemoryOS routing policy."""
    s = (chip_string or "").strip().lower()
    rules = [
        (("ps5", "playstation 5", "oberon"), "ps5"),
        (("xbox", "series x", "series s", "scarlett"), "xbox_series"),
        (("switch", "tegra"), "switch"),
        (("snapdragon x", "x elite", "x plus", "oryon"), "snapdragon_x"),
        (("snapdragon", "qualcomm", "sm8", "adreno"), "snapdragon_mobile"),
        (("apple m1", "apple m2", "apple m3", "apple m4", "m1 ", "m2 ", "m3 ", "m4 ", "m-series"), "apple_m"),
        (("apple a", "a17", "a18", "a19", "iphone", "bionic"), "apple_a"),
        (("kirin",), "huawei_kirin"),
        (("kunpeng",), "huawei_kunpeng"),
        (("dimensity", "helio", "mediatek"), "mediatek_dimensity"),
        (("exynos",), "samsung_exynos"),
        (("tensor", "pixel"), "google_tensor"),
        (("unisoc", "tiger t"), "unisoc"),
        (("grace", "gb10", "gb200"), "nvidia_grace"),
        (("ampere", "altra"), "ampere_arm"),
        (("power9", "power10", "power11", "ibm power", "ppc64"), "ibm_power"),
        (("intel", "core ultra", "xeon", "i5-", "i7-", "i9-"), "intel_core"),
        (("ryzen", "epyc", "amd", "threadripper"), "amd_ryzen"),
    ]
    for tokens, key in rules:
        if any(tok in s for tok in tokens):
            return SILICON_CATALOG[key]
    return SiliconSpec(
        family=chip_string.strip() or "Generic Host CPU",
        vendor="Generic",
        category="pc_laptop",
        isa=platform.machine().lower() or "x86_64",
        unified_memory=False,
        recommended_route="frank_cpu_plus_cloud",
    )

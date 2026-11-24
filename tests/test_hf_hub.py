"""Unit and live HTTP tests for Hugging Face Open-Weight Hub & 8GB Hardware-Fit integration."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.memoryos import hf_hub
from src.memoryos.cloud_video import (
    VideoBudgetExceededError,
    analyze_video_frames_cloud,
    generate_video_cloud,
    sanitize_video_error,
)
from tests.test_jupiter_studio import LiveStudioServerMixin

_TINY_PNG_URI = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+X2ZkAAAAASUVORK5CYII="
)


class _FakeResp:
    def __init__(self, body: bytes, status: int = 200, content_type: str = "application/json") -> None:
        self._body = body
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self._body


class TestHuggingFaceHubCore(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        hf_hub._SEARCH_CACHE.clear()
        hf_hub._WHOAMI_CACHE.clear()

    def test_8gb_hardware_fit_tiers_and_repo_validation(self) -> None:
        fit_4b = hf_hub.estimate_8gb_hardware_fit(
            "unsloth/Qwen3.5-4B-GGUF",
            params_total=4_000_000_000,
            tags=["gguf"],
            pipeline_tag="text-generation",
        )
        self.assertEqual(fit_4b["tier"], "fits_8gb_local")
        self.assertTrue(fit_4b["fits_8gb_vram"])
        self.assertTrue(fit_4b["zero_cost_local_ready"])
        self.assertLessEqual(fit_4b["est_q4_vram_gb"], 4.0)

        fit_27b = hf_hub.estimate_8gb_hardware_fit(
            "Qwen/Qwen3.8-27B",
            params_total=27_781_427_952,
            tags=["safetensors"],
            pipeline_tag="image-text-to-text",
        )
        self.assertEqual(fit_27b["tier"], "cloud_offload_only")
        self.assertFalse(fit_27b["fits_8gb_vram"])

        fit_vid = hf_hub.estimate_8gb_hardware_fit(
            "Wan-AI/Wan2.2-T2V-A14B",
            params_total=14_000_000_000,
            pipeline_tag="text-to-video",
        )
        self.assertEqual(fit_vid["tier"], "cloud_offload_only")

        self.assertEqual(
            hf_hub.validate_safe_hf_repo_id("hf.co/unsloth/gemma-4-E2B-it-GGUF:Q4_K_M"),
            "unsloth/gemma-4-E2B-it-GGUF:Q4_K_M",
        )
        for bad in ("../etc/passwd", "https://evil.com/org/repo", "org//repo", "justmodel"):
            with self.assertRaises(ValueError):
                hf_hub.validate_safe_hf_repo_id(bad)

    def test_local_hf_cache_scanner_and_token_redaction(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            hub_dir = Path(td) / "hub"
            gguf_repo = hub_dir / "models--unsloth--gemma-4-E2B-it-GGUF" / "snapshots" / "abc123"
            gguf_repo.mkdir(parents=True)
            (gguf_repo / "gemma-4-E2B-it-Q4_K_M.gguf").write_bytes(b"G" * (1024 * 64))

            tts_repo = hub_dir / "models--Qwen--Qwen3-TTS-12Hz-1.7B-VoiceDesign" / "snapshots" / "def456"
            tts_repo.mkdir(parents=True)
            (tts_repo / "model.safetensors").write_bytes(b"S" * (1024 * 32))

            found = hf_hub.scan_local_hf_cache([Path(td)])
            self.assertEqual(len(found), 2)
            by_id = {m["id"]: m for m in found}
            self.assertTrue(by_id["unsloth/gemma-4-E2B-it-GGUF"]["is_gguf"])
            self.assertEqual(
                by_id["unsloth/gemma-4-E2B-it-GGUF"]["ollama_target"],
                "ollama:hf.co/unsloth/gemma-4-E2B-it-GGUF",
            )
            self.assertEqual(by_id["unsloth/gemma-4-E2B-it-GGUF"]["cost_usd"], 0.0)
            self.assertIsNone(by_id["Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"]["ollama_target"])

        redacted = hf_hub.sanitize_hf_error("Auth failed for hf_AbCdEfGhIjKlMnOpQrSt123456 and Bearer secret_tok")
        self.assertNotIn("hf_AbCdEfGhIjKlMnOpQrSt123456", redacted)
        self.assertNotIn("secret_tok", redacted)

        vid_redacted = sanitize_video_error("HF error token hf_SuperSecretVideoToken987654")
        self.assertNotIn("hf_SuperSecretVideoToken987654", vid_redacted)

    def test_whoami_zero_card_safety_and_loopback_ollama_pull(self) -> None:
        def fake_whoami(req, timeout=6.0):
            self.assertIn("/whoami-v2", req.full_url)
            return _FakeResp(json.dumps({"type": "user", "isPro": False, "canPay": None}).encode("utf-8"))

        with patch.dict(
            os.environ,
            {"HF_TOKEN": "hf_UnitTestValidToken12345", "MEMORYOS_VIDEO_MAX_JOB_USD": "0"},
        ), patch("src.memoryos.hf_hub.urllib.request.urlopen", side_effect=fake_whoami):
            safety = hf_hub.get_hf_account_safety(live_check=True)
            self.assertTrue(safety["authenticated"])
            self.assertFalse(safety["can_pay"])
            self.assertTrue(safety["zero_spend_locked"])
            self.assertTrue(safety["guaranteed_zero_cost"])
            self.assertIn("$0.00", safety["billing_summary"])

        # SSRF guard: refuse non-loopback Ollama host
        with self.assertRaises(ValueError):
            hf_hub.pull_hf_gguf_to_ollama(
                "unsloth/Qwen3.5-4B-GGUF",
                ollama_host="http://192.168.1.99:11434",
            )

        captured = []

        def fake_pull(req, timeout=180.0):
            captured.append(req)
            return _FakeResp(json.dumps({"status": "success"}).encode("utf-8"))

        with patch("src.memoryos.hf_hub.urllib.request.urlopen", side_effect=fake_pull):
            res = hf_hub.pull_hf_gguf_to_ollama(
                "unsloth/Qwen3.5-4B-GGUF",
                ollama_host="http://127.0.0.1:11434",
            )
            self.assertTrue(res["ok"])
            self.assertEqual(res["cost_usd"], 0.0)
            self.assertEqual(res["studio_target"], "ollama:hf.co/unsloth/Qwen3.5-4B-GGUF")
            sent = json.loads(captured[0].data.decode("utf-8"))
            self.assertEqual(sent["model"], "hf.co/unsloth/Qwen3.5-4B-GGUF")
            self.assertFalse(sent["stream"])

    def test_hf_video_zero_lock_and_local_ollama_vision_analyzer(self) -> None:
        # 1. Zero-spend lock blocks HF open-weight cloud video before HTTP call
        with patch.dict(
            os.environ,
            {"HF_TOKEN": "hf_UnitTestVideoKey12345", "MEMORYOS_VIDEO_MAX_JOB_USD": "0"},
        ), patch(
            "src.memoryos.cloud_video.urllib.request.urlopen",
            side_effect=AssertionError("Zero-spend lock must block HF paid video before network call"),
        ):
            with self.assertRaises(VideoBudgetExceededError):
                generate_video_cloud(
                    prompt="Open-weight Wan test clip",
                    target="hf:Wan-AI/Wan2.2-TI2V-5B",
                    duration=5,
                    resolution="360p",
                )

        # 2. Local Ollama Hugging Face GGUF vision analyzes frames at $0.00
        def fake_local_vlm(req, timeout=45.0):
            self.assertEqual(req.full_url, "http://127.0.0.1:11434/v1/chat/completions")
            return _FakeResp(
                json.dumps({
                    "choices": [{
                        "message": {
                            "content": json.dumps({
                                "label": "Local GGUF Frame",
                                "summary": "Synthesizer patchbay indexed locally at $0.00.",
                                "tags": ["synth", "local"],
                                "mood": "focused",
                            })
                        }
                    }]
                }).encode("utf-8")
            )

        with patch.dict(os.environ, {"OLLAMA_HOST": "http://127.0.0.1:11434"}), patch(
            "src.memoryos.cloud_video.urllib.request.urlopen", side_effect=fake_local_vlm
        ):
            an = analyze_video_frames_cloud(
                frames=[{"timestamp_s": 0.0, "data_uri": _TINY_PNG_URI, "mse_delta": 200.0}],
                video_name="Studio_Take.mp4",
                target="ollama:hf.co/unsloth/gemma-4-E2B-it-GGUF",
                save_to_vault=False,
            )
            self.assertTrue(an["ok"])
            self.assertEqual(an["provider"], "Local Ollama ($0.00)")
            self.assertEqual(an["scenes"][0]["label"], "Local GGUF Frame")


class TestHuggingFaceStudioEndpoints(LiveStudioServerMixin, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        hf_hub._SEARCH_CACHE.clear()
        hf_hub._WHOAMI_CACHE.clear()

    def test_hf_http_routes_and_studio_html_stage(self) -> None:
        from apps.jupiter_studio_ui import STUDIO_HTML
        from src.memoryos import cloud_video

        self.assertIn('id="stage-btn-hf"', STUDIO_HTML)
        self.assertIn('id="hf-hub-stage"', STUDIO_HTML)
        self.assertIn('id="vid-gen-dest-pill"', STUDIO_HTML)
        self.assertNotIn(r"I:\video-outputs", STUDIO_HTML)
        self.assertIn("ollama:hf.co/unsloth/gemma-4-E2B-it-GGUF", STUDIO_HTML)
        for forbidden in ("<svg", "SURPRISE", "generateContent", "gemini-2.5", "gemini-2.0", "gemini-1.5"):
            self.assertNotIn(forbidden, STUDIO_HTML)

        # Stranger-test check: without I:/video-outputs directory, default output path is ./outputs/video
        with patch.dict(os.environ, {"MEMORYOS_VIDEO_OUTPUT_DIR": ""}), patch.object(
            cloud_video, "DEFAULT_VIDEO_OUTPUT_DIR_WIN", Path(REPO_ROOT / "__nonexistent_drive_dir__")
        ):
            self.assertEqual(cloud_video.get_video_output_dir(create=False), REPO_ROOT / "outputs" / "video")

        self.assertTrue((REPO_ROOT / "QUICKSTART.md").is_file())
        env_ex = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn('MEMORYOS_VIDEO_MAX_JOB_USD="0.00"', env_ex)
        self.assertIn('MEMORYOS_VIDEO_OUTPUT_DIR="./outputs/video"', env_ex)

        with tempfile.TemporaryDirectory() as td:
            cache_dir = Path(td) / "models--prism-ml--Bonsai-4B-gguf" / "snapshots" / "s1"
            cache_dir.mkdir(parents=True)
            (cache_dir / "bonsai-4b-q4.gguf").write_bytes(b"B" * 4096)

            fake_hub_payload = [
                {
                    "id": "prism-ml/Bonsai-4B-gguf",
                    "pipeline_tag": "text-generation",
                    "likes": 512,
                    "downloads": 64100,
                    "tags": ["gguf", "ternary"],
                    "gguf": {"total": 4_000_000_000},
                    "inferenceProviderMapping": [],
                },
                {
                    "id": "Wan-AI/Wan2.2-TI2V-5B",
                    "pipeline_tag": "text-to-video",
                    "likes": 1060,
                    "downloads": 20000,
                    "tags": ["diffusers", "text-to-video"],
                    "inferenceProviderMapping": [{"provider": "fal-ai", "status": "live"}],
                },
            ]

            def fake_hub_urlopen(req, timeout=10.0):
                url = req.full_url
                if "/api/models" in url:
                    return _FakeResp(json.dumps(fake_hub_payload).encode("utf-8"))
                if "/api/tags" in url:
                    return _FakeResp(json.dumps({"models": [{"name": "frank:latest"}]}).encode("utf-8"))
                if "/api/pull" in url:
                    return _FakeResp(json.dumps({"status": "success"}).encode("utf-8"))
                raise AssertionError(f"Unexpected URL in HF endpoint test: {url}")

            with patch.dict(
                os.environ,
                {
                    "MEMORYOS_HF_CACHE_DIR": td,
                    "MEMORYOS_VIDEO_MAX_JOB_USD": "0",
                    "OLLAMA_HOST": "http://127.0.0.1:11434",
                },
            ), patch("src.memoryos.hf_hub.urllib.request.urlopen", side_effect=fake_hub_urlopen):
                st, _, raw = self._raw_request("GET", "/api/hf/status?live=0")
                self.assertEqual(st, 200)
                st_doc = json.loads(raw)
                self.assertTrue(st_doc["safety"]["zero_spend_locked"])
                self.assertEqual(st_doc["local_cache"]["count"], 1)
                self.assertTrue(st_doc["ollama"]["live"])

                st, _, raw = self._raw_request("GET", "/api/hf/models?task=8gb-gguf&limit=6")
                self.assertEqual(st, 200)
                m_doc = json.loads(raw)
                self.assertEqual(m_doc["count"], 2)
                self.assertTrue(m_doc["models"][0]["cached_locally"])
                self.assertEqual(m_doc["models"][0]["hardware_fit"]["tier"], "fits_8gb_local")

                # Invalid repo_id -> HTTP 400
                st, _, _ = self._raw_request(
                    "POST",
                    "/api/hf/ollama-pull",
                    body=json.dumps({"repo_id": "../bad/repo"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(st, 400)

                # Valid GGUF pull -> HTTP 200 ($0.00)
                st, _, raw = self._raw_request(
                    "POST",
                    "/api/hf/ollama-pull",
                    body=json.dumps({"repo_id": "prism-ml/Bonsai-4B-gguf"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(st, 200)
                pull_doc = json.loads(raw)
                self.assertEqual(pull_doc["cost_usd"], 0.0)
                self.assertEqual(pull_doc["studio_target"], "ollama:hf.co/prism-ml/Bonsai-4B-gguf")


if __name__ == "__main__":
    unittest.main()

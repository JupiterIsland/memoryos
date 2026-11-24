"""Adversarial security, fuzzing, byte-range, fail-closed spend lock & concurrency tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
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

from src.memoryos import cloud_video, hf_hub
from tests.test_jupiter_studio import LiveStudioServerMixin

_TINY_PNG_URI = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+X2ZkAAAAASUVORK5CYII="
)


class _DummyResp:
    def __init__(self, body: bytes) -> None:
        self._body = body
        self.status = 200
        self.headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self._body


class TestAdversarialSecurityAndFailClosed(unittest.TestCase):
    def test_ssrf_url_matrix_and_loopback_ollama_confinement(self) -> None:
        unsafe_urls = [
            "",
            "http://fal.media/files/clip.mp4",
            "file:///C:/Windows/win.ini",
            "ftp://example.com/clip.mp4",
            "https://user:pass@fal.media/clip.mp4",
            "https://127.0.0.1/clip.mp4",
            "https://localhost/clip.mp4",
            "https://[::1]/clip.mp4",
            "https://[::ffff:127.0.0.1]/clip.mp4",
            "https://169.254.169.254/latest/meta-data/",
            "https://10.0.0.5/internal.mp4",
            "https://172.16.12.1/internal.mp4",
            "https://192.168.1.20/router.mp4",
            "https://printer.local/clip.mp4",
            "https://metadata.internal/clip.mp4",
            "https://bad host.example.com/clip.mp4",
            "https://fal.media/clip\x00.mp4",
        ]
        for u in unsafe_urls:
            self.assertFalse(cloud_video._is_safe_public_https_url(u), f"Expected unsafe URL to be blocked: {u!r}")

        self.assertTrue(cloud_video._is_safe_public_https_url("https://fal.media/files/safe_clip.mp4"))
        self.assertTrue(cloud_video._is_safe_public_https_url("https://replicate.delivery/pbxt/out.mp4"))

        for bad_ollama in (
            "http://0.0.0.0:11434",
            "http://192.168.1.10:11434",
            "https://attacker.example:11434",
            "ftp://127.0.0.1:11434",
        ):
            with self.assertRaises(ValueError):
                hf_hub._validate_loopback_ollama_url(bad_ollama)
            with patch.dict(os.environ, {"OLLAMA_HOST": bad_ollama}):
                with self.assertRaises(ValueError):
                    cloud_video.analyze_video_frames_cloud(
                        frames=[{"timestamp_s": 0.0, "data_uri": _TINY_PNG_URI, "mse_delta": 100.0}],
                        target="ollama:gemma4:26b",
                        save_to_vault=False,
                    )

    def test_windows_reserved_filenames_and_path_traversal_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            blocked_names = [
                "CON.mp4",
                "con.mp4",
                "NUL.mp4",
                "AUX.mp4",
                "PRN.mp4",
                "COM1.mp4",
                "LPT9.mp4",
                "NUL.extra.mp4",
                "../escape.mp4",
                "..\\escape.mp4",
                "nested/clip.mp4",
                "clip.mp4.exe",
                ".env",
                "null\x00byte.mp4",
            ]
            for name in blocked_names:
                self.assertIsNone(
                    cloud_video.resolve_safe_video_path(name, output_dir=out),
                    f"Expected filename {name!r} to be rejected",
                )
            ok = cloud_video.resolve_safe_video_path("omni_scene_01.mp4", output_dir=out)
            self.assertIsNotNone(ok)

    def test_zero_spend_cap_nan_inf_fuzzing_and_custom_hf_targets(self) -> None:
        with patch.dict(os.environ, {"MEMORYOS_VIDEO_MAX_JOB_USD": ""}):
            # Custom Hugging Face open-weight video model outside static catalog must estimate cleanly
            est_custom_hf = cloud_video.estimate_video_generation_cost(
                target="hf:meituan-longcat/LongCat-Video",
                duration=5,
                resolution="720p",
                max_budget_usd=0.0,
            )
            self.assertEqual(est_custom_hf["provider"], "hf")
            self.assertEqual(est_custom_hf["env_var"], "HF_TOKEN")
            self.assertEqual(est_custom_hf["max_budget_usd"], 0.0)
            self.assertFalse(est_custom_hf["within_budget"])

            for bad_num in ("NaN", "Infinity", "-Infinity", -0.01, -100):
                with self.assertRaises(ValueError):
                    cloud_video.estimate_video_generation_cost(max_budget_usd=bad_num)  # type: ignore[arg-type]
                with self.assertRaises(ValueError):
                    cloud_video.estimate_video_generation_cost(rate_override=bad_num)  # type: ignore[arg-type]

            for bad_dur in ("NaN", "Infinity", "0", "2", "16", "4.5", "abc"):
                with self.assertRaises(ValueError):
                    cloud_video.estimate_video_generation_cost(duration=bad_dur)

        # Mistyped or non-finite MEMORYOS_VIDEO_MAX_JOB_USD in .env MUST fail closed to $0.00!
        for corrupt_env in ("zero", "NaN", "Infinity", "-1.5", "$0.00"):
            with patch.dict(os.environ, {"MEMORYOS_VIDEO_MAX_JOB_USD": corrupt_env}):
                est = cloud_video.estimate_video_generation_cost(
                    target="gemini:gemini-omni-1.2-flash",
                    duration=5,
                    resolution="360p",
                    max_budget_usd=50.0,
                )
                self.assertEqual(
                    est["max_budget_usd"],
                    0.0,
                    f"Corrupt env cap {corrupt_env!r} did not fail closed to $0.00!",
                )
                self.assertFalse(est["within_budget"])

    def test_hf_cache_skips_empty_stubs_and_topbar_zindex_present(self) -> None:
        from apps.jupiter_studio_ui import STUDIO_HTML

        self.assertIn("z-index: 50;", STUDIO_HTML)

        with tempfile.TemporaryDirectory() as td:
            hub = Path(td) / "hub"
            # Empty metadata-only stub (< 1 KB, no weight files) must be ignored
            stub = hub / "models--org--metadata-only-stub" / "refs"
            stub.mkdir(parents=True)
            (stub / "main").write_bytes(b"deadbeef")

            # Real cached GGUF repo must be included once
            real_repo = hub / "models--unsloth--Qwen3.5-4B-GGUF" / "snapshots" / "rev1"
            real_repo.mkdir(parents=True)
            (real_repo / "model.gguf").write_bytes(b"W" * (1024 * 16))

            found = hf_hub.scan_local_hf_cache([Path(td)])
            self.assertEqual([m["id"] for m in found], ["unsloth/Qwen3.5-4B-GGUF"])


class TestAdversarialHTTPTortureAndConcurrency(LiveStudioServerMixin, unittest.TestCase):
    def test_cors_origin_blocking_malformed_json_and_byte_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vid_dir = Path(td) / "videos"
            vid_dir.mkdir(parents=True)
            sample_mp4 = vid_dir / "range_test.mp4"
            sample_mp4.write_bytes(b"ABCDEFGHIJKLMNOP")  # 16 bytes (indices 0..15)

            with patch.dict(
                os.environ,
                {
                    "MEMORYOS_VIDEO_OUTPUT_DIR": str(vid_dir),
                    "MEMORYOS_VIDEO_MAX_JOB_USD": "0",
                    "MEMORYOS_HF_CACHE_DIR": td,
                },
            ):
                # 1. Foreign Origin blocked (403) across every video & HF endpoint
                evil_hdr = {"Origin": "https://evil-site.example"}
                for get_ep in ("/api/hf/status?live=0", "/api/hf/models", "/api/video/status", "/api/video/ledger"):
                    st, _, _ = self._raw_request("GET", get_ep, headers=evil_hdr)
                    self.assertEqual(st, 403, f"Expected 403 for foreign Origin on GET {get_ep}")

                for post_ep in ("/api/hf/ollama-pull", "/api/video/analyze", "/api/video/generate"):
                    st, _, _ = self._raw_request(
                        "POST",
                        post_ep,
                        body=b"{}",
                        headers={"Origin": "https://evil-site.example", "Content-Type": "application/json"},
                    )
                    self.assertEqual(st, 403, f"Expected 403 for foreign Origin on POST {post_ep}")

                # 2. Malformed / non-object JSON bodies return 400 (never 500)
                for raw_body in (b"[]", b'"just-a-string"', b"12345", b"{truncated"):
                    for post_ep in ("/api/hf/ollama-pull", "/api/video/generate", "/api/video/analyze"):
                        st, _, _ = self._raw_request(
                            "POST",
                            post_ep,
                            body=raw_body,
                            headers={"Content-Type": "application/json"},
                        )
                        self.assertEqual(st, 400, f"Expected 400 for body {raw_body!r} on {post_ep}, got {st}")

                # 3. NaN/Inf query params on /api/video/estimate return 400 (never 500)
                for bad_qs in ("max_budget_usd=NaN", "max_budget_usd=Infinity", "max_budget_usd=-5", "duration=NaN"):
                    st, _, _ = self._raw_request("GET", f"/api/video/estimate?{bad_qs}")
                    self.assertEqual(st, 400, f"Expected 400 for {bad_qs}")

                # 4. Windows reserved filename over HTTP -> 400
                st, _, _ = self._raw_request("GET", "/api/video/outputs/NUL.mp4")
                self.assertEqual(st, 400)

                # 5. Byte-Range torture matrix on 16-byte MP4
                st, hdrs, body = self._raw_request(
                    "GET", "/api/video/outputs/range_test.mp4", headers={"Range": "bytes=0-0"}
                )
                self.assertEqual(st, 206)
                self.assertEqual(body, b"A")
                self.assertEqual(hdrs.get("content-range"), "bytes 0-0/16")

                st, hdrs, body = self._raw_request(
                    "GET", "/api/video/outputs/range_test.mp4", headers={"Range": "bytes=-4"}
                )
                self.assertEqual(st, 206)
                self.assertEqual(body, b"MNOP")
                self.assertEqual(hdrs.get("content-range"), "bytes 12-15/16")

                st, hdrs, body = self._raw_request(
                    "GET", "/api/video/outputs/range_test.mp4", headers={"Range": "bytes=12-9999"}
                )
                self.assertEqual(st, 206)
                self.assertEqual(body, b"MNOP")
                self.assertEqual(hdrs.get("content-range"), "bytes 12-15/16")

                for invalid_range in ("bytes=16-20", "bytes=10-4", "bytes=-", "bytes=-0", "items=0-4"):
                    st, _, _ = self._raw_request(
                        "GET", "/api/video/outputs/range_test.mp4", headers={"Range": invalid_range}
                    )
                    self.assertEqual(st, 416, f"Expected 416 for Range {invalid_range!r}, got {st}")

    def test_24_thread_concurrent_endpoint_stress(self) -> None:
        hf_hub._SEARCH_CACHE.clear()
        fake_models = [{"id": "unsloth/Qwen3.5-4B-GGUF", "pipeline_tag": "text-generation", "tags": ["gguf"]}]

        def fake_hub(req, timeout=10.0):
            if "/api/models" in req.full_url:
                return _DummyResp(json.dumps(fake_models).encode("utf-8"))
            return _DummyResp(json.dumps({"models": []}).encode("utf-8"))

        routes = [
            "/api/health",
            "/api/hf/status?live=0",
            "/api/hf/models?task=8gb-gguf&limit=4",
            "/api/video/estimate?target=hf:Wan-AI/Wan2.2-TI2V-5B&duration=5&resolution=360p",
            "/api/video/ledger?limit=5",
            "/api/frank/predict?q=reclaim+idle+vram+before+launching+game",
        ]

        with tempfile.TemporaryDirectory() as td, patch.dict(
            os.environ,
            {"MEMORYOS_HF_CACHE_DIR": td, "MEMORYOS_VIDEO_MAX_JOB_USD": "0"},
        ), patch("src.memoryos.hf_hub.urllib.request.urlopen", side_effect=fake_hub):
            def hit(idx: int) -> int:
                ep = routes[idx % len(routes)]
                status_code, _, raw = self._raw_request("GET", ep)
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise AssertionError(f"Non-dict response on {ep}")
                return status_code

            with ThreadPoolExecutor(max_workers=12) as pool:
                statuses = list(pool.map(hit, range(24)))

        self.assertEqual(statuses, [200] * 24)

    def test_openai_v1_failover_gateway_sync_and_stream(self) -> None:
        st, _, raw = self._raw_request("GET", "/v1/models")
        self.assertEqual(st, 200)
        models_doc = json.loads(raw)
        self.assertEqual(models_doc["object"], "list")
        self.assertTrue(any(m["id"] == "auto:d3" for m in models_doc["data"]))

        from apps.jupiter_studio import JupiterStudioHandler

        # Force cloud + Ollama failure -> must automatically cascade to built-in Frank-v1 ($0.00)
        with patch.object(
            JupiterStudioHandler, "_call_cloud_direct", return_value=("", "HTTP 429 quota exhausted")
        ), patch.object(
            JupiterStudioHandler, "_call_ollama_chat", return_value=("", "Ollama offline")
        ):
            st, _, raw = self._raw_request(
                "POST",
                "/v1/chat/completions",
                body=json.dumps({
                    "model": "auto:d3",
                    "messages": [{"role": "user", "content": "reclaim GPU VRAM before gaming"}],
                    "stream": False,
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(st, 200)
            comp = json.loads(raw)
            self.assertEqual(comp["object"], "chat.completion")
            self.assertIn("Frank-v1", comp["model"])
            self.assertTrue(len(comp["choices"][0]["message"]["content"]) > 0)

            # Streaming SSE mode
            st, hdrs, sse_raw = self._raw_request(
                "POST",
                "/v1/chat/completions",
                body=json.dumps({
                    "model": "studio:frank",
                    "messages": [{"role": "user", "content": "status check"}],
                    "stream": True,
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(st, 200)
            self.assertIn("text/event-stream", hdrs.get("content-type", ""))
            sse_text = sse_raw.decode("utf-8")
            self.assertIn("chat.completion.chunk", sse_text)
            self.assertIn("data: [DONE]", sse_text)


if __name__ == "__main__":
    unittest.main()

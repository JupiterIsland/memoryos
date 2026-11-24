"""Unit and HTTP integration tests for cloud-offloaded video workflows."""

from __future__ import annotations

import base64
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

from src.memoryos.cloud_video import (
    VideoBudgetExceededError,
    analyze_video_frames_cloud,
    estimate_video_generation_cost,
    gate_video_frames,
    generate_video_cloud,
    get_video_spend_ledger,
    list_generated_videos,
    resolve_safe_video_path,
    sanitize_video_error,
    search_video_scenes,
    validate_omni_video_params,
)
from src.memoryos.control_plane import ImmutableLedger
from src.memoryos.memory_keeper import MemoryVault
from tests.test_jupiter_studio import LiveStudioServerMixin

_TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+X2ZkAAAAASUVORK5CYII="
)
_TINY_PNG_URI = f"data:image/png;base64,{_TINY_PNG_B64}"


class _FakeHttpResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self._data


class TestCloudVideoAnalyzer(unittest.TestCase):
    def test_gate_video_frames_skips_static_and_caps_offload(self) -> None:
        frames = [
            {"timestamp_s": 0.0, "data_uri": _TINY_PNG_URI, "mse_delta": 255.0},
            {"timestamp_s": 2.0, "data_uri": _TINY_PNG_URI, "mse_delta": 1.2},
            {"timestamp_s": 4.0, "data_uri": _TINY_PNG_URI, "mse_delta": 0.4},
            {"timestamp_s": 6.0, "data_uri": _TINY_PNG_URI, "mse_delta": 48.0},
            {"timestamp_s": 8.0, "data_uri": _TINY_PNG_URI, "mse_delta": 62.0},
        ]
        gated = gate_video_frames(frames, mse_threshold=12.0, max_cloud_frames=2)
        self.assertEqual(gated["frames_total"], 5)
        self.assertEqual(gated["frames_offloaded"], 2)
        self.assertEqual(gated["frames_skipped"], 3)
        self.assertEqual(gated["frames_skipped_pct"], 60.0)
        self.assertEqual([f["timestamp_s"] for f in gated["selected"]], [0.0, 6.0])
        self.assertGreaterEqual(gated["gate_ms"], 0.0)

    def test_analyze_video_frames_offloads_to_tokenlab_and_saves_to_vault(self) -> None:
        captured_reqs = []

        def fake_urlopen(req, timeout=45.0):
            captured_reqs.append(req)
            idx = len(captured_reqs)
            body = json.dumps({
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "label": f"Archive Scene {idx}",
                            "summary": f"Rehearsal guitar close-up at cue {idx}.",
                            "tags": ["archive", "guitar"],
                            "mood": "warm",
                        })
                    }
                }]
            }).encode("utf-8")
            return _FakeHttpResponse(body)

        frames = [
            {"timestamp_s": 0.0, "data_uri": _TINY_PNG_URI, "mse_delta": 255.0},
            {"timestamp_s": 4.0, "data_uri": _TINY_PNG_URI, "mse_delta": 0.5},
            {"timestamp_s": 8.0, "data_uri": _TINY_PNG_URI, "mse_delta": 75.0},
        ]

        with tempfile.TemporaryDirectory() as td, patch.dict(
            os.environ,
            {
                "TOKENLAB_API_KEY": "tl-unit-test-token",
                "TOKENLAB_BASE_URL": "https://api.tokenlab.amd.com/v1",
            },
        ), patch("src.memoryos.cloud_video.urllib.request.urlopen", side_effect=fake_urlopen):
            vault = MemoryVault(
                db_path=Path(td) / "vault.sqlite",
                weights_path=Path(td) / "weights.json",
            )
            res = analyze_video_frames_cloud(
                frames=frames,
                video_name="Archive_VHS_Reel1.mp4",
                target="cloud:MiniCPM-V-4.7-35B-A3B",
                prompt_hint="Look for guitars",
                save_to_vault=True,
                vault=vault,
            )
            matched = search_video_scenes(vault, query="guitar")
            unmatched = search_video_scenes(vault, query="nonexistent_token_xyz")

        self.assertTrue(res["ok"])
        self.assertEqual(res["local_vram_mb"], 0)
        self.assertEqual(res["provider"], "AMD Token Lab")
        self.assertEqual(res["model"], "MiniCPM-V-4.7-35B-A3B")
        self.assertEqual(res["frames_total"], 3)
        self.assertEqual(res["frames_skipped"], 1)
        self.assertEqual(res["frames_offloaded"], 2)
        self.assertEqual(len(res["scenes"]), 2)
        self.assertTrue(res["saved_to_vault"])

        self.assertEqual(len(captured_reqs), 2)
        sent_payload = json.loads(captured_reqs[0].data.decode("utf-8"))
        self.assertEqual(sent_payload["model"], "MiniCPM-V-4.7-35B-A3B")
        user_blocks = sent_payload["messages"][0]["content"]
        self.assertEqual(user_blocks[1]["type"], "image_url")
        self.assertEqual(user_blocks[1]["image_url"]["url"], _TINY_PNG_URI)

        self.assertEqual(len(matched), 2)
        self.assertEqual(matched[0]["video_slug"], "archive_vhs_reel1")
        self.assertEqual(unmatched, [])


class TestCloudVideoGenerator(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        env_patch = patch.dict(os.environ, {"MEMORYOS_VIDEO_MAX_JOB_USD": ""})
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def test_validate_omni_video_params_and_constraints(self) -> None:
        with self.assertRaises(ValueError):
            validate_omni_video_params("")
        with self.assertRaises(ValueError):
            validate_omni_video_params("cat", last_frame_data_uri=_TINY_PNG_URI)
        with self.assertRaises(ValueError):
            validate_omni_video_params(
                "transition",
                duration=12,
                first_frame_data_uri=_TINY_PNG_URI,
                last_frame_data_uri=_TINY_PNG_URI,
            )
        with self.assertRaises(ValueError):
            validate_omni_video_params(
                "extend clip",
                duration=14,
                previous_interaction_id="v1_abc",
            )
        with self.assertRaises(ValueError):
            validate_omni_video_params("bad res", resolution="8k")
        with self.assertRaises(ValueError):
            validate_omni_video_params("bad ratio", aspect_ratio="4:3")
        with self.assertRaises(ValueError):
            validate_omni_video_params("too many refs", reference_images=[_TINY_PNG_URI] * 7)

        ok = validate_omni_video_params("Sunset ocean", aspect_ratio="9:16", resolution="1080p", duration="12s")
        self.assertEqual(ok["duration_s"], 12)
        self.assertEqual(ok["aspect_ratio"], "9:16")
        self.assertEqual(ok["resolution"], "1080p")

    def test_missing_gemini_key_blocks_before_http_and_sanitizer_redacts(self) -> None:
        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIza-your-gemini-key-here"}), patch(
            "src.memoryos.cloud_video.urllib.request.urlopen",
            side_effect=AssertionError("Placeholder key must fail before HTTP call"),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                generate_video_cloud("Neon rain street")
            self.assertIn("GEMINI_API_KEY", str(ctx.exception))

        cleaned = sanitize_video_error(
            "POST https://generativelanguage.googleapis.com/v1beta/interactions?key=AIzaSuperSecretKey1234567890ABCD "
            "failed Bearer tok_abc_123"
        )
        self.assertNotIn("AIzaSuperSecretKey1234567890ABCD", cleaned)
        self.assertNotIn("tok_abc_123", cleaned)

    def test_generate_video_cloud_uri_poll_and_download(self) -> None:
        captured_reqs = []
        poll_count = {"n": 0}
        fake_mp4 = b"\x00\x00\x00\x18ftypmp42fake_video_bytes"

        def fake_urlopen(req, timeout=30.0):
            captured_reqs.append(req)
            url = req.full_url
            if url.endswith("/interactions"):
                return _FakeHttpResponse(json.dumps({
                    "id": "v1_omni_test_001",
                    "output_video": {
                        "type": "video",
                        "mime_type": "video/mp4",
                        "uri": "https://generativelanguage.googleapis.com/v1beta/files/vid123abc",
                    },
                }).encode("utf-8"))
            if url.endswith("/files/vid123abc"):
                poll_count["n"] += 1
                state = "PROCESSING" if poll_count["n"] == 1 else "ACTIVE"
                return _FakeHttpResponse(json.dumps({"name": "files/vid123abc", "state": state}).encode("utf-8"))
            if url.endswith("/files/vid123abc:download?alt=media"):
                return _FakeHttpResponse(fake_mp4)
            raise AssertionError(f"Unexpected URL: {url}")

        secret_key = "AIzaRealUnitTestVideoKey999999"
        with tempfile.TemporaryDirectory() as td, patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": secret_key,
                "MEMORYOS_VIDEO_OUTPUT_DIR": td,
            },
        ), patch("src.memoryos.cloud_video.urllib.request.urlopen", side_effect=fake_urlopen):
            res = generate_video_cloud(
                prompt="Analog synth rack in dark studio",
                aspect_ratio="16:9",
                resolution="720p",
                duration=8,
                first_frame_data_uri=_TINY_PNG_URI,
                last_frame_data_uri=_TINY_PNG_URI,
                poll_interval_s=0.01,
            )
            saved_bytes = Path(res["path"]).read_bytes()
            listed = list_generated_videos(Path(td))

        self.assertTrue(res["ok"])
        self.assertEqual(res["local_vram_mb"], 0)
        self.assertEqual(res["interaction_id"], "v1_omni_test_001")
        self.assertEqual(saved_bytes, fake_mp4)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["filename"], res["filename"])

        for r in captured_reqs:
            self.assertNotIn(secret_key, r.full_url)
            self.assertEqual(r.get_header("X-goog-api-key"), secret_key)

        create_payload = json.loads(captured_reqs[0].data.decode("utf-8"))
        self.assertEqual(create_payload["model"], "gemini-omni-1.2-flash")
        self.assertEqual(
            create_payload["response_format"],
            {"type": "video", "delivery": "uri", "aspect_ratio": "16:9", "duration": "8s", "resolution": "720p"},
        )
        prompt_text = create_payload["input"][-1]["text"]
        self.assertIn("starting frame", prompt_text.lower())
        self.assertIn("final frame", prompt_text.lower())
        self.assertNotIn("<FIRST_FRAME>", prompt_text)
        self.assertNotIn("<LAST_FRAME>", prompt_text)

    def test_generate_video_cloud_inline_base64_delivery(self) -> None:
        fake_mp4 = b"\x00\x00\x00\x1cftypisom_inline_bytes"

        def fake_urlopen(req, timeout=30.0):
            return _FakeHttpResponse(json.dumps({
                "id": "v1_inline_99",
                "steps": [{
                    "type": "model_output",
                    "content": [{
                        "type": "video",
                        "mime_type": "video/mp4",
                        "data": base64.b64encode(fake_mp4).decode("ascii"),
                    }],
                }],
            }).encode("utf-8"))

        with tempfile.TemporaryDirectory() as td, patch.dict(
            os.environ, {"GEMINI_API_KEY": "AIzaRealUnitTestInlineKey888"}
        ), patch("src.memoryos.cloud_video.urllib.request.urlopen", side_effect=fake_urlopen):
            res = generate_video_cloud(
                prompt="Rain on window pane",
                duration=5,
                output_dir=Path(td),
            )
            self.assertEqual(Path(res["path"]).read_bytes(), fake_mp4)
            self.assertEqual(res["interaction_id"], "v1_inline_99")

    def test_resolve_safe_video_path_blocks_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            self.assertIsNone(resolve_safe_video_path("../secret.mp4", out_dir))
            self.assertIsNone(resolve_safe_video_path("foo.txt", out_dir))
            self.assertIsNone(resolve_safe_video_path("sub/a.mp4", out_dir))
            self.assertIsNone(resolve_safe_video_path("", out_dir))
            valid = resolve_safe_video_path("omni_valid_123.mp4", out_dir)
            self.assertIsNotNone(valid)
            self.assertEqual(valid.name, "omni_valid_123.mp4")

    def test_cost_estimator_hard_cap_and_secret_redaction(self) -> None:
        est_gem = estimate_video_generation_cost("gemini:gemini-omni-1.2-flash", duration=10, resolution="1080p")
        self.assertEqual(est_gem["rate_per_sec_usd"], 0.15)
        self.assertEqual(est_gem["estimated_cost_usd"], 1.50)

        est_fal = estimate_video_generation_cost(
            "fal:fal-ai/pika/v2.2/text-to-video",
            duration=5,
            resolution="360p",
            max_budget_usd=0.50,
        )
        self.assertEqual(est_fal["estimated_cost_usd"], 0.20)
        self.assertTrue(est_fal["within_budget"])

        est_rep = estimate_video_generation_cost(
            "replicate:luma/ray-2",
            duration=10,
            resolution="1080p",
            max_budget_usd=1.00,
        )
        self.assertEqual(est_rep["estimated_cost_usd"], 2.40)
        self.assertFalse(est_rep["within_budget"])

        # Hard cap must block before any HTTP request
        with patch.dict(os.environ, {"FAL_KEY": "fal_live_secret_12345"}), patch(
            "src.memoryos.cloud_video.urllib.request.urlopen",
            side_effect=AssertionError("Over-cap job must be blocked before network I/O"),
        ):
            with self.assertRaises(VideoBudgetExceededError) as ctx:
                generate_video_cloud(
                    prompt="Expensive 4k hero sequence",
                    target="gemini:gemini-omni-1.2-flash",
                    duration=15,
                    resolution="4k",
                    max_budget_usd=1.00,
                )
            self.assertGreater(ctx.exception.estimated_cost_usd, 1.00)

            with patch.dict(os.environ, {"MEMORYOS_VIDEO_MAX_JOB_USD": "0", "GEMINI_API_KEY": "AIzaLiveTestKey123456"}):
                est_zero = estimate_video_generation_cost("gemini:gemini-omni-1.2-flash", duration=5, resolution="360p", max_budget_usd=5.0)
                self.assertEqual(est_zero["max_budget_usd"], 0.0)
                self.assertFalse(est_zero["within_budget"])
                with self.assertRaises(VideoBudgetExceededError):
                    generate_video_cloud(
                        prompt="Zero-spend lock check",
                        target="gemini:gemini-omni-1.2-flash",
                        duration=5,
                        resolution="360p",
                        max_budget_usd=5.0,
                    )

        # Redact FAL_KEY (Key ...) and REPLICATE_API_TOKEN (r8_...)
        cleaned = sanitize_video_error(
            "Header Authorization: Key fal_top_secret_999 and token r8_replicate_secret_abc failed"
        )
        self.assertNotIn("fal_top_secret_999", cleaned)
        self.assertNotIn("r8_replicate_secret_abc", cleaned)

    def test_fal_adapter_queue_polling_and_ssrf_guard(self) -> None:
        captured_reqs = []
        poll_cnt = {"n": 0}
        fake_mp4 = b"\x00\x00\x00\x18ftypmp42fal_video"

        def fake_fal_urlopen(req, timeout=45.0):
            captured_reqs.append(req)
            url = req.full_url
            if url == "https://queue.fal.run/fal-ai/wan-25-preview/text-to-video":
                return _FakeHttpResponse(json.dumps({
                    "request_id": "req_fal_01",
                    "status_url": "https://queue.fal.run/fal-ai/wan-25-preview/text-to-video/requests/req_fal_01/status",
                    "response_url": "https://queue.fal.run/fal-ai/wan-25-preview/text-to-video/requests/req_fal_01",
                }).encode("utf-8"))
            if url.endswith("/requests/req_fal_01/status"):
                poll_cnt["n"] += 1
                st = "IN_PROGRESS" if poll_cnt["n"] == 1 else "COMPLETED"
                return _FakeHttpResponse(json.dumps({"status": st}).encode("utf-8"))
            if url.endswith("/requests/req_fal_01"):
                return _FakeHttpResponse(json.dumps({"video": {"url": "https://fal.media/files/out_demo.mp4"}}).encode("utf-8"))
            if url == "https://fal.media/files/out_demo.mp4":
                return _FakeHttpResponse(fake_mp4)
            raise AssertionError(f"Unexpected fal URL: {url}")

        with tempfile.TemporaryDirectory() as td, patch.dict(
            os.environ, {"FAL_KEY": "fal_test_key_abc123"}
        ), patch("src.memoryos.cloud_video.urllib.request.urlopen", side_effect=fake_fal_urlopen):
            res = generate_video_cloud(
                prompt="Fast Wan draft neon street",
                target="fal:fal-ai/wan-25-preview/text-to-video",
                duration=5,
                resolution="360p",
                output_dir=Path(td),
                poll_interval_s=0.01,
            )
            self.assertEqual(Path(res["path"]).read_bytes(), fake_mp4)
            self.assertEqual(res["provider"], "fal.ai Cloud")
            self.assertEqual(res["estimated_cost_usd"], 0.25)

        self.assertEqual(captured_reqs[0].get_header("Authorization"), "Key fal_test_key_abc123")
        # CDN asset download must NOT carry fal API key
        self.assertNotIn("Authorization", captured_reqs[-1].headers)

        # SSRF guard must reject private IP URLs returned by upstream
        for bad_url in ("http://127.0.0.1/evil.mp4", "https://192.168.1.10/evil.mp4"):
            def fake_ssrf_fal(req, timeout=45.0):
                url = req.full_url
                if url == "https://queue.fal.run/fal-ai/wan-25-preview/text-to-video":
                    return _FakeHttpResponse(json.dumps({
                        "status": "COMPLETED",
                        "video": {"url": bad_url},
                    }).encode("utf-8"))
                raise AssertionError("SSRF URL should never be requested")

            with patch.dict(os.environ, {"FAL_KEY": "fal_test_key_abc123"}), patch(
                "src.memoryos.cloud_video.urllib.request.urlopen", side_effect=fake_ssrf_fal
            ):
                with self.assertRaises(ValueError):
                    generate_video_cloud(
                        prompt="SSRF check",
                        target="fal:fal-ai/wan-25-preview/text-to-video",
                        duration=5,
                        resolution="360p",
                    )

    def test_replicate_adapter_and_immutable_spend_ledger(self) -> None:
        captured_reqs = []
        poll_cnt = {"n": 0}
        fake_mp4 = b"\x00\x00\x00\x18ftypisom_rep_video"

        def fake_rep_urlopen(req, timeout=45.0):
            captured_reqs.append(req)
            url = req.full_url
            if url == "https://api.replicate.com/v1/models/runwayml/gen4-turbo/predictions":
                return _FakeHttpResponse(json.dumps({
                    "id": "pred_rep_01",
                    "status": "starting",
                    "urls": {"get": "https://api.replicate.com/v1/predictions/pred_rep_01"},
                }).encode("utf-8"))
            if url == "https://api.replicate.com/v1/predictions/pred_rep_01":
                poll_cnt["n"] += 1
                if poll_cnt["n"] == 1:
                    return _FakeHttpResponse(json.dumps({"status": "processing"}).encode("utf-8"))
                return _FakeHttpResponse(json.dumps({
                    "status": "succeeded",
                    "output": ["https://replicate.delivery/pbxt/demo_clip.mp4"],
                }).encode("utf-8"))
            if url == "https://replicate.delivery/pbxt/demo_clip.mp4":
                return _FakeHttpResponse(fake_mp4)
            raise AssertionError(f"Unexpected Replicate URL: {url}")

        with tempfile.TemporaryDirectory() as td, patch.dict(
            os.environ, {"REPLICATE_API_TOKEN": "r8_unit_test_tok_999"}
        ), patch("src.memoryos.cloud_video.urllib.request.urlopen", side_effect=fake_rep_urlopen):
            db_file = Path(td) / "spend.sqlite"
            ledger = ImmutableLedger(db_file)
            vault = MemoryVault(db_path=db_file, weights_path=Path(td) / "weights.json")

            res = generate_video_cloud(
                prompt="Runway hero synth close-up",
                target="replicate:runwayml/gen4-turbo",
                duration=10,
                resolution="1080p",
                output_dir=Path(td),
                vault=vault,
                ledger=ledger,
                poll_interval_s=0.01,
            )
            self.assertEqual(Path(res["path"]).read_bytes(), fake_mp4)
            self.assertEqual(res["estimated_cost_usd"], 1.20)
            self.assertIsNotNone(res["ledger_event_id"])

            spend = get_video_spend_ledger(db_file)
            self.assertTrue(spend["ledger_valid"])
            self.assertEqual(spend["summary"]["total_generated_clips"], 1)
            self.assertEqual(spend["summary"]["total_generated_seconds"], 10)
            self.assertEqual(spend["summary"]["total_est_spend_usd"], 1.20)

        self.assertEqual(captured_reqs[0].get_header("Authorization"), "Bearer r8_unit_test_tok_999")
        self.assertEqual(captured_reqs[0].get_header("Prefer"), "wait=60")
        self.assertNotIn("Authorization", captured_reqs[-1].headers)


class TestCloudVideoHTTPEndpoints(LiveStudioServerMixin, unittest.TestCase):
    """End-to-end HTTP verification against a live loopback Jupiter Studio server."""

    def test_video_endpoints_and_ui_integrity(self) -> None:
        from apps.jupiter_studio_ui import STUDIO_HTML

        self.assertIn('id="stage-btn-video"', STUDIO_HTML)
        self.assertIn('id="cloud-video-stage"', STUDIO_HTML)
        for forbidden in ("<svg", "generateContent", "gemini-2.5", "gemini-2.0", "gemini-1.5"):
            self.assertNotIn(forbidden, STUDIO_HTML)

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            vault_db = td_path / "studio_video_http.sqlite"
            vid_dir = td_path / "video-outputs"
            vid_dir.mkdir(parents=True, exist_ok=True)

            with patch.dict(
                os.environ,
                {
                    "MEMORYOS_VIDEO_OUTPUT_DIR": str(vid_dir),
                    "MEMORYOS_VIDEO_MAX_JOB_USD": "",
                    "TOKENLAB_API_KEY": "tl-unit-http-key",
                    "GEMINI_API_KEY": "",
                    "HF_TOKEN": "",
                    "HUGGINGFACE_API_KEY": "",
                    "FAL_KEY": "",
                    "FAL_API_KEY": "",
                    "REPLICATE_API_TOKEN": "",
                    "REPLICATE_API_KEY": "",
                },
            ), patch("apps.jupiter_studio._get_studio_db_path", return_value=vault_db):
                # 1. GET /api/video/status
                st, _, raw = self._raw_request("GET", "/api/video/status")
                self.assertEqual(st, 200)
                status_doc = json.loads(raw)
                self.assertEqual(status_doc["local_vram_mb"], 0)
                self.assertTrue(status_doc["analyzer"]["ready"])
                self.assertFalse(status_doc["generator"]["ready"])

                # 2. POST /api/video/analyze (mocked upstream)
                def fake_vision(req, timeout=45.0):
                    return _FakeHttpResponse(json.dumps({
                        "choices": [{
                            "message": {
                                "content": json.dumps({
                                    "label": "Stage Lights",
                                    "summary": "Blue backlight silhouette on stage.",
                                    "tags": ["stage", "lights"],
                                    "mood": "dramatic",
                                })
                            }
                        }]
                    }).encode("utf-8"))

                with patch("src.memoryos.cloud_video.urllib.request.urlopen", side_effect=fake_vision):
                    st, _, raw = self._raw_request(
                        "POST",
                        "/api/video/analyze",
                        body=json.dumps({
                            "video_name": "Live_Cue.mp4",
                            "target": "cloud:MiniCPM-V-4.7-35B-A3B",
                            "save_to_vault": True,
                            "frames": [
                                {"timestamp_s": 0.0, "data_uri": _TINY_PNG_URI, "mse_delta": 255.0},
                                {"timestamp_s": 2.0, "data_uri": _TINY_PNG_URI, "mse_delta": 0.2},
                            ],
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                    )
                self.assertEqual(st, 200)
                an_res = json.loads(raw)
                self.assertEqual(an_res["frames_skipped"], 1)
                self.assertEqual(an_res["frames_offloaded"], 1)
                self.assertEqual(an_res["scenes"][0]["label"], "Stage Lights")

                # 3. GET /api/video/scenes
                st, _, raw = self._raw_request("GET", "/api/video/scenes?q=Stage")
                self.assertEqual(st, 200)
                scenes = json.loads(raw)["scenes"]
                self.assertEqual(len(scenes), 1)
                self.assertEqual(scenes[0]["label"], "Stage Lights")

                # 4. POST /api/video/generate with missing key -> 503 + setup_hint
                st, _, raw = self._raw_request(
                    "POST",
                    "/api/video/generate",
                    body=json.dumps({"prompt": "Cybernetic vinyl turntable", "duration": 5}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(st, 503)
                gen_err = json.loads(raw)
                self.assertTrue(gen_err["missing_key"])
                self.assertIn("setup_hint", gen_err)

                # 5. POST /api/video/generate mocked success -> 200 + Range streaming
                fake_mp4 = b"0123456789ABCDEF"

                def fake_omni(req, timeout=30.0):
                    return _FakeHttpResponse(json.dumps({
                        "id": "v1_http_ok",
                        "output_video": {
                            "type": "video",
                            "mime_type": "video/mp4",
                            "data": base64.b64encode(fake_mp4).decode("ascii"),
                        },
                    }).encode("utf-8"))

                with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaHttpMockKey999999"}), patch(
                    "src.memoryos.cloud_video.urllib.request.urlopen", side_effect=fake_omni
                ):
                    st, _, raw = self._raw_request(
                        "POST",
                        "/api/video/generate",
                        body=json.dumps({"prompt": "Neon turntable", "duration": 5}).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                    )
                self.assertEqual(st, 200)
                gen_ok = json.loads(raw)
                fname = gen_ok["filename"]

                # GET /api/video/outputs list
                st, _, raw = self._raw_request("GET", "/api/video/outputs")
                self.assertEqual(st, 200)
                self.assertEqual(len(json.loads(raw)["videos"]), 1)

                # Full stream -> 200
                st, hdrs, data = self._raw_request("GET", f"/api/video/outputs/{fname}")
                self.assertEqual(st, 200)
                self.assertEqual(hdrs.get("content-type"), "video/mp4")
                self.assertEqual(data, fake_mp4)

                # Byte range -> 206 Partial Content
                st, hdrs, data = self._raw_request(
                    "GET",
                    f"/api/video/outputs/{fname}",
                    headers={"Range": "bytes=0-3"},
                )
                self.assertEqual(st, 206)
                self.assertEqual(data, b"0123")
                self.assertEqual(hdrs.get("content-range"), f"bytes 0-3/{len(fake_mp4)}")

                # Traversal blocked -> 400
                st, _, _ = self._raw_request("GET", "/api/video/outputs/..%2Fsecret.mp4")
                self.assertEqual(st, 400)

                # 6. GET /api/video/estimate
                st, _, raw = self._raw_request(
                    "GET",
                    "/api/video/estimate?target=fal:fal-ai/wan-25-preview/text-to-video&duration=5&resolution=360p&max_budget_usd=0.50",
                )
                self.assertEqual(st, 200)
                est_doc = json.loads(raw)
                self.assertEqual(est_doc["estimated_cost_usd"], 0.25)
                self.assertTrue(est_doc["within_budget"])

                # 7. POST /api/video/generate over budget cap -> 400 + budget_exceeded
                st, _, raw = self._raw_request(
                    "POST",
                    "/api/video/generate",
                    body=json.dumps({
                        "target": "gemini:gemini-omni-1.2-flash",
                        "prompt": "Over-budget 4k scene",
                        "duration": 15,
                        "resolution": "4k",
                        "max_budget_usd": 1.00,
                    }).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(st, 400)
                cap_err = json.loads(raw)
                self.assertTrue(cap_err["budget_exceeded"])
                self.assertGreater(cap_err["estimated_cost_usd"], 1.00)

                # 8. Missing FAL_KEY / REPLICATE_API_TOKEN -> 503 with exact setup_hint
                with patch.dict(os.environ, {"FAL_KEY": "", "FAL_API_KEY": "", "REPLICATE_API_TOKEN": "", "REPLICATE_API_KEY": ""}):
                    st, _, raw = self._raw_request(
                        "POST",
                        "/api/video/generate",
                        body=json.dumps({
                            "target": "fal:fal-ai/wan-25-preview/text-to-video",
                            "prompt": "Draft clip",
                            "duration": 5,
                            "resolution": "360p",
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                    )
                    self.assertEqual(st, 503)
                    fal_err = json.loads(raw)
                    self.assertTrue(fal_err["missing_key"])
                    self.assertIn("FAL_KEY", fal_err["setup_hint"])

                    st, _, raw = self._raw_request(
                        "POST",
                        "/api/video/generate",
                        body=json.dumps({
                            "target": "replicate:runwayml/gen4-turbo",
                            "prompt": "Runway clip",
                            "duration": 5,
                            "resolution": "720p",
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                    )
                    self.assertEqual(st, 503)
                    rep_err = json.loads(raw)
                    self.assertTrue(rep_err["missing_key"])
                    self.assertIn("REPLICATE_API_TOKEN", rep_err["setup_hint"])

                # 9. GET /api/video/ledger shows recorded analyze + generate SHA-256 chain
                st, _, raw = self._raw_request("GET", "/api/video/ledger")
                self.assertEqual(st, 200)
                ledger_doc = json.loads(raw)
                self.assertTrue(ledger_doc["ledger_valid"])
                self.assertEqual(ledger_doc["summary"]["total_analyzed_clips"], 1)
                self.assertEqual(ledger_doc["summary"]["total_frames_skipped"], 1)
                self.assertEqual(ledger_doc["summary"]["total_generated_clips"], 1)
                self.assertGreater(ledger_doc["summary"]["total_est_spend_usd"], 0.0)


if __name__ == "__main__":
    unittest.main()

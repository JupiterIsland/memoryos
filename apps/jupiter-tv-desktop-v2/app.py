#!/usr/bin/env python3
"""Jupiter Desktop — AI Video Player & Visual AI Studio."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

from PyQt6.QtCore import QBuffer, QIODevice, Qt, QTimer, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.shared.ai import (
    SceneAnalyzer,
    SceneDetector,
    build_storyboard_sheet,
    export_interactive_visual_dashboard,
    render_hero_poster,
)
from apps.shared.ai.visual_fx import decode_image_bytes
from apps.shared.memory_store import MemoryStore
from src.memoryos.quiet_advisor_db import QUIET_ADVISOR_SQLITE_PATH

try:
    from apps.shared.stream_manager import StreamManager
except ImportError:
    class StreamManager:  # type: ignore[no-redef]
        """Lightweight fallback when optional stream_manager module is absent."""

        def resolve(self, source: str) -> str:
            return source

try:
    from apps.shared.utils import truncate
except ImportError:
    def truncate(text: str, length: int = 60) -> str:  # type: ignore[no-redef]
        return text if len(text) <= length else f"{text[: length - 3]}..."

import time

from quiet_advisor_client import (
    MemoryOSRouterClient,
    QuietAdvisorClient,
    compute_mse_delta,
    extract_cv2_frame,
)
from widgets import (
    AIVisualTimeline,
    FrameVisionPanel,
    HeroPosterPanel,
    StoryboardPanel,
    TelemetryVisualizerWidget,
)


def _format_clock(ms: int) -> str:
    sec = max(0, int(ms // 1000))
    mins, s = divmod(sec, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs}:{mins:02d}:{s:02d}" if hrs else f"{mins:02d}:{s:02d}"


class JupiterDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jupiter Desktop - AI Scene Navigator & Visual Studio")
        self.setGeometry(80, 60, 1340, 860)
        self.setStyleSheet(
            """
            QMainWindow { background: #0b0d14; }
            QLineEdit { background: #151926; color: #00ffff; border: 2px solid #ff1493; padding: 7px; border-radius: 4px; }
            QPushButton { background: #ff1493; color: #090b12; border: none; padding: 8px 10px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background: #00ffff; }
            QLabel { color: #d6e4ff; }
            QTextEdit { background: #0d1019; color: #00ff9d; border: 1px solid #ff1493; font-family: monospace; }
            QTabWidget::pane { border: 1px solid #ff1493; background: #0d1019; }
            QTabBar::tab { background: #141928; color: #9cb0d0; padding: 8px 14px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #ff1493; color: #090b12; font-weight: bold; }
            """
        )

        # Core state (wired to QuietAdvisorDB.sqlite + AMD Token Lab router_to_gemma)
        self.stream_manager = StreamManager()
        self.memory = MemoryStore()
        self.scene_detector = SceneDetector()
        self.advisor_db_path = QUIET_ADVISOR_SQLITE_PATH
        self.scene_analyzer = SceneAnalyzer(
            memory_store=self.memory,
            advisor_db_path=self.advisor_db_path,
        )
        self.current_url: str | None = None
        self.scene_markers = []
        self._last_video_frame_bytes: bytes = b""
        self._last_frame_capture_ts: float = 0.0
        self._prev_cv2_frame = None
        self._prev_inspected_frame_bytes: bytes = b""
        self._last_vision_result = None
        self._active_scene_index: int = -1
        self._frame_gate_in_flight: bool = False
        self.advisor_client = QuietAdvisorClient(
            router_url=os.getenv("MEMORYOS_ROUTER_URL", "http://127.0.0.1:5000"),
            session_id="jupiter-desktop-session",
            user_id="default",
        )
        self.router_client = self.advisor_client

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(360)
        self.player.setVideoOutput(self.video_widget)

        sink = self.video_widget.videoSink()
        if sink is not None:
            sink.videoFrameChanged.connect(self._on_video_frame)

        self.player.positionChanged.connect(self.update_slider_position)
        self.player.durationChanged.connect(self.update_slider_max)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)

        # Build split layout: Player & timeline left | AI Graphical Studio right
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        root_layout = QVBoxLayout(main_widget)

        header = QLabel("JUPITER DESKTOP // AI SCENE NAVIGATOR & GRAPHICAL STUDIO")
        header.setFont(QFont("Courier", 12, QFont.Weight.Bold))
        header.setStyleSheet("color: #00ffff;")
        root_layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter, stretch=1)

        # Left column: player + transport + AI timeline + log
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste URL or select local video file...")
        self.browse_btn = QPushButton("BROWSE")
        self.browse_btn.clicked.connect(self.browse_local_file)
        self.load_btn = QPushButton("LOAD")
        self.load_btn.clicked.connect(self.load_input)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.browse_btn)
        url_layout.addWidget(self.load_btn)
        left_layout.addLayout(url_layout)

        left_layout.addWidget(self.video_widget, stretch=1)

        # AI Visual Timeline (color bands + intensity waveform + cut ticks)
        self.slider = AIVisualTimeline()
        self.slider.setMaximum(100000)
        self.slider.sliderMoved.connect(self.on_slider_move)
        left_layout.addWidget(self.slider)

        transport_row = QHBoxLayout()
        self.play_btn = QPushButton("PLAY / PAUSE")
        self.play_btn.clicked.connect(self.toggle_play)
        self.time_label = QLabel("00:00 / 00:00")
        self.analyze_btn = QPushButton("DETECT SCENES + AI LABEL")
        self.analyze_btn.clicked.connect(self.detect_scenes)
        self.recap_btn = QPushButton("AI RECAP")
        self.recap_btn.clicked.connect(self.request_recap)
        transport_row.addWidget(self.play_btn)
        transport_row.addWidget(self.time_label)
        transport_row.addStretch()
        transport_row.addWidget(self.analyze_btn)
        transport_row.addWidget(self.recap_btn)
        left_layout.addLayout(transport_row)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search scenes semantically (e.g. 'car chase', 'guitar solo')...")
        self.search_btn = QPushButton("FIND SCENE")
        self.search_btn.clicked.connect(self.search_scenes)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        left_layout.addLayout(search_layout)

        self.status_label = QLabel("Ready")
        left_layout.addWidget(self.status_label)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(130)
        left_layout.addWidget(self.log_area)

        # Right column: 4-tab AI Graphical Studio
        self.studio_tabs = QTabWidget()
        self.storyboard_panel = StoryboardPanel()
        self.frame_vision_panel = FrameVisionPanel()
        self.hero_poster_panel = HeroPosterPanel()
        self.telemetry_panel = TelemetryVisualizerWidget()

        self.studio_tabs.addTab(self.storyboard_panel, "Storyboard")
        self.studio_tabs.addTab(self.frame_vision_panel, "Frame FX & Vision")
        self.studio_tabs.addTab(self.hero_poster_panel, "Hero Poster")
        self.studio_tabs.addTab(self.telemetry_panel, "AI Telemetry")

        self.storyboard_panel.scene_selected.connect(self._seek_ms)
        self.storyboard_panel.export_png_requested.connect(self.export_storyboard_png)
        self.storyboard_panel.export_html_requested.connect(self.export_html_studio)
        self.frame_vision_panel.capture_requested.connect(self.capture_current_frame)
        self.frame_vision_panel.vlm_scan_requested.connect(self.scan_captured_frame)
        self.hero_poster_panel.regenerate_requested.connect(self.render_poster_card)
        self.hero_poster_panel.save_requested.connect(self.save_poster_png)

        splitter.addWidget(left_panel)
        splitter.addWidget(self.studio_tabs)
        splitter.setSizes([720, 600])

        self.log("[*] Jupiter Desktop Visual AI Studio initialized")

    def _on_video_frame(self, video_frame) -> None:
        """Keep a fresh PNG snapshot of the latest rendered frame for pause and scene transitions."""
        try:
            if not video_frame.isValid():
                return
            now = time.monotonic()
            is_paused = self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState
            if not is_paused and (now - self._last_frame_capture_ts) < 0.25:
                return
            img = video_frame.toImage()
            if img.isNull():
                return
            buf = QBuffer()
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            img.save(buf, "PNG")
            self._last_video_frame_bytes = bytes(buf.data())
            self._last_frame_capture_ts = now
        except Exception:
            pass

    def on_playback_state_changed(self, state) -> None:
        """When the user pauses the video, extract the cv2 frame and run the CPU MSE delta check."""
        if state == QMediaPlayer.PlaybackState.PausedState and self.current_url:
            pos_ms = int(self.player.position())
            self.log(f"[*] Video paused at {_format_clock(pos_ms)} — extracting cv2 frame & checking CPU MSE delta...")
            self.evaluate_video_loop_frame(trigger="pause", pos_ms=pos_ms)

    def browse_local_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            "Videos (*.mp4 *.mkv *.avi *.mov *.webm);;All Files (*)",
        )
        if path:
            self.url_input.setText(path)
            self.load_input()

    def toggle_play(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def load_input(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            self.log("[-] Please enter a URL or file path")
            return

        self.current_url = url
        self.log(f"[*] Loading: {truncate(url)}...")
        self.status_label.setText(f"Loading: {truncate(url)}")
        try:
            qurl = QUrl.fromLocalFile(url) if not url.startswith(("http", "magnet")) else QUrl(url)
            self.player.setSource(qurl)
            self.player.play()
            self.log("[+] Now playing")
        except Exception as e:
            self.log(f"[-] Load error: {e}")

    def detect_scenes(self) -> None:
        if not self.current_url:
            self.log("[-] Load a video first")
            return

        self.log(f"[*] Detecting REAL scenes + palettes from: {truncate(self.current_url)}...")
        self.status_label.setText("Detecting scenes & extracting keyframes...")
        self.analyze_btn.setEnabled(False)

        threading.Thread(target=self._detect_async, daemon=True).start()

    def _detect_async(self) -> None:
        try:
            scenes = self.scene_analyzer.analyze(
                self.current_url,
                use_ai=True,
                progress_callback=lambda msg: QTimer.singleShot(0, lambda m=msg: self.status_label.setText(m)),
            )
            QTimer.singleShot(0, lambda: self._show_scenes(scenes))
        except Exception as e:
            QTimer.singleShot(0, lambda err=e: self.log(f"[-] Detection failed: {err}"))
        finally:
            QTimer.singleShot(0, lambda: self.analyze_btn.setEnabled(True))

    def _show_scenes(self, scenes) -> None:
        self.scene_markers = scenes
        self.log(f"[+] DETECTED {len(scenes)} SCENES:")
        for i, scene in enumerate(scenes):
            summary_txt = f" — {scene.summary}" if getattr(scene, "summary", "") else ""
            self.log(f"    {i+1}. {scene.label} ({scene.start_ms/1000:.1f}s-{scene.end_ms/1000:.1f}s){summary_txt}")

        self.slider.set_scenes(scenes)
        self.storyboard_panel.set_scenes(scenes)
        self.render_poster_card()
        self._sync_quiet_advisor()
        self.status_label.setText(f"Scenes: {len(scenes)} | Storyboard & Poster ready")

    def _sync_quiet_advisor(self) -> None:
        """Refresh Quiet Advisor telemetry after Jupiter TV inferences and surface d3 hints."""
        self.telemetry_panel.refresh_from_db()
        stats = getattr(self.scene_analyzer, "vlm_stats", {})
        if stats.get("frames_evaluated"):
            self.log(
                f"[TOKEN LAB VLM GATE] Evaluated={stats.get('frames_evaluated', 0)} | "
                f"Gemma-4-31B-IT={stats.get('gemma_routed', 0)} | "
                f"d3 Skipped={stats.get('d3_skipped', 0)} -> Logged to QuietAdvisorDB.sqlite"
            )
        hint = getattr(self.scene_analyzer, "last_advisor_hint", None)
        if not hint:
            return
        d3 = hint.get("d3_routing") or {}
        choice = str(d3.get("choice") or "surface_now")
        conf = float(d3.get("confidence") or 0.0)
        self.log(
            f"[QUIET ADVISOR · d3 {choice} {conf * 100:.0f}%] {hint.get('title')} -> {hint.get('recommended_action')}"
        )
        surfaced_ids = getattr(self, "_surfaced_card_ids", set())
        card_id = hint.get("id")
        if choice == "surface_now" and conf >= 0.70 and card_id not in surfaced_ids:
            surfaced_ids.add(card_id)
            self._surfaced_card_ids = surfaced_ids
            try:
                from quiet_advisor_ui import QuietAdvisorPopup

                self._advisor_popup = QuietAdvisorPopup(card=hint)
                self._advisor_popup.show()
            except Exception:
                pass

    def extract_current_cv2_frame(self, pos_ms: int | None = None) -> tuple[object, bytes]:
        """Extract current video frame as a cv2 BGR ndarray + PNG bytes via cv2 or QVideoSink."""
        target_pos = int(self.player.position() if pos_ms is None else pos_ms)
        frame_bgr, frame_bytes = extract_cv2_frame(
            video_source=self.current_url,
            position_ms=target_pos,
            fallback_frame_bytes=self._last_video_frame_bytes,
        )
        if not frame_bytes and self.current_url:
            sec = max(0.0, target_pos / 1000.0)
            data_url = self.scene_analyzer.extract_keyframe(self.current_url, sec)
            frame_bytes = decode_image_bytes(data_url)
            if frame_bytes and frame_bgr is None:
                frame_bgr, _ = extract_cv2_frame(None, target_pos, fallback_frame_bytes=frame_bytes)

        if not frame_bytes and self.scene_markers:
            first_b64 = next((s.thumbnail_b64 for s in self.scene_markers if s.thumbnail_b64), "")
            frame_bytes = decode_image_bytes(first_b64)
            if frame_bytes and frame_bgr is None:
                frame_bgr, _ = extract_cv2_frame(None, target_pos, fallback_frame_bytes=frame_bytes)

        return frame_bgr, frame_bytes

    def capture_current_frame(self) -> bytes:
        """Capture current video frame via cv2 / QVideoSink or keyframe extractor."""
        _, frame_bytes = self.extract_current_cv2_frame()
        if not frame_bytes:
            self.log("[-] Load a video or detect scenes before capturing a frame")
            return b""

        self.frame_vision_panel.set_frame_bytes(frame_bytes)
        self.studio_tabs.setCurrentWidget(self.frame_vision_panel)
        self.log("[+] Frame captured into Frame FX & Vision inspector")
        return frame_bytes

    def evaluate_video_loop_frame(
        self,
        trigger: str = "playback",
        pos_ms: int | None = None,
        switch_tab: bool = False,
    ) -> None:
        """
        Extract the current cv2 frame on pause or scene change, compute CPU MSE delta,
        call advisor_client.check_frame_delta(), and route to Token Lab if not skipped.
        """
        if self._frame_gate_in_flight:
            return

        target_pos = int(self.player.position() if pos_ms is None else pos_ms)
        frame_bgr, frame_bytes = self.extract_current_cv2_frame(pos_ms=target_pos)
        if not frame_bytes and frame_bgr is None:
            return

        if frame_bytes:
            self.frame_vision_panel.set_frame_bytes(frame_bytes)
            if switch_tab:
                self.studio_tabs.setCurrentWidget(self.frame_vision_panel)

        self._frame_gate_in_flight = True
        self.frame_vision_panel.scan_btn.setEnabled(False)
        self.status_label.setText(f"[{trigger}] Calculating CPU MSE delta -> querying MemoryOS d3 router...")
        media_name = Path(self.current_url).name if self.current_url else "Video stream"
        hint = f"{media_name} ({trigger} @ {_format_clock(target_pos)})"
        prev_input = (
            self._prev_cv2_frame
            if self._prev_cv2_frame is not None
            else (self._prev_inspected_frame_bytes or None)
        )
        curr_input = frame_bgr if frame_bgr is not None else frame_bytes

        def _worker():
            import json
            from apps.shared.ai.models import FrameVisionResult
            from apps.shared.ai.visual_fx import compute_frame_metrics

            delta = compute_mse_delta(curr_input, prev_input)
            try:
                gate = self.advisor_client.check_frame_delta(
                    mse=delta["mse"],
                    brightness_delta=delta["brightness_delta"],
                    contrast_delta=delta["contrast_delta"],
                    intensity_delta=delta["intensity_delta"],
                    palette_shift=delta["palette_shift"],
                    context_hint=hint,
                    session_id="jupiter-tv-vision",
                    frame_delta=delta,
                    mse_delta=delta["mse_delta"],
                    previous_response=(
                        json.dumps(self._last_vision_result.to_dict())
                        if self._last_vision_result is not None
                        else None
                    ),
                )
                if gate.get("skip_vision") and self._last_vision_result is not None:
                    prev_res = self._last_vision_result
                    res = FrameVisionResult(
                        caption=f"[d3 skip · {trigger} · MSE={delta['mse_delta']:.2f}] {prev_res.caption}",
                        objects=prev_res.objects,
                        mood=prev_res.mood,
                        lighting=prev_res.lighting,
                        palette=prev_res.palette,
                        tags=prev_res.tags,
                        model="d3-gatekeeper (skipped via /api/frame-delta)",
                        latency_ms=float(gate.get("gate_latency_ms") or 0.0),
                    )
                    QTimer.singleShot(
                        0,
                        lambda: self._finish_frame_scan(res, frame_bytes, frame_bgr=frame_bgr),
                    )
                    return

                routed = self.advisor_client.route_inference(
                    prompt=(
                        "Analyze this video frame as a visual cinema director.\n"
                        f"Context: {hint}\n"
                        'Return strict JSON with keys: "caption", "objects", "mood", "lighting", "tags".'
                    ),
                    task_type="vision_heavy",
                    session_id="jupiter-tv-vision",
                    image_bytes=frame_bytes,
                    frame_delta=delta,
                    mse_delta=delta["mse_delta"],
                    max_tokens=220,
                )
                metrics = compute_frame_metrics(frame_bytes)
                raw = str(routed.get("content") or "{}").strip()
                parsed = json.loads(raw[raw.find("{") : raw.rfind("}") + 1]) if "{" in raw and "}" in raw else {}
                res = FrameVisionResult(
                    caption=str(parsed.get("caption") or f"Routed via /api/route ({routed.get('model')})"),
                    objects=[str(o) for o in (parsed.get("objects") or ["keyframe-subject"])][:6],
                    mood=str(parsed.get("mood") or "cinematic"),
                    lighting=str(parsed.get("lighting") or "balanced"),
                    palette=metrics["palette"],
                    tags=[str(t) for t in (parsed.get("tags") or ["tokenlab-vlm"])][:6],
                    model=str(routed.get("model") or "Gemma-4-31B-IT"),
                    latency_ms=float(routed.get("latency_ms") or 0.0),
                )
            except Exception:
                res = self.scene_analyzer.inspect_frame(frame_bytes, context_hint=hint)
            QTimer.singleShot(
                0,
                lambda: self._finish_frame_scan(res, frame_bytes, frame_bgr=frame_bgr),
            )

        threading.Thread(target=_worker, daemon=True).start()

    def scan_captured_frame(self) -> None:
        """Calculate CPU MSE delta and call MemoryOS Router (/api/frame-delta -> /api/route)."""
        if not self.frame_vision_panel.current_raw_frame:
            self.capture_current_frame()
        self.evaluate_video_loop_frame(trigger="manual_scan", pos_ms=int(self.player.position()), switch_tab=True)

    def _finish_frame_scan(self, result, frame_bytes: bytes = b"", frame_bgr: object = None) -> None:
        self._frame_gate_in_flight = False
        self.frame_vision_panel.scan_btn.setEnabled(True)
        self.frame_vision_panel.show_vision_result(result)
        if frame_bytes:
            self._prev_inspected_frame_bytes = frame_bytes
        if frame_bgr is not None:
            self._prev_cv2_frame = frame_bgr
        self._last_vision_result = result
        self.status_label.setText(f"Vision scan complete ({result.model})")
        self.log(f"[AI VISION] {result.caption}")
        self._sync_quiet_advisor()

    def render_poster_card(self) -> None:
        title = Path(self.current_url).stem if self.current_url else "Jupiter Feature"
        png = render_hero_poster(
            title=title,
            scenes=self.scene_markers,
            hero_frame=self.frame_vision_panel.current_raw_frame or None,
        )
        self.hero_poster_panel.set_poster_bytes(png)

    def save_poster_png(self) -> None:
        if not self.hero_poster_panel.poster_bytes:
            self.render_poster_card()
        out_path = Path("memory") / "jupiter_hero_poster.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(self.hero_poster_panel.poster_bytes)
        self.log(f"[+] Saved Hero Poster PNG -> {out_path}")

    def export_storyboard_png(self) -> None:
        title = Path(self.current_url).stem if self.current_url else "Jupiter Feature"
        png_bytes = build_storyboard_sheet(self.scene_markers, title=title)
        out_path = Path("memory") / "jupiter_storyboard.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(png_bytes)
        self.log(f"[+] Exported AI Storyboard PNG -> {out_path}")

    def export_html_studio(self) -> None:
        title = Path(self.current_url).stem if self.current_url else "Jupiter TV Visual Studio"
        tele = self.telemetry_panel.get_snapshot()
        out = export_interactive_visual_dashboard(self.scene_markers, telemetry=tele, title=title)
        self.log(f"[+] Exported Interactive HTML5/SVG Studio -> {out}")

    def _seek_ms(self, pos_ms: int) -> None:
        self.player.setPosition(int(pos_ms))
        self.log(f"[*] Jumped to {_format_clock(pos_ms)} — checking cv2 frame MSE delta...")
        self.evaluate_video_loop_frame(trigger="scene_seek", pos_ms=int(pos_ms))

    def search_scenes(self) -> None:
        query = self.search_input.text().strip()
        if not query or not self.scene_markers:
            self.log("[-] Detect scenes and enter a search query first")
            return
        matches = self.scene_analyzer.search_scenes(self.scene_markers, query)
        if not matches:
            self.log(f"[-] No scene matched '{query}'")
            return
        best = matches[0]
        self._seek_ms(best.start_ms)
        self.log(f"[+] Best match: '{best.label}' ({best.start_ms / 1000:.1f}s)")

    def request_recap(self) -> None:
        if not self.scene_markers:
            self.log("[-] Detect scenes first before requesting a recap")
            return
        pos_ms = self.player.position() or None
        self.recap_btn.setEnabled(False)
        self.status_label.setText("Generating AI recap...")

        def _worker():
            summary = self.scene_analyzer.recap(self.scene_markers, up_to_ms=pos_ms)
            QTimer.singleShot(0, lambda: self._show_recap(summary))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_recap(self, summary: str) -> None:
        self.recap_btn.setEnabled(True)
        self.status_label.setText("AI recap ready")
        self.log(f"[AI RECAP] {summary}")
        self._sync_quiet_advisor()
        if self.scene_markers:
            title = Path(self.current_url).stem if self.current_url else "Jupiter Feature"
            self.hero_poster_panel.set_poster_bytes(
                render_hero_poster(title=title, scenes=self.scene_markers, subtitle=summary)
            )

    def on_slider_move(self, position: int) -> None:
        if self.player.duration() <= 0:
            return
        slider_max = max(1, self.slider.maximum())
        clicked_time = (position / slider_max) * self.player.duration()
        self.player.setPosition(int(clicked_time))

    def update_slider_position(self, pos: int) -> None:
        dur = self.player.duration()
        self.time_label.setText(f"{_format_clock(pos)} / {_format_clock(dur)}")
        if dur > 0:
            self.slider.blockSignals(True)
            self.slider.setValue(int((pos / dur) * self.slider.maximum()))
            self.slider.blockSignals(False)

        # Video playback loop: detect scene transitions and run cv2 MSE delta -> check_frame_delta()
        if self.scene_markers:
            matched_idx = -1
            matched_scene = None
            for idx, scene in enumerate(self.scene_markers):
                if int(scene.start_ms) <= pos < int(scene.end_ms):
                    matched_idx = idx
                    matched_scene = scene
                    break
            if matched_idx != -1 and matched_idx != self._active_scene_index:
                prev_idx = self._active_scene_index
                self._active_scene_index = matched_idx
                if prev_idx != -1 and matched_scene is not None:
                    self.log(
                        f"[*] Scene changed -> {matched_scene.label} ({_format_clock(pos)}) — "
                        "extracting cv2 frame & checking CPU MSE delta..."
                    )
                    self.evaluate_video_loop_frame(
                        trigger=f"scene_change:{matched_scene.label}",
                        pos_ms=int(pos),
                    )

    def update_slider_max(self, duration: int) -> None:
        self.slider.setMaximum(max(1, duration))

    def log(self, msg: str) -> None:
        self.log_area.append(msg)
        cursor = self.log_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_area.setTextCursor(cursor)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("JUPITER DESKTOP - AI VISUAL STUDIO")
    print("=" * 60 + "\n")
    app = QApplication(sys.argv)
    window = JupiterDesktop()
    window.show()
    sys.exit(app.exec())

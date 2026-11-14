"""Custom PyQt6 AI graphical widgets for Jupiter TV Desktop."""

from __future__ import annotations

from typing import Dict, List, Optional

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from apps.shared.ai.models import FrameVisionResult, Scene
from apps.shared.ai.visual_fx import (
    DEFAULT_NEON_PALETTE,
    SUPPORTED_FILTERS,
    apply_visual_filter,
    decode_image_bytes,
)


def _format_ts(ms: int) -> str:
    sec = max(0, int(ms // 1000))
    mins, s = divmod(sec, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs}:{mins:02d}:{s:02d}" if hrs else f"{mins:02d}:{s:02d}"


def _pixmap_from_data(raw_or_b64: str | bytes, width: int = 0, height: int = 0) -> Optional[QPixmap]:
    raw = decode_image_bytes(raw_or_b64) if isinstance(raw_or_b64, str) else raw_or_b64
    if not raw:
        return None
    pix = QPixmap()
    if not pix.loadFromData(raw):
        return None
    if width > 0 and height > 0:
        return pix.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    return pix


class AIVisualTimeline(QSlider):
    """Custom slider painting scene color ribbons, AI intensity curve, and cut ticks."""

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.scene_markers: List[Scene] = []
        self.setMinimumHeight(42)
        self.setMouseTracking(True)

    def set_scenes(self, scenes: List[Scene]) -> None:
        self.scene_markers = list(scenes)
        self.update()

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        if not self.scene_markers or self.maximum() <= 0 or self.width() <= 0:
            return
        ratio = max(0.0, min(1.0, event.position().x() / self.width()))
        target_ms = int(ratio * self.maximum())
        hovered = next(
            (s for s in self.scene_markers if s.start_ms <= target_ms <= s.end_ms),
            None,
        )
        if hovered:
            tip = f"{_format_ts(hovered.start_ms)} · {hovered.label}"
            if hovered.summary:
                tip += f"\n{hovered.summary}"
            QToolTip.showText(event.globalPosition().toPoint(), tip, self)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = max(1, self.width())
        h = max(1, self.height())
        max_val = max(1, self.maximum())

        # Dark background track
        painter.fillRect(0, 4, w, h - 8, QColor(14, 18, 28))

        if self.scene_markers:
            # 1. Scene palette blocks
            for sc in self.scene_markers:
                x0 = int((sc.start_ms / max_val) * w)
                x1 = max(x0 + 2, int((sc.end_ms / max_val) * w))
                col = QColor((sc.palette or DEFAULT_NEON_PALETTE)[0])
                col.setAlpha(48)
                painter.fillRect(x0, 6, x1 - x0, h - 12, col)

            # 2. Smooth AI intensity / visual energy waveform
            path = QPainterPath()
            path.moveTo(0, h - 8)
            for sc in self.scene_markers:
                xm = ((sc.start_ms + sc.end_ms) / 2.0 / max_val) * w
                y = (h - 10) - max(0.05, min(1.0, sc.intensity)) * (h - 18)
                path.lineTo(xm, y)
            path.lineTo(w, h - 8)
            path.closeSubpath()

            grad = QLinearGradient(0, 4, 0, h - 6)
            grad.setColorAt(0.0, QColor(0, 255, 255, 110))
            grad.setColorAt(1.0, QColor(255, 20, 147, 20))
            painter.fillPath(path, grad)

            # 3. Pink scene cut markers
            painter.setPen(QPen(QColor(255, 20, 147), 2))
            for sc in self.scene_markers:
                x = int((sc.start_ms / max_val) * w)
                painter.drawLine(x, 3, x, h - 3)

        # 4. Playhead progress bar + glowing cyan needle
        play_x = int((self.value() / max_val) * w)
        painter.fillRect(0, h - 5, play_x, 3, QColor(0, 255, 255))
        painter.setPen(QPen(QColor(0, 255, 255), 3))
        painter.drawLine(play_x, 2, play_x, h - 2)
        painter.end()


SceneSlider = AIVisualTimeline


class SceneCardWidget(QFrame):
    """Visual thumbnail + palette + AI summary card for a single scene."""

    clicked = pyqtSignal(int)

    def __init__(self, index: int, scene: Scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            """
            SceneCardWidget {
                background: #141928;
                border: 1px solid #ff1493;
                border-radius: 8px;
            }
            SceneCardWidget:hover {
                border: 2px solid #00ffff;
                background: #192136;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        thumb = QLabel()
        thumb.setFixedHeight(110)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet("background: #0b0e17; border-radius: 4px; color: #5b6d8f;")
        pix = _pixmap_from_data(scene.thumbnail_b64, 240, 110) if scene.thumbnail_b64 else None
        if pix:
            thumb.setPixmap(pix)
        else:
            thumb.setText(f"Scene #{index + 1}")
        layout.addWidget(thumb)

        # Palette swatch strip
        sw_row = QHBoxLayout()
        sw_row.setSpacing(3)
        for hx in (scene.palette or DEFAULT_NEON_PALETTE)[:5]:
            chip = QFrame()
            chip.setFixedHeight(6)
            chip.setStyleSheet(f"background: {hx}; border-radius: 2px; border: none;")
            sw_row.addWidget(chip)
        layout.addLayout(sw_row)

        ts_lbl = QLabel(f"#{index + 1} · {_format_ts(scene.start_ms)} - {_format_ts(scene.end_ms)}")
        ts_lbl.setStyleSheet("color: #00ffff; font-size: 11px; font-weight: bold;")
        layout.addWidget(ts_lbl)

        title_lbl = QLabel(scene.label or f"Scene {index + 1}")
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel((scene.summary or scene.transcript or "Click to seek")[:90])
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #9cb0d0; font-size: 11px;")
        layout.addWidget(desc_lbl)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.scene.start_ms)
        super().mousePressEvent(event)


class StoryboardPanel(QWidget):
    """Scrollable visual storyboard grid + export actions."""

    scene_selected = pyqtSignal(int)
    export_png_requested = pyqtSignal()
    export_html_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self.export_png_btn = QPushButton("EXPORT STORYBOARD PNG")
        self.export_png_btn.clicked.connect(self.export_png_requested.emit)
        self.export_html_btn = QPushButton("OPEN HTML AI STUDIO")
        self.export_html_btn.clicked.connect(self.export_html_requested.emit)
        btn_row.addWidget(self.export_png_btn)
        btn_row.addWidget(self.export_html_btn)
        root.addLayout(btn_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: #0d1019;")
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(10)
        self.scroll.setWidget(self.grid_host)
        root.addWidget(self.scroll)

        self.empty_label = QLabel("Run DETECT SCENES + AI LABEL to build visual scene cards.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid.addWidget(self.empty_label, 0, 0)

    def set_scenes(self, scenes: List[Scene]) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not scenes:
            lbl = QLabel("No scenes detected yet.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(lbl, 0, 0)
            return

        for idx, sc in enumerate(scenes):
            card = SceneCardWidget(idx, sc)
            card.clicked.connect(self.scene_selected.emit)
            self.grid.addWidget(card, idx // 2, idx % 2)


class FrameVisionPanel(QWidget):
    """Live frame capture, AI graphical filter switcher, HUD overlay & VLM inspector."""

    capture_requested = pyqtSignal()
    vlm_scan_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_raw_frame: bytes = b""
        self.current_filter: str = "crisp"
        self.hud_enabled: bool = True

        layout = QVBoxLayout(self)

        top_btns = QHBoxLayout()
        self.capture_btn = QPushButton("CAPTURE FRAME")
        self.capture_btn.clicked.connect(self.capture_requested.emit)
        self.scan_btn = QPushButton("AI VISION SCAN (GEMMA)")
        self.scan_btn.clicked.connect(self.vlm_scan_requested.emit)
        self.hud_btn = QPushButton("HUD: ON")
        self.hud_btn.clicked.connect(self._toggle_hud)
        top_btns.addWidget(self.capture_btn)
        top_btns.addWidget(self.scan_btn)
        top_btns.addWidget(self.hud_btn)
        layout.addLayout(top_btns)

        filter_row = QHBoxLayout()
        self.filter_buttons: Dict[str, QPushButton] = {}
        for mode in SUPPORTED_FILTERS:
            btn = QPushButton(mode.upper())
            btn.clicked.connect(lambda _=False, m=mode: self.set_filter(m))
            filter_row.addWidget(btn)
            self.filter_buttons[mode] = btn
        layout.addLayout(filter_row)

        self.preview_label = QLabel("Capture a paused or playing frame to preview AI graphics & VLM scan.")
        self.preview_label.setMinimumHeight(250)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: #0b0e17; border: 2px solid #00ffff; border-radius: 6px;")
        layout.addWidget(self.preview_label)

        self.analysis_box = QTextEdit()
        self.analysis_box.setReadOnly(True)
        self.analysis_box.setMaximumHeight(140)
        self.analysis_box.setPlaceholderText("VLM caption, detected objects, mood, lighting & color tags appear here...")
        layout.addWidget(self.analysis_box)

    def _toggle_hud(self) -> None:
        self.hud_enabled = not self.hud_enabled
        self.hud_btn.setText(f"HUD: {'ON' if self.hud_enabled else 'OFF'}")
        self._render_preview()

    def set_frame_bytes(self, raw_bytes: bytes) -> None:
        self.current_raw_frame = raw_bytes
        self._render_preview()

    def set_filter(self, mode: str) -> None:
        self.current_filter = mode
        self._render_preview()

    def show_vision_result(self, result: FrameVisionResult) -> None:
        txt = (
            f"Model: {result.model} ({result.latency_ms:.0f} ms)\n"
            f"Caption: {result.caption}\n"
            f"Mood: {result.mood} | Lighting: {result.lighting}\n"
            f"Objects: {', '.join(result.objects) or 'N/A'}\n"
            f"Tags: {', '.join(result.tags)}\n"
            f"Palette: {' '.join(result.palette)}"
        )
        self.analysis_box.setPlainText(txt)

    def _render_preview(self) -> None:
        if not self.current_raw_frame:
            return
        filtered = apply_visual_filter(self.current_raw_frame, mode=self.current_filter)
        pix = _pixmap_from_data(filtered, 480, 270)
        if not pix:
            return
        if self.hud_enabled:
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            w, h = pix.width(), pix.height()
            painter.setPen(QPen(QColor(0, 255, 255, 160), 1))
            # Rule-of-thirds + targeting bracket
            painter.drawLine(w // 3, 0, w // 3, h)
            painter.drawLine((2 * w) // 3, 0, (2 * w) // 3, h)
            painter.drawLine(0, h // 3, w, h // 3)
            painter.drawLine(0, (2 * h) // 3, w, (2 * h) // 3)
            painter.setPen(QPen(QColor(255, 20, 147), 2))
            painter.drawRect(8, 8, w - 16, h - 16)
            painter.fillRect(14, 14, 130, 20, QColor(10, 12, 18, 200))
            painter.setPen(QColor(0, 255, 255))
            painter.setFont(QFont("Courier", 9, QFont.Weight.Bold))
            painter.drawText(20, 28, f"FX: {self.current_filter.upper()}")
            painter.end()
        self.preview_label.setPixmap(pix)


class HeroPosterPanel(QWidget):
    """Displays generated Stremio-style AI Show Poster PNG."""

    save_requested = pyqtSignal()
    regenerate_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.poster_bytes: bytes = b""
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        regen_btn = QPushButton("RENDER AI POSTER")
        regen_btn.clicked.connect(self.regenerate_requested.emit)
        save_btn = QPushButton("SAVE POSTER PNG")
        save_btn.clicked.connect(self.save_requested.emit)
        row.addWidget(regen_btn)
        row.addWidget(save_btn)
        layout.addLayout(row)

        self.poster_label = QLabel("Click RENDER AI POSTER after loading/analyzing a video.")
        self.poster_label.setMinimumHeight(300)
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_label.setStyleSheet("background: #0b0e17; border: 2px solid #ff1493; border-radius: 6px;")
        layout.addWidget(self.poster_label)

    def set_poster_bytes(self, png_bytes: bytes) -> None:
        self.poster_bytes = png_bytes
        pix = _pixmap_from_data(png_bytes, 480, 300)
        if pix:
            self.poster_label.setPixmap(pix)


class TelemetryChartCanvas(QWidget):
    """QPainter canvas drawing Token Lab model latency bars & d3 confidence arc."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(210)
        self.latencies: Dict[str, float] = {
            "MiniCPM5-2B": 145.0,
            "DeepSeek-V4.1": 320.0,
            "Qwen3.8-27B": 480.0,
            "Gemma-4-31B": 690.0,
        }
        self.d3_confidence: float = 0.91

    def update_metrics(self, latencies: Dict[str, float], confidence: float) -> None:
        if latencies:
            self.latencies = latencies
        self.d3_confidence = max(0.0, min(1.0, float(confidence)))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(11, 14, 23))

        # Left side: d3 Confidence Radial Gauge
        gauge_rect_x, gauge_rect_y, gauge_sz = 20, 32, 120
        painter.setPen(QPen(QColor(35, 44, 68), 10))
        painter.drawArc(gauge_rect_x, gauge_rect_y, gauge_sz, gauge_sz, 0, 360 * 16)
        painter.setPen(QPen(QColor(0, 255, 255), 10))
        span = int(-360 * 16 * self.d3_confidence)
        painter.drawArc(gauge_rect_x, gauge_rect_y, gauge_sz, gauge_sz, 90 * 16, span)

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Courier", 12, QFont.Weight.Bold))
        painter.drawText(gauge_rect_x + 36, gauge_rect_y + 66, f"{int(self.d3_confidence * 100)}%")
        painter.setPen(QColor(255, 20, 147))
        painter.setFont(QFont("Courier", 9, QFont.Weight.Bold))
        painter.drawText(gauge_rect_x + 12, gauge_rect_y + gauge_sz + 24, "d3 ROUTER CONF")

        # Right side: Model Latency Bars
        bar_x = 175
        avail_w = max(80, w - bar_x - 85)
        max_ms = max(1.0, max(self.latencies.values()))
        painter.setFont(QFont("Courier", 9))

        for idx, (model_name, ms) in enumerate(list(self.latencies.items())[:5]):
            y = 26 + idx * 36
            painter.setPen(QColor(210, 224, 248))
            painter.drawText(bar_x, y, model_name[:16])

            fill_w = max(8, int((ms / max_ms) * avail_w))
            grad = QLinearGradient(bar_x, y + 6, bar_x + fill_w, y + 18)
            grad.setColorAt(0.0, QColor(0, 255, 255))
            grad.setColorAt(1.0, QColor(255, 20, 147))
            painter.fillRect(bar_x, y + 6, avail_w, 12, QColor(24, 30, 46))
            painter.fillRect(bar_x, y + 6, fill_w, 12, grad)

            painter.setPen(QColor(0, 255, 255))
            painter.drawText(bar_x + avail_w + 8, y + 16, f"{ms:.0f}ms")

        painter.end()


class QuietAdvisorCardFrame(QFrame):
    """Interactive Quiet Advisor insight card with Apply / Dismiss / Mute controls."""

    action_triggered = pyqtSignal(int, str)

    def __init__(self, card: Dict[str, object], parent=None):
        super().__init__(parent)
        card_id = int(card["id"])
        d3 = card.get("d3_routing") or {}
        conf = float(d3.get("confidence", 0.0)) * 100.0
        choice = str(d3.get("choice", "surface_now"))

        self.setStyleSheet(
            """
            QuietAdvisorCardFrame {
                background: #14192a;
                border: 1px solid #00ffff;
                border-radius: 8px;
            }
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        head = QLabel(
            f"[{str(card.get('detector_type', 'advisor')).upper()}]  d3: {choice} ({conf:.1f}%)"
        )
        head.setStyleSheet("color: #ff1493; font-size: 11px; font-weight: bold;")
        layout.addWidget(head)

        title = QLabel(str(card.get("title") or "Quiet Advisor Insight"))
        title.setWordWrap(True)
        title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel(str(card.get("subtitle") or card.get("description") or "")[:180])
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #9cb0d0; font-size: 11px;")
        layout.addWidget(desc)

        metrics = card.get("metrics") or []
        if metrics:
            kpi = QLabel("  |  ".join(str(m) for m in metrics[:3]))
            kpi.setWordWrap(True)
            kpi.setStyleSheet("color: #00ffff; font-size: 11px;")
            layout.addWidget(kpi)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Acknowledge & Apply")
        apply_btn.clicked.connect(lambda: self.action_triggered.emit(card_id, "action"))
        dismiss_btn = QPushButton("DISMISS")
        dismiss_btn.clicked.connect(lambda: self.action_triggered.emit(card_id, "dismiss"))
        mute_btn = QPushButton("MUTE TYPE")
        mute_btn.clicked.connect(lambda: self.action_triggered.emit(card_id, "archive"))
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(dismiss_btn)
        btn_row.addWidget(mute_btn)
        layout.addLayout(btn_row)

        # Smooth fade-in animation bound to self
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)
        self.fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self.fade_anim.setDuration(400)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_anim.start()


class TelemetryVisualizerWidget(QWidget):
    """Combines Token Lab chart canvas with interactive Quiet Advisor insight cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_cards: List[dict] = []
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("REFRESH")
        refresh_btn.clicked.connect(self.refresh_from_db)
        detect_btn = QPushButton("RUN DETECTION")
        detect_btn.clicked.connect(self.run_detection_now)
        btn_row.addWidget(refresh_btn)
        btn_row.addWidget(detect_btn)
        layout.addLayout(btn_row)

        self.canvas = TelemetryChartCanvas()
        layout.addWidget(self.canvas)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setStyleSheet("border: none; background: #0d1019;")
        self.cards_host = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setSpacing(8)
        self.cards_scroll.setWidget(self.cards_host)
        layout.addWidget(self.cards_scroll, stretch=1)

        self.refresh_from_db()

    def get_snapshot(self) -> Dict[str, object]:
        return {
            "model_latencies": dict(self.canvas.latencies),
            "d3_confidence": self.canvas.d3_confidence,
            "advisor_cards": self._last_cards,
        }

    def run_detection_now(self) -> None:
        try:
            from apps.quiet_advisor_ui.api import run_detection_cycle

            res = run_detection_cycle(lookback_hours=48, seed_if_empty=False)
            self._apply_state(res["state"])
        except Exception:
            self.refresh_from_db()

    def _on_card_action(self, card_id: int, action: str) -> None:
        if action in ("action", "acknowledge"):
            try:
                from router_client import MemoryOSRouterClient

                matched = next((c for c in self._last_cards if int(c.get("id") or -1) == int(card_id)), {})
                MemoryOSRouterClient().acknowledge_card(
                    card_type=str(matched.get("detector_type") or "vram_thrashing"),
                    card_id=card_id,
                    action="acknowledge",
                    user_id=str(matched.get("user_id") or "default"),
                )
                self._apply_state(MemoryOSRouterClient().get_state())
                return
            except Exception:
                pass
        try:
            from apps.quiet_advisor_ui.api import apply_card_action

            res = apply_card_action(card_id=card_id, action=action)
            self._apply_state(res["state"])
        except Exception:
            self.refresh_from_db()

    def _apply_state(self, state: Dict[str, object]) -> None:
        telemetry = state.get("telemetry") or {}
        model_stats = telemetry.get("model_stats") or []
        latencies = {str(m["model_id"]): float(m["avg_latency_ms"]) for m in model_stats}
        active_cards = list(state.get("active_cards") or [])
        self._last_cards = active_cards

        top_conf = 0.91
        if active_cards:
            top_conf = float((active_cards[0].get("d3_routing") or {}).get("confidence") or 0.91)
        self.canvas.update_metrics(latencies or self.canvas.latencies, top_conf)

        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if active_cards:
            for card in active_cards[:6]:
                frame = QuietAdvisorCardFrame(card)
                frame.action_triggered.connect(self._on_card_action)
                self.cards_layout.addWidget(frame)
            self.cards_layout.addStretch()
        else:
            empty = QLabel(
                "No active Quiet Advisor cards. Run detection or launch:\npython apps/quiet_advisor_ui/server.py"
            )
            empty.setWordWrap(True)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #8ea3c7; padding: 12px;")
            self.cards_layout.addWidget(empty)

    def refresh_from_db(self) -> None:
        try:
            from apps.quiet_advisor_ui.api import get_dashboard_state

            self._apply_state(get_dashboard_state())
        except Exception:
            self.canvas.update_metrics(self.canvas.latencies, self.canvas.d3_confidence)

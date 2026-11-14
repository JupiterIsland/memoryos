#!/usr/bin/env python3
"""Floating PyQt6 Quiet Advisor card alert with smooth opacity animations."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.quiet_advisor_ui.api import apply_card_action, get_dashboard_state, run_detection_cycle


class QuietAdvisorPopup(QWidget):
    """Frameless, always-on-top bottom-right card alert backed by QuietAdvisorDB."""

    def __init__(self, card: Optional[Dict[str, Any]] = None, db_path: Optional[Path] = None):
        super().__init__()
        self.db_path = db_path
        self.card = card or self._load_top_card()
        self._closing = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, True)
        self.setFixedWidth(410)

        self._build_ui()
        self.adjustSize()
        self.position_bottom_right()

        # Auto fade-out after 15 seconds
        QTimer.singleShot(15000, self.trigger_fade_out)

        # Start completely transparent and bind animation to self to prevent GC
        self.setWindowOpacity(0.0)
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(400)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_anim.start()

    def _load_top_card(self) -> Dict[str, Any]:
        state = get_dashboard_state(db_path=self.db_path)
        active = state.get("active_cards") or []
        if not active:
            run_detection_cycle(lookback_hours=48, seed_if_empty=False, db_path=self.db_path)
            state = get_dashboard_state(db_path=self.db_path)
            active = state.get("active_cards") or []

        if active:
            return active[0]
        return {
            "id": None,
            "user_id": "default",
            "detector_type": "quiet_advisor",
            "title": "MemoryOS Hybrid Telemetry Ready",
            "subtitle": "Zero local VRAM used · d3 router standing by",
            "description": "No active hardware/context alerts waiting. Run detections anytime from Quiet Advisor.",
            "metrics": [],
            "recommended_action": "acknowledge",
            "d3_routing": {"choice": "surface_now", "confidence": 0.90},
        }

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setStyleSheet(
            """
            QFrame {
                background-color: #0e1320;
                border: 2px solid #00ffff;
                border-radius: 10px;
            }
            QLabel {
                border: none;
                background: transparent;
                color: #eaf3ff;
            }
            QPushButton {
                background-color: #192238;
                color: #d6e4ff;
                border: 1px solid #2b385a;
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #00ffff;
                color: #00ffff;
            }
            QPushButton#applyBtn {
                background-color: #00ffff;
                color: #07090f;
                border-color: #00ffff;
            }
            QPushButton#muteBtn {
                border-color: #ff1493;
                color: #ff77bd;
            }
            """
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)

        d3 = self.card.get("d3_routing") or {}
        conf = float(d3.get("confidence") or 0.0) * 100.0
        choice = str(d3.get("choice") or "surface_now")
        detector = str(self.card.get("detector_type") or "advisor").upper()

        top_row = QHBoxLayout()
        badge = QLabel(f"{detector}  ·  d3: {choice} ({conf:.1f}%)")
        badge.setStyleSheet("color: #ff1493; font-size: 11px; font-weight: bold;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.trigger_fade_out)
        top_row.addWidget(badge)
        top_row.addStretch()
        top_row.addWidget(close_btn)
        layout.addLayout(top_row)

        title = QLabel(str(self.card.get("title") or "Quiet Advisor Insight"))
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        sub_txt = str(self.card.get("subtitle") or "")
        if sub_txt:
            sub = QLabel(sub_txt)
            sub.setWordWrap(True)
            sub.setStyleSheet("font-size: 12px; color: #00ffff;")
            layout.addWidget(sub)

        desc = QLabel(str(self.card.get("description") or "")[:240])
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 11px; color: #a7badb;")
        layout.addWidget(desc)

        metrics = self.card.get("metrics") or []
        if metrics:
            kpi = QLabel("  |  ".join(str(m) for m in metrics[:3]))
            kpi.setWordWrap(True)
            kpi.setStyleSheet("font-size: 11px; color: #00f59b; font-weight: bold;")
            layout.addWidget(kpi)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Acknowledge & Apply")
        apply_btn.setObjectName("applyBtn")
        apply_btn.clicked.connect(lambda: self._handle_card_action("action"))

        dismiss_btn = QPushButton("DISMISS")
        dismiss_btn.clicked.connect(lambda: self._handle_card_action("dismiss"))

        mute_btn = QPushButton("MUTE")
        mute_btn.setObjectName("muteBtn")
        mute_btn.clicked.connect(lambda: self._handle_card_action("archive"))

        btn_row.addWidget(apply_btn)
        btn_row.addWidget(dismiss_btn)
        btn_row.addWidget(mute_btn)
        layout.addLayout(btn_row)

        outer.addWidget(frame)

    def position_bottom_right(self, margin: int = 22) -> None:
        """Snap the popup cleanly above the desktop taskbar in the bottom-right corner."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.right() - self.width() - margin
        y = geo.bottom() - self.height() - margin
        self.move(max(geo.left(), x), max(geo.top(), y))

    def _handle_card_action(self, action: str) -> None:
        card_id = self.card.get("id")
        card_type = str(self.card.get("detector_type") or "vram_thrashing")
        user_id = self.card.get("user_id")
        if action in ("action", "acknowledge"):
            try:
                from apps.jupiter_tv_desktop_v2.router_client import MemoryOSRouterClient
            except ImportError:
                sys.path.insert(0, str(REPO_ROOT / "apps" / "jupiter-tv-desktop-v2"))
                from router_client import MemoryOSRouterClient  # type: ignore[import-not-found]
            try:
                MemoryOSRouterClient().acknowledge_card(
                    card_type=card_type,
                    card_id=int(card_id) if card_id is not None else None,
                    action="acknowledge",
                    user_id=user_id,
                )
                self.trigger_fade_out()
                return
            except Exception:
                pass

        if card_id is not None:
            try:
                apply_card_action(
                    card_id=int(card_id),
                    action=action,
                    user_id=user_id,
                    db_path=self.db_path,
                )
            except Exception:
                pass
        elif action in ("action", "acknowledge"):
            try:
                from src.memoryos.quiet_advisor_db import acknowledge_card_sync

                acknowledge_card_sync(
                    user_id=user_id,
                    card_type=card_type,
                    action="acknowledge",
                    db_path=self.db_path,
                )
            except Exception:
                pass
        self.trigger_fade_out()

    def trigger_fade_out(self) -> None:
        """Smoothly fade out over 400ms before closing."""
        if self._closing:
            return
        self._closing = True
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(400)
        self.fade_out_anim.setStartValue(self.windowOpacity())
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out_anim.finished.connect(self.close)
        self.fade_out_anim.start()


def main() -> None:
    app = QApplication(sys.argv)
    popup = QuietAdvisorPopup()
    popup.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

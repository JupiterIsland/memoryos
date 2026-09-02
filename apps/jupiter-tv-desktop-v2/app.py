#!/usr/bin/env python3
"""
Jupiter Desktop — Simplified using shared modules.
Clean separation: UI layer + shared business logic.
"""

import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

sys.path.insert(0, '../..')
from apps.shared.stream_manager import StreamManager
from apps.shared.memory_store import MemoryStore
from apps.shared.utils import parse_m3u, truncate


class JupiterDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎸 Jupiter Desktop")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("""
            QMainWindow { background: #0f0f0f; }
            QLineEdit { background: #1a1a1a; color: #00ffff; border: 2px solid #ff1493; padding: 8px; border-radius: 4px; }
            QPushButton { background: #ff1493; color: #000; border: none; padding: 10px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background: #00ffff; }
            QLabel { color: #00ffff; }
            QTextEdit { background: #0d0d0d; color: #00ff00; border: 2px solid #ff1493; font-family: monospace; }
            QListWidget { background: #1a1a1a; color: #00ffff; border: 2px solid #ff1493; }
        """)

        # State
        self.stream_manager = StreamManager()
        self.memory = MemoryStore()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(QAudioOutput())

        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # Header
        header = QLabel("🚀 JUPITER DESKTOP - Stream Player")
        header.setFont(QFont("Courier", 14, QFont.Weight.Bold))
        layout.addWidget(header)

        # URL Input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube, M3U, magnet, or direct URL...")
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Load Button
        self.load_btn = QPushButton("▶ LOAD")
        self.load_btn.clicked.connect(self.load_input)
        layout.addWidget(self.load_btn)

        # Channel List
        layout.addWidget(QLabel("Channels:"))
        self.channel_list = QListWidget()
        self.channel_list.itemClicked.connect(self.on_channel_selected)
        layout.addWidget(self.channel_list)

        # Status & Log
        layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("🟢 Ready")
        layout.addWidget(self.status_label)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(120)
        layout.addWidget(self.log_area)

        main_widget.setLayout(layout)
        self.log("✅ Jupiter Desktop initialized")

    def load_input(self):
        url = self.url_input.text().strip()
        if not url:
            self.log("❌ Please enter a URL")
            return

        self.log(f"🔄 Loading: {truncate(url)}...")
        self.status_label.setText("🔄 Loading...")
        thread = threading.Thread(target=self._load_async, args=(url,))
        thread.daemon = True
        thread.start()

    def _load_async(self, url):
        try:
            if url.endswith(".m3u") or "#EXTM3U" in url or "get.php" in url:
                channels = parse_m3u(url)
                QTimer.singleShot(0, lambda: self._display_channels(channels))
            else:
                playable = self.stream_manager.resolve(url)
                QTimer.singleShot(0, lambda: self._play(playable, truncate(url)))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.log(f"❌ Error: {str(e)}"))
            QTimer.singleShot(0, lambda: self.status_label.setText("❌ Error"))

    def _display_channels(self, channels):
        self.channel_list.clear()
        for ch in channels[:50]:
            item = QListWidgetItem(ch.name)
            item.setData(Qt.ItemDataRole.UserRole, ch.url)
            self.channel_list.addItem(item)
        self.log(f"✅ Loaded {len(channels)} channels")
        self.status_label.setText(f"📡 {len(channels)} channels")

    def on_channel_selected(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        name = item.text()
        self.log(f"🎬 Playing: {name}")
        thread = threading.Thread(target=lambda: self._resolve_and_play(url, name))
        thread.daemon = True
        thread.start()

    def _resolve_and_play(self, url, name):
        try:
            playable = self.stream_manager.resolve(url)
            QTimer.singleShot(0, lambda: self._play(playable, name))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.log(f"❌ Playback error: {e}"))

    def _play(self, url_or_path, title):
        try:
            self.player.setSource(QUrl(url_or_path))
            self.player.play()
            self.status_label.setText(f"▶ {truncate(title)}")
            self.log(f"✅ Playing: {title}")
        except Exception as e:
            self.log(f"❌ Playback failed: {e}")
            self.status_label.setText("❌ Playback error")

    def log(self, msg):
        self.log_area.append(msg)
        cursor = self.log_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_area.setTextCursor(cursor)


if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 JUPITER DESKTOP - LAUNCHING")
    print("="*50 + "\n")
    app = QApplication(sys.argv)
    window = JupiterDesktop()
    window.show()
    sys.exit(app.exec())

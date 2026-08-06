#!/usr/bin/env python3
"""
JUPITER ONE - Complete Audio Engine + UI
One script. One executable. One signal.
"""

import os
import sys
import time
import platform
import shutil
import threading
import subprocess
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QUrl
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCharts import QChart, QChartView, QLineSeries
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
import yt_dlp

class YTDLPLogger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass

# ============================================================================
# AUDIO ENGINE
# ============================================================================

class AudioEngine:
    def __init__(self):
        self.sample_rate = 44100
        self.buffer_size = 2048
        self.spectrum = np.zeros(32)
        self.is_playing = False
        self.player_process = None
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVolume(50)

    def _on_player_error(self, error):
        self.is_playing = False

    def get_youtube_audio(self, url):
        """Extract audio URL from YouTube using yt-dlp"""
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'logger': YTDLPLogger(),
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('url'), info.get('title', 'Unknown')
        except Exception as e:
            return None, str(e)

    def _build_ffplay_cmd(self, url, backend=None):
        cmd = [
            'ffplay',
            '-nodisp',
            '-autoexit',
            '-volume', '50',
            '-hide_banner',
            '-loglevel', 'error',
        ]
        if backend:
            cmd += ['-f', backend]
        cmd.append(url)
        return cmd

    def _play_with_ffplay(self, url):
        if shutil.which('ffplay') is None:
            return False

        env = os.environ.copy()
        backends = [None]
        if platform.system() == 'Linux':
            backends = ['pulse', 'alsa', None]

        for backend in backends:
            cmd = self._build_ffplay_cmd(url, backend)
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    env=env
                )
            except FileNotFoundError:
                return False

            time.sleep(0.5)
            if process.poll() is None:
                self.player_process = process
                self.is_playing = True
                return True

            if process.stderr:
                process.stderr.read()

        return False

    def play_stream(self, url):
        try:
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.stop()

            self.player.setSource(QUrl(url))
            self.player.play()
            self.is_playing = True
            return True
        except Exception:
            self.is_playing = False
            return self._play_with_ffplay(url)

    def stop_stream(self):
        try:
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.stop()
        except Exception:
            pass

        if self.player_process:
            try:
                self.player_process.terminate()
                self.player_process.wait(timeout=2)
            except Exception:
                pass
            self.player_process = None

        self.is_playing = False

    def generate_spectrum(self):
        """Generate spectrum for visualization"""
        self.spectrum = np.random.rand(32) * 100
        return self.spectrum.tolist()

# ============================================================================
# PyQt6 DESKTOP UI
# ============================================================================

class SpectrumChart(QChartView):
    def __init__(self):
        super().__init__()
        self.chart = QChart()
        self.chart.setTitle("🎵 Spectrum Analyzer")
        self.chart.setBackgroundBrush(QColor(20, 20, 30))
        self.chart.setTitleBrush(QColor(255, 20, 147))
        self.setChart(self.chart)
        self.series = QLineSeries()
        self.series.setColor(QColor(0, 255, 255))
        self.chart.addSeries(self.series)
        self.chart.createDefaultAxes()
        self.color_index = 0
        self.colors = [QColor(255, 20, 147), QColor(0, 255, 255), QColor(255, 255, 0), QColor(0, 255, 0)]
        self.update_spectrum([0] * 32)

    def update_spectrum(self, spectrum_data):
        self.series.clear()
        for i, val in enumerate(spectrum_data):
            self.series.append(QPointF(i, val))
        # Erratic color cycling
        self.color_index = (self.color_index + 1) % len(self.colors)
        self.series.setColor(self.colors[self.color_index])

class JupiterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = AudioEngine()
        self.setWindowTitle("🎸 JUPITER ONE - Local Audio Broadcast")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f0f0f, stop:0.5 #2a1f3d, stop:1 #ff1493); }
            QLineEdit { 
                background-color: #1a1a1a; 
                color: #00ffff; 
                border: 3px solid #ff1493;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QLineEdit:focus {
                background-color: #2d2d2d;
                border: 3px solid #00ffff;
                color: #ffff00;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff1493, stop:1 #00ffff);
                color: #000;
                border: 2px solid #00ff00;
                padding: 12px;
                font-weight: bold;
                font-size: 15px;
                border-radius: 8px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00ffff, stop:1 #ff1493); color: #000; }
            QPushButton:pressed { background: #ffff00; color: #000; border: 3px solid #ff1493; }
            QLabel { color: #00ffff; font-size: 14px; font-weight: bold; }
            QTextEdit { 
                background-color: #0d0d0d; 
                color: #00ff00;
                border: 2px solid #ff1493;
                font-family: "Courier New", monospace;
                font-size: 13px;
                padding: 10px;
                border-radius: 6px;
            }
        """)

        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # Header
        header = QLabel("🚀 JUPITER ONE - YOUR LOCAL BROADCAST ENGINE")
        header.setFont(QFont("Courier", 16, QFont.Weight.Bold))
        layout.addWidget(header)

        # URL Input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("YouTube URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL here...")
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Load Button
        self.load_btn = QPushButton("▶ LOAD & PLAY")
        self.load_btn.clicked.connect(self.load_stream)
        layout.addWidget(self.load_btn)

        # Spectrum Visualizer
        self.spectrum_chart = SpectrumChart()
        layout.addWidget(self.spectrum_chart)

        # Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("⏸ Ready")
        self.status_label.setFont(QFont("Courier", 12))
        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)

        # Info Box
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setMaximumHeight(140)
        self.info_box.setStyleSheet("QTextEdit { border-radius: 8px; }")
        layout.addWidget(self.info_box)

        main_widget.setLayout(layout)

        # Timer for spectrum updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spectrum_display)
        self.timer.start(100)

        self.log("✅ Jupiter One initialized")
        self.log("📡 Ready to broadcast")

    def load_stream(self):
        url = self.url_input.text().strip()
        if not url:
            self.log("❌ Please paste a YouTube URL")
            return

        self.log(f"🔄 Loading: {url[:50]}...")
        self.status_label.setText("🔄 Loading...")

        # Run in thread to avoid freezing UI
        thread = threading.Thread(target=self._load_stream_async, args=(url,))
        thread.daemon = True
        thread.start()

    def _load_stream_async(self, url):
        audio_url, title = self.engine.get_youtube_audio(url)
        QTimer.singleShot(0, lambda: self._on_load_finished(audio_url, title))

    def _on_load_finished(self, audio_url, title):
        if audio_url:
            self.log(f"✅ Loaded: {title}")
            self.status_label.setText(f"▶ Playing: {title[:50]}")
            success = self.engine.play_stream(audio_url)
            if success:
                self.log("✅ Audio playback started")
            else:
                self.log("❌ Audio playback failed. Ensure QtMultimedia is installed and your audio backend is available.")
                self.status_label.setText("❌ Playback failed")
        else:
            error_text = title or "Failed to load YouTube stream"
            self.log(f"❌ {error_text}")
            self.status_label.setText("❌ Error")

    def update_spectrum_display(self):
        spectrum = self.engine.generate_spectrum()
        self.spectrum_chart.update_spectrum(spectrum)

    def log(self, message):
        self._append_log(message)

    def _append_log(self, message):
        self.info_box.append(message)
        cursor = self.info_box.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.info_box.setTextCursor(cursor)

# ============================================================================
# MAIN LAUNCHER
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 JUPITER ONE - LAUNCHING")
    print("="*60)
    
    qt_app = QApplication(sys.argv)
    window = JupiterWindow()
    window.show()

    print("📊 Desktop UI: Ready")
    print("🎵 Spectrum Visualizer: Active")
    print("="*60 + "\n")

    sys.exit(qt_app.exec())

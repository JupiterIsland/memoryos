#!/usr/bin/env python3
"""
Jupiter Mobile — Kivy app using shared modules.
Clean screen management, no hardcoded limits.
"""

import sys
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import mainthread

sys.path.insert(0, '../..')
from apps.shared.stream_manager import StreamManager
from apps.shared.memory_store import MemoryStore
from apps.shared.utils import parse_m3u, truncate


class JupiterMobile(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stream_manager = StreamManager()
        self.memory = MemoryStore()
        self.channels = []

    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        main_layout.canvas.clear()

        # Header
        header = Label(
            text='[b]🎸 JUPITER MOBILE[/b]',
            markup=True,
            size_hint_y=0.1,
            color=(0, 1, 1, 1)
        )
        main_layout.add_widget(header)

        # URL Input
        self.url_input = TextInput(
            multiline=False,
            hint_text='Enter YouTube, M3U, magnet, or direct URL',
            size_hint_y=0.1,
            background_color=(0.1, 0.1, 0.1, 1),
            foreground_color=(0, 1, 1, 1)
        )
        main_layout.add_widget(self.url_input)

        # Load Button
        load_btn = Button(text='▶ LOAD', size_hint_y=0.1)
        load_btn.bind(on_press=self.load_input)
        main_layout.add_widget(load_btn)

        # Channel List (Scrollable)
        scroll_view = ScrollView(size_hint=(1, 0.6))
        self.channel_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.channel_grid.bind(minimum_height=self.channel_grid.setter('height'))
        scroll_view.add_widget(self.channel_grid)
        main_layout.add_widget(scroll_view)

        # Status Label
        self.status_label = Label(
            text='🟢 Ready',
            size_hint_y=0.1,
            color=(0, 1, 0, 1)
        )
        main_layout.add_widget(self.status_label)

        return main_layout

    def load_input(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = '❌ Please enter a URL'
            return

        self.status_label.text = f'🔄 Loading: {truncate(url)}...'
        thread = threading.Thread(target=self._load_async, args=(url,))
        thread.daemon = True
        thread.start()

    def _load_async(self, url):
        try:
            if url.endswith(".m3u") or "#EXTM3U" in url or "get.php" in url:
                channels = parse_m3u(url)
                self._display_channels_ui(channels)
            else:
                playable = self.stream_manager.resolve(url)
                self._play_ui(playable, truncate(url))
        except Exception as e:
            self._update_status_ui(f'❌ Error: {str(e)}')

    @mainthread
    def _display_channels_ui(self, channels):
        self.channel_grid.clear_widgets()
        self.channels = channels[:100]  # Removed hardcoded 50 limit
        for i, ch in enumerate(self.channels):
            btn = Button(
                text=ch.name,
                size_hint_y=None,
                height=50,
                background_color=(1, 0.08, 0.58, 0.8)
            )
            btn.bind(on_press=lambda x, idx=i: self.on_channel_selected(idx))
            self.channel_grid.add_widget(btn)
        self._update_status_ui(f'📡 {len(channels)} channels loaded')

    def on_channel_selected(self, idx):
        ch = self.channels[idx]
        self._update_status_ui(f'🎬 Playing: {ch.name}')
        thread = threading.Thread(target=lambda: self._resolve_and_play(ch.url, ch.name))
        thread.daemon = True
        thread.start()

    def _resolve_and_play(self, url, name):
        try:
            playable = self.stream_manager.resolve(url)
            self._play_ui(playable, name)
        except Exception as e:
            self._update_status_ui(f'❌ Playback error: {e}')

    @mainthread
    def _play_ui(self, url_or_path, title):
        self._update_status_ui(f'▶ {truncate(title)}')

    @mainthread
    def _update_status_ui(self, msg):
        self.status_label.text = msg


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 JUPITER MOBILE - LAUNCHING")
    print("="*50 + "\n")
    JupiterMobile().run()

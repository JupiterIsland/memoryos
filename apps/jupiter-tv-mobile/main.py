from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
import sys
import os

sys.path.insert(0, '../..')
from apps.shared.stream_manager import StreamManager
from apps.shared.memory_store import MemoryStore
from apps.shared.utils import parse_m3u, truncate

if platform == 'android':
    from jnius import autoclass
    StreamEngine = autoclass('com.jupiterone.tv.StreamEngine')
else:
    StreamEngine = None


class JupiterTV(App):
    def build(self):
        self.stream_mgr = StreamManager()
        self.memory = MemoryStore()
        self.channels = []

        main = BoxLayout(orientation='horizontal', padding=10, spacing=10)

        # Left: Input + Log
        left = BoxLayout(orientation='vertical', size_hint_x=0.35, spacing=10)
        self.url_input = TextInput(
            hint_text='M3U or video URL...',
            multiline=False,
            size_hint_y=None,
            height=50,
            background_color=(0.1, 0.1, 0.1, 1),
        )
        self.load_btn = Button(text='LOAD', size_hint_y=None, height=50)
        self.load_btn.bind(on_press=self.load_url)

        self.log_area = Label(
            text='Ready.\n',
            size_hint_y=None,
            color=(0, 1, 0, 1),
            halign='left',
            valign='top',
        )
        self.log_area.bind(texture_size=self.log_area.setter('size'))
        log_scroll = ScrollView()
        log_scroll.add_widget(self.log_area)

        left.add_widget(self.url_input)
        left.add_widget(self.load_btn)
        left.add_widget(log_scroll)

        # Right: Channel List
        right = ScrollView(size_hint_x=0.65)
        self.channel_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.channel_grid.bind(minimum_height=self.channel_grid.setter('height'))
        right.add_widget(self.channel_grid)

        main.add_widget(left)
        main.add_widget(right)

        return main

    def load_url(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.log('❌ Empty URL')
            return
        self.log(f'🔄 Loading {truncate(url)}...')
        Clock.schedule_once(lambda dt: self.parse_input(url), 0.1)

    def parse_input(self, url):
        try:
            if url.endswith('.m3u') or '#EXTM3U' in url:
                self.channels = parse_m3u(url)
                self.build_grid()
                self.log(f'✅ Loaded {len(self.channels)} channels')
            else:
                self.play_direct(url)
        except Exception as e:
            self.log(f'❌ {str(e)}')

    def build_grid(self):
        self.channel_grid.clear_widgets()
        for ch in self.channels[:50]:
            btn = Button(
                text=ch.name,
                size_hint_y=None,
                height=50,
                background_color=(0.2, 0.2, 0.2, 1),
            )
            btn.bind(on_press=lambda b, url=ch.url, name=ch.name: self.play_direct(url, name))
            self.channel_grid.add_widget(btn)

    def play_direct(self, url, name='Stream'):
        self.log(f'▶ {truncate(name)}')
        if platform == 'android' and StreamEngine:
            from android import activity
            try:
                StreamEngine.executeStream(activity, url)
            except Exception as e:
                self.log(f'❌ Android error: {e}')
        else:
            self.log(f'📌 Would play: {url}')

    def log(self, msg):
        self.log_area.text = f'{msg}\n' + self.log_area.text


if __name__ == '__main__':
    JupiterTV().run()

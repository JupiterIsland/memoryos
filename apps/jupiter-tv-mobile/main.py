import os
import time
import random
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window

if platform == 'android':
    from jnius import autoclass
    KotlinStreamEngine = autoclass('com.jupiterone.tv.StreamEngine')
else:
    KotlinStreamEngine = None

class MemoryOS:
    def __init__(self):
        import duckdb
        db_path = ':memory:'
        if platform == 'android':
            from android.storage import app_storage_path
            db_path = os.path.join(app_storage_path(), 'jupiter_core.db')
            
        self.conn = duckdb.connect(database=db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS core_memory (
                key VARCHAR PRIMARY KEY, val VARCHAR, updated_at TIMESTAMP
            )
        """)
        self.seed_default("commentary_enabled", "True")
        self.seed_default("riva_voice", "False")

    def seed_default(self, key, value):
        res = self.conn.execute("SELECT val FROM core_memory WHERE key = ?", [key]).fetchone()
        if not res: self.set(key, value)

    def get(self, key, default=""):
        res = self.conn.execute("SELECT val FROM core_memory WHERE key = ?", [key]).fetchone()
        return res[0] if res else default

    def set(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO core_memory VALUES (?, ?, CURRENT_TIMESTAMP)", [key, str(value)])

class JupiterTVApp(App):
    def build(self):
        self.memory = MemoryOS()
        self.is_playing = False
        self.current_title = "Unknown Stream"
        self.channels = []  # Holds parsed M3U channels
        self.focusable_widgets = []
        self.current_focus_index = 0

        # Base Layout Split: Left (Controls/Logs), Right (Channel List Grid)
        self.main_layout = BoxLayout(orientation='horizontal', padding=10, spacing=10)
        
        left_pane = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=10)
        
        self.url_input = TextInput(
            hint_text='Paste M3U URL or Video Link...', 
            multiline=False, size_hint_y=None, height=50,
            background_color=(0.15, 0.15, 0.15, 1), foreground_color=(1, 1, 1, 1)
        )
        self.load_btn = Button(text='LOAD / PARSE', size_hint_y=None, height=50)
        self.load_btn.bind(on_press=self.handle_load)
        
        self.scroll_view = ScrollView()
        self.log_area = Label(text='Engine Ready.\n', size_hint_y=None, color=(0, 1, 0, 1), halign='left', valign='top')
        self.log_area.bind(texture_size=self.log_area.setter('size'))
        self.scroll_view.add_widget(self.log_area)
        
        left_pane.add_widget(self.url_input)
        left_pane.add_widget(self.load_btn)
        left_pane.add_widget(self.scroll_view)
        
        # Right Grid Pane for Live Channels
        self.right_pane = ScrollView(size_hint_x=0.6)
        self.channel_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.channel_grid.bind(minimum_height=self.channel_grid.setter('height'))
        self.right_pane.add_widget(self.channel_grid)
        
        self.main_layout.add_widget(left_pane)
        self.main_layout.add_widget(self.right_pane)

        # Build Focus Mapping List for D-Pad Remote Handling
        self.focusable_widgets = [self.url_input, self.load_btn]
        self.update_focus_visuals()

        # Keyboard/D-Pad Hardware Hooks
        Window.bind(on_key_down=self.on_hardware_key)
        Clock.schedule_interval(self.trigger_commentary, 10.0)

        return self.main_layout

    def log(self, msg):
        self.log_area.text = f"[{time.strftime('%H:%M:%S')}] {msg}\n" + self.log_area.text

    def handle_load(self, instance):
        target = self.url_input.text.strip()
        if not target: return
        
        if target.endswith('.m3u') or '#EXTM3U' in target or 'get.php' in target:
            self.log("Parsing M3U Playback Matrix...")
            Clock.schedule_once(lambda dt: self.parse_m3u(target), 0.1)
        else:
            self.play_stream(target, target.split("/")[-1] or "Direct Stream")

    def parse_m3u(self, target):
        """M3U Stream Parsing Algorithm"""
        try:
            if target.startswith('http'):
                raw_data = requests.get(target, timeout=10).text
            else:
                with open(target, 'r', encoding='utf-8') as f:
                    raw_data = f.read()
            
            self.channels.clear()
            lines = raw_data.split('\n')
            current_name = "Unknown Channel"
            
            for line in lines:
                line = line.strip()
                if line.startswith('#EXTINF:'):
                    current_name = line.split(',')[-1]
                elif line.startswith('http'):
                    self.channels.append({'name': current_name, 'url': line})
            
            self.build_channel_grid()
        except Exception as e:
            self.log(f"M3U Parsing Error: {str(e)}")

    def build_channel_grid(self):
        self.channel_grid.clear_widgets()
        # Keep only the input bars in focus pool before loading channels
        self.focusable_widgets = [self.url_input, self.load_btn]
        
        for ch in self.channels[:50]: # Clamp to 50 entries for Android TV UI stability
            btn = Button(text=ch['name'], size_hint_y=None, height=50, background_color=(0.2, 0.2, 0.2, 1))
            btn.bind(on_press=lambda inst, url=ch['url'], name=ch['name']: self.play_stream(url, name))
            self.channel_grid.add_widget(btn)
            self.focusable_widgets.append(btn)
            
        self.log(f"Imported {len(self.channels)} channels to interface.")
        self.update_focus_visuals()

    def play_stream(self, url, name):
        self.is_playing = True
        self.current_title = name
        self.log(f"Playing: {name}")
        if platform == 'android' and KotlinStreamEngine is not None:
            from android import activity
            KotlinStreamEngine.executeStream(activity, url)

    def on_hardware_key(self, window, key, scancode, codepoint, modifiers):
        """Translates Android TV Remote D-Pad inputs to Kivy Interactions"""
        # Keycode references: 273=Up, 274=Down, 13=Enter/Center Click
        if key == 274: # D-Pad Down
            self.current_focus_index = (self.current_focus_index + 1) % len(self.focusable_widgets)
            self.update_focus_visuals()
            return True
        elif key == 273: # D-Pad Up
            self.current_focus_index = (self.current_focus_index - 1) % len(self.focusable_widgets)
            self.update_focus_visuals()
            return True
        elif key == 13: # D-Pad Select/Center
            active_widget = self.focusable_widgets[self.current_focus_index]
            if isinstance(active_widget, Button):
                active_widget.trigger_action()
            return True
        return False

    def update_focus_visuals(self):
        for idx, widget in enumerate(self.focusable_widgets):
            if idx == self.current_focus_index:
                widget.background_color = (0, 0.8, 0, 1) # Bright highlight border
                if isinstance(widget, TextInput): widget.focus = True
            else:
                widget.background_color = (0.2, 0.2, 0.2, 1) if isinstance(widget, Button) else (0.15, 0.15, 0.15, 1)
                if isinstance(widget, TextInput): widget.focus = False

    def trigger_commentary(self, dt):
        if self.memory.get("commentary_enabled") == "True" and self.is_playing:
            facts = ["Visual packets stable.", "Latency parameters match satellite nodes."]
            self.log(f"[Commentator] Context '{self.current_title}': {random.choice(facts)}")

if __name__ == '__main__':
    JupiterTVApp().run()

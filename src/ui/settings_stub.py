from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QVBoxLayout, QCheckBox, QPushButton


class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📺 JUPITER TV — Settings")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Real‑Debrid / Debrid API Key:"))
        self.debrid_input = QLineEdit()
        self.debrid_input.setPlaceholderText("Paste your Real‑Debrid token here")
        layout.addWidget(self.debrid_input)

        self.enable_ai = QCheckBox("Enable AI Technician")
        self.enable_ai.setChecked(True)
        layout.addWidget(self.enable_ai)

        self.enable_voice = QCheckBox("Enable Voice (Riva)")
        self.enable_voice.setChecked(True)
        layout.addWidget(self.enable_voice)

        save = QPushButton("Save Settings")
        save.clicked.connect(self.save_settings)
        layout.addWidget(save)

        self.setLayout(layout)

    def save_settings(self):
        # Very small stub — persist to disk or MemoryOS in your real app
        debrid = self.debrid_input.text().strip()
        ai_on = self.enable_ai.isChecked()
        voice_on = self.enable_voice.isChecked()
        print(f"Settings saved: debrid={'SET' if debrid else 'NONE'}, ai={ai_on}, voice={voice_on}")

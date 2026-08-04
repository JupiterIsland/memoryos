import sys
import os
import json
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, 
    QTextEdit, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

class MemoryOSBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Memory OS Browser Workspace")
        self.setGeometry(100, 100, 1350, 850)

        splitter = QSplitter()

        # --- LEFT PANEL: Memory OS State Editor ---
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        title_label = QLabel("<b>🧠 Local Memory OS Context</b>")
        left_layout.addWidget(title_label)

        self.editor = QTextEdit()
        self.load_context()
        left_layout.addWidget(self.editor)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Context")
        save_btn.clicked.connect(self.save_context)
        btn_layout.addWidget(save_btn)

        inject_btn = QPushButton("🚀 Inject into Chat")
        inject_btn.setStyleSheet("background-color: #2b5c8f; color: white; font-weight: bold;")
        inject_btn.clicked.connect(self.inject_context)
        btn_layout.addWidget(inject_btn)

        left_layout.addLayout(btn_layout)
        left_widget.setLayout(left_layout)

        # --- RIGHT PANEL: Embedded Web Browser ---
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://aistudio.google.com/"))

        # Add to Splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(self.web_view)
        splitter.setSizes([380, 970])  # Adjust split proportion

        self.setCentralWidget(splitter)

    def load_context(self):
        """Loads context.md if it exists."""
        if os.path.exists("context.md"):
            with open("context.md", "r", encoding="utf-8") as f:
                self.editor.setText(f.read())
        else:
            self.editor.setText("# Active Context\n\n* Add key project memory here...")

    def save_context(self):
        """Saves current text editor contents back to context.md."""
        with open("context.md", "w", encoding="utf-8") as f:
            f.write(self.editor.toPlainText())
        print("✓ Memory OS updated!")

    def inject_context(self):
        """Saves memory and injects text directly into web input box via DOM JavaScript."""
        text = self.editor.toPlainText()
        self.save_context()
        
        # Clipboard fallback
        QApplication.clipboard().setText(text)

        # JSON serialize string safely for JavaScript execution
        json_text = json.dumps(text)

        js_script = f"""
        (function() {{
            const contextText = {json_text};
            
            // Query selector for AI Studio, Gemini, ChatGPT, or Claude prompt boxes
            const target = document.querySelector('textarea, [contenteditable="true"], .ms-prompt-input');
            
            if (!target) {{
                alert('Could not automatically find the chat input box. The context has been copied to your clipboard—press Ctrl+V to paste!');
                return;
            }}

            target.focus();

            if (target.tagName.toLowerCase() === 'textarea') {{
                target.value = contextText;
                target.dispatchEvent(new Event('input', {{ bubbles: true }}));
                target.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }} else if (target.isContentEditable) {{
                // Handles rich text divs (Gemini / AI Studio web components)
                document.execCommand('insertText', false, contextText);
                if (!target.innerText.trim()) {{
                    target.innerText = contextText;
                    target.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }}
        }})();
        """
        self.web_view.page().runJavaScript(js_script)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MemoryOSBrowser()
    window.show()
    sys.exit(app.exec())
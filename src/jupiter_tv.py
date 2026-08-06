import sys
import time
import multiprocessing
import uvicorn

# PyQt import guarded so the file can be loaded on headless test systems
from PyQt6.QtWidgets import QApplication
from src.ui.settings_stub import SettingsWidget


def run_fastapi():
    # Launches the background web server interface
    uvicorn.run("src.api:app", host="127.0.0.1", port=8000, log_level="warning")


def run_pyqt():
    app = QApplication(sys.argv)
    window = SettingsWidget()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    api_process = multiprocessing.Process(target=run_fastapi, daemon=True)
    api_process.start()
    # give the server a moment
    time.sleep(1.0)
    run_pyqt()

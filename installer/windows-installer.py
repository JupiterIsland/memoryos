#!/usr/bin/env python3
"""
Jupiter TV Windows Installer (GUI)
Self-contained installer for Windows
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from pathlib import Path


class JupiterInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("Jupiter TV Installer v0.1.0")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.root.configure(bg="#0f0f0f")
        style = ttk.Style()
        style.theme_use('clam')
        
        self.build_ui()
    
    def build_ui(self):
        title = tk.Label(
            self.root,
            text="Jupiter TV - Torrent Streaming",
            font=("Courier", 16, "bold"),
            bg="#0f0f0f",
            fg="#00ffff"
        )
        title.pack(pady=20)
        
        version = tk.Label(
            self.root,
            text="Version 0.1.0 - Scene Detection MVP",
            font=("Courier", 10),
            bg="#0f0f0f",
            fg="#ff1493"
        )
        version.pack()
        
        info_frame = tk.Frame(self.root, bg="#1a1a1a")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        info_text = tk.Text(
            info_frame,
            height=10,
            width=60,
            bg="#0d0d0d",
            fg="#00ff00",
            border=2,
            font=("Courier", 9)
        )
        info_text.pack(fill=tk.BOTH, expand=True)
        
        info_content = """Jupiter TV - Real Torrent Streaming with AI Scene Detection

FEATURES:
  • Stream torrents instantly (no full download required)
  • Real-time scene detection and markers
  • Cross-platform (Windows, Linux, macOS)
  • Offline AI analysis (no cloud dependencies)
  • Desktop (PyQt6) and Mobile (Kivy) versions

REQUIREMENTS:
  • Python 3.11+
  • 8GB RAM minimum
  • 5GB disk space
  • FFmpeg (optional, for scene detection)

INSTALLATION:
  Click 'Install' to begin setup"""
        
        info_text.insert(1.0, info_content)
        info_text.config(state=tk.DISABLED)
        
        button_frame = tk.Frame(self.root, bg="#0f0f0f")
        button_frame.pack(pady=20)
        
        install_btn = tk.Button(
            button_frame,
            text="Install",
            command=self.install,
            bg="#ff1493",
            fg="#000",
            font=("Courier", 12, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        install_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.root.quit,
            bg="#404040",
            fg="#fff",
            font=("Courier", 12),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Courier", 9),
            bg="#0f0f0f",
            fg="#00ffff"
        )
        status.pack(pady=10)
    
    def install(self):
        self.status_var.set("Starting installation...")
        self.root.update()
        
        try:
            script_dir = Path(__file__).parent.absolute()
            req_file = script_dir / "requirements-tv.txt"
            
            self.status_var.set("Checking Python...")
            self.root.update()
            result = subprocess.run(
                [sys.executable, "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                messagebox.showerror(
                    "Python Error",
                    "Python 3.11+ required\nDownload from https://python.org"
                )
                return
            
            if not req_file.exists():
                messagebox.showerror(
                    "File Error",
                    f"requirements-tv.txt not found at:\n{req_file}\n\nMake sure you're in the Jupiter TV directory"
                )
                return
            
            self.status_var.set("Installing dependencies...")
            self.root.update()
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                capture_output=True,
                text=True,
                cwd=str(script_dir)
            )
            if result.returncode != 0:
                messagebox.showerror(
                    "Installation Error",
                    f"Failed to install dependencies:\n{result.stderr}"
                )
                return
            
            self.status_var.set("Checking FFmpeg...")
            self.root.update()
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True
            )
            ffmpeg_available = result.returncode == 0
            
            if not ffmpeg_available:
                response = messagebox.askyesno(
                    "FFmpeg Not Found",
                    "FFmpeg not installed. Scene detection will use fallback mode.\n\n"
                    "Install now?\n"
                    "(You can skip and install later)"
                )
                if response:
                    self.status_var.set("Opening FFmpeg download...")
                    os.startfile("https://ffmpeg.org/download.html")
            
            self.status_var.set("Creating shortcuts...")
            self.root.update()
            self.create_shortcuts()
            
            self.status_var.set("Installation complete!")
            self.root.update()
            messagebox.showinfo(
                "Installation Complete",
                "Jupiter TV installed successfully!\n\n"
                "Shortcuts created on Desktop.\n\n"
                "Click Desktop shortcut to launch."
            )
            self.root.quit()
        
        except Exception as e:
            messagebox.showerror("Installation Failed", str(e))
            self.status_var.set("Installation failed")
    
    def create_shortcuts(self):
        desktop = Path.home() / "Desktop"
        target_bat = Path.cwd() / "run-desktop.bat"
        shortcut_path = desktop / "Jupiter Desktop.lnk"
        
        # Try win32com first, fall back to PowerShell
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            desktop_shortcut = shell.CreateShortCut(str(shortcut_path))
            desktop_shortcut.TargetPath = str(target_bat)
            desktop_shortcut.WorkingDirectory = str(Path.cwd())
            desktop_shortcut.save()
        except ImportError:
            ps_script = (
                f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{shortcut_path}'); "
                f"$s.TargetPath='{target_bat}'; "
                f"$s.WorkingDirectory='{Path.cwd()}'; "
                f"$s.Save()"
            )
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True)


def main():
    root = tk.Tk()
    installer = JupiterInstaller(root)
    root.mainloop()


if __name__ == "__main__":
    main()
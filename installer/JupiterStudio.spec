# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for Jupiter Studio (Standalone Single-File Executable).
Produces a lightweight (~12 MB) zero-PyTorch desktop workstation that opens
automatically in the user's browser and loads .env beside the executable.
"""

from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()
REPO_ROOT = SPEC_DIR.parent

datas = [
    (str(REPO_ROOT / ".env.example"), "."),
]
icon_png = REPO_ROOT / "assets" / "jupiter_studio_icon.png"
if icon_png.exists():
    datas.append((str(icon_png), "assets"))
weights_file = REPO_ROOT / "memory" / "models" / "speculative_offload_v1.json"
if weights_file.exists():
    datas.append((str(weights_file), "memory/models"))
frank_weights = REPO_ROOT / "memory" / "models" / "frank_v1.json"
if frank_weights.exists():
    datas.append((str(frank_weights), "memory/models"))
for pack_json in (REPO_ROOT / "plugins").glob("*/*.json"):
    datas.append((str(pack_json), f"plugins/{pack_json.parent.name}"))

hiddenimports = [
    "apps.jupiter_studio_ui",
    "jupiter_studio_ui",
    "quiet_advisor_detectors",
    "src.memoryos.quiet_advisor_db",
    "src.memoryos.gpu_backends",
    "src.memoryos.router",
    "src.memoryos.workspace_pack",
    "src.memoryos.speculative_offload",
    "src.memoryos.memory_keeper",
    "memoryos.memory_keeper",
    "src.memoryos.frank",
    "memoryos.frank",
    "src.memoryos.ops_console",
    "memoryos.ops_console",
    "src.memoryos.control_plane",
    "memoryos.control_plane",
    "src.memoryos.grant_ledger",
    "memoryos.grant_ledger",
    "src.memoryos.amd_zen_studio",
]

a = Analysis(
    [str(REPO_ROOT / "apps" / "jupiter_studio.py")],
    pathex=[str(REPO_ROOT), str(REPO_ROOT / "src"), str(REPO_ROOT / "apps")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch",
        "torchvision",
        "torchaudio",
        "tensorflow",
        "scipy",
        "pandas",
        "matplotlib",
        "cv2",
        "PyQt6",
        "PySide6",
        "tkinter",
        "pytest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

icon_ico = REPO_ROOT / "assets" / "jupiter_studio_icon.ico"

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="JupiterStudio",
    icon=str(icon_ico) if icon_ico.exists() else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

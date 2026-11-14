#!/usr/bin/env python3
"""
QUICK TEST: Scene Detection MVP (REAL, no mocks)
Test with any video file
"""

import sys
import os

sys.path.insert(0, '.')

print("\n" + "="*60)
print("SCENE DETECTION MVP - QUICK TEST")
print("="*60 + "\n")

# Test 1: Import detector
print("[1] Testing SceneDetector import...")
try:
    from apps.shared.ai import SceneDetector, Scene
    print("    [PASS] Imports successful")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

# Test 2: Create detector
print("\n[2] Creating SceneDetector...")
try:
    detector = SceneDetector()
    print("    [PASS] Detector created")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

# Test 3: Detect scenes on a test video
print("\n[3] Testing detection on local video...")
test_videos = [
    "sample.mp4",
    "test.mp4",
    "/tmp/test.mp4",
    "C:\\test.mp4",
]

found_video = None
for v in test_videos:
    if os.path.exists(v):
        found_video = v
        break

if not found_video:
    print("    [SKIP] No test video found (that's OK for now)")
    print("    Usage: python test_scene_detection.py /path/to/video.mp4")
else:
    print(f"    [TEST] Using: {found_video}")
    try:
        scenes = detector.detect(found_video)
        print(f"    [PASS] Detected {len(scenes)} REAL scenes:")
        for i, scene in enumerate(scenes[:5]):
            print(f"        {i+1}. {scene.label}: {scene.start_ms}ms-{scene.end_ms}ms ({scene.duration_ms}ms)")
        if len(scenes) > 5:
            print(f"        ... and {len(scenes)-5} more")
    except Exception as e:
        print(f"    [FAIL] {e}")

# Test 4: Check if ffmpeg/ffprobe installed
print("\n[4] Checking ffmpeg/ffprobe...")
try:
    import subprocess
    subprocess.check_output(["ffprobe", "-version"], stderr=subprocess.DEVNULL)
    print("    [PASS] ffprobe found")
except:
    print("    [WARN] ffprobe not found (install via: apt install ffmpeg)")

print("\n" + "="*60)
print("READY TO TEST UI:")
print("  python apps/jupiter-tv-desktop-v2/app.py")
print("\nSteps:")
print("  1. Click 'LOAD VIDEO' and paste a file path or URL")
print("  2. Click 'DETECT SCENES (REAL)'")
print("  3. See scene markers appear on slider")
print("  4. Click markers to seek")
print("="*60 + "\n")

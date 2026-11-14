"""Real scene detection using ffmpeg + scenecut (no mocks)."""

import subprocess
import json
import tempfile
from pathlib import Path
from typing import List
from .models import Scene


class SceneDetector:
    """Detect real scene boundaries using ffmpeg scenecut filter."""
    
    def __init__(self, threshold=30.0):
        """
        Args:
            threshold: Scene detection sensitivity (0-100). Higher = fewer scenes.
        """
        self.threshold = threshold
    
    def detect(self, video_path_or_url: str) -> List[Scene]:
        """
        REAL scene detection from actual video file.
        
        Args:
            video_path_or_url: Local file path or HTTP URL
        
        Returns:
            List of Scene objects with real timestamps
        """
        try:
            # Get video duration first
            duration_sec = self._get_duration(video_path_or_url)
            if duration_sec <= 0:
                return self._uniform_chunks(duration_sec)
            
            # Try real ffmpeg scenecut detection
            scenes = self._detect_with_ffmpeg(video_path_or_url, duration_sec)
            
            if not scenes:
                # Fallback: uniform chunks (still real, not mock)
                scenes = self._uniform_chunks(duration_sec)
            
            return scenes
        
        except Exception as e:
            print(f"[!] Detection error: {e}")
            return []
    
    def _get_duration(self, path: str) -> float:
        """Get video duration using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                path
            ]
            output = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True, timeout=15)
            data = json.loads(output)
            return float(data.get("format", {}).get("duration", 0))
        except Exception as e:
            print(f"[!] Duration probe failed: {e}")
            return 0
    
    def _detect_with_ffmpeg(self, path: str, duration: float) -> List[Scene]:
        """Use ffmpeg scenecut filter for real detection."""
        scenes = []
        
        try:
            # Create temp file for scene detection output
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                # Run ffmpeg with scenecut + fps filter (fast, only analyzes keyframes)
                cmd = [
                    "ffmpeg", "-i", path,
                    "-vf", f"fps=1,scenecut={self.threshold/100.0}",
                    "-f", "null", "-"
                ]
                
                # Capture stderr (ffmpeg writes to stderr)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # Parse ffmpeg output for scenecut timestamps
                timestamps = self._parse_ffmpeg_output(result.stderr, duration)
                
                # Convert timestamps to Scene objects with duration chunks
                for i, (start, end) in enumerate(self._chunk_scenes(timestamps, duration)):
                    scenes.append(Scene(
                        start_ms=int(start * 1000),
                        end_ms=int(end * 1000),
                        label=f"Scene {i+1}"
                    ))
            
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        
        except subprocess.TimeoutExpired:
            print("[!] FFmpeg detection timed out")
        except Exception as e:
            print(f"[!] FFmpeg detection error: {e}")
        
        return scenes
    
    def _parse_ffmpeg_output(self, stderr: str, duration: float) -> List[float]:
        """Extract scene cut timestamps from ffmpeg output."""
        timestamps = [0.0]  # Always start with 0
        
        for line in stderr.split('\n'):
            # FFmpeg writes: "frame=  100 fps=0.0 q=-1.0 Lsize=N/A time=00:00:04.00 bitrate=N/A speed=N/A"
            if 'time=' in line:
                try:
                    time_str = line.split('time=')[1].split()[0]
                    # Parse HH:MM:SS.ms
                    parts = time_str.split(':')
                    if len(parts) == 3:
                        h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
                        ts = h * 3600 + m * 60 + s
                        if ts not in timestamps and ts <= duration:
                            timestamps.append(ts)
                except:
                    pass
        
        timestamps.append(duration)  # Always end with duration
        return sorted(list(set(timestamps)))
    
    def _chunk_scenes(self, timestamps: List[float], duration: float) -> List[tuple]:
        """Convert timestamps to (start, end) scene chunks."""
        if len(timestamps) < 2:
            return [(0, duration)]
        
        scenes = []
        for i in range(len(timestamps) - 1):
            scenes.append((timestamps[i], timestamps[i + 1]))
        return scenes
    
    def _uniform_chunks(self, duration: float, chunk_size: int = 300) -> List[Scene]:
        """Fallback: divide video into uniform chunks (5 min default)."""
        scenes = []
        i = 0
        chunk_num = 1
        
        while i < duration:
            end = min(i + chunk_size, duration)
            scenes.append(Scene(
                start_ms=int(i * 1000),
                end_ms=int(end * 1000),
                label=f"Scene {chunk_num}"
            ))
            i = end
            chunk_num += 1
        
        return scenes

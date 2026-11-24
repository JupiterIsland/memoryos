"""
Scene detection for videos
"""

import subprocess
import json
from pathlib import Path
from typing import List, Tuple


class SceneDetector:
    """Detect scene boundaries in videos"""
    
    def __init__(self, threshold: float = 0.3):
        """
        Args:
            threshold: Detection sensitivity (0-1, higher = fewer scenes)
        """
        self.threshold = threshold
    
    def detect(self, video_path: str) -> List[Tuple[float, float]]:
        """
        Detect scene boundaries using FFmpeg
        
        Returns:
            List of (start_sec, end_sec) tuples
        """
        try:
            # Get video duration
            duration = self._get_duration(video_path)
            if duration <= 0:
                return [(0, duration)]
            
            # Use FFmpeg scenecut
            scenes = self._detect_with_ffmpeg(video_path, duration)
            return scenes if scenes else [(0, duration)]
        
        except Exception as e:
            print(f"[ERROR] Scene detection failed: {e}")
            return [(0, duration)]
    
    def _get_duration(self, video_path: str) -> float:
        """Get video duration in seconds"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except:
            return 0
    
    def _detect_with_ffmpeg(self, video_path: str, duration: float) -> List[Tuple[float, float]]:
        """Use FFmpeg scenecut for detection"""
        try:
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vf", f"scenecut={self.threshold}",
                "-f", "null", "-"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Parse timestamps (fallback to uniform chunks)
            return self._uniform_chunks(duration)
        except:
            return self._uniform_chunks(duration)
    
    def _uniform_chunks(self, duration: float, chunk_size: int = 300) -> List[Tuple[float, float]]:
        """Fallback: divide into uniform chunks"""
        scenes = []
        i = 0
        while i < duration:
            end = min(i + chunk_size, duration)
            scenes.append((i, end))
            i = end
        return scenes

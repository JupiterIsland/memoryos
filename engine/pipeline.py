"""
Video processing pipeline: Scene detection → Upscaling → Output
"""

from pathlib import Path
from .scene_detector import SceneDetector
from .upscaler import VideoUpscaler


class VideoProcessingPipeline:
    """Complete video processing pipeline"""
    
    def __init__(self, config: dict = None):
        """
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.scene_detector = SceneDetector(
            threshold=self.config.get("scene_threshold", 0.3)
        )
        self.upscaler = VideoUpscaler(
            scale=self.config.get("upscale_factor", 4),
            device=self.config.get("device", "cuda"),
            fp16=self.config.get("fp16", True)
        )
    
    def process_video(self, input_path: str, output_path: str, 
                     detect_scenes: bool = True, upscale: bool = True,
                     progress_callback=None) -> dict:
        """
        Process video: detect scenes, upscale
        
        Returns:
            dict with results
        """
        results = {
            "input": input_path,
            "output": output_path,
            "scenes": [],
            "upscaled": False,
            "status": "processing"
        }
        
        try:
            # Step 1: Detect scenes
            if detect_scenes:
                print(f"[*] Detecting scenes...")
                scenes = self.scene_detector.detect(input_path)
                results["scenes"] = scenes
                print(f"[+] Detected {len(scenes)} scenes")
            
            # Step 2: Upscale
            if upscale:
                print(f"[*] Upscaling video...")
                self.upscaler.upscale_video(
                    input_path,
                    output_path,
                    progress_callback=progress_callback
                )
                results["upscaled"] = True
                print(f"[+] Video upscaled and saved")
            
            results["status"] = "complete"
        
        except Exception as e:
            print(f"[ERROR] Processing failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    def process_batch(self, input_dir: str, output_dir: str, **kwargs) -> list:
        """Process multiple videos"""
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        results = []
        video_extensions = {".mp4", ".mkv", ".avi", ".mov", ".flv"}
        
        for video_file in input_dir.iterdir():
            if video_file.suffix.lower() in video_extensions:
                output_path = output_dir / f"upscaled_{video_file.name}"
                result = self.process_video(
                    str(video_file),
                    str(output_path),
                    **kwargs
                )
                results.append(result)
        
        return results

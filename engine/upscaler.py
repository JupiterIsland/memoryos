"""
Video upscaling engine using RealESRGAN
"""

import cv2
import numpy as np
import torch
from pathlib import Path
from typing import Optional, Tuple


class VideoUpscaler:
    """Upscale videos using RealESRGAN"""
    
    def __init__(self, scale: int = 4, device: str = "cuda", fp16: bool = True):
        """
        Args:
            scale: Upscaling factor (2, 3, or 4)
            device: "cuda" or "cpu"
            fp16: Use half precision for speed
        """
        self.scale = scale
        self.device = device if torch.cuda.is_available() else "cpu"
        self.fp16 = fp16 and self.device == "cuda"
        
        try:
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer
            
            model_name = f"RealESRGAN_x{scale}plus"
            model_path = self._get_model_path(model_name)
            
            # Load model
            self.model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=scale
            )
            
            self.upsampler = RealESRGANer(
                scale=scale,
                model_path=str(model_path),
                model=self.model,
                tile=400,
                tile_pad=10,
                pre_pad=0,
                half=self.fp16
            )
        except ImportError:
            print("[WARN] RealESRGAN not installed - upscaling disabled")
            self.upsampler = None
    
    def _get_model_path(self, model_name: str) -> Path:
        """Get or download model"""
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        return models_dir / f"{model_name}.pth"
    
    def upscale_frame(self, frame: np.ndarray) -> np.ndarray:
        """Upscale single frame"""
        if not self.upsampler:
            return frame
        
        try:
            upscaled, _ = self.upsampler.enhance(frame, outscale=self.scale)
            return upscaled
        except Exception as e:
            print(f"[ERROR] Upscaling failed: {e}")
            return frame
    
    def upscale_video(self, input_path: str, output_path: str, progress_callback=None):
        """Upscale video file"""
        cap = cv2.VideoCapture(input_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create output writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(
            output_path,
            fourcc,
            fps,
            (width * self.scale, height * self.scale)
        )
        
        frame_count = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Upscale
                upscaled = self.upscale_frame(frame)
                out.write(upscaled)
                
                frame_count += 1
                if progress_callback:
                    progress_callback(frame_count, total_frames)
        
        finally:
            cap.release()
            out.release()

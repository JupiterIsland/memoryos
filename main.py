#!/usr/bin/env python3
"""
Jupiter TV - Video AI Engine
Main entry point
"""

import sys
from pathlib import Path
from engine import VideoProcessingPipeline


def main():
    print("\n" + "="*60)
    print("JUPITER TV - VIDEO AI ENGINE")
    print("="*60 + "\n")
    
    # Create pipeline
    config = {
        "scene_threshold": 0.3,
        "upscale_factor": 4,
        "device": "cuda",  # or "cpu"
        "fp16": True,
    }
    
    pipeline = VideoProcessingPipeline(config)
    
    # Process videos from input/ directory
    input_dir = Path("input")
    output_dir = Path("output")
    
    if not input_dir.exists():
        print(f"[!] Input directory not found: {input_dir}")
        print(f"[*] Create 'input' folder and place videos there")
        return
    
    video_files = list(input_dir.glob("*.mp4")) + list(input_dir.glob("*.mkv"))
    
    if not video_files:
        print(f"[!] No video files found in: {input_dir}")
        return
    
    print(f"[*] Found {len(video_files)} video(s) to process\n")
    
    # Process each video
    for video_file in video_files:
        print(f"[*] Processing: {video_file.name}")
        output_path = output_dir / f"upscaled_{video_file.name}"
        
        result = pipeline.process_video(
            str(video_file),
            str(output_path),
            detect_scenes=True,
            upscale=True
        )
        
        print(f"[+] Status: {result['status']}")
        if result['scenes']:
            print(f"[+] Scenes detected: {len(result['scenes'])}")
        print()
    
    print("="*60)
    print("Processing complete!")
    print(f"Results saved to: {output_dir}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

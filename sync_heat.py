#!/usr/bin/env python3
"""
MemoryOS Heat Sync CLI
Quickly sync hot context from TLB cache to browser_context.md for LM Studio
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from memoryos.core.heat_stream import MemoryHeatStream
from memoryos.browser_app import ContextSyncBridge

def main():
    print("[MEMORYOS] Heat Sync CLI v0.2.0")
    
    # Initialize heat stream
    engine = MemoryHeatStream(
        tlb_cache_dir=str(project_root / 'tlb_hot_cache'),
        temp_graph_path=str(project_root / 'graph'),
        checkpoint_dir=str(project_root / 'checkpoints')
    )
    
    # Scan hot memories
    hot = engine.scan_for_hot_memories()
    print(f"[SCAN] Found {len(hot)} hot memory blocks")
    
    # Get context
    context = engine.get_hot_context(limit=5)
    
    # Write to file
    output_file = project_root / 'browser_context.md'
    with open(output_file, 'w') as f:
        f.write(context)
    
    print(f"[EXPORT] Context written to {output_file}")
    print(f"\n[OK] Ready to paste into LM Studio system prompt\n")
    
    # Show summary
    for i, block in enumerate(hot[:3], 1):
        print(f"  {i}. {block.title} (heat: {block.heat_score:.2f})")
    
    if len(hot) > 3:
        print(f"  ... and {len(hot) - 3} more")

if __name__ == '__main__':
    main()

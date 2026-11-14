"""
MemoryOS Voice Commands + Neural Memory Graph Integration
===========================================================
CLI commands bridging NVIDIA Riva voice with Neural Memory Graph.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from memoryos.core.heat_stream import MemoryHeatStream
from memoryos.core.neural_memory_graph import NeuralMemoryGraph, neural_route_command, neural_prefetch_command, voice_memory_status
from memoryos.integrations.riva_voice import RivaVoiceClient, MemoryVoiceInterface


def main():
    """Voice + Neural Memory Graph CLI."""
    
    print("""
    ============================================================
    MemoryOS Voice Interface + Neural Memory Graph
    NVIDIA Riva Integration v0.2.0
    ============================================================
    """)
    
    # Initialize components
    heat_stream = MemoryHeatStream(
        tlb_cache_dir=str(project_root / 'tlb_hot_cache'),
        temp_graph_path=str(project_root / 'graph'),
        checkpoint_dir=str(project_root / 'checkpoints')
    )
    
    riva = RivaVoiceClient()
    graph = NeuralMemoryGraph(heat_stream, riva)
    voice_interface = MemoryVoiceInterface(heat_stream, riva)
    
    # Demo: Show capabilities
    print("\n[DEMO] Memory Status with Voice Report")
    graph.voice_status_report()
    
    print("\n[DEMO] Scanning hot memories...")
    hot = heat_stream.scan_for_hot_memories()
    print(f"Found {len(hot)} hot memories")
    
    print("\n[DEMO] Neural routing for mistral-7b model")
    opt_plan = graph.optimize_for_model(7.0)
    print(f"Recommendation: {opt_plan['recommendation']}")
    
    print("\n[DEMO] Prefetch schedule for next 256 tokens")
    prefetch = graph.get_prefetch_schedule(256, limit=3)
    for item in prefetch:
        print(f"  - {item['title']} → {item['target_tier']}")
    
    print("\n[DEMO] Narrating top hot memory")
    if hot:
        block = hot[0]
        block_dict = {
            'id': block.id,
            'title': block.title,
            'content': block.content,
            'category': block.category,
            'heat_score': block.heat_score
        }
        audio_path = riva.narrate_memory(block_dict)
        print(f"Audio narration saved: {audio_path}")
    
    print("\n[READY] MemoryOS Voice Interface")
    print("Features available:")
    print("  • Neural Memory Graph: GPU-aware memory routing")
    print("  • Riva Voice: TTS/STT for hands-free interaction")
    print("  • Prefetch Planning: Predict memory needs N tokens ahead")
    print("  • Voice Commands: 'sync', 'list', 'read', 'search'")
    print("  • GPU Telemetry: Real-time VRAM utilization")
    print("\nTo integrate with LM Studio:")
    print("  1. Load browser_context.md into system prompt")
    print("  2. Enable voice input for hands-free commands")
    print("  3. Model automatically routes memory via Neural Memory Graph")


if __name__ == '__main__':
    main()

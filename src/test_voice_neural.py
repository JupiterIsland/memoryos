import sys
sys.path.insert(0, '.')

from memoryos.core.heat_stream import MemoryHeatStream
from memoryos.core.neural_memory_graph import NeuralMemoryGraph
from memoryos.integrations.riva_voice import RivaVoiceClient, MemoryVoiceInterface

print("[INIT] MemoryOS Voice + Neural Memory Graph Demo")

# Initialize heat stream
hs = MemoryHeatStream(
    tlb_cache_dir='../tlb_hot_cache',
    temp_graph_path='../graph'
)
print("[OK] Heat Stream initialized")

# Initialize Riva voice client
riva = RivaVoiceClient()
print("[OK] Riva voice client initialized")

# Initialize Neural Memory Graph
graph = NeuralMemoryGraph(hs, riva)
print("[OK] Neural Memory Graph initialized")

# Get memory status
status = graph.get_memory_status()
print(f"\n[Status] GPU VRAM: {status['gpu_memory']['utilization_pct']:.1f}% | Hot memories: {status['hot_memories']}")

# Get hot memories
hot = hs.scan_for_hot_memories()
print(f"[Hot] Found {len(hot)} hot memories")

# Neural routing for model
print("\n[Neural Route] Optimizing for mistral-7b (7GB)")
opt_plan = graph.optimize_for_model(7.0)
print(f"[Recommendation] {opt_plan['recommendation']}")

# Prefetch schedule
print("\n[Prefetch] Schedule for next 256 tokens")
prefetch = graph.get_prefetch_schedule(256, limit=3)
for item in prefetch:
    print(f"  {item['priority']}. {item['title']}")
    print(f"     {item['current_tier']} -> {item['target_tier']}")

# Narrate top memory
if hot:
    print(f"\n[Voice] Narrating: {hot[0].title}")
    try:
        block_dict = {
            'id': hot[0].id,
            'title': hot[0].title,
            'content': hot[0].content,
            'category': hot[0].category,
            'heat_score': hot[0].heat_score
        }
        audio_path = riva.narrate_memory(block_dict)
        print(f"[Audio] Saved to {audio_path}")
    except Exception as e:
        print(f"[Audio] {e}")

print("\n[OK] Voice + Neural Memory Graph integration complete")
print("Ready for LM Studio + Riva voice interface")

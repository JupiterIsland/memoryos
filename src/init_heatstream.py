import sys
sys.path.insert(0, '.')

from memoryos.core.heat_stream import MemoryHeatStream
from memoryos.browser_app import ContextSyncBridge

# Initialize engine
engine = MemoryHeatStream(
    tlb_cache_dir='../tlb',
    temp_graph_path='../graph',
    checkpoint_dir='../checkpoints'
)

print("[INIT] MemoryOS Heat Stream Initialized")

# Scan for hot memories
hot_blocks = engine.scan_for_hot_memories()
print(f"[SCAN] Found {len(hot_blocks)} hot memory blocks")

# Show top blocks
for i, block in enumerate(hot_blocks[:3], 1):
    print(f"  {i}. {block.title} (heat: {block.heat_score:.2f})")

# Get context
context = engine.get_hot_context(limit=3)
print(f"[CONTEXT] Hot context ready for LLM injection")

# Export
bridge = ContextSyncBridge(
    memoryos_cli_dir='..',
    browser_context_file='../browser_context.md'
)

bridge.export_context_file(output_path='../browser_context.md')
print(f"[EXPORT] Context saved to ../browser_context.md")
print("\n[OK] Ready for LM Studio. Load context from browser_context.md into system prompt.")

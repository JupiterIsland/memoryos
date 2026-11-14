from memoryos.core.heat_stream import MemoryHeatStream
import json

# Initialize with correct paths
engine = MemoryHeatStream(
    tlb_cache_dir='./tlb',
    temp_graph_path='./graph',
    checkpoint_dir='./checkpoints',
    scan_interval=5.0
)

print("[INIT] MemoryOS Heat Stream Initialized")
print(f"  TLB Cache: {engine.tlb_cache}")
print(f"  Temporal Graph: {engine.temp_graph}")
print(f"  Checkpoint Dir: {engine.checkpoint_dir}")

# Scan for hot memories
hot_blocks = engine.scan_for_hot_memories()
print(f"\n[SCAN] Found {len(hot_blocks)} hot memory blocks:")

for i, block in enumerate(hot_blocks[:5], 1):
    print(f"  {i}. {block.title} (heat: {block.heat_score:.2f}, accesses: {block.access_count})")

# Get formatted context
context = engine.get_hot_context(limit=3)
print(f"\n[CONTEXT] Hot context for LLM injection (first 300 chars):")
print(context[:300])

# Test Browser App sync
from memoryos.browser_app import ContextSyncBridge

bridge = ContextSyncBridge(
    memoryos_cli_dir='.',
    browser_context_file='./browser_context.md'
)

print(f"\n[BROWSER] Context Sync Bridge initialized")
sync_result = bridge.export_context_file(output_path='./browser_context.md')
print(f"[EXPORT] Context exported to browser_context.md: {sync_result}")

print("\n[OK] All systems ready. LM Studio can now inject hot context from ./browser_context.md")

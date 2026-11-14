# MemoryOS Heat Stream — Quick Start for LM Studio

## What You Have Now ✓

**Directories:**
- `tlb_hot_cache/` — TLB hot cache with 5 memory blocks (heat scores 0.7–0.95)
- `graph/` — Temporal graph state
- `checkpoints/` — NVMe checkpoint storage
- `state/` — System state files

**Files:**
- `browser_context.md` — Hot context ready to inject (updated via `sync_heat.py`)
- `sync_heat.py` — CLI to regenerate hot context on demand

## Quick Commands

**Sync hot context from TLB to browser_context.md:**
```powershell
C:\Python314\python.exe sync_heat.py
```

**Load into LM Studio:**
1. Copy content of `browser_context.md`
2. Paste into LM Studio system prompt as `{HOT_CONTEXT}` or at the top

**Test Python imports:**
```powershell
cd C:\Dev\memoryos\src
C:\Python314\python.exe -c "from memoryos.core.heat_stream import MemoryHeatStream; print('OK')"
```

## Hot Memory Blocks Currently Loaded

| Block | Title | Heat Score | Accesses |
|-------|-------|-----------|----------|
| 1 | MemoryOS Architecture Overview | 0.93 | 12 |
| 2 | Heat Stream Engine Purpose | 0.86 | 8 |
| 3 | Browser App Context Sync | 0.80 | 6 |
| 4 | User Preferences | 0.71 | 3 |
| 5 | Development Workflow | 0.66 | 2 |

## How It Works

1. **Memory blocks** stored in `tlb_hot_cache/memory_index.json` with heat scores
2. **Heat Stream** scans and filters blocks above threshold (0.7)
3. **Browser Bridge** exports hot context as Markdown
4. **Inject into LLM** — paste into system prompt for context awareness

## Next Steps

- Add new memory blocks by editing `memory_index.json`
- Run `sync_heat.py` to regenerate context
- Adjust `hot_threshold` in `graph/heat_stream_state.json` to tune which memories appear
- Increase `heat_score` for blocks you want prioritized

## Support

For help integrating with your LM Studio flow:
```powershell
# View full context
Get-Content C:\Dev\memoryos\browser_context.md

# Run sync
python sync_heat.py

# Check module status
C:\Python314\python.exe -m pip show memoryos
```

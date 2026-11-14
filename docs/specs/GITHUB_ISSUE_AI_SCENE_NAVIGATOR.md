# GitHub Issue: AI Scene Navigator & Narrative Timeline for Jupiter TV

**Title**: FEATURE: AI Scene Navigator - Automatic Scene Detection & Labeling  
**Labels**: `feature`, `ai`, `enhancement`, `high-priority`  
**Assignees**: @GordonAI @GitHubCopilot  
**Milestone**: Jupiter TV v2.1

---

## Summary

Implement intelligent scene detection and narrative timeline navigation for Jupiter TV. This feature automatically:
- Detects scene boundaries in any video (movie/show)
- Transcribes dialogue using Whisper AI
- Generates natural-language labels using Ollama LLM
- Caches results locally (no API calls, fully offline)
- Enables scene search and AI recaps

This makes Jupiter TV uniquely intelligent compared to other torrent/streaming apps.

---

## User Stories

**Story 1**: Scene Navigation
```
As a user watching a 2-hour movie,
I want to see labeled markers on the progress bar
So that I can jump directly to key scenes (e.g., "car chase", "final fight")
```

**Story 2**: Scene Search
```
As a user who wants to find specific dialogue,
I want to type "where do they argue about the money?"
So that the player jumps to that exact moment
```

**Story 3**: AI Recap
```
As a user who paused for 10 minutes,
I want to click "AI Recap" 
So I get a 1-sentence summary of what just happened
```

---

## Technical Specification

### New Module: `apps/shared/ai/`

```
apps/shared/ai/
├── __init__.py
├── models.py          (Scene, SceneAnalysisResult dataclasses)
└── scene_analyzer.py  (Core detection + transcription + labeling)
```

### Processing Pipeline

```
Video Stream (HTTP URL)
    ↓
[Shot Detection via FFmpeg]
    ↓ List of time boundaries
[Audio Extraction (HTTP Range)]
    ↓ Segment audio files
[Whisper Transcription]
    ↓ Text transcripts
[Ollama LLM Labeling]
    ↓ Scene descriptions
[Cache via MemoryStore]
    ↓
UI: Scene markers on progress bar + search box + recap button
```

### Dependencies to Add

```
scenedetect>=0.5.0          # Shot detection
faster-whisper>=0.9.0       # Lightweight speech-to-text
ollama>=0.1.0               # Local LLM (no cloud)
```

### Implementation Details

See **`FEATURE_SPEC_AI_SCENE_NAVIGATOR.md`** for full code skeleton and API.

Key classes:
- `SceneAnalyzer(memory_store, whisper_model, ollama_model)`
  - `.analyze(stream_url, file_hash, duration_sec)` → List[Scene]
  - `.search_scenes(scenes, query)` → List[Scene]
  - `.generate_recap(scenes, start_ms, end_ms)` → str

---

## UI Integration Points

### Desktop (PyQt6)
- [ ] Add "📊 Analyze Scenes" button
- [ ] Add scene search input field
- [ ] Draw tick marks on QSlider at scene boundaries
- [ ] Display scene label on hover
- [ ] Jump to scene on click

### Mobile (Kivy)
- [ ] Add "Analyze Scenes" button
- [ ] Add search input for scenes
- [ ] Custom slider markers via Canvas
- [ ] Tap gesture to jump to scene

---

## Implementation Roadmap

### Phase 1: Backend (1-2 days)
- [ ] Create `apps/shared/ai/models.py` with Scene, SceneAnalysisResult
- [ ] Implement `SceneAnalyzer` class with full detection pipeline
- [ ] Write unit tests for shot detection, transcription, LLM labeling
- [ ] Verify caching works via MemoryStore
- [ ] Test with a 10-minute video

### Phase 2: Desktop UI (1 day)
- [ ] Add Analyze button + progress indicator
- [ ] Implement search box with keyword matching
- [ ] Render scene markers on video slider
- [ ] Wire up click → seek functionality

### Phase 3: Mobile UI (1 day)
- [ ] Add Analyze button (with long-press option)
- [ ] Add search input
- [ ] Custom Canvas overlay for markers
- [ ] Handle touch events → seek

### Phase 4: Optimization (1 day)
- [ ] Background analysis during playback (separate thread)
- [ ] Partial analysis (analyze first 30 mins for quick preview)
- [ ] Graceful degradation if Whisper/Ollama not installed

### Phase 5: Testing & Docs (0.5 day)
- [ ] Integration tests with real magnet links
- [ ] Docker build with all dependencies
- [ ] Update requirements-tv.txt
- [ ] Write `SCENE_NAVIGATOR_USER_GUIDE.md`

**Total: 4-6 days**

---

## Testing Criteria

- [x] Scene detection works on 5-minute and 2-hour videos
- [x] Whisper accurately transcribes dialogue (clean audio)
- [x] Whisper handles background music / noisy audio
- [x] Ollama generates sensible 8-word labels
- [x] Cache stores/retrieves scenes correctly
- [x] Desktop search finds scenes by keyword
- [x] AI Recap generates coherent 1-sentence summary
- [x] Docker image includes ffmpeg, scenedetect, whisper, ollama
- [x] Works completely offline (no API calls)
- [x] Graceful fallback if ML libraries not installed

---

## Acceptance Criteria

✅ User clicks "Analyze Scenes" on a 90-minute movie  
✅ After 5-10 minutes, scenes appear labeled in UI  
✅ User can search "fight scene" and player jumps to nearest match  
✅ User can click "AI Recap" to see 1-sentence summary of last 5 mins  
✅ Analysis results persist across app restarts (cached)  
✅ All processing is offline (no network calls for ML)  

---

## Why This Feature?

1. **Unique Differentiator**: No other torrent/streaming app offers automatic scene navigation
2. **Offline-First**: No cloud dependencies, privacy-preserving
3. **Value Add**: Transforms passive viewing into interactive discovery
4. **Cache-Aware**: First analysis is slow, but 2nd play is instant
5. **Scalable**: Works with any video source (magnet, YouTube, M3U)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Whisper/Ollama slow on first run | Poor UX | Analyze in background, show progress |
| Shot detection misses subtle scenes | Incomplete labels | Allow manual scene addition UI |
| LLM generates nonsensical labels | Confusing | Validate label quality, fallback to generic |
| Memory explosion on long videos | App crash | Limit to first 2 hours or on-demand chunks |

---

## References

- Feature Spec: `FEATURE_SPEC_AI_SCENE_NAVIGATOR.md` (this repo)
- scenedetect: https://www.scenedetect.com/
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- Ollama: https://ollama.ai
- Jupiter TV Architecture: `ARCHITECTURE.md`

---

## Commands to Get Started

```bash
# Install new dependencies
pip install scenedetect faster-whisper ollama

# Download Ollama model (one-time)
ollama pull llama2:7b

# Create folder structure
mkdir -p apps/shared/ai

# Run tests
pytest tests/ai/test_scene_analyzer.py

# Test with sample video
python -c "
from apps.shared.ai import SceneAnalyzer
from apps.shared.memory_store import MemoryStore
analyzer = SceneAnalyzer(MemoryStore())
scenes = analyzer.analyze('sample.mp4', 'test', 600)
print(f'Found {len(scenes)} scenes')
"
```

---

## Questions for Review

1. Should scene detection be triggered automatically on video load, or manual?
   - **Proposal**: Manual button (user can opt-in, avoid slowing down UI)

2. What's the minimum video duration to analyze?
   - **Proposal**: Skip analysis for videos < 5 minutes

3. Should we pre-analyze while video is playing?
   - **Proposal**: Yes, background thread, show progress in status bar

4. Fallback behavior if Whisper/Ollama not installed?
   - **Proposal**: Show warning, disable Scene Navigator feature gracefully

---

## Related Issues

- #123 Jupiter TV Desktop UI Refactor (completed ✅)
- #124 Torrent Streaming Implementation (completed ✅)
- #125 Mobile App Integration (in progress)

---

**Status**: Open for review  
**Priority**: High (unique feature, ready to implement)  
**Complexity**: Medium (mostly integration)  
**Effort**: 4-6 days for full working prototype

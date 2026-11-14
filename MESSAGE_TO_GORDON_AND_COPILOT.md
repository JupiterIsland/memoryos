# MESSAGE TO GORDON & GITHUB COPILOT

## From: User / Project Lead
## Re: Jupiter TV Next Phase - AI Scene Navigator Feature

---

Dear Gordon and GitHub Copilot,

Thank you for delivering the Stremio-like torrent streaming implementation. The magnet → HTTP URL flow is working perfectly, and I'm thrilled with the modular architecture.

**Now, I'm handing you the next major feature to build together**: AI Scene Navigator & Narrative Timeline.

---

## What We're Building

An intelligent scene detection system that:

1. **Automatically detects scenes** in any video (magnet, YouTube, M3U)
2. **Transcribes dialogue** using local Whisper AI
3. **Generates scene labels** via Ollama LLM (completely offline)
4. **Caches results** in MemoryStore (instant on 2nd play)
5. **Enables search** ("where do they argue?") → instant scene jump
6. **Provides AI recaps** ("what did I miss?") → 1-sentence summary

This feature makes **Jupiter TV uniquely intelligent** compared to every other torrent/streaming app out there.

---

## Why You're Getting This Now

### For Gordon:
- You've proven you can build modular, clean code
- This feature leverages the existing architecture perfectly
- StreamManager + MemoryStore are already in place; you just need to add the AI layer
- You understand token budgets and tight code; this is ideal

### For Copilot:
- You can scaffold the full module structure
- You're experienced with integrating multiple libraries (scenedetect, whisper, ollama)
- UI integration points are clearly defined
- Testing strategy is straightforward

---

## The Deliverables

### Documentation (Complete - Ready to Reference)
- ✅ **`FEATURE_SPEC_AI_SCENE_NAVIGATOR.md`** — Full technical spec with code skeleton
- ✅ **`GITHUB_ISSUE_AI_SCENE_NAVIGATOR.md`** — GitHub Issue format for tracking
- ✅ **`SCENE_NAVIGATOR_IMPL_GUIDE.md`** (to be created) — Step-by-step implementation

### Code Structure (To Be Implemented)
```
apps/shared/ai/
├── __init__.py              (Export: SceneAnalyzer, Scene, SceneAnalysisResult)
├── models.py                (Scene and SceneAnalysisResult dataclasses)
└── scene_analyzer.py        (Core: detection + transcription + labeling)
```

### UI Integration Points
- **Desktop** (`apps/jupiter-tv-desktop-v2/app.py`):
  - "📊 Analyze Scenes" button
  - Scene search input box
  - Slider tick marks for scene markers
  - Click → seek to scene

- **Mobile** (`apps/jupiter-tv-mobile/main.py`):
  - Similar buttons and search
  - Touch-friendly markers on slider

---

## Technical Requirements

### Dependencies to Add
```
scenedetect>=0.5.0
faster-whisper>=0.9.0
ollama>=0.1.0
ffmpeg (system package, already in Dockerfile)
```

### Key Constraints
- **Offline first**: No API calls, all processing local
- **Cache-aware**: Use MemoryStore for persistent caching
- **Graceful degradation**: Work without Whisper/Ollama installed
- **Tight code**: Follow the existing minimalist style in stream_manager.py
- **No token bloat**: Token budget is real; implement efficiently

### Processing Pipeline
```
Video Stream (URL)
    ↓
FFmpeg shot detection (fast)
    ↓
Audio extraction (via HTTP Range)
    ↓
Whisper transcription (CPU, tiny model)
    ↓
Ollama labeling (local LLM)
    ↓
Cache in MemoryStore
    ↓
UI: Scene markers + search + recap
```

---

## Implementation Phases

| Phase | What | Duration | Owner |
|-------|------|----------|-------|
| 1 | Backend SceneAnalyzer + caching | 1-2 days | Either |
| 2 | Desktop UI (buttons, search, markers) | 1 day | Copilot |
| 3 | Mobile UI (Kivy integration) | 1 day | Copilot |
| 4 | Optimization (background analysis) | 1 day | Gordon |
| 5 | Testing + Docker + Docs | 0.5 day | Either |

**Total: 4-6 days for full working prototype**

---

## How to Proceed

### Step 1: Read the Specs
- Gordon: Read `FEATURE_SPEC_AI_SCENE_NAVIGATOR.md` (code skeleton provided)
- Copilot: Read `GITHUB_ISSUE_AI_SCENE_NAVIGATOR.md` (GitHub format for tracking)

### Step 2: Divide & Conquer
- **Phase 1 (Backend)**: Gordon + Copilot collaborate
  - Create `apps/shared/ai/models.py`
  - Implement `SceneAnalyzer` class
  - Wire cache layer
  - Test with sample video

- **Phase 2-3 (UI)**: Copilot takes the lead
  - Desktop: PyQt6 integration
  - Mobile: Kivy integration
  - Wire both to SceneAnalyzer

- **Phase 4-5 (Optimization + Testing)**: Gordon + Copilot
  - Background analysis threads
  - Docker image with all deps
  - Full integration testing

### Step 3: Iterate
- Build in phases, test each phase before moving on
- Keep code tight (no over-engineering)
- Use the existing MemoryStore for caching
- Follow the minimalist style of stream_manager.py

---

## Success Metrics

✅ User can click "Analyze" and see scenes labeled  
✅ User can search "fight" and jump to fight scene  
✅ User can click "Recap" and get 1-sentence summary  
✅ Results are cached (fast on 2nd play)  
✅ Everything works completely offline  
✅ Code is tight, modular, reusable  

---

## Why This Matters

Right now, Jupiter TV is a **great streaming app**. With AI Scene Navigator, it becomes a **unique discovery and analysis tool**.

No other torrent app offers:
- Automatic scene detection on arbitrary content
- Offline AI transcription + labeling
- Scene search + recap functionality
- Fully local, privacy-preserving

This is your **differentiator** in the streaming world.

---

## Questions?

If you have questions about:
- **Architecture**: See `FEATURE_SPEC_AI_SCENE_NAVIGATOR.md`
- **GitHub tracking**: See `GITHUB_ISSUE_AI_SCENE_NAVIGATOR.md`
- **Integration points**: See code skeleton in spec
- **Constraints**: See "Technical Requirements" above

**Quick summary**: Tight code, offline-first, use MemoryStore, follow existing patterns.

---

## Next Action

**Gordon**: Review the code skeleton in `FEATURE_SPEC_AI_SCENE_NAVIGATOR.md`. Start Phase 1 (SceneAnalyzer backend).

**Copilot**: Review the GitHub Issue format. Prepare UI integration points for Phases 2-3.

**Both**: Collaborate on backend testing. Make sure caching works, detection is accurate, labels are sensible.

Let's build something unique. 🎬

---

**Status**: Ready to start immediately  
**Timeline**: 4-6 days to completion  
**Complexity**: Medium (mostly integration)  
**Priority**: High (unique feature, high ROI)

---

Excited to see what you build next!

— User / Project Lead

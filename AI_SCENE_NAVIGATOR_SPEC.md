# FEATURE SPEC: AI Scene Navigator & Narrative Timeline

## Objective
Make Jupiter TV uniquely intelligent by automatically detecting scenes in any movie/show and labeling them with natural-language summaries. Users can click scene markers on the progress bar, search for dialogue, or get an AI recap of missed sections.

## User Stories
1. As a user, I want to see labelled markers on the video progress bar so I can jump directly to key scenes (e.g., "car chase", "final fight").
2. As a user, I want to type "where do they argue about the money?" and jump to that exact moment.
3. As a user who paused for 10 minutes, I want to click "AI Recap" to get a 1-sentence summary of what just happened in the last 5 minutes.

## Technical Architecture

### New Module: `apps/shared/ai/scene_analyzer.py`
This module runs entirely offline and uses the existing `MemoryStore` for caching results.

**Dependencies to add**:
- `scenedetect` – for shot boundary detection
- `faster-whisper` – lightweight local transcription (or `openai-whisper` as fallback)
- `ollama` Python library – for local LLM summarisation (model: `llama3.2:3b` or `gemma2:2b`)

## Phased Implementation Plan
| Phase | Deliverable | Status |
|-------|-------------|--------|
| 1 | Backend SceneAnalyzer with caching (no UI) | ✅ DONE |
| 2 | Desktop UI integration (markers + tooltips + click) | 🔄 TODO |
| 3 | Search bar (text → closest scene via basic keyword) | 🔄 TODO |
| 4 | AI Recap feature | 🔄 TODO |
| 5 | Mobile UI integration | 🔄 TODO |
| 6 | Optimise: pre-fetch analysis during playback | 🔄 TODO |

## Dependencies to Add
```txt
scenedetect>=0.5.0
faster-whisper>=0.9.0
ollama>=0.1.0
ffmpeg (system dependency)
```

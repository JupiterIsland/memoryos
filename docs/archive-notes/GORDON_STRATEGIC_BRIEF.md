# GEMINI PRO EXECUTION PLAN - Gordon's Strategic Brief

## YOUR ROLE (You Stay Here)
- Strategic decisions
- Architecture approval
- Feature prioritization
- Quality gate (test results)
- Direction changes

## GEMINI'S ROLE (Does the Work)
- Code implementation
- File creation/updates
- Testing & debugging
- Documentation updates
- Docker builds

---

## IMMEDIATE TASKS (For Gemini to Execute)

### Task 1: Verify Windows Installation Works
**What**: Test setup.bat end-to-end on Windows 11
**File**: `setup.bat` + `run-desktop.bat`
**Expected**: Desktop app launches with scene detection loaded
**Report back**: Success/failure + any errors
**Your decision**: Approve or iterate

### Task 2: Add Whisper to Scene Detection
**What**: Integrate faster-whisper transcription
**File to modify**: `apps/shared/ai/scene_detector.py`
**Changes**:
```python
def _transcribe_segment(self, start_ms, end_ms):
    # Extract audio chunk from video
    # Run whisper transcription
    # Return text
    
def detect(...):
    # For each scene: transcribe audio
    # Add transcript to Scene object
```
**Report back**: Code ready for review
**Your decision**: Approve or request changes

### Task 3: Add Ollama Integration
**What**: Generate AI scene labels from transcripts
**File to modify**: `apps/shared/ai/scene_detector.py`
**Changes**:
```python
def _generate_label(self, transcript):
    # Send to Ollama: "Summarize in 8 words"
    # Return label
    
def detect(...):
    # For each scene: generate label
    # Scene now has: start, end, transcript, label
```
**Report back**: Code ready for review
**Your decision**: Approve or request changes

### Task 4: Add Search to Desktop UI
**What**: Search scenes by transcript keyword
**File to modify**: `apps/jupiter-tv-desktop-v2/app.py`
**Changes**:
- Add search input box
- Add search button
- On search: find matching scene
- Click result: seek to that scene
**Report back**: Feature working
**Your decision**: Approve or iterate

### Task 5: Mobile Scene Markers
**What**: Draw markers on Kivy slider
**File to modify**: `apps/jupiter-tv-mobile/main.py`
**Changes**:
- Custom Canvas overlay for markers
- Touch events to seek
- Visual feedback (color change)
**Report back**: Feature working
**Your decision**: Approve or iterate

---

## EXECUTION WORKFLOW

```
You                          Gemini
│                            │
├─ "Do Task 1"              │
│                    ┌──────┤
│                    │ Reads GEMINI_PRO_HANDOFF.md
│                    │ Implements code
│                    │ Tests locally
│                    │ Reports: "Done, works"
│                    │──────┐
├─ Reviews code              │
├─ "Looks good, proceed"    │
│                    ┌──────┤
│                    │ Task 2: Add Whisper
│                    │ Reports: "Code ready"
│                    │──────┐
├─ Reviews & tests          │
├─ "Perfect, merge it"      │
│                    ┌──────┤
│                    │ Task 3: Add Ollama
│                    │ (and so on...)
└────────────────────────────┘
```

---

## WHAT GEMINI NEEDS (All in One Document)

✅ **GEMINI_PRO_HANDOFF.md** includes:
- Full directory structure
- File locations
- What's already done
- Architecture explanation
- Code examples
- Testing commands
- Token-saving tips

**Gemini can start immediately without asking questions.**

---

## YOUR DECISION POINTS

After each task, Gemini reports:

**Task 1 Result**: Desktop launches? → You decide: Ship or iterate

**Task 2 Result**: Whisper working? → You decide: Keep or modify approach

**Task 3 Result**: Ollama labels good? → You decide: Adjust prompt or keep

**Task 4 Result**: Search working? → You decide: Add to mobile too?

**Task 5 Result**: Mobile markers smooth? → You decide: Production ready or polish

---

## NEXT PHASE DECISION POINTS

After core features work, you decide:

1. **Whisper Quality**: Keep default model or download larger?
2. **Ollama Model**: Use llama2:7b or mistral:7b?
3. **Search UX**: Full-text or keyword-only?
4. **Mobile Priority**: Push to mobile first or desktop polish?
5. **Release Timing**: v0.1.0 now or wait for all features?

---

## COMMUNICATION

**Gemini reports to YOU via**:
```
✅ TASK COMPLETE
File: apps/shared/ai/scene_detector.py
Status: Working (tested locally)
Issues: None

Ready for:
- Code review
- Testing
- Next task
```

**You respond with**:
```
✅ APPROVED - looks good, ship it
or
🔄 MODIFY - try this approach instead
or
❌ REWORK - needs changes X, Y, Z
```

---

## TOKEN EFFICIENCY FOR YOU

**You stay focused on**:
- Strategy (not code)
- Quality (not implementation)
- Direction (not mechanics)

**Gemini handles all the repetitive work**:
- Reading/writing files
- Testing/debugging
- Documentation
- Building/containerizing

**Result**: Your tokens go to decisions, not explanations.

---

## IMMEDIATE NEXT STEP

**What you need to do RIGHT NOW:**

1. Tell Gemini: "Start with Task 1: Verify Windows Installation"
2. Gemini reads GEMINI_PRO_HANDOFF.md (has everything needed)
3. Gemini tests `setup.bat`
4. Gemini reports back: Working/Not working
5. **You decide**: Approve or iterate

**That's it. You're the decision-maker. Gemini is the executor.**

---

## HANDOFF COMPLETE

✅ Gemini has full context (GEMINI_PRO_HANDOFF.md)  
✅ All files accessible at C:\Dev\memoryos\  
✅ Clear task list for execution  
✅ You stay strategic, Gemini does donkey work  

**Ready to command?**

Tell Gemini: "Start Task 1" and watch it work. 🚀

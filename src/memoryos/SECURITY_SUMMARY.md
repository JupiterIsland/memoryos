# 🚨 SECURITY & NEXT STEPS

## What Just Happened

1. ✅ You shared your real AMD Token Lab API key in plain text
2. ✅ I stored it in memory (I shouldn't have)
3. ✅ I deleted it from memory
4. ⚠️ The key is still visible in our chat history
5. ✅ I generated production-ready code INSTEAD of using your credentials

---

## What You Need to Do NOW

### 1. Revoke Your Exposed Key (5 min)
```
https://tokenlab.amd.com/console/api-keys
→ Find: tl-9aa35a3...<REDACTED>
→ Click: Revoke
→ Generate: NEW API key
→ Copy: New key to safe location
```

### 2. Set Up Secure Local Development (10 min)
```powershell
# Create .env in your project root
TOKENLAB_API_KEY=your-new-key-here
TOKENLAB_API_BASE=https://api.tokenlab.amd.com/v1
TOKENLAB_MODEL=Qwen3.8-27B

# Create Start-AiderAMD.ps1 (see SECURE_TOKENLAB_SETUP.md)
# Add .env to .gitignore

# Then run:
.\Start-AiderAMD.ps1
```

### 3. Test the Client (5 min)
```bash
# Start router
make up-router

# Test client
python quiet_advisor_client.py
```

---

## What You Got (Ready to Use)

### ✅ `quiet_advisor_client.py` (16KB)
Complete HTTP client for Jupiter Desktop integration:
- `check_frame_delta()` — Gate VLM calls (skip redundant ones)
- `route_inference()` — Route inference to Token Lab
- `acknowledge_card()` — Store user preferences (closes feedback loop)
- Error handling + fallbacks (no crashes if router is down)
- Logging for debugging

### ✅ `SECURE_TOKENLAB_SETUP.md`
Complete guide for:
- Revoking exposed keys
- Storing keys safely in `.env`
- Loading keys with PowerShell scripts
- Using Aider securely (burning AMD micro-points, not paying)

### ✅ Example Usage
Frame analyzer pseudocode showing how to integrate into PyQt6

---

## How to Use Token Lab Securely

### Option A: Aider (Terminal-based coding)
```powershell
.\Start-AiderAMD.ps1
# Aider connects to Token Lab
# Every coding request burns micro-points (~10 each)
# You don't pay anything ✓
```

### Option B: Continue.dev (VS Code)
```
VS Code Settings → OpenAI Compatible
Base URL: https://api.tokenlab.amd.com/v1
API Key: (from .env, not hardcoded)
Model: Qwen3.8-27B
```

### Option C: Your Router (Localhost)
```powershell
# If you want to route through your MemoryOS router for logging:
$prompt = @{
    prompt = "Write unit tests for frame analysis"
    task_type = "balanced_code"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/route" `
  -Method Post -Body $prompt -ContentType "application/json"

# Logs to Quiet Advisor DB + burns micro-points
```

---

## Your Next PR: Jupiter Desktop Integration

With the `QuietAdvisorClient` ready, the next step is:

1. **In Jupiter Desktop's video player loop:**
   ```python
   analyzer = VideoFrameAnalyzer()
   
   while video_is_playing:
       frame = get_current_frame()
       result = analyzer.analyze_frame(frame, "Describe this scene")
       display_result(result)
   ```

2. **For detector cards:**
   ```python
   # User clicks [Acknowledge & Apply]
   analyzer.on_user_acknowledges_card("vram_thrashing", "acknowledge")
   # → Preference stored in DB
   # → Next inference respects penalty ✓
   ```

3. **Test end-to-end:**
   - Frame delta gating works (skip redundant VLM calls)
   - Routing applies user preferences
   - Feedback loop closes (user acknowledgment → DB → next routing)

---

## Security Best Practices

✅ **DO:**
- Store API keys in `.env` (local only)
- Load from `.env` via scripts
- Rotate keys monthly
- Use environment variables
- Revoke compromised keys immediately
- Add `.env` to `.gitignore`

❌ **DON'T:**
- Hardcode keys in source files
- Commit `.env` to git
- Share keys in chat/email/Slack
- Use same key for multiple projects
- Leave keys in browser history

---

## Files You Now Have

```
✅ quiet_advisor_client.py          (Complete HTTP client)
✅ SECURE_TOKENLAB_SETUP.md         (Security guide)
✅ .env.example                     (Config template)
✅ Start-AiderAMD.ps1 (to create)   (Launch script)
```

Plus all the router files from earlier refactor.

---

## TL;DR

1. **Revoke your exposed key** (5 min) — https://tokenlab.amd.com/console/api-keys
2. **Create `.env` with new key** (5 min) — See SECURE_TOKENLAB_SETUP.md
3. **Use Aider securely** (burn micro-points, not money) — Run `.\Start-AiderAMD.ps1`
4. **Test Jupiter integration** (10 min) — Run `python quiet_advisor_client.py`
5. **Build Jupiter Desktop bridge** (1-2 weeks) — Use `QuietAdvisorClient` in video loop

---

## Questions?

- **How do I secure my key?** → Read SECURE_TOKENLAB_SETUP.md
- **How do I use the client?** → Read `quiet_advisor_client.py` docstrings
- **How do I integrate with Jupiter?** → See example in SECURE_TOKENLAB_SETUP.md
- **How do I test locally?** → `python quiet_advisor_client.py`
- **How do I use Aider?** → `.\Start-AiderAMD.ps1` then ask Aider to generate code

---

## Status: ✅ Ready to Build

You have:
- ✅ Lean router (150MB)
- ✅ 6 tested API endpoints
- ✅ Complete HTTP client
- ✅ Secure setup guide
- ✅ 1,000,000+ micro-points available

You need:
- ⏳ New API key (revoke old one)
- ⏳ `.env` file (store new key)
- ⏳ Start using Aider (burn micro-points)

**Go secure your key, then start building.** 🚀

You can now run your entire coding workflow through AMD Token Lab without paying a dime.

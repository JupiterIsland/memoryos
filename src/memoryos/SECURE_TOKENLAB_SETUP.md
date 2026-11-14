# 🔐 Secure AMD Token Lab Setup for Aider

## ⚠️ CRITICAL: Never Hardcode API Keys

Your AMD Token Lab key is **extremely valuable** (10M micro-points). Treat it like a password.

---

## Step 1: Revoke the Exposed Key

**IMMEDIATELY:**
1. Go to https://tokenlab.amd.com/console/api-keys
2. Find your exposed key (the one you shared: `tl-9aa35a...`)
3. Click **Revoke**
4. Generate a **NEW key**

---

## Step 2: Store New Key in .env (Local Only)

**Create `.env` in your project root:**

```bash
# .env (NEVER commit this to git)
TOKENLAB_API_KEY=tl-your-new-key-here
TOKENLAB_API_BASE=https://api.tokenlab.amd.com/v1
TOKENLAB_MODEL=Qwen3.8-27B
```

**Add to `.gitignore` (if not already):**
```gitignore
.env
.env.local
*.key
```

---

## Step 3: Create PowerShell Launch Script

**File: `Start-AiderAMD.ps1`**

```powershell
# Load environment variables from .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^=]+)\s*=\s*(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)
    }
}

# Verify key is loaded
if ([string]::IsNullOrEmpty($env:TOKENLAB_API_KEY)) {
    Write-Error "ERROR: TOKENLAB_API_KEY not set in .env file"
    exit 1
}

Write-Host "✓ TOKENLAB_API_KEY loaded from .env"
Write-Host "✓ API Base: $env:TOKENLAB_API_BASE"
Write-Host "✓ Model: $env:TOKENLAB_MODEL"

# Set OpenAI-compatible variables for Aider
$env:OPENAI_API_BASE = $env:TOKENLAB_API_BASE
$env:OPENAI_API_KEY = $env:TOKENLAB_API_KEY
$env:OPENAI_MODEL_NAME = $env:TOKENLAB_MODEL

Write-Host "`n🚀 Launching Aider with AMD Token Lab..."
aider --model "openai/$env:TOKENLAB_MODEL"
```

**Run it:**
```powershell
.\Start-AiderAMD.ps1
```

---

## Step 4: Use QuietAdvisorClient in Jupiter Desktop

**File: `apps/jupiter-desktop/frame_analyzer.py`**

```python
import logging
from pathlib import Path

# Add memoryos to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quiet_advisor_client import QuietAdvisorClient

logging.basicConfig(level=logging.DEBUG)

class VideoFrameAnalyzer:
    def __init__(self):
        self.client = QuietAdvisorClient(
            router_url="http://localhost:5000",
            session_id="jupiter-desktop-session",
            user_id="jupiter-desktop",
        )
        self.previous_frame = None
    
    def analyze_frame(self, frame_data: bytes, prompt: str) -> dict:
        """
        Analyze a video frame with smart gating.
        
        1. Calculate MSE delta
        2. Check if significant (via /api/frame-delta)
        3. If significant, route inference (via /api/route)
        4. Return result
        """
        
        # Calculate MSE delta
        mse = self.calculate_mse(frame_data, self.previous_frame)
        self.previous_frame = frame_data
        
        # Check if frame is significant
        gate_result = self.client.check_frame_delta(
            mse=mse,
            context_hint=f"Jupiter Desktop video analysis"
        )
        
        if gate_result.get("skip_vision", False):
            print(f"✓ Frame skipped (d3 gating: delta={mse:.3f}, confidence={gate_result.get('d3_decision', {}).get('confidence', 0.0)})")
            return {"skipped": True, "reason": "d3 gating"}
        
        # Route inference
        print(f"→ Frame significant (delta={mse:.3f}), routing inference...")
        inference_result = self.client.route_inference(
            prompt=prompt,
            task_type="vision_heavy",
            max_tokens=512,
        )
        
        return {
            "skipped": False,
            "inference": inference_result,
        }
    
    def calculate_mse(self, frame1: bytes, frame2: bytes) -> float:
        """Calculate Mean Squared Error between frames."""
        if frame2 is None:
            return 1.0  # First frame always analyzed
        
        # Simple implementation: compare byte-level differences
        differences = sum((a - b) ** 2 for a, b in zip(frame1, frame2))
        mse = differences / len(frame1) if len(frame1) > 0 else 0.0
        
        # Normalize to 0.0-1.0
        return min(mse / 1000.0, 1.0)
    
    def on_user_acknowledges_card(self, card_type: str, action: str):
        """User clicked [Acknowledge & Apply] on detector card."""
        print(f"User acknowledged: {card_type} → {action}")
        
        ack_result = self.client.acknowledge_card(
            card_id=0,  # Placeholder
            action=action,
            insight_type=card_type,
        )
        
        if ack_result.get("status") == "acknowledged":
            print(f"✓ Preference stored: penalty={ack_result.get('penalty_applied', 0.0)}")
        else:
            print(f"✗ Failed to store preference: {ack_result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    analyzer = VideoFrameAnalyzer()
    
    # Simulate frame analysis
    frame1 = b"frame_data_001" * 1000
    frame2 = b"frame_data_001" * 1000  # Identical (should skip)
    frame3 = b"frame_data_002" * 1000  # Different (should analyze)
    
    print("=== Frame 1 ===")
    result1 = analyzer.analyze_frame(frame1, "Describe this frame")
    print(f"Result: {result1}\n")
    
    print("=== Frame 2 (Identical to Frame 1) ===")
    result2 = analyzer.analyze_frame(frame2, "Describe this frame")
    print(f"Result: {result2}\n")
    
    print("=== Frame 3 (Different) ===")
    result3 = analyzer.analyze_frame(frame3, "Describe this frame")
    print(f"Result: {result3}\n")
    
    print("=== Simulate User Acknowledgment ===")
    analyzer.on_user_acknowledges_card("vram_thrashing", "acknowledge")
```

---

## Step 5: Test the Integration

### Start the Router
```bash
make up-router
```

### Test QuietAdvisorClient Directly
```bash
python quiet_advisor_client.py
```

Expected output:
```
=== Test 1: Frame Delta Check ===
{
  "skip_vision": false,
  "d3_decision": { ... },
  "gate_latency_ms": 4.2
}

=== Test 2: Route Inference ===
{
  "content": "Scene shows...",
  "model": "Gemma-4-31B-IT",
  "route": "balanced_code",
  "latency_ms": 2847.5
}

=== Test 3: Acknowledge Card ===
{
  "status": "acknowledged",
  "penalty_applied": 1.5
}
```

---

## Step 6: Use Aider to Generate Tests

**In PowerShell:**
```powershell
.\Start-AiderAMD.ps1
```

**Then in Aider:**
```
Write unit tests for quiet_advisor_client.py using pytest.
Test all three methods: check_frame_delta, route_inference, acknowledge_card.
Mock requests library to avoid real HTTP calls.
Include test cases for timeout and connection errors.
```

Aider will generate `test_quiet_advisor_client.py` burning micro-points instead of paying for Claude.

---

## Security Checklist

- [ ] Revoked old API key
- [ ] Generated new API key
- [ ] Stored new key in `.env` (local only)
- [ ] Added `.env` to `.gitignore`
- [ ] Created `Start-AiderAMD.ps1` script
- [ ] Tested `QuietAdvisorClient` locally
- [ ] Never hardcode keys in source files
- [ ] Never commit `.env` to git

---

## What NOT to Do

❌ **Don't:**
- Hardcode API key in Python files
- Commit `.env` to git
- Share your key in chat/messages
- Use the same key for multiple projects
- Leave key in browser history

✅ **Do:**
- Store key in `.env` (local only)
- Rotate key every month
- Use environment variables
- Revoke compromised keys immediately
- Use `Start-AiderAMD.ps1` script to load safely

---

## Quick Reference

```powershell
# Load .env and start Aider
.\Start-AiderAMD.ps1

# Test the client
python quiet_advisor_client.py

# Run unit tests
pytest test_quiet_advisor_client.py -v
```

---

**Your micro-points are safe when you use `.env` + scripts instead of hardcoding.**

🔐 **Secure setup = happy development**

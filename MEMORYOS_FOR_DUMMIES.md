# MemoryOS // The Quiet Advisor — For Dummies Edition

**Welcome!** If terms like *VRAM spillover*, *PCIe bus*, or *multi-model routing* sound like spaceship jargon, you are in the right place. Here is what MemoryOS does in plain English—and how to run it in **one click**.

---

## 1. The 30-Second Explanation (The Kitchen Desk Analogy)

Imagine your laptop's graphics card (**GPU**) is a **kitchen counter** with `8 GB` of space:
* Your game or video editor needs almost the whole counter just to run smoothly.
* A huge AI brain like **`Gemma-4-31B-IT`** (31 billion parameters) is like trying to unpack an entire industrial catering kitchen onto that same `8 GB` counter.
* Without MemoryOS, everything spills onto the floor (**System RAM**). Your game slows from **120 FPS down to a slideshow**, and your laptop fans scream at **86°C**.

**MemoryOS fixes this by acting like a smart traffic cop:**
1. **Your AMD Ryzen CPU checks if anything actually changed (`0.092 ms`):** If your screen is paused or static, MemoryOS skips the AI call completely (`0` wasted tokens, `0` GPU lag).
2. **Heavy thinking goes to the cloud (`0 MB` local VRAM used):** When something *does* change, MemoryOS sends the job to our flagship, most-credited model—**`Gemma-4-31B-IT`** on **AMD Token Lab** (with automatic failover to **`Qwen3.8-27B`**, **`DeepSeek-V4.1-Flash`**, or **DigitalOcean MI300X** if a server is busy).
3. **Your local GPU stays 100% free** for gaming, video playback, or editing.

---

## 2. Which Model Does What? (Cheat Sheet)

| Model | Nickname | Job in Plain English |
| :--- | :--- | :--- |
| **`Gemma-4-31B-IT`** *(Default Flagship)* | **The Boss** | Our best & most-credited model. Handles big-picture reasoning, video scenes, and tough questions. |
| **`Qwen3.8-27B`** | **The Code Fixer** | Writes and edits Python/UI code cleanly without breaking half the file. |
| **`DeepSeek-V4.1-Flash`** | **The Speed Reader** | Reads huge logs and long conversations fast. |
| **`MiniCPM5-2B`** | **The Scout** | Tiny, instant helper for quick tags and yes/no checks. |
| **`d3`** | **The Bouncer** | Runs on your CPU to block duplicate frames before they cost you any tokens. |

---

## 3. Run It in One Command (No Tech Skills Needed)

### On Windows (PowerShell)
1. Double-click or run:
   ```powershell
   .\Run-MemoryOS-For-Dummies.ps1
   ```
2. Your browser will open **`http://127.0.0.1:8765`** automatically.

### On Ubuntu / WSL2 / Linux
1. Run:
   ```bash
   ./run-for-dummies.sh
   ```
2. Open **`http://127.0.0.1:8765`** in your browser.

---

## 4. What You See on the Dashboard (`http://127.0.0.1:8765`)

* **Top Badges (`FPS` & `VRAM SAVED: 100%`):** Shows that your local graphics card isn't being choked by AI models.
* **Recommendation Cards:** Plain-English tips from the **Quiet Advisor** (for example: *"Trim unused context"* or *"Enable 8-bit shield"*). Clicking **Apply** saves the setting for you automatically.
* **Quick-Save Checkpoints:** Like video game quick-saves (`20` saved states on your SSD) so MemoryOS can recover in under `3 ms` if anything crashes.

---

## 5. Common "Oops" Questions

* **"What if `Gemma-4-31B-IT` says `503 Busy` or `429 Rate Limit`?"**  
  Don't worry! Free cloud grants get busy sometimes. MemoryOS automatically falls back to **`Qwen3.8-27B`**, **`DeepSeek-V4.1-Flash`**, **DigitalOcean MI300X** (if `DO_MODEL_ACCESS_KEY` is in `.env`), or its **built-in offline mode** so the app never crashes.
* **"Do I need to pay anything to try this?"**  
  No. The Dummies launcher works **100% offline** out of the box with the seeded 50-record demo database, and uses your free **AMD Token Lab** key when present in `.env`.

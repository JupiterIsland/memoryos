# Richard's AI Prompt & Workflow Cheatsheet

**Context:** Fast-thinking workflow. Paste raw files. Enforce strict constraints. Avoid hallucinations.  
**Target Architecture:** Pure Python stdlib, `BaseHTTPRequestHandler`, surgical `SEARCH/REPLACE` blocks.

---

## Section 1: The "Architecture Guardrails" (Put this in almost every prompt)

AI models default to the most popular frameworks (Flask, FastAPI, React). Jupiter Studio is strict pure Python. **Always paste this at the top of your prompt when asking for backend code:**

> **CRITICAL ARCHITECTURAL CONSTRAINTS:**
> - Do NOT use Flask, FastAPI, or `@app.route`.
> - Use standard library `BaseHTTPRequestHandler` (`do_GET`, `do_POST`).
> - Do NOT use `importlib`, `exec()`, or `eval()`.
> - The code must run on pure Python standard library with zero external dependencies.

---

## Section 2: Copy-Paste Prompts for Specific Tasks

### 1. The "Targeted Fix" Prompt (Surgical `SEARCH/REPLACE`)
*Use this when you need to add a feature or fix a bug without the AI rewriting the whole file.*

> I have attached `[filename]`.
> Please implement the following change: `[insert 1-2 sentence description of what you want]`.
>
> **Rules:**
> 1. Do NOT rewrite the entire file.
> 2. Output the exact `SEARCH/REPLACE` blocks required.
> 3. Ensure the `SEARCH` block is an exact match of the existing code.

### 2. The "Brutal Audit" Prompt (For DeepSeek)
*Use this when you've just written 500 lines of code and want to know if it's actually secure and efficient.*

> I have attached `[filename]`. Act as a senior systems engineer doing a hostile code review.
> Focus ONLY on:
> 1. **Security:** SQL injection, path traversal, SSRF, secret leakage.
> 2. **Performance:** Blocking I/O on the main thread, memory leaks, disk I/O inside loops.
> 3. **Correctness:** Edge cases that will crash the `ThreadingHTTPServer`.
>
> Output a bulleted list of issues. Do not rewrite the code. Just tell me what is broken and where.

### 3. The "Architecture Planner" Prompt (For Gemini / Claude)
*Use this before you write a new system (like the FrankHub or Control Plane).*

> I am building a new feature for Jupiter Studio: `[describe feature]`.
> The current stack is `[list relevant files]`.
>
> Do NOT write the code yet.
> 1. Outline the exact API endpoints needed.
> 2. Outline the SQLite schema changes required.
> 3. Identify the 3 most likely bugs or edge cases (e.g., concurrency, crash recovery).
> 4. Wait for my approval before generating code.

### 4. The "WTF is this error" Prompt
*Use this when a traceback makes no sense.*

> I am getting this error:
> ```text
> [Paste the exact traceback here]
> ```
> Here is the file it's breaking on: `[filename]`.
> Do not give me a general explanation of the error. Tell me the exact line number, why it's failing in this specific context, and give me the `SEARCH/REPLACE` block to fix it.

---

## Section 3: Workflow Hacks (How to Get Things Done Faster)

### Hack 1: The "Dirty Commit" (The AI Undo Button)
AI will break your CSS. It is inevitable.  
**Rule:** Before you paste an AI's `SEARCH/REPLACE` blocks, run this in your terminal:

```bash
git commit -am "WIP: before AI edits"
```

If the AI breaks the layout or deletes a necessary function, you just run `git reset --hard HEAD` and you are instantly back to a working state. No panic.

### Hack 2: The "Context Sandwich"
When pasting huge files (like `jupiter_studio_ui.py`), AI gets lost in the middle 40,000 tokens.  
**Rule:** Put your instructions at the TOP of the prompt, and repeat the most critical instruction at the BOTTOM of the prompt.

- **Top:** `"Only output SEARCH/REPLACE blocks for the CSS."`
- **Middle:** `[60k tokens of file]`
- **Bottom:** `"Remember: Do NOT rewrite the file. Only give me the CSS SEARCH/REPLACE."`

### Hack 3: The "Model Tag-Team"
Don't use one model for everything. Use them for their strengths:

- **Gemini / Claude:** Planning, architecture, UI layout, writing complex JavaScript logic.
- **DeepSeek:** Brutal code audits, finding security flaws, optimizing pure Python.
- **Antigravity / OpenCode / Qwen:** Applying surgical edits directly to local files and running tests until green.

### Hack 4: The "Typo Guard"
If you type too fast and misspell something (like typing `"trank"` instead of `"track"`), the AI will build an entire feature around your typo.  
**Rule:** If the AI's output makes absolutely zero sense, stop it immediately, hit `Ctrl+C`, and type:

> `"Correction: I meant [correct word], not [typo]. Discard that last response and try again."`

### Hack 5: Force the AI to Use Your Variables
If you want the AI to add a feature to a specific button or div, don't describe it.  
**Rule:** Copy the exact line of HTML or Python and paste it in the prompt:

> `"Add the click handler to this exact div: <div class=\"radar-metric\" id=\"frank-telemetry-chip\"><b id=\"rad-frank\">. Do not change the class or the ID."`

### Hack 6: The "Stop and Re-Read" Trigger
Sometimes an AI will confidently tell you that a file is broken when it isn't, or it will try to "fix" code that doesn't exist.  
**Rule:** If the AI starts hallucinating, paste this:

> `"Stop. Re-read the exact code I attached. Do not guess. If you cannot find the exact line I am talking about, say so instead of inventing a fix."`

---

## Section 4: The "Ship It" Checklist

Before you tag a release or push to `main`:

- [ ] Run `python3 -m py_compile [file]` to catch syntax errors instantly.
- [ ] Run `python3 NEON_SINGLE_FILE.py` to check the Control Plane.
- [ ] Run `unittest` (`126/126` across all 12 CI modules).
- [ ] Run the app and click around for 2 minutes. The AI can pass 126 tests but still break the CSS alignment of a button.

---

## Future Feature: The "Prompt Presets" UI (`v2.2.0`)

**Idea:** Instead of copy-pasting from this file, bake these prompts directly into the `Ctrl+K` Command Palette.

- Add a dropdown / Command Palette section in the UI: `"Load Prompt Preset..."`
- **Options:** Targeted Fix, Brutal Audit, Architecture Planner, Architecture Guardrails.
- When clicked, it injects the text directly into the chat box and attaches the active workspace files.

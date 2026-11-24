# Contributing to MemoryOS // Jupiter Studio

Thank you for your interest in contributing!

## Maintenance Expectations

* **Solo Project:** Issues and PRs are triaged **weekly** on a best-effort basis.
* **Questions & Ideas:** Please use **[GitHub Discussions](https://github.com/JupiterIsland/memoryos/discussions)** for setup help, feature pitches, and hardware compatibility notes rather than opening bug issues for general questions.

---

## Core Architectural Rules

Before opening a pull request, please respect these project guardrails:

1. **Zero External Runtime Dependencies in the Core:** The main workstation (`apps/jupiter_studio.py`, `src/memoryos/router.py`, `frank.py`, `memory_keeper.py`, `control_plane.py`, `workspace_pack.py`) runs purely on the Python standard library (`>= 3.11`). Do not require Flask, FastAPI, PyTorch, or heavy ML frameworks at runtime. (NumPy and FastAPI remain optional accelerators/fallbacks only.)
2. **Zero Arbitrary Plugin Execution:** `src/memoryos/control_plane.py` must never use `exec`, `eval`, `importlib`, or execute plugin-supplied shell strings.
3. **No Broken Security Boundaries:** Keep loopback-by-default binding, `Host`/`Origin`/`Referer`/`Sec-Fetch-Site` guards, secret-file filtering, and `WorkspacePack` path/symlink containment intact across every PR.
4. **Minimal Monochrome / Ultraviolet UI:** Keep `apps/jupiter_studio_ui.py` icon-free (zero inline `<svg>` icons, icon fonts, or emojis).

---

## Pull Request Checklist

1. Run the single-command verifier locally before pushing:
   ```bash
   python3 -B verify.py
   ```
   Every CI module must compile, `NEON_SINGLE_FILE.py` must report `NEON STATUS: CERTIFICATION READY`, and all unit tests must pass cleanly under `-W error::DeprecationWarning`.
2. **Include tests with every code change** (behavior changes, bug fixes, or new provider integrations).
3. Never commit `.env`, `QuietAdvisorDB.sqlite*`, API keys, or local build artifacts (`dist/`, `__pycache__/`).
4. Keep PRs focused and small so they can be reviewed cleanly.

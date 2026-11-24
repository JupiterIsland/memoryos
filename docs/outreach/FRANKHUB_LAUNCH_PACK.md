# FrankHub Launch Pack (GitHub · Discord · LinkedIn · Pages)

Use this pack to move cleanly onto your new GitHub, GitHub Pages, Discord, and LinkedIn without breaking history or overclaiming features.

---

## 1. Rollout Checklist (Day 1 → Day 4)

### Day 1 — Accounts & Continuity
- Keep `JupiterIsland/memoryos` live and intact (commits, `v2.0.0` tag, binaries, and GitHub Actions CI proof remain unbroken).
- Reserve your new GitHub account/organization, Discord server name, and update your LinkedIn profile links.
- Add your new GitHub / Discord URLs to the footer and links in `FRANKHUB.md` and `website/frankhub.html`.

### Day 2 — New GitHub Repository & GitHub Pages
When pushing to the new GitHub repo while keeping full commit history intact:

```powershell
# In C:\Users\RJMed\My Drive\memoryos
git remote add neworigin https://github.com/<YOUR_NEW_USER>/<YOUR_NEW_REPO>.git
git push neworigin main --tags
```

For your **brand-new GitHub Pages site**:
- **If using `website/` via `.github/workflows/deploy-website.yml`:** `website/frankhub.html` and `website/assets/screenshots/*` are already wired cleanly (alongside `website/jupiter-island.html`).
- **If creating a standalone landing page on your new repo:** copy `website/frankhub.html` → `index.html`, copy `website/assets/` alongside it, and update the two `https://github.com/JupiterIsland/memoryos` hrefs if your new repo has a new slug.

### Day 3 — LinkedIn Origin Story Post (Draft)
Publish the human story before dropping product links:

> A year ago I wasn’t trying to build Jupiter Studio or FrankHub.
>
> Everyone kept talking about AI like an untouchable mystery box, so I started experimenting on an 8 GB laptop to see what actually happened under the hood.
>
> One messy folder turned into another: *Gordon* → *Jupiter One* → *MemoryOS* → *The Quiet Advisor*. Most ideas got binned. The ones that solved real problems survived — keeping VRAM free before a compile or game, remembering workspace rules across sessions, and stopping local continual learners from forgetting old skills when learning new ones.
>
> That small survivor turned into **Frank** (`Frank-v1`), a zero-VRAM pure-Python neural helper (`241–335 μs` on CPU), and **FrankHub**, the workshop inside Jupiter Studio where Frank learns, stores rules in SQLite, and gets audited against forgetting.
>
> No hype, no datacentre GPU required — just open-source tools built out of curiosity.
>
> Code + screenshots in the comments / repo link below.

### Day 4 — Discord Structure & Welcome Copy

Suggested clean channels (keep it small to start):
- `#start-here` — Origin story, repo link, latest release binary, and how to run `clean_install_windows.ps1`
- `#frankhub-audits` — Share `Audit Frank` (`Naive vs EWC+Replay`) scores, checkpoint health, and teaching prompts
- `#hardware-setups` — Laptop GPUs, AMD Ryzen AI NPU (`Lemonade Server`), `Ollama`, Groq / Token Lab routing setups
- `#experiments` — Early builds, UI themes (`QUANTUM`, `RADEON`, `ATARI B&W`), and `Modelfile.frank` tweaks
- `#releases` — GitHub release notes and CI status updates

**Pinned `#start-here` welcome message:**

> **Welcome to FrankHub.**
>
> **FrankHub is where Frank learns** — the memory vault, EWC continual learning, and audit workbench inside **Jupiter Studio** (`MIT` open source).
>
> * GitHub: `<NEW_GITHUB_URL>`
> * Latest Release (`v2.0.0`): `<NEW_RELEASES_URL>`
> * Web Page: `<NEW_PAGES_URL>`
>
> Start with `python3 -B apps/jupiter_studio.py` or grab the standalone zip from Releases, open the **FrankHub** tab, pin a rule, teach `Frank-v1`, and click **Audit Frank** to run the live anti-forgetting self-test.

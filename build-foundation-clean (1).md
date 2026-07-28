# Full Working System Map

## System Overview

```text
Windows + C:\Dev
        ↓
Jupiter Island Cockpit
        ↓
365 Copilot / Build Director
        ↓
Jupiter Island Model / Workhorse
        ↓
NetBeans + Local History
        ↓
Cygwin Commands
        ↓
Localhost Proof Screen
        ↓
Git Checkpoint
        ↓
GitHub Output

Side lanes:
Perplexity / Comet = research scout
Tor / Onion = separate privacy environment
```

---

## Foundation: Windows + `C:\Dev`

`C:\Dev` is the single root for everything you build, test, save, and later push to GitHub.

Purpose:

- Stops projects scattering across Desktop, Downloads, Documents, and random app folders.
- Makes backup, Git, NetBeans, Cygwin, Jupiter Island, and model work all point to one known place.
- Gives the whole system a fixed physical base.

```text
C:\Dev
│
├── ai-media-ops-console
├── The Music
├── Jupiter Island
├── models
├── scripts
├── archives
├── docker
└── workspace
```

```text
             WINDOWS HOST
                  │
                  ▼
              C:\Dev ROOT
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
Projects       Models        Scripts
    │             │             │
    ▼             ▼             ▼
Sonic Boom  Jupiter Island  Build tools
```

This is the floor. Everything else stands on it.

---

## Central Control Layer: Jupiter Island

Jupiter Island becomes the main cockpit.

Purpose:

- You chat to models for information, planning, coding help, and build direction.
- It should eventually generate code, apply file changes into `C:\Dev`, run or guide commands, and keep work moving without bouncing between noisy browser tabs.
- This is where Sonic Boom can be directed and built from, while the actual files still live safely in `C:\Dev`.

```text
Jupiter Island = helmet / cockpit / command centre
```

```text
                JUPITER ISLAND COCKPIT
                         │
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
 Chat to models      Build tasks        Project memory
     │                   │                   │
     ▼                   ▼                   ▼
 Instructions        Code output         Saved work
                         │
                         ▼
                       C:\Dev
```

Use it for:

```text
Fix App.jsx only.
Build Sonic Boom Control Room.
Summarise changed files.
Prepare Git commit message.
```

---

## Build Director: Microsoft 365 Copilot / Me

I act as the build director and sequence controller.

Purpose:

- Keep the project moving in the right order.
- Decide what to fix first, what to ignore, and what not to overbuild.
- Translate broad ideas into exact implementation steps for the Jupiter Island model, NetBeans, Cygwin, or Git.

```text
Current State
Target State
Next Action
```

```text
             BUILD DIRECTOR
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
Assess state   Set target   Give next action
      │            │            │
      └────────────┼────────────┘
                   ▼
            Controlled build step
```

---

## Workhorse Layer: Jupiter Island Model

The Jupiter Island model is the builder.

Purpose:

- Generate code.
- Explain errors.
- Help rebuild broken files.
- Work inside the local project structure once Jupiter Island supports that.
- Eventually apply changes directly into `C:\Dev`.

```text
              JUPITER ISLAND MODEL
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
 Generate code     Fix errors     Explain files
        │              │              │
        └──────────────┼──────────────┘
                       ▼
             Controlled file change
                       │
                       ▼
                     C:\Dev
```

Good instruction:

```text
Modify only src/App.jsx.
Do not touch routing, backend, auth, database, or build config.
Return changed files only.
```

Bad instruction:

```text
Improve the whole app.
```

That is how chaos starts.

---

## Source Editing Layer: NetBeans

NetBeans is the controlled file workshop.

Purpose:

- Open and edit actual files under `C:\Dev`.
- Inspect `App.jsx`, `App.css`, `main.jsx`, configs, Markdown, Dockerfiles, and project structure.
- Use Local History to recover mistakes before Git is even involved.

```text
                NETBEANS
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   Open files   Inspect code   Edit safely
       │           │           │
       └───────────┼───────────┘
                   ▼
             Save into C:\Dev
```

Key use:

```text
Open file
Inspect
Edit
Save
Use Local History if broken
```

---

## Recovery Layer: NetBeans Local History

Local History is your short-term safety net.

Purpose:

- Recover from bad pastes, mixed code, accidental deletions, or model damage.
- Restore earlier versions of files even if you did not commit to Git.
- Protect fast experimentation.

```text
              LOCAL HISTORY
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   Bad paste   Deleted file   Broken edit
        │           │           │
        └───────────┼───────────┘
                    ▼
           Restore previous version
                    │
                    ▼
              Working file again
```

Git is for checkpoints. Local History is for “I just broke that”.

---

## Terminal Layer: Cygwin

Cygwin is the command layer attached to `C:\Dev`.

Purpose:

- Run project commands without relying on browser tools.
- Use Linux-style commands on Windows.
- Inspect files, Git status, folder trees, and run Vite.

```shell
cd /cygdrive/c/Dev/ai-media-ops-console
git status
tree src
npm run dev
```

```text
                 CYGWIN
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
   git status    tree src    npm run dev
      │            │            │
      └────────────┼────────────┘
                   ▼
              Terminal truth
```

Cygwin tells the truth. If a model says something works but Cygwin errors, Cygwin wins.

---

## Truth Screen: Localhost

Localhost is the visual proof.

Purpose:

- Shows whether the app really runs.
- Confirms React is mounting.
- Exposes broken JSX, CSS issues, blank pages, and runtime errors.
- Stops you trusting theory.

```text
              LOCALHOST
                  │
                  ▼
        http://localhost:5173/
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
 Renders UI   Shows error   Blank/raw HTML
      │           │           │
      ▼           ▼           ▼
 Progress    Fix code     Fix React mount
```

Target result:

```text
Sonic Boom Control Room renders cleanly.
No raw HTML.
No mixed code.
No broken imports.
```

---

## Version Control Layer: Git in NetBeans

Git becomes your checkpoint and history system.

Purpose:

- Track what changed.
- Compare files before committing.
- Commit known-good states.
- Push completed work to GitHub.

```text
              GIT IN NETBEANS
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    Review diff   Commit      Push later
       │            │            │
       └────────────┼────────────┘
                    ▼
             Clean checkpoint
```

Correct use:

```text
Fix files locally
Test localhost
Review Git diff
Commit checkpoint
Push to GitHub
```

---

## Remote Storage / Output: GitHub

GitHub is the remote archive and publishing point.

Purpose:

- Store the finished project state.
- Keep work backed up.
- Let future tools or collaborators access the repo.
- Preserve milestones once the local version is working.

```text
              LOCAL PROJECT
                    │
                    ▼
              Git checkpoint
                    │
                    ▼
                  GitHub
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    Backup      Remote repo   Future deploy
```

Correct order:

```text
Local build first
Git commit second
GitHub push third
```

---

## Research Scout: Perplexity / Comet

Perplexity and Comet are for research, comparison, and checking facts.

Purpose:

- Research tools, libraries, plugins, browsers, NVIDIA docs, music platforms, and technical options.
- Compare sources quickly.
- Reduce tab chaos.
- Help decide whether a tool is useful or just marketing.

```text
          PERPLEXITY / COMET
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
 Research docs  Compare tools  Check claims
      │           │           │
      └───────────┼───────────┘
                  ▼
          Decision support only
```

---

## Separate Privacy / Alternate Environment: Tor + Onion Setup

Tor is a separate environment, not part of the normal Sonic Boom build loop.

Purpose:

- Create a privacy-focused browsing or onion-service environment.
- Keep experimental/private web work away from the main build browser.
- Avoid mixing normal development, research browsing, Microsoft account work, and onion work in one place.

```text
              TOR / ONION
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
 Private web   Onion setup   Separate testing
       │           │           │
       └───────────┼───────────┘
                   ▼
         Separate from main build loop
```

---

## Browser Layer

Browsers are support tools, not the centre.

Purpose:

- Open localhost.
- View docs.
- Test web pages.
- Use Comet/Perplexity for research.
- Keep Edge limited to Microsoft account or Microsoft-specific work if it keeps pulling you into Bing/Copilot loops.

```text
               BROWSERS
                  │
   ┌──────────────┼──────────────┐
   ▼              ▼              ▼
Plain browser    Comet          Edge
localhost        research       Microsoft only
   │              │              │
   └──────────────┼──────────────┘
                  ▼
         Support role, not cockpit
```

Jupiter Island is the cockpit. Browsers are support tools.

---

## Sonic Boom Flow

This is how Sonic Boom should move through the system.

```text
Idea
↓
365 Copilot shapes it into build steps
↓
Jupiter Island model generates or edits code
↓
Files save into C:\Dev
↓
NetBeans inspects and corrects files
↓
Cygwin runs the commands
↓
Localhost proves it works
↓
Git records checkpoint
↓
GitHub receives finished state
```

```text
              SONIC BOOM FLOW
                    │
                    ▼
             Music control idea
                    │
                    ▼
             Build instruction
                    │
                    ▼
              Code generated
                    │
                    ▼
             Saved under C:\Dev
                    │
                    ▼
              Tested locally
                    │
                    ▼
              Git checkpoint
                    │
                    ▼
              GitHub output
```

Current task:

```text
Sonic Boom idea
↓
Clean React files
↓
Render Control Room
↓
Confirm localhost
↓
Commit first checkpoint
```

---

## Sonic Boom Current Build Target

First prototype slice:

```text
Sonic Boom Control Room
```

It must show:

```text
Live Radio
Active Band Rooms
New Music
Upcoming Gigs
Open Sessions
Mentors Online
Restoration Projects
Opportunities
```

```text
           SONIC BOOM CONTROL ROOM
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
 Live Radio    Band Rooms       Gig Guide
    │               │               │
    ▼               ▼               ▼
 Requests       Discussions     Real events
    │               │               │
    └───────────────┼───────────────┘
                    ▼
          People meet through music
```

Rules:

```text
No backend
No database
No auth
No audio engine
No AI calls
No routing until clean
```

The first goal is not a complete platform. The first goal is a clean working screen that proves the direction.

---

## Build Loop With Commands

### 1. Start in Cygwin

```shell
cd /cygdrive/c/Dev/ai-media-ops-console
git status
tree src
npm run dev
```

### 2. Open localhost

```text
http://localhost:5173/
```

Check:

```text
Does it render?
Is it blank?
Is raw HTML showing?
Is mixed code visible?
Any browser console errors?
```

### 3. Edit in NetBeans

Open:

```text
src/main.jsx
src/App.jsx
src/App.css
src/index.css
src/data/sonicBoomData.js
```

Rules:

```text
main.jsx = React mount only
App.jsx = React layout only
App.css = styling only
index.css = global theme only
sonicBoomData.js = mock data only
```

### 4. Refresh localhost

```text
Save file
   │
   ▼
Refresh localhost
   │
   ├── Works = move forward
   └── Broken = use error + Local History
```

### 5. Check Git

```shell
git status
git diff --stat
```

### 6. Commit only when clean

```shell
git add src/main.jsx src/App.jsx src/App.css src/index.css src/data/sonicBoomData.js
git commit -m "Add Sonic Boom control room prototype"
```

Only commit after:

```text
localhost renders cleanly
files are separated correctly
no mixed code
```

### 7. Push later

```shell
git push
```

---

## Final Working Stack

```text
Windows + C:\Dev
= fixed base for all projects and files

Jupiter Island
= central cockpit where models, instructions, building and project control happen

365 Copilot
= build director that decides order and prevents scope drift

Jupiter Island model
= workhorse that generates and applies code under direction

NetBeans
= real file workshop with editing, inspection, Git, and Local History

Cygwin
= command layer for running builds, Git checks, and project inspection

localhost
= proof screen that shows whether the app actually works

Git in NetBeans
= checkpoint system and controlled version history

GitHub
= remote storage and final project output

Perplexity / Comet
= research scout for tools, docs, platforms, and comparisons

Tor / onion setup
= separate privacy environment, not mixed with the main build loop
```

```text
              FULL SYSTEM STACK

              GitHub Output
                   ▲
                   │
              Git Checkpoint
                   ▲
                   │
            Localhost Proof
                   ▲
                   │
             Cygwin Commands
                   ▲
                   │
          NetBeans File Workshop
                   ▲
                   │
        Jupiter Island Workhorse
                   ▲
                   │
            365 Build Director
                   ▲
                   │
        Jupiter Island Cockpit
                   ▲
                   │
          Windows + C:\Dev Root

Side support:
Comet / Perplexity = research
Tor / Onion = separate privacy environment
```

---

## Operating Rule

If a tool does not help one of these, it is noise:

```text
Build
Inspect
Run
Recover
Research
Commit
Ship
```

For Sonic Boom, the next real milestone is simple:

```text
Clean render first.
Then build the Control Room.
Then commit.
```

No nonsense.

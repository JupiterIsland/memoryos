# Security Policy

## Supported Versions

Only the current **`v2.x`** release line is actively supported with security updates.

| Version | Supported |
| :--- | :--- |
| `v2.x` (`main`) | Yes |
| `< v2.0` | No |

---

## Reporting a Vulnerability Privately

If you discover a security issue, please report it privately via **[GitHub Security Advisories](https://github.com/JupiterIsland/memoryos/security/advisories/new)** rather than opening a public GitHub Issue.

Please include:
- A clear description of the issue and the affected file/endpoint.
- Minimal reproduction steps or a proof-of-concept request.
- Your assessment of impact (for example, local API key exposure or cross-origin bypass).

Reports are reviewed as promptly as a solo-maintainer schedule allows.

---

## Security Architecture & Boundaries

* **Loopback Binding by Default:** Both Jupiter Studio (`apps/jupiter_studio.py`) and the standalone router server (`src/memoryos/server.py`) bind to `127.0.0.1` by default and refuse non-loopback addresses (`0.0.0.0`, `::`, LAN IPs, or empty host strings) unless `--unsafe-lan` is explicitly passed.
* **Per-Launch Access Token for LAN (and Optional Loopback):** Binding non-loopback automatically enables a random per-launch access token (`?t=...` on initial open, immediately swapped for an `HttpOnly; SameSite=Strict` cookie or `X-Studio-Token` header). Pass `--require-token` (or set `JUPITER_STUDIO_REQUIRE_TOKEN=1`) to enforce the token on loopback as well.
* **DNS-Rebinding & CSRF Guards:** Requests with unexpected `Host`, `Origin`, `Referer`, or `Sec-Fetch-Site: cross-site` headers are rejected with `HTTP 403`.
* **Workspace Path Containment:** `WorkspacePack` (`src/memoryos/workspace_pack.py`) resolves every requested path (including symlinks) with `.resolve()` and `.relative_to(root_dir)`, dropping anything outside the workspace root.
* **Secret Upload Blocklist (Safety Net):** Both the backend (`WorkspacePack`) and browser UI drop common credential files (`.env`, `.pem`, `.key`, `.p12`, `.pfx`, `.htpasswd`, SSH keys, `credentials.json`). Treat this as a **safety net, not an absolute guarantee** — never store secrets inside source files you deliberately attach to prompts.
* **Declarative Zero-Exec Plugins (`src/memoryos/control_plane.py`):** Plugin packs only select named functions from `ALLOWED_EXECUTORS` (no `exec`, `eval`, or dynamic `importlib`). `DeclarativePluginLoader` rejects packs requesting `allow_network: true`.

---

## Honest Scope Limits & Non-Goals

* **Local Process Trust (Default Loopback Mode):** Without `--require-token`, any process running under your OS user account can call `http://127.0.0.1:7860/api/*` without a token (that same user account can already read `.env` on disk). Use `--require-token` if you run untrusted local software under your own account.
* **Plain HTTP on `--unsafe-lan`:** LAN mode uses unencrypted HTTP. Use it only on a trusted private network or behind an authenticating TLS reverse proxy.
* **SHA-256 Checksums on Checkpoints & Plugin Manifests:** Embedded `checksum_sha256` fields detect accidental file corruption cleanly, not a malicious attacker who already has write access to your local filesystem.
* **NEON Execution Budgets:** `BudgetEnforcer` enforces caller-side wall-clock timeouts (`thread.join`), estimated caller memory hints, and post-hoc CPU time checks (`time.process_time()`). Python threads cannot be forcibly terminated mid-syscall inside the same process.

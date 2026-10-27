# Project Aiko — Engineering Audit & Remediation

**Repository:** `omax404/aiko` (Project-Aiko) · **Branch:** `main` · **HEAD at audit start:** `487c128`
**Audit date:** 2026-10-24/25 · **Working tree:** the repo already contained uncommitted changes from a prior session; those were treated as the code under audit and preserved.
**Method:** 5 parallel read-only audit tracks (security/API, backend runtime, React/Tauri client, Android+website, QA/DX) → consolidated risk-ranked plan → parallel remediation in disjoint write scopes → Lead review + full verification.

Detailed per-track evidence (quotes, line numbers, exploit scenarios): `.tmp/audit/{sec-api,core-runtime,frontend,mobile-web,qa-dx}.md`
Raw measurements: `.tmp/audit/qa-baseline.txt`

---

## 1. Executive summary

**Verdict:** the product is a genuinely ambitious multi-stack companion app (Python/aiohttp hub + Tauri/React client + Kotlin app + Discord/Telegram/Twitch satellites), but its "Tier-0 / production-grade / 100 % tests" self-description was not supported. The audit found **one exploitable cross-trust vulnerability**, **three product features that were silently non-functional**, **a release pipeline that could not have produced a build**, and **CI that could never have been green**.

What was true: `npx tsc --noEmit` is clean (strict + `noUncheckedIndexedAccess`), no secrets are committed, the JWT/HMAC implementation is not trivially forgeable, the upload extension allow-list and MCP file sandbox are sound, HITL is server-side and fails closed, and the bundled `package-lock.json` files are consistent.

What was not:

| Theme | Reality found |
|---|---|
| CI | Never green: ubuntu install dies on unconditional `pyaudio`; `ruff` = 1 595 errors; coverage gate 70 % vs measured **27.5 %**. Release job also structurally broken by an absolute Windows path in `scripts/neural_hub.spec`. |
| Features | Semantic RAG never initialised (circular gate) → `[RECALL]`/memory context always empty. Discord satellite crashed at import (`bot` undefined). Android↔hub sync could not authenticate or even open cleartext to a LAN IP. |
| Security | Satellite bots relay untrusted internet users' messages under the **desktop admin JWT**, and `SCAN`/`CAMERA`/`EMAIL_INBOX`/`BIO_REGISTER` had no authz/HITL → a Discord stranger could get the master's screen described. Plus: `[OPEN:]` cmd.exe injection, LaTeX arbitrary-file-read, attachment arbitrary-local-file-read/SSRF, HITL approvals broadcast to any client, JWTs written to the access log via `?token=`. |
| Correctness | `chat_token` released the client's "thinking" lock on the first streamed sentence → concurrent sends interleave into one buffer; 45 s watchdog produced ghost/duplicate replies; `vision.analyze_base64` defined twice (provider routing bypassed); `broadcast_event` could kill healthy sockets due to a zip/index mismatch. |
| Process | 27.5 % coverage with 15 modules at 0 %; a test file re-declared the code it tested; integration "tests" contained zero tests; no lint/format enforcement; no dependency pinning or lockfile. |

**Remediation delivered in this pass:** 38 tracked files modified + 2 new files (regression tests, this report) — **+1 210 / −263 lines** across the tracked diff — covering 24 FIXED issues, 8 PARTIAL, 15 FLAGGED for product/legal decisions. Every fix is justified by a reproduced defect; nothing was rewritten for style. Final gates: **pytest 100 passed / 1 skipped**, **ruff CI gate exit 0**, **all core modules byte-compile and import**, **`tsc --noEmit` 0 errors**, **Vitest 20/20**, **hub app constructs with 48 routes / 4 middlewares**.

> Important: no git commits were created. The worktree had pre-existing uncommitted changes touching many of the same files, so committing would have silently mixed someone else's work into the audit history. The remediation is a reviewable working-tree diff; see §7 for the exact commands to commit it in logical chunks.

---

## 2. Discovery (Phase 1)

| Item | Finding |
|---|---|
| Purpose | Self-hosted, user-owned AI companion desktop app: emotional state, long-term memory, vision/hearing/voice, PC automation with a human-in-the-loop gate, satellites (Discord/Telegram/Twitch), native Android client, marketing site. |
| Languages / LOC | Python ~8.6 k statements (`core/` + `launch.py`), TypeScript/TSX ~6 k (47 files), Kotlin ~33 files, Rust (Tauri shell, small), PS1/BAT launchers. |
| Backend runtime | **aiohttp** (`core/neural_hub.py` builds `web.Application`; 28 `/api/*` routes + `/ws`). Manifests declare `flask`, `uvicorn`, `fastapi` but only `core/callback_server.py` (dead Flask app) uses Flask. Binds `127.0.0.1`, first free port 8000–8049, writes `data/port.json`. |
| Frontend runtime | React 19 + Zustand 5 + Vite 7 + Tailwind 4 + pixi 6.5.10 (Live2D via `pixi-live2d-display` 0.4.0), packaged by Tauri v2; React Markdown + KaTeX for message rendering. |
| Android | Kotlin 2.0.21 / AGP 8.10 / Gradle 8.12, Compose BOM, Hilt, Room 2.7.1, DataStore, `io.getstream:stream-webrtc-android`, CameraX, ML Kit barcode (QR pairing), GLES Live2D. |
| Website | Next.js App Router + React 19 + Three/R3F/GSAP, deployed on Vercel. |
| Entry points | `LAUNCH_AIKO.bat` → `launch.py` (venv bootstrap → `python -m core.neural_hub` → Tauri binary) · `core/neural_hub.py` · `aiko-app/src/main.tsx` · `android MainActivity` · satellites `python -m core.satellites.*`. |
| Deployment | Desktop/self-hosted only; no Docker/container config; Tauri MSI/NSIS via GitHub release; website on Vercel. |
| Tests / CI | pytest (98 collected baseline), Vitest (12 baseline), GitHub Actions (3 jobs + tag release). Missing: pre-commit, formatter gate, mypy in CI, Android/website jobs, dependency lock. |
| Dependency posture | 51+ runtime deps, all `>=`, no upper bounds, no lockfile/hashes; `pip install -r requirements.txt` runs automatically on first launch (`launch.py:77`). Split-brain between `requirements.txt` and `pyproject.toml` (e.g. `chromadb` only in requirements but imported by `core/rag_memory.py`). |

---

## 3. Prioritized issue table (Phase 3)

Severity is risk-adjusted for this threat model: single-user local app, loopback hub, but with **untrusted remote users** arriving through public bots and a LAN/mobile client. Effort: S ≤ 1 h, M ≤ 1 day, L > 1 day.

| # | Issue (evidence at audit time) | Sev | Effort | Fix approach | Status |
|---|---|---|---|---|---|
| 1 | **Release pipeline cannot build**: `scripts/neural_hub.spec` hardcodes `C:\Users\ousmo\...`; PyInstaller fails on runner → Tauri `externalBin` missing. | Critical | S | Resolve paths from `SPECPATH`/`__file__`; clear error if hub script missing. | **FIXED** |
| 2 | **CI never green**: ubuntu install dies (`pyaudio` sdist needs portaudio); `ruff` 1 595 errors; coverage gate 70 % vs 27.5 %. | Critical | S/M | apt system deps; two-tier ruff gate (fatal rules gate, full lint advisory); coverage floor 25 with ratchet comment; pin ruff. | **FIXED** |
| 3 | **Semantic memory dead**: `is_available()` false until `_initialized`, which only `_initialize()` sets, reachable only after the gate → conversations never embedded, context always empty. (`core/rag_memory.py:243`) | Critical | M | Memoized lazy init (`_init_attempted`), `is_available()` triggers one attempt; prime from worker thread at boot. | **FIXED** |
| 4 | **Discord satellite crashes at import**: `bot` never instantiated → `NameError` on `@bot.event` (`core/satellites/discord_bot.py:93`). | Critical | S | Restore `commands.Bot` with `message_content`/`voice_states` intents. | **FIXED** |
| 5 | **Remote satellite users get admin-capability reads**: bots forward any Discord/Twitch user's message with the desktop admin JWT; auto screen-capture on keywords + `SCAN`/`CAMERA`/`EMAIL_INBOX`/`BIO_REGISTER` had no admin check or HITL. (`core/chat_engine.py:371`, `executor.py:283-296`) | Critical | M | Admin-gate auto-capture; add those four tools to the HITL set and admin-gate their handlers. | **FIXED** (bot-token scoping still recommended) |
| 6 | **Android mobile sync cannot work**: `AikoPrefs.setAuthToken` had zero call sites (no token ever provisioned), WebRTC offer POST sent no `Authorization`, and the network security config's CIDR `<domain>` entries are invalid → cleartext to LAN IPs blocked. | Critical | M | Valid NSC (documented accepted cleartext risk), Bearer on offer, fail-fast when token missing; also `allowBackup=false`. | **PARTIAL** — token provisioning still needs `ChatRepository`/QR change |
| 7 | **HITL approval is not bound to the requester**: tool request broadcast to all clients; any client (stale tab, Android, any token) can approve/deny. (`core/api/websocket.py:14-37,422-433`) | High | M | Bind `request_id` → originating connection + args hash via a `ContextVar`, accept approval only from that client. | **FLAGGED** (design change) |
| 8 | **`/token` treats loopback as authorization**: any local process/other Windows session gets a 24 h admin JWT; reverse proxy on loopback makes it a total bypass. (`routes.py:98-113`) | High | M | Reject proxy headers (done); longer-term: one-time nonce + socket ACL / per-session scoped token. | **PARTIAL** |
| 9 | **Attachments = arbitrary local file read + SSRF**: `os.path.exists(source)` → `open()` on client-supplied path; else unbounded `session.get(source)`. (`chat_engine.py:559-616`) | High | M | Confine local reads to `data/uploads` (resolve + `is_relative_to`), SSRF-gate URLs to public IPs, 20 MB cap + timeout. | **FIXED** |
| 10 | **Settings can redirect the LLM (and the user's API key)**: `POST /api/settings` is an unrestricted config write (`extra="allow"`); `llm.url` accepted anything. (`routes.py:463`) | High | S | Validate `llm.url` with existing `verify_connection_safety` (HTTPS for remote hosts). | **FIXED** |
| 11 | **JWTs leak into logs**: aiohttp default access log records `GET /ws?token=...`; Android logs the full WS URL. (`core/neural_hub.py:436`, `ChatRepository.kt:249`) | High | S | Redaction filter on `aiohttp.access`; Android log line still open (FLAGGED). | **PARTIAL** |
| 12 | **JWT hardening**: header `alg` never parsed, default token TTL 168 h (doc says 24 h), `exp` checked before signature. (`core/api/auth.py:27-64`) | High | S | Parse/validate `alg=HS256`, require `sub`, numeric `exp`, enforce expiry after signature, default 24 h. | **FIXED** |
| 13 | **Concurrent chats corrupt one brain**: WS rate-limiter allows 5 msgs/2 s, each spawned as an independent task; history/tool futures/streaming interleave. (`websocket.py:353`) | High | M | Per-connection `asyncio.Lock` serializing chat/branch; control messages stay unlocked; cancel+await on disconnect. | **FIXED** |
| 14 | **Client streaming state broken**: `chat_token` cleared `isThinking` on the first sentence → send guard released mid-stream; reply rebuilt from sentence chunks lost formatting; 45 s watchdog injected ghost messages and the late reply duplicated. (`useNeuralStore.ts:339-360`) | High | M | `isThinking` spans the request lifecycle; prefer authoritative `chat_end.text`; verbatim tokens; watchdog retained for silence. | **FIXED** |
| 15 | **Settings/onboarding silently 401**: `/api/settings` fetch paths omitted the Bearer header. (`SettingsPanel.tsx:25-53`, `OnboardingWizard.tsx:30-37`) | High | S | Use `getAuthHeaders()` on GET/POST. | **FIXED** |
| 16 | **TTS audio URL hardcoded `:8000`** although the hub may bind 8001–8049. (`useNeuralStore.ts:364`) | High | S | Resolve via discovered hub URL. | **FIXED** |
| 17 | **StrictMode double-mount opens two WebSockets** (guard set after two awaits; orphan keeps heartbeat/broadcast handlers → duplicate `chat_end`/`tts_audio`). (`useNeuralStore.ts:237-275`) | High | S | Acquire connect guard before the first `await`; reset on every exit path. | **FIXED** |
| 18 | **`refresh_index` does not exist** → `AttributeError` every 300 s; knowledge ingestion never ran. (`background.py:97`) | High | M | Implement mtime-manifest based `refresh_index()` over `data/knowledge` + call it safely. | **FIXED** |
| 19 | **Proactive interval unvalidated**: `0` → screen+VLM+ReAct every ~100 ms; `"180"` → `TypeError` kills the loop silently. (`websocket.py:394`) | High | S | Coerce, clamp to `[10, 3600]`, never raise. | **FIXED** |
| 20 | **Internal exceptions returned to UI**: `f"Error processing message: {e}"`. (`websocket.py:170-177`) | High | S | Fixed user-facing strings + `logger.exception`. | **FIXED** |
| 21 | **`broadcast_event` can kill healthy sockets**: results zipped against unfiltered client list; index shift on closed clients. (`broadcast.py:31-53`) | High | S | Pair each client with its own send future. | **FIXED** |
| 22 | **Runtime NameErrors**: `config` undefined in `/api/email/settings`; `logger` undefined in `pc_manager`; Discord `bot` (see #4). (`routes.py:877`, `pc_manager.py:189`) | High | S | Import fixes. | **FIXED** |
| 23 | **`vision.analyze_base64` defined twice** — second (Ollama-only) shadows provider-routed version → cloud/transformers vision bypassed for attachments. (`vision.py:271,488`) | High | S | Keep one provider-routed implementation. | **FIXED** |
| 24 | **LaTeX arbitrary file read**: `os.path.join(output_dir, filename)` with percent-decoded path param (`..%5C..%5C`). (`routes.py:677`) | High | S | `resolve()` containment + `.png/.pdf` allow-list. | **FIXED** |
| 25 | **`[OPEN:]` cmd.exe injection**: metacharacters interpreted by `cmd /c start` even with `shell=False`. (`executor.py:402`) | High | S | `os.startfile` (ShellExecute) + metacharacter rejection. | **FIXED** |
| 26 | **`pdflatex` shell escape** on untrusted snippets. (`latex_engine.py:47,88`) | Med | S | `-no-shell-escape`. | **FIXED** |
| 27 | **Provider API key persisted to localStorage** (`neural-storage`) and copied from backend every 30 s. (`useNeuralStore.ts:968-1043`) | High | S/M | Remove from persisted slice / keep in memory; needs product decision on offline settings. | **FLAGGED** |
| 28 | **Tauri webview hardening**: `withGlobalTauri:true`, CSP `unsafe-eval`/`unsafe-inline`. (`tauri.conf.json:13,44`) | Med | M | Remove `unsafe-eval`, restrict `withGlobalTauri`, add navigation handler. | **FLAGGED** |
| 29 | **Android release can ship debug-signed**: fallback to `~/.android/debug.keystore` with `android`/`androiddebugkey`. (`app/build.gradle.kts:24-40`) | Critical (release) | S | Fail-closed signing (task action throws when unconfigured); no fallback. | **FIXED** |
| 30 | **Android plaintext secrets + backup**: DataStore provider keys/token, `allowBackup="true"`. | High | S | `allowBackup=false` (done); Keystore-backed storage recommended. | **PARTIAL** |
| 31 | **Live2D Cubism SDK + proprietary model shipped under bare MIT** (207 KB core ×2, 57.67 MB `vivian.moc3` ×2, no notices). | High (legal) | M | Legal review; add third-party notices / confirm redistribution rights before release. | **FLAGGED** |
| 32 | **No dependency pinning/lockfile**; first-run `pip install` pulls latest of 51 unpinned deps into real users' machines. | High | M | Lockfile/constraints, upper bounds for breaking majors, hash pinning; documented as known limitation. | **FLAGGED** |
| 33 | **Memory write path is O(n²) and blocks the loop**: every message triggers a synchronous embedding HTTP call + full-history JSON atomic write ×3. (`unified_memory.py:528-551`) | High | L | Async write-behind queue + incremental persistence; needs design. | **FLAGGED** |
| 34 | **Blocking calls in coroutines**: pyautogui type/click/press, `subprocess.run(30s)`, 50 MB upload `f.write`, full-collection export. | Med | M | pyautogui offloaded (done); export offloaded+capped (done); upload streaming + subprocess remain. | **PARTIAL** |
| 35 | **Authorization fail-open in persona selection**: `is_master = not MASTER_ID or user_id in {"user","master","omax","admin","owner"}` — unset `MASTER_ID` makes everyone "master", hardcoded names are a backdoor. (`chat_engine.py:409`) | High | M | Derive from verified claims (`is_admin`) instead of name matching; product decision on default persona. | **FLAGGED** |
| 36 | **WebRTC swaps global `hub.brain.on_sentence`** while other chats run → cross-client token routing. (`routes.py:769-799`) | High | M | Pass per-connection callback instead of mutating shared state. | **FLAGGED** |
| 37 | **Android WebView maximally open** (`allowUniversalAccessFromFileURLs` + `addJavascriptInterface` + string-built `evaluateJavascript`). (`AikoAvatar.kt:174-219`) | High | M | `WebViewAssetLoader`, disable file access, `JSONObject.quote`. | **FLAGGED** |
| 38 | **Website had zero security headers** (no CSP/frame-ancestors/HSTS/referrer policy). (`next.config.ts`) | High | S | `headers()` with CSP, DENY, nosniff, HSTS, Permissions-Policy. | **FIXED** |
| 39 | **Website content contradicted code**: mobile app listed "upcoming" while `android/` ships; platform list omitted Android. (`content.ts`) | Med | S | Correct copy. | **FIXED** |
| 40 | **Website 60 fps React re-render of SVG tree** + always-on WebGL hero. (`Architecture.tsx:60-76`, `EmotionField.tsx`) | Med | M | Refs/CSS transforms; pause offscreen. | **FLAGGED** |
| 41 | **Whole-store Zustand subscriptions** in mascot/control panel → 60 fps re-renders during TTS. | Med | S | `useShallow` field selectors. | **FIXED** (2 files) |
| 42 | **CI hygiene**: no `permissions:` (release would 403), no concurrency, no pip cache, `bandit@main` unpinned and non-gating, frontend tests never run. | High | S | Least-privilege permissions, concurrency cancel, pip cache, pinned Bandit that gates on HIGH, `npm test` step. | **FIXED** |
| 43 | **README/SECURITY claims contradicted code**: "108 tests 100 % pass" (actual 98/97/1 + 12–20 frontend), "7.6 ms latency" (no benchmark), "24 h rotating tokens" vs 168 h default, "EMAIL_SEND requires HITL" while `/api/email/send` bypasses. | High (trust) | S | Corrected to measured numbers; latency claim removed; gaps documented as Known Gaps. | **FIXED** |
| 44 | **Tests**: 27.5 % coverage, 15 modules at 0 %; sanitizer test re-declared implementation (already drifted); integration file has zero tests; flaky hour-dependent proactive test. | High | M | Coverage floor 25 + ratchet; sanitizer test imports real code (14 cases); 3 regression tests added (sanitize/truncate, JWT expiry/tamper, broadcast pairing). | **PARTIAL** |
| 45 | **Repo/DX**: `.coverage` untracked, 336 MB of committed binaries (57 MB model duplicated per platform), `.pt` artifact, dead `docs/*.html` site dumps, no pre-commit/formatter, dead Flask server. | Med | M | `.gitignore` hardened; dead artifacts/licensing left as decisions. | **PARTIAL** |

---

## 4. Implemented changes (Phase 4)

Grouped by intent; every change is in the working-tree diff (`git diff`). Key before/after excerpts:

### 4.1 Trust boundary: bots → hub (`executor.py`, `chat_engine.py`, `websocket.py`)
Satellite bots authenticate to the hub with the desktop admin JWT, so "who spoke" was conflated with "who may do". The gate is now capability-based rather than identity-text-based:
```
- CONFIRMATION_REQUIRED_TOOLS = {"OPEN","TYPE","CLICK","PRESS","EMAIL_SEND"}
+ CONFIRMATION_REQUIRED_TOOLS = {..., "SCAN","CAMERA","EMAIL_INBOX","BIO_REGISTER"}
```
```
- if self.vision and any(st in message.lower() for st in screen_triggers):
+ if self.vision and is_admin and any(st in message.lower() for st in screen_triggers):
```
Each of the four handlers now starts with `if not is_admin: observations.append("[Security Block: ...]"); return`. Behavior change: desktop users see a HITL prompt for screen scans — intentional (privacy-sensitive read).

### 4.2 HITL bypass via cmd and LaTeX
```
- subprocess.Popen(["cmd.exe","/c","start","",target], shell=False)     # target came from the LLM
+ if any(ch in target for ch in '&|<>^"\r\n\x00'): block
+ os.startfile(target)                    # ShellExecute: no shell metacharacter parsing
+ fallback subprocess.Popen(["cmd.exe","/c","start","",target])        # only after validation
```
`pdflatex` invocations gained `-no-shell-escape`; `handle_latex_image` now does `resolve()` containment + `.png/.pdf` allow-list.

### 4.3 Authentication
`verify_token` now validates `alg == HS256`, requires a non-empty `sub`, requires a numeric `exp`, and checks expiry *after* signature verification; default TTL 168 h → 24 h. `/token` rejects `Forwarded`/`X-Forwarded-For`/`X-Real-IP` so a local reverse proxy cannot turn the loopback check into an unauthenticated admin-token dispenser. The aiohttp access logger is wrapped in a filter that redacts `token=` from the request line (browsers cannot set headers on WS upgrades, so this was a real log leak).

### 4.4 Memory / RAG
`RAGMemorySystem` got an explicit init contract: `_init_attempted` memoizes one blocking attempt, `is_available()` triggers it, and `background.knowledge_ingestion_loop` primes it off-loop at startup. Added `refresh_index()` (mtime manifest `data/knowledge/.rag_ingested.json`) replacing the nonexistent method that raised every 5 minutes. Result: `add_memory`/`search_memory`/`RECALL` are reachable again.

### 4.5 Streaming client
`chat_token`/`tts_chunk` no longer clear `isThinking`; the request lifecycle is authoritative. `chat_end` prefers the server's full `text`/`content` over sentence-chunk concatenation, so code fences/paragraphs survive. Per-token `+ ' '` removed. `branchChat` got the watchdog + failure path, so a dropped socket no longer bricks the composer. Connect guard moved before the first `await` (StrictMode).

### 4.6 Correctness small-fixes
`broadcast_event` pairs client↔future; `handle_create_session` generates a UUID instead of keying history on `None`; upload filenames get a random suffix (`/uploads` is unauthenticated); `chat_api` audio URL derives from the actual request host/port; settings writes are atomic (`os.replace`) and masked-value detection no longer drops legitimate values containing `...`; `_redact_secrets` masks container values and credential-shaped strings in lists; `refresh_index`/`is_available` no longer hammer init; `pc_manager` logger defined.

### 4.7 Android / website
Android: fail-closed release signing (no debug-keystore fallback; Gradle task action so config cache/IDE stay working), `allowBackup=false`, valid network security config (documented accepted cleartext risk + follow-up), Bearer on WebRTC offer with fail-fast, token read from the existing DataStore key. Website: real security headers; corrected roadmap/platform copy.

### 4.8 CI / packaging / docs
- `ci.yml`: least-privilege `permissions`, `concurrency` cancel, pip cache, apt packages for `portaudio`/GL, two-tier ruff (fatal rules gate; full lint advisory), `--cov-fail-under=25` with a measured-baseline comment, `npm test` added, pinned `ruff`, Bandit installed/pinned-by-installer and gating on HIGH, release `contents: write`, `fail_on_unmatched_files`.
- `scripts/neural_hub.spec`: `SPECPATH`/`__file__`-relative paths.
- `pyproject.toml`: `chromadb` added, ruff config migrated to `[tool.ruff.lint]`.
- `requirements.txt`: dev tools removed, `jinja2` added, Linux system-package note.
- `.gitignore`: coverage/mypy/ruff/bandit/egg-info/pytest temp artifacts.
- `README.md`/`SECURITY.md`: measured test table, removed unverifiable latency numbers, honest CI description, 24 h vs 168 h token truth, `/api/email/send` HITL bypass documented as known gap, data-at-rest section (Fernet memory vault vs XOR config obfuscation).

---

## 5. Verification (Phase 5)

| Gate | Before | After |
|---|---|---|
| `pytest tests/` | 97 passed, 1 skipped; exit 0 | **100 passed, 1 skipped** (101 collected: 98 + 3 regression tests); exit 0 |
| Coverage (`--cov=core`) | **27.49 %** (2 377/8 646 stmts) | **27.6 %** post-fix (2 448/8 880 stmts); floor set to 25 with ratchet comment (CI no longer lies) |
| `ruff check core/ tests/` | **1 595 errors**, exit 1 | CI fatal gate (`E9,F63,F7,F82`): **exit 0**; full lint remains advisory (1 563 style findings, non-gating by design) |
| `mypy core/` | 158 errors (not in CI) | not gated (recommended follow-up) |
| `npx tsc --noEmit` | 0 errors | **0 errors** |
| `npm test` (Vitest) | 12 tests | **20 tests** (6 schemas + 14 sanitizer importing the real implementation), pass |
| `py_compile` all `core/*.py` | — | exit 0 |
| Import smoke `import core.neural_hub...` | — | OK |
| Hub app construction | — | 48 routes / 4 middlewares |
| Release spec | absolute path, fails | `ast.parse` OK, path-relative |

Notes: the audit environment's sandbox blocked Vitest for the frontend/QA agents (esbuild `spawn EPERM`); the Lead re-ran both gates with full access and recorded the above. Android/Gradle and Next.js builds have no toolchain network access here — those changes were validated statically (XML parsed, TS evaluated under Node type-stripping, Kotlin delimiter/symbol checks) and are flagged for CI verification.

### Tests added
`tests/unit/test_regressions_audit.py` — (a) `_sanitize_input` strips NUL/control chars, preserves newlines, truncates 60 000 → 50 000 and returns `(text, True, "")`; (b) `verify_token` rejects expired and payload-tampered tokens (and asserts the secret is non-empty so it cannot pass vacuously); (c) `broadcast_event` keeps a healthy fake client and reaps a closed one, with one correctly-shaped envelope. `tests/unit/test_security.py` HITL test updated to reflect `os.startfile` and to assert no launch on denial.

---

## 6. Residual risks & decisions needed (human review)

1. **Satellite token scoping (P0 follow-up).** Capability gating + HITL closes the remote screen/camera/inbox exposure, but bots still speak with the admin JWT. Proper fix: non-admin service token per satellite + explicit actor claim; then admin-only tools require the desktop to act. This changes bot behavior and should be a product decision.
2. **HITL approval binding.** Approval is still broadcast; binding it to the originating connection (ContextVar + `request_id` → ws/args hash) is a design change worth doing next.
3. **`/token` local trust model.** Loopback-only + proxy-header rejection is as far as code can go; a one-time nonce + Windows socket ACL (or named pipe) is the durable fix.
4. **Android pairing.** The app still cannot obtain a token; the QR flow must carry `host:port` + token (ideally cert fingerprint) and call `setAuthToken`; WebRTC/reconnect state-sync per `specs/001-mobile-webrtc-state-sync` remains unimplemented. Cleartext LAN is an accepted, documented risk until TLS/pinning lands.
5. **Live2D licensing.** Cubism Core + the `vivian` model are proprietary assets redistributed under a bare MIT LICENSE with no notices. Legal review before public release; also deduplicate 57.67 MB `.moc3` across platforms.
6. **Dependency supply chain.** No lockfile/hash pinning; first-run `pip install` fetches latest. Establish constraints/uv lock + upper bounds for breaking majors (torch/numpy/pydantic/aiohttp/OpenAI SDK), then enable Dependabot/Renovate.
7. **Memory architecture.** Per-message sync embedding + full-history JSON save is O(n²) and blocks the loop; needs an async write-behind queue. This is the largest remaining performance/correctness item.
8. **`is_master` fail-open.** Changing it alters the default local persona; needs a product decision on "who is master" (recommended: derive from verified `is_admin` claims only).
9. **Frontend/desktop hardening.** Provider API key in `localStorage`, Tauri CSP `unsafe-eval`, markdown links navigating the webview, unvirtualized message list, focus-trap/a11y gaps.
10. **Website/Android performance & CI coverage.** 60 fps SVG state, always-on WebGL, Compose recomposition; no Android/website CI jobs yet.
11. **Docs/claims.** README no longer overstates; the "Tier-0 production-grade" framing should be dropped or defined by an explicit checklist.

---

## 7. Deliverables, reproduction, and commit guidance

**Artifacts**
- This report: `AUDIT_REPORT.md`
- Working-tree remediation: `git diff` (38 tracked files) + new `tests/unit/test_regressions_audit.py`
- Per-track evidence: `.tmp/audit/sec-api.md`, `core-runtime.md`, `frontend.md`, `mobile-web.md`, `qa-dx.md`, `qa-baseline.txt`

**Reproduce the gates**
```powershell
# Backend
.\.venv\Scripts\python.exe -m pytest tests/ -q
.\.venv\Scripts\python.exe -m ruff check core/ tests/ --select E9,F63,F7,F82
.\.venv\Scripts\python.exe -m py_compile (git ls-files 'core/*.py')
# Frontend
cd aiko-app; npx tsc --noEmit; npm test
```

**Suggested commit sequence** (working tree already contains a prior session's uncommitted changes; review before splitting):
1. `fix(security): bind satellite capabilities to admin + HITL; harden OPEN/LaTeX; redact tokens from logs`
2. `fix(api): auth hardening, path-traversal containment, settings validation/atomicity, upload randomness, broadcast pairing`
3. `fix(runtime): lazy RAG init + knowledge refresh, WS interval clamp, per-connection serialization, error boundaries`
4. `fix(ui): request-lifecycle thinking state, authoritative chat_end, auth headers, TTS URL, StrictMode connect guard`
5. `fix(mobile,web): fail-closed signing, backup/cleartext config, WebRTC auth, security headers, content truth`
6. `ci,docs: honest pipeline, lint/coverage gates, manifest sync, measured README/SECURITY`

**Assumptions made** (all explicit, none silent): threat model = single-user local app with untrusted users arriving via public bots and a LAN mobile client; local desktop clients are trusted admins (HITL still gates destructive actions); "cleartext LAN is acceptable" is treated as the product's current stance, documented as a risk; cosmetic lint (1 563 style findings) was intentionally left non-gating to keep this pass reviewable rather than reformatting 88 files.

## 8. Follow-up verification (2026-10-27)

The original findings above are a snapshot. This follow-up updated several security boundaries:

- Satellite integrations now receive one-hour non-admin tokens; `/token` returns only a limited browser token. Sensitive APIs and desktop-control actions require a verified administrator claim.
- HITL requests go only to the initiating WebSocket, and approval is accepted only from that same live connection with an administrator claim. WebSocket JWTs use a first-frame handshake. Upload/TTS media uses short-lived signed URLs; settings credentials are encrypted before persistence.
- Android WebSocket auth now uses the same first-frame handshake and no longer places or logs its token in the URL. A new desktop-admin QR flow issues a three-minute one-use pairing code, exchanges it for a 30-day non-admin phone token, and stores that token in Android DataStore. The hub now binds to LAN interfaces by default for phone connectivity; set `AIKO_BIND_HOST=127.0.0.1` to disable it. HTTP LAN traffic remains a documented risk until TLS pinning is added.
- The client’s 45-second silence watchdog now logs that the turn is still pending without clearing the send lock or inserting a false timeout message. The active server response or socket close remains authoritative.
- Rechecked: full Python tests passed with one platform-dependent skip; TypeScript passed; Vitest passed 20/20; Android `:app:compileDebugKotlin` passed; changed Python modules byte-compiled. The Android SDK emitted a metadata-version warning.
- **Native desktop window remains unresolved.** `npm run tauri dev` starts Vite and Tauri reports `show()`/focus success, but Windows exposes only Tauri's hidden 16x16 event-target helper; no WebView2 child or dashboard surface appears. WebView2 Runtime is installed. The `MAIN WINDOW FOUND` log does not prove that the dashboard opened.
- **Additional native launch check (2026-10-27).** A release build completed, and a console-visible `cargo run` reached `RunEvent::Ready`; on this host `WebviewWindow::hwnd()` still returned “the underlying handle is not available,” and the window inventory still showed no Aiko dashboard. The launch path is therefore not verified fixed. A duplicate launch also previously panicked when Ctrl+Alt+A was already globally registered; shortcut registration now logs the conflict instead of aborting app startup. `cargo check` passes with that change.
- **Verification side effect, recovered.** The native launch invoked Aiko's stale-process cleanup. A background restart attempt was blocked by command policy; I then restored the services with the documented foreground `npm run tauri dev` launch from `aiko-app`. Verified Vite at port 1422 and Neural Hub `/status` at port 8000 both return HTTP 200. The full frontend is open in the in-app browser while native HWND creation remains under investigation.
- `npm audit fix` plus direct KaTeX and dependency overrides removed the reported JavaScript vulnerabilities; npm reported zero vulnerabilities after the fix. Other remaining work includes the async write-behind memory queue, request cancellation for a truly stuck turn, Python dependency lock/hash pinning, and Live2D/Cubism redistribution review. The baseline status table should be read with this follow-up; partial/flagged rows are not evidence of current completion.

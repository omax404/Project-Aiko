# Aiko Professionalization Roadmap

## Target State: Professional Product
- **Secure** — Zero hardcoded secrets, proper auth, sandboxed execution
- **Reliable** — Tested, CI/CD, graceful error handling, observability
- **Scalable** — Modular architecture, not a monolith
- **Shippable** — Clean builds, signed releases, proper packaging
- **Maintainable** — Clear code, docs, no personal references

---

## Phase 1: Security & Foundation (Weeks 1-4)
**Goal: Make it safe to expose to users.**

### 1.1 Secret Management
- [ ] Remove ALL hardcoded secrets (`security.py`, `user_settings.json`, `proactive.py`, `memory.py`)
- [ ] Implement a proper secret vault (keyring on desktop, env vars for server)
- [ ] Remove `.env` from git history (`git filter-branch` or BFG)
- [ ] Add `.env` to `.gitignore` properly
- [ ] Generate new API keys (the old ones are leaked in git history)

### 1.2 Authentication & Authorization
- [ ] Add JWT token validation to `neural_hub.py` REST API
- [ ] Add WebSocket auth handshake
- [ ] Role-based access control (User vs Admin vs Master)
- [ ] Remove hardcoded `omax`/`omax404` master checks — make it configurable
- [ ] Discord/Telegram bot: verify admin via config, not hardcoded usernames

### 1.3 MCP Sandbox Hardening
- [ ] Replace path-prefix checks with `pathlib.Path.resolve()` + `os.path.realpath()`
- [ ] Add file operation audit logging
- [ ] Restrict dangerous operations (delete, write outside home) behind explicit user confirmation
- [ ] Add a "safe mode" toggle for users who don't want PC control at all

### 1.4 Input Validation
- [ ] Add Pydantic models for all API inputs
- [ ] Sanitize agent command parsing (currently regex-based, needs structured schemas)
- [ ] Rate limiting on public endpoints

---

## Phase 2: Architecture & Testing (Weeks 5-8)
**Goal: Make it maintainable and testable.**

### 2.1 Modularization
- [ ] Extract `neural_hub.py` into:
  - `api/routes.py` — FastAPI/HTTP routes
  - `api/websocket.py` — WebSocket manager
  - `services/broadcast.py` — Event broadcasting
- [ ] Extract `chat_engine.py` into:
  - `services/llm_client.py` — LLM communication
  - `services/agent_executor.py` — Tool execution
  - `services/persona_manager.py` — Prompt construction
- [ ] Dependency injection container (replace global imports)

### 2.2 Testing Framework
- [ ] Add `pytest` to dev dependencies
- [ ] Write unit tests for `security.py`, `mcp_bridge.py`, `config_manager.py`
- [ ] Add integration tests for the chat flow (mock LLM)
- [ ] Add test coverage reporting (`pytest-cov`)
- [ ] CI pipeline: GitHub Actions running tests on every PR

### 2.3 Error Handling & Observability
- [ ] Replace bare `except Exception` with specific exception types
- [ ] Add structured logging (JSON) with correlation IDs
- [ ] Health check endpoint with dependency status (LLM, DB, TTS)
- [ ] Graceful shutdown handlers (SIGTERM/SIGINT)

---

## Phase 3: Build & Distribution (Weeks 9-12)
**Goal: Make it installable by normal users.**

### 3.1 Desktop (Tauri)
- [ ] Fix `aiko-app` build: lock npm deps, pin Rust versions
- [ ] Signed binaries (Windows code signing, macOS notarization)
- [ ] Auto-updater integration (Tauri updater)
- [ ] Remove `node_modules`/`target` from repo (add to `.gitignore`)

### 3.2 Docker
- [ ] Fix `docker-compose.yml` port mismatch
- [ ] Remove `sandbox` service dependency (or create the actual `sandbox/`)
- [ ] Multi-stage build optimization (reduce image size from ~4GB to <1GB)
- [ ] Non-root user in container (fix `chmod 777`)
- [ ] Docker health checks that actually work

### 3.3 Android
- [ ] Complete the scaffolded Android app (currently only 3 files)
- [ ] Implement actual API client connecting to Neural Hub
- [ ] Proper release signing config (not debug signing)
- [ ] Firebase/App Distribution for beta testing

### 3.4 Packaging
- [ ] `pip install aiko-desktop` (PyPI package)
- [ ] Windows MSI/NSIS installer
- [ ] macOS `.dmg`
- [ ] Linux AppImage or flatpak

---

## Phase 4: User Experience & Polish (Weeks 13-16)
**Goal: Make it delightful for paying users.**

### 4.1 Onboarding
- [ ] First-run wizard (API key setup, voice calibration, persona selection)
- [ ] In-app settings validation (test LLM connection before saving)
- [ ] Clear error messages when dependencies are missing (Ollama not found, etc.)

### 4.2 Monetization Prep (if applicable)
- [ ] License key validation system
- [ ] Feature tiers (Free vs Premium: cloud models, voice cloning, etc.)
- [ ] Telemetry (opt-in) for crash reporting and usage analytics

### 4.3 Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User manual (not just README)
- [ ] Developer contributing guide
- [ ] Architecture decision records (ADRs)

---

## Phase 5: Scale & Enterprise (Months 5-6)
**Goal: Make it viable for teams and businesses.**

- [ ] Multi-user support with proper isolation
- [ ] PostgreSQL backend option (instead of JSON files)
- [ ] Redis for message queuing
- [ ] Admin dashboard for managing instances
- [ ] Plugin marketplace with sandboxed plugins
- [ ] GDPR compliance (data export, deletion)

---

## Immediate First Steps (This Week)
1. **Decision**: Self-hosted only, or SaaS/cloud component too?
2. **Decision**: Open source or proprietary? (affects licensing strategy)
3. **Decision**: Single user per instance, or multi-user?
4. **Action**: I'll create a `security/` module and start removing hardcoded secrets
5. **Action**: Set up `pytest` and write first 5 tests

---

*Generated for Aiko Desktop professionalization project.*

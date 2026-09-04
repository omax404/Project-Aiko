# Contributing to Project Aiko

Thank you for your interest in contributing to Project Aiko! We welcome contributions across all domains: core AI algorithms, Live2D animations, native mobile, security, and satellite integrations.

---

## Code Standards & Architecture

Project Aiko adheres to **Tier-0 Production Grade** architecture:
- **Python Backend:** Python 3.10–3.12. All asynchronous routes and background tasks must be strictly non-blocking (`asyncio.to_thread` for CPU/IO-heavy work). All database operations must use parameterized queries (`?`).
- **Desktop Frontend:** React 19 + TypeScript + Tauri v2. Must pass `npx tsc --noEmit` with ultra-strict mode (`noUncheckedIndexedAccess: true`). Use atomic Zustand selectors and `React.memo` to prevent re-render cascades.
- **Contracts:** Schema models must be validated using **Zod** (frontend) and **Pydantic v2** (backend ingress).
- **Security:** Strict Zero-Trust standards. Any tool performing operating system execution or file manipulation must route through the Human-in-the-Loop (HITL) gate. Consult [SECURITY.md](SECURITY.md) for security policies.

---

## Development Workflow

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/omax404/Project-Aiko.git
   cd Project-Aiko
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```
3. Set up the desktop frontend:
   ```bash
   cd aiko-app
   npm install
   ```

---

## Running Tests

Before submitting a Pull Request, ensure all automated verification suites pass:

1. **Python Backend Test Suite:**
   ```bash
   pytest tests/
   ```
2. **Frontend Type Check (Ultra-Strict):**
   ```bash
   cd aiko-app
   npx tsc --noEmit
   ```
3. **Frontend Vitest Suite:**
   ```bash
   cd aiko-app
   npm test
   ```
4. **Desktop Production Build:**
   ```bash
   cd aiko-app
   npm run build
   ```

---

## Submitting Pull Requests

1. Create a feature branch (`git checkout -b feature/my-feature`).
2. Follow [Conventional Commits](https://www.conventionalcommits.org/) format (e.g. `feat:`, `fix:`, `perf:`, `docs:`).
3. Ensure no secrets, tokens, or personal paths are committed.
4. Push to your fork and submit a PR against `main`.

# Security Policy & Architecture - Project Aiko

This document defines the security architecture, threat model, authentication lifecycle, and policy enforcement implemented in Project Aiko.

---

## 1. Zero-Trust Security Architecture

Project Aiko authenticates protected API and WebSocket operations with signed, expiring tokens. Health checks and the loopback-only browser/satellite token handshakes are limited exceptions; loopback by itself does not grant the desktop administrator role.

### Authentication & Token Lifecycle
1. **JWT Handshake Tokens:**
   - Generated with HMAC-SHA256 using an isolated master secret stored with restricted filesystem permissions.
   - The desktop owner token is written to `data/local_token.txt` on startup, expires after 24 hours, and is retrieved by the native frontend through Tauri IPC. The loopback `/token` endpoint returns only a limited browser token.
   - `generate_token()` defaults to 24 hours. Satellite tokens have a one-hour lifetime.
   - Long-lived persistent tokens have been removed.
2. **Satellite Bots (Discord, Telegram, Twitch):**
   - Acquire a one-hour non-admin token from the loopback `/bot-token` endpoint. Bots never read the desktop owner-token file.
   - Chat identities are namespaced per bot and upstream user. Satellite credentials cannot access administrator-only APIs or PC-control tools.
   - On HTTP 401 responses, satellite bots automatically purge their cached credentials and acquire a fresh handshake token.
3. **Mobile Clients (Android App):**
   - Pair using a three-minute, one-use QR code minted by the desktop administrator. Redeeming it yields a 30-day non-admin mobile token. The QR is generated locally in the desktop UI; it is not sent to a third-party QR service.
   - Authenticate WebSockets with a token in the first data frame, keeping credentials out of request URLs. HTTP APIs use Authorization: Bearer headers.
   - Memory export and synchronization endpoints (/api/memory/export) strictly validate the Bearer token.

---

## 2. Server-Side Human-in-the-Loop (HITL) Permission Gate

To eliminate Remote Code Execution (RCE) and Indirect Prompt Injection risks (e.g., untrusted websites, documents, or screen content injecting malicious tool directives into the LLM context), Project Aiko enforces a mandatory server-side approval gate.

### Sensitive Tools Requiring Human Approval:
- **System OS & GUI Actions:** OPEN, TYPE, CLICK, PRESS
- **Privacy-sensitive reads:** SCAN, CAMERA, EMAIL_INBOX, BIO_REGISTER
- **Communication & Outbound Traffic:** EMAIL_SEND
- **Sensitive Model Context Protocol (MCP) Tools:** write_file, delete_file, kill_proc, run_cmd, set_clipboard, uia_click, uia_type

### Enforcement Rules:
- **No Master/Admin Bypass:** Confirmation applies to all callers, including the master user and administrative tokens. An attacker cannot bypass the approval gate by spoofing an admin prompt.
- **WebSocket Verification:** The Neural Hub sends the request only to the WebSocket that initiated the operation. It accepts an approval only from that same live connection with an administrator claim, and waits up to 30 seconds. Satellite clients cannot approve their own requests.
- If unapproved or timed out, execution is blocked:
  [TOOL_BLOCKED] Execution of <TOOL_NAME> was denied or timed out.

### Email send route
The direct `POST /api/email/send` endpoint is disabled. Email can only be sent through the chat tool flow, which requires approval on the WebSocket that initiated the request.

---

## 3. Configuration Redaction & Credential Isolation

The Neural Hub `/api/settings` endpoint redacts sensitive fields before returning settings and encrypts secret values before persistence:
- Keys matching known provider tokens (OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, DISCORD_TOKEN, TELEGRAM_TOKEN, TWITCH_TOKEN, SPOTIFY_CLIENT_SECRET, EMAIL_PASSWORD) are masked.
- Keys containing substrings SECRET, TOKEN, PASSWORD, PASSWD, CREDENTIAL, or PRIVATE are masked.
- Keys ending in _API_KEY, _SECRET_KEY, _PRIVATE_KEY, or _AUTH_KEY are masked.
- Redacted strings preserve up to 4 preview characters for troubleshooting while ensuring the secret payload is hidden:
  sk-p...***
  very...***

---

## 4. Data-at-Rest Protection

Two different mechanisms are used, and they are **not equally strong** — do not describe both as "encrypted":

1. **Memory vault — real encryption.** `core/security/cipher.py:MemoryCipher` uses **Fernet (AES-128-CBC + HMAC-SHA256)** with a 32-byte key derived via **PBKDF2-HMAC-SHA256, 480 000 iterations**, from a master secret (`AIKO_MASTER_SECRET`) plus a per-install salt (`AIKO_SALT`). Keys are read from the environment first, then from the generated `data/.aiko_secrets.json`. This protects episodic memory contents at rest.
2. **Configuration values — OS-backed protection.** Windows uses DPAPI scoped to the current Windows user. Other platforms use Fernet with a random local key file restricted to the current account where supported. Legacy XOR values remain readable for migration and are re-encrypted when settings are saved.

The hub listens on all local network interfaces by default so a paired phone can reach it. Protected API endpoints require bearer authentication; the one-use pairing exchange, non-sensitive status/health routes, and signed upload/TTS URLs are limited exceptions. Set `AIKO_BIND_HOST=127.0.0.1` to disable LAN access. Plain HTTP on the LAN remains a risk; use a trusted private network until HTTPS/WSS certificate pinning is added.

The non-Windows fallback key is stored beside configuration data, so it protects against casual file disclosure but not an attacker who can read both files. Keep the data directory out of version control and restrict account access.

---

## 5. Prompt Injection Defenses

The system implements multi-layer defense-in-depth against prompt injection:
1. **Regex & Heuristic Input Classification:** Scans incoming messages for system instruction bypass patterns, jailbreaks, and delimiter escapes.
2. **Bearer Token Scrubbing:** Text outputs generated by LLMs are filtered through sanitize_output() to automatically redact accidental leaks of Bearer tokens or sensitive headers.
3. **Peripheral Memory Privacy Filtering:** Screen OCR and ambient context monitoring blacklists password managers and private browsing windows (1password, bitwarden, keepass, incognito, inprivate, credit card).

---

## 6. Reporting Security Vulnerabilities

If you discover a potential security flaw in Project Aiko, please report it privately via GitHub Security Advisories or directly to the repository maintainer.

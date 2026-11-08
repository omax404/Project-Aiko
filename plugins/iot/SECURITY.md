# IoT plugin threat model

This plugin lets Aiko actuate allowlisted smart-home devices over MQTT. It is the
highest-consequence surface in the codebase after OS control: a wrong action can
unlock a door, disable a sensor or run a heater. The design therefore treats the
LLM as an **untrusted planner** and the local user as the only authority.

## Trust boundaries

| Principal | Trust | Notes |
|---|---|---|
| Local user (dashboard owner) | **Trusted** | Only principal who can approve an action. |
| Aiko's LLM / prompt context | **Untrusted planner** | May be manipulated by chat text, screen OCR, e-mail, web pages or a rogue MCP assistant. |
| MQTT broker | **Untrusted transport** | May be shared, plaintext or compromised; payloads are outbound-only and never executed. |
| Remote satellite users (Discord/Telegram/Twitch) | **Untrusted** | Their text reaches the LLM; it must not gain hardware authority. |
| Dashboard client | **Trusted UI, unverified identity** | Approval is only as good as the existing HITL gate (see residual risk R4). |

## Invariant (enforced in code)

> **No IoT publish happens without a fresh, per-action human confirmation that
> arrives *after* the action arguments are fully resolved.**

Implemented in `plugins/iot/plugin.py::IotPlugin.execute_tool`:

1. Tool name is looked up in the shipped capability manifest; unknown tools are
   rejected before any other work.
2. Device id is validated against `^[A-Za-z0-9_-]{1,64}$` **and** must exist in
   the operator-supplied allowlist (`config["devices"]`). There is no
   discovery-by-topic: a device becomes controllable only by explicit config.
3. The requested scope (`read`/`write`/`toggle`) must be declared by the tool and
   permitted for that device.
4. The MQTT topic is constructed server-side from the allowlist entry — never
   from model output — and re-validated against a conservative charset. Wildcards
   (`+`, `#`) and null bytes are rejected by both the plugin and `MqttBridge.publish`.
5. `_request_confirmation()` calls the existing server-side
   `core.api.websocket.request_tool_permission` gate (or an injected equivalent in
   tests). The confirmation payload includes `device_id`, `device_name`, `action`,
   `scope`, `topic` and, for writes, the value. Failure to reach the gate, an
   exception, or a `False`/timeout result all **deny** the action (fail closed).
6. Only after approval is the JSON payload published. The return value is
   `[TOOL_BLOCKED] …` when denied and `[TOOL_ERROR] …` on transport failure, so the
   LLM observes a hard failure rather than a silent success.

`capabilities.json` is the dashboard's contract for rendering scope-aware prompts.
The manifest loader refuses manifests that declare `"required": false` or
`"auto_approve": true`.

## Attack classes considered

| Attack | Result |
|---|---|
| Prompt injection asks Aiko to "unlock the front door" | A HITL prompt appears with the exact device/topic/scope; without approval nothing is published. |
| Injured model supplies `device_id: "../../other/device"` | Rejected by the id regex / allowlist; no topic built from it. |
| Model supplies a topic or MQTT wildcard | Topic is server-constructed; wildcard/null bytes are rejected. |
| Repeat/replay of a previous approval | Approvals are per request id in the HITL gate; the plugin asks again for every call and never stores consent. |
| Malicious MQTT broker sends crafted messages | The plugin never subscribes to or executes inbound payloads; it is publish-only. |
| Rogue MCP assistant delegates an IoT action | The assistant still goes through this plugin, so the same per-action gate applies — trust is not inherited. |
| Scope escalation (`toggle` → `write`) | Each tool declares one scope; devices may narrow it with `allowed_scopes`. |
| Denial-of-service by spamming confirmations | Each action maps to one confirmation and the existing HITL timeout bounds the wait; no auto-approve exists. |

## Non-goals / known residual risks

- **R1 — Broker compromise.** MQTT is the trust boundary to the hardware. Use TLS
  (`use_tls: true` / `IOT_MQTT_TLS=true`), unique broker credentials and network
  segmentation for anything safety-relevant. Plain MQTT exposes payloads on the LAN.
- **R2 — Device semantics.** A `toggle` cannot express "lock" vs "unlock"; encode
  high-stakes devices as `set` with explicit values and restrict scopes.
- **R3 — Approval fatigue.** The gate is only effective if the user reads it. The
  manifest ships a prompt template that names the device and scope; never enable
  many devices you would approve blindly.
- **R4 — Approval identity.** The HITL gate is connection-scoped (see
  `docs/security/hitl-threat-model.md`, P3.1). A second authenticated client can
  answer a confirmation; binding approvals to the originating connection is the
  planned follow-up.
- **R5 — Credentials at rest.** Broker credentials come from config/env; protect
  the config file and prefer short-lived broker accounts.

## Verification

`tests/unit/test_iot_plugin.py` asserts, among others:

- a toggle **without** an approved `tool_request` returns a hard
  `[TOOL_BLOCKED]` error and never calls `publish`;
- a denied or failing confirmation fails closed;
- confirmation happens **per action** (two calls → two confirmations), with the
  resolved device/scope/topic in the prompt arguments;
- unknown devices, invalid ids, disallowed scopes and unsafe topics are rejected;
- publish failures surface as `[TOOL_ERROR]`, never as success;
- the manifest cannot be configured for auto-approve.

"""HITL-gated IoT plugin (generic MQTT transport).

Security invariant: every device action — read, write or toggle — is routed
through Aiko's server-side ``tool_request`` confirmation flow immediately before
publishing. There is deliberately no per-device "remember" that bypasses the
gate, so prompt-injected content cannot actuate hardware without the user
approving that exact action.
"""
from __future__ import annotations

import inspect
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from core.plugins.base import AikoPlugin

from .mqtt_bridge import MqttBridge, MqttBridgeError

logger = logging.getLogger("IoT")

CAPABILITIES_PATH = Path(__file__).with_name("capabilities.json")
DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
TOPIC_RE = re.compile(r"^[A-Za-z0-9._/-]{1,200}$")
_TOPIC_ACTION = {"read": "read", "write": "set", "toggle": "toggle"}

ConfirmFn = Callable[[str, Dict[str, Any]], Any]


def load_capabilities(path: Path = CAPABILITIES_PATH) -> Dict[str, Any]:
    """Load and validate the plugin capability manifest."""
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("capabilities manifest must be an object")
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported capabilities schema_version")
    tools = manifest.get("tools")
    scopes = manifest.get("scopes")
    if not isinstance(tools, list) or not tools:
        raise ValueError("capabilities manifest must declare tools")
    if not isinstance(scopes, dict) or not scopes:
        raise ValueError("capabilities manifest must declare scopes")
    for tool in tools:
        if not isinstance(tool, dict) or not tool.get("name"):
            raise ValueError("every tool needs a name")
        if tool.get("scope") not in scopes:
            raise ValueError(f"tool {tool.get('name')} declares an unknown scope")
        if not isinstance(tool.get("parameters"), dict):
            raise ValueError(f"tool {tool.get('name')} needs a parameter schema")
    confirmation = manifest.get("confirmation")
    if not isinstance(confirmation, dict) or confirmation.get("required") is not True:
        raise ValueError("IoT capabilities must require per-action confirmation")
    if confirmation.get("auto_approve") is True:
        raise ValueError("auto-approve is forbidden for IoT tools")
    return manifest


class IotPlugin(AikoPlugin):
    """Controls allowlisted MQTT devices, one confirmed action at a time."""

    name = "IoT"
    description = "HITL-gated MQTT smart-home control"

    def __init__(
        self,
        config: Dict[str, Any] = None,
        confirm: Optional[ConfirmFn] = None,
        bridge: Optional[MqttBridge] = None,
    ) -> None:
        super().__init__(config)
        self._confirm = confirm
        self._bridge = bridge
        self._manifest: Dict[str, Any] = {}
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._scopes: Dict[str, str] = {}
        self._devices: Dict[str, Dict[str, Any]] = {}
        self._topic_prefix = "aiko/devices"
        self._qos = 1

    # ------------------------------------------------------------------ setup
    async def initialize(self) -> bool:
        try:
            self._manifest = load_capabilities()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.error("IoT capabilities manifest is invalid: %s", exc)
            return False

        self._tools = {tool["name"]: tool for tool in self._manifest["tools"]}
        self._scopes = dict(self._manifest["scopes"])

        cfg = self.config or {}
        devices = cfg.get("devices")
        if not isinstance(devices, dict) or not devices:
            logger.warning("IoT plugin has no device allowlist configured; staying inactive.")
            return False
        self._devices = devices

        host = cfg.get("host") or os.getenv("IOT_MQTT_HOST", "")
        if not host:
            logger.warning("IoT plugin has no MQTT host configured; staying inactive.")
            return False

        self._topic_prefix = cfg.get("topic_prefix") or self._manifest["transport"]["topic_prefix"]
        self._qos = int(cfg.get("qos", self._manifest["transport"].get("qos", 1)))

        if self._bridge is None:
            self._bridge = MqttBridge(
                host=host,
                port=int(cfg.get("port") or os.getenv("IOT_MQTT_PORT", 1883)),
                username=cfg.get("username") or os.getenv("IOT_MQTT_USERNAME"),
                password=cfg.get("password") or os.getenv("IOT_MQTT_PASSWORD"),
                use_tls=bool(cfg.get("use_tls") or os.getenv("IOT_MQTT_TLS", "").lower() == "true"),
            )
            try:
                self._bridge.connect()
            except MqttBridgeError as exc:
                logger.error("IoT MQTT connection failed: %s", exc)
                return False

        self.is_active = True
        logger.info("IoT plugin active with %d allowlisted device(s).", len(self._devices))
        return True

    async def shutdown(self) -> None:
        if self._bridge is not None:
            self._bridge.close()
        await super().shutdown()

    # ------------------------------------------------------------- tool surface
    def get_tools(self) -> List[Dict[str, Any]]:
        if not self.is_active:
            return []
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            for tool in self._tools.values()
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if not self.is_active:
            return "[TOOL_ERROR] IoT plugin is not configured (no broker/allowlist)."

        spec = self._tools.get(tool_name)
        if spec is None:
            return f"[TOOL_ERROR] Unknown IoT tool: {tool_name}"

        args = dict(arguments or {})
        device_id = str(args.get("device_id") or "")
        if not DEVICE_ID_RE.match(device_id):
            return "[TOOL_BLOCKED] Invalid or missing device id."

        device = self._devices.get(device_id)
        if not isinstance(device, dict):
            return f"[TOOL_ERROR] Device '{device_id}' is not in the allowlist."

        scope = str(spec["scope"])
        allowed_scopes = device.get("allowed_scopes") or list(self._scopes)
        if scope not in allowed_scopes:
            return f"[TOOL_BLOCKED] Scope '{scope}' is not allowed for device '{device_id}'."

        if scope == "write":
            if "value" not in args:
                return "[TOOL_ERROR] iot.device.set requires a 'value'."
            value = args["value"]
            if not isinstance(value, (str, int, float, bool)):
                return "[TOOL_BLOCKED] Device values must be a string, number or boolean."

        base_topic = str(device.get("topic") or device_id)
        action = _TOPIC_ACTION[scope]
        topic = f"{self._topic_prefix}/{base_topic}/{action}"
        if not TOPIC_RE.match(topic):
            return "[TOOL_BLOCKED] Refusing to publish to an unsafe MQTT topic."

        # ---------------------------------------------------------- HITL gate
        confirmation_args: Dict[str, Any] = {
            "device_id": device_id,
            "device_name": device.get("name", device_id),
            "action": tool_name,
            "scope": scope,
            "topic": topic,
        }
        if scope == "write":
            confirmation_args["value"] = args["value"]

        approved = await self._request_confirmation(tool_name, confirmation_args)
        if not approved:
            logger.warning("IoT action denied by HITL gate: %s on %s", tool_name, device_id)
            return (
                f"[TOOL_BLOCKED] Execution of {tool_name} on '{device_id}' was denied "
                "or timed out."
            )

        payload: Dict[str, Any] = {
            "source": "aiko",
            "action": action,
            "device_id": device_id,
        }
        if scope == "write":
            payload["value"] = args["value"]

        try:
            assert self._bridge is not None
            self._bridge.publish(topic, payload, qos=self._qos)
        except MqttBridgeError as exc:
            return f"[TOOL_ERROR] MQTT action failed: {exc}"

        logger.info("IoT action approved and published: %s -> %s", tool_name, topic)
        return json.dumps(
            {"status": "ok", "device_id": device_id, "scope": scope, "topic": topic}
        )

    # ------------------------------------------------------------------ helpers
    async def _request_confirmation(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """Ask the server-side HITL gate. Fails closed if the gate is unavailable."""
        confirm = self._confirm
        if confirm is None:
            try:
                from core.api.websocket import request_tool_permission
            except Exception as exc:  # pragma: no cover - import-environment specific
                logger.error("HITL gate unavailable; denying IoT action: %s", exc)
                return False
            confirm = request_tool_permission

        try:
            result = confirm(tool_name, args)
            if inspect.isawaitable(result):
                result = await result
            return bool(result)
        except Exception as exc:
            logger.error("HITL confirmation failed; denying IoT action: %s", exc)
            return False

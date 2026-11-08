"""Minimal, injectable MQTT transport for the IoT plugin.

The transport is deliberately thin: connect, publish, close. It never subscribes
to arbitrary topics and never executes inbound payloads. ``paho-mqtt`` is an
optional-at-runtime dependency (declared in requirements.txt) and is imported
lazily so the rest of Aiko can run without an MQTT stack; a client factory can be
injected for tests.
"""
from __future__ import annotations

import importlib
import json
import logging
import ssl
from typing import Any, Callable, Optional

logger = logging.getLogger("IoT.MQTT")


class MqttBridgeError(RuntimeError):
    """Raised when the MQTT transport cannot satisfy a request."""


class MqttBridge:
    """Thin MQTT publisher with TLS support and an injectable client factory."""

    def __init__(
        self,
        host: str,
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = False,
        keepalive: int = 30,
        client_factory: Optional[Callable[[], Any]] = None,
    ) -> None:
        self.host = (host or "").strip()
        self.port = int(port)
        self.username = username or None
        self.password = password or None
        self.use_tls = bool(use_tls)
        self.keepalive = int(keepalive)
        self._client_factory = client_factory
        self._client: Any = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None

    def _default_client_factory(self) -> Callable[[], Any]:
        try:
            mqtt = importlib.import_module("paho.mqtt.client")
        except ImportError as exc:  # pragma: no cover - depends on install extras
            raise MqttBridgeError(
                "paho-mqtt is not installed; run `pip install -r requirements.txt` "
                "or `pip install paho-mqtt>=2.0.0`"
            ) from exc
        api_version = getattr(mqtt, "CallbackAPIVersion", None)
        if api_version is not None:
            return lambda: mqtt.Client(api_version.VERSION2)
        return mqtt.Client  # paho-mqtt 1.x compatibility

    def connect(self) -> bool:
        """Connect to the broker. Raises MqttBridgeError on failure."""
        if not self.host:
            raise MqttBridgeError("MQTT host is not configured")
        factory = self._client_factory or self._default_client_factory()
        client = factory()
        try:
            if self.username:
                client.username_pw_set(self.username, self.password)
            if self.use_tls:
                client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
            client.connect(self.host, self.port, self.keepalive)
            client.loop_start()
        except MqttBridgeError:
            raise
        except Exception as exc:
            raise MqttBridgeError(f"MQTT connection to {self.host}:{self.port} failed: {exc}") from exc
        self._client = client
        self._connected = True
        logger.info("Connected to MQTT broker at %s:%s (tls=%s)", self.host, self.port, self.use_tls)
        return True

    def publish(self, topic: str, payload: dict, qos: int = 1) -> int:
        """Publish a JSON payload to an exact topic. Raises on failure."""
        if not self.is_connected:
            raise MqttBridgeError("MQTT transport is not connected")
        if not topic or any(token in topic for token in ("+", "#", "\x00")):
            raise MqttBridgeError("Refusing to publish to a wildcard or empty topic")
        message = json.dumps(payload, separators=(",", ":"))
        try:
            info = self._client.publish(topic, message, qos=int(qos))
        except Exception as exc:
            raise MqttBridgeError(f"MQTT publish to {topic!r} failed: {exc}") from exc
        rc = getattr(info, "rc", 0)
        if rc != 0:
            raise MqttBridgeError(f"MQTT publish to {topic!r} returned rc={rc}")
        return int(rc)

    def close(self) -> None:
        """Stop the network loop and disconnect. Safe to call twice."""
        client, self._client = self._client, None
        self._connected = False
        if client is None:
            return
        try:
            client.loop_stop()
        except Exception as exc:  # pragma: no cover - transport-specific
            logger.debug("MQTT loop_stop failed: %s", exc)
        try:
            client.disconnect()
        except Exception as exc:  # pragma: no cover - transport-specific
            logger.debug("MQTT disconnect failed: %s", exc)

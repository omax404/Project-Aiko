"""IoT plugin: a HITL-gated, generic MQTT bridge for smart-home devices.

Every device action requires a fresh human confirmation through Aiko's existing
``tool_request`` flow; there is no "remember this device" auto-approve. See
``SECURITY.md`` for the threat model.
"""
from .mqtt_bridge import MqttBridge, MqttBridgeError
from .plugin import IotPlugin

__all__ = ["IotPlugin", "MqttBridge", "MqttBridgeError"]

"""Tests for the HITL-gated IoT/MQTT plugin (no broker or network required)."""
from __future__ import annotations

import importlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from plugins.iot.mqtt_bridge import MqttBridge, MqttBridgeError
from plugins.iot.plugin import DEVICE_ID_RE, IotPlugin, load_capabilities

CAPABILITIES = importlib.import_module("plugins.iot.plugin").CAPABILITIES_PATH


class FakeBridge:
    def __init__(self) -> None:
        self.published = []
        self.closed = False

    def publish(self, topic: str, payload: dict, qos: int = 1) -> int:
        self.published.append((topic, payload, qos))
        return 0

    def close(self) -> None:
        self.closed = True


class FakeBrokerClient:
    def __init__(self) -> None:
        self.connected = None
        self.published = []
        self.loop_started = False
        self.loop_stopped = False
        self.disconnected = False
        self.credentials = None
        self.tls = None

    def username_pw_set(self, username, password=None):
        self.credentials = (username, password)

    def tls_set(self, **kwargs):
        self.tls = kwargs

    def connect(self, host, port, keepalive):
        self.connected = (host, port, keepalive)

    def loop_start(self):
        self.loop_started = True

    def loop_stop(self):
        self.loop_stopped = True

    def disconnect(self):
        self.disconnected = True

    def publish(self, topic, message, qos=1):
        self.published.append((topic, message, qos))
        return SimpleNamespace(rc=0)


CONFIG = {
    "host": "broker.local",
    "devices": {
        "lamp": {"name": "Desk Lamp", "topic": "lamp"},
        "kettle": {"name": "Kettle", "topic": "kettle", "allowed_scopes": ["toggle"]},
    },
}


@pytest.fixture
def bridge():
    return FakeBridge()


@pytest.fixture
def confirm():
    return AsyncMock(return_value=True)


@pytest.fixture
def plugin(bridge, confirm):
    return IotPlugin(config=CONFIG, confirm=confirm, bridge=bridge)


async def _active(plugin):
    assert await plugin.initialize() is True
    return plugin


# ------------------------------------------------------------------ manifest
class TestCapabilities:
    def test_manifest_declares_three_scoped_tools(self):
        manifest = load_capabilities()
        names = {tool["name"] for tool in manifest["tools"]}
        assert names == {"iot.device.toggle", "iot.device.set", "iot.device.read"}
        assert set(manifest["scopes"]) == {"read", "write", "toggle"}
        assert manifest["confirmation"]["required"] is True

    def test_manifest_rejects_auto_approve(self, tmp_path):
        data = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        data["confirmation"]["auto_approve"] = True
        path = tmp_path / "capabilities.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="auto-approve"):
            load_capabilities(path)

    def test_manifest_rejects_unknown_scope(self, tmp_path):
        data = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        data["tools"][0]["scope"] = "admin"
        path = tmp_path / "capabilities.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="unknown scope"):
            load_capabilities(path)

    def test_manifest_rejects_missing_confirmation(self, tmp_path):
        data = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        data["confirmation"]["required"] = False
        path = tmp_path / "capabilities.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="confirmation"):
            load_capabilities(path)


# ----------------------------------------------------------------- lifecycle
class TestLifecycle:
    @pytest.mark.asyncio
    async def test_initialize_requires_device_allowlist(self, bridge):
        plugin = IotPlugin(config={"host": "broker.local"}, bridge=bridge)
        assert await plugin.initialize() is False
        assert plugin.is_active is False

    @pytest.mark.asyncio
    async def test_initialize_requires_host(self, bridge):
        plugin = IotPlugin(config={"devices": CONFIG["devices"]}, bridge=bridge)
        assert await plugin.initialize() is False

    @pytest.mark.asyncio
    async def test_initialize_activates_with_injected_bridge(self, plugin):
        await _active(plugin)
        assert plugin.is_active is True

    @pytest.mark.asyncio
    async def test_tools_are_exposed_only_when_active(self, plugin):
        assert plugin.get_tools() == []
        await _active(plugin)
        tools = plugin.get_tools()
        assert len(tools) == 3
        assert all(tool["type"] == "function" for tool in tools)
        assert {tool["function"]["name"] for tool in tools} == {
            "iot.device.toggle",
            "iot.device.set",
            "iot.device.read",
        }

    @pytest.mark.asyncio
    async def test_shutdown_closes_bridge(self, plugin, bridge):
        await _active(plugin)
        await plugin.shutdown()
        assert bridge.closed is True

    @pytest.mark.asyncio
    async def test_inactive_plugin_rejects_actions(self):
        plugin = IotPlugin(config={"devices": CONFIG["devices"], "host": "broker.local"})
        result = await plugin.execute_tool("iot.device.toggle", {"device_id": "lamp"})
        assert result.startswith("[TOOL_ERROR]")


# ------------------------------------------------------------------- HITL gate
class TestHitlGate:
    @pytest.mark.asyncio
    async def test_toggle_without_approval_is_blocked_and_not_published(
        self, plugin, bridge, confirm
    ):
        await _active(plugin)
        confirm.return_value = False

        result = await plugin.execute_tool("iot.device.toggle", {"device_id": "lamp"})

        assert result.startswith("[TOOL_BLOCKED]")
        assert bridge.published == []
        confirm.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_approved_toggle_is_published(self, plugin, bridge, confirm):
        await _active(plugin)

        result = await plugin.execute_tool("iot.device.toggle", {"device_id": "lamp"})

        payload = json.loads(result)
        assert payload["status"] == "ok"
        assert payload["device_id"] == "lamp"
        topic, message, qos = bridge.published[0]
        assert topic == "aiko/devices/lamp/toggle"
        assert (json.loads(message) if isinstance(message, str) else message) == {"source": "aiko", "action": "toggle", "device_id": "lamp"}
        assert qos == 1

    @pytest.mark.asyncio
    async def test_every_action_requires_its_own_confirmation(self, plugin, confirm, bridge):
        await _active(plugin)

        await plugin.execute_tool("iot.device.toggle", {"device_id": "lamp"})
        await plugin.execute_tool("iot.device.toggle", {"device_id": "lamp"})

        assert confirm.await_count == 2
        assert len(bridge.published) == 2

    @pytest.mark.asyncio
    async def test_confirmation_receives_scope_device_and_topic(self, plugin, confirm):
        await _active(plugin)

        await plugin.execute_tool("iot.device.set", {"device_id": "lamp", "value": 40})

        tool_name, args = confirm.await_args.args
        assert tool_name == "iot.device.set"
        assert args["device_id"] == "lamp"
        assert args["scope"] == "write"
        assert args["topic"] == "aiko/devices/lamp/set"
        assert args["value"] == 40

    @pytest.mark.asyncio
    async def test_confirmation_exception_fails_closed(self, plugin, bridge, confirm):
        await _active(plugin)
        confirm.side_effect = RuntimeError("dashboard offline")

        result = await plugin.execute_tool("iot.device.toggle", {"device_id": "lamp"})

        assert result.startswith("[TOOL_BLOCKED]")
        assert bridge.published == []

    @pytest.mark.asyncio
    async def test_sync_confirmation_callable_is_supported(self, bridge):
        plugin = IotPlugin(config=CONFIG, confirm=lambda name, args: True, bridge=bridge)
        await _active(plugin)

        result = await plugin.execute_tool("iot.device.toggle", {"device_id": "lamp"})

        assert json.loads(result)["status"] == "ok"


# --------------------------------------------------------------- validation
class TestValidation:
    @pytest.mark.asyncio
    async def test_unknown_tool_is_rejected(self, plugin, confirm):
        await _active(plugin)
        result = await plugin.execute_tool("iot.device.explode", {"device_id": "lamp"})
        assert result.startswith("[TOOL_ERROR]")
        confirm.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unknown_device_is_rejected(self, plugin, confirm):
        await _active(plugin)
        result = await plugin.execute_tool("iot.device.toggle", {"device_id": "door"})
        assert "not in the allowlist" in result
        confirm.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_id",
        ["../lamp", "lamp/#", "lamp +", "", "a" * 65, "lamp;rm -rf"],
    )
    async def test_invalid_device_ids_are_blocked(self, plugin, confirm, device_id):
        await _active(plugin)
        result = await plugin.execute_tool("iot.device.toggle", {"device_id": device_id})
        assert result.startswith("[TOOL_BLOCKED]")
        confirm.assert_not_awaited()

    def test_device_id_regex_allows_safe_ids(self):
        assert DEVICE_ID_RE.match("living_room-lamp2")

    @pytest.mark.asyncio
    async def test_scope_narrowing_on_device_is_enforced(self, plugin, confirm):
        await _active(plugin)
        result = await plugin.execute_tool("iot.device.set", {"device_id": "kettle", "value": "on"})
        assert result.startswith("[TOOL_BLOCKED]")
        confirm.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_requires_value(self, plugin, confirm):
        await _active(plugin)
        result = await plugin.execute_tool("iot.device.set", {"device_id": "lamp"})
        assert result.startswith("[TOOL_ERROR]")
        confirm.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_rejects_container_values(self, plugin, confirm):
        await _active(plugin)
        result = await plugin.execute_tool(
            "iot.device.set", {"device_id": "lamp", "value": {"nested": True}}
        )
        assert result.startswith("[TOOL_BLOCKED]")
        confirm.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unsafe_topic_in_device_config_is_blocked(self, bridge, confirm):
        config = {
            "host": "broker.local",
            "devices": {"evil": {"name": "Evil", "topic": "evil/#"}},
        }
        plugin = IotPlugin(config=config, confirm=confirm, bridge=bridge)
        await _active(plugin)

        result = await plugin.execute_tool("iot.device.toggle", {"device_id": "evil"})

        assert result.startswith("[TOOL_BLOCKED]")
        confirm.assert_not_awaited()
        assert bridge.published == []

    @pytest.mark.asyncio
    async def test_publish_failure_is_reported_as_error(self, plugin, confirm):
        await _active(plugin)

        def boom(topic, payload, qos=1):
            raise MqttBridgeError("broker gone")

        plugin._bridge.publish = boom
        result = await plugin.execute_tool("iot.device.toggle", {"device_id": "lamp"})

        assert result.startswith("[TOOL_ERROR]")
        assert "broker gone" in result

    @pytest.mark.asyncio
    async def test_read_publishes_to_read_topic(self, plugin, bridge):
        await _active(plugin)
        result = await plugin.execute_tool("iot.device.read", {"device_id": "lamp"})
        assert json.loads(result)["scope"] == "read"
        assert bridge.published[0][0] == "aiko/devices/lamp/read"


# --------------------------------------------------------------- MQTT bridge
class TestMqttBridge:
    def test_publish_before_connect_raises(self):
        bridge = MqttBridge(host="broker.local", client_factory=FakeBrokerClient)
        with pytest.raises(MqttBridgeError, match="not connected"):
            bridge.publish("aiko/devices/lamp/toggle", {})

    def test_connect_uses_credentials_and_tls(self):
        client = FakeBrokerClient()
        bridge = MqttBridge(
            host="broker.local",
            port=8883,
            username="aiko",
            password="secret",
            use_tls=True,
            client_factory=lambda: client,
        )

        assert bridge.connect() is True
        assert client.connected == ("broker.local", 8883, 30)
        assert client.credentials == ("aiko", "secret")
        assert client.tls is not None
        assert client.loop_started is True

    def test_publish_serialises_json_and_rejects_wildcards(self):
        client = FakeBrokerClient()
        bridge = MqttBridge(host="broker.local", client_factory=lambda: client)
        bridge.connect()

        assert bridge.publish("aiko/devices/lamp/toggle", {"on": True}) == 0
        topic, message, qos = client.published[0]
        assert topic == "aiko/devices/lamp/toggle"
        assert json.loads(message) == {"on": True}
        assert qos == 1

        with pytest.raises(MqttBridgeError, match="wildcard"):
            bridge.publish("aiko/devices/+/toggle", {})
        with pytest.raises(MqttBridgeError, match="wildcard"):
            bridge.publish("", {})

    def test_connect_failure_is_wrapped(self):
        class Broken(FakeBrokerClient):
            def connect(self, host, port, keepalive):
                raise OSError("connection refused")

        bridge = MqttBridge(host="broker.local", client_factory=Broken)
        with pytest.raises(MqttBridgeError, match="connection refused"):
            bridge.connect()

    def test_nonzero_publish_rc_raises(self):
        class Rejecting(FakeBrokerClient):
            def publish(self, topic, message, qos=1):
                return SimpleNamespace(rc=4)

        bridge = MqttBridge(host="broker.local", client_factory=Rejecting)
        bridge.connect()
        with pytest.raises(MqttBridgeError, match="rc=4"):
            bridge.publish("aiko/devices/lamp/toggle", {})

    def test_close_is_idempotent(self):
        client = FakeBrokerClient()
        bridge = MqttBridge(host="broker.local", client_factory=lambda: client)
        bridge.connect()
        bridge.close()
        bridge.close()
        assert client.loop_stopped is True
        assert client.disconnected is True
        assert bridge.is_connected is False

    def test_missing_paho_dependency_has_actionable_error(self, monkeypatch):
        def raiser(name):
            raise ImportError("No module named 'paho'")

        monkeypatch.setattr("plugins.iot.mqtt_bridge.importlib.import_module", raiser)
        bridge = MqttBridge(host="broker.local")
        with pytest.raises(MqttBridgeError, match="paho-mqtt is not installed"):
            bridge.connect()

    def test_missing_host_is_rejected(self):
        bridge = MqttBridge(host="", client_factory=FakeBrokerClient)
        with pytest.raises(MqttBridgeError, match="host is not configured"):
            bridge.connect()

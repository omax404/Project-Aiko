"""
AIKO VTS CONNECTOR (FIXED)
Handles registration and communication with VTube Studio API.
"""
import asyncio
import json
import os
import logging
from core.utils import async_retry

logger = logging.getLogger("VTS")

try:
    import websockets
except ImportError:
    websockets = None
    print(" [!] VTS Connector requires 'websockets'. Please run: pip install websockets")

VTS_PORT = 8001
PLUGIN_NAME = "Aiko_Recall_v1"
DEVELOPER = "Antigravity"

class VTSConnector:
    def __init__(self, port=8001):
        self.port = port
        self.websocket = None
        self.connected = False
        self.token = None
        self.auth_token_path = "vts_token.txt"
        self.load_token()

    def _is_socket_open(self) -> bool:
        return self.websocket is not None and not getattr(self.websocket, "closed", True)
        
    def load_token(self):
        if os.path.exists(self.auth_token_path):
            try:
                with open(self.auth_token_path, "r") as f:
                    self.token = f.read().strip()
            except IOError as e:
                logger.warning(f"Could not load token: {e}")
                self.token = None
                
    def save_token(self, token):
        self.token = token
        with open(self.auth_token_path, "w") as f:
            f.write(token)
            
    @async_retry(max_attempts=3, backoff_factor=2.0)
    async def _establish_connection(self):
        return await websockets.connect(f"ws://localhost:{self.port}")

    async def connect(self):
        """Connect to VTube Studio and register custom parameters."""
        if websockets is None: return False

        if self.connected and self._is_socket_open():
            return True

        if self._is_socket_open():
            await self.close()

        try:
            self.websocket = await self._establish_connection()
            auth_success = await self.authenticate()
            if auth_success:
                self.connected = True
                # --- Critical Step: Registering the parameter so it appears in the list ---
                await self.create_custom_parameter("AikoMouth") 
                logger.info("Connection Established & Authenticated.")
                return True
            else:
                logger.error("Authentication Failed during Connect.")
                self.connected = False
                await self.close()
                return False
                
        except Exception as e:
            logger.error(f"Connection Failed: {e}")
            self.connected = False
            await self.close()
            return False

    async def create_custom_parameter(self, param_name):
        """Formal request to VTS to add a new parameter to the Input list."""
        if not self._is_socket_open():
            return
        req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "create-param-aiko",
            "messageType": "ParameterCreationRequest",
            "data": {
                "parameterName": param_name,
                "explanation": "Controls Aiko's mouth movement",
                "min": 0,
                "max": 1,
                "defaultValue": 0
            }
        }
        await self.websocket.send(json.dumps(req))
        # Receive response to ensure execution
        try:
             await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
        except asyncio.TimeoutError:
             logger.warning("VTS Parameter Creation timed out (might already exist).")

    async def authenticate(self) -> bool:
        """Authenticate with VTS. Returns True if successful."""
        if not self._is_socket_open():
            return False
        
        if not self.token:
            print(" [VTS] Requesting Authorization... Please check VTube Studio popup!")
            req = {
                "apiName": "VTubeStudioPublicAPI", "apiVersion": "1.0",
                "requestID": "auth-token-req", "messageType": "AuthenticationTokenRequest",
                "data": {"pluginName": PLUGIN_NAME, "pluginDeveloper": DEVELOPER}
            }
            await self.websocket.send(json.dumps(req))
            try:
                resp_str = await asyncio.wait_for(self.websocket.recv(), timeout=130)
                resp = json.loads(resp_str)
                if "data" in resp and "authenticationToken" in resp["data"]:
                    self.token = resp["data"]["authenticationToken"]
                    self.save_token(self.token)
                else: return False
            except asyncio.TimeoutError: return False
                
        if self.token:
            auth_req = {
                "apiName": "VTubeStudioPublicAPI", "apiVersion": "1.0",
                "requestID": "auth-login", "messageType": "AuthenticationRequest",
                "data": {
                    "pluginName": PLUGIN_NAME, "pluginDeveloper": DEVELOPER,
                    "authenticationToken": self.token
                }
            }
            await self.websocket.send(json.dumps(auth_req))
            resp = json.loads(await self.websocket.recv())
            return resp.get("data", {}).get("authenticated", False)
        return False
        
    async def get_hotkeys(self):
        """Get list of available hotkeys."""
        if not self.connected: return []
        req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "hotkeys-list",
            "messageType": "HotkeysInCurrentModelRequest",
            "data": {}
        }
        try:
            await self.websocket.send(json.dumps(req))
            resp = json.loads(await self.websocket.recv())
            if "data" in resp and "availableHotkeys" in resp["data"]:
                return resp["data"]["availableHotkeys"]
        except Exception as e:
            logger.debug(f"Helpers error: {e}")
        return []

    async def trigger_hotkey(self, hotkey_id: str):
        """Trigger a hotkey by ID."""
        if not self.connected: return
        req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": f"exec-{hotkey_id}",
            "messageType": "HotkeyTriggerRequest",
            "data": {
                "hotkeyID": hotkey_id
            }
        }
        try:
            await self.websocket.send(json.dumps(req))
        except Exception as e:
            logger.error(f"Hotkey trigger error: {e}")
            self.connected = False

    async def set_parameters(self, params: list):
        if not self.connected: return
        req = {
            "apiName": "VTubeStudioPublicAPI", "apiVersion": "1.0",
            "requestID": "set-params", "messageType": "InjectParameterDataRequest",
            "data": {"mode": "set", "parameterValues": params}
        }
        try:
            await self.websocket.send(json.dumps(req))
        except Exception as e:
            self.connected = False

    async def set_mouth_open(self, value: float):
        """Sends value to ALL possible mouth parameters to force movement."""
        if not self.connected:
            print(" [VTS] Disconnected during speech. Attempting reconnect...")
            await self.connect()
            
        if self.connected:
            # print(f" [VTS] Sending Sync: {value:.2f}") # Too spammy, enable if needed
            await self.set_parameters([
                {"id": "AikoMouth", "value": value},
                {"id": "MouthOpen", "value": value},
                {"id": "ParamMouthOpen", "value": value}
            ])

    async def set_face_pose(self, angle_x=0, angle_y=0, eye_l=1, eye_r=1, brow_l=0, brow_r=0):
        """Control Face and Eye parameters."""
        await self.set_parameters([
            {"id": "FaceAngleX", "value": angle_x},
            {"id": "FaceAngleY", "value": angle_y},
            {"id": "EyeOpenLeft", "value": eye_l},
            {"id": "EyeOpenRight", "value": eye_r},
            {"id": "Brows", "value": (brow_l + brow_r) / 2}, # VTS usually maps 'Brows' to both
            {"id": "EyeRightX", "value": 0}, # Reset gaze
            {"id": "EyeRightY", "value": 0}
        ])

    async def set_expression(self, expression_name: str):
        """Trigger expression hotkey with Chinese/Japanese character support."""
        if not self.connected: return
        
        # Mapping from our internal emotions to VTS Hotkey Names (from screenshot)
        # 哭=Cry, 害羞=Shy, 慌张=Panic, 白眼=EyeRoll, 黑脸=DarkFace
        MAPPING = {
            "sad": "哭",
            "cry": "哭",
            "shy": "害羞",
            "blush": "害羞",
            "panic": "慌张",
            "surprised": "慌张",
            "shocked": "白眼",
            "annoyed": "白眼",
            "angry": "黑脸",
            "dark": "黑脸"
        }
        
        target = MAPPING.get(expression_name.lower(), expression_name.lower())
        
        try:
            hotkeys = await self.get_hotkeys()
            for hk in hotkeys:
                hk_name = hk.get("name", "").lower()
                # Check for direct match or substring match
                if target in hk_name or hk_name in target:
                    await self.trigger_hotkey(hk.get("hotkeyID"))
                    logger.info(f" [VTS] Triggered Expression: {hk.get('name')} (for '{expression_name}')")
                    return
            # logger.warning(f"No hotkey found for: {expression_name} -> {target}")
        except Exception as e:
            logger.error(f"Error setting expression: {e}")

    async def close(self):
        self.connected = False
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
        self.websocket = None

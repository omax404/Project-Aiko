"""
VRM Model Engine for Aiko Desktop
Provides control interface for VRM models using VTube Studio or web-based Three.js
"""
import logging
import json
import asyncio
from typing import Optional, Dict, Any

logger = logging.getLogger("VRMEngine")


class VRMEngine:
    """
    VRM Model Controller
    
    Supports:
    - VTube Studio integration for desktop VRM
    - Web-based VRM rendering via @pixiv/three-vrm
    - Animation and expression control
    """
    
    def __init__(self):
        self.model_path: Optional[str] = None
        self.is_loaded = False
        self.current_expression = "neutral"
        self.animations = {}
        
        # VRM BlendShape presets (ARKit compatible)
        self.blend_shapes = {
            "neutral": {},
            "happy": {"happy": 1.0, "blinkLeft": 0.3, "blinkRight": 0.3},
            "angry": {"angry": 1.0, "browDownLeft": 0.8, "browDownRight": 0.8},
            "sad": {"sad": 1.0, "blinkLeft": 0.5, "blinkRight": 0.5},
            "surprised": {"surprised": 1.0, "eyeWideLeft": 0.7, "eyeWideRight": 0.7},
            "relaxed": {"relaxed": 0.8, "mouthSmileLeft": 0.3, "mouthSmileRight": 0.3}
        }
        
        # Lip sync visemes
        self.visemes = {
            "aa": "viseme_aa",
            "E": "viseme_E", 
            "ih": "viseme_ih",
            "oh": "viseme_oh",
            "ou": "viseme_ou",
            "PP": "viseme_PP",
            "FF": "viseme_FF",
            "TH": "viseme_TH",
            "DD": "viseme_DD",
            "kk": "viseme_kk",
            "CH": "viseme_CH",
            "SS": "viseme_SS",
            "nn": "viseme_nn",
            "RR": "viseme_RR",
            "sil": "viseme_sil"
        }
        
    def load_model(self, path: str) -> bool:
        """Load a VRM model from path."""
        try:
            self.model_path = path
            self.is_loaded = True
            logger.info(f"VRM model loaded: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load VRM: {e}")
            return False
            
    def set_expression(self, expression: str, weight: float = 1.0) -> Dict[str, Any]:
        """
        Set facial expression.
        Returns blend shape data for the expression.
        """
        if expression in self.blend_shapes:
            self.current_expression = expression
            return {
                "expression": expression,
                "blendShapes": self.blend_shapes[expression],
                "weight": weight
            }
        return {"expression": "neutral", "blendShapes": {}}
        
    def set_lip_sync(self, viseme: str, weight: float = 1.0) -> Dict[str, Any]:
        """Set lip sync viseme for speech."""
        if viseme in self.visemes:
            return {
                "viseme": self.visemes[viseme],
                "weight": weight
            }
        return {"viseme": "viseme_sil", "weight": 0}
        
    def set_pose(self, bone: str, rotation: Dict[str, float]) -> Dict[str, Any]:
        """
        Set bone rotation for posing.
        bone: VRM bone name (head, neck, spine, etc.)
        rotation: {x, y, z} in degrees
        """
        return {
            "bone": bone,
            "rotation": rotation
        }
        
    def look_at(self, target: Dict[str, float]) -> Dict[str, Any]:
        """
        Set look-at target position.
        target: {x, y, z} world coordinates
        """
        return {
            "type": "lookAt",
            "target": target
        }
        
    def start_animation(self, name: str, loop: bool = False) -> Dict[str, Any]:
        """Start a named animation."""
        return {
            "action": "startAnimation",
            "name": name,
            "loop": loop
        }
        
    def stop_animation(self, name: str = None) -> Dict[str, Any]:
        """Stop animation (all if name is None)."""
        return {
            "action": "stopAnimation",
            "name": name
        }
        
    def get_web_config(self) -> Dict[str, Any]:
        """
        Get configuration for web-based VRM renderer.
        Returns settings for @pixiv/three-vrm initialization.
        """
        return {
            "modelPath": self.model_path,
            "autoUpdate": True,
            "lookAtType": "bone",
            "springBoneEnabled": True,
            "expressionManager": True,
            "materialDebug": False,
            "defaultExpression": "neutral",
            "animations": list(self.animations.keys())
        }
        
    def to_vts_params(self, expression: str) -> Dict[str, float]:
        """
        Convert VRM expression to VTube Studio parameters.
        Useful for hybrid Live2D/VRM setups.
        """
        vts_mapping = {
            "happy": {"MouthSmile": 0.8, "EyeSmile": 0.6, "Cheek": 0.5},
            "angry": {"BrowFrownLeft": 0.9, "BrowFrownRight": 0.9, "MouthFrown": 0.5},
            "sad": {"MouthFrown": 0.7, "BrowSadLeft": 0.8, "BrowSadRight": 0.8},
            "surprised": {"EyeWideLeft": 1.0, "EyeWideRight": 1.0, "MouthO": 0.6},
            "neutral": {}
        }
        return vts_mapping.get(expression, {})


# Singleton instance
vrm_engine = VRMEngine()

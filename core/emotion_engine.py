"""
core/emotion_engine.py

Advanced Automatic Emotion Neural Network for Aiko.
Maps Aiko's responses into a continuous 2D Circumplex Model of Affect (Valence/Arousal).
"""

import re
import math
import logging
import time

logger = logging.getLogger("EmotionEngine")

# The 25 emotions mapped to approximate (Valence, Arousal) coordinates.
# Valence: -1.0 (Negative) to 1.0 (Positive)
# Arousal: -1.0 (Low Energy) to 1.0 (High Energy)
EMOTION_MAP = {
    "happy": (0.8, 0.4),
    "excited": (0.9, 0.8),
    "playful": (0.6, 0.6),
    "proud": (0.5, 0.3),
    "affectionate": (0.7, 0.1),
    "caring": (0.6, -0.2),
    "content": (0.5, -0.6),
    "calm": (0.3, -0.8),
    
    "angry": (-0.8, 0.8),
    "frustrated": (-0.6, 0.6),
    "annoyed": (-0.4, 0.4),
    "jealous": (-0.7, 0.5),
    "protective": (0.2, 0.7),
    
    "sad": (-0.8, -0.5),
    "disappointed": (-0.6, -0.3),
    "lonely": (-0.7, -0.6),
    "worried": (-0.5, 0.5),
    
    "shy": (0.2, 0.2),
    "embarrassed": (-0.2, 0.4),
    "smug": (0.4, 0.2),
    "sarcastic": (-0.2, 0.1),
    "mischievous": (0.3, 0.5),
    
    "surprised": (0.2, 0.9),
    "distant": (-0.4, -0.4),
    "neutral": (0.0, 0.0)
}

class EmotionEngine:
    def __init__(self):
        self.valence = 0.0
        self.arousal = 0.0
        self.target_valence = 0.0
        self.target_arousal = 0.0
        
        self.active_emotions = {"neutral": 1.0}
        self.overrides = {}  # Manual web UI overrides {"angry": 0.8}
        
        self.last_update = time.time()
        self.smoothing_factor = 2.0  # Speed of gliding toward target

    def process_text(self, text: str):
        """Extract <emotion>...</emotion> tags and update target state."""
        # Find tags
        matches = re.findall(r'<emotion>(.*?)</emotion>', text, re.IGNORECASE)
        found_emotions = []
        
        if matches:
            tags = matches[-1].lower().replace(',', ' ').split()
            logger.info(f" [EmotionEngine] Detected RAW TAGS from LLM: {tags}")
            for tag in tags:
                # Fuzzy match
                for em in EMOTION_MAP.keys():
                    if em in tag or tag in em:
                        found_emotions.append(em)
                        
        # Fallback to keyword matching if no tags
        if not found_emotions:
            text_lower = text.lower()
            for em in EMOTION_MAP.keys():
                if em in text_lower:
                    found_emotions.append(em)
        
        if not found_emotions:
            found_emotions = ["neutral"]
            
        # Calculate new target based on average of found emotions
        tv, ta = 0.0, 0.0
        for em in found_emotions:
            v, a = EMOTION_MAP[em]
            tv += v
            ta += a
            
        tv /= len(found_emotions)
        ta /= len(found_emotions)
        
        self.target_valence = tv
        self.target_arousal = ta
        
        # Update active labels
        self.active_emotions = {em: 1.0 / len(found_emotions) for em in found_emotions}
        
    def set_override(self, emotion_name: str, value: float):
        """Manually override an emotion's weight (0.0 to 1.0)."""
        emotion_name = emotion_name.lower()
        if emotion_name in EMOTION_MAP:
            if value <= 0.01:
                self.overrides.pop(emotion_name, None)
            else:
                self.overrides[emotion_name] = value

    def reset_overrides(self):
        self.overrides.clear()

    def update(self):
        """Step the simulation toward the target, applying overrides."""
        now = time.time()
        dt = min(now - self.last_update, 0.1) # max 100ms step
        self.last_update = now
        
        # 1. Start with the natural target
        tv = self.target_valence
        ta = self.target_arousal
        
        # 2. Apply manual overrides (pulls the target toward the overridden emotions)
        total_weight = 1.0
        for em, weight in self.overrides.items():
            ov, oa = EMOTION_MAP[em]
            tv = (tv * total_weight + ov * weight) / (total_weight + weight)
            ta = (ta * total_weight + oa * weight) / (total_weight + weight)
            total_weight += weight
            
        # 3. Smoothly glide current valence/arousal toward the computed target
        self.valence += (tv - self.valence) * self.smoothing_factor * dt
        self.arousal += (ta - self.arousal) * self.smoothing_factor * dt
        
        # Clamp bounds
        self.valence = max(-1.0, min(1.0, self.valence))
        self.arousal = max(-1.0, min(1.0, self.arousal))
        
    def get_state(self):
        """Return the current 2D telemetry and dominant emotions."""
        self.update()
        
        # Determine current quadrant label
        quadrant = "Neutral"
        if self.valence > 0.2 and self.arousal > 0.2: quadrant = "High Arousal Positive"
        elif self.valence > 0.2 and self.arousal < -0.2: quadrant = "Low Arousal Positive"
        elif self.valence < -0.2 and self.arousal > 0.2: quadrant = "High Arousal Negative"
        elif self.valence < -0.2 and self.arousal < -0.2: quadrant = "Low Arousal Negative"

        # Calculate distances to all 25 mapped emotions to find "closest match"
        distances = []
        for em, (v, a) in EMOTION_MAP.items():
            # Add override boost if active
            boost = self.overrides.get(em, 0.0)
            dist = math.sqrt((self.valence - v)**2 + (self.arousal - a)**2)
            # Inverse distance weighting
            score = max(0, 1.0 - dist) + (boost * 0.5)
            distances.append((em, score))
            
        distances.sort(key=lambda x: x[1], reverse=True)
        dominant = [em for em, score in distances[:3] if score > 0.2]
        if not dominant: dominant = ["neutral"]

        return {
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
            "quadrant": quadrant,
            "dominant_emotions": dominant,
            "overrides": self.overrides
        }

    def get_active_emotion(self) -> str:
        """Helper to get the single most dominant emotion."""
        state = self.get_state()
        emotions = state.get("dominant_emotions", ["neutral"])
        return emotions[0] if emotions else "neutral"

# Global singleton instance
emotion_engine = EmotionEngine()

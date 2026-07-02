"""
core/emotion_engine.py

Advanced Automatic Emotion Neural Network for Aiko.
Simulates a real biological chemical field (Dopamine, Serotonin, Cortisol, Adrenaline).
"""

import re
import math
import logging
import time
import json
import os

logger = logging.getLogger("EmotionEngine")

# BASELINES (The natural resting state of the chemical field)
BASELINES = {
    "dopamine": 0.5,    # Joy/Reward
    "serotonin": 0.5,   # Calm/Affection
    "cortisol": 0.2,    # Stress/Anger
    "adrenaline": 0.1,   # Fear/Energy/Action
    "oxytocin": 0.3,    # Trust/Bonding/Empathy
    "melatonin": 0.1    # Drowsiness/Tiredness
}

# DECAY_RATES (How fast they pull back to baseline per second)
DECAY_RATES = {
    "dopamine": 0.005,
    "serotonin": 0.001,
    "cortisol": 0.002,
    "adrenaline": 0.02,
    "oxytocin": 0.003,
    "melatonin": 0.008
}

# (Dopamine, Serotonin, Cortisol, Adrenaline, Oxytocin, Melatonin) Centers for the UI 25 Emotions
EMOTION_MAP = {
    "happy": (0.8, 0.6, 0.1, 0.5, 0.7, 0.1),
    "excited": (0.9, 0.5, 0.1, 0.8, 0.6, 0.1),
    "playful": (0.8, 0.5, 0.2, 0.6, 0.7, 0.1),
    "proud": (0.7, 0.7, 0.2, 0.5, 0.6, 0.1),
    "affectionate": (0.7, 0.9, 0.1, 0.4, 0.9, 0.1),
    "caring": (0.6, 0.8, 0.1, 0.3, 0.9, 0.1),
    "content": (0.6, 0.8, 0.1, 0.2, 0.7, 0.2),
    "calm": (0.5, 0.7, 0.1, 0.2, 0.6, 0.3),
    
    "angry": (0.2, 0.1, 0.9, 0.8, 0.1, 0.1),
    "frustrated": (0.3, 0.2, 0.8, 0.7, 0.2, 0.1),
    "annoyed": (0.4, 0.3, 0.6, 0.5, 0.3, 0.1),
    "jealous": (0.2, 0.2, 0.7, 0.6, 0.3, 0.1),
    "protective": (0.5, 0.6, 0.5, 0.8, 0.8, 0.1),
    
    "sad": (0.2, 0.1, 0.6, 0.2, 0.3, 0.4),
    "disappointed": (0.3, 0.2, 0.5, 0.2, 0.2, 0.3),
    "lonely": (0.2, 0.1, 0.5, 0.2, 0.1, 0.4),
    "worried": (0.4, 0.3, 0.7, 0.7, 0.4, 0.3),
    
    "shy": (0.5, 0.6, 0.4, 0.6, 0.7, 0.2),
    "embarrassed": (0.4, 0.4, 0.6, 0.6, 0.5, 0.2),
    "smug": (0.7, 0.5, 0.3, 0.4, 0.4, 0.1),
    "sarcastic": (0.5, 0.4, 0.5, 0.4, 0.3, 0.1),
    "mischievous": (0.8, 0.5, 0.3, 0.6, 0.5, 0.1),
    
    "surprised": (0.6, 0.5, 0.4, 0.9, 0.5, 0.1),
    "distant": (0.4, 0.2, 0.4, 0.2, 0.2, 0.5),
    "neutral": (0.5, 0.5, 0.2, 0.1, 0.5, 0.1) # Matches baseline
}

class EmotionEngine:
    def __init__(self):
        # Initial resting state baselines
        self.baselines = {k: v for k, v in BASELINES.items()}
        
        # Current active chemical levels
        self.chemicals = {k: v for k, v in BASELINES.items()}
        
        # Momentum variables for emotional inertia
        self.momentum = {k: 0.0 for k in BASELINES}
        
        self.overrides = {}  
        self.last_update = time.time()
        self.is_flushing = False
        self._flush_timer = 0
        
        # Pull personalized identity attractor from profile
        self.sync_with_profile()

    def sync_with_profile(self):
        """Update resting-state baselines based on relationship score in master_profile.json."""
        try:
            # Robust path logic relative to core/
            profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "master_profile.json")
            if os.path.exists(profile_path):
                with open(profile_path, "r") as f:
                    data = json.load(f)
                    rel = data.get("relationship", {})
                    score = rel.get("score", 5.0)
                    
                    # 1. BASELINE DRIFT LOGIC
                    # If score is high (8+), she is naturally more affectionate (high Serotonin baseline)
                    # If score is low (<3), she is naturally more stressed/defensive (high Cortisol baseline)
                    
                    # Serotonin Drift (0.5 baseline, ranges from 0.2 to 0.8)
                    self.baselines["serotonin"] = 0.2 + (score / 10.0) * 0.6
                    
                    # Dopamine Drift (0.5 baseline, rises with affection)
                    self.baselines["dopamine"] = 0.3 + (score / 10.0) * 0.4
                    
                    # Cortisol Drift (Lower score = higher resting stress)
                    # Score 0 -> 0.7 baseline, Score 10 -> 0.1 baseline
                    self.baselines["cortisol"] = 0.7 - (score / 10.0) * 0.6
                    
                    logger.info(f" [EmotionEngine] Baselines synced with profile. Relationship Score: {score}")
                    logger.info(f" [EmotionEngine] Identity Attractors: {self.baselines}")
        except Exception as e:
            logger.error(f" [EmotionEngine] Sync Error: {e}")

    def flush_chemicals(self):
        """Reset all chemicals instantly to their current personalized baselines."""
        self.sync_with_profile() # Reload from disk first
        for chem, base in self.baselines.items():
            self.chemicals[chem] = base
        
        self.is_flushing = True
        self._flush_timer = time.time()
        logger.info(" [EmotionEngine] Neural cache flushed. Chemicals reset to baselines.")

    def apply_delta(self, d_dopa=0.0, d_sero=0.0, d_cort=0.0, d_adre=0.0, d_oxy=0.0, d_mela=0.0):
        """Apply a spike or drop to the chemical field, pushing both concentrations and momentum."""
        self.chemicals["dopamine"] += d_dopa
        self.chemicals["serotonin"] += d_sero
        self.chemicals["cortisol"] += d_cort
        self.chemicals["adrenaline"] += d_adre
        self.chemicals["oxytocin"] += d_oxy
        self.chemicals["melatonin"] += d_mela
        
        # Push momentum as well (representing velocity/inertia of emotional shock)
        self.momentum["dopamine"] += d_dopa * 0.5
        self.momentum["serotonin"] += d_sero * 0.5
        self.momentum["cortisol"] += d_cort * 0.5
        self.momentum["adrenaline"] += d_adre * 0.5
        self.momentum["oxytocin"] += d_oxy * 0.5
        self.momentum["melatonin"] += d_mela * 0.5
        
        # Clamp bounds
        for k in self.chemicals:
            self.chemicals[k] = max(0.0, min(1.0, self.chemicals[k]))

    def process_text(self, text: str):
        """Extract tags and spike chemicals appropriately."""
        matches = re.findall(r'<emotion>(.*?)</emotion>', text, re.IGNORECASE)
        found_emotions = []
        
        if matches:
            tags = matches[-1].lower().replace(',', ' ').split()
            logger.info(f" [EmotionEngine] Detected RAW TAGS from LLM: {tags}")
            for tag in tags:
                for em in EMOTION_MAP.keys():
                    if em in tag or tag in em:
                        found_emotions.append(em)
                        
        if not found_emotions:
            text_lower = text.lower()
            for em in EMOTION_MAP.keys():
                if em in text_lower:
                    found_emotions.append(em)
        
        if not found_emotions:
            found_emotions = ["neutral"]
            
        # Instead of moving a fixed percentage towards the target center,
        # we calculate a stimulus delta relative to the baseline state.
        # This makes her response dynamic based on relationship baselines.
        sensitivity = 0.25
        for em in found_emotions:
            t_d, t_s, t_c, t_a, t_oxy, t_mela = EMOTION_MAP[em]
            
            d_dopa = (t_d - self.baselines["dopamine"]) * sensitivity
            d_sero = (t_s - self.baselines["serotonin"]) * sensitivity
            d_cort = (t_c - self.baselines["cortisol"]) * sensitivity
            d_adre = (t_a - self.baselines["adrenaline"]) * sensitivity
            d_oxy = (t_oxy - self.baselines["oxytocin"]) * sensitivity
            d_mela = (t_mela - self.baselines["melatonin"]) * sensitivity
            
            self.apply_delta(d_dopa, d_sero, d_cort, d_adre, d_oxy, d_mela)
            
        # Clamp
        for k in self.chemicals:
            self.chemicals[k] = max(0.0, min(1.0, self.chemicals[k]))

    def update(self):
        """Step the simulation: decay chemicals toward baseline and apply somatic feedback."""
        now = time.time()
        dt = now - self.last_update
        self.last_update = now
        
        # Prevent massive jumps if system sleeps
        if dt > 3600: 
            dt = 3600
            
        # Manage flush notification timer
        if self.is_flushing and (now - self._flush_timer > 2.0):
            self.is_flushing = False
            
        # 1. Decay momentum toward 0 (friction)
        # Momentum friction rate: 0.15 (decays in ~15-20 seconds)
        momentum_friction = 0.15
        for chem in self.chemicals:
            self.momentum[chem] *= math.exp(-momentum_friction * dt)
            
        # 2. Update chemicals: exponential decay towards baseline + momentum force
        for chem, val in self.chemicals.items():
            base = self.baselines[chem]
            rate = DECAY_RATES[chem]
            # Continuous exponential decay: C(t) = base + (C(t0) - base) * e^(-rate * dt)
            decayed_val = base + (val - base) * math.exp(-rate * dt)
            # Add momentum force
            self.chemicals[chem] = decayed_val + self.momentum[chem] * dt
            
        # SOMATIC FEEDBACK (Fake Body)
        # We read the host PC's state to influence Aiko's stress levels mathematically.
        try:
            import psutil
            import math
            cpu_load = psutil.cpu_percent()
            ram_load = psutil.virtual_memory().percent
            
            # Logistic Activation Function (Sigmoid)
            def sigmoid(x, k, x0): 
                try:
                    return 1.0 / (1.0 + math.exp(-k * (x - x0)))
                except OverflowError:
                    return 0.0 if (x - x0) < 0 else 1.0
            
            # Continuous biological mapping
            # CPU load smoothly maps to Adrenaline target (midpoint 60%, curve steepness 0.1)
            target_adrenaline = sigmoid(cpu_load, 0.1, 60.0)
            
            # RAM load smoothly maps to Cortisol target (midpoint 80%, curve steepness 0.15)
            target_cortisol = sigmoid(ram_load, 0.15, 80.0)
            
            # Chemicals drift towards their biological targets based on hardware equilibrium
            self.chemicals["adrenaline"] += (target_adrenaline - self.chemicals["adrenaline"]) * 0.1 * dt
            self.chemicals["cortisol"] += (target_cortisol - self.chemicals["cortisol"]) * 0.05 * dt
                
            self.cpu_load = cpu_load
            self.ram_load = ram_load
        except Exception as e:
            self.cpu_load = 0.0
            self.ram_load = 0.0
            logger.debug(f"Somatic feedback failed: {e}")
            
        # Clamp bounds again after feedback
        for k in self.chemicals:
            self.chemicals[k] = max(0.0, min(1.0, self.chemicals[k]))
            
    def get_biological_telemetry(self) -> str:
        """Returns a string block to inject into the LLM Persona prompt."""
        self.update()
        
        d = self.chemicals["dopamine"]
        s = self.chemicals["serotonin"]
        c = self.chemicals["cortisol"]
        a = self.chemicals["adrenaline"]
        o = self.chemicals["oxytocin"]
        m = self.chemicals["melatonin"]
        
        def level(val):
            if val > 0.8: return "Very High"
            if val > 0.6: return "High"
            if val > 0.4: return "Moderate"
            if val > 0.2: return "Low"
            return "Very Low"

        # Calculate Fake Vitals
        cpu = getattr(self, "cpu_load", 0.0)
        ram = getattr(self, "ram_load", 0.0)
        heart_rate = int(60 + (cpu * 0.8) + (a * 40)) # Resting 60, peaks at ~180
        muscle_tension = int((ram * 0.5) + (c * 50)) # 0 to 100%

        somatic = []
        if d > 0.7: somatic.append("highly energetic/joyful")
        if s > 0.7: somatic.append("deeply affectionate")
        if s < 0.3: somatic.append("feeling lonely/cold")
        if c > 0.6: somatic.append("stressed/frustrated")
        if c > 0.8: somatic.append("angry/tsundere")
        if a > 0.7: somatic.append("startled/hyper")
        if o > 0.7: somatic.append("deeply trusting/bonded")
        if m > 0.6: somatic.append("sleepy/lethargic")
        if heart_rate > 120: somatic.append("heart racing/overwhelmed")
        if muscle_tension > 80: somatic.append("physically tense/exhausted")
        
        somatic_str = ", ".join(somatic) if somatic else "stable and relaxed"

        return f"""[BIOLOGICAL TELEMETRY]
Dopamine (Joy/Reward): {d:.2f} ({level(d)})
Serotonin (Affection/Calm): {s:.2f} ({level(s)})
Cortisol (Stress/Anger): {c:.2f} ({level(c)})
Adrenaline (Energy/Fear): {a:.2f} ({level(a)})
Oxytocin (Bonding/Empathy): {o:.2f} ({level(o)})
Melatonin (Drowsiness): {m:.2f} ({level(m)})

[PHYSICAL VITALS]
Heart Rate: {heart_rate} BPM
Muscle Tension: {muscle_tension}%

Somatic Translation: You feel {somatic_str}."""

    def get_state(self):
        """Return the current telemetry and dominant emotions for the UI."""
        self.update()
        
        d = self.chemicals["dopamine"]
        s = self.chemicals["serotonin"]
        c = self.chemicals["cortisol"]
        a = self.chemicals["adrenaline"]
        o = self.chemicals["oxytocin"]
        m = self.chemicals["melatonin"]
        
        # Calculate distances to all 25 mapped emotions to find "closest match"
        distances = []
        for em, (t_d, t_s, t_c, t_a, t_oxy, t_mela) in EMOTION_MAP.items():
            dist = math.sqrt((d - t_d)**2 + (s - t_s)**2 + (c - t_c)**2 + (a - t_a)**2 + (o - t_oxy)**2 + (m - t_mela)**2)
            # Inverse distance weighting
            score = max(0, 2.0 - dist)
            distances.append((em, score))
            
        distances.sort(key=lambda x: x[1], reverse=True)
        dominant = [em for em, score in distances[:3] if score > 0.5]
        if not dominant: dominant = ["neutral"]

        return {
            "dopamine": round(d, 3),
            "serotonin": round(s, 3),
            "cortisol": round(c, 3),
            "adrenaline": round(a, 3),
            "oxytocin": round(o, 3),
            "melatonin": round(m, 3),
            "dominant_emotions": dominant,
            # Forward compatibility for any UI still expecting valence/arousal keys
            "valence": round((d + s - c) / 2.0, 3), 
            "arousal": round((d + a) / 2.0, 3)
        }

    def get_active_emotion(self) -> str:
        """Helper to get the single most dominant emotion."""
        state = self.get_state()
        emotions = state.get("dominant_emotions", ["neutral"])
        return emotions[0] if emotions else "neutral"

    def get_inference_modifiers(self) -> dict:
        """
        Dynamically calculates LLM inference parameters based on the 4D chemical state.
        This provides 'Neuromodulator Coupling' as per Aurora principles.
        """
        self.update()
        d = self.chemicals["dopamine"]
        s = self.chemicals["serotonin"]
        c = self.chemicals["cortisol"]
        a = self.chemicals["adrenaline"]

        import math
        
        # Base default inference parameters
        modifiers = {
            "temperature": 0.75,
            "top_p": 0.9,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "max_tokens": 300
        }

        # Multi-variable continuous mapping
        modifiers["temperature"] = 0.75 + (a * 0.5) - (s * 0.3) + (c * 0.1)
        modifiers["top_p"] = 0.9 - (s * 0.4) + (d * 0.05)
        
        # Dopamine drives exploration; Cortisol suppresses it
        modifiers["presence_penalty"] = (d * 0.8) - (c * 0.2)
        modifiers["frequency_penalty"] = (a * 1.0)

        # Keep max_tokens safely high (2000) to avoid ugly mid-sentence API truncation.
        # Emotional state (like tsundere/stress) naturally guides Aiko to speak in shorter 
        # bursts via system prompts, but the hard API token limit must never cut her off mid-word.
        modifiers["max_tokens"] = 2000

        # Clamp all values to safe bounds for standard LLM APIs
        modifiers["temperature"] = max(0.1, min(2.0, modifiers["temperature"]))
        modifiers["top_p"] = max(0.1, min(1.0, modifiers["top_p"]))
        modifiers["presence_penalty"] = max(-2.0, min(2.0, modifiers["presence_penalty"]))
        modifiers["frequency_penalty"] = max(-2.0, min(2.0, modifiers["frequency_penalty"]))
        modifiers["max_tokens"] = max(10, min(4000, modifiers["max_tokens"]))

        return modifiers

# Global singleton instance
emotion_engine = EmotionEngine()

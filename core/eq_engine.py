"""
core/eq_engine.py
─────────────────
Emotional Intelligence (EQ) Signal Detector for Aiko.

Pre-analyzes user messages for emotional cues and injects a lightweight
[EQ_CONTEXT] block into the LLM prompt so Aiko can adapt her response
plan, tone, and content — not just word choice.

Based on: Zall et al., "Intelligent Agents with Emotional Intelligence"
(arXiv:2511.20657), operationalized for text-only conversation.
"""

import re
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Deque

logger = logging.getLogger("EQEngine")

# ── Lexicon-based signal patterns ────────────────────────────────────────────

# Frustration / stuck
_FRUSTRATION_WORDS = re.compile(
    r'\b(ugh|wtf|broken|stuck|doesn\'?t work|not working|still broken|can\'?t|'
    r'impossible|ridiculous|annoying|annoyed|hate this|waste of time|'
    r'the hell|stupid|dumb|useless|garbage|trash|shit|damn|crap|ffs|omg)\b',
    re.IGNORECASE
)

# Anxiety / overwhelm / low confidence
_ANXIETY_WORDS = re.compile(
    r'\b(sorry to bother|i guess|maybe it\'?s just me|i\'?m not sure|'
    r'overwhelmed|anxious|stressed|nervous|worried|scared|panic|'
    r'too much|can\'?t handle|freaking out|help me|idk|'
    r'i don\'?t know what to do|lost|confused)\b',
    re.IGNORECASE
)

# Hedging qualifiers
_HEDGING = re.compile(
    r'\b(i think|maybe|probably|i suppose|kind of|sort of|might be|'
    r'not sure if|is it okay if|would it be possible)\b',
    re.IGNORECASE
)

# Sadness / grief
_SADNESS_WORDS = re.compile(
    r'\b(sad|depressed|lonely|miss|lost someone|passed away|died|'
    r'heartbroken|crying|tears|grief|mourning|devastated|empty|numb)\b',
    re.IGNORECASE
)

# Excitement / positive arousal
_EXCITEMENT_WORDS = re.compile(
    r'\b(amazing|awesome|incredible|fantastic|can\'?t wait|so excited|'
    r'let\'?s go|hell yeah|yesss+|wooo+|fire|lit|based|insane|'
    r'love it|perfect|brilliant|genius|beautiful|sick)\b',
    re.IGNORECASE
)

# Pride / accomplishment
_PRIDE_WORDS = re.compile(
    r'\b(i did it|finally|nailed it|figured it out|solved|'
    r'got it working|passed|won|achieved|completed|shipped|'
    r'look what i|check this out|made this|built this)\b',
    re.IGNORECASE
)

# Defensive / criticism-sensitive
_DEFENSIVE_WORDS = re.compile(
    r'\b(it\'?s not my fault|i didn\'?t|don\'?t blame me|'
    r'whatever|fine|okay fine|i know|i already know|'
    r'you don\'?t understand|that\'?s not fair|stop|leave me alone)\b',
    re.IGNORECASE
)


@dataclass
class EQSignal:
    """A detected emotional signal from a single user message."""
    affect: str              # e.g. "frustration", "anxiety", "excitement"
    confidence: float        # 0.0 - 1.0
    indicators: List[str]    # what triggered it
    
    def __repr__(self):
        return f"EQSignal({self.affect}, conf={self.confidence:.2f}, indicators={self.indicators})"


@dataclass
class EQSnapshot:
    """The full EQ read of a user message, including drift context."""
    primary: Optional[EQSignal] = None
    secondary: Optional[EQSignal] = None
    drift_note: str = ""           # e.g. "tone shifted from excited to frustrated"
    arousal_level: str = "normal"  # "low", "normal", "high", "very_high"
    
    @property
    def is_emotional(self) -> bool:
        return self.primary is not None and self.primary.confidence >= 0.3
    
    def to_context_string(self) -> str:
        """Format as a compact context block for the LLM prompt."""
        if not self.is_emotional:
            return ""
        
        parts = []
        parts.append(f"Detected affect: {self.primary.affect} (confidence: {self.primary.confidence:.0%})")
        if self.primary.indicators:
            parts.append(f"Indicators: {', '.join(self.primary.indicators[:3])}")
        if self.secondary and self.secondary.confidence >= 0.25:
            parts.append(f"Secondary: {self.secondary.affect}")
        if self.drift_note:
            parts.append(f"Drift: {self.drift_note}")
        if self.arousal_level in ("high", "very_high"):
            parts.append(f"Arousal: {self.arousal_level}")
        
        return "[EQ_CONTEXT]: " + " | ".join(parts)


class EQEngine:
    """
    Lightweight emotional intelligence signal detector.
    Tracks recent user messages to detect emotional drift over the conversation.
    """
    
    def __init__(self, window_size: int = 8):
        # Rolling window of recent (message, primary_affect) pairs per user
        self._history: dict[str, Deque] = {}
        self._window_size = window_size
    
    def _get_history(self, user_id: str) -> Deque:
        if user_id not in self._history:
            self._history[user_id] = deque(maxlen=self._window_size)
        return self._history[user_id]
    
    def analyze(self, message: str, user_id: str = "user") -> EQSnapshot:
        """
        Analyze a user message for emotional signals.
        Returns an EQSnapshot with primary affect, confidence, and drift context.
        """
        signals = []
        msg_lower = message.lower().strip()
        msg_len = len(message.strip())
        
        # ── Lexicon-based detection ──────────────────────────────────────
        
        frustration_hits = _FRUSTRATION_WORDS.findall(message)
        if frustration_hits:
            conf = min(0.4 + 0.15 * len(frustration_hits), 0.95)
            signals.append(EQSignal("frustration", conf, frustration_hits[:3]))
        
        anxiety_hits = _ANXIETY_WORDS.findall(message)
        hedging_hits = _HEDGING.findall(message)
        if anxiety_hits or len(hedging_hits) >= 2:
            combined = (anxiety_hits + hedging_hits)[:3]
            conf = min(0.35 + 0.15 * len(anxiety_hits) + 0.08 * len(hedging_hits), 0.9)
            signals.append(EQSignal("anxiety", conf, combined))
        
        sadness_hits = _SADNESS_WORDS.findall(message)
        if sadness_hits:
            conf = min(0.5 + 0.15 * len(sadness_hits), 0.95)
            signals.append(EQSignal("sadness", conf, sadness_hits[:3]))
        
        excitement_hits = _EXCITEMENT_WORDS.findall(message)
        if excitement_hits:
            conf = min(0.4 + 0.12 * len(excitement_hits), 0.9)
            signals.append(EQSignal("excitement", conf, excitement_hits[:3]))
        
        pride_hits = _PRIDE_WORDS.findall(message)
        if pride_hits:
            conf = min(0.45 + 0.15 * len(pride_hits), 0.9)
            signals.append(EQSignal("pride", conf, pride_hits[:3]))
        
        defensive_hits = _DEFENSIVE_WORDS.findall(message)
        if defensive_hits:
            conf = min(0.4 + 0.15 * len(defensive_hits), 0.85)
            signals.append(EQSignal("defensiveness", conf, defensive_hits[:3]))
        
        # ── Structural / punctuation signals ─────────────────────────────
        
        arousal = "normal"
        structural_indicators = []
        
        # ALL CAPS detection (more than 60% uppercase in a message > 5 chars)
        alpha_chars = [c for c in message if c.isalpha()]
        if len(alpha_chars) > 5:
            caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
            if caps_ratio > 0.6:
                arousal = "high"
                structural_indicators.append("ALL_CAPS")
        
        # Repeated punctuation
        if re.search(r'[?!]{3,}', message):
            arousal = "high" if arousal != "high" else "very_high"
            structural_indicators.append("repeated_punctuation")
        
        # Very short message (potential frustration/disengagement signal)
        # Only flag if history shows longer messages before
        history = self._get_history(user_id)
        if msg_len < 15 and len(history) >= 2:
            recent_lengths = [len(h[0]) for h in list(history)[-3:]]
            avg_recent = sum(recent_lengths) / len(recent_lengths) if recent_lengths else 0
            if avg_recent > 40:
                # Message significantly shorter than recent average -> possible disengagement
                structural_indicators.append("sudden_brevity")
                if not any(s.affect == "frustration" for s in signals):
                    signals.append(EQSignal("frustration", 0.3, ["sudden_brevity"]))
        
        # Boost arousal signals into existing detections
        if structural_indicators and signals:
            for s in signals:
                s.indicators.extend(structural_indicators)
                s.confidence = min(s.confidence + 0.1, 0.95)
        elif structural_indicators and not signals and arousal in ("high", "very_high"):
            # High arousal with no clear affect — flag as ambiguous heightened state
            signals.append(EQSignal("heightened_arousal", 0.4, structural_indicators))
        
        # ── Sort by confidence and build snapshot ────────────────────────
        
        signals.sort(key=lambda s: s.confidence, reverse=True)
        
        primary = signals[0] if signals else None
        secondary = signals[1] if len(signals) > 1 else None
        
        # ── Drift detection ──────────────────────────────────────────────
        
        drift_note = ""
        if primary and len(history) >= 2:
            recent_affects = [h[1] for h in list(history)[-3:] if h[1]]
            if recent_affects:
                last_affect = recent_affects[-1]
                if last_affect != primary.affect:
                    # Classify the shift
                    positive = {"excitement", "pride"}
                    negative = {"frustration", "sadness", "anxiety", "defensiveness"}
                    
                    if last_affect in positive and primary.affect in negative:
                        drift_note = f"tone shifted from {last_affect} to {primary.affect} (mood drop)"
                    elif last_affect in negative and primary.affect in positive:
                        drift_note = f"tone shifted from {last_affect} to {primary.affect} (mood lift)"
                    elif last_affect != primary.affect:
                        drift_note = f"tone shifted from {last_affect} to {primary.affect}"
        
        # Record this message in history
        history.append((message, primary.affect if primary else None))
        
        snapshot = EQSnapshot(
            primary=primary,
            secondary=secondary,
            drift_note=drift_note,
            arousal_level=arousal
        )
        
        if snapshot.is_emotional:
            logger.info(f"[EQ] User '{user_id}': {snapshot.to_context_string()}")
        
        return snapshot


# ── Module-level singleton ───────────────────────────────────────────────────
eq_engine = EQEngine()

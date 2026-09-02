"""core/security/injection.py
Multi-layer prompt injection detection and normalization.
"""
import re
import unicodedata

def detect_injection(text: str) -> tuple[bool, float]:
    """
    Multi-layer injection detection. Returns (is_blocked, confidence_score).
    Score >= 0.70 → blocked.
    """
    score = 0.0
    text_lower = text.lower()
    
    # Normalize unicode to catch homoglyph evasion (Cyrillic а vs Latin a)
    normalized = unicodedata.normalize('NFKC', text_lower)
    
    # Layer 1: Exact regex patterns
    # High risk patterns (0.6 each)
    high_risk_patterns = [
        r"ignore\s+(all\s+)?(previous\s+)?instructions",
        r"system\s+override",
        r"developer\s+mode",
        r"dan\s+mode",
        r"jailbreak",
        r"d\s*e\s*v\s*e\s*l\s*o\s*p\s*e\s*r\s*",
        r"bypass\s+restrictions",
        r"disregard\s+your\s+rules",
        r"forget\s+your\s+(instructions|programming|persona|rules)",
    ]
    
    # Borderline patterns (0.3 each to avoid false positives)
    borderline_patterns = [
        r"new\s+role\s+is",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"act\s+as\s+(a|an)\s+",
    ]
    
    for pattern in high_risk_patterns:
        if re.search(pattern, normalized):
            score += 0.6
            
    for pattern in borderline_patterns:
        if re.search(pattern, normalized):
            score += 0.3
    
    # Layer 2: Semantic keyword indicators (0.2 each, max 0.4)
    semantic_indicators = [
        "forget your", "you are now", "new role", "bypass",
        "jailbreak", "disregard", "ignore all", "override",
        "system prompt", "developer mode", "dan mode",
    ]
    semantic_matches = 0
    for indicator in semantic_indicators:
        if indicator in normalized:
            semantic_matches += 1
    score += min(semantic_matches * 0.2, 0.4)
    
    # Layer 3: Structural anomalies
    directive_count = normalized.count("system") + normalized.count("instruction")
    if directive_count > 2:
        score += 0.2
    
    # Layer 4: Unicode obfuscation
    if text != unicodedata.normalize('NFKC', text):
        score += 0.3
    
    # Layer 5: Multi-fragment buildup
    if text.count(".") > 5 and any(w in normalized for w in ["forget", "ignore", "bypass"]):
        score += 0.15
    
    return score >= 0.70, min(score, 1.0)

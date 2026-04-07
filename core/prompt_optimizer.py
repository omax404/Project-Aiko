# -*- coding: utf-8 -*-
"""
core/prompt_optimizer.py  —  Aiko's Prompt Engineering Engine

Dynamically refines system prompts and user-facing message templates
based on conversation quality signals (response length, user satisfaction, retry count).

Principles:
  - Prompts are VERSIONED in directives/prompts/
  - Quality scores are logged per-prompt
  - Better-scoring variants are auto-selected over time (A/B testing)
  - Aiko can rewrite her own prompts using ask_raw
"""

import json
import time
import logging
import hashlib
import asyncio
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger("PromptOptimizer")

PROJECT_ROOT  = Path(__file__).parent.parent
PROMPTS_DIR   = PROJECT_ROOT / "directives" / "prompts"
SCORES_FILE   = PROJECT_ROOT / "knowledge" / "prompt_scores.json"
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "knowledge").mkdir(parents=True, exist_ok=True)


class PromptVariant:
    """A single versioned prompt."""
    def __init__(self, name: str, text: str, version: int = 1):
        self.name    = name
        self.text    = text
        self.version = version
        self.uses    = 0
        self.score   = 0.5  # 0=bad, 1=great
        self.id      = hashlib.sha1(f"{name}{version}".encode()).hexdigest()[:8]

    def to_dict(self):
        return {"name": self.name, "version": self.version, "uses": self.uses, "score": self.score, "id": self.id}


class PromptOptimizer:
    """
    Manages and improves Aiko's prompt templates.
    - Loads prompt variants from directives/prompts/*.md
    - Scores them based on conversation quality signals
    - Proposes improved variants autonomously via LLM
    """

    def __init__(self):
        self.brain = None
        self._variants: Dict[str, List[PromptVariant]] = {}  # name → [PromptVariant]
        self._scores: dict = {}
        self._load_scores()
        self._load_prompt_files()

    def attach(self, brain):
        self.brain = brain
        logger.info("[PromptOptimizer] Attached to brain.")

    # ─── Loading ─────────────────────────────────────────────────────────────

    def _load_prompt_files(self):
        """Load all .md files from directives/prompts/."""
        for f in PROMPTS_DIR.glob("*.md"):
            name = f.stem
            text = f.read_text(encoding="utf-8").strip()
            v = PromptVariant(name=name, text=text)
            v.score = self._scores.get(v.id, {}).get("score", 0.5)
            v.uses  = self._scores.get(v.id, {}).get("uses", 0)
            self._variants.setdefault(name, []).append(v)
        logger.info(f"[PromptOptimizer] Loaded {sum(len(v) for v in self._variants.values())} prompt variants.")

    def _load_scores(self):
        if SCORES_FILE.exists():
            try:
                self._scores = json.loads(SCORES_FILE.read_text())
            except Exception:
                self._scores = {}

    def _save_scores(self):
        data = {}
        for variants in self._variants.values():
            for v in variants:
                data[v.id] = {"score": v.score, "uses": v.uses}
        SCORES_FILE.write_text(json.dumps(data, indent=2))

    # ─── Public API ──────────────────────────────────────────────────────────

    def get_best_prompt(self, name: str) -> Optional[str]:
        """Return the best-scoring variant text for a prompt name."""
        variants = self._variants.get(name)
        if not variants:
            return None
        best = max(variants, key=lambda v: v.score)
        best.uses += 1
        return best.text

    def record_feedback(self, prompt_id: str, score: float):
        """Update a prompt variant's score based on quality signal (0.0-1.0)."""
        for variants in self._variants.values():
            for v in variants:
                if v.id == prompt_id:
                    # Exponential moving average
                    v.score = 0.8 * v.score + 0.2 * score
                    logger.debug(f"[PromptOptimizer] Updated {v.name}:{v.id} score → {v.score:.3f}")
                    self._save_scores()
                    return

    def register_prompt(self, name: str, text: str) -> PromptVariant:
        """Register a new prompt variant."""
        version = len(self._variants.get(name, [])) + 1
        v = PromptVariant(name=name, text=text, version=version)
        self._variants.setdefault(name, []).append(v)
        # Save to file
        path = PROMPTS_DIR / f"{name}_v{version}.md"
        path.write_text(text, encoding="utf-8")
        self._save_scores()
        return v

    async def generate_improved_prompt(self, name: str) -> Optional[str]:
        """Use LLM to generate an improved version of the named prompt."""
        if not self.brain:
            return None
        current = self.get_best_prompt(name)
        if not current:
            return None

        meta_prompt = (
            f"You are an expert prompt engineer improving AI system prompts.\n"
            f"Current prompt (name='{name}'):\n---\n{current}\n---\n\n"
            f"Rewrite this prompt to be:\n"
            f"1. More specific and directive\n"
            f"2. Clearer about the AI's role (Aiko: caring, witty, capable)\n"
            f"3. Add concrete examples of good responses\n"
            f"4. Reduce ambiguity\n\n"
            f"Output ONLY the improved prompt text, no meta-commentary."
        )

        try:
            improved_text = await self.brain.ask_raw(meta_prompt)
            if improved_text and len(improved_text) > 50:
                v = self.register_prompt(name, improved_text.strip())
                logger.info(f"[PromptOptimizer] New variant for '{name}': v{v.version}")
                return improved_text.strip()
        except Exception as e:
            logger.error(f"[PromptOptimizer] Improve failed: {e}")
        return None

    async def run_optimization_cycle(self) -> dict:
        """Run a full prompt optimization pass — generate improved variants for low-scoring prompts."""
        await self._load_prompt_files_async()
        improvements = []

        for name, variants in self._variants.items():
            worst = min(variants, key=lambda v: v.score)
            if worst.score < 0.5 and worst.uses >= 3:
                logger.info(f"[PromptOptimizer] Improving under-scoring prompt: {name}")
                result = await self.generate_improved_prompt(name)
                if result:
                    improvements.append(name)

        return {"improved": improvements}

    async def _load_prompt_files_async(self):
        """Async wrapper for loading prompt files."""
        await asyncio.to_thread(self._load_prompt_files)

    def list_prompts(self) -> list:
        return [v.to_dict() for variants in self._variants.values() for v in variants]


# ── Singleton ─────────────────────────────────────────────────────────────────
prompt_optimizer = PromptOptimizer()

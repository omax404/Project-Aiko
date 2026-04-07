# -*- coding: utf-8 -*-
"""
core/self_coder.py  —  Aiko's Self-Coding Improvement Engine

Aiko can analyze her own source files, identify quality issues,
and autonomously write improved versions using her LLM Brain.

3-Layer Architecture: SOP (directives/coding_assistant.md) → Orchestrate → Execute
"""

import asyncio
import ast
import os
import time
import logging
import hashlib
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger("AikoSelfCoder")

PROJECT_ROOT = Path(__file__).parent.parent

# Files she is allowed to improve autonomously (safe list)
IMPROVABLE_FILES = [
    "core/autonomous_agent.py",
    "core/optimizer.py",
    "core/proactive.py",
    "directives/*.md",
]

# Quality heuristics
MAX_FUNCTION_LINES = 60
MAX_FILE_LINES = 500
MIN_DOCSTRING_COVERAGE = 0.6


class SelfCoder:
    """
    Aiko's autonomous self-improvement engine.
    
    Cycle:
    1. Scan allowed source files for quality issues
    2. Generate improvement proposals via LLM (ask_raw)
    3. Write improved code to .tmp/self_improvements/
    4. Present diff to user for approval (never auto-applies to live code)
    """

    def __init__(self):
        self.brain = None        # Set by attach()
        self.callback: Optional[Callable] = None
        self._output_dir = PROJECT_ROOT / ".tmp" / "self_improvements"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._proposals: list = []  # pending improvement proposals
        self._hashes: dict = {}     # file hash cache (avoid re-analyzing unchanged files)

    def attach(self, brain, callback: Callable = None):
        self.brain = brain
        self.callback = callback
        logger.info("[SelfCoder] Attached to brain.")

    # ─── Public API ──────────────────────────────────────────────────────────

    async def run_improvement_cycle(self) -> list:
        """Scan, analyze, and propose improvements. Returns list of proposals."""
        logger.info("[SelfCoder] Starting improvement cycle...")
        proposals = []

        for pattern in IMPROVABLE_FILES:
            for f in PROJECT_ROOT.glob(pattern):
                if not f.exists() or not f.is_file():
                    continue
                proposal = await self._analyze_file(f)
                if proposal:
                    proposals.append(proposal)

        self._proposals = proposals
        logger.info(f"[SelfCoder] {len(proposals)} improvement proposals generated.")
        return proposals

    async def apply_proposal(self, proposal_id: str) -> bool:
        """Apply a specific proposal to .tmp/self_improvements/ (NOT live code)."""
        for p in self._proposals:
            if p["id"] == proposal_id:
                out_path = self._output_dir / p["filename"]
                out_path.write_text(p["improved_code"], encoding="utf-8")
                logger.info(f"[SelfCoder] Proposal {proposal_id} written to {out_path}")
                return True
        return False

    def list_proposals(self) -> list:
        return [{"id": p["id"], "file": p["file"], "issue": p["issue"]} for p in self._proposals]

    # ─── Internal Logic ──────────────────────────────────────────────────────

    async def _analyze_file(self, path: Path) -> Optional[dict]:
        """Analyze a Python file for quality issues and generate a fix proposal."""
        try:
            source = path.read_text(encoding="utf-8")
        except Exception:
            return None

        # Skip if unchanged since last analysis
        file_hash = hashlib.md5(source.encode()).hexdigest()
        if self._hashes.get(str(path)) == file_hash:
            return None
        self._hashes[str(path)] = file_hash

        issues = self._detect_issues(source, path)
        if not issues:
            return None

        # Build a targeted prompt for the LLM
        issue_str = "\n".join(f"- {i}" for i in issues)
        prompt = (
            f"You are a senior Python engineer reviewing Aiko's own source code.\n"
            f"File: {path.name}\n\n"
            f"Issues found:\n{issue_str}\n\n"
            f"Here is the code:\n```python\n{source[:3000]}\n```\n\n"
            f"Rewrite the COMPLETE improved version of this file, fixing all listed issues. "
            f"Preserve all existing functionality. Add clear docstrings. "
            f"Output ONLY the Python code, no explanations."
        )

        if not self.brain:
            return None

        logger.info(f"[SelfCoder] Generating improvement for {path.name} ({len(issues)} issues)...")
        try:
            improved = await self.brain.ask_raw(prompt)
        except Exception as e:
            logger.error(f"[SelfCoder] LLM call failed: {e}")
            return None

        if not improved or len(improved) < 50:
            return None

        # Strip markdown fences if present
        import re
        improved = re.sub(r'^```python\n|^```\n|```$', '', improved, flags=re.MULTILINE).strip()

        proposal_id = hashlib.sha1(f"{path}{time.time()}".encode()).hexdigest()[:8]
        return {
            "id": proposal_id,
            "file": str(path),
            "filename": path.name,
            "issues": issues,
            "issue": issues[0] if issues else "Quality improvement",
            "original_lines": len(source.splitlines()),
            "improved_code": improved,
        }

    def _detect_issues(self, source: str, path: Path) -> list:
        """Static analysis to find code quality issues."""
        issues = []
        lines = source.splitlines()

        if len(lines) > MAX_FILE_LINES:
            issues.append(f"File is {len(lines)} lines (recommend < {MAX_FILE_LINES})")

        # AST-based checks
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
            return issues

        funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

        # Long functions
        for fn in funcs:
            start = fn.lineno
            end = fn.end_lineno or start
            if (end - start) > MAX_FUNCTION_LINES:
                issues.append(f"Function `{fn.name}` is {end - start} lines (too long)")

        # Missing docstrings
        no_doc = [f.name for f in funcs if not (f.body and isinstance(f.body[0], ast.Expr) and isinstance(f.body[0].value, ast.Constant))]
        if funcs and len(no_doc) / len(funcs) > (1 - MIN_DOCSTRING_COVERAGE):
            issues.append(f"Low docstring coverage: {len(no_doc)}/{len(funcs)} functions missing docs")

        # Broad except clauses
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(f"Bare `except:` at line {node.lineno} — use specific exceptions")
                break

        # TODO / FIXME comments
        todos = [i + 1 for i, l in enumerate(lines) if "# TODO" in l or "# FIXME" in l or "# HACK" in l]
        if todos:
            issues.append(f"Unresolved TODOs/FIXMEs at lines: {todos[:5]}")

        return issues


# ── Singleton ─────────────────────────────────────────────────────────────────
self_coder = SelfCoder()

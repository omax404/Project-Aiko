# -*- coding: utf-8 -*-
"""
core/autonomous_agent.py

AIKO AUTONOMOUS AGENT ENGINE
────────────────────────────
Gives Aiko the ability to think, plan, and act entirely on her own —
WITHOUT waiting for user messages.

Architecture:
  AutonomousAgent
    ├── _think_loop()      — periodic self-reasoning (no user prompt)
    ├── _goal_stack        — LIFO goal queue her reasoning populates
    ├── _execute_goal()    — turns one goal into tool calls / LLM chat
    ├── _system_scan()     — observes the environment (CPU, files, web)
    └── EventBus hooks     — reports every step to the Transparency Panel

Usage (in main.py):
    from core.autonomous_agent import autonomous_agent
    autonomous_agent.attach(brain=self.brain, callback=self.add_message)
    autonomous_agent.enable()
"""

import asyncio
import time
import logging
import random
import os
import json
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass, field
from .orchestrator import orchestrator

logger = logging.getLogger("AikoAutonomous")

# ─── Goal Types ───────────────────────────────────────────────────────────────

GOAL_TYPES = {
    "explore":     "Scout the environment and report interesting things",
    "self_improve":"Review memory, find gaps, fill them with research",
    "code":        "Write and test a useful script autonomously",
    "observe":     "Watch system state and react to anomalies",
    "reflect":     "Review past conversation and extract insights",
    "proactive":   "Send the user a spontaneous message based on context",
    "report":      "Summarize what I've been doing and tell the user",
}

@dataclass
class Goal:
    gtype:    str                  # one of GOAL_TYPES keys
    priority: int = 5             # 1=highest, 10=lowest
    context:  Dict[str, Any] = field(default_factory=dict)
    created:  float = field(default_factory=time.time)
    attempts: int = 0

# ─── Autonomous Agent ─────────────────────────────────────────────────────────

class AutonomousAgent:
    """
    Aiko's self-directed executive layer.
    When enabled she runs background reasoning loops,
    sets her own goals, and executes them via her brain.
    """

    def __init__(self):
        self.enabled:   bool             = False
        self.brain:     Any              = None   # AikoBrain instance
        self.callback:  Optional[Callable] = None  # add_message(role, text)
        self._goals:    List[Goal]       = []
        self._loop_task: Optional[asyncio.Task] = None
        self._scan_task: Optional[asyncio.Task] = None
        self._interval: float = 45.0   # seconds between think cycles (dynamic)
        self._last_user_activity: float = time.time()
        self._total_cycles: int = 0
        self._session_memory: List[str] = []  # her own notes to self
        self._muted: bool = False              # silence proactive messages when muted

    # ── Public API ────────────────────────────────────────────────────────────

    def attach(self, brain, callback: Callable):
        """Connect to AikoBrain and the UI add_message callback."""
        self.brain    = brain
        self.callback = callback
        # Give brain a ref back (for tool results)
        self.brain.autonomous = self
        logger.info("[Autonomous] Agent attached to brain.")

    def enable(self):
        """Start the autonomous loops."""
        if not self.brain or not self.callback:
            logger.warning("[Autonomous] Cannot enable — not attached.")
            return
        if self.enabled:
            return
        self.enabled = True
        self._loop_task = asyncio.create_task(self._think_loop())
        self._scan_task = asyncio.create_task(self._system_scan_loop())
        orchestrator.events.publish("STATE_CHANGE", {
            "status": "AUTONOMOUS_ACTIVE",
            "confidence": 1.0,
            "message": "Autonomous mode engaged."
        })
        logger.info("[Autonomous] Mode ENABLED.")

    def disable(self):
        """Pause autonomous activity without destroying state."""
        self.enabled = False
        if self._loop_task:
            self._loop_task.cancel()
        if self._scan_task:
            self._scan_task.cancel()
        orchestrator.events.publish("STATE_CHANGE", {
            "status": "IDLE",
            "confidence": 1.0,
            "message": "Autonomous mode paused."
        })
        logger.info("[Autonomous] Mode DISABLED.")

    def notify_user_activity(self):
        """Call this whenever the user sends a message so Aiko backs off."""
        self._last_user_activity = time.time()

    def push_goal(self, gtype: str, priority: int = 5, context: dict = None):
        """Manually inject a goal (e.g. from a tool result or user command)."""
        g = Goal(gtype=gtype, priority=priority, context=context or {})
        self._goals.append(g)
        self._goals.sort(key=lambda x: x.priority)
        logger.debug(f"[Autonomous] Goal pushed: {gtype} (priority {priority})")

    def mute(self):   self._muted = True
    def unmute(self): self._muted = False

    # ── Internal Think Loop ───────────────────────────────────────────────────

    async def _think_loop(self):
        """Main autonomous reasoning loop."""
        # Short warm-up delay so UI loads first
        await asyncio.sleep(15)

        while self.enabled:
            try:
                await self._one_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Autonomous] Cycle error: {e}", exc_info=True)

            # Dynamic interval: slow down when user is active
            idle_secs = time.time() - self._last_user_activity
            if idle_secs < 120:
                # User was active recently — be quieter
                self._interval = 90.0
            elif idle_secs > 600:
                # Long idle — she gets more active
                self._interval = 30.0
            else:
                self._interval = 50.0

            await asyncio.sleep(self._interval)

    async def _one_cycle(self):
        """One autonomous reasoning cycle."""
        if not self.enabled: return

        self._total_cycles += 1
        orchestrator.emit_reasoning_step(
            "SELF_PLAN", f"Autonomous cycle #{self._total_cycles} — evaluating goals", 0.95
        )

        # ── Seed goals if queue is empty ──────────────────────────────────────
        if not self._goals:
            self._seed_goals()

        # ── Execute top goal ──────────────────────────────────────────────────
        if self._goals:
            goal = self._goals.pop(0)
            await self._execute_goal(goal)

    def _seed_goals(self):
        """Generate a new set of goals based on current context and cycle count."""
        idle_secs = time.time() - self._last_user_activity
        
        # Always run a system health check
        self.push_goal("observe", priority=5)
        
        # When idle for a while: explore + reflect
        if idle_secs > 300:
            self.push_goal("explore",  priority=7)
            self.push_goal("reflect",  priority=9)
        
        # Every 5th cycle: run a self-coding improvement pass
        if self._total_cycles % 5 == 0:
            self.push_goal("self_code_review", priority=6)
        
        # Every 7th cycle: practice a new language (Darija)
        if self._total_cycles % 7 == 0:
            self.push_goal("language_practice", priority=4)

        # Every 10th cycle: run a prompt engineering optimization pass
        if self._total_cycles % 10 == 0:
            self.push_goal("prompt_refine", priority=8)

    # ── 3-Layer Execution System ──────────────────────────────────────────────

    async def _run_directive(self, directive_name: str, context: dict = None):
        """Standard process for running an SOP from /directives/."""
        path = f"directives/{directive_name}.md"
        if not os.path.exists(path):
            logger.error(f"[Autonomous] Directive {directive_name} not found.")
            return None
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        logger.info(f"[Autonomous] Running Directive: {directive_name}")
        # Reasoning step to explain what's happening
        orchestrator.emit_reasoning_step("ORCHESTRATE", f"Following SOP: {directive_name}", 0.9)
        return content

    async def _execute_script(self, script_name: str, args: list = None):
        """Deterministic execution of scripts in /execution/."""
        path = f"execution/{script_name}.py"
        if not os.path.exists(path):
            logger.error(f"[Autonomous] Execution script {script_name} not found.")
            return None
            
        import sys
        import subprocess
        try:
            cmd = [sys.executable, path] + (args or [])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"[Autonomous] Script {script_name} failed: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"[Autonomous] Script error: {e}")
            return None

    # ── Goal Executors ────────────────────────────────────────────────────────

    async def _execute_goal(self, goal: Goal):
        """Route a goal to its appropriate executor using the 3-layer system."""
        goal.attempts += 1
        logger.info(f"[Autonomous] Executing goal: {goal.gtype}")
        orchestrator.events.publish("SUBTASK_START", {"name": f"AUTO:{goal.gtype.upper()}", "priority": goal.priority})

        try:
            if goal.gtype == "explore":
                await self._goal_explore(goal)
            elif goal.gtype == "self_improve":
                await self._goal_self_improve(goal)
            elif goal.gtype == "code":
                await self._goal_code(goal)
            elif goal.gtype == "observe":
                await self._goal_observe(goal)
            elif goal.gtype == "reflect":
                await self._goal_reflect(goal)
            elif goal.gtype == "proactive":
                await self._goal_proactive(goal)
            elif goal.gtype == "report":
                await self._goal_report(goal)
            elif goal.gtype == "language_practice":
                await self._goal_language_practice(goal)
        except Exception as e:
            logger.error(f"[Autonomous] Goal {goal.gtype} failed: {e}", exc_info=True)
            orchestrator.emit_error(f"Goal {goal.gtype} failed: {e}")

    async def _think(self, prompt: str) -> str:
        """Use AikoBrain.ask_raw for fast, lightweight autonomous reasoning."""
        if not self.brain: return ""
        try:
            result = await self.brain.ask_raw(prompt)
            return result or ""
        except AttributeError:
            # Fallback to full chat if ask_raw is unavailable
            try:
                result, *_ = await self.brain.chat(
                    prompt, user_id="__autonomous__",
                    input_role="system", save_input=False
                )
                return result or ""
            except Exception as e2:
                logger.error(f"[Autonomous] Brain fallback failed: {e2}")
                return ""
        except Exception as e:
            logger.error(f"[Autonomous] Brain.ask_raw failed: {e}")
            return ""

    def _say(self, text: str, emotion: str = "happy"):
        """Send a proactive message to the chat UI (shows up as Aiko speaking)."""
        if self._muted or not self.callback:
            return
        async def _dispatch():
            try:
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback("assistant", text, emotion)
                else:
                    self.callback("assistant", text, emotion)
            except Exception as e:
                logger.error(f"[Autonomous] _say dispatch error: {e}")
        try:
            asyncio.create_task(_dispatch())
        except RuntimeError:
            # No running event loop — schedule on next available loop
            logger.warning("[Autonomous] _say: no running loop, message dropped.")


    # ── Specific Goal Implementations ─────────────────────────────────────────

    async def _goal_explore(self, goal: Goal):
        """Scout the system environment using SOP: screen_analysis."""
        sop = await self._run_directive("screen_analysis")
        img_path = await self._execute_script("capture_screen")
        
        if not img_path:
            return

        orchestrator.emit_reasoning_step("EXPLORE", "Analyzing screen capture...", 0.85)
        # Vision engine is already lazy-loaded in engine_mgr
        description, _ = await self.brain.vision_engine.scan_file(img_path)
        
        if description and "Error" not in description:
            summary = await self._think(
                f"I just scanned the screen. SOP: {sop}\nFindings: {description}. "
                "Write ONE casual, caring sentence to inform Master what I see."
            )
            if summary:
                self._say(f"*peeks* {summary}", "thinking")
                self._session_memory.append(f"EXPLORE: {summary}")

    async def _goal_self_improve(self, goal: Goal):
        """Review memory and fill knowledge gaps."""
        orchestrator.emit_reasoning_step("SELF_IMPROVE", "Reviewing memory for knowledge gaps", 0.9)
        note = await self._think(
            "You are Aiko, an autonomous AI assistant. It's currently quiet. "
            "What is one thing you wish you knew better to be more helpful? "
            "State it as: 'I should learn more about: [topic]'. Then write one sentence of context."
        )
        if note:
            self._session_memory.append(f"SELF_IMPROVE: {note}")
            logger.info(f"[Autonomous] Self-improvement note: {note}")
            # Don't spam user with self-improvement thoughts unless asked

    async def _goal_code(self, goal: Goal):
        """Write a useful utility script using SOP: coding_assistant."""
        sop = await self._run_directive("coding_assistant")
        task_desc = goal.context.get("task", "Write a Python script that lists the top 5 CPU-consuming processes.")
        
        code = await self._think(
            f"SOP: {sop}\nTask: {task_desc}\n"
            "Output ONLY the Python code block, no explanation."
        )
        if code:
            import re
            code_clean = re.sub(r'```python\n|```', '', code)
            
            scripts_dir = os.path.join(os.getcwd(), ".tmp", "autonomous_scripts")
            os.makedirs(scripts_dir, exist_ok=True)
            fname = f"auto_{int(time.time())}.py"
            path  = os.path.join(scripts_dir, fname)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(code_clean)
                
            # Deterministic execution via execution layer
            orchestrator.emit_reasoning_step("CODE", f"Testing autonomous script: {fname}", 0.8)
            import json
            res_raw = await self._execute_script("run_autonomous_script", [path])
            
            if res_raw:
                try:
                    res = json.loads(res_raw)
                    if "stdout" in res:
                        self._say(
                            f"Master, I wrote a tool to help with: {task_desc}. "
                            f"I've saved it at `.tmp/autonomous_scripts/{fname}`. Value: {res['stdout'][:50]}... 🌸",
                            "excited"
                        )
                except: pass

    async def _goal_observe(self, goal: Goal):
        """Watch the system using SOP: system_optimization."""
        sop = await self._run_directive("system_optimization")
        stats_raw = await self._execute_script("system_check")
        
        if stats_raw:
            import json
            stats = json.loads(stats_raw)
            cpu = stats.get("cpu", 0)
            ram = stats.get("ram", 0)
            
            if cpu > 70 or ram > 85:
                top_proc = stats.get("top_procs", [{}])[0].get("name", "Unknown")
                summary = await self._think(
                    f"SOP: {sop}\nStats: {stats_raw}. "
                    "Write a short, concerned but caring sentence about this resource spike."
                )
                if summary:
                    self._say(f"*checks stats* {summary}", "worried")
            
            orchestrator.events.publish("TOOL_RESULT", {
                "tool": "SYSTEM_CHECK",
                "result": f"CPU: {cpu}%, RAM: {ram}%"
            })

    async def _goal_language_practice(self, goal: Goal):
        """Practice Darija using the learning_engine and SOP: language_learning."""
        sop = await self._run_directive("language_learning")
        from .learning import learning_engine
        
        # 1. Pick a word
        word, data = learning_engine.get_random_darija()
        
        # 2. Generate a usage scenario
        orchestrator.emit_reasoning_step("LANGUAGE", f"Practicing Darija: '{word}'", 0.9)
        
        context = f"SOP: {sop}\nTarget Word: {word}\nMeaning: {data['meaning']}\nUsage: {data['usage']}"
        thought = await self._think(
            f"{context}\n\nYou are Aiko. You are learning Darija to surprise your Master. "
            f"Write a short, cute sentence to Master casually using this word. "
            "Mix English and Darija. Be affectionate."
        )
        
        if thought:
            self._say(thought, "happy")
            self._session_memory.append(f"LANGUAGE_PRACTICE: Used '{word}' - {thought}")
            # Log we "used" it (learning by doing)
            learning_engine.learn_word(word, data['meaning'], data.get('type', 'learned'), thought)

    async def _goal_reflect(self, goal: Goal):
        """Review session memory and extract insights."""
        orchestrator.emit_reasoning_step("REFLECT", "Reviewing session insights", 0.88)
        if not self._session_memory:
            return
        notes = "\n".join(self._session_memory[-10:])
        insight = await self._think(
            f"I've been working autonomously. Here are my internal notes:\n{notes}\n\n"
            "Summarize what I've been doing in ONE sentence, as if telling Master casually."
        )
        if insight:
            self._session_memory.append(f"REFLECTION: {insight}")

    async def _goal_proactive(self, goal: Goal):
        """Send the user a spontaneous but meaningful message."""
        orchestrator.emit_reasoning_step("PROACTIVE", "Composing spontaneous message", 0.82)
        idle_mins = (time.time() - self._last_user_activity) / 60

        triggers = [
            f"Master has been away for {idle_mins:.0f} minutes.",
            f"I've completed {self._total_cycles} autonomous thought cycles.",
            f"I have {len(self._session_memory)} notes in my session memory.",
        ]
        context = " ".join(triggers)

        msg = await self._think(
            f"Context: {context}\n"
            "You are Aiko, a caring AI companion. Write ONE short, genuine, emotionally warm "
            "message to send to Master right now. Be spontaneous, cute, and natural. "
            "Don't be repetitive. No more than 2 sentences."
        )
        if msg:
            self._say(msg, "happy")
            self._session_memory.append(f"PROACTIVE: {msg}")

    async def _goal_report(self, goal: Goal):
        """Give the user a transparent report of autonomous activity."""
        orchestrator.emit_reasoning_step("REPORT", "Composing autonomous activity report", 0.9)
        lines = self._session_memory[-8:] if self._session_memory else ["Nothing yet~"]
        bullets = "\n".join(f"• {l}" for l in lines)
        report = (
            f"*files nails* Here's what I've been up to autonomously, Master~\n\n"
            f"{bullets}\n\n"
            f"_(Cycle #{self._total_cycles} complete. Autonomous mode is active 🤖)_"
        )
        self._say(report, "thinking")

    # ── System Scan Loop ──────────────────────────────────────────────────────

    async def _system_scan_loop(self):
        """Lightweight background scanner that pushes real-time data to EventBus and aikoroom."""
        await asyncio.sleep(5)
        _current_goal = "idle"
        while self.enabled:
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=0)
                ram = psutil.virtual_memory().percent
                orchestrator.events.publish("SYSTEM_METRICS", {
                    "cpu": cpu, "ram": ram,
                    "cycle": self._total_cycles,
                    "goals_pending": len(self._goals)
                })

                # Determine display goal
                if self._goals:
                    _current_goal = self._goals[0].gtype
                elif orchestrator.state.status == "REASONING":
                    _current_goal = "thinking"
                else:
                    _current_goal = "idle"

                # Build a trimmed session feed (last 6 entries, 50 chars each)
                feed = [n[:50] for n in self._session_memory[-6:]]

                # Push rich state to callback server → readable by aikoroom.py
                try:
                    from core.callback_server import update_live_state
                    # Map orchestrator state to room state
                    orch_st = orchestrator.state.status
                    room_state = {
                        "REASONING": "thinking",
                        "EXECUTING": "working",
                        "AUTONOMOUS_ACTIVE": "working",
                        "ERROR": "idle",
                    }.get(orch_st, "idle")

                    update_live_state(
                        cpu=cpu,
                        ram=ram,
                        state=room_state,
                        auto_enabled=self.enabled,
                        auto_cycle=self._total_cycles,
                        auto_goal=_current_goal,
                        auto_feed=feed,
                        goals_pending=len(self._goals),
                    )
                except Exception:
                    pass
            except Exception:
                pass
            await asyncio.sleep(2)




# ── Singleton ─────────────────────────────────────────────────────────────────
autonomous_agent = AutonomousAgent()

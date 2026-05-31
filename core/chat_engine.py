"""
AIKO CHAT ENGINE (Brain) - Optimized v2.0
Handles LLM interactions with Local Ollama or OpenAI-compatible APIs using a ReAct Agent Loop.
Optimized for: Speed, Memory, Connection Pooling
"""

import asyncio
import aiohttp
import re
import json
import logging
import os
import base64
import mimetypes
from datetime import datetime
from functools import lru_cache
from dotenv import load_dotenv
from .persona import get_persona_prompt, get_core_brain_prompt, detect_emotion
from .gifs import get_emotion_category, get_random_gif, search_gif
from .game_bridge import game_manager
from .orchestrator import orchestrator
from .sandbox_bridge import SandboxBridge
from .mcp_bridge import mcp_bridge
from .image_engine import ImageEngine
from .utils import retry
from .config_manager import config
from .plugins import PluginManager
from .plugins.game_plugin import GamePlugin
from .plugins.spotify_plugin import SpotifyPlugin


load_dotenv()
logger = logging.getLogger("Brain")
from .config_manager import config

from .agent_executor import (
    AgentExecutor,
    RUN_PYTHON_PATTERN, LATEX_PATTERN, OPEN_PATTERN, TYPE_PATTERN, CLICK_PATTERN, PRESS_PATTERN,
    TASK_PATTERN, NOTE_PATTERN, READ_PATTERN, WRITE_PATTERN, DRAW_PATTERN, VIDEO_PATTERN,
    MCP_PATTERN, IMAGE_PATTERN, GIF_PATTERN, RECALL_PATTERN, BIO_REGISTER_PATTERN
)

# Connection pool - shared across all instances
_session_pool = None

def get_session():
    """Get or create shared aiohttp session with connection pooling."""
    global _session_pool
    if _session_pool is None or _session_pool.closed:
        # Optimized configuration for local & remote/cloud LLM stability
        timeout = aiohttp.ClientTimeout(total=400, connect=20, sock_read=380)
        connector = aiohttp.TCPConnector(
            limit=50,  # Increased capacity
            limit_per_host=20,
            force_close=False,  # Allow Keep-Alive for remote/cloud LLM stability
            enable_cleanup_closed=True
        )
        _session_pool = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={"Accept": "application/json"}
        )
    return _session_pool

async def close_session():
    """Close the shared session - call on shutdown."""
    global _session_pool
    if _session_pool and not _session_pool.closed:
        await _session_pool.close()
        _session_pool = None


class AikoBrain:
    """Aiko's AI brain with Tool Feedback Loop - Optimized."""

    def __init__(self, memory_manager, rag_memory, pc_manager=None, vision_engine=None,
                 vts_connector=None, latex_engine=None, action_bridge=None, obsidian=None):
        self.memory = memory_manager
        self.rag = rag_memory
        self.pc = pc_manager
        self.vision = vision_engine
        self.suppress_speech = False  # New flag for selective silence
        
        self.model = config.get("MODEL_NAME", "deepseek-chat")
        self.vts = vts_connector
        self.latex = latex_engine
        self.bridge = action_bridge
        self.obsidian = obsidian
        self.sandbox = SandboxBridge()
        self.image_engine = ImageEngine()
        self.executor = AgentExecutor()
        
        # Reflective Memory
        self._message_count = 0
        self._reflective_state = ""
        self.model = config.get("MODEL_NAME")
        self.using_fallback = False
        self.on_thinking = None
        self.app_callback = None
        self.on_sentence = None

        # --- PLUGIN ARCHITECTURE ---
        self.plugins = PluginManager()
        self._plugins_ready = False

    async def _init_plugins(self):
        """Initialize and register plugins."""
        if self._plugins_ready:
            return
            
        logger.info("🔌 Loading Aiko Plugins...")
        await self.plugins.register_plugin(GamePlugin())
        await self.plugins.register_plugin(SpotifyPlugin())
        self._plugins_ready = True
        logger.info("✅ Plugins loaded successfully.")

        # OPTIMIZATION: Cache system prompts per user type
        self._cached_prompts = {}
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes

        # Streaming buffer for batching tokens
        self._stream_buffer = ""
        self._stream_timer = None
        self._stream_batch_size = 50  # ms

    def _get_cached_prompt(self, is_master: bool) -> str:
        """Get cached system prompt with time-based invalidation."""
        now = datetime.now().timestamp()
        cache_key = "master" if is_master else "guest"

        # Invalidate cache every 5 minutes (time-of-day changes)
        if now - self._cache_timestamp > self._cache_ttl:
            self._cached_prompts.clear()
            self._cache_timestamp = now

        if cache_key not in self._cached_prompts:
            self._cached_prompts[cache_key] = get_persona_prompt(is_master=is_master)

        return self._cached_prompts[cache_key]

    def _emit_sentence(self, text: str):
        """Emit a complete sentence to the UI streaming callback with emotion detection."""
        # Only suppress if it's a raw system tag or code block
        if not text or text.startswith(("```", "{\"")):
            return
            
        if self.on_sentence:
            try:
                # Detect emotion for this sentence
                emotion = detect_emotion(text)
                
                # Handle async and sync callbacks safely
                if asyncio.iscoroutinefunction(self.on_sentence):
                    asyncio.create_task(self.on_sentence(text, emotion, suppress_audio=self.suppress_speech))
                else:
                    self.on_sentence(text, emotion, suppress_audio=self.suppress_speech)
            except Exception as e:
                logger.error(f"Sentence Callback Error: {e}")

    async def chat(self, message: str, user_id: str = "omax", input_role: str = "user",
                   save_input: bool = True, initial_images: list = None) -> tuple:
        """
        Send message to LLM and get response with ReAct loop.
        Optimized for: Fewer allocations, batched streaming, connection reuse.
        """
        await self._init_plugins()
        # Process Attachments
        processed_images = []
        file_context = ""

        if initial_images:
            processed_images, file_context = await self._process_attachments(initial_images)
            
            if processed_images:
                # Dynamically determine if the active LLM is a vision-capable multimodal model
                active_model = config.get("MODEL_NAME", self.model or "qwen3.5:cloud")
                is_vision_model = any(keyword in active_model.lower() for keyword in ["vision", "vl", "llava", "moondream", "minicpm", "multimodal", "gpt-4o", "claude-3"])
                
                if not is_vision_model and self.vision:
                    logger.info(f"[ChatEngine] Active LLM '{active_model}' is text-only. Pre-processing {len(processed_images)} image(s) using Vision Engine...")
                    for idx, img_b64 in enumerate(processed_images):
                        description = await self.vision.analyze_base64(img_b64)
                        file_context += f"\n[IMAGE_{idx+1}_ANALYSIS]: {description}"
                    # Clear processed_images so we don't send raw bytes to a text-only LLM
                    processed_images = []
                else:
                    file_context += f"\n[VISUAL_INPUT]: {len(processed_images)} image(s) attached. Describe what you see."

            if file_context:
                message = f"{message}\n\n[SENSORY_CONTEXT]:\n{file_context}"

        if save_input:
            self.memory.add_message(user_id, input_role, message)
            self._message_count += 1
            
            # Trigger reflection every 5 messages
            if self._message_count % 5 == 0:
                asyncio.create_task(self._update_reflective_state(user_id))

        if self.on_thinking:
            self.on_thinking(True)

        # RAG Context - offloaded to thread (Enhanced for MemPalace)
        rag_context = ""
        if self.rag and self.rag.is_available():
            try:
                loop = asyncio.get_running_loop()
                results = await loop.run_in_executor(None, self.rag.search_memory, message, 5)
                if results:
                    rag_context = "\n[RECALLED MEMORIES]:\n"
                    for i, res in enumerate(results, 1):
                        meta = res.get('meta', {})
                        source = meta.get('source', 'unknown')
                        room = meta.get('room', 'general')
                        rag_context += f"({i}) [{room} / {source}]: {res['text']}\n"
            except Exception as e:
                logger.warning(f"RAG Async Search Error: {e}")

        history = self.memory.get_history(user_id)

        # Main Thinking Loop (Max 5 turns)
        observations = []
        image_prompts = []
        video_prompts = []
        images_data = processed_images
        final_response = "I'm a bit confused, Master..."
        plugin_context = ""

        logger.info(f" [Brain] Started thinking for user {user_id}: {message[:50]}...")

        for turn in range(5):
            # --- 1. CORE BRAIN (REASONING LAYER) ---
            is_master = str(user_id) in ("omax", os.getenv("MASTER_ID", "766774147832873012"))
            system_prompt = get_core_brain_prompt()

            if self.pc:
                system_prompt += self._get_tools_prompt()

            if rag_context:
                system_prompt += f"\n\n<relevant_memory_context>\n{rag_context[:1000]}\n</relevant_memory_context>"

            messages = [{"role": "system", "content": system_prompt}]

            # Map history - slice to last 20 only
            for h in history[-20:]:
                role = "user" if h["role"] == "system" else h["role"]
                messages.append({"role": role, "content": h["content"]})

            if observations:
                obs_text = "\n".join(observations)
                messages.append({"role": "system", "content": f"[OBSERVATIONS]:\n{obs_text}"})

            # Call LLM
            orchestrator.emit_reasoning_step("AI_THINKING", "Core Engine Reasoning...", 0.90)
            
            # Combine Persona and Tools for single-pass generation
            persona_prompt = self._get_cached_prompt(is_master)
            
            # Add Reflective State if it exists
            if self._reflective_state:
                persona_prompt += f"\n\n[REFLECTIVE_STATE] (Internal emotional context):\n{self._reflective_state}"
                
            # Add tool instructions to the persona prompt
            single_pass_prompt = persona_prompt + "\n\n" + self._get_tools_prompt()
            
            messages = [{"role": "system", "content": single_pass_prompt}]
            for h in history[-20:]:
                role = "user" if h["role"] == "system" else h["role"]
                messages.append({"role": role, "content": h["content"]})
            
            if observations:
                obs_text = "\n".join(observations)
                messages.append({"role": "system", "content": f"[OBSERVATIONS]:\n{obs_text}"})
            
            if plugin_context:
                messages.append({"role": "system", "content": f"[DYNAMIC_CONTEXT]:\n{plugin_context}"})

            text = await self._call_llm(messages, self.model, images=images_data if images_data else None, apply_neuromodulators=True)

            # Check for Tools - use compiled patterns
            has_tool = any(tag in text.upper() for tag in [
                "[OPEN:", "[SCAN]", "[TYPE:", "[CLICK:", "[PRESS:", "[TASK:", "[LATEX:",
                "[GAME:", "[RUN_PYTHON:", "[MCP:", "[IMAGE:", "[BIO_REGISTER]", "[MUSIC:"
            ])
            
            if not has_tool:
                # Conversational response - we are done in one pass!
                final_response = text
                orchestrator.emit_tool_result("Text_Reply", "Message complete.")
                break

            final_response = text
            await self._execute_tools(text, observations, images_data, user_id)

        # Process emotion
        from .emotion_engine import emotion_engine
        emotion_engine.process_text(final_response)
        state = emotion_engine.get_state()
        active_emotion = state["dominant_emotions"][0]

        # Dynamic GIF extraction (Explicit tag or Implicit Emotion matching)
        gif_url = None
        import random
        # 1. Explicit tag: [GIF: query]
        gif_match = GIF_PATTERN.search(final_response)
        if gif_match:
            gif_query = gif_match.group(1).strip()
            gif_url = await search_gif(gif_query)
        # 2. Implicit emotional trigger (35% chance on non-neutral states)
        elif active_emotion not in ("neutral", "thinking", None) and random.random() < 0.35:
            gif_url = await search_gif(f"{active_emotion} girl")

        # Clean Tags - remove XML think/emotion blocks and system tool tags, but PRESERVE personality [Tags]
        cleaned_response = re.sub(r'<think>.*?</think>|<emotion>.*?</emotion>|<.*?>', '', final_response, flags=re.IGNORECASE | re.DOTALL)
        # Only strip technical tool tags [TOOL:...] or [MCP:...] including [GIF:...]
        cleaned_response = re.sub(r'\[(SCAN|MCP|TASK|BIO_REGISTER|GAME|OPEN|TYPE|CLICK|PRESS|WAIT|WALLPAPER|WEATHER|MUSIC|LETTER|VTS_BG|IMAGE|RECALL|LATEX|REFLECTIVE_STATE|GIF)[^\]]*?\]', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n{3,}', '\n\n', cleaned_response).strip()

        # Save & Return
        self.memory.add_message(user_id, "assistant", cleaned_response)
        
        # --- LONG-TERM MEMORY (MemPalace) ---
        if self.rag and self.rag.is_available():
            mem_text = f"User ({user_id}): {message}\nAiko: {cleaned_response}"
            # Commit to semantic archive
            self.rag.add_memory(mem_text, metadata={"type": "conversation", "user_id": str(user_id), "room": "conversations"})

        if self.on_thinking:
            self.on_thinking(False)

        return cleaned_response, active_emotion, image_prompts, video_prompts, "[TASK:" in final_response.upper(), gif_url

    def _get_tools_prompt(self) -> str:
        """Get tools prompt - cached for performance."""
        tools = """\n\n[TOOLS]:\nUse tags to control PC:\n[OPEN: app]\n[TYPE: text]\n[PRESS: key]\n[CLICK: x, y]\n[WAIT: seconds]\n[SCAN] (See screen)\n[WALLPAPER: image_name]\n[TASK: complex goal]\n[WEATHER: city]\n[MUSIC: action]\n[LETTER: message]\n[VTS_BG: name]\n[GAME: minecraft | command]\n[GAME: factorio | command]\n[IMAGE: descriptive prompt]\n[GIF: search_query] (Search and send a Giphy/Tenor GIF matching query)
[RECALL: question | room] (Search my memory palace)
[BIO_REGISTER] (Register Master's face)
[MUSIC: play/pause/skip/prev/now/volume 50/play song name] (Spotify control)"""

        if self.latex:
            tools += "\n[LATEX: code] (Compile LaTeX to PDF)"

        tools += """

[MCP TOOLS — File System & PC State]:
Use these tags to interact with Master's PC directly:
- [MCP: sysinfo]                         → Get CPU, RAM, disk, battery, uptime
- [MCP: processes | name_filter]         → List running processes
- [MCP: downloads]                        → See Master's Downloads folder
- [MCP: desktop]                          → See Master's Desktop
- [MCP: list_dir | C:/path/to/dir]       → List any allowed directory
- [MCP: read_file | C:/path/to/file.txt] → Read a text file (first 200 lines)
- [MCP: write_file | C:/path/to/file.txt | content here] → Write/create a file
- [MCP: find_files | *.py]               → Search for files by pattern
- [MCP: run_cmd | dir /b C:/Users/Master/Desktop] → Run a safe shell command
- [MCP: clipboard]                        → Read clipboard content
- [MCP: set_clipboard | text to copy]    → Write to clipboard
- [MCP: kill_proc | 1234]                → Kill a process by PID

Use MCP tools whenever Master asks about his PC state, files, or wants you to read/write something."""
        return tools

    async def _execute_tools(self, text: str, observations: list, images_data: list, user_id: str):
        """Execute tools found in the text with Identity-Based Authorization."""
        await self.executor.execute_tools(self, text, observations, images_data, user_id)

    async def _process_attachments(self, attachment_paths_or_urls: list) -> tuple:
        """Process local file paths or URLs for vision/context."""
        images = []
        context_parts = []
        import base64

        IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff', '.avif'}

        for source in attachment_paths_or_urls:
            try:
                content = None
                filename = os.path.basename(source)
                
                if os.path.exists(source):
                    with open(source, 'rb') as f:
                        content = f.read()
                else:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(source) as resp:
                            if resp.status == 200:
                                content = await resp.read()

                if not content: continue

                # Determine if this is an image using extension OR mimetypes
                ext = os.path.splitext(source.lower())[1]
                mime_type, _ = mimetypes.guess_type(source)
                is_image = ext in IMAGE_EXTENSIONS or (mime_type and mime_type.startswith('image/'))

                if is_image:
                    b64 = base64.b64encode(content).decode('utf-8')
                    images.append(b64)
                    context_parts.append(f"[User attached image: {filename}]")
                    logger.info(f"[Attachment] Processed image: {filename} ({len(content)} bytes)")
                else:
                    # Text/Code Handling
                    try:
                        text = content.decode('utf-8', errors='ignore')
                        context_parts.append(f"Content of {filename}:\n```\n{text[:2000]}\n```")
                    except:
                        context_parts.append(f"[File attached: {filename}]")

            except Exception as e:
                logger.error(f"Attachment Error {source}: {e}")

        return images, "\n".join(context_parts)

    async def _call_llm(self, messages, model=None, images=None, apply_neuromodulators=False):
        """
        Call LLM with automatic fallback and connection pooling.
        Optimized for streaming with sentence-level emission.
        """
        PROVIDER = config.get("PROVIDER", "Ollama")
        MODEL = config.get("MODEL_NAME", model or "qwen3.5:cloud")
        FALLBACK_URL = config.get("FALLBACK_URL", "http://127.0.0.1:1234/v1/chat/completions")
        FALLBACK_MODEL = config.get("FALLBACK_MODEL", "qwen3.5-4b:2")
        API_KEY = config.get("API_KEY", "")

        session = get_session()

        async def stream_openai(url: str, mdl: str, msgs: list, key: str = "") -> tuple:
            """Stream from OpenAI-compatible endpoint."""
            headers = {"Content-Type": "application/json"}
            if key:
                headers["Authorization"] = f"Bearer {key}"
            if "openrouter.ai" in url:
                headers["HTTP-Referer"] = "https://aiko-desktop.local"
                headers["X-Title"] = "Aiko Desktop"

            if apply_neuromodulators:
                from core.emotion_engine import emotion_engine
                modifiers = emotion_engine.get_inference_modifiers()
            else:
                modifiers = {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "presence_penalty": 0.0,
                    "frequency_penalty": 0.0,
                    "max_tokens": 2000
                }

            payload = {
                "model": mdl,
                "messages": msgs,
                "stream": True,
                "temperature": modifiers["temperature"],
                "top_p": modifiers["top_p"],
                "presence_penalty": modifiers["presence_penalty"],
                "frequency_penalty": modifiers["frequency_penalty"],
                "max_tokens": modifiers["max_tokens"]
            }

            try:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error(f"[Brain] {url} → {resp.status}: {body[:200]}")
                        return None, resp.status

                    full = ""
                    cur = ""
                    stream_completed = False
                    async for line in resp.content:
                        if not line:
                            continue
                        
                        decoded = line.decode("utf-8").strip()
                        if not decoded:
                            continue
                        if decoded == "data: [DONE]":
                            stream_completed = True
                            continue
                        if decoded.startswith("data: "):
                            decoded = decoded[6:]
                        
                        try:
                            data = json.loads(decoded)
                            # Handle standard OpenAI
                            if "choices" in data:
                                tok = data["choices"][0].get("delta", {}).get("content", "")
                            # Handle LM Studio / Ollama-style wrap in api/v1/chat
                            elif "message" in data:
                                tok = data["message"].get("content", "")
                            # Handle direct response field
                            else:
                                tok = data.get("response", data.get("content", ""))
                        except:
                            continue
                        
                        if not tok:
                            continue
                        full += tok
                        cur += tok
                        if any(cur.endswith(p) for p in [".", "!", "?", "\n", "。", "！", "？"]):
                            self._emit_sentence(cur.strip())
                            cur = ""

                    if cur.strip():
                        self._emit_sentence(cur.strip())
                    
                    if not stream_completed and full:
                        logger.warning(f"[Brain] Warning: OpenAI stream from {url} was closed prematurely.")
                        full += f"\n\n*(Note: Connection to {PROVIDER} was closed prematurely by the server/proxy. The response may be incomplete.)*"

                    return full, 200

            except asyncio.TimeoutError:
                logger.error(f"[Brain] Timeout → {url}")
                return None, 408
            except Exception as e:
                logger.error(f"[Brain] Error → {url}: {e}")
                return None, 500

        async def stream_ollama(mdl: str, msgs: list, imgs: list) -> tuple:
            """Stream from Ollama native API."""
            url = config.get("LLM_URL", "http://127.0.0.1:11434/api/chat")
            if not url.endswith(("/chat", "/api/chat")):
                if url.endswith("/api") or url.endswith("/api/"):
                    url = url.rstrip("/") + "/chat"
                else:
                    url = url.rstrip("/") + "/api/chat"

            headers = {}
            if API_KEY:
                headers["Authorization"] = f"Bearer {API_KEY}"

            ollama_msgs = []
            # Find the index of the LAST user message to attach images to
            last_user_idx = -1
            if imgs:
                for i in range(len(msgs) - 1, -1, -1):
                    if msgs[i]["role"] == "user":
                        last_user_idx = i
                        break

            for i, m in enumerate(msgs):
                om = {"role": m["role"], "content": m["content"]}
                if imgs and i == last_user_idx:
                    om["images"] = imgs
                ollama_msgs.append(om)

            if apply_neuromodulators:
                from core.emotion_engine import emotion_engine
                modifiers = emotion_engine.get_inference_modifiers()
            else:
                modifiers = {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "presence_penalty": 0.0,
                    "frequency_penalty": 0.0,
                    "max_tokens": 2000
                }

            payload = {
                "model": mdl,
                "messages": ollama_msgs,
                "stream": True,
                "think": False,
                "options": {
                    "temperature": modifiers["temperature"], 
                    "top_p": modifiers["top_p"],
                    "presence_penalty": modifiers["presence_penalty"],
                    "frequency_penalty": modifiers["frequency_penalty"],
                    "num_ctx": 4096,
                    "num_predict": modifiers["max_tokens"]
                }
            }

            try:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error(f"[Brain] Ollama → {resp.status}: {body[:200]}")
                        return None, resp.status

                    full = ""
                    cur = ""
                    stream_completed = False
                    async for line in resp.content:
                        if not line:
                            continue
                        
                        decoded = line.decode("utf-8").strip()
                        if not decoded: continue
                        
                        # Handle potential merged lines in chunk
                        for single_json in decoded.split('\n'):
                            if not single_json.strip(): continue
                            try:
                                data = json.loads(single_json)
                                if data.get("done") is True:
                                    stream_completed = True
                                tok = data.get("message", {}).get("content", "")
                            except:
                                continue
                                
                            if not tok:
                                continue
                            
                            logger.info(f" [ChatEngine] Token rcvd: '{tok}'")
                            full += tok
                            cur += tok
                            
                            if any(cur.endswith(p) for p in [".", "!", "?", "\n", "。", "！", "？"]):
                                self._emit_sentence(cur.strip())
                                cur = ""

                    if cur.strip():
                        self._emit_sentence(cur.strip())

                    if not stream_completed and full:
                        logger.warning(f"[Brain] Warning: Ollama stream from {url} was closed prematurely.")
                        full += f"\n\n*(Note: Connection to {PROVIDER} Cloud was closed prematurely by the server/proxy. The response may be incomplete.)*"

                    return full, 200

            except asyncio.TimeoutError:
                logger.error("[Brain] Timeout → Ollama")
                return None, 408
            except Exception as e:
                logger.error(f"[Brain] Error → Ollama: {e}")
                return None, 500

        def inject_vision_openai(msgs: list, imgs: list) -> list:
            """Add base64 images to last user message."""
            if not imgs:
                return msgs
            out = list(msgs)
            for i in range(len(out) - 1, -1, -1):
                if out[i]["role"] == "user":
                    parts = [{"type": "text", "text": out[i]["content"]}]
                    for b64 in imgs:
                        img_data = b64.split(",", 1)[-1] if "," in b64 else b64
                        parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}
                        })
                    out[i] = {**out[i], "content": parts}
                    break
            return out

        logger.info(f"[Brain] Calling {PROVIDER} / {MODEL}")

        if PROVIDER == "Ollama":
            content, status = await stream_ollama(MODEL, messages, images or [])
        else:
            vision_msgs = inject_vision_openai(messages, images or [])
            primary_url = config.get("LLM_URL", "http://127.0.0.1:11434/api")
            content, status = await stream_openai(primary_url, MODEL, vision_msgs, API_KEY)

        if content:
            return content

        # Provider-aware dynamic error messages
        if status == 408:
            return f"{PROVIDER} is taking too long to think. (Timeout)"
        if status == 404:
            if PROVIDER == "Ollama":
                return f"Model '{MODEL}' not found. Run: `ollama pull {MODEL}`"
            else:
                return f"Model '{MODEL}' not found on {PROVIDER}."
        if status == 401:
            return f"API key rejected by {PROVIDER}. Check your credentials."
        return f"{PROVIDER} is unreachable or returned an error. (Error {status})"

    async def _update_reflective_state(self, user_id: str):
        """Generates a summary of the current emotional dynamic."""
        try:
            history = self.memory.get_history(user_id)[-10:]
            if not history:
                return
            
            prompt = (
                "Summarize the emotional dynamic and context of this conversation in 1-2 short sentences. "
                "Focus on Aiko's mood towards the user (e.g., 'Aiko is currently annoyed but affectionate')."
            )
            messages = [{"role": "system", "content": prompt}]
            for h in history:
                role = "user" if h["role"] == "system" else h["role"]
                messages.append({"role": role, "content": h["content"]})
                
            # Use the unified LLM caller instead of hardcoded Ollama endpoint
            content = await self._call_llm(messages, apply_neuromodulators=False)
            if content:
                self._reflective_state = content.strip()
                logger.info(f"🧠 Reflection Updated: {self._reflective_state}")
        except Exception as e:
            logger.error(f"Failed to update reflective state: {e}")

    async def ask_raw(self, prompt: str) -> str:
        """Lightweight direct call — bypasses tools, uses current model."""
        messages = [
            {"role": "system", "content": "You are a helpful JSON assistant. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        return await self._call_llm(messages, self.model)

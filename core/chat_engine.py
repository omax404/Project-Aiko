"""core/chat_engine.py
AikoBrain — thin orchestrator. Delegates all heavy work to infrastructure modules.
"""
import asyncio
import re
import json
import logging
import os
import mimetypes
from datetime import datetime
from dotenv import load_dotenv

from core.persona import get_persona_prompt, get_core_brain_prompt, detect_emotion
from core.gifs import get_emotion_category, get_random_gif, search_gif
from core.orchestrator import orchestrator
from core.sandbox_bridge import SandboxBridge
from core.config_manager import config
from core.plugins import PluginManager
from core.plugins.game_plugin import GamePlugin
from core.plugins.spotify_plugin import SpotifyPlugin

# Import extracted infrastructure functions
from core.infrastructure.llm.streaming import get_session, close_session, stream_openai, stream_ollama
from core.infrastructure.tools.executor import AgentExecutor, GIF_PATTERN
from core.infrastructure.rag.context_builder import build_rag_context
from core.infrastructure.media.generator import handle_generate_command, handle_selfie_request

load_dotenv()
logger = logging.getLogger("Brain")

STICKER_MAPPING = {
    "hello": "07_Waving_Hello.png",
    "waving": "07_Waving_Hello.png",
    "happy_umbrella": "01_Happy_Cheer.png",
    "cheering": "01_Happy_Cheer.png",
    "ssr_star_eyes": "01_Happy_Cheer.png",
    "wink": "14_Winking_Peace.png",
    "lol": "11_Laughing.png",
    "victory": "14_Winking_Peace.png",
    "heart_eyes": "09_Heart_Eyes_Rose.png",
    "present": "09_Heart_Eyes_Rose.png",
    "cup": "17_Teacup_Sip.png",
    "singing": "09_Heart_Eyes_Rose.png",
    "thumbs_up": "06_Confident_Smirk_Right.png",
    "proud": "06_Confident_Smirk_Right.png",
    "thinking": "08_Thinking_Pose.png",
    "reading": "08_Thinking_Pose.png",
    "studying": "08_Thinking_Pose.png",
    "idea": "08_Thinking_Pose.png",
    "surprised": "03_Surprised_Gasp.png",
    "shocked": "03_Surprised_Gasp.png",
    "shy_blush": "02_Shy_Blush.png",
    "shy_smile": "02_Shy_Blush.png",
    "pouty_umbrella": "10_Annoyed_Pout.png",
    "angry_dagger": "10_Annoyed_Pout.png",
    "confused": "15_Sick_Dizzy.png",
    "sweatdrop": "15_Sick_Dizzy.png",
    "dizzy": "15_Sick_Dizzy.png",
    "sleeping": "04_Sleepy_Yawn.png",
    "sleeping_zzz": "04_Sleepy_Yawn.png",
    "crying_tears": "05_Crying_Comical.png"
}

def translate_stickers(text: str) -> str:
    """Helper to translate virtual /stickers/lavender_<mood>.png to actual local paths."""
    if not text:
        return text
    def repl(match):
        alt = match.group(1)
        mood = match.group(2)
        mapped = STICKER_MAPPING.get(mood.lower())
        if mapped:
            return f"![{alt}](/stickers/{mapped})"
        return match.group(0)
    return re.sub(r'!\[([^\]]*)\]\(/stickers/lavender_([a-zA-Z0-9_-]+)\.png\)', repl, text)


class AikoBrain:
    """Aiko's AI brain with Tool Feedback Loop - Optimized."""

    def __init__(self, memory_manager, rag_memory, pc_manager=None, vision_engine=None,
                 vts_connector=None, latex_engine=None, action_bridge=None, obsidian=None) -> None:
        self.memory = memory_manager
        self.rag = rag_memory
        self.pc = pc_manager
        self.vision = vision_engine
        self.suppress_speech = False
        
        self.model = config.get("MODEL_NAME", "deepseek-chat")
        self.vts = vts_connector
        self.latex = latex_engine
        self.bridge = action_bridge
        self.obsidian = obsidian
        self.sandbox = SandboxBridge()
        self.executor = AgentExecutor()
        
        self._message_count = 0
        self._reflective_state = ""
        self.using_fallback = False
        self.on_thinking = None
        self.app_callback = None
        self.on_sentence = None

        self._cached_prompts = {}
        self._cache_timestamp = 0
        self._cache_ttl = 300

        self._stream_buffer = ""
        self._stream_timer = None
        self._stream_batch_size = 50

        self.plugins = PluginManager()
        self._plugins_ready = False

    async def _init_plugins(self) -> None:
        """Initialize and register plugins."""
        if self._plugins_ready:
            return
            
        logger.info("🔌 Loading Aiko Plugins...")
        await self.plugins.register_plugin(GamePlugin())
        await self.plugins.register_plugin(SpotifyPlugin())
        self._plugins_ready = True
        logger.info("✅ Plugins loaded successfully.")

    def _get_cached_prompt(self, is_master: bool) -> str:
        """Get cached system prompt with time-based invalidation."""
        now = datetime.now().timestamp()
        cache_key = "master" if is_master else "guest"

        if now - self._cache_timestamp > self._cache_ttl:
            self._cached_prompts.clear()
            self._cache_timestamp = now

        if cache_key not in self._cached_prompts:
            self._cached_prompts[cache_key] = get_persona_prompt(is_master=is_master)

        return self._cached_prompts[cache_key]

    def _emit_sentence(self, text: str) -> None:
        """Emit a complete sentence to the UI streaming callback with emotion detection."""
        text = translate_stickers(text)
        if not text or text.startswith(("```", "{\"")):
            return
            
        if self.on_sentence:
            try:
                emotion = detect_emotion(text)
                if asyncio.iscoroutinefunction(self.on_sentence):
                    asyncio.create_task(self.on_sentence(text, emotion, suppress_audio=self.suppress_speech))
                else:
                    self.on_sentence(text, emotion, suppress_audio=self.suppress_speech)
            except Exception as e:
                logger.error(f"Sentence Callback Error: {e}")

    async def chat(self, message: str, user_id: str = "user", input_role: str = "user",
                   save_input: bool = True, initial_images: list = None) -> tuple:
        """
        Send message to LLM and get response with ReAct loop.
        """
        await self._init_plugins()

        # Check if the user is calling the /generate command
        if message.strip().startswith("/generate"):
            if save_input:
                self.memory.add_message(user_id, input_role, message)
            text_reply, emotion = await handle_generate_command(message, self, user_id, save_input)
            if save_input:
                self.memory.add_message(user_id, "assistant", text_reply)
            self._emit_sentence(text_reply)
            return text_reply, emotion, [], [], False, None

        # Process Attachments
        processed_images = []
        file_context = ""

        if initial_images:
            processed_images, file_context = await self._process_attachments(initial_images)
            
            if processed_images:
                active_model = config.get("MODEL_NAME", self.model or "qwen3.5:cloud")
                is_vision_model = any(keyword in active_model.lower() for keyword in ["vision", "vl", "llava", "moondream", "minicpm", "multimodal", "gpt-4o", "claude-3"])
                
                if not is_vision_model and self.vision:
                    logger.info(f"[ChatEngine] Active LLM '{active_model}' is text-only. Pre-processing {len(processed_images)} image(s) using Vision Engine...")
                    for idx, img_b64 in enumerate(processed_images):
                        description = await self.vision.analyze_base64(img_b64)
                        file_context += f"\n[IMAGE_{idx+1}_ANALYSIS]: {description}"
                    processed_images = []
                else:
                    file_context += f"\n[VISUAL_INPUT]: {len(processed_images)} image(s) attached. Describe what you see."

            if file_context:
                message = f"{message}\n\n[SENSORY_CONTEXT]:\n{file_context}"

        if save_input:
            self.memory.add_message(user_id, input_role, message)
            self._message_count += 1
            if self._message_count % 5 == 0:
                asyncio.create_task(self._update_reflective_state(user_id))

        if self.on_thinking:
            self.on_thinking(True)

        # RAG Context (extracted to infrastructure)
        rag_context = await build_rag_context(self.rag, message, 5)
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
            master_id = os.getenv("MASTER_ID", "")
            is_master = master_id and str(user_id) == master_id
            static_persona = self._get_cached_prompt(is_master) + "\n\n" + self._get_tools_prompt()
            
            dynamic_context = ""
            if self._reflective_state:
                dynamic_context += f"\n\n[REFLECTIVE_STATE] (Internal emotional context):\n{self._reflective_state}"
                
            if rag_context:
                dynamic_context += f"\n\n<relevant_memory_context>\n{rag_context[:1000]}\n</relevant_memory_context>"

            from core.vision_context import vision_context_buffer
            vision_ctx = vision_context_buffer.get_context_string()
            if vision_ctx:
                dynamic_context += f"\n\n<current_visual_awareness>\n{vision_ctx}\n</current_visual_awareness>"

            # Structured system prompt with cache_control for static persona + tools prefix
            system_content = [
                {
                    "type": "text",
                    "text": static_persona,
                    "cache_control": {"type": "ephemeral"}
                }
            ]
            if dynamic_context.strip():
                system_content.append({
                    "type": "text",
                    "text": dynamic_context.strip()
                })

            messages = [{"role": "system", "content": system_content}]
            
            for h in history[-20:]:
                role = "user" if h["role"] == "system" else h["role"]
                messages.append({"role": role, "content": h["content"]})
            
            if observations:
                obs_text = "\n".join(observations)
                messages.append({"role": "system", "content": f"[OBSERVATIONS]:\n{obs_text}"})
            
            if plugin_context:
                messages.append({"role": "system", "content": f"[DYNAMIC_CONTEXT]:\n{plugin_context}"})

            text = await self._call_llm(messages, self.model, images=images_data if images_data else None, apply_neuromodulators=True)

            has_tool = any(tag in text.upper() for tag in [
                "[OPEN:", "[SCAN]", "[TYPE:", "[CLICK:", "[PRESS:", "[TASK:", "[LATEX:",
                "[GAME:", "[EXEC:", "[MCP:", "[IMAGE:", "[BIO_REGISTER]", "[MUSIC:"
            ])
            
            if not has_tool:
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

        # Dynamic GIF extraction
        gif_url = None
        import random
        gif_match = GIF_PATTERN.search(final_response)
        if gif_match:
            gif_query = gif_match.group(1).strip()
            gif_url = await search_gif(gif_query)
        elif active_emotion not in ("neutral", "thinking", None) and random.random() < 0.35:
            gif_url = await search_gif(f"{active_emotion} girl")

        # Clean Tags
        cleaned_response = re.sub(r'<(think|emotion|thought|relevant_memory_context|current_visual_awareness)>.*?</\1>', '', final_response, flags=re.IGNORECASE | re.DOTALL)
        cleaned_response = re.sub(r'</?(think|emotion|thought|relevant_memory_context|current_visual_awareness)>', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\[(SCAN|MCP|TASK|BIO_REGISTER|GAME|OPEN|TYPE|CLICK|PRESS|WAIT|WALLPAPER|WEATHER|MUSIC|LETTER|VTS_BG|IMAGE|RECALL|LATEX|REFLECTIVE_STATE|GIF)[^\]]*?\]', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n{3,}', '\n\n', cleaned_response).strip()
        cleaned_response = translate_stickers(cleaned_response)

        # Check if the user requested a selfie/pic
        is_selfie_req = any(kw in message.lower() for kw in [
            "send me a selfie", "send a selfie", "take a selfie", 
            "send me a pic", "send a pic", "send me a picture",
            "send a photo", "send me a photo", "show yourself", 
            "how do you look", "how are you looking"
        ])
        
        if is_selfie_req:
            selfie_md = await handle_selfie_request(self, user_id, save_input)
            if selfie_md:
                cleaned_response += selfie_md

        # Save & Return
        if save_input:
            self.memory.add_message(user_id, "assistant", cleaned_response)
            if self.rag and self.rag.is_available():
                mem_text = f"User ({user_id}): {message}\nAiko: {cleaned_response}"
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
- [MCP: uia_list]                         → List all open windows and window titles
- [MCP: uia_list | Window Title]          → List all child controls inside a window (buttons, text inputs, etc.)
- [MCP: uia_click | Window Title | Control Name] → Click a button or UI element inside a specific window
- [MCP: uia_type | Window Title | Control Name | text] → Click and type text into a text field inside a specific window

Use MCP tools whenever Master asks about his PC state, files, wants you to read/write something, or wants to interact with desktop applications."""
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
                    local_upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads", filename)
                    if os.path.exists(local_upload_path):
                        with open(local_upload_path, 'rb') as f:
                            content = f.read()
                    else:
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            async with session.get(source) as resp:
                                if resp.status == 200:
                                    content = await resp.read()

                if not content: continue

                ext = os.path.splitext(source.lower())[1]
                mime_type, _ = mimetypes.guess_type(source)
                is_image = ext in IMAGE_EXTENSIONS or (mime_type and mime_type.startswith('image/'))

                if is_image:
                    b64 = base64.b64encode(content).decode('utf-8')
                    images.append(b64)
                    context_parts.append(f"[User attached image: {filename}]")
                    logger.info(f"[Attachment] Processed image: {filename} ({len(content)} bytes)")
                else:
                    try:
                        text = content.decode('utf-8', errors='ignore')
                        context_parts.append(f"Content of {filename}:\n```\n{text[:2000]}\n```")
                    except (UnicodeDecodeError, OSError) as e:
                        logger.warning(f"Failed to decode attachment text for {filename}: {e}")
                        context_parts.append(f"[File attached: {filename}]")

            except (OSError, ValueError, TypeError) as e:
                logger.error(f"Attachment Error {source}: {e}")

        return images, "\n".join(context_parts)

    async def _call_llm(self, messages, model=None, images=None, apply_neuromodulators=False):
        """Call LLM with connection pooling."""
        PROVIDER = config.get("PROVIDER", "Ollama")
        MODEL = config.get("MODEL_NAME", model or "qwen3.5:cloud")
        API_KEY = config.get("API_KEY", "")

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

        try:
            if PROVIDER == "Ollama":
                url = config.get("LLM_URL", "http://127.0.0.1:11434/api/chat")
                if not url:
                    url = "http://127.0.0.1:11434/api/chat"
                content, status = await stream_ollama(
                    url=url, model=MODEL, messages=messages, images=images,
                    api_key=API_KEY, modifiers=modifiers, emit_callback=self._emit_sentence
                )
            else:
                primary_url = config.get("LLM_URL", "")
                if not primary_url:
                    if PROVIDER.lower() == "cloud":
                        return "Master, since you configured Aiko to use a Cloud provider, please enter your cloud endpoint URL (e.g., OpenRouter or custom Ollama cloud) in Settings (user_settings.json). (⁠ꈍ⁠ᴗ⁠ꈍ⁠)"
                    primary_url = "http://127.0.0.1:11434/v1/chat/completions"
                
                content, status = await stream_openai(
                    url=primary_url, model=MODEL, messages=messages, images=images,
                    api_key=API_KEY, modifiers=modifiers, emit_callback=self._emit_sentence
                )
        except Exception as conn_err:
            logger.error(f"[Brain] LLM connection failed: {conn_err}")
            return f"Ehh? I couldn't connect to your LLM provider '{PROVIDER}', Master. Please check if your LLM server/cloud URL is active and reachable. (Error: {str(conn_err)}) (⁠ꈍ⁠ᴗ⁠ꈍ⁠)"

        if content:
            return content

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
                
            content = await self._call_llm(messages, apply_neuromodulators=False)
            if content:
                self._reflective_state = content.strip()
                logger.info(f"🧠 Reflection Updated: {self._reflective_state}")
        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to update reflective state: {e}")

    async def ask_raw(self, prompt: str) -> str:
        """Lightweight direct call — bypasses tools, uses current model."""
        messages = [
            {"role": "system", "content": get_persona_prompt(is_master=True)},
            {"role": "user", "content": prompt}
        ]
        return await self._call_llm(messages, self.model)

# core/infrastructure/llm/streaming.py
import aiohttp
import asyncio
import json
import logging
from typing import Callable, Optional, Tuple, List
from core.config_manager import config
from core.utils import verify_connection_safety

logger = logging.getLogger("LLMStreaming")

# Connection pool - shared across all instances
_session_pool = None

def get_session() -> aiohttp.ClientSession:
    """Get or create shared aiohttp session with connection pooling."""
    global _session_pool
    if _session_pool is None or _session_pool.closed:
        timeout = aiohttp.ClientTimeout(total=400, connect=20, sock_read=380)
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=20,
            force_close=False,
        )
        _session_pool = aiohttp.ClientSession(connector=connector, timeout=timeout)
    return _session_pool

async def close_session():
    """Explicitly clean up session pool on app teardown."""
    global _session_pool
    if _session_pool and not _session_pool.closed:
        await _session_pool.close()

def inject_vision_openai(msgs: List[dict], imgs: List[str]) -> List[dict]:
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

def prepare_messages_for_api(msgs: List[dict], imgs: List[str], url: str) -> List[dict]:
    """Prepare messages for OpenAI / OpenRouter / Ollama APIs, handling vision & prompt caching."""
    out = list(msgs)
    is_openrouter = "openrouter.ai" in url or "anthropic.com" in url or "deepseek" in url
    
    # Flatten array contents if endpoint doesn't support structured system content
    normalized = []
    for m in out:
        role = m.get("role")
        content = m.get("content")
        if isinstance(content, list) and role == "system" and not is_openrouter:
            # Flatten to plain string for basic text endpoints
            text_parts = [part.get("text", "") for part in content if isinstance(part, dict) and "text" in part]
            normalized.append({"role": role, "content": "\n\n".join(filter(None, text_parts))})
        else:
            normalized.append(m)
            
    return inject_vision_openai(normalized, imgs)

async def stream_openai(
    url: str,
    model: str,
    messages: List[dict],
    images: Optional[List[str]],
    api_key: str,
    modifiers: dict,
    emit_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[Optional[str], int]:
    """Stream from OpenAI-compatible endpoint."""
    verify_connection_safety(url)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if "openrouter.ai" in url:
        headers["HTTP-Referer"] = "https://aiko-desktop.local"
        headers["X-Title"] = "Aiko Desktop"

    # Inject images & prepare prompt caching
    processed_messages = prepare_messages_for_api(messages, images or [], url)

    payload = {
        "model": model,
        "messages": processed_messages,
        "stream": True,
        "temperature": modifiers["temperature"],
        "top_p": modifiers["top_p"],
        "presence_penalty": modifiers["presence_penalty"],
        "frequency_penalty": modifiers["frequency_penalty"],
        "max_tokens": modifiers["max_tokens"]
    }

    session = get_session()
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
                    if "choices" in data:
                        tok = data["choices"][0].get("delta", {}).get("content", "")
                    elif "message" in data:
                        tok = data["message"].get("content", "")
                    else:
                        tok = data.get("response", data.get("content", ""))
                except Exception as e:
                    logger.debug(f"JSON parsing failed for stream chunk: {e}")
                    continue
                
                if not tok:
                    continue
                full += tok
                cur += tok
                if emit_callback and any(cur.endswith(p) for p in [".", "!", "?", "\n", "。", "！", "？"]):
                    emit_callback(cur.strip())
                    cur = ""

            if emit_callback and cur.strip():
                emit_callback(cur.strip())
            
            if not stream_completed and full:
                provider = config.get("PROVIDER", "Ollama")
                logger.warning(f"[Brain] Warning: OpenAI stream from {url} was closed prematurely.")
                full += f"\n\n*(Note: Connection to {provider} was closed prematurely by the server/proxy. The response may be incomplete.)*"

            return full, 200

    except asyncio.TimeoutError:
        logger.error(f"[Brain] Timeout → {url}")
        return None, 408
    except (aiohttp.ClientError, aiohttp.ServerDisconnectedError, ConnectionError, OSError) as e:
        logger.error(f"[Brain] Network Error → {url}: {e}")
        return None, 500
    except (TypeError, ValueError, KeyError) as e:
        logger.error(f"[Brain] Data Error → {url}: {e}")
        return None, 500

async def stream_ollama(
    url: str,
    model: str,
    messages: List[dict],
    images: Optional[List[str]],
    api_key: str,
    modifiers: dict,
    emit_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[Optional[str], int]:
    """Stream from Ollama native API."""
    verify_connection_safety(url)

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    ollama_msgs = []
    last_user_idx = -1
    if images:
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "user":
                last_user_idx = i
                break

    for i, m in enumerate(messages):
        om = {"role": m["role"], "content": m["content"]}
        if images and i == last_user_idx:
            om["images"] = images
        ollama_msgs.append(om)

    payload = {
        "model": model,
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

    session = get_session()
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
                
                for single_json in decoded.split('\n'):
                    if not single_json.strip(): continue
                    try:
                        data = json.loads(single_json)
                        if data.get("done") is True:
                            stream_completed = True
                        tok = data.get("message", {}).get("content", "")
                    except Exception as e:
                        logger.debug(f"JSON parsing failed for Ollama chunk: {e}")
                        continue
                        
                    if not tok:
                        continue
                    
                    logger.info(f" [ChatEngine] Token rcvd: '{tok}'")
                    full += tok
                    cur += tok
                    
                    if emit_callback and any(cur.endswith(p) for p in [".", "!", "?", "\n", "。", "！", "？"]):
                        emit_callback(cur.strip())
                        cur = ""

            if emit_callback and cur.strip():
                emit_callback(cur.strip())

            if not stream_completed and full:
                provider = config.get("PROVIDER", "Ollama")
                logger.warning(f"[Brain] Warning: Ollama stream from {url} was closed prematurely.")
                full += f"\n\n*(Note: Connection to {provider} Cloud was closed prematurely by the server/proxy. The response may be incomplete.)*"

            return full, 200

    except asyncio.TimeoutError:
        logger.error(f"[Brain] Timeout → {url}")
        return None, 408
    except (aiohttp.ClientError, aiohttp.ServerDisconnectedError, ConnectionError, OSError) as e:
        logger.error(f"[Brain] Network Error → {url}: {e}")
        return None, 500
    except (TypeError, ValueError, KeyError) as e:
        logger.error(f"[Brain] Data Error → {url}: {e}")
        return None, 500

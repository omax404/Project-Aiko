# core/infrastructure/rag/context_builder.py
import asyncio
import logging
from typing import Any

logger = logging.getLogger("RAGContext")

async def build_rag_context(
    rag: Any,
    query: str,
    top_k: int = 5,
) -> str:
    """Build RAG context string from memory. Pure function, no AikoBrain dependencies."""
    if not rag or not rag.is_available():
        return ""
    try:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, rag.search_memory, query, top_k)
        if not results:
            return ""
        context = "\n[RECALLED MEMORIES]:\n"
        for i, res in enumerate(results, 1):
            meta = res.get('meta', {})
            source = meta.get('source', 'unknown')
            room = meta.get('room', 'general')
            context += f"({i}) [{room} / {source}]: {res['text']}\n"
        return context
    except (asyncio.TimeoutError, OSError) as e:
        logger.warning(f"RAG build failed (I/O): {e}")
        return ""
    except (TypeError, KeyError) as e:
        logger.warning(f"RAG build failed (data format): {e}")
        return ""

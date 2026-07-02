
"""
AIKO RAG MEMORY SYSTEM
Long-term semantic memory using ChromaDB (Local) or SharedMemoryServer (Remote).
"""

import os
import uuid
import time
import requests
import logging
logger = logging.getLogger("RAG")
try:
    from mempalace.searcher import search_memories
    from mempalace.miner import get_collection, add_drawer, chunk_text
    HAS_MEMPALACE = True
except ImportError:
    HAS_MEMPALACE = False

DEFAULT_PALACE = os.path.expanduser("~/.mempalace/palace")
DEFAULT_WING = "Aiko-desktop"

class MemPalaceRAG:
    """MemPalace-backed semantic memory for Aiko."""
    
    def __init__(self, palace_path: str = None, wing: str = None):
        self.palace_path = palace_path or DEFAULT_PALACE
        self.wing = wing or DEFAULT_WING
        self.collection = None
        self._initialized = False
        self._cached_count = 0

    def _initialize(self):
        """Lazy initialize ChromaDB collection via MemPalace."""
        if not HAS_MEMPALACE: return
        if self._initialized: return
        try:
            self.collection = get_collection(self.palace_path)
            self._initialized = True
            logger.info(f" [MemPalace] Connected to Palace: {self.palace_path} (Wing: {self.wing})")
        except Exception as e:
            logger.error(f" [MemPalace] Init Error: {e}")

    def wake_up(self):
        """Invoke the MemPalace wake-up sequence to build the world context."""
        if os.getenv("USE_MEMPALACE", "false").lower() != "true":
            return
        if not HAS_MEMPALACE: return
        try:
            from mempalace.cli import cmd_wakeup
            import argparse
            args = argparse.Namespace(palace=self.palace_path, wing=self.wing)
            cmd_wakeup(args)
            logger.info(" [MemPalace] 🌅 Palace Wake-up Sequence Complete.")
        except Exception as e:
            logger.error(f" [MemPalace] Wake-up Error: {e}")

    def mine_project(self, project_dir: str = "./"):
        """Manually trigger a mine scan of the project."""
        if os.getenv("USE_MEMPALACE", "false").lower() != "true":
            return
        if not HAS_MEMPALACE: return
        try:
            from mempalace.miner import mine
            mine(project_dir=project_dir, palace_path=self.palace_path, wing_override=self.wing, agent="Aiko")
            logger.info(f" [MemPalace] ⛏️ Finished mining: {project_dir}")
        except Exception as e:
            logger.error(f" [MemPalace] Mine Error: {e}")

    def is_available(self) -> bool:
        if os.getenv("USE_MEMPALACE", "false").lower() != "true":
            return False
        if not HAS_MEMPALACE: return False
        self._initialize()
        return self.collection is not None

    def add_memory(self, text: str, metadata: dict = None, room: str = "general"):
        """File a memory into a specific room in the Aiko wing."""
        if not self.is_available(): return
        if not text.strip(): return
        
        try:
            # Chunk long texts as per MemPalace spec
            chunks = chunk_text(text, metadata.get("source", "conversation") if metadata else "conversation")
            for i, chunk in enumerate(chunks):
                add_drawer(
                    collection=self.collection,
                    wing=self.wing,
                    room=room,
                    content=chunk["content"],
                    source_file=metadata.get("source", "conversation") if metadata else "conversation",
                    chunk_index=i,
                    agent="Aiko"
                )
        except Exception as e:
            logger.error(f" [MemPalace] Add Error: {e}")

    def search_memory(self, query: str, n_results: int = 5, wing: str = None, room: str = None) -> tuple:
        """High-recall search using MemPalace search logic."""
        if not self.is_available(): return ()
        
        try:
            results = search_memories(
                query=query,
                palace_path=self.palace_path,
                wing=wing or self.wing,
                room=room,
                n_results=n_results
            )
            
            if "error" in results:
                logger.error(f" [MemPalace] Search Error: {results['error']}")
                return ()
                
            # Format to Aiko's expected (text, meta) format
            formatted = []
            for hit in results.get("results", []):
                formatted.append({
                    "text": hit["text"],
                    "meta": {
                        "wing": hit["wing"],
                        "room": hit["room"],
                        "source": hit["source_file"],
                        "similarity": hit["similarity"]
                    }
                })
            return tuple(formatted)
        except Exception as e:
            logger.error(f" [MemPalace] Search Fatal: {e}")
            return ()

    def get_memory_count(self) -> int:
        """Count only drawers in Aiko's wing."""
        if not self.is_available(): return self._cached_count
        try:
            # Chroma count is global; for wing-specific we'd need a query but count() is fine for status
            self._cached_count = self.collection.count()
            return self._cached_count
        except Exception: return self._cached_count

_mempalace_instance = None

def get_mempalace_rag() -> MemPalaceRAG:
    global _mempalace_instance
    if _mempalace_instance is None:
        _mempalace_instance = MemPalaceRAG()
    return _mempalace_instance

from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

# Configuration
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")
EMBEDDING_MODEL_NAME = "nomic-embed-text"
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
# If this ENV is set, we talk to the server instead of opening the local DB
REMOTE_RAG_URL = os.getenv("REMOTE_RAG_URL") 

class RAGMemorySystem:
    """Semantic long-term memory."""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.ef = None  # Embedding Function
        self._initialized = False
        self.remote_url = REMOTE_RAG_URL
        self.use_mempalace = os.getenv("USE_MEMPALACE", "false").lower() == "true" # Dynamic switch
        self.mempalace = MemPalaceRAG()
        self._cached_count = 0
            
    def _initialize(self):
        """Initialize ChromaDB or prepare remote client."""
        if self.remote_url:
            logger.info(f" [RAG] 🔗 Connected to Remote Memory: {self.remote_url}")
            self._initialized = True
            return

        if self.use_mempalace:
            if self.mempalace.is_available():
                logger.info(" [RAG] 🏰 Using MemPalace (High-Recall Architecture)")
                self._initialized = True
                return
            else:
                logger.warning(" [RAG] MemPalace fallback to standard ChromaDB.")


        logger.info(" [RAG] 📦 Initializing Local Memory System (ChromaDB)...")
        os.makedirs(os.path.dirname(CHROMA_PATH), exist_ok=True)
        
        try:
            import chromadb
            from chromadb.utils import embedding_functions
        except ImportError as e:
            logger.error(f" [!] [RAG] Missing dependencies: {e}")
            return
            
        # Setup Ollama Embedding Function
        try:
            self.ef = embedding_functions.OllamaEmbeddingFunction(
                model_name=EMBEDDING_MODEL_NAME,
                url=f"{OLLAMA_BASE_URL}/api/embeddings"
            )
        except Exception as e:
            logger.error(f" [X] [RAG] Embedding Init Error: {e}")
            return

        def _get_coll():
            client = chromadb.PersistentClient(path=CHROMA_PATH)
            return client, client.get_or_create_collection(name="aiko_memory_v2", embedding_function=self.ef)

        try:
            # Multi-threaded init with timeout to prevent Windows hang
            import threading
            init_res = {"success": False, "c": None, "coll": None}
            def _task():
                try:
                    c, coll = _get_coll()
                    init_res.update({"success": True, "c": c, "coll": coll})
                except Exception as e:
                    logger.debug(f"Failed to connect to local ChromaDB: {e}")
            
            t = threading.Thread(target=_task, daemon=True)
            t.start()
            t.join(timeout=4.0)
            
            if not init_res["success"]:
                logger.warning(" [!] [RAG] DB is LOCKED by another process. Running in Read-Only/Empty mode.")
                return

            self.client, self.collection = init_res["c"], init_res["coll"]
            logger.info(f" [OK] [RAG] Local DB Connected. Items: {self.collection.count()}")
            self._initialized = True
        except Exception as e:
            logger.error(f" [X] [RAG] Fatal DB Error: {e}")
        
    def _ensure_initialized(self):
        if self._initialized: return
        self._initialize()

    def is_available(self) -> bool:
        if not self._initialized:
            return False
        if self.remote_url: return True
        if self.use_mempalace and self.mempalace.is_available(): return True
        return self.collection is not None
        
    def add_memory(self, text: str, metadata: dict = None):
        """Add a text snippet to memory (Local or Remote)."""
        if not text.strip(): return
        self._ensure_initialized()

        if self.use_mempalace and self.mempalace.is_available():
            self.mempalace.add_memory(text, metadata)
            return
        
        if self.remote_url:
            try:
                requests.post(f"{self.remote_url}/store", json={"text": text, "metadata": metadata}, timeout=5)
                return
            except Exception as e:
                logger.error(f"[RAG] Remote store error: {e}")
                return

        if not self.collection: return
        try:
            mem_id = str(uuid.uuid4())
            meta = metadata or {}
            meta["timestamp"] = time.time()
            self.collection.add(documents=[text], metadatas=[meta], ids=[mem_id])
            self.search_memory.cache_clear()
        except Exception as e:
            logger.error(f"[RAG] Add Error: {e}")
            
    @lru_cache(maxsize=128)
    def search_memory(self, query: str, n_results: int = 3) -> tuple:
        """Find relevant memories (Local or Remote)."""
        if not query.strip(): return ()
        self._ensure_initialized()

        if self.use_mempalace and self.mempalace.is_available():
            return self.mempalace.search_memory(query, n_results)
        
        if self.remote_url:
            try:
                resp = requests.post(f"{self.remote_url}/retrieve", json={"query": query, "n_results": n_results}, timeout=5)
                if resp.status_code == 200:
                    return tuple(resp.json().get("results", []))
                return ()
            except Exception as e:
                logger.error(f"[RAG] Remote search error: {e}")
                return ()

        if not self.collection: return ()
        try:
            results = self.collection.query(query_texts=[query], n_results=n_results)
            memories = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    memories.append({"text": doc, "meta": meta})
            return tuple(memories)
        except Exception as e:
            logger.error(f"[RAG] Search Error: {e}")
            return ()

    def ingest_document(self, file_path: str) -> bool:
        if not self.is_available() or not os.path.exists(file_path): return False
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            if text:
                self.add_memory(text, metadata={"source": os.path.basename(file_path)})
                return True
        except Exception as e:
            logger.error(f"Failed to ingest document {file_path}: {e}")
            return False
        return False

    def get_memory_count(self) -> int:
        self._ensure_initialized()
        if self.remote_url:
            try:
                resp = requests.get(f"{self.remote_url}/status", timeout=2)
                self._cached_count = resp.json().get("memory_count", 0)
                return self._cached_count
            except Exception as e:
                logger.warning(f"Failed to retrieve status from remote memory: {e}")
                return self._cached_count
        if self.use_mempalace and self.mempalace.is_available():
            self._cached_count = self.mempalace.get_memory_count()
            return self._cached_count
        if self.collection:
            try:
                self._cached_count = self.collection.count()
            except Exception as e:
                logger.warning(f"Failed to query local memory collection count: {e}")
        return self._cached_count

"""
Aiko Deferred Initializer
Runs heavy indexing and mining operations in a separate process to avoid GIL blocking the main Neural Hub event loop.
"""
import sys
import os
import logging

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("DeferredInitializer")


from core.rag_memory import get_mempalace_rag
from core.config_manager import config
from core.obsidian_connector import ObsidianConnector

def main():
    if os.getenv("USE_MEMPALACE", "false").lower() != "true":
        logger.info("🌸 MemPalace is disabled. Skipping background memory indexing and vault mining.")
        return
    logger.info("🌸 Starting background memory indexing and vault mining...")
    
    # Optimize directory scanning by adding project-specific temp/IDE folders to SKIP_DIRS
    try:
        from mempalace.miner import SKIP_DIRS
        extra_skips = {".gradle", ".idea", ".kotlin", ".testsprite", ".tools", ".claude", ".logs"}
        SKIP_DIRS.update(extra_skips)
        logger.info(f"Updated MemPalace skip directories with: {extra_skips}")
    except Exception as skip_err:
        logger.warning(f"Could not update MemPalace SKIP_DIRS: {skip_err}")

    mp = get_mempalace_rag()
    
    # 1. Wake up Palace
    try:
        logger.info("🌅 Palace Wake-up sequence initiated...")
        mp.wake_up()
    except Exception as e:
        logger.error(f"Palace wake-up failed: {e}")
        
    # 2. Mine Project Directory
    try:
        logger.info("⛏️ Mining project directory...")
        mp.mine_project("./")
    except Exception as e:
        logger.error(f"Project mining failed: {e}")
        
    # 3. Mine Obsidian Vault
    try:
        vault_path = config.get("obsidian_path", "")
        obsidian = ObsidianConnector(vault_path=vault_path)
        if obsidian.is_valid:
            logger.info("⛏️ Obsidian Vault Mining initiated...")
            obsidian.mine_vault(mp)
        else:
            logger.info("Obsidian Vault linked path is invalid or empty, skipping mining.")
    except Exception as e:
        logger.error(f"Obsidian mining failed: {e}")
        
    logger.info("🌸 Background memory indexing and vault mining complete.")

if __name__ == "__main__":
    main()

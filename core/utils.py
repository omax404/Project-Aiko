"""
AIKO UTILITIES
Common helpers and decorators.
"""

import time
import asyncio
from functools import wraps
from typing import TypeVar, Callable

import shutil
import os
from pathlib import Path

T = TypeVar('T')

def clear_cache(target_dirs=None, max_log_size_mb=10):
    """
    Cleans up temporary files and rotates large logs.
    """
    print(" [System] Starting Cache Cleanup...")
    
    # 1. LaTeX Temp Folder
    latex_path = Path(os.path.expanduser("~")) / "Downloads" / "Aiko_Latex"
    if latex_path.exists():
        try:
            # Keep PDFs, remove .tex, .aux, .log, .toc
            for ext in ['*.tex', '*.aux', '*.log', '*.toc', '*.out']:
                for f in latex_path.glob(ext):
                    f.unlink()
            print(f" [OK] Cleaned LaTeX artifacts in {latex_path}")
        except Exception as e:
            print(f" [X] Failed to clean LaTeX cache: {e}")

    # 2. Log Rotation (session_history.log)
    log_file = Path("session_history.log")
    if log_file.exists():
        size_mb = log_file.stat().st_size / (1024 * 1024)
        if size_mb > max_log_size_mb:
            try:
                # Keep last 1000 lines
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines[-1000:])
                print(f" [OK] Rotated log file ({size_mb:.2f} MB -> Trimmed)")
            except Exception as e:
                print(f" [X] Log rotation failed: {e}")

    print(" [System] Cache Logistic: Cleanup Complete.")

def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        sleep_time = backoff_factor ** attempt
                        print(f" [Retry] {func.__name__} failed ({e}). Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                        continue
                    raise
            raise last_exception
        return wrapper
    return decorator

def async_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Async Retry decorator."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        sleep_time = backoff_factor ** attempt
                        print(f" [Retry] {func.__name__} failed ({e}). Retrying in {sleep_time}s...")
                        await asyncio.sleep(sleep_time)
                        continue
                    raise
            raise last_exception
        return wrapper
    return decorator

"""Thread pool manager for parallel execution"""

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional


class ThreadPoolManager:
    """
    Singleton Pattern for managing shared ThreadPoolExecutor

    Uses threads instead of processes because the computation-heavy path
    (vectorized NumPy operations) releases the GIL. This avoids the
    pickle/unpickle overhead of ProcessPoolExecutor while still achieving
    true parallelism for the NumPy C-level code.

    Single Responsibility:
    - Only manages thread pool lifecycle
    - Does NOT perform calculations
    """

    _instance: Optional['ThreadPoolManager'] = None
    _thread_pool: Optional[ThreadPoolExecutor] = None
    _max_workers: Optional[int] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern - only one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_pool(cls) -> ThreadPoolExecutor:
        """Get or create shared ThreadPoolExecutor instance (thread-safe)"""
        if cls._thread_pool is None:
            with cls._lock:
                if cls._thread_pool is None:
                    cpu_count = os.cpu_count() or 2
                    cls._max_workers = max(2, cpu_count - 1)
                    cls._thread_pool = ThreadPoolExecutor(max_workers=cls._max_workers)
                    logging.debug(
                        f"[PARALLEL-INIT] Created ThreadPoolExecutor with {cls._max_workers} "
                        f"workers (CPU count: {cpu_count})"
                    )
        return cls._thread_pool

    @classmethod
    def shutdown(cls):
        """Shutdown the thread pool (for cleanup)"""
        if cls._thread_pool is not None:
            cls._thread_pool.shutdown(wait=True)
            cls._thread_pool = None
            logging.debug("[PARALLEL-SHUTDOWN] ThreadPoolExecutor shutdown")

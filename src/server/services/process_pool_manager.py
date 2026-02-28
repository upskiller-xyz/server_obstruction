"""Process pool manager for parallel execution"""

import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from typing import Optional


class ProcessPoolManager:
    """
    Singleton Pattern for managing shared ProcessPoolExecutor

    Single Responsibility:
    - Only manages process pool lifecycle
    - Does NOT perform calculations
    """

    _instance: Optional['ProcessPoolManager'] = None
    _process_pool: Optional[ProcessPoolExecutor] = None
    _max_workers: Optional[int] = None

    def __new__(cls):
        """Singleton pattern - only one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_pool(cls) -> ProcessPoolExecutor:
        """Get or create shared ProcessPoolExecutor instance"""
        if cls._process_pool is None:
            cpu_count = multiprocessing.cpu_count()
            cls._max_workers = max(2, cpu_count - 1)
            cls._process_pool = ProcessPoolExecutor(max_workers=cls._max_workers)
            logging.debug(
                f"[PARALLEL-INIT] Created ProcessPoolExecutor with {cls._max_workers} "
                f"workers (CPU count: {cpu_count})"
            )
        return cls._process_pool

    @classmethod
    def shutdown(cls):
        """Shutdown the process pool (for cleanup)"""
        if cls._process_pool is not None:
            cls._process_pool.shutdown(wait=True)
            cls._process_pool = None
            logging.debug("[PARALLEL-SHUTDOWN] ProcessPoolExecutor shutdown")

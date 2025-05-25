# utils/performance_monitor.py - NEW FILE
"""
Performance monitoring and optimization utilities for bulk scanning
"""

import time
import logging
from typing import Dict, List, Optional
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class ScanPerformanceMonitor:
    """
    Monitor and log performance metrics for bulk scanning operations
    """

    def __init__(self):
        self.timings = {}
        self.counters = {}
        self.start_time = None
        self.errors = []

    def start_scan(self):
        """Start monitoring a scan operation"""
        self.start_time = time.time()
        self.timings = {}
        self.counters = {}
        self.errors = []
        logger.info("Performance monitoring started")

    @contextmanager
    def time_operation(self, operation_name: str):
        """Context manager to time an operation"""
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.timings[operation_name] = duration
            logger.info(f"{operation_name} completed in {duration:.2f}s")

    def count_operation(self, operation_name: str, count: int = 1):
        """Count occurrences of an operation"""
        if operation_name not in self.counters:
            self.counters[operation_name] = 0
        self.counters[operation_name] += count

    def log_error(self, error

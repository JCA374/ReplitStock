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
    
    def log_error(self, error_type: str, message: str, ticker: Optional[str] = None):
        """Log an error that occurred during scanning"""
        self.errors.append({
            'type': error_type,
            'message': message,
            'ticker': ticker,
            'timestamp': datetime.now().isoformat()
        })
        logger.error(f"{error_type}: {message}" + (f" (ticker: {ticker})" if ticker else ""))
    
    def get_performance_summary(self) -> Dict:
        """
        Get a summary of performance metrics
        
        Returns:
            Dictionary containing performance metrics
        """
        if not self.start_time:
            return {"status": "Not started"}
        
        total_duration = time.time() - self.start_time
        
        return {
            "total_duration_seconds": total_duration,
            "operation_timings": self.timings,
            "operation_counts": self.counters,
            "error_count": len(self.errors),
            "start_time": datetime.fromtimestamp(self.start_time).isoformat()
        }
    
    def print_summary(self):
        """Print a summary of performance metrics to the log"""
        summary = self.get_performance_summary()
        
        if "status" in summary:
            logger.info(f"Performance summary: {summary['status']}")
            return
        
        logger.info("============ PERFORMANCE SUMMARY ============")
        logger.info(f"Total scan duration: {summary['total_duration_seconds']:.2f}s")
        logger.info("Operation timings:")
        for op, duration in summary['operation_timings'].items():
            logger.info(f"  - {op}: {duration:.2f}s")
        
        logger.info("Operation counts:")
        for op, count in summary['operation_counts'].items():
            logger.info(f"  - {op}: {count}")
        
        logger.info(f"Error count: {summary['error_count']}")
        logger.info("=============================================")
    
    def calculate_stats(self) -> Dict:
        """
        Calculate detailed statistics about the scan
        
        Returns:
            Dictionary containing performance statistics
        """
        summary = self.get_performance_summary()
        
        if "status" in summary:
            return {"status": summary["status"]}
        
        # Calculate operation percentages
        total_time = summary['total_duration_seconds']
        time_percentages = {}
        
        for op, duration in summary['operation_timings'].items():
            time_percentages[op] = (duration / total_time) * 100
        
        # Calculate throughput metrics
        total_operations = sum(summary['operation_counts'].values())
        operations_per_second = total_operations / total_time if total_time > 0 else 0
        
        # Calculate error rate
        error_rate = len(self.errors) / total_operations if total_operations > 0 else 0
        
        return {
            "total_duration_seconds": total_time,
            "time_percentages": time_percentages,
            "operations_per_second": operations_per_second,
            "error_rate": error_rate,
            "total_operations": total_operations
        }
"""
Memory management module.

This module provides memory monitoring and management capabilities for efficient
video processing with dynamic worker allocation based on available system resources.
"""

import logging
import multiprocessing
import threading
from typing import Dict, Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from src.config import Constants, MemoryConfig, PerformanceConfig

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Memory monitoring and management for efficient processing.

    This class provides system memory monitoring, worker optimization based on
    available memory, and memory pressure detection to prevent system overload.
    """

    def __init__(
        self, max_memory_percent: int = MemoryConfig.DEFAULT_MEMORY_PERCENT_LIMIT
    ) -> None:
        """
        Initialize the memory manager.

        Args:
            max_memory_percent: Maximum system memory usage percentage threshold
        """
        self.max_memory_percent = max_memory_percent
        self.available = PSUTIL_AVAILABLE
        self.process = psutil.Process() if self.available else None
        self.lock = threading.Lock()

        if not self.available:
            logger.warning("psutil not available - using conservative memory estimates")

    def get_memory_info(self) -> Dict[str, float]:
        """
        Get current memory usage information.

        Returns:
            Dict containing system and process memory information:
            - system_total_gb: Total system memory in GB
            - system_available_gb: Available system memory in GB
            - system_used_percent: System memory usage percentage
            - process_rss_mb: Process resident set size in MB
            - process_vms_mb: Process virtual memory size in MB
        """
        if not self.available:
            # Fallback when psutil is not available
            return {
                "system_total_gb": MemoryConfig.CONSERVATIVE_SYSTEM_TOTAL_GB,
                "system_available_gb": MemoryConfig.CONSERVATIVE_SYSTEM_AVAILABLE_GB,
                "system_used_percent": MemoryConfig.CONSERVATIVE_SYSTEM_USED_PERCENT,
                "process_rss_mb": MemoryConfig.CONSERVATIVE_PROCESS_RSS_MB,
                "process_vms_mb": MemoryConfig.CONSERVATIVE_PROCESS_VMS_MB,
            }

        # System memory
        system_memory = psutil.virtual_memory()

        # Process memory
        process_memory = self.process.memory_info()

        return {
            "system_total_gb": system_memory.total / Constants.BYTES_PER_GB,
            "system_available_gb": system_memory.available / Constants.BYTES_PER_GB,
            "system_used_percent": system_memory.percent,
            "process_rss_mb": process_memory.rss / Constants.BYTES_PER_MB,
            "process_vms_mb": process_memory.vms / Constants.BYTES_PER_MB,
        }

    def get_optimal_workers(
        self,
        min_workers: int = PerformanceConfig.MIN_WORKERS,
        max_workers: Optional[int] = None,
    ) -> int:
        """
        Calculate optimal number of workers based on available memory.

        Args:
            min_workers: Minimum number of workers to use
            max_workers: Maximum number of workers to use (defaults to CPU count)

        Returns:
            Optimal number of workers based on memory constraints
        """
        if max_workers is None:
            max_workers = min(
                multiprocessing.cpu_count(), PerformanceConfig.DEFAULT_MAX_WORKERS
            )

        memory_info = self.get_memory_info()

        # Estimate memory per worker (Whisper model + processing overhead)
        memory_per_worker_gb = MemoryConfig.MEMORY_PER_WORKER_GB

        # Available memory for workers (reserve memory for system + main process)
        available_for_workers_gb = (
            memory_info["system_available_gb"] - MemoryConfig.SYSTEM_MEMORY_RESERVE_GB
        )

        # Calculate max workers based on memory
        memory_based_workers = max(
            PerformanceConfig.MIN_WORKERS,
            int(available_for_workers_gb / memory_per_worker_gb),
        )

        # Take minimum of CPU-based and memory-based limits
        optimal_workers = min(
            max_workers, memory_based_workers, multiprocessing.cpu_count()
        )
        optimal_workers = max(min_workers, optimal_workers)

        logger.info(
            f"Memory analysis: {memory_info['system_available_gb']:.1f}GB available, "
            f"optimal workers: {optimal_workers} (max: {max_workers})"
        )

        return optimal_workers

    def check_memory_pressure(self) -> bool:
        """
        Check if system is under memory pressure.

        Returns:
            True if system memory usage exceeds the configured threshold
        """
        memory_info = self.get_memory_info()
        return memory_info["system_used_percent"] > self.max_memory_percent

    def get_memory_recommendations(self) -> Dict[str, str]:
        """
        Get memory optimization recommendations based on current usage.

        Returns:
            Dict containing memory optimization recommendations
        """
        memory_info = self.get_memory_info()
        recommendations = {}

        if memory_info["system_used_percent"] > 90:
            recommendations["critical"] = (
                "System memory critically low - consider stopping other applications"
            )
        elif memory_info["system_used_percent"] > 80:
            recommendations["warning"] = (
                "High memory usage - monitor for performance impact"
            )

        if memory_info["system_available_gb"] < 2:
            recommendations["low_memory"] = (
                "Less than 2GB available - processing may be slow"
            )

        optimal_workers = self.get_optimal_workers()
        if optimal_workers < multiprocessing.cpu_count():
            recommendations["worker_limit"] = (
                f"Memory constrains workers to {optimal_workers} "
                f"(CPU has {multiprocessing.cpu_count()} cores)"
            )

        return recommendations

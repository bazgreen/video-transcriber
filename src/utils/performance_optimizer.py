"""
Performance optimization utilities for video transcriber.

This module provides advanced performance optimizations including:
- Dynamic worker scaling based on system resources
- Memory-aware processing strategies
- Intelligent chunk size optimization
- Performance monitoring and recommendations
"""

import gc
import logging
import os
import time
from typing import Any, Dict, List, Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from src.config import Constants, PerformanceConfig


def get_safe_memory_status() -> Dict[str, Any]:
    """Get memory status safely without requiring memory_manager parameter"""
    try:
        # Try to get memory manager from routes if available
        try:
            from src.routes.api import memory_manager

            if memory_manager:
                from src.utils.memory import get_memory_status_safe

                return get_memory_status_safe(memory_manager)
        except ImportError:
            pass

        # Fallback to psutil if available
        if PSUTIL_AVAILABLE:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "system_total_gb": memory.total / Constants.BYTES_PER_GB,
                "system_available_gb": memory.available / Constants.BYTES_PER_GB,
                "system_used_percent": memory.percent,
                "process_rss_mb": memory_info.rss / Constants.BYTES_PER_MB,
                "process_vms_mb": memory_info.vms / Constants.BYTES_PER_MB,
                "available": True,
            }
        else:
            # Conservative fallback values
            return {
                "system_total_gb": 8.0,
                "system_available_gb": 4.0,
                "system_used_percent": 50.0,
                "process_rss_mb": 500.0,
                "process_vms_mb": 1000.0,
                "available": False,
            }
    except Exception as e:
        logger.warning(f"Error getting memory status: {e}")
        return {
            "system_total_gb": 8.0,
            "system_available_gb": 4.0,
            "system_used_percent": 50.0,
            "process_rss_mb": 500.0,
            "process_vms_mb": 1000.0,
            "available": False,
        }


logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """
    Advanced performance optimization manager.

    Provides intelligent resource management and performance tuning
    based on system capabilities and current workload.
    """

    def __init__(self):
        """Initialize the performance optimizer."""
        self.start_time = time.time()
        self.metrics_history: List[Dict] = []
        self.last_gc_time = time.time()

    def get_optimal_worker_count(self, file_size_mb: float = 0) -> int:
        """
        Calculate optimal worker count based on system resources and file size.

        Args:
            file_size_mb: Size of file being processed in MB

        Returns:
            Optimal number of workers for current conditions
        """
        try:
            # Get system information
            cpu_count = os.cpu_count() or 4
            memory_status = get_safe_memory_status()
            available_gb = memory_status.get("system_available_gb", 4)

            # Base calculation on CPU cores
            cpu_workers = min(cpu_count, PerformanceConfig.MAX_WORKERS_LIMIT)

            # Adjust based on available memory
            if available_gb >= PerformanceConfig.HIGH_MEMORY_THRESHOLD_GB:
                memory_workers = min(
                    cpu_workers + 2, PerformanceConfig.MAX_WORKERS_LIMIT
                )
            else:
                # Reduce workers for memory-constrained systems
                memory_workers = max(
                    PerformanceConfig.MIN_WORKERS, int(cpu_workers * 0.7)
                )

            # Consider file size
            if file_size_mb > 0:
                # For very large files, reduce parallelism to avoid memory issues
                if file_size_mb > 800:  # > 800MB
                    size_workers = max(
                        PerformanceConfig.MIN_WORKERS, memory_workers - 2
                    )
                elif file_size_mb > 400:  # > 400MB
                    size_workers = max(
                        PerformanceConfig.MIN_WORKERS, memory_workers - 1
                    )
                else:
                    size_workers = memory_workers
            else:
                size_workers = memory_workers

            optimal = max(PerformanceConfig.MIN_WORKERS, min(size_workers, cpu_workers))

            logger.info(
                f"Optimal workers: {optimal} (CPU: {cpu_count}, "
                f"Memory: {available_gb:.1f}GB, File: {file_size_mb:.1f}MB)"
            )

            return optimal

        except Exception as e:
            logger.warning(f"Error calculating optimal workers: {e}")
            return PerformanceConfig.DEFAULT_MAX_WORKERS

    def get_optimal_chunk_size(self, video_duration: float, file_size_mb: float) -> int:
        """
        Calculate optimal chunk size based on video characteristics and system
        resources.

        Args:
            video_duration: Duration of video in seconds
            file_size_mb: Size of video file in MB

        Returns:
            Optimal chunk duration in seconds
        """
        try:
            base_chunk_size = 300  # 5 minutes default

            # Adjust based on video duration
            if video_duration < 600:  # < 10 minutes
                chunk_size = min(base_chunk_size, int(video_duration / 3))
            elif video_duration < 1800:  # < 30 minutes
                chunk_size = base_chunk_size
            else:  # Long videos
                chunk_size = max(base_chunk_size, min(600, int(video_duration / 8)))

            # Adjust based on file size
            if file_size_mb > 500:
                # Larger chunks for big files to reduce overhead
                chunk_size = min(chunk_size + 120, 600)  # Add up to 2 minutes
            elif file_size_mb < 100:
                # Smaller chunks for small files for faster processing
                chunk_size = max(
                    60, chunk_size - 60
                )  # Reduce by 1 minute, min 1 minute

            # Consider available memory
            memory_status = get_safe_memory_status()
            available_gb = memory_status.get("system_available_gb", 4)

            if available_gb < 4:
                # Reduce chunk size for memory-constrained systems
                chunk_size = max(120, int(chunk_size * 0.7))

            logger.info(
                f"Optimal chunk size: {chunk_size}s (Duration: {video_duration:.1f}s, "
                f"Size: {file_size_mb:.1f}MB, Memory: {available_gb:.1f}GB)"
            )

            return chunk_size

        except Exception as e:
            logger.warning(f"Error calculating optimal chunk size: {e}")
            return base_chunk_size

    def optimize_memory_usage(self, force: bool = False) -> Dict:
        """
        Perform memory optimization and cleanup.

        Args:
            force: Force garbage collection even if not due

        Returns:
            Memory status after optimization
        """
        try:
            current_time = time.time()

            # Only run GC if enough time has passed or forced
            if force or (current_time - self.last_gc_time) > 30:  # 30 second intervals
                logger.debug("Running garbage collection for memory optimization")

                # Force garbage collection
                collected = gc.collect()
                self.last_gc_time = current_time

                # Get updated memory status
                memory_status = get_safe_memory_status()

                logger.info(f"Memory optimization: collected {collected} objects")

                return {
                    "optimized": True,
                    "objects_collected": collected,
                    "memory_status": memory_status,
                    "timestamp": current_time,
                }

            return {
                "optimized": False,
                "reason": "GC not due",
                "memory_status": get_safe_memory_status(),
                "timestamp": current_time,
            }

        except Exception as e:
            logger.error(f"Error during memory optimization: {e}")
            return {
                "optimized": False,
                "error": str(e),
                "memory_status": get_safe_memory_status(),
                "timestamp": time.time(),
            }

    def get_performance_recommendations(self) -> List[str]:
        """
        Generate performance recommendations based on current system state.

        Returns:
            List of performance recommendations
        """
        recommendations = []

        try:
            # Get system info
            memory_status = get_safe_memory_status()
            available_gb = memory_status.get("system_available_gb", 0)
            used_percent = memory_status.get("system_used_percent", 0)
            cpu_count = os.cpu_count() or 4

            # Memory recommendations
            if used_percent > 85:
                recommendations.append(
                    "⚠️ High memory usage detected - consider processing smaller "
                    "files or reducing worker count"
                )
            elif available_gb < 2:
                recommendations.append(
                    "💡 Low available memory - enable memory cleanup and use "
                    "smaller chunk sizes"
                )
            elif available_gb > 8:
                recommendations.append(
                    "✅ Abundant memory available - you can increase worker count "
                    "for faster processing"
                )

            # CPU recommendations
            if cpu_count >= 8:
                max_recommended = min(cpu_count, PerformanceConfig.MAX_WORKERS_LIMIT)
                recommendations.append(
                    f"🚀 High-performance system detected ({cpu_count} cores) - "
                    f"consider increasing max workers to {max_recommended}"
                )
            elif cpu_count <= 2:
                recommendations.append(
                    "⚠️ Limited CPU cores - use conservative worker settings "
                    "for stability"
                )

            # Performance features
            if PerformanceConfig.ENABLE_PARALLEL_UPLOAD:
                recommendations.append(
                    "✅ Parallel upload enabled - large files will be processed "
                    "more efficiently"
                )

            if PerformanceConfig.CHUNK_SIZE_OPTIMIZATION:
                recommendations.append(
                    "✅ Dynamic chunk sizing enabled - processing will adapt to "
                    "video characteristics"
                )

            if not recommendations:
                recommendations.append(
                    "✅ System performance is optimal for current configuration"
                )

        except Exception as e:
            logger.error(f"Error generating performance recommendations: {e}")
            recommendations.append(
                "⚠️ Unable to analyze system performance - using default settings"
            )

        return recommendations

    def monitor_processing_performance(
        self, operation: str, duration: float, file_size_mb: Optional[float] = None
    ) -> None:
        """
        Monitor and log processing performance metrics.

        Args:
            operation: Name of the operation being monitored
            duration: Duration of the operation in seconds
            file_size_mb: Optional file size for throughput calculation
        """
        try:
            memory_status = get_safe_memory_status()

            metric = {
                "timestamp": time.time(),
                "operation": operation,
                "duration": duration,
                "memory_used_percent": memory_status.get("percent", 0),
                "memory_available_gb": memory_status.get("available_gb", 0),
            }

            if file_size_mb:
                metric["file_size_mb"] = file_size_mb
                metric["throughput_mbps"] = (
                    file_size_mb / duration if duration > 0 else 0
                )

            self.metrics_history.append(metric)

            # Keep only last 100 metrics to prevent memory bloat
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]

            # Log performance info
            if file_size_mb:
                logger.info(
                    f"Performance: {operation} completed in {duration:.2f}s "
                    f"({file_size_mb:.1f}MB @ {metric['throughput_mbps']:.2f} MB/s)"
                )
            else:
                logger.info(f"Performance: {operation} completed in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Error monitoring performance: {e}")

    def get_performance_summary(self) -> Dict:
        """
        Get summary of recent performance metrics.

        Returns:
            Performance summary statistics
        """
        try:
            if not self.metrics_history:
                return {"status": "No performance data available"}

            recent_metrics = self.metrics_history[-10:]  # Last 10 operations

            avg_duration = sum(m["duration"] for m in recent_metrics) / len(
                recent_metrics
            )

            throughputs = [
                m.get("throughput_mbps", 0)
                for m in recent_metrics
                if m.get("throughput_mbps", 0) > 0
            ]
            avg_throughput = sum(throughputs) / len(throughputs) if throughputs else 0

            uptime = time.time() - self.start_time

            return {
                "uptime_seconds": uptime,
                "operations_completed": len(self.metrics_history),
                "avg_operation_duration": avg_duration,
                "avg_throughput_mbps": avg_throughput,
                "recent_operations": len(recent_metrics),
                "current_memory_status": get_safe_memory_status(),
                "recommendations": self.get_performance_recommendations(),
            }

        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {"error": str(e)}


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

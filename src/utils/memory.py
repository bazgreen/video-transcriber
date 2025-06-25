"""
Memory management utilities.

This module provides centralized memory monitoring and management functions
to eliminate duplicate code across services and routes.
"""

import logging
from typing import Dict, Any, Optional, List

from src.config import MemoryConfig

logger = logging.getLogger(__name__)
memory_config = MemoryConfig()


def get_memory_status_safe(memory_manager) -> Dict[str, Any]:
    """
    Safely get memory information with fallbacks.
    
    This function centralizes memory info access that was duplicated
    across multiple modules.
    
    Args:
        memory_manager: MemoryManager instance (can be None)
        
    Returns:
        Dictionary containing memory information
    """
    if not memory_manager:
        return {
            'system_total_gb': memory_config.CONSERVATIVE_SYSTEM_TOTAL_GB,
            'system_available_gb': memory_config.CONSERVATIVE_SYSTEM_AVAILABLE_GB,
            'system_used_percent': memory_config.CONSERVATIVE_SYSTEM_USED_PERCENT,
            'process_rss_mb': memory_config.CONSERVATIVE_PROCESS_RSS_MB,
            'process_vms_mb': memory_config.CONSERVATIVE_PROCESS_VMS_MB,
            'available': False
        }
    
    try:
        memory_info = memory_manager.get_memory_info()
        memory_info['available'] = True
        return memory_info
    except Exception as e:
        logger.warning(f"Failed to get memory info: {e}")
        return get_memory_status_safe(None)


def check_memory_constraints(
    memory_manager, 
    pressure_threshold: int = 90,
    min_available_gb: float = 2.0
) -> Dict[str, Any]:
    """
    Check memory constraints and return recommendations.
    
    Args:
        memory_manager: MemoryManager instance
        pressure_threshold: Memory pressure threshold percentage
        min_available_gb: Minimum required available memory in GB
        
    Returns:
        Dictionary with memory status and recommendations
    """
    memory_info = get_memory_status_safe(memory_manager)
    
    # Check for memory pressure
    memory_pressure = memory_info['system_used_percent'] > pressure_threshold
    low_memory = memory_info['system_available_gb'] < min_available_gb
    
    # Generate recommendations
    recommendations = []
    if memory_pressure:
        recommendations.append(
            f"System under memory pressure: {memory_info['system_used_percent']:.1f}% used"
        )
    
    if low_memory:
        recommendations.append(
            f"Low available memory: {memory_info['system_available_gb']:.1f}GB available"
        )
    
    if memory_manager:
        optimal_workers = memory_manager.get_optimal_workers()
        if optimal_workers < 4:  # Assuming normal expectation is 4+ workers
            recommendations.append(
                f"Memory limits workers to {optimal_workers} (consider reducing concurrent operations)"
            )
    
    return {
        'memory_info': memory_info,
        'memory_pressure': memory_pressure,
        'low_memory': low_memory,
        'recommendations': recommendations,
        'status': 'warning' if (memory_pressure or low_memory) else 'ok'
    }


def log_memory_status(memory_manager, context: str = "") -> None:
    """
    Log memory status with consistent formatting.
    
    Args:
        memory_manager: MemoryManager instance
        context: Optional context string for the log message
    """
    memory_info = get_memory_status_safe(memory_manager)
    
    context_str = f" ({context})" if context else ""
    logger.info(
        f"Memory status{context_str}: {memory_info['system_used_percent']:.1f}% used, "
        f"{memory_info['system_available_gb']:.1f}GB available, "
        f"process using {memory_info['process_rss_mb']:.1f}MB"
    )


def validate_memory_for_operation(
    memory_manager, 
    operation_name: str,
    required_memory_gb: float = 1.0,
    max_pressure_threshold: int = 85
) -> None:
    """
    Validate system has sufficient memory for an operation.
    
    Args:
        memory_manager: MemoryManager instance
        operation_name: Name of the operation (for error messages)
        required_memory_gb: Required available memory in GB
        max_pressure_threshold: Maximum allowed memory pressure percentage
        
    Raises:
        UserFriendlyError: If insufficient memory available
    """
    from src.models.exceptions import UserFriendlyError
    
    constraints = check_memory_constraints(
        memory_manager, 
        max_pressure_threshold, 
        required_memory_gb
    )
    
    if constraints['memory_pressure']:
        memory_info = constraints['memory_info']
        raise UserFriendlyError(
            f"Insufficient memory for {operation_name}: "
            f"{memory_info['system_used_percent']:.1f}% used, "
            f"{memory_info['system_available_gb']:.1f}GB available. "
            f"Please close other applications and try again."
        )
    
    if constraints['low_memory']:
        memory_info = constraints['memory_info']
        raise UserFriendlyError(
            f"Low memory for {operation_name}: "
            f"only {memory_info['system_available_gb']:.1f}GB available, "
            f"need at least {required_memory_gb:.1f}GB. "
            f"Please free up memory and try again."
        )
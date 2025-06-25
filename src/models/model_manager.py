"""
Model management module.

This module provides efficient Whisper model management with lazy loading
and memory monitoring capabilities.
"""

import threading
import logging
from typing import Any, Optional

import whisper

from src.config import VideoConfig
from .memory import MemoryManager

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Memory-efficient Whisper model management.
    
    This class provides lazy loading of Whisper models with memory monitoring
    and automatic cleanup capabilities to optimize resource usage.
    """
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
        """
        Initialize the model manager.
        
        Args:
            memory_manager: Optional memory manager for monitoring
        """
        self._model: Optional[Any] = None
        self._model_lock = threading.Lock()
        self._load_count = 0
        self._memory_manager = memory_manager
        self._model_name = VideoConfig.WHISPER_MODEL
        
    def get_model(self, model_name: Optional[str] = None) -> Any:
        """
        Get Whisper model with lazy loading and memory monitoring.
        
        Args:
            model_name: Optional model name to load (defaults to configured model)
            
        Returns:
            Loaded Whisper model instance
        """
        if model_name is None:
            model_name = self._model_name
            
        # Check if we need to reload a different model
        if self._model is not None and model_name != self._model_name:
            logger.info(f"Switching from {self._model_name} to {model_name}")
            self.clear_model()
            self._model_name = model_name
        
        if self._model is None:
            with self._model_lock:
                if self._model is None:  # Double-check locking
                    self._load_model(model_name)
        
        return self._model
    
    def _load_model(self, model_name: str) -> None:
        """
        Load the Whisper model with memory monitoring.
        
        Args:
            model_name: Name of the model to load
        """
        logger.info(f"Loading Whisper model: {model_name}")
        
        # Validate model name
        if model_name not in VideoConfig.SUPPORTED_WHISPER_MODELS:
            logger.warning(
                f"Model '{model_name}' not in supported models. "
                f"Supported: {VideoConfig.SUPPORTED_WHISPER_MODELS}"
            )
        
        # Monitor memory before loading
        memory_before = None
        if self._memory_manager:
            memory_before = self._memory_manager.get_memory_info()
        
        try:
            self._model = whisper.load_model(model_name)
            self._load_count += 1
            self._model_name = model_name
            
            # Monitor memory after loading
            if self._memory_manager and memory_before:
                memory_after = self._memory_manager.get_memory_info()
                memory_used = memory_after['process_rss_mb'] - memory_before['process_rss_mb']
                
                logger.info(
                    f"Whisper model '{model_name}' loaded successfully. "
                    f"Memory used: {memory_used:.1f}MB "
                    f"(Total process memory: {memory_after['process_rss_mb']:.1f}MB)"
                )
            else:
                logger.info(f"Whisper model '{model_name}' loaded successfully")
                
        except Exception as e:
            logger.error(f"Failed to load Whisper model '{model_name}': {e}")
            raise
    
    def clear_model(self) -> None:
        """Clear model from memory if needed."""
        with self._model_lock:
            if self._model is not None:
                logger.info(f"Clearing Whisper model '{self._model_name}' from memory")
                del self._model
                self._model = None
    
    def get_model_info(self) -> dict:
        """
        Get information about the currently loaded model.
        
        Returns:
            Dict containing model information
        """
        with self._model_lock:
            return {
                'model_loaded': self._model is not None,
                'model_name': self._model_name if self._model else None,
                'load_count': self._load_count,
                'supported_models': list(VideoConfig.SUPPORTED_WHISPER_MODELS)
            }
    
    def preload_model(self, model_name: Optional[str] = None) -> None:
        """
        Preload a model for faster processing.
        
        Args:
            model_name: Model to preload (defaults to configured model)
        """
        if model_name is None:
            model_name = VideoConfig.WHISPER_MODEL
            
        logger.info(f"Preloading Whisper model: {model_name}")
        self.get_model(model_name)
    
    def reload_model(self) -> None:
        """Reload the current model (useful for memory cleanup)."""
        current_model = self._model_name
        self.clear_model()
        self.get_model(current_model)
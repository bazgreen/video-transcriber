"""
Model management module.

This module provides efficient Whisper model management with lazy loading
and memory monitoring capabilities.
"""

import logging
import threading
from typing import Any, Optional

try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

from src.config import VideoConfig

from .memory import MemoryManager

logger = logging.getLogger(__name__)


def resolve_whisper_device() -> str:
    """
    Resolve the compute device for Whisper.

    Honors VideoConfig.WHISPER_DEVICE ("auto", "cpu", "cuda", "mps").
    "auto" prefers CUDA, then Apple Silicon MPS, then CPU.
    """
    configured = getattr(VideoConfig, "WHISPER_DEVICE", "auto").lower()
    if configured != "auto":
        return configured
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return "mps"
    except Exception:  # pragma: no cover - torch import issues fall back to CPU
        pass
    return "cpu"


def resolve_whisper_backend() -> str:
    """
    Resolve the transcription backend: "mlx" (Apple Silicon, mlx-whisper)
    or "openai" (openai-whisper). Honors VideoConfig.WHISPER_BACKEND
    ("auto" | "mlx" | "openai").
    """
    configured = getattr(VideoConfig, "WHISPER_BACKEND", "auto").lower()
    if configured in ("mlx", "openai"):
        return configured
    if configured == "whisper":  # friendly alias
        return "openai"
    try:
        import mlx_whisper  # noqa: F401

        return "mlx"
    except ImportError:
        return "openai"


#: Hugging Face repos for mlx-community Whisper conversions.
_MLX_REPO_OVERRIDES = {
    "turbo": "mlx-community/whisper-large-v3-turbo",
    "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "large": "mlx-community/whisper-large-v3-mlx",
}


def mlx_repo_for(model_name: str) -> str:
    """Map an openai-whisper model name to its mlx-community HF repo."""
    return _MLX_REPO_OVERRIDES.get(
        model_name, f"mlx-community/whisper-{model_name}-mlx"
    )


class MLXWhisperModel:
    """
    Thin adapter giving mlx-whisper the same .transcribe(audio, **kwargs)
    surface as an openai-whisper model, so services need no backend logic.
    """

    def __init__(self, repo: str):
        self.repo = repo

    def transcribe(self, audio, **kwargs):
        import mlx_whisper

        kwargs.pop("fp16", None)  # mlx manages precision itself
        return mlx_whisper.transcribe(audio, path_or_hf_repo=self.repo, **kwargs)


def load_whisper_model(model_name: str):
    """
    Load a Whisper model on the best available backend.

    Returns (model, description) where model exposes .transcribe(...).
    Order: mlx-whisper (if selected/available) -> openai-whisper on
    cuda/mps with warm-up validation -> openai-whisper on CPU.
    """
    import numpy as _np

    if resolve_whisper_backend() == "mlx":
        try:
            model = MLXWhisperModel(mlx_repo_for(model_name))
            # Warm-up: triggers weight download and validates the repo.
            model.transcribe(_np.zeros(16000, dtype=_np.float32))
            return model, f"mlx-whisper ({model.repo})"
        except Exception as mlx_error:
            logger.warning(
                f"mlx-whisper backend failed for '{model_name}' ({mlx_error}); "
                "falling back to openai-whisper."
            )

    if not WHISPER_AVAILABLE:
        raise RuntimeError("Whisper is not available - cannot load model")

    device = resolve_whisper_device()
    try:
        model = whisper.load_model(model_name, device=device)
        if device != "cpu":
            model.transcribe(_np.zeros(16000, dtype=_np.float32), fp16=True)
    except Exception as device_error:
        if device == "cpu":
            raise
        logger.warning(
            f"Whisper failed on device '{device}' ({device_error}); "
            "falling back to CPU. Set WHISPER_DEVICE=cpu to silence this."
        )
        model = whisper.load_model(model_name, device="cpu")
        device = "cpu"
    return model, f"openai-whisper ({device})"


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
        if not WHISPER_AVAILABLE:
            logger.warning(
                "Whisper not available - model functionality will be limited"
            )

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
        if not WHISPER_AVAILABLE:
            raise RuntimeError("Whisper is not available - cannot load model")

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
            self._model, backend_desc = load_whisper_model(model_name)
            logger.info(f"Whisper backend: {backend_desc}")
            self._load_count += 1
            self._model_name = model_name

            # Monitor memory after loading
            if self._memory_manager and memory_before:
                memory_after = self._memory_manager.get_memory_info()
                memory_used = (
                    memory_after["process_rss_mb"] - memory_before["process_rss_mb"]
                )

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
                "model_loaded": self._model is not None,
                "model_name": self._model_name if self._model else None,
                "load_count": self._load_count,
                "supported_models": list(VideoConfig.SUPPORTED_WHISPER_MODELS),
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

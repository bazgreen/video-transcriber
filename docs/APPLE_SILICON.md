# Running Video Transcriber on Apple Silicon (M-series)

Updated: 2026-08-31. Tuned for M4 Pro-class machines with 24GB unified memory.

## Whisper compute device

Whisper now auto-selects a device via the `WHISPER_DEVICE` setting
(`src/config/settings.py`, env-overridable):

- `auto` (default): CUDA > MPS (Apple Silicon GPU) > CPU. A warm-up
  transcription runs at load; if an op is unsupported on MPS the app logs a
  warning and falls back to CPU automatically.
- `cpu` | `mps` | `cuda`: force a device, e.g. `WHISPER_DEVICE=cpu ./run.sh`.

## mlx-whisper backend (default on Apple Silicon)

`mlx-whisper` (Apple's MLX framework) is now an integrated backend and is
installed automatically on Apple Silicon (see requirements.txt platform
marker). Backend selection via `WHISPER_BACKEND`:

- `auto` (default): mlx-whisper when importable, else openai-whisper
- `mlx` | `openai`: force a backend

With mlx, model names map to mlx-community conversions on Hugging Face
(e.g. `large-v3-turbo` -> `mlx-community/whisper-large-v3-turbo`); weights
download on first use. If the mlx path fails for any reason the app logs a
warning and falls back to openai-whisper (MPS, then CPU).

On Apple Silicon the default model is now `large-v3-turbo` - with mlx it is
several times faster than real time on an M4 Pro and much more accurate than
`small`. Other platforms keep `small`. Override with `WHISPER_MODEL`.

Note: openai-whisper's MPS support depends on your torch version. If MPS gives
wrong output or crashes, force CPU with `WHISPER_DEVICE=cpu`.

## Model choice with 24GB unified memory

| Model | RAM per instance | Notes |
|-------|-----------------|-------|
| small (default) | ~1GB | Good speed/accuracy balance |
| medium | ~2.5GB | Better accuracy, ~2-3x slower |
| large-v3 | ~5GB | Best accuracy; fine on 24GB, keep workers low |

Set with `WHISPER_MODEL=medium ./run.sh`.

## Parallel workers

Worker count is computed at runtime from CPU cores and available memory
(`src/utils/performance_optimizer.py`). On a 12-core M4 Pro with 24GB you
should see 6-12 workers for the `small` model. If you switch to `large-v3`,
cap workers (e.g. `MAX_WORKERS=3`) so total model memory stays well under
the memory limit.

## FFmpeg

`brew install ffmpeg` builds include VideoToolbox hardware acceleration.
Audio extraction (the step this app uses FFmpeg for) is CPU-light either way.

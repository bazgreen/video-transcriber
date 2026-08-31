# Running Video Transcriber on Apple Silicon (M-series)

Updated: 2026-08-31. Tuned for M4 Pro-class machines with 24GB unified memory.

## Whisper compute device

Whisper now auto-selects a device via the `WHISPER_DEVICE` setting
(`src/config/settings.py`, env-overridable):

- `auto` (default): CUDA > MPS (Apple Silicon GPU) > CPU. A warm-up
  transcription runs at load; if an op is unsupported on MPS the app logs a
  warning and falls back to CPU automatically.
- `cpu` | `mps` | `cuda`: force a device, e.g. `WHISPER_DEVICE=cpu ./run.sh`.

Note: openai-whisper's MPS support depends on your torch version. If MPS gives
wrong output or crashes, force CPU. For maximum Apple Silicon throughput
consider `mlx-whisper` (Apple MLX-based, uses the Neural Engine/GPU fully) or
`faster-whisper` (CTranslate2, excellent CPU performance) as alternative
backends - not yet integrated into this app.

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

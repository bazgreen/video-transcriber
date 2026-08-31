# Dependency refresh - August 2026

All requirement floors raised to current stable versions and verified:
`pip install -r requirements.txt` resolves cleanly and all 103 unit tests pass
(Python 3.10, Linux aarch64; app boot smoke-tested via create_app()).

Resolved versions at verification time: Flask 3.1.3, Flask-SocketIO 5.6.1,
Celery 5.6.3, redis-py 8.1.0, numpy 2.2.6, torch 2.13.0,
openai-whisper 20250625, psutil 7.2.2, bcrypt 5.0.0.

Deliberate constraints:
- `pyannote.audio >=3.1,<4.0` - 4.x renamed `use_auth_token` to `token` in
  `Pipeline.from_pretrained` and moved to new community pipelines;
  `src/services/speaker_diarization.py` uses the 3.x API. Upgrade deliberately
  alongside a code change.

Housekeeping in the same change:
- Zero-byte corrupted files at repo root (docs stubs, empty tests, empty
  requirements fragments) removed from git; local copies parked in
  `_to_delete/` (gitignored) pending manual deletion.
- `requirements-auth/pdf/docx.txt` repopulated (they are referenced by
  install scripts and docs but had been zeroed).
- `main.py` module docstring repaired (had code pasted mid-sentence).
- Two session-ID tests aligned with documented behaviour (spaces are allowed).

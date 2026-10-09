"""Cover-art generation (SDXL-Turbo preferred, SD-Turbo fallback — CPU-only).

One PNG per track, rendered from the track's style prompt on the CPU so it
never fights the music engines for VRAM. Same one-shot job pattern as stems:
an asyncio task registry per track, serialized through a single lock because
a full CPU render takes 1-3 minutes.

GET  /api/tracks/{id}/cover        -> the PNG (404 until generated)
POST /api/tracks/{id}/cover        -> start {prompt, seed?}
GET  /api/tracks/{id}/cover/status -> {status, error}
POST /api/tracks/{id}/cover/cancel -> abort a running render
DELETE /api/tracks/{id}/cover      -> remove the file
"""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from pathlib import Path

from .config import DATA_DIR

# Preferred first: SDXL-Turbo (smarter, still 1 step), fallback to SD-Turbo.
# Directories live under DATA_DIR (gitignored) and are fetched by the setup
# scripts; either one present is enough.
MODEL_CANDIDATES: list[tuple[str, int]] = [("sdxl-turbo", 1), ("sd-turbo", 2)]


def _active_model() -> tuple[Path, int]:
    for name, steps in MODEL_CANDIDATES:
        d = DATA_DIR / name
        if (d / "model_index.json").is_file():
            return d, steps
    return DATA_DIR / MODEL_CANDIDATES[0][0], MODEL_CANDIDATES[0][1]

_lock = asyncio.Lock()


@dataclass
class CoverJob:
    status: str = "queued"  # queued|running|done|failed|cancelled
    error: str = ""
    task: asyncio.Task | None = None
    cancel_requested: bool = False


_jobs: dict[int, CoverJob] = {}
_pipe = None
_pipe_steps = 1
_pipe_dir: Path | None = None


def weights_present() -> bool:
    d, _ = _active_model()
    return (d / "model_index.json").is_file()


def _ensure_pipe():
    global _pipe, _pipe_steps, _pipe_dir
    model_dir, steps = _active_model()
    if _pipe is not None and _pipe_dir == model_dir:
        return _pipe
    if not (model_dir / "model_index.json").is_file():
        raise RuntimeError(f"Cover model weights missing in {model_dir}")
    import torch
    from diffusers import AutoPipelineForText2Image

    torch.set_num_threads(max(1, (torch.get_num_threads() or 4)))
    _pipe = AutoPipelineForText2Image.from_pretrained(str(model_dir), torch_dtype=torch.float32)
    _pipe.to("cpu")
    _pipe.set_progress_bar_config(disable=True)
    _pipe_steps = steps
    _pipe_dir = model_dir
    return _pipe


def cover_path_for(audio_path: str) -> Path:
    p = Path(audio_path)
    return p.with_name(f"{p.stem}_cover.png")


def start(track_id: int) -> CoverJob:
    job = _jobs.get(track_id)
    if job and job.status in ("queued", "running"):
        return job
    job = CoverJob()
    _jobs[track_id] = job
    job.task = asyncio.create_task(_run(track_id, job))
    return job


def status(track_id: int) -> CoverJob:
    return _jobs.get(track_id) or CoverJob(status="idle")


def cancel(track_id: int) -> bool:
    job = _jobs.get(track_id)
    if not job or job.status not in ("queued", "running"):
        return False
    job.cancel_requested = True
    if job.task:
        job.task.cancel()
    return True


async def _run(track_id: int, job: CoverJob) -> None:
    from . import db

    job.status = "running"
    try:
        row = db.get_track(track_id)
        if row is None:
            raise RuntimeError("track not found")
        audio_path = row["audio_path"]
        # Prompt/style/seed were frozen at start time.
        prompt = job_prompt(track_id)
        seed = job_seed(track_id)
        out_path = cover_path_for(audio_path)

        def _render():
            import torch

            pipe = _ensure_pipe()
            gen = torch.Generator().manual_seed(seed)

            def _cb(pipe_, step, timestep, callback_kwargs):
                if job.cancel_requested:
                    raise InterruptedError("cancelled")
                return callback_kwargs

            img = pipe(
                prompt,
                num_inference_steps=_pipe_steps,
                guidance_scale=0.0,
                height=512,
                width=512,
                generator=gen,
                callback_on_step_end=_cb,
            ).images[0]
            img.save(out_path)

        async with _lock:
            await asyncio.to_thread(_render)
        if job.cancel_requested:
            raise asyncio.CancelledError()
        db.set_track_cover(track_id, str(out_path))
        job.status = "done"
    except asyncio.CancelledError:
        job.status = "cancelled"
    except InterruptedError:
        job.status = "cancelled"
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)[:300]


# Start-time parameters, stashed so retries stay consistent.
_pending: dict[int, dict] = {}


def job_prompt(track_id: int) -> str:
    return str(_pending.get(track_id, {}).get("prompt") or "album cover art")


def job_seed(track_id: int) -> int:
    v = _pending.get(track_id, {}).get("seed")
    return int(v) if isinstance(v, int) else random.randrange(2**31)


def configure(track_id: int, prompt: str, seed: int | None) -> None:
    _pending[track_id] = {"prompt": prompt[:600], "seed": seed}

"""Backend-managed Ollama server (CPU-only).

Ollama is optional (translation fallback, lyric writing), but running it
meant an extra terminal window and easy GPU/VRAM clashes. This manager lets
the web UI start/stop it like the music engines: pinned to CPU so the GPU
stays free, with stdout captured to LOG_DIR/ollama.log so the LogDock panes
show it next to the engine logs.

If an Ollama is already listening on :11434 (e.g. the tray app), we refuse to
start a second one and report busy instead.
"""
from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

import httpx

from .config import LOG_DIR, ProcessSpec
from .orchestrator.process import ManagedProcess

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_PORT = 11434

_spec = ProcessSpec(
    name="ollama",
    cwd=Path.cwd(),
    cmd=["ollama", "serve"],
    env={
        # CPU only, scoped to this child process (never setx!): keeps the
        # 8 GB VRAM free for YuE2/ACE-Step.
        "CUDA_VISIBLE_DEVICES": "-1",
        "GGML_VK_VISIBLE_DEVICES": "-1",
        "OLLAMA_VULKAN": "0",
    },
    health_url=f"{OLLAMA_HOST}/",
    startup_timeout=60.0,
    shutdown_timeout=10.0,
)

_proc = ManagedProcess(_spec)
_lock = asyncio.Lock()


async def _port_busy() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_HOST}/")
            return resp.status_code < 500
    except httpx.HTTPError:
        return False


def ollama_on_path() -> bool:
    return shutil.which("ollama") is not None


async def status() -> dict:
    async with _lock:
        managed = _proc.is_running
    external = (not managed) and await _port_busy()
    return {
        "managed": managed,
        "running": managed or external,
        "external": external,
        "on_path": ollama_on_path(),
    }


async def start() -> dict:
    if not ollama_on_path():
        return {"ok": False, "error": "ollama is not on PATH for the backend process"}
    if await _port_busy():
        return {"ok": False, "error": "busy: another Ollama already listens on :11434 (quit the tray app first)"}
    async with _lock:
        if _proc.is_running:
            return {"ok": True, "already": True}
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        _proc.start()
    try:
        await _proc.wait_healthy()
    except (RuntimeError, TimeoutError) as exc:
        await _proc.stop()
        return {"ok": False, "error": str(exc)[:300]}
    return {"ok": True}


async def stop() -> dict:
    async with _lock:
        if not _proc.is_running:
            return {"ok": True, "already": True}
        await _proc.stop()
    return {"ok": True}

"""Start/stop the backend-managed CPU-only Ollama (see app/ollama.py)."""
from __future__ import annotations

from fastapi import APIRouter

from .. import ollama as ollama_mgr

router = APIRouter(prefix="/api/ollama", tags=["ollama"])


@router.get("/status")
async def ollama_status():
    return await ollama_mgr.status()


@router.post("/start")
async def ollama_start():
    return await ollama_mgr.start()


@router.post("/stop")
async def ollama_stop():
    return await ollama_mgr.stop()

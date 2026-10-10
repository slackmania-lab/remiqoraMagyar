from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import LOG_DIR, yue2_specs
from ..orchestrator.manager import manager
from ..orchestrator.process import StartCancelled

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])

_LOG_NAME = re.compile(r"^[\w][\w.\-]*$")
_MAX_BYTES = 64 * 1024


class SwitchRequest(BaseModel):
    model: str


@router.get("/config")
async def get_config():
    return {
        "yue2_specs": yue2_specs(),
    }


@router.get("/status")
async def get_status():
    return manager.status_snapshot()


@router.post("/switch")
async def switch(req: SwitchRequest):
    try:
        await manager.switch_to(req.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except StartCancelled as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (RuntimeError, TimeoutError) as exc:
        # Startup failed; manager.status_snapshot() already reflects the
        # per-model error state/message for the UI to display.
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return manager.status_snapshot()


@router.post("/stop")
async def stop():
    await manager.stop_active()
    return manager.status_snapshot()


@router.get("/logs")
async def list_logs():
    """Process log files the backend captured (engine servers, one-shot jobs)."""
    try:
        files = sorted(LOG_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return {"logs": []}
    out = []
    for p in files:
        try:
            st = p.stat()
        except OSError:
            continue
        out.append({"name": p.name, "size": st.st_size, "mtime": st.st_mtime})
    return {"logs": out}


@router.get("/logs/{name}")
async def read_log(name: str, offset: int = 0, limit: int = 200):
    """Tail of one log file. Byte offset based so the UI can follow cheaply:
    pass back next_offset; empty lines list means nothing new."""
    if not _LOG_NAME.match(name) or ".." in name:
        raise HTTPException(status_code=400, detail="bad log name")
    path = LOG_DIR / name
    try:
        size = path.stat().st_size
    except OSError:
        raise HTTPException(status_code=404, detail="log not found")
    offset = max(0, min(offset, size))
    limit = max(1, min(limit, 500))
    with open(path, "rb") as f:
        f.seek(offset)
        chunk = f.read(_MAX_BYTES)
    next_offset = offset + len(chunk)
    text = chunk.decode("utf-8", errors="replace")
    lines = text.splitlines()[-limit:]
    return {"name": name, "size": size, "next_offset": next_offset, "truncated": next_offset < size, "lines": lines}

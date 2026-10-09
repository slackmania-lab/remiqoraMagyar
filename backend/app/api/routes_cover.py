"""Cover-art endpoints. The heavy lifting lives in app/cover.py; this file only
maps track ids to jobs and files, following routes_stems.py's shape."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .. import cover, db

router = APIRouter(prefix="/api/tracks", tags=["cover"])


class CoverBody(BaseModel):
    prompt: str = ""
    seed: Optional[int] = None


def _need_track(track_id: int):
    row = db.get_track(track_id)
    if not row or not Path(row["audio_path"]).exists():
        raise HTTPException(status_code=404, detail="track not found")
    return row


def _job_to_dict(track_id: int) -> dict:
    job = cover.status(track_id)
    return {"status": job.status, "error": job.error}


@router.post("/{track_id}/cover")
async def start_cover(track_id: int, body: CoverBody):
    row = _need_track(track_id)
    prompt = " ".join((body.prompt or "").split())
    if not prompt:
        style = ""
        try:
            import json

            style = str((json.loads(row["params_json"] or "{}")).get("style") or "")
        except (ValueError, AttributeError):
            style = ""
        prompt = f"{row['title']}, {style}, album cover art".strip(", ")
    cover.configure(track_id, prompt, body.seed)
    cover.start(track_id)
    return _job_to_dict(track_id)


@router.post("/{track_id}/cover/cancel")
async def cancel_cover(track_id: int):
    _need_track(track_id)
    if not cover.cancel(track_id):
        return JSONResponse({"error": "nothing running"}, status_code=409)
    return _job_to_dict(track_id)


@router.get("/{track_id}/cover/status")
async def cover_status(track_id: int):
    row = db.get_track(track_id)
    if not row:
        raise HTTPException(status_code=404, detail="track not found")
    data = _job_to_dict(track_id)
    has_file = bool(row["cover_path"] if "cover_path" in row.keys() else None)
    # A failed job must stay "failed" even when an older cover file exists;
    # otherwise the UI would show a stale image as a fresh success.
    if data["status"] in ("idle", "cancelled") and has_file:
        data["status"] = "done"
    data["url"] = f"/api/tracks/{track_id}/cover" if has_file else None
    return data


@router.delete("/{track_id}/cover")
async def delete_cover(track_id: int):
    row = db.get_track(track_id)
    if not row:
        raise HTTPException(status_code=404, detail="track not found")
    if not cover.cancel(track_id):
        pass
    path = row["cover_path"] if "cover_path" in row.keys() else None
    if path:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass
    db.set_track_cover(track_id, None)
    return {"deleted": True}


@router.get("/{track_id}/cover")
async def get_cover(track_id: int):
    row = db.get_track(track_id)
    path = row["cover_path"] if row and "cover_path" in row.keys() else None
    if not row or not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="track has no cover art")
    return FileResponse(path, media_type="image/png", filename=f"cover_{track_id}.png")

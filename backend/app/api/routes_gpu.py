"""GPU load readout for the "is it stuck or working?" question.

Runs `nvidia-smi` (present with NVIDIA drivers on Windows/Linux) and exposes
utilization + VRAM. Results are cached for a few seconds so several browser
tabs polling don't fork a process each. On machines without an NVIDIA GPU
(AMD/Apple/CPU-only) it returns {"available": false} and the UI hides the badge.

GET /api/gpu -> { available, util_percent, mem_used_mib, mem_total_mib, temp_c }
"""
from __future__ import annotations

import shutil
import subprocess
import time

from fastapi import APIRouter

router = APIRouter(prefix="/api/gpu", tags=["gpu"])

_CACHE_TTL = 2.0
_cache: dict = {"at": 0.0, "payload": {"available": False}}


def _read_nvidia_smi() -> dict:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return {"available": False}
    try:
        out = subprocess.run(
            [exe, "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return {"available": False}
    if out.returncode != 0:
        return {"available": False}
    # With several GPUs, report the hottest (most likely the busy) one.
    best = None
    for line in out.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        try:
            util, used, total, temp = (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
        except ValueError:
            continue
        if best is None or util > best[0]:
            best = (util, used, total, temp)
    if best is None:
        return {"available": False}
    return {
        "available": True,
        "util_percent": round(best[0]),
        "mem_used_mib": round(best[1]),
        "mem_total_mib": round(best[2]),
        "temp_c": round(best[3]),
    }


@router.get("")
async def gpu_status():
    now = time.monotonic()
    if now - _cache["at"] < _CACHE_TTL:
        return _cache["payload"]
    payload = _read_nvidia_smi()
    _cache["at"] = now
    _cache["payload"] = payload
    return payload

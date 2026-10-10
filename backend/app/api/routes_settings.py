"""App-wide settings that are entered once and reused everywhere (today: the artist name that goes
into the tags of downloaded tracks)."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import db

router = APIRouter(prefix="/api/settings", tags=["settings"])

ARTIST_KEY = "artist"
WORDBANK_KEY = "wordbanks"

# Must stay in sync with frontend/src/utils/wordbank.ts categories.
PROMPT_CATS = ("moods", "genres", "instruments", "images", "extras", "eras")
THEME_CATS = ("places", "feelings", "objects", "times")
_MAX_WORDS = 200
_MAX_LEN = 80


class SettingsBody(BaseModel):
    artist: str = Field("", max_length=120)


class WordbanksBody(BaseModel):
    prompt: dict[str, list[str]] = Field(default_factory=dict)
    theme: dict[str, list[str]] = Field(default_factory=dict)


# No proper names in the dice banks: no cities, countries, waters, mountains,
# peoples or personal names. Hungarian common nouns are lowercase, so any
# capitalized word is a proper name; well-known lowercase geo/ethnic terms
# are covered by the denylist.
_BANNED_NAMES = frozenset(
    "magyar magyarország budapest duna tisza dráva balaton velencei-tó "
    "fertő mátra bükk bakony pilis börzsöny zemplén mecsek villány alpok "
    "tátra kárpátok gellért várhegy hősök margitsziget lánchíd szabadság "
    "viking vikingek magyarok török arab cigány roma zsidó német orosz angol "
    "francia olasz spanyol portugál holland lengyel cseh szlovák román szerb "
    "horvát szlovén ukrán osztrák svájci görög japán kínai indiai egyiptomi "
    "törökök arabok párizs london berlin moszkva bécs prága varsó amszterdam "
    "róma madrid lisszabon istanbul kairó".split()
)


def _is_name(word: str) -> bool:
    return bool(word) and (word[0].isupper() or word.lower() in _BANNED_NAMES)


def _clean_bank(raw: dict, allowed: tuple[str, ...]) -> dict[str, list[str]]:
    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="wordbank must be an object")
    out: dict[str, list[str]] = {}
    for cat, words in raw.items():
        if cat not in allowed or not isinstance(words, list):
            continue
        seen: list[str] = []
        for w in words:
            if not isinstance(w, str):
                continue
            w = " ".join(w.split())[:_MAX_LEN]
            parts = w.split()
            # Drop entries containing any proper/geographic name.
            if not w or any(_is_name(p.strip(".,;:!?()\"'’") or " ") for p in parts):
                continue
            if w.lower() not in (s.lower() for s in seen):
                seen.append(w)
            if len(seen) >= _MAX_WORDS:
                break
        if seen:
            out[cat] = seen
    return out


@router.get("")
async def get_settings():
    return {"artist": db.get_setting(ARTIST_KEY, "")}


@router.put("")
async def put_settings(body: SettingsBody):
    artist = " ".join(body.artist.split())
    db.set_setting(ARTIST_KEY, artist)
    return {"artist": artist}


@router.get("/wordbanks")
async def get_wordbanks():
    raw = db.get_setting(WORDBANK_KEY, "")
    try:
        data = json.loads(raw) if raw else {}
    except ValueError:
        data = {}
    return {
        "prompt": _clean_bank(data.get("prompt", {}), PROMPT_CATS),
        "theme": _clean_bank(data.get("theme", {}), THEME_CATS),
    }


@router.put("/wordbanks")
async def put_wordbanks(body: WordbanksBody):
    data = {
        "prompt": _clean_bank(body.prompt, PROMPT_CATS),
        "theme": _clean_bank(body.theme, THEME_CATS),
    }
    db.set_setting(WORDBANK_KEY, json.dumps(data, ensure_ascii=False))
    return data

"""Hungarian (or any non-English) prompt preprocessing via a local Ollama LLM.

The music engines expect English style tags; the vocal_language field already
supports 'hu', so singing in Hungarian works — only the style description needs
translating/structuring. This route does NOT generate music, it only rewrites
text, so it never touches the GPU orchestrator and can run in parallel with
generation (Ollama itself should run on CPU: CUDA_VISIBLE_DEVICES=-1).

POST /api/prompt/prepare { text, target, model? } -> { style_en, lyrics, simple, vocal_language }
GET  /api/prompt/status -> { reachable, model, model_present, models[] }
"""
from __future__ import annotations

import json
import os
import re

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/prompt", tags=["prompt"])

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
# Translator backend: "auto" (built-in NLLB when its weights are present,
# otherwise Ollama), "local" (NLLB only), "ollama" (Ollama only).
TRANSLATOR = os.getenv("TRANSLATOR", "auto").strip().lower() or "auto"

SYSTEM_PROMPT = (
    "You are a music prompt translator for an AI music studio. "
    "Input is a free-form track description, in Hungarian or any other language. "
    "Output STRICT JSON only, no markdown, no commentary, with keys: "
    '{"style_en": "...", "lyrics": "...", "simple": "...", "vocal_language": "..."}. '
    "Rules for style_en (MOST IMPORTANT): a DETAILED comma-separated list of ENGLISH "
    "tags, 8-15 items, never Hungarian. Expand every input word into concrete musical "
    "detail: tempo feel (e.g. 'slow tempo 70bpm', 'driving mid-tempo'), instruments "
    "with character (e.g. 'distorted electric guitars', 'warm acoustic guitar', "
    "'orchestral strings', 'deep sub bass', 'punchy drums'), vocal character "
    "(e.g. 'emotional female vocal', 'whispered male vocal', 'choir backing'), mood "
    "nuances (e.g. 'melancholic', 'dark', 'hopeful lift in chorus'), era/production "
    "(e.g. '80s', 'modern polished production', 'lo-fi'). Do NOT collapse distinct "
    "details into one generic word: 'lassu rock orchestral betetekkel' must become "
    "separate tags like 'slow tempo rock, orchestral strings interlude, ...', not just "
    "'rock, orchestral'. "
    "lyrics = the song lyrics in their ORIGINAL language; if the input is only a "
    "description with NO lyric lines, lyrics MUST be an empty string — do NOT invent "
    "or write new lyrics, ever. If lyrics lack structure, "
    "add [Verse]/[Chorus] section headers where sensible. "
    "simple = two English sentences describing the whole track with its details "
    "(for simple mode). "
    'vocal_language = ISO code guessed from lyrics ("hu" for Hungarian, "en" for '
    'English, "" when instrumental/empty). Keep style_en under 600 chars. '
    "Preserve EVERY attribute from the input (mood, tempo, instruments, vocal gender, "
    "theme) — never drop details. Example: input 'szomoru dal, lassu rock, orchestral "
    "betetekkel, epikus' -> {\"style_en\": \"sad, slow tempo rock, distorted electric "
    "guitars, orchestral strings interlude, epic cinematic drums, melancholic, dark "
    "atmosphere, emotional build-up\", \"lyrics\": \"\", \"simple\": \"A sad slow "
    "rock song with epic orchestral string interludes and cinematic drums.\", "
    "\"vocal_language\": \"\"}."
)


class PrepareIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    target: str = Field(default="ace_custom", max_length=32)
    model: str = Field(default="", max_length=64)
    # Source language ISO code (hu/es/de/... — see nllb.SUPPORTED_LANGS) or
    # "auto" (default): Hungarian-vs-English heuristic.
    src_lang: str = Field(default="auto", max_length=16)


async def _ollama_models(client: httpx.AsyncClient) -> list[str]:
    resp = await client.get(f"{OLLAMA_HOST}/api/tags")
    resp.raise_for_status()
    return [m.get("name", "") for m in resp.json().get("models", [])]


class PrepareOut(BaseModel):
    style_en: str = ""
    lyrics: str = ""
    simple: str = ""
    vocal_language: str = ""


def _extract_json(raw: str) -> dict:
    """Tolerate LLMs wrapping JSON in code fences or prose."""
    cleaned = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.S)
    if fence:
        cleaned = fence.group(1)
    else:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, ValueError):
        return {}


async def _run_blocking(fn, *args):
    import asyncio

    return await asyncio.to_thread(fn, *args)


@router.get("/status")
async def prompt_status():
    from .. import nllb

    local_ready = nllb.weights_present()
    engine = "local" if (TRANSLATOR == "local" or (TRANSLATOR == "auto" and local_ready)) else "ollama"
    supported_langs = [{"code": code, "label": label} for code, (_, label) in nllb.SUPPORTED_LANGS.items()]
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            names = await _ollama_models(client)
    except httpx.HTTPError as exc:
        return {"reachable": False, "engine": engine, "local_ready": local_ready, "model": OLLAMA_MODEL, "models": [], "supported_langs": supported_langs, "error": str(exc)[:200]}
    return {"reachable": True, "engine": engine, "local_ready": local_ready, "model": OLLAMA_MODEL, "model_present": OLLAMA_MODEL in names, "models": names, "supported_langs": supported_langs}


def _use_local() -> bool:
    from .. import nllb

    if TRANSLATOR == "local":
        return True
    if TRANSLATOR == "ollama":
        return False
    return nllb.weights_present()


@router.post("/prepare", response_model=PrepareOut)
async def prompt_prepare(body: PrepareIn):
    from fastapi import HTTPException

    text = " ".join(body.text.split())
    if _use_local():
        from .. import nllb

        try:
            en, src = await _run_blocking(nllb.translate_to_english, text, body.src_lang)
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=f"Local translator unavailable: {exc}") from exc
        return PrepareOut(
            style_en=en[:600],
            lyrics="",
            simple=en[:600],
            vocal_language=src if src != "en" else "",
        )
    model = (body.model or OLLAMA_MODEL).strip()
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            names = await _ollama_models(client)
            if model not in names:
                raise HTTPException(status_code=502, detail=f"Ollama model not pulled: {model}")
            resp = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": model,
                    "stream": False,
                    # Thinking models (qwen3*) spend the whole budget reasoning
                    # unless told otherwise — that caused multi-minute hangs.
                    "think": False,
                    "options": {"temperature": 0.5, "num_predict": 800},
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Target: {body.target}\nInput: {text}"},
                    ],
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("message", {}).get("content", "")
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        # 502 so the frontend can show "Ollama nem elérhető" distinctly.
        raise HTTPException(status_code=502, detail=f"Ollama unreachable: {exc}") from exc

    data = _extract_json(raw)
    out = PrepareOut(
        style_en=str(data.get("style_en", ""))[:600],
        lyrics=str(data.get("lyrics", ""))[:2000],
        simple=str(data.get("simple", ""))[:600],
        vocal_language=str(data.get("vocal_language", ""))[:8],
    )
    # Fallback: if the model returned prose instead of JSON, use it as English prompt.
    if not out.style_en and not out.simple and raw.strip():
        out.simple = raw.strip()[:500]
    return out


LYRICS_SYSTEM_PROMPT = (
    "You are a songwriter writing original lyrics for an AI music studio. "
    "The theme may arrive in any language (often Hungarian); the SONG itself "
    "must be written in the requested language. "
    "Output the lyrics ONLY: section headers like [Verse 1], [Verse 2], [Chorus], "
    "[Bridge], [Outro] on their own lines, then the lines. No titles, no "
    "commentary, no explanations, no markdown fences. "
    "Rules: short singable lines (roughly 6-10 syllables), real rhymes (not "
    "assonance soup), concrete images over abstractions, one clear emotion per "
    "song, chorus with a hook that repeats verbatim. Never reuse famous "
    "copyrighted lyrics. Keep it under 2000 characters. "
    "CRITICAL: every single word of the song must be in the requested "
    "language. Translate ALL theme words — never copy a theme word verbatim "
    "into the lyrics (e.g. Hungarian 'magány' must become 'solitude' or "
    "'loneliness', 'kavics' must become 'pebble'). No mixed-language lines, ever."
)

# ISO code -> language name used inside the lyricist prompt.
LYRICS_LANGS: dict[str, str] = {
    "en": "English",
    "hu": "Hungarian",
    "ar": "Arabic",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "de": "German",
    "fr": "French",
    "it": "Italian",
    "pt": "Portuguese",
    "es": "Spanish",
}

LYRIC_DEFAULT_MODELS = ("qwen3:8b", "qwen3.5:9b", "llama3.1:8b")


class LyricsIn(BaseModel):
    theme: str = Field(min_length=1, max_length=1000)
    lang: str = Field(default="en", max_length=8)
    verses: int = Field(default=3, ge=1, le=8)
    chorus: bool = Field(default=True)
    bridge: bool = Field(default=False)
    outro: bool = Field(default=False)
    mood: str = Field(default="", max_length=40)
    model: str = Field(default="", max_length=64)


class LyricsOut(BaseModel):
    lyrics: str = ""
    lang: str = ""
    model: str = ""


def _resolve_lyric_model(names: list[str], want: str) -> str:
    want = (want or "").strip()
    if want and want in names:
        return want
    for candidate in LYRIC_DEFAULT_MODELS:
        if candidate in names:
            return candidate
    if OLLAMA_MODEL in names:
        return OLLAMA_MODEL
    return ""


@router.post("/lyrics", response_model=LyricsOut)
async def prompt_lyrics(body: LyricsIn):
    from fastapi import HTTPException

    lang = (body.lang or "en").strip().lower()
    if lang not in LYRICS_LANGS:
        raise HTTPException(status_code=400, detail=f"Unsupported lyrics language: {body.lang}")
    theme = " ".join(body.theme.split())
    # NOTE: no pre-translation here on purpose. An earlier version piped the
    # theme through NLLB first, but short fragments mistranslate without
    # context ("kavics" -> "coughing") and poison the whole song topic. The
    # LLM knows common Hungarian words itself; the CRITICAL rule above keeps
    # them out of the lyrics.
    parts = [f"{body.verses} verse(s)"]
    if body.chorus:
        parts.append("a repeating [Chorus] after every second verse")
    if body.bridge:
        parts.append("one [Bridge] with a perspective shift before the last chorus")
    if body.outro:
        parts.append("a short closing [Outro]")
    structure = ", ".join(parts)
    mood = " ".join(body.mood.split())
    mood_line = f"\nMood: {mood}" if mood else ""
    try:
        async with httpx.AsyncClient(timeout=420.0) as client:
            names = await _ollama_models(client)
            model = _resolve_lyric_model(names, body.model)
            if not model:
                raise HTTPException(status_code=502, detail="No suitable Ollama model pulled (need e.g. qwen3:8b)")
            resp = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": model,
                    "stream": False,
                    # See above: thinking off, bounded output.
                    "think": False,
                    "options": {"temperature": 0.8, "num_predict": 1500},
                    "messages": [
                        {"role": "system", "content": LYRICS_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": f"Language: {LYRICS_LANGS[lang]}\nStructure: {structure}{mood_line}\nTheme: {theme}",
                        },
                    ],
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("message", {}).get("content", "")
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama unreachable: {exc}") from exc
    lyrics = _extract_json(raw).get("lyrics") if raw.strip().startswith("{") else None
    text = str(lyrics or raw).strip()[:3000]
    # Strip accidental fences/prose wrappers models sometimes add.
    text = re.sub(r"^```(?:\w+)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()
    return LyricsOut(lyrics=text, lang=lang, model=model)

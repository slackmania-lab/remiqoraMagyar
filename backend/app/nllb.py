"""Built-in Hungarian/any-language -> English translator (NLLB-200-distilled-600M).

Runs fully offline on CPU inside the backend process — no Ollama, no GPU, no
VRAM usage, so it can never clash with the music engines. The model weights
(~2.4GB) live under DATA_DIR/nllb and are downloaded once via
huggingface_hub (see the download helper below / setup docs).

NLLB translates faithfully but does NOT expand style descriptions the way an
LLM does; the /api/prompt/prepare contract stays identical so the frontend
needs no logic changes — only the engine label differs.
"""
from __future__ import annotations

import re
import threading
from pathlib import Path
from .config import DATA_DIR

NLLB_DIR = DATA_DIR / "nllb"
DST_EN = "eng_Latn"

# ISO code -> (NLLB language code, self-name for the UI dropdown).
SUPPORTED_LANGS: dict[str, tuple[str, str]] = {
    "hu": ("hun_Latn", "Magyar"),
    "es": ("spa_Latn", "Español"),
    "de": ("deu_Latn", "Deutsch"),
    "fr": ("fra_Latn", "Français"),
    "it": ("ita_Latn", "Italiano"),
    "pt": ("por_Latn", "Português"),
    "ru": ("rus_Cyrl", "Русский"),
    "uk": ("ukr_Cyrl", "Українська"),
    "pl": ("pol_Latn", "Polski"),
    "ro": ("ron_Latn", "Română"),
    "nl": ("nld_Latn", "Nederlands"),
    "cs": ("ces_Latn", "Čeština"),
    "tr": ("tur_Latn", "Türkçe"),
    "en": ("eng_Latn", "English"),
}

_HU_CHARS = frozenset("áéíóöőúüűÁÉÍÓÖŐÚÜŰ")

# Distinctive stopwords (deliberately no 1-letter words: 'a' collides with English).
_HU_STOP = frozenset(
    "egy az és hogy nem van vagy mint már csak meg azt ezt akkor amikor ahol "
    "nagyon sem nincs voltak lesz kell lehet nagy indiai zenekar dallam dal lassú "
    "szomorú gyors hangos halk sötét világos régi új magyar".split()
)
_EN_STOP = frozenset(
    "the and with about from song love night light heart home dark eyes rain "
    "wait beneath you your lonely".split()
)

_lock = threading.Lock()
_tokenizer = None
_model = None


def weights_present() -> bool:
    return (NLLB_DIR / "config.json").is_file() and any(NLLB_DIR.glob("*.safetensors")) or (NLLB_DIR / "pytorch_model.bin").is_file()


# Frequent unaccented -> accented fixes: many users type without accents and NLLB
# mistranslates those words (e.g. "betetekkel"). Applied case-insensitively to
# whole words only; unknown words pass through untouched.
_ACCENT_MAP = {
    "szomoru": "szomorú", "lassu": "lassú", "gyors": "gyors", "sotet": "sötét",
    "vilagos": "világos", "dallam": "dallam", "dallamvilag": "dallamvilág",
    "zenekar": "zenekar", "hangszerek": "hangszerek", "hangszereles": "hangszerelés",
    "betetekkel": "betétekkel", "betetek": "betétek", "epikus": "epikus",
    "regi": "régi", "uj": "új", "magyar": "magyar", "gyerekrol": "gyerekről",
    "gyerekekrol": "gyerekekről", "eszak": "észak", "tuz": "tűz", "viz": "víz",
    "fold": "föld", "hold": "hold", "nap": "nap", "ejjel": "éjjel", "ejjel-nappal": "éjjel-nappal",
    "sziv": "szív", "almok": "álmok", "alom": "álom", "elet": "élet",
    "halal": "halál", "szerelem": "szerelem", "fajdalom": "fájdalom",
    "orom": "öröm", "banat": "bánat", "remeny": "remény", "emlek": "emlék",
    "mult": "múlt", "jovo": "jövő", "tavasz": "tavasz", "osz": "ősz",
    "tel": "tél", "nyar": "nyár", "eso": "eső", "ho": "hó", "szel": "szél",
    "tenger": "tenger", "hegyek": "hegyek", "volgy": "völgy", "ut": "út",
    "hazafele": "hazafelé", "egyedul": "egyedül", "orokke": "örökké",
    "neha": "néha", "mar": "már", "meg": "meg", "hogy": "hogy",
    "eros": "erős", "lagy": "lágy", "kemeny": "kemény", "csendes": "csendes",
    "hangos": "hangos",
    "noi": "női", "ferfi": "férfi", "enek": "ének", "enekel": "énekel",
    "enekes": "énekes", "enekesno": "énekesnő", "korus": "kórus",
    "gitar": "gitár", "zongora": "zongora", "hegedu": "hegedű",
    "dob": "dob", "dobok": "dobok", "fuvola": "fuvola", "trombita": "trombita",
    "vonos": "vonós", "vonosok": "vonósok", "hurok": "húrok",
    "tempo": "tempó", "ritmus": "ritmus", "rock": "rock", "metal": "metal",
    "ballada": "ballada", "keringo": "keringő", "indulo": "induló",
}


def _restore_accents(text: str) -> str:
    def fix(word: str) -> str:
        m = re.match(r"^(\W*)(.*?)(\W*)$", word, flags=re.UNICODE)
        if not m:
            return word
        pre, core, post = m.groups()
        key = core.lower()
        if key in _ACCENT_MAP:
            acc = _ACCENT_MAP[key]
            core = acc.capitalize() if core[:1].isupper() else acc
        return f"{pre}{core}{post}"

    return re.sub(r"\S+", lambda m: fix(m.group(0)), text)


def looks_hungarian(text: str) -> bool:
    """Accent-independent heuristic with a majority rule.

    NLLB with a forced hun_Latn source hallucinates on English-dominant text
    (e.g. six English tags plus one Hungarian word came back as
    "I'm not sure I'm gonna make it"), so Hungarian must clearly dominate:
    at least ~1 in 3 words carries Hungarian markers (diacritics or
    stopwords). The bridge exists for Hungarian input, so pure ties still
    default to Hungarian.
    """
    words = [w for w in text.lower().replace(",", " ").split() if w]
    if not words:
        return False
    marked = 0
    for w in words:
        if any(ch in _HU_CHARS for ch in w) or w in _HU_STOP:
            marked += 1
    return (marked / len(words)) >= 0.3


def _ensure_loaded() -> None:
    global _tokenizer, _model
    if _model is not None:
        return
    if not weights_present():
        raise RuntimeError(f"NLLB weights missing in {NLLB_DIR}")
    try:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(f"NLLB runtime deps missing (torch/transformers): {exc}") from exc
    torch.set_num_threads(max(1, (torch.get_num_threads() or 4)))
    _tokenizer = AutoTokenizer.from_pretrained(str(NLLB_DIR))
    _model = AutoModelForSeq2SeqLM.from_pretrained(str(NLLB_DIR))
    _model.eval()


def _translate_one(text: str, nllb_code: str) -> str:
    """Translate one (already accent-restored) chunk with NLLB."""
    import torch

    _ensure_loaded()
    _tokenizer.src_lang = nllb_code
    inputs = _tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    forced_bos = _tokenizer.convert_tokens_to_ids(DST_EN)
    with torch.no_grad():
        out = _model.generate(
            **inputs,
            forced_bos_token_id=forced_bos,
            max_length=512,
        )
    en = _tokenizer.batch_decode(out, skip_special_tokens=True)[0]
    # NLLB sometimes decorates music-related lines with stray note symbols.
    en = re.sub(r"^[^A-Za-z0-9\u00C0-\u017F]+", "", en.strip())
    en = re.sub(r"[^A-Za-z0-9\u00C0-\u017F).!?\"]+$", "", en.strip())
    return " ".join(en.split())


def _guard(en: str, fallback: str, iso: str) -> tuple[str, str]:
    # Last-resort guard: NLLB occasionally answers instead of translating
    # ("I'm not sure...", "Sorry..."). A translation must never read like a
    # chatbot reply — fall back to the input.
    if re.search(r"(?i)\bi['’]m not sure\b|\bsorry\b|\bas an ai\b|\bi cannot\b|\bi can't\b", en):
        return fallback, iso
    return en, iso


def translate_to_english(text: str, src: str = "auto") -> tuple[str, str]:
    """Return (english_text, iso_src_lang).

    "auto" (default) works comma-segment by comma-segment: Hungarian segments
    go through NLLB, the rest passes through untouched. This keeps mixed
    inputs ("hardcore trap, indiai dallamvilág") fully English without the
    all-or-nothing guessing that either hallucinates or echoes.
    An explicit ISO code translates the whole text from that language.
    """
    cleaned = " ".join(text.split())
    if not cleaned:
        return "", ""
    iso = (src or "auto").strip().lower()
    if iso != "auto":
        if iso == "en" or iso not in SUPPORTED_LANGS:
            return cleaned, "en"
        text_in = _restore_accents(cleaned) if iso == "hu" else cleaned
        with _lock:
            out = _translate_one(text_in, SUPPORTED_LANGS[iso][0])
        return _guard(out, cleaned, iso)
    parts = [p.strip() for p in re.split(r"[,\n]+", cleaned) if p.strip()]
    if not parts:
        return "", ""
    translated_any = False
    done: list[str] = []
    with _lock:
        for part in parts:
            if looks_hungarian(part):
                try:
                    out = _translate_one(_restore_accents(part), SUPPORTED_LANGS["hu"][0])
                except RuntimeError:
                    out = part
                done.append(out)
                translated_any = True
            else:
                done.append(part)
    en = ", ".join(done)
    if translated_any:
        return _guard(en, cleaned, "hu")
    return cleaned, "en"


def local_dir() -> Path:
    return NLLB_DIR

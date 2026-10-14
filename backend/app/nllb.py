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


# Music-domain glossary HU->EN. Applied before NLLB so genre/mood/instrument
# words come out deterministically right; NLLB then handles whatever remains.
# Phrases first (longest match wins), then single words.
_GLOSSARY_PHRASES = {
    "tiszta énekhangon": "with clean vocals",
    "tiszta énekhanggal": "with clean vocals",
    "női énekkel": "with female vocals",
    "női énekhangon": "with female vocals",
    "férfi énekkel": "with male vocals",
    "férfi énekhangon": "with male vocals",
    "férfihangon": "with male vocals",
    "lassú tempóban": "at a slow tempo",
    "gyors tempóban": "at a fast tempo",
    "közepes tempóban": "at a medium tempo",
    "pörgős ritmussal": "with a driving rhythm",
    "élő dobokkal": "with live drums",
    "suttogós vokállal": "with whispered vocals",
    "gyerekkórussal": "with a children's choir",
    "torz vokállal": "with distorted vocals",
    "dübörgő basszussal": "with thundering bass",
    "visszhangos gitárral": "with echoing guitar",
    "csiszolt produkció": "polished production",
    "nyers hangzással": "with a raw sound",
    "telt hangzással": "with a full sound",
    "éjszakai város": "night city",
    "csillagos ég": "starry sky",
    "kis kocsma": "small pub",
    "elhagyott gyár": "abandoned factory",
    "hóesés": "falling snow",
    "naplemente": "sunset",
    "tábortűz": "campfire",
    "80-as évek": "80s",
    "60-as évek": "60s",
    "70-es évek": "70s",
    "középkori hangulat": "medieval atmosphere",
    "egy esős kedden": "on a rainy tuesday",
    "holdtöltekor": "at full moon",
    "hajnal előtt": "before dawn",
    "éjfél után": "after midnight",
    "szilveszter éjjelén": "on new year's eve",
    "tél derekán": "in deep winter",
    "szerelem első látásra": "love at first sight",
    "utolsó tánc": "last dance",
    "kölcsönkapott kabát": "borrowed coat",
    "törött óra": "broken clock",
    "megfakult fénykép": "faded photograph",
    "elveszett kulcs": "lost key",
    "régi bakelit": "old vinyl",
    "papírhajó": "paper boat",
    "üres boríték": "empty envelope",
    "rozsdás bicikli": "rusty bicycle",
    "lejárt vonatjegy": "expired train ticket",
    "recsegő rádió": "crackling radio",
    "poros padlásláda": "dusty attic trunk",
    "befejezetlen levél": "unfinished letter",
    "tengerészcsomó": "sailor's knot",
    "kinyílt esernyő": "opened umbrella",
    "villanypózna fénye": "lamppost light",
    "folyóparti pad": "riverside bench",
    "templomtorony": "church tower",
    "tanyasi udvar": "farmyard",
    "szőlőhegy": "vineyard hill",
    "panelrengeteg": "housing estate maze",
    "kórházi folyosó": "hospital corridor",
    "éjjeli benzinkút": "night gas station",
    "néptelen strand": "empty beach",
    "bezárt mozi": "closed cinema",
    "üres játszótér": "empty playground",
    "kihűlt kávé": "cold coffee",
    "elhagyott kikötő": "abandoned harbor",
    "csonka hold": "crescent moon",
    "vasárnapi piac": "sunday market",
    "ködös folyópart": "foggy riverside",
    "rozsdás híd": "rusty bridge",
    "szabadságvágy": "longing for freedom",
}

_GLOSSARY_WORDS = {
    # moods
    "szomorú": "sad", "vidám": "cheerful", "epikus": "epic", "sötét": "dark",
    "világos": "bright", "álmodozó": "dreamy", "vad": "wild", "nyugodt": "calm",
    "melankolikus": "melancholic", "ünnepélyes": "festive", "lázadó": "rebellious",
    "nosztalgikus": "nostalgic", "sejtelmes": "mysterious", "játékos": "playful",
    "drámai": "dramatic", "törékeny": "fragile", "büszke": "proud",
    "fájdalmas": "painful", "reményteli": "hopeful", "baljós": "ominous",
    "mámoros": "ecstatic", "higgadt": "composed", "szilaj": "fiery",
    "bensőséges": "intimate", "fenyegető": "threatening", "fénylő": "radiant",
    "keserédes": "bittersweet", "pajkos": "mischievous", "komor": "gloomy",
    "lebegő": "floating", "tüzes": "fiery", "erős": "strong", "lágy": "soft",
    "kemény": "hard", "csendes": "quiet", "hangos": "loud",
    # music nouns
    "dal": "song", "zene": "music", "dallam": "melody", "dallamos": "melodic",
    "ritmus": "rhythm", "ritmusos": "rhythmic", "tempó": "tempo",
    "hangzás": "sound", "produkció": "production", "ballada": "ballad",
    "keringő": "waltz", "rock": "rock", "metal": "metal",
    "betét": "interlude", "betétek": "interludes",
    "betéttel": "with an interlude", "betétekkel": "with interludes",
    # adjectives & production
    "elektronikus": "electronic", "akusztikus": "acoustic",
    "elektromos": "electric", "modern": "modern", "hagyományos": "traditional",
    "klasszikus": "classic", "népi": "folk", "régi": "old", "új": "new",
    "fiatal": "young", "öreg": "old", "nagy": "great", "kis": "small",
    "kicsi": "small", "hosszú": "long", "rövid": "short", "magas": "high",
    "mély": "deep", "vastag": "thick", "vékony": "thin", "sima": "smooth",
    "érdes": "rough", "éles": "sharp", "tompa": "muted",
    "piszkos": "dirty", "szürke": "grey", "fekete": "black", "fehér": "white",
    "piros": "red", "vörös": "red", "kék": "blue", "zöld": "green",
    "sárga": "yellow", "arany": "golden", "ezüst": "silver",
    "tavaszi": "spring", "nyári": "summer", "őszi": "autumn", "téli": "winter",
    "havas": "snowy", "esős": "rainy", "szeles": "windy", "napos": "sunny",
    "felhős": "cloudy", "csillagos": "starry",
    # song parts & music craft
    "refrén": "chorus", "verzé": "verse", "verze": "verse", "intró": "intro",
    "outró": "outro", "szóló": "solo", "híd": "bridge", "stílus": "style",
    "műfaj": "genre", "korszak": "era", "hangulat": "mood",
    "atmoszféra": "atmosphere", "energia": "energy", "erő": "power",
    "dinamika": "dynamics", "feszültség": "tension", "csúcspont": "climax",
    "hangszer": "instrument", "hangszerelés": "arrangement",
    "zenekar": "band", "együttes": "ensemble",
    # people & body & world
    "lány": "girl", "fiú": "boy", "nő": "woman", "férfi": "man",
    "gyerek": "child", "barát": "friend", "ellenség": "enemy",
    "isten": "god", "ördög": "devil", "angyal": "angel", "király": "king",
    "katona": "soldier", "tengerész": "sailor", "vándor": "wanderer",
    "idegen": "stranger", "hős": "hero", "szem": "eye", "könny": "tear",
    "vér": "blood", "kéz": "hand", "ház": "house", "pénz": "money",
    "autó": "car", "utca": "street", "tér": "square", "város": "city",
    "falu": "village", "buli": "party", "koncert": "concert",
    "fesztivál": "festival", "klub": "club", "bár": "bar",
    "ünnep": "celebration", "esküvő": "wedding", "temetés": "funeral",
    # time & adverbs
    "reggel": "morning", "dél": "noon", "délután": "afternoon",
    "éjfél": "midnight", "tegnap": "yesterday", "ma": "today",
    "holnap": "tomorrow", "mindig": "always", "soha": "never",
    "néha": "sometimes", "gyakran": "often", "ritkán": "rarely",
    "most": "now", "már": "already", "még": "still", "megint": "again",
    "újra": "anew", "lassan": "slowly", "halkan": "quietly",
    "hangosan": "loudly",
    # instruments
    "gitár": "guitar", "gitárral": "with guitar", "zongora": "piano",
    "hegedű": "violin", "dob": "drums", "dobokkal": "with drums",
    "harmonika": "accordion", "furulya": "flute", "szaxofon": "saxophone",
    "cselló": "cello", "hárfa": "harp", "trombita": "trumpet",
    "bendzsó": "banjo", "cimbalom": "cimbalom", "basszusgitár": "bass guitar",
    "basszus": "bass", "basszussal": "with bass", "szintetizátor": "synthesizer",
    "brácsa": "viola", "nagybőgő": "double bass", "klarinét": "clarinet",
    "oboa": "oboe", "orgona": "organ", "szájharmonika": "harmonica",
    "ukulele": "ukulele", "mandolin": "mandolin", "tambura": "tambura",
    "hegedűvel": "with violin", "zongorával": "with piano",
    # vocals
    "ének": "vocals", "énekkel": "with vocals", "énekhang": "vocal",
    "női": "female", "férfi": "male", "kórus": "choir", "kórussal": "with choir",
    "énekes": "singer", "énekesnő": "female singer", "vokál": "backing vocals",
    # images
    "eső": "rain", "város": "city", "tenger": "sea", "hegyek": "mountains",
    "hegy": "mountain", "vonat": "train", "kikötő": "harbor", "sivatag": "desert",
    "erdő": "forest", "folyó": "river", "ég": "sky", "csillag": "star",
    "csillagos": "starry", "köd": "fog", "ködös": "foggy", "tűz": "fire",
    "hó": "snow", "nap": "sun", "hold": "moon", "szél": "wind", "víz": "water",
    "föld": "earth", "tó": "lake", "tengerpart": "seashore", "híd": "bridge",
    "sziget": "island", "templom": "church", "kastély": "castle", "piac": "market",
    "metró": "metro", "vihar": "storm", "hajnal": "dawn", "alkonyat": "dusk",
    "este": "evening", "reggel": "morning", "éj": "night", "éjszaka": "night",
    "éjfél": "midnight",
    # feelings/things
    "szív": "heart", "szerelem": "love", "fájdalom": "pain", "öröm": "joy",
    "bánat": "sorrow", "remény": "hope", "emlék": "memory", "álom": "dream",
    "élet": "life", "halál": "death", "múlt": "past", "jövő": "future",
    "magány": "solitude", "egyedül": "alone", "otthon": "home", "haza": "home",
    "út": "road", "szabadság": "freedom",
    # time/seasons
    "tavasz": "spring", "nyár": "summer", "ősz": "autumn", "tél": "winter",
    "hétfő": "monday", "kedd": "tuesday", "márciusban": "in march",
    # verbs/adverbs
    "száguldva": "speeding", "vágtatva": "galloping", "lüktetve": "pulsing",
    "andalogva": "strolling", "lassan": "slowly", "halkan": "quietly",
    "hangosan": "loudly",
}


def _apply_glossary(text: str) -> str:
    lowered = text.lower()
    for phrase in sorted(_GLOSSARY_PHRASES, key=len, reverse=True):
        if phrase in lowered:
            lowered = lowered.replace(phrase, _GLOSSARY_PHRASES[phrase])
    out: list[str] = []
    for tok in lowered.split():
        m = re.match(r"^(\W*)(.*?)(\W*)$", tok, flags=re.UNICODE)
        if not m:
            out.append(tok)
            continue
        pre, core, post = m.groups()
        out.append(f"{pre}{_GLOSSARY_WORDS.get(core, core)}{post}")
    return " ".join(out)


def _has_hungarian_left(text: str) -> bool:
    for tok in text.split():
        core = re.sub(r"^\W+|\W+$", "", tok.lower(), flags=re.UNICODE)
        if not core:
            continue
        if any(ch in _HU_CHARS for ch in core):
            return True
        if core in _ACCENT_MAP or core in _HU_STOP:
            return True
    return False


def pretranslate(text: str) -> tuple[str, bool]:
    """Deterministic Hungarian->English vocabulary pass (accents + glossary).

    Returns (text, has_hungarian_left). Safe to run before either engine:
    known music words become English, the rest stays for NLLB/LLM.
    """
    cleaned = " ".join(text.split())
    if not cleaned:
        return "", False
    out = _apply_glossary(_restore_accents(cleaned))
    out = " ".join(out.split())
    return out, _has_hungarian_left(out)

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
    if iso == "hu":
        # Explicit Hungarian behaves exactly like auto: per-segment detection.
        # Forcing the whole mixed text through hun_Latn hallucinates
        # ("Electronic" -> dictionary definition). The dropdown stays
        # meaningful for the other languages (whole-text from that language).
        iso = "auto"
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
    # Group CONSECUTIVE Hungarian segments into one chunk: single words
    # without context mistranslate badly ("száguldva" -> "of a width of
    # <= 10 mm"), while the same words together translate fine. Glossary
    # output goes DIRECTLY to the result (never mixed into NLLB input —
    # mixed-language chunks hallucinate); NLLB only ever sees coherent raw
    # Hungarian for the words the glossary does not know.
    chunks: list[tuple[str, str]] = []  # (kind, text): kind in {"gloss", "nllb", "raw"}
    for part in parts:
        gloss, _ = pretranslate(part)
        # Glossary hit beyond mere casing ("dallamos" -> "melodic", but not
        # "Dark" -> "dark"): Hungarian was in there even with no markers.
        if gloss.lower() != part.lower() and not _has_hungarian_left(gloss):
            kind, text = "gloss", gloss
        elif looks_hungarian(part):
            kind, text = "nllb", _restore_accents(part)
        else:
            kind, text = "raw", part
        if kind == "nllb" and chunks and chunks[-1][0] == "nllb":
            chunks[-1] = ("nllb", chunks[-1][1] + ", " + text)
        else:
            chunks.append((kind, text))
    translated_any = False
    done: list[str] = []
    with _lock:
        for kind, chunk in chunks:
            if kind != "nllb":
                if kind == "gloss":
                    translated_any = True
                done.append(chunk)
                continue
            translated_any = True
            try:
                out = _translate_one(chunk, SUPPORTED_LANGS["hu"][0])
            except RuntimeError:
                out = chunk
            done.append(out)
    en = ", ".join(done)
    if translated_any:
        return _guard(en, cleaned, "hu")
    return cleaned, "en"


def local_dir() -> Path:
    return NLLB_DIR

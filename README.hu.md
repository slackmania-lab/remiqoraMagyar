> Ez a fájl a [README.md](README.md) magyar fordítása — az eredeti angol változat a mérvadó.

<p align="right"><a href="README.md">English</a> · <a href="README.ru.md">Русский</a> · <b>Magyar</b></p>

<p align="center">
  <img src="frontend/public/favicon.svg" width="88" height="88" alt="Remiqora">
</p>

<h1 align="center">Remiqora</h1>
<p align="center"><i>AI-jal készült. Általad készült.</i></p>

<p align="center">
  Helyi, GPU-val gyorsított zenei generáló és produceri stúdió — egy felület az <b>ACE-Step 1.5</b>-höz és a <b>YuE2-3B</b>-hez, beépített többsávos DAW-val.
</p>

<p align="center">🚧 Aktív fejlesztés alatt áll — számíts törő változásokra, hibákra és csiszolatlan részekre. Még nem stabil kiadás.</p>

<p align="center">
  <a href="https://remiqora.com/"><img alt="Weboldal" src="https://img.shields.io/badge/website-remiqora.com-22d3ee?style=flat-square"></a>
  <img alt="Állapot" src="https://img.shields.io/badge/status-in%20development-eab308?style=flat-square">
  <a href="LICENSE"><img alt="Licenc" src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square"></a>
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-0f0f14?style=flat-square">
  <img alt="GPU" src="https://img.shields.io/badge/GPU-NVIDIA%20CUDA%20%7C%20Apple%20Metal-76B900?style=flat-square">
  <img alt="Stack" src="https://img.shields.io/badge/stack-Vue%203%20%2B%20FastAPI-a855f7?style=flat-square">
  <img alt="Felület nyelvei" src="https://img.shields.io/badge/UI-EN%20%2F%20RU%20%2F%20HU-ec4899?style=flat-square">
  <a href="https://ko-fi.com/inikolax"><img alt="Támogatás Ko-fi-n" src="https://img.shields.io/badge/Support-Ko--fi-FF5E5B?style=flat-square&logo=ko-fi&logoColor=white"></a>
</p>

<p align="center">
  <img src="docs/hero-poster.png" alt="Remiqora — AI-jal készült, általad készült" width="900">
</p>

<p align="center">
  <a href="#why-this-exists">Miért</a> ·
  <a href="#whats-inside">Mi van benne</a> ·
  <a href="#ace-step-generation">ACE-Step</a> ·
  <a href="#yue2-and-sheetsage2-generation">YuE2</a> ·
  <a href="#lora-training-ace-step">LoRA</a> ·
  <a href="#built-in-daw">DAW</a> ·
  <a href="#desktop-app-experimental">Asztali alkalmazás</a> ·
  <a href="#built-with">Készült</a> ·
  <a href="#license--liability-for-generated-content">Licenc</a> ·
  <a href="#-installation">Telepítés</a>
</p>

---

## Miért létezik ez

Az ACE-Step és a YuE2 két független zenei generáló motor, mindegyiknek saját webes felülete, saját eredménytárolási formátuma és saját folyamata van, amelyet kézzel kell elindítanod és leállítanod. Egy átlagos fogyasztói GPU-n általában nem tudnak egyszerre futni. A Remiqora ezt egy ráépülő egységes réteggel oldja meg:

- **Egy felület** két különböző UX-ű felület helyett.
- **Kölcsönösen kizáró vezénylő**: válassz modellt a fejlécben — az elindul, a másik pedig magától leáll. Nem kell kézzel kilőnöd a folyamatokat, mielőtt a másik motort elindítanád.
- **Közös tárhely**: minden zeneszám (generált, feltöltött vagy a szerkesztőben összerakott) egy központi SQLite-adatbázisban és megosztott mappában van nyilvántartva, és minden modulból elérhető — a Demucs, a MuScriptor és a szerkesztő is ugyanabból a könyvtárból dolgozik három különálló helyett.
- **DAW a generálás fölött**: a generált zeneszám nem végpont, hanem nyersanyag — szedd szét sávokra, húzd rá az idősávra, dolgozd meg effektekkel, keverd más zeneszámokkal, és exportáld.
- **Beépített LoRA-tanítás**: nem csak generálás — az ACE-Step-et a saját hangodra vagy stílusodra is finomhangolhatod közvetlenül a böngészőből, konzol nélkül.

---

## Mi van benne

| Modul | Mit csinál |
|---|---|
| **ACE-Step 1.5** | Gyors generálás szövegből/stílus címkékből, feldolgozások (coverek), szakaszok újrafestése, szólamok kinyerése/hozzáadása egy referencia-zeneszámra építve. |
| **YuE2-3B** | Teljes hosszúságú zeneszámok generálása CoT partitúra-tervezéssel (szimbolikus ABC-terv a hanganyag előtt). |
| **SheetSage2** | Kinyeri a dallamot és a harmóniát egy referencia-zeneszámból ABC-notációba — ez szolgál a YuE2 bemeneteként. |
| **LoRA-tanítás** | Adathalmaz → automatikus címkézés → előfeldolgozás → tanítás → export — a teljes ACE-Step finomhangolási folyamat a saját hangodra/stílusodra, a böngészőben. |
| **Demucs** | Bármely zeneszámot 4 sávra bont szét: ének, dob, basszus, egyéb. |
| **MuScriptor** | Átírja a hanganyagot (a teljes mixet vagy egyetlen sávot) MIDI-hangjegyekké. |
| **Beépített DAW** | Többsávos idősáv-szerkesztő zeneszámok/sávok végső mixszé rakásához: effektsor minden csatornán, automatikus BPM és időnyújtás, WAV/MP3-export. |

A felület teljesen kétnyelvű (orosz/angol). A rendszernyelveden indul, és a fejlécben lévő váltó ezt felülbírálja.

---

## ACE-Step: generálás

![ACE-Step: generálás és zeneszám-folyam](docs/screenshots/en/02-ace-step.png)

Két beviteli mód: **„Egyszerű”** — egyetlen szöveges leírás, amelyből a modell magától következtet a stílusra és a dalszövegre; és **„Egyéni”** — stílus címkék automatikus kiegészítéssel plusz dalszöveg szerkezeti jelölésekkel (`[Verse]/[Chorus]/[Bridge]`) és előadásmód-jelölésekkel (`(whisper)`, `(falsetto)`), vagy egy „Instrumentális” jelölőnégyzet.

Ha csatolsz egy referencia-zeneszámot, 5 remix-forgatókönyv nyílik meg:
- **Feldolgozás (Cover)** — új stílusba öltöztetés a dallam megtartásával (hangolható eredeti-megőrzési erősség).
- **Szakasz újrafestése** — csak a zeneszám kiválasztott részének cseréje.
- **Szólam kinyerése** — egy hangszer/ének kihúzása egy kész mixből (12 lehetőség: ének, dob, basszus, gitár stb.).
- **Szólam hozzáadása** — egy hiányzó hangszer megkomponálása a mix tetejére.
- **Szám befejezése** — ugyanez, de egyszerre egy egész szólamlistára.

Plusz: 10–300 mp időtartam, 1/2/4 variációs köteg, mp3/wav/flac formátumok, haladó paraméterek (BPM, hangnem, ütemmutató, ének nyelve, következtetési lépések, guidance scale, seed), LoRA-adapterek támogatása állítható erősséggel, helyi presetek és egy „Stop all” gomb a kötegelt feladatok megszakításához.

## YuE2 és SheetSage2: generálás

![YuE2: generálás és zeneszám-folyam](docs/screenshots/en/03-yue2.png)

Három **CoT (Chain-of-Thought)** mód: `off` — egyből hanganyag; `melody` — a hangszerelés egy megadott dallam (ABC) köré épül; `full` — a modell először egy szimbolikus tervet épít (dallam + akkordok), majd generálja a hanganyagot.

A **SheetSage2** segítségével feltölthetsz egy referencia-zeneszámot, és a dallamát egy kattintással, rögtön az űrlapon áthúzhatod ABC-notációba — utána kézzel is szerkesztheted. Ezen túl: `q8_0`/`q4_0` pontosság, 1–4-es köteg, a hanggenerálás és az ABC-tervező teljes mintavételezési paraméterkészlete külön-külön, helyi presetek, valamint egy már legenerált zeneszám ABC-partitúrájának megtekintése és újrafelhasználása.

## LoRA-tanítás (ACE-Step)

![LoRA-tanítás](docs/screenshots/en/04-lora-training.png)

A teljes ACE-Step finomhangolási folyamat a saját adathalmazodon, konzol nélkül:

1. **Adathalmaz** — tölts fel hangfájlokat közvetlenül a böngészőből (fogd és vidd) vagy mutass egy meglévő szervermappára, egy trigger szó, egy „minden zeneszám instrumentális” jelölés.
2. **Automatikus címkézés** — LLM-mel generált leírás, műfaj, BPM/hangnem, dalszöveg-átírás/újraformázás.
3. **Átnézés és szerkesztés** — minden minta táblázata, ahol tanítás előtt javíthatod a leírást/műfajt/címkéket.
4. **Előfeldolgozás** — a címkézett mintákat tenzorokká alakítja.
5. **Tanítás** — LoRA rank/alpha/dropout, tanulási ráta, epochok, kötegméret, FP8, gradiens-ellenőrzőpontozás, élő folyamat ETA-val és TensorBoard-linkkel.
6. **Export és nyilvántartás** — a kész adapter azonnal bekerül a generáló űrlap LoRA-listájába.

## Sávszétválasztás (Demucs)

![Sávszétválasztás](docs/screenshots/en/05-stems-panel.png)

Egy kattintással bármely mentett zeneszámot 4 különálló sávra bont (Demucs `htdemucs`), folyamatjelzővel, sávonkénti külön lejátszóval és letöltéssel, valamint újrafuttatási vagy törlési lehetőséggel. Az aktív generáló modell mellett fut (annak leállítása nélkül), közös GPU-záron osztozva. Az **„Open in editor”** gombbal mind a 4 sávot azonnal átküldheted egy új beépített DAW-projektbe további keveréshez.

## MIDI-átírás (MuScriptor)

![MIDI-átírás](docs/screenshots/en/06-midi-panel.png)

Átírja a teljes mixet vagy bármely már szétválasztott sávot MIDI-be. Technikailag ez nem külön folyamat — egy modell, amely a már futó YuE2-szerverbe töltődik be, ezért **az átíráshoz a YuE2-nek kell az aktív modellnek lennie**. Eredmény: beépített Web Audio szintis lejátszó, mini zongoratekercs (piano roll), hangjegyszám- és BPM-kijelzés, valamint `.mid` letöltés.

## Beépített DAW

![Szerkesztő: négysávos projekt az idősávon](docs/screenshots/en/08-editor-with-clip.png)

Tetszőleges számú sáv, amelyekre bármit rátehetsz a megosztott könyvtárból (teljes mix, egyetlen sáv, lemezről feltöltött fájl) — választóablakkal vagy úgy, hogy a fájlt egyenesen a sávra húzod. A leggyorsabb belépés a sávokon át vezet: a sávpanelen lévő **„Open in editor”** gomb egy kész négysávos projektet hoz létre (ének, dob, basszus, egyéb).

### Idősáv és klipek

- Klipek szabad áthelyezése és széleinek vágása (roncsolásmentes — a forrásfájl érintetlen marad). A klipek mindig a szomszédos klipek széleihez és az idősáv nullpontjához tapadnak; a **Magnet** gomb emellett a projekt BPM-jéből származtatott rácshoz is tapaszt (a lépés a zoomtól függ: 1/16, 1/8, 1/4 hang vagy egy ütem).
- **Klip szétvágása** a kurzornál (`S`), duplikálás (`Ctrl+D`), törlés (`Delete`).
- Gombok magán a klipen: **M** (némítás), **S** (szóló), **W** (warp) és ✕. Húzható **beúsztatás / kiúsztatás** fogók ülnek a klip szélein; alapból minden él kap egy automatikus 15 ms-os mikro-átúsztatást, amely eltünteti a hirtelen vágások digitális kattogását.
- **Loop**: hurokrégió az idővonalzón — egészben húzhatod vagy bármelyik szélénél fogva; a vonalzóra kattintva odaugrasz.
- **BPM és Warp**: amikor egy klip a könyvtárból vagy lemezről behúzva bekerül, a tempója automatikusan felismerésre kerül (az első 30 másodpercből). A **BPM** mező állítja be a projekt tempóját, a **W** gomb pedig ehhez időnyújtja a klipet (SoundTouch), a hangmagasság megőrzésével. A felismerő egyszerű, és összetett anyagon tévedhet.
- **Visszavonás/Újra** (`Ctrl+Z` / `Ctrl+Y`) — legfeljebb **30 lépés** előzmény. Nagyíts `Ctrl+görgő`-vel vagy a csúszkával és a **Fit** gombbal; az idősávot `Shift+húzás`-sal vagy a középső egérgombbal pásztázhatod.

### Csatornák és effektek

![Effektsor a dobcsatornán](docs/screenshots/en/10-editor-effects.png)

- Minden sávon van hangerő, panoráma, némítás/szóló és szín (a sávlista feletti pöttyök), plusz egy közös master busz.
- **8 effektből álló sor** minden csatornán és a masteren: EQ (Mély/Közép/Magas, ±12 dB), Dynamics (kompresszor: küszöb és arány), Filter (LP/HP: frekvencia és rezonancia), Chorus, Delay, Reverb, Distortion és Bitcrush. Minden effekt valós időben fut, a paraméterértékek a csúszkák mellett láthatók.
- Sztereó master VU-méterek (L/R) az eszköztáron, és szintmérő túlvezérlés-jelzéssel a kiválasztott sáv csatornáján.

### Súgó

![Beépített szerkesztő-súgó](docs/screenshots/en/11-editor-help.png)

Az eszköztáron lévő **„?”** gomb beépített súgót nyit: gyorsbillentyűk listája, egérkezelés, valamint rövid tippek a Loophoz és a Magnethez.

### Projekt és export

- A projektek a szerveren tárolódnak, és listából nyithatók meg. Nincs automatikus mentés — használd a **Save** gombot; ha mentetlen szerkesztéssel zárod be a lapot vagy navigálsz el, a szerkesztő figyelmeztet az elvesztésükre.
- A kevert projektet **WAV** vagy **MP3** formátumban exportálhatod — offline rendereléssel (ugyanaz a feldolgozási gráf, mint az élő lejátszásnál), és visszamentve a megosztott zeneszám-könyvtárba.

---

## Architektúra

- **`backend/`** — FastAPI (Python). Az `app/orchestrator/` kezeli a modellek folyamat-életciklusát (indítás/leállítás/egészségfigyelés), és kikényszeríti a kölcsönös kizárásukat egyetlen GPU-n. Az `app/api/routes_proxy.py` fordított proxyként működik: `/api/ace/*` → az ACE-Step REST API-ja (8001-es port) és `/api/yue2/*` → a YuE2 natív szervere (`audiocpp_server.exe`, 8080-as port). Az `app/db.py` + `routes_tracks.py` a megosztott SQLite-adatbázis és fájlok, modellenként rendezve, függetlenül attól, hogyan készült a zeneszám (generálás, feltöltés vagy a szerkesztőben összerakott).
- **`frontend/`** — Vue 3 + TypeScript + Tailwind v4 + Pinia + vue-router + vue-i18n. Teljesen natív megvalósítás (nem iframe) a modellek eredeti API-jaira építve — a `src/audio/` saját Web Audio motort tartalmaz (keverő, idősáv, effektek, MIDI-elemző és szintetizátor, WAV/MP3-kódolók).
- **`desktop/`** — opcionális Electron-burok és telepítő: első indításos beállítás, szerver-életciklus és csomagolás. Ugyanazt a `backend/`-et és `frontend/`-et futtatja; lásd: [`desktop/README.md`](desktop/README.md).
- Csak maguk a modellek következtetési folyamatai (`acestep-api` és `audiocpp_server.exe`) futnak az eredeti kódjukból — minden más (felület, proxyzás, tárhely, fájlfeltöltés/átkódolás) ebben a repóban van megírva. A YuE2 saját webes felülete (`web-ui/server.py`) már nincs használatban — az egyetlen hasznos részét (a nem WAV-feltöltések átkódolását ffmpeg-gel) átültettük ide: `backend/app/api/routes_yue2_upload.py`.

---

## Készült

A Remiqora egy felület és vezénylő harmadik féltől származó következtetési motorok fölött. A kódjuk nincs ebbe a repóba beágyazva — csak apró funkcionális foltok (`external/patches/`) az eredetieken:

| Projekt | Mi van használva | Licenc |
|---|---|---|
| [ACE-Step-1.5](https://github.com/ace-step/ACE-Step-1.5) | Szöveg/stílus-vezérelt zenei generáló motor, LoRA-tanítás | MIT |
| [audio.cpp](https://github.com/0xShug0/audio.cpp) (`dev` ág) | YuE2 (generálás), SheetSage2 (dallamkinyerés), MuScriptor (MIDI-átírás) | Apache-2.0 |
| [Demucs](https://github.com/adefossez/demucs) | Sávszétválasztás (`htdemucs`) | MIT |

A foltok részletei és a pontos alap-commitek itt vannak: [`external/patches/README.md`](external/patches/README.md).

Az asztali alkalmazás ezen felül használja még: [Electron](https://www.electronjs.org) (MIT), [electron-builder](https://www.electron.build) (MIT), [uv](https://docs.astral.sh/uv/) (MIT vagy Apache-2.0) és statikus FFmpeg-buildek (GPL), amelyeket első indításkor tölt le a szétosztás helyett.

---

## Licenc és felelősség a generált tartalomért

A Remiqora saját kódja (ez a repó) [MIT-licencű](LICENSE). Ez csak a felületre és a vezénylőre vonatkozik — ez külön dolog attól, milyen licenc alatt áll egy *zeneszám*, amelyet vele generálsz. A Remiqora vezénylő, nem saját modellel rendelkező generátor — minden hanganyagot harmadik féltől származó motorok állítanak elő (ACE-Step 1.5, YuE2-3B, valamint a rájuk épülő SheetSage2/MuScriptor eszközök). Emiatt:

- **A Remiqora szerzője semmilyen felelősséget nem vállal** azért, ami az alkalmazáson át generált zeneszámokkal utána történik — akár kereskedelmi, akár más, akár publikált, akár privát felhasználásról van szó. Amit létrehozol, és ahogyan tovább használod, az teljes mértékben a te felelősséged.
- **A generált zeneszámra annak a modellnek a licence vonatkozik, amely létrehozta**, nem ennek a repónak a licence. A fenti táblázat a *kód* licencét sorolja — a *modell súlyok* licencelése eltérhet:
  - **ACE-Step 1.5** — a kód és a modell súlyok is MIT-licencűek, és a modell szerzői kifejezetten kimondják, hogy a generált zene kereskedelmileg is felhasználható.
  - **YuE2-3B** — a modell súlyok (az audio.cpp saját Apache-2.0 *kód*-licencétől eltérően) **CC BY-NC 4.0** alatt vannak terjesztve. Ez azt jelenti, hogy a YuE2-vel generált zeneszámok **kereskedelmileg nem használhatók fel** a jogtulajdonos külön engedélye nélkül, és bármilyen felhasználásnál feltüntetendő a szerzőség.
- Mielőtt egy generált zeneszámot publikálnál, pénzzé tennél vagy más módon terjesztenél, **ellenőrizd az adott modell aktuális licencfeltételeit** a saját HuggingFace/súly oldalán — ezek a feltételek az adott modell jogtulajdonosához tartoznak, és ettől a repótól függetlenül változhatnak.
- A Remiqora „ahogy van”, mindenféle garancia nélkül áll rendelkezésre. A használatával elfogadod, hogy egy generált zeneszám jogi és az azt létrehozó modell licencének való megfelelésének ellenőrzése kizárólag a te felelősséged.
- **Forrásmegjelölés**: ha a Remiqora kódját forkolod, másolod vagy ráépítesz, tartsd meg a hivatkozást — egy linket vissza erre a repóra és Nikolay Cherkashinra ([inikolax](https://github.com/inikolax)) mint eredeti szerzőre. A fenti MIT-licenc amúgy is megköveteli a szerzői jogi közlemény megtartását minden másolatban; ez csak annak közérthető kimondása.

---

## 📦 Telepítés

Kétféleképpen telepítheted a Remiqorát: az **asztali alkalmazással** (kísérleti, ezt írjuk le először) vagy a **szkriptekkel** (az alábbi 0–2. lépések).

### Asztali alkalmazás (kísérleti)

Ha inkább nem használnál terminált, a Remiqora **asztali alkalmazásként** is elérhető **Windowsra** (NVIDIA RTX 20-as széria vagy újabb, 580-as vagy újabb driver) és **macOS-re** (Apple Silicon). Saját ablakban nyílik meg, és mindent beállít az első indításkor, így nincs szükség Gitre, Pythonra, CUDA Toolkitre vagy fordítóra. A Windows-telepítő felhasználónként települ, rendszergazdai jog nem kell hozzá.

**Letöltés (v0.2.2, előzetes kiadás):** [Windows-telepítő (.exe)](https://github.com/inikolax/remiqora/releases/download/v0.2.2/Remiqora-Setup-0.2.2.exe) · [macOS-telepítő (.dmg, Apple Silicon)](https://github.com/inikolax/remiqora/releases/download/v0.2.2/Remiqora-0.2.2-arm64.dmg) · [összes fájl és SHA-256 összeg](https://github.com/inikolax/remiqora/releases/tag/v0.2.2)

<p align="center">
  <img src="docs/screenshots/en/12-desktop-check.png" alt="First launch: the app checks the GPU, driver, free space and connection, and asks where to keep models and projects" width="48%">
  <img src="docs/screenshots/en/13-desktop-download.png" alt="First launch: components downloading and installing, with overall and per-component progress" width="48%">
</p>

- **Első indítás.** Az alkalmazás ellenőrzi a GPU-t, a drivert, a szabad lemezterületet és a kapcsolatot, megkérdezi, melyik mappába kerüljenek a modellek és a projektek, majd oda telepít: az előre buildelt audio.cpp motort (Windowson CUDA, macOS-en Metal), az ACE-Step-et, a Demucsot, a modell súlyokat és az FFmpeg-et. Nagyjából 30 GB letöltéssel és kb. 35 GB lemezhellyel számolj (Windowson mérve); a képernyő 50 GB szabad helyet kér. Ha megszakad, a kész lépéseket kihagyja, a letöltéseket pedig folytatja.
- **Minden későbbi indítás.** Az alkalmazás elindítja a szervert, és megnyitja a felületet. Az ablak bezárása leállítja a modelszervereket, és felszabadítja a GPU-t.
- **Hol van minden.** A modellek, az adatbázis, a generált hanganyagok és a naplók a választott mappában maradnak, és semmi nincs sehova feltöltve. A mappa utólag nem helyezhető át, mert az adatbázis abszolút útvonalakat tárol.

**Állapot.** Kísérleti. A telepítők még nincsenek aláírva, ezért a Windows SmartScreen-figyelmeztetést mutat („További információ” → „Futtatás mindenképp”), a macOS pedig azt mondja, hogy nem tudja ellenőrizni az alkalmazást: zárd be az üzenetet, nyisd meg a Rendszerbeállítások → Adatvédelem és biztonság részt, kattints a „Megnyitás mégis”-re, és erősítsd meg (egyszer kell). Ha a macOS ehelyett azt mondja, hogy az alkalmazás „sérült, és nem nyitható meg” (a 0.2.1-es és korábbi build, [#33](https://github.com/inikolax/remiqora/issues/33)), húzd az Alkalmazások közé, és futtasd Terminálban: `xattr -dr com.apple.quarantine /Applications/Remiqora.app`. Minden fájl SHA-256 összege a kiadási oldalon lévő `SHA256SUMS.txt`-ben van. Ha inkább magad buildelnél telepítőt:

```sh
cd frontend && npm ci && cd ../desktop && npm ci
npm run dist    # Windows: dist/Remiqora-Setup-<version>.exe · macOS (Macen futtasd): dist/Remiqora-<version>-arm64.dmg
```

A [`desktop/README.md`](desktop/README.md) leírja, mit telepít az első futás, milyen tesztkapcsolókat és milyen ismert hiányosságokat.

**Miből épül.** Egy [Electron](https://www.electronjs.org)-burok ugyanazon webes felület és FastAPI-backend köré, [electron-builder](https://www.electron.build)-rel csomagolva (NSIS-telepítő Windowson, DMG macOS-en). Az első indítás [uv](https://docs.astral.sh/uv/)-ot használ a Python-környezetekhez, az [audio.cpp](https://github.com/0xShug0/audio.cpp) kiadási binárisait és statikus FFmpeg-buildeket. A licencek változatlanok; különösen a YuE2-3B súlyok maradnak CC BY-NC 4.0 alatt.

### Telepítés szkriptekkel

Az alábbi lépések a szkriptes telepítést írják le: Git, terminál és Windowson a build eszközök.

### 0. lépés: build eszközök

```cmd
setup_prereqs.bat
```

`winget`-en át (beépítve a Windows 10/11-be) telepíti a Gitet, Pythont, `uv`-ot, Node.js-t, CMake-et, ffmpeg-et, plusz a Visual Studio Build Toolst (C++ workload) és a CUDA Toolkitet — ezek nagyok, rendszergazdai jogot kérnek, és sokáig tarthatnak. A `setup_prereqs.bat -SkipHeavy` csak a kicsi, gyors eszközöket telepíti, a Build Tools/CUDA kézi telepítését pedig rád hagyja a szkript által kiírt linkek alapján.

**Az NVIDIA GPU-drivert szándékosan kihagytuk** — telepítsd kézzel az [nvidia.com/drivers](https://www.nvidia.com/drivers) oldalról a kártyádhoz: más gépén némán videodrivert cserélni kockázatos (elsötétülhet a képernyő, és általában újraindítást igényel a te időbeosztásod szerint, nem a szkripté szerint).

Telepítés után zárd be a terminált, és nyiss újat, hogy a PATH felvegye a frissen telepített eszközöket.

**macOS-en (Apple Silicon):**
```sh
./setup_prereqs.sh
```
[Homebrew](https://brew.sh)-n át telepíti a Gitet, Pythont, `uv`-ot, Node.js-t, CMake-et, ffmpeg-et és Ninját. Nincs külön GPU-driver lépés: a Metal a macOS része. CMake/Ninja valójában csak az alábbi `--from-source` build-úthoz kell — az alapértelmezett YuE2-beállításhoz egyáltalán nem kell fordító.

### 1. lépés: generáló motorok

```cmd
setup_models.bat
```

A szkript:
1. Klónozza az `ace-step/ACE-Step-1.5`-öt (MIT) és a `0xShug0/audio.cpp`-t (Apache-2.0, `dev` ág — a YuE2-támogatás egyelőre csak dev-ágon van) az `external/` mappába.
2. Feltesz egy apró foltot az ACE-Step-re (feladatmegszakítási API; az audio.cpp nem igényel foltot, lásd: `external/patches/README.md`) — a saját egyéni web-felületeik nélkül, amelyekre nincs szükség.
3. Futtatja az `uv sync`-et az ACE-Step-hez, és buildeli az `audiocpp_server`-t (CUDA-kiadás, `yue2,sheetsage2,muscriptor` modellek) az audio.cpp-hez.
4. Letölti a YuE2/SheetSage2/MuScriptor GGUF-súlyokat (~10 GB) az audio.cpp `tools/model_manager_v2.py` szkriptjével.
5. Beállít egy `demucs` uv-projektet az `external/Demucs`-ban sávszétválasztáshoz, a PyTorch cu128-as wheel-indexére irányítva, hogy CUDA-s buildet kapjon (egy sima `uv add demucs` csendben CPU-s torch-wheelt oldana fel helyette).
6. Létrehozza a `backend/.env`-et a frissen klónozott repók útvonalaival, beleértve az `FFMPEG_BIN_DIR`-t — automatikusan felismerve az `ffmpeg` winget-telepítéséből (`setup_prereqs.bat`), még rögtön a telepítés után is ugyanabban a terminálban, mielőtt egy új felvenné a PATH-ról.

Az ACE-Step saját súlyait nem kell külön letölteni — az `acestep-api` az első kérésre lehúzza őket HuggingFace-ről/ModelScope-ról, ugyanúgy, mint a saját Gradio-felülete.

A szkript idempotens — biztonságosan újrafuttatható (a `-SkipBuild` / `-SkipWeights` jelölők kihagyják a megfelelő lépéseket). Elvárja, hogy a `git`, az [`uv`](https://docs.astral.sh/uv/getting-started/installation/), a Python 3, a CMake, a CUDA Toolkit és a Visual Studio Build Tools (C++ workload) már telepítve legyen — ha bármelyik hiányzik, azt a lépést egyszerűen kihagyja egy tippel, hogy mit telepíts.

Ezután az egyetlen kézi lépés a `CUDA_BIN_DIR` ellenőrzése a `backend/.env`-ben (az `FFMPEG_BIN_DIR` automatikusan kitöltődik — kivéve ha az ffmpeg egyáltalán nem található, ilyenkor a szkript jelzi, és kézzel kell beállítanod).

Kemény gépkövetelmények, amelyeket a szkript nem tud eltüntetni: Windows, CUDA-képes NVIDIA GPU (RTX 4080 16 GB-on tesztelve) és telepített videodriver.

**macOS-en (Apple Silicon):**
```sh
./setup_models.sh
```
macOS-re szabva, egy eltéréssel a fenti Windows-lépésekhez képest: alapból az `audiocpp_server` az audio.cpp saját **előre buildelt macOS/Metal kiadásából** települ (rögzített tag, kicsomagolás előtt sha256-ellenőrzéssel) — egyáltalán nem kell fordító, ellentétben a Windows-úttal, amely mindig forrásból buildel, mivel nincs előre buildelt CUDA-kiadás. A Demucs uv-projekt sincs CUDA wheel-indexre irányítva — egy sima `torch` függőség darwin/arm64-en amúgy is MPS-képes wheelt old fel, ugyanúgy, ahogy az ACE-Step-1.5 saját `pyproject.toml`-ja is teszi. A kiírt `backend/.env`-ben nincs `CUDA_BIN_DIR` — ezen az úton nincs CUDA toolkit, mivel a YuE2 a Metal-backenden fut.

Add hozzá a `--from-source`-ot, hogy a kiadás letöltése helyett ugyanabból a rögzített `dev` commitból buildelje az audio.cpp-t, amelyet a Windows is használ (hasznos, ha a kiadás lemarad egy `dev`-csak javítás mögött, vagy Intel Maceken, amelyeket az előre buildelt csomag nem fed le) — ehhez teljes **Xcode.app** kell (nem csak a Command Line Tools) a Metal-shaderfordító miatt; a `setup_prereqs.sh` pontos lépéseket ír ki, ha hiányzik. A `--skip-build` / `--skip-weights` megfelel a `-SkipBuild` / `-SkipWeights`-nek. Egyébként elvárja, hogy a `git`, az `uv` és a Python 3 már telepítve legyen (`cmake` is, a `--from-source`-hoz).

Kemény gépkövetelmények, amelyeket ez az út nem tud eltüntetni: macOS, Apple Silicon (M-széria) az alapértelmezett előre buildelt úthoz (Intelhez `--from-source` kell). MacBook Airen, Apple M5-tel, 24 GB RAM-mal tesztelve — beleértve egy tiszta futást egy olyan gépen, amelyen nem volt előzetes Homebrew-csomag vagy projektállapot, végig a YuE2-vel való hanggenerálásig a Metal-backenden. Ez az út újabb és kevésbé kipróbált, mint a Windows/CUDA-s — számíts rá, hogy lassabb (Metal CUDA helyett). A `--from-source` különösen igényelhet néha kézi igazítást (a rögzített commit-pin megemelését), ha az audio.cpp `dev` ága elmozdul upstream; az alapértelmezett kiadásalapú út rögzített tagre van pinelve, így magától nem mozdul el.

**Linuxon (NVIDIA CUDA):**
```sh
./setup_linux.sh
```
Buildeli az audio.cpp-t a natív linuxos CUDA-backenddel, telepíti az ACE-Step-et és a Demucsot elkülönített környezetekbe, letölti a modell súlyokat, és kiírja a `backend/.env`-et. Elvárja: git, Python 3.11/3.12, uv, Node.js 20.19+ (vagy 22.12+), npm, CMake, ffmpeg, valamint CUDA toolkit nvcc-vel plusz cuBLAS/cuFFT fejlesztői fejlécekkel. Az NVIDIA-drivert szándékosan nem telepíti és nem módosítja.

Az eszközútvonalak felülbírálhatók (`UV_BIN`, `NODE_BIN`, `NPM_BIN`, `CMAKE_BIN`, `NVCC_BIN`, `CUDA_TOOLKIT_PREFIX`, `CUDA_LIB_DIR`). Több-GPU-s gépeken az `ACE_STEP_DEVICE=0 YUE2_DEVICE=1 ./setup_linux.sh` külön eszközre pinezi a motorokat, és bekapcsolja az egyidejű modelltartást, ha a két explicit eszközérték eltér; ha bármelyik érték nincs beállítva (vagy mindkettő ugyanarra az eszközre mutat), marad az alapértelmezett kizárólagos váltogatás. Ubuntu 24.04 x86_64-en NVIDIA CUDA-val végponttól végpontig validálva.

### 2. lépés: futtatás

```cmd
dev.bat
```
Felhozza a backendet (9000-es port) és a frontendet Hot Module Replacementtel (Vite, 5173-as port), első futáskor létrehozza a `backend/.venv`-et és a `frontend/node_modules`-t, majd böngészőt nyit a [http://localhost:5173](http://localhost:5173) címen.

Éles módhoz — buildeld az SPA-t, és szolgálj ki mindent egyetlen portról:
```cmd
prod_run.bat
```
Buildeli a klienst `npm run build`-del, és a kész SPA-csomagot az API-val együtt szolgálja ki a [http://127.0.0.1:9000](http://127.0.0.1:9000) címen.

A sávszétválasztás `demucs` uv-projektjét a fenti `setup_models.bat` állítja be; maguk a `htdemucs` súlyok az első használatkor automatikusan letöltődnek.

**Linuxon:** a `./prod_run_linux.sh` buildeli a frontendet, és alapból a `127.0.0.1:9000`-en szolgálja ki az SPA-t és az API-t. Felülbírálhatod a `REMIQORA_HOST` / `REMIQORA_PORT` változókkal. Ha LAN-hozzáférést szeretnél, futtasd így: `REMIQORA_HOST=0.0.0.0 ./prod_run_linux.sh`; a Remiqorának nincs beépített hitelesítése, ezért csak megbízható hálózaton vagy hitelesített fordított proxy mögött tedd elérhetővé.

**macOS-en:** a `./dev.sh` és a `./prod_run.sh` a megfelelői — ugyanúgy viselkednek, kivéve hogy a backend/frontend a szkript saját háttérfeladataiként fut (mindkettőt Ctrl+C-vel állítod le), nem külön terminálablakokban.

---

## ⚙ Beállítás (.env)

A beállítások a `backend/.env`-ben élnek (minta: `backend/.env.example`; a `setup_models.bat` automatikusan létrehozza a klónozott repók útvonalaival):
```ini
ACE_STEP_DIR=E:\AI\ACE\ACE-Step-1.5
YUE2_DIR=E:\AI\YuE2-3B
DEMUCS_DIR=E:\AI\Demucs
FFMPEG_BIN_DIR=E:\AI\ACE\tools\ffmpeg-shared\ffmpeg-master-latest-win64-gpl-shared\bin
CUDA_BIN_DIR=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.4\bin
```

- `ACE_STEP_DIR` — a klónozott és foltozott ACE-Step-1.5 gyökere.
- `YUE2_DIR` — a klónozott és foltozott audio.cpp gyökere (ahol az `audiocpp_server.exe` buildelődik, és a YuE2/SheetSage2/MuScriptor GGUF-súlyok élnek).
- `DEMUCS_DIR` — a sávszétválasztáshoz használt `demucs` uv-projekt gyökere.
- `FFMPEG_BIN_DIR` — az `ffmpeg.exe`/`ffprobe.exe` fájlokat tartalmazó mappa.
- `CUDA_BIN_DIR` — a telepített CUDA Toolkit `bin` mappája (rajta kell lennie a PATH-on az `audiocpp_server.exe`-hez). Csak Windows — macOS-en ez nincs beállítva, mivel a YuE2 ott a Metal-backenden fut.
- `TRANSLATOR` — prompt-híd motor: `auto` (alapból: beépített offline fordító, ha a súlyai megvannak, különben Ollama), `local` (csak beépített), `ollama` (csak Ollama).

### Prompt-híd (magyar/bármilyen nyelvű bevitel)

Mindkét generáló űrlap elfogad szabadszavas leírást magyarul (vagy spanyolul, németül, franciául, … — válaszd ki a forrásnyelvet a dobozban, vagy hagyd Automaton). A backend lefordítja angol stílus címkékre `POST /api/prompt/prepare`-rel, és átnézésre kitölti az űrlapot — a már beírt dalszövegedet sosem írja felül. Két motor:

- **Beépített (alapértelmezett):** `facebook/nllb-200-distilled-600M` CPU-n fut a backenden belül (~2,4 GB, a setup-szkriptek töltik le egyszer a `backend/data/nllb` mappába, amely gitignore-olt). Nincs extra szolgáltatás, nincs VRAM-használat.
- **Ollama-tartalék:** `OLLAMA_HOST` (alapból `http://127.0.0.1:11434`) + `OLLAMA_MODEL` (alapból `qwen2.5:3b`). Gazdagabb stíluskifejtés nagyobb modellekkel a sebesség rovására; tartsd az Ollamát CPU-n (`ollama-cpu` jellegű indítás `CUDA_VISIBLE_DEVICES=-1`-gyel, saját ablakára szűkítve), hogy ne egye el a GPU-t, amelyre a zenei motoroknak van szükségük.

---

## Ismert korlátok

- Az ACE-Step és a YuE2 alapból kizárólagosan vált. Több-GPU-s linuxos gépeken, ha az `ACE_STEP_DEVICE` és a `YUE2_DEVICE` is explicit, eltérő eszközértékre van állítva, bekapcsol az egyidejű modelltartás, és mindegyik motor a saját GPU-jára pinelődik.
- A MIDI-átíráshoz kifejezetten a YuE2-nek kell aktívnak lennie (a MuScriptor-modell annak folyamatába töltődik be).
- A Windows (NVIDIA CUDA), a macOS/Apple Silicon (Metal/MPS) és a Linux x86_64 (NVIDIA CUDA) útvonalakhoz tartoznak setup-/futtató szkriptek — az elsőhöz `.bat`/`.ps1`, a másik kettőhöz `.sh` szkriptek. A Linux közösségi hozzájárulás: forrásból buildeli az audio.cpp-t, a driver mellé CUDA fejlesztői toolkit is kell, és Ubuntu 24.04-en lett végponttól végpontig ellenőrizve (WSL2-n GPU-átadással), nem natív vason vagy más disztrókon.
- Az asztali telepítők kísérletiek: aláíratlanok (SmartScreen- vagy Gatekeeper-kérdés), és az első indítás nagyjából 30 GB-ot tölt le. A telepítő Linuxot még nem támogat — linuxos felhasználók forrásból futnak a `setup_linux.sh`-val.
- A macOS/Metal-út újabb és kevésbé harcedzett, mint a Windows/CUDA-s; számíts rá, hogy lassabb. Alapból egy rögzített kiadási tagre pinezett előre buildelt YuE2-binárist telepít (nem kell fordító); a `--from-source` ehelyett ugyanazt a `dev` commitot buildeli, amelyet a Windows is használ, és néha igényelheti a pin megemelését, ha a `dev` elmozdul.

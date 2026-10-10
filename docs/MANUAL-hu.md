# Remiqora Magyar — kezelési utasítás

Helyi, GPU-s AI-zénestúdió: szövegből/leírásból generál zenét (ACE-Step 1.5,
YuE2-3B), szétszedi sávokra (Demucs), átírja MIDI-re (MuScriptor), LoRA-val
tanítható, és van beépített többsávos szerkesztője (DAW). Ez a magyar kiadás
([`slackmania-lab/remiqoraMagyar`](https://github.com/slackmania-lab/remiqoraMagyar))
az eredeti [`inikolax/remiqora`](https://github.com/inikolax/remiqora) forkja az
alábbi extrákkal: magyar felület, magyar/bármilyen nyelvű prompt-híd beépített
fordítóval, dalszöveg-író, generálási receptek, kedvencek, fejléc-hangerő,
GPU-terhelésjelző, AI-borítóképek, YuE2 kényelmi alapok (instrumentális pipa,
random seed be, 8 inference steps).

## Tartalom

1. [Indítási sorrend](#1-indítási-sorrend)
2. [Zenegenerálás YuE2-vel](#2-zenegenerálás-yue2-vel)
3. [Zenegenerálás ACE-Step-pel](#3-zenegenerálás-ace-step-pel)
4. [Prompt-híd (magyar/bármilyen nyelvű leírás)](#4-prompt-híd)
5. [Dalszöveg-író](#5-dalszöveg-író)
6. [Receptek (ismételhető generálások)](#6-receptek)
7. [Kedvencek](#7-kedvencek)
8. [Fejléc: hangerő, nyelv, GPU-jelvény](#8-fejléc)
9. [Borítóképek](#9-borítóképek)
10. [Stems, MIDI, DAW (röviden)](#10-stems-midi-daw)
11. [Fájlok, tárhely, súlyok](#11-fájlok-tárhely-súlyok)
12. [Hibakeresés](#12-hibakeresés)
13. [Frissítés GitHubról](#13-frissítés-githubról)

## 1. Indítási sorrend

A zene a GPU-n (NVIDIA), a segédszolgáltatások CPU-n futnak — ezért számít
a sorrend:

1. **Ollama (csak ha LLM-es fordítást/cizellálást vagy dalszöveg-írást akarsz):**
   dupla klikk az Asztalon lévő **`ollama-cpu.bat`**-ra. Ez CPU-módba
   kényszeríti (csak a saját ablakára!), így nem eszi a videokártya
   memóriáját. Az ablakot hagyd nyitva, amíg kell; bezárás = leáll.
   A beépített fordítóhoz és a zenéhez **nem kell**.
2. **Backend:** `yue.bat` dupla klikk (a `remiqora` mappából indítja a
   szervert a `http://127.0.0.1:9000` címen). Elsőre venv-et és pip-csomagokat
   tesz fel — türelem.
3. **Böngésző:** `http://127.0.0.1:9000` (vagy dev-módban `npm run dev` után
   `http://localhost:5173`). Első betöltéskor `Ctrl+Shift+R`, ha régi
   felületet látnál (cache).
4. **Modell indítása:** fejlécben kattints a motorra (**Start YuE2-3B** vagy
   **Start ACE-Step 1.5**). A másik magától leáll — egy GPU-n egyszerre csak
   egy modell fér el. Az első betöltés perceket vesz igénybe (súlyok a
   GPU-memóriába).

Leállítás: a backend ablak bezárása mindent leállít (a modellek GPU-folyamatait
is). Az Ollama-ablakot külön kell bezárni.

## 2. Zenegenerálás YuE2-vel

A YuE2 egész dalokat ír énekkel, 2-4 percben. Mezők:

- **Dalszöveg (Lyrics):** kötelező — a motor üresen el sem indul (kivéve
  instrumentális pipával, lásd lejjebb). `[Verse] / [Chorus] / [Bridge] /
  [Outro]` tagokkal strukturáld. Magyar szöveg is mehet (a kiejtés lutri,
  néha akcentussal énekel).
- **Stílus (Style/genre):** angol tagek, vesszővel (`sad, slow tempo rock,
  distorted electric guitars, melancholic, 70bpm`). Minél konkrétabb, annál
  jobb: tempóérzet, hangszerek karakterrel, vokál jellege, korszak.
- **COT mód:** `off` (gyors, terv nélkül), `melody` (adott dallam köré épít),
  `full` (előbb dallam+akkord ABC-tervet ír, aztán zenét — lassabb, jobb
  szerkezet; az instrumentális adapter megköveteli).
- **Modell pontossága:** `q8_0` (szebb, lassabb, ~több VRAM) vagy `q4_0`
  (gyorsabb vázlatokhoz). 8 GB VRAM-mal a `q4_0` a biztonságos alap.
- **Seed:** fix szám = ismételhető; **Random** pipa = mindig más. A kész
  kártyán látszik a tényleges seed.
- **Inference steps:** hány finomító lépés (8 gyors vázlat, 16-38 végleges —
  minél több, annál lassabb).
- **Variants:** 1-4 változat egy menetben (sorrendben készülnek).
- **Instrumentális pipa:** `[instrumental]` kerül a szövegbe, a COT `full`-ra
  vált, és betöltődik az instrumentális LoRA-adapter (egyszeri áttöltés,
  ~1 perc). Ígéret: ~95%-ban énekmentes; a maradék hümmögést lásd a
  10. pontnál (Demucs-takarítás).
- **ABC-kotta:** `full`/`melody` módban itt látszik/szerkeszthető a terv;
  SheetSage2-vel referenciából is kinyerhető.

**Sebesség-ökölszabály (RTX 5060 8 GB):** vázlat = `off` + `q4_0` + 8 steps +
1 variáns (percek). Végleges = `full` + `q8_0` + 16-38 steps (10-30+ perc).
Generálás közben a lista tetején a **GPU-jelvény** mutatja a terhelést
(`GPU 97% · 7.5/8.1 GB · 68°C`): ha magas, dolgozik — várd ki.

## 3. Zenegenerálás ACE-Step-pel

Gyors, rövidebb (10-300 mp) generálás, remix-műfajokkal:

- **Egyszerű (Simple):** egy mondat, a motor stílust ÉS szöveget is kitalál.
- **Egyéni (Custom):** style-tagek + dalszöveg, vagy **Instrumentális** pipa.
- **Referencia-sávval:** cover, szakasz-átfestés, sáv-kiemelés/hozzáadás,
  befejezés.
- **Súlyok:** első indításkor az `acestep-download` húzza le a checkpointokat;
  ha `Failed to load model ... no file named ...safetensors` hibát látsz,
  futtasd: `external\ACE-Step-1.5\.venv\Scripts\acestep-download.exe --dir external\ACE-Step-1.5\checkpoints`.

## 4. Prompt-híd

A generáló formok tetején lévő doboz: magyar (vagy bármilyen nyelvű) leírást
fordít angol stílus-tagekké, és **automatikusan beírja** a formba (átnézhető,
szerkeszthető; a saját dalszövegedet sosem írja felül).

- **Forrásnyelv:** Auto (magyar/angol felismerés) vagy 13 nyelv kézzel
  (magyar, español, Deutsch, …). Ékezet nélkül is működik (gyakori szavak
  ékezet-visszaállítással).
- **Motorok:** `beépített` chip = offline NLLB-fordító (CPU, gyors, hű
  fordítás, Ollama sem kell); legördülővel Ollama-modellek (`qwen2.5:3b`
  gyors, `qwen3:8b` cizelláltabb tagek — lassabb). Ha Ollama kell:
  `ollama-cpu.bat` az Asztalról.
- Beállítás `.env`-ben: `TRANSLATOR=auto` (súly ha van, különben Ollama) /
  `local` / `ollama`.

## 5. Dalszöveg-író

A dalszöveg-mező feletti doboz (mindkét formban): **témából ír strukturált
dalszöveget**. Téma bármilyen nyelven + célnyelv (English, Magyar, العربية,
Svenska, Norsk, Dansk, …) + versszakszám + refrén-pipa + Ollama-modell.
Gombnyomásra `[Verse]/[Chorus]` szerkezetű szöveg kerül a mezőbe. Megjegyzés:
a 8b-s modellek jó vázat adnak, de a rímeket érdemes kézzel csiszolni; az
ACE-form a célnyelvből a vokál-nyelvet is beállítja, ha támogatott.

## 6. Receptek

Minden küldéskor automatikusan lejön egy `<seed>_<cím>.remiqora.json`
(„recept"): motor, seed(ek), összes beállítás, dalszöveg, prompt, dátum.
A preset-sáv **📥** gombjával visszatölthető (a random pipa ilyenkor
automatikusan kikapcsol, hogy a tárolt seed érvényesüljön), és elküldhető
másnak — ő ugyanazt legenerálja. Kész példák: `recipes/` mappa a repóban.
Figyelem: a GPU-s mintavételezés közel determinisztikus, nem bit-pontos —
ugyanaz a zene születik, apró renderelési eltérések lehetnek.

## 7. Kedvencek

Minden kész kártyán **♡/❤** szív a kuka mellett — azonnal mentődik az
adatbázisba. Ha van kedvenced, a lista tetején megjelenik a **♡ Kedvencek**
szűrőgomb. Sok szám között így válogatható ki, mi tetszett.

## 8. Fejléc

- **Hangerő-csúszka** (🔊): az összes előnézet/lejátszás hangereje (sávok,
  DAW, MIDI). Megjegyzett érték. Az **exportot nem érinti** — a WAV/MP3
  mindig teljes jelszinttel renderel.
- **Nyelvgomb** (HU/EN/RU körforgás): a felület nyelve; magyar böngészővel
  magától magyarul indul.
- **GPU-jelvény**: csak generálás közben látszik a számlista tetején
  (`GPU % · VRAM · °C`, 3 mp-es frissítés). Magas = dolgozik, megnyugodhatsz.
- **Model-LED-ek**: melyik motor fut (zöld), áll (szürke), hibás (piros).

## 9. Borítóképek

Minden kész kártyán **🖼** gomb: a stílusból 512-es képet renderel **CPU-n**
(SDXL-Turbo, ha lejött a ~7 GB súly, különben SD-Turbo fallback) — a GPU
szabad marad. Kattintásra **nagyítható** (lightbox, Esc zár), **⬇** gombbal
letölthető, a fájl a hang mellé kerül (`..._cover.png`). A ✎ gombbal a
képprompt szabadon átírható (bármi lehet, nem csak borító); az érintetlen
automatikus prompthoz `no text, no watermark` társul, mert a betűk
rendre összefolynak. Arcok/kezek: gyengéje — absztrakt stílus ajánlott.

## 10. Stems, MIDI, DAW

- **Demucs (Stems panel):** egy kattintásra 4 sáv (vocals/drums/bass/other),
  sávonként lejátszás/letöltés. **Tipp makacs hümmögésre:** az
  instrumentálisnak szánt számot szed szét, és az **Open in editor** után a
  vocals-sávot némítsd/töröld — garantáltan énekmentes mix.
- **MuScriptor (MIDI panel):** mix vagy sáv átírása MIDI-be (YuE2-nek kell
  futnia hozzá), beépített lejátszó + zongoratekercs + `.mid` letöltés.
- **DAW (Szerkesztő):** tetszőleges sávszám, clipek mozgatása/vágása/fade-je,
  effektek (EQ, kompresszor, reverb…), BPM-warp, mentés, WAV/MP3 export a
  közös tárba. Nincs autosave — a **Mentés** gombot használd.

## 11. Fájlok, tárhely, súlyok

| Mi | Hol | Méret |
|---|---|---|
| YuE2/SheetSage2/MuScriptor súlyok | `external/audio.cpp/models/` | ~10 GB |
| ACE-Step checkpointok | `external/ACE-Step-1.5/checkpoints/` | ~9 GB |
| NLLB fordító | `backend/data/nllb/` | ~2,4 GB |
| SDXL borító (+SD fallback) | `backend/data/sdxl-turbo/`, `backend/data/sd-turbo/` | ~7 + 4 GB |
| Adatbázis + generált hangok | `backend/data/` (`aicollector.db`, `files/`) | nő használat közben |
| Ollama-modellek | `%USERPROFILE%\.ollama\models\` | darabonként 2-9 GB |

Asztali segítők: `ollama-cpu.bat` (CPU-s Ollama), `dl-sdxl.bat` (borítómodell
letöltése), `dl-nllb` helyett a setup scriptek (`setup_models.*` az NLLB-t és
az SDXL-t is lehúzza egyszer; `-SkipWeights`/`--skip-weights` kihagyja).

## 12. Hibakeresés

- **`CUDA backend ... has no device 0`:** a szerver nem látja a GPU-t.
  Gyógyszer sorrendben: fejlécben **Stop + Start** az adott motorra (backendet
  nem kell újraindítani). Ha visszatér: minden terminálablakot becsukni, **új**
  Terminálból indítani (a régiek régi környezetet hordozhatnak); ellenőrzés:
  `echo %CUDA_VISIBLE_DEVICES%` → üres kell legyen. Makacs esetben teljes
  leállítás + hidegindítás (nem alvásból ébresztés).
- **503-as sorok a logban leállított motornál:** normális volt régen; a
  mostani build már nem kérdezi az egészséget, ha a motor áll.
- **`Failed to load model ... safetensors` (ACE):** hiányzó checkpointok —
  lásd a 3. pont parancsát.
- **Híd: „Ollama is not reachable":** csak Ollama-módban számít; beépített
  módban nyugodtan állhat az Ollama.
- **Régi felület frissítés után:** `Ctrl+Shift+R` (erőltetett frissítés).
- **Logok:** `backend/logs/` (motoronként), böngésző-hibákhoz `F12` → Console.

## 13. Frissítés GitHubról

- Fork: [`slackmania-lab/remiqoraMagyar`](https://github.com/slackmania-lab/remiqoraMagyar).
- Eredeti: [`inikolax/remiqora`](https://github.com/inikolax/remiqora) —
  függőben lévő upstream PR: [#38](https://github.com/inikolax/remiqora/pull/38)
  (prompt-híd + NLLB + CUDA-szegezés).
- Saját példareceptek: `recipes/` mappa — új kedvencből egy paranccsal
  gyártható (az adatbázis soraiból), mehet melléjük README-sor.
